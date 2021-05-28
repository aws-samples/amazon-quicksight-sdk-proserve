import os
import logging
import json
import boto3
from botocore.exceptions import ClientError

from quicksight_migration.batch_migration_lambda import migrate as batch
from quicksight_migration.incremental_migration_lambda import migrate as incremental
import quicksight_migration.quicksight_utils as qs_utils

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def delete_sqs_message(sqs_queue, aws_region, receipt_handle):
    """Delete the processed message in the SQS queue"""

    client = boto3.client('sqs', region_name=aws_region)
    try:
        response = client.delete_message(
            QueueUrl=sqs_queue,
            ReceiptHandle=receipt_handle
        )
    except ClientError as exc:
        logger.error("Failed to delete message from SQS queue: %s", sqs_queue)
        logger.error(exc.response['Error']['Message'])
        raise
    else:
        logger.info("SQS message deleted from %s! Receipt Handle: %s", sqs_queue, receipt_handle)
    return response


def lambda_handler(event, context):
    logger.info(event)

    # SQS Message
    sqs_url = os.getenv('SQS_URL')
    sqs_receipt_handle = event['Records'][0]['receiptHandle']
    sqs_region = event['Records'][0]['awsRegion']
    request_dict = json.loads(event['Records'][0]['body'])

    source_account_id = request_dict['source_account_id']
    target_account_id = request_dict['target_account_id']
    source_region = request_dict['source_region']
    target_region = request_dict['target_region']
    infra_config_param_name = os.getenv('INFRA_CONFIG_PARAM')
    s3_bucket = os.getenv('BUCKET_NAME')
    s3_key = os.getenv('S3_KEY')

    if request_dict.get('source_role_name') is not None:
        source_role_name = request_dict['source_role_name']
    else:
        source_role_name = request_dict.get('source_role_name',
                                            'quicksight-migration-target-assume-role')

    if request_dict.get('target_role_name') is not None:
        target_role_name = request_dict['target_role_name']
    else:
        target_role_name = request_dict.get('target_role_name',
                                            'quicksight-migration-target-assume-role')

    source_session = qs_utils.assume_role(source_account_id, source_role_name,
                                            source_region)
    target_session = qs_utils.assume_role(target_account_id, target_role_name,
                                            target_region)
    target_admin = qs_utils.get_user_arn(target_session, 'quicksight-migration-user')
    infra_details = qs_utils.get_ssm_parameters(target_session, infra_config_param_name)

    # QuickSight VPC connection will use VPC ID as name
    vpc = None
    if infra_details.get('vpcId') is not None:
        vpc = infra_details['vpcId']

    # RDS
    rds = None
    rdscredential = None
    if infra_details.get('rdsClusterId') is not None:
        rds = ['rdsClusterId']
        rds_password = qs_utils.get_secret(target_session, infra_details['rdsPassword'])
        rdscredential = {
            'CredentialPair': {
                'Username': infra_details['rdsUsername'],
                'Password': rds_password
            }
        }

    # Redshift
    redshift = None
    redshiftcredential = None
    if infra_details.get('redshiftClusterId') is not None:
        redshift_password = qs_utils.get_secret(target_session, infra_details['redshiftPassword'])
        redshift = {
            "ClusterId": infra_details['redshiftClusterId'],
            "Host": infra_details['redshiftHost'],
            "Database": infra_details['redshiftDB']
        }
        redshiftcredential = {
            'CredentialPair': {
                'Username': infra_details['redshiftUsername'],
                'Password': redshift_password
            }
        }

    namespace = 'default'
    if infra_details.get('namespace') is not None:
        namespace = infra_details['namespace']

    version = '1'
    if infra_details.get('version') is not None:
        version = infra_details['version']

    tag = [
            {
                'Key': 'testmigration',
                'Value': 'true'
            }
        ]

    target = qs_utils.get_target(
        target_session, rds, redshift, s3_bucket, s3_key,
        vpc, tag, target_admin, rdscredential, redshiftcredential, target_region,
        namespace, version)

    if request_dict['migration_type'] == "BATCH":
        try:
            batch(
                source_region,
                target_region,
                source_session,
                target_session,
                target,
                target_admin
            )
        except:
            raise Exception('Failed batch migration')
    elif request_dict['migration_type'] == "INCREMENTAL" and request_dict['migration_resource']:
        if request_dict['migration_resource'] not in ['theme', 'analysis', 'dashboard']:
            logger.error(
                "The migration_resource %s is not a valid resource",
                request_dict['migration_resource']
            )
            raise ValueError("Required parameters were not given")
        if not request_dict['migration_items'] or len(request_dict['migration_items'].split(",")) < 1:
            logger.error("The migration_items is missing or migration_items list is empty")
            raise ValueError("Required parameters were not given")

        try:
            incremental(
                source_region,
                target_region,
                source_session,
                target_session,
                target,
                target_admin,
                request_dict['migration_resource'],
                request_dict['migration_items'].split(",")
            )
        except:
            raise Exception('Failed incremental migration')
    else:
        logger.error(
            "The migration_type %s is not allowed or missing migration_resource\
                for 'INCREMENTAL' migration", request_dict['migration_type'])
        raise ValueError("Required parameters were not given")

    # Delete message from SQS queue if migration was successful
    delete_sqs_message(sqs_url, sqs_region, sqs_receipt_handle)
