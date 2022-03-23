"""
Gets Quicksight dashboard information and populates a DynamoDB table
"""
import os
import logging
import boto3
from botocore.exceptions import ClientError
from typing import Dict, Optional, Union
import botocore


def default_botocore_config() -> botocore.config.Config:
    """Botocore configuration."""
    retries_config: Dict[str, Union[str, int]] = {
        "max_attempts": int(os.getenv("AWS_MAX_ATTEMPTS", "5")),
    }
    mode: Optional[str] = os.getenv("AWS_RETRY_MODE")
    if mode:
        retries_config["mode"] = mode
    return botocore.config.Config(
        retries=retries_config,
        connect_timeout=10,
        max_pool_connections=10,
        user_agent_extra=f"qs_sdk_BIOps",
    )


LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.INFO)


class QuickSight:
    """QuickSight"""
    def __init__(self):
        self.logger = LOGGER
        self.logger.info(self.__class__.__name__)
        self.region = os.environ.get('AWS_REGION')
        # AWS clients
        self.client_quicksight = boto3.client("quicksight", config=default_botocore_config())
        self.client_sts = boto3.client("sts", config=default_botocore_config())


    @property
    def account_id(self):
        """
        Get account ID

        :return: AWS account ID
        """
        return self.client_sts.get_caller_identity()["Account"]


    def get_dashboards(self) -> list:
        """
        Get all QuickSight dashboards
        """

        # Retrieve all of the existing dashboards
        dash_ids = []
        next_token = {}
        while True:
            dash_list = self.client_quicksight.list_dashboards(
                AwsAccountId=self.account_id,
                **next_token
            )

            for dash in dash_list['DashboardSummaryList']:
                dash_id = dash['DashboardId']
                dash_ids.append(dash_id)
            # Check if NextToken was in the response
            if 'NextToken' in dash_list:
                self.logger.debug("Found nextToken in dashboards list. Next set of items...")
                next_token['NextToken'] = dash_list['NextToken']
            else:
                self.logger.debug("No nextToken found in dashboards list")
                break

        return dash_ids

    def describe_dashboard(self, dash_id) -> dict:
        """
        Describe a dashboard
        """
        try:
            self.logger.info("Describing dashboard: %s", dash_id)
            response = self.client_quicksight.describe_dashboard(
                AwsAccountId=self.account_id,
                DashboardId=dash_id
            )
        except ClientError as ex:
            if ex.response['Error']['Code'] == 'InvalidParameterValueException':
                raise ex
            elif ex.response['Error']['Code'] == 'ResourceNotFoundException':
                raise ex
            elif ex.response['Error']['Code'] == 'AccessDeniedException':
                raise ex
            elif ex.response['Error']['Code'] == 'ThrottlingException':
                raise ex
            elif ex.response['Error']['Code'] == 'UnsupportedUserEditionException':
                raise ex
            elif ex.response['Error']['Code'] == 'InternalFailureException':
                raise ex

        return response


    def describe_dataset(self, dataset_id) -> str:
        """
        Get the QuickSight dataset name
        """

        # Describe a dataset
        try:
            dataset = self.client_quicksight.describe_data_set(
                AwsAccountId=self.account_id,
                DataSetId=dataset_id
            )
        except ClientError as ex:
            self.logger.error("Failed to describe dataset")
            self.logger.error(ex.response['Error']['Message'])

        return dataset['DataSet']['Name']


