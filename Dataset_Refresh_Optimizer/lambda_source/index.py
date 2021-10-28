#!/usr/bin/env python3
"""Lambda function to Trigger SPICE ingestion job."""

import json
import logging
import time
import traceback
from datetime import datetime

import boto3
from botocore.exceptions import ClientError, ParamValidationError

LOGGER = logging.getLogger()
LOGGER.setLevel(logging.INFO)

session = boto3.Session(region_name='us-east-2')
qs = session.client('quicksight')
sns = session.client('sns')
sts = session.client('sts')
ACC = sts.get_caller_identity()['Account']

LOGGER.info('-- Account ID: ' + ACC)
now = datetime.now()
_today = now.strftime("%Y-%m-%d-%H-%M-%S")


def get_dataset_id(_ds_name):
    """Returns the ID of the target dataset."""
    try:
        response = qs.list_data_sets(AwsAccountId=ACC)
        while True:
            for res in response['DataSetSummaries']:
                if res["Name"] == _ds_name:
                    _ds_id = res["DataSetId"]
                    LOGGER.info('-- DataSetName: %s , DataSetID: %s', _ds_name, _ds_id)
                    return _ds_id
            try:
                response = qs.list_data_sets(AwsAccountId=ACC, NextToken=response["NextToken"])
            except KeyError:
                break
    except Exception as e:
        LOGGER.error(e)
        # send_notification(str(e))
        traceback.print_exc()

    return None


def get_dataset_ingestions(_ds_id):
    """Returns the list of ingestions of the target dataset."""
    try:
        try:
            response = qs.list_ingestions(AwsAccountId=ACC, DataSetId=_ds_id)
        except ParamValidationError:
            LOGGER.error('-- WARNING! dataset ID: ' + str(_ds_id) + ' not set for refreshing or author access error!')
        while True:
            for res in response['Ingestions']:
                status = res["IngestionStatus"]
                if status in ['RUNNING', 'QUEUED']:
                    LOGGER.info('-- DataSetID: %s is already being updated ...', _ds_id)
                    LOGGER.info('-- Last scheduled ingestion created at %s', res["CreatedTime"])
                    time.sleep(10)
                try:
                    if int(res["IngestionTimeInSeconds"]) > 1500:
                        LOGGER.info('-- ERROR! Ingestion time more than specified schedule')
                        LOGGER.info('-- IngestionTimeInSeconds = ' + str(res["IngestionTimeInSeconds"]))
                        LOGGER.info('-- Process on hold ...')
                        time.sleep(10)
                        LOGGER.info('-- Process continued ...')
                        return -1
                except KeyError:
                    pass
                    # LOGGER.info('-- Last status has been retrieved, no duration identified.')
            try:
                response = qs.list_ingestions(AwsAccountId=ACC, DataSetId=_ds_id, NextToken=response["NextToken"])
            except KeyError:
                break
        return response['Ingestions']
    except Exception as e:
        LOGGER.error(e)
        traceback.print_exc()

    return None


def create_dataset_ingestion(_ds_id):
    try:
        res = qs.create_ingestion(DataSetId=_ds_id, IngestionId=_today, AwsAccountId=ACC)
    except ClientError as error:
        if error.response['Error']['Code'] == 'LimitExceededException':
            LOGGER.info('API call limit exceeded; backing off and retrying...')
            return None
        else:
            raise error
    return res


def get_sns_arn():
    """Retrieves SNS Topic ARN."""
    try:
        response = sns.list_topics()
        while True:
            for res in response['Topics']:
                if "QSTopicSNSEmail" in res["TopicArn"]:
                    LOGGER.info('-- SNS Topic ARN: ' + res["TopicArn"])
                    return res["TopicArn"]
            try:
                response = sns.list_topics(NextToken=response["NextToken"])
            except KeyError:
                break
    except Exception as e:
        LOGGER.error(e)
        # send_notification(str(e))
    return None


def send_notification(msg):
    """Sends notification to SNS topic in case of failure."""
    target_arn = get_sns_arn()
    if not target_arn:
        return False
    response = sns.publish(TargetArn=target_arn,
                           Message=json.dumps({'default': json.dumps(msg)}),
                           MessageStructure='json')
    LOGGER.info('-- Notification sent to the SNS topic: ' + target_arn)
    return True


def handler(event, context):
    """Lambda function to trigger SPICE refresh jobs."""
    LOGGER.info('-- Received Event: %s', event)
    LOGGER.info('-- Received Context: %s', context)
    ds_name = event['TARGET_DATASET']
    ds_id = get_dataset_id(ds_name)
    ds_ingestion = get_dataset_ingestions(ds_id)
    if ds_ingestion == -1:
        return {"message": "FATAL ERROR!, ingestion time exceeded the schedule interval !", "StatusCode": 503}
    else:
        res = create_dataset_ingestion(ds_id)
        if not res:
            return {"message": "FATAL ERROR!, could not create ingestion!", "StatusCode": 503}
        else:
            LOGGER.info('-- Successfully triggered an ingestion for dataset: %s , DataSetId: %s', ds_name, ds_id)
            LOGGER.info('-- Ingestion time value for reference: %s', _today)
            return {"message": "Finished successfully.", "StatusCode": 200}
