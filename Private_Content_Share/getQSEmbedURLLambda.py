# getQSEmbedURLLambda.py
# author Ian Liao
# 11/03/2022

import os
import logging
# import requests
import boto3
import json
import base64
from botocore.client import Config
from botocore.exceptions import ClientError


LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
logging.getLogger("boto3").setLevel(logging.WARNING)
logging.getLogger("botocore").setLevel(logging.WARNING)
logger = logging.getLogger()
logger.setLevel(LOG_LEVEL)
# handler = logger.handlers[0]
# formatter = logging.Formatter('[%(levelname)s]\t%(asctime)s.%(msecs)dZ\t%(aws_request_id)s\t%(message)s\n', '%Y-%m-%dT%H:%M:%S')
# handler.setFormatter(formatter)

DEFAULT_QS_REGION = ""
DEFAULT_QS_IDENTITY_REGION = ""
DEFAULT_DASHBOARD_ID = ''
DEFAULT_QS_GROUP = ''

# Environment variables
QS_REGION = os.environ.get("QS_REGION", DEFAULT_QS_REGION)
dashboard_id = os.environ.get("DASHBOARD_ID", DEFAULT_DASHBOARD_ID)
QS_IDENTITY_REGION = os.environ.get("QS_IDENTITY_REGION", DEFAULT_QS_IDENTITY_REGION)
QS_GROUP = os.environ.get("QS_GROUP", DEFAULT_QS_GROUP)

sts_client = boto3.client("sts")
AWS_ACCOUNT_ID = sts_client.get_caller_identity()["Account"]

qs_client = boto3.client(
    "quicksight",
    region_name=QS_REGION
)

qs_id_client = boto3.client(
    "quicksight",
    region_name=QS_IDENTITY_REGION
)

def get_user_arn(user_email):
    return "arn:aws:quicksight:" + QS_IDENTITY_REGION + ":" + AWS_ACCOUNT_ID + ":user/default/" + user_email

def grant_dashboard_permission(user_email):
    qs_client.update_dashboard_permissions(
        AwsAccountId=AWS_ACCOUNT_ID,
        DashboardId=dashboard_id,
        GrantPermissions=[
            {
                'Principal': get_user_arn(user_email),
                'Actions': [
                    'quicksight:DescribeDashboard',
                    'quicksight:ListDashboardVersions',
                    'quicksight:UpdateDashboardPermissions',
                    'quicksight:QueryDashboard',
                    'quicksight:UpdateDashboard',
                    'quicksight:DeleteDashboard',
                    'quicksight:DescribeDashboardPermissions',
                    'quicksight:UpdateDashboardPublishedVersion'
                ]
            },
        ]
    )
    return

def create_quicksight_reader(user_email):
    try:
        qs_id_client.register_user(
            IdentityType='QUICKSIGHT',
            Email=user_email,
            UserRole='READER',
            AwsAccountId=AWS_ACCOUNT_ID,
            Namespace='default',
            UserName=user_email
        )
    except ClientError as e:
        logger.error(e)
        raise
    logger.info(f'Reader {user_email} is created.')
    return

def add_user_to_group(user_email):
    response = qs_id_client.create_group_membership(
        MemberName=user_email,
        GroupName='SupportEngineerGroup',
        AwsAccountId=AWS_ACCOUNT_ID,
        Namespace='default'
    )
    logger.info(f'Reader {user_email} is added to the support group.')

def check_quicksight_user(user_email):
    try:
        qs_id_client.describe_user(
            UserName=user_email,
            AwsAccountId=AWS_ACCOUNT_ID,
            Namespace='default'
        )
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            logger.info(f'User {user_email} does not exist yet.')
            create_quicksight_reader(user_email)
            #grant_dashboard_permission(user_email)
            add_user_to_group(user_email)
            pass
        else:
            logger.info(e)
            raise e


def get_quicksight_embed_url(did, user_email):
    user_arn = get_user_arn(user_email)
    response = qs_client.generate_embed_url_for_registered_user(
        AwsAccountId=AWS_ACCOUNT_ID,
        SessionLifetimeInMinutes=100,
        UserArn=user_arn,
        ExperienceConfiguration={
            'Dashboard': {
                'InitialDashboardId': did
            }
        }
    )
    return response['EmbedUrl']


def lambda_handler(event, context):
    logger.info(f"payload={event}")
    logger.info(context)
    token = event['params']['header']['Authorization']
    userName = json.loads(base64.b64decode(token.split('.')[1] + "========"))['cognito:username']
    user_email = json.loads(base64.b64decode(token.split('.')[1] + "========"))['email']
    logger.info(f'User is identified as {user_email}.')
    check_quicksight_user(user_email)
    qs_embed_url = get_quicksight_embed_url(dashboard_id, user_email)
    logger.info(qs_embed_url)
    return {
        "statusCode": 302,
        "headers": {
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Credentials": bool("true")
        },
        "headers": {
            "Location": qs_embed_url
        },
        "body": "https://example.com"
    }