class Dynamo:
    def __init__(self):
        self.logger = LOGGER
        self.logger.info(self.__class__.__name__)
        self.region = os.environ.get('AWS_REGION')
        self.table_name = os.environ.get('TABLE_NAME')

        # AWS clients
        self.session = boto3.session.Session()
        self.client = self.session.client(
            service_name='dynamodb',
            region_name=self.region
        )

    def get_item(self, dashboard_id) -> dict:
        """Gets an item from a DDB table given an dashboard_id"""
        try:
            response = self.client.get_item(
                TableName=self.table_name,
                Key={
                    'dashboardId': {
                        'S': dashboard_id
                    }
                }
            )
        except ClientError as ex:
            if ex.response['Error']['Code'] == 'ResourceNotFoundException':
                self.logger.exception('Unable to find dashboard_id %s, will create.', dashboard_id)
                raise ex
            elif ex.response['Error']['Code'] == 'RequestLimitExceeded':
                raise ex
            elif ex.response['Error']['Code'] == 'ProvisionedThroughputExceededException':
                raise ex
        else:
            if len(response) == 1:
                return None
            return response['Item']


    def get_item_ids(self):
        """Gets all items from a DDB table"""
        try:
            response = self.client.scan(
                TableName=self.table_name
            )

            data = response['Items']
            while 'LastEvaluatedKey' in response:
                response = self.client.scan(
                    TableName=self.table_name,
                    ExclusiveStartKey=response['LastEvaluatedKey']
                )
                data.extend(response['Items'])
        except ClientError as ex:
            self.logger.exception('Unable to perform scan on table')
            raise ex

        return data

    def put_item(self, dashboard) -> dict:
        """Inserts or updates an dashboard into a DDB table"""

        dash_errors = []
        # Grab the errors list
        dash_error_list = dashboard['Version']['Errors']
        # Check if there are errors in the list
        if len(dash_error_list) > 0:
            for dash_error in dash_error_list:
                # Add dasboard ID and error type to errors dict
                dash_errors.append(dash_error['Type'])
        else:
            self.logger.debug("No errors found for dashboard: %s", dashboard['DashboardId'])
            dash_errors.append("None")

        try:
            response = self.client.update_item(
                TableName=self.table_name,
                Key={
                    'dashboardId':{
                        'S': dashboard['DashboardId']
                    }
                },
                AttributeUpdates={
                    "name":{
                        "Action": "PUT", "Value":{
                            "S": dashboard['Name']
                        }
                    },
                    "created_time":{
                        "Action": "PUT", "Value":{
                            "S": str(dashboard['CreatedTime'])
                        }
                    },
                    "last_published_time":{
                        "Action": "PUT", "Value":{
                            "S": str(dashboard['LastPublishedTime'])
                        }
                    },
                    "last_updated_time":{
                        "Action": "PUT", "Value":{
                            "S": str(dashboard['LastUpdatedTime'])
                        }
                    },
                    "version_number":{
                        "Action": "PUT", "Value":{
                            "N": str(dashboard['Version']['VersionNumber'])
                        }
                    },
                    "errors":{
                        "Action": "PUT", "Value":{
                            "SS": dash_errors
                        }
                    }
                }
            )
            return response
        except ClientError as ex:
            self.logger.exception('Unable to insert or update dashboard_id %s.', dashboard['DashboardId'])
            raise ex

    def delete_item(self, dashboard_id) -> dict:
        """Deletes an item dashboard_id"""
        try:
            response = self.client.update_item(
                TableName=self.table_name,
                Key={
                    'dashboardId':{
                        'S': dashboard_id
                    }
                }
            )
            return response
        except ClientError as ex:
            self.logger.exception('Unable to delete dashboard_id %s.', dashboard_id)
            raise ex


def lambda_handler(event, context):
    """Lambda handler"""
    quicksight = QuickSight()
    dynamo = Dynamo()

    # Add dashboard to DDB table
    dashboards_list = quicksight.get_dashboards()
    for dash_id in dashboards_list:
        dash_details = quicksight.describe_dashboard(dash_id)['Dashboard']
        LOGGER.info("Putting %s into DDB", dash_id)
        LOGGER.info("Dashboard details: %s", dash_details)
        dynamo.put_item(dash_details)

    # If a dashboard no longer exists then remove from DDB table
    known_dashboards = dynamo.get_item_ids()
    known_dashboard_ids = []
    for known_dash_id in known_dashboards:
        known_dashboard_ids.append(known_dash_id['dashboardId']['S'])
    LOGGER.info("Dashboard ID's found in DDB table: %s", known_dashboard_ids)
    old_dashboards = list(set(dashboards_list).difference(known_dashboard_ids))
    for old_dash_id in old_dashboards:
        LOGGER.info("Deleting %s from DDB", old_dash_id)
        dynamo.delete_item(old_dash_id)
