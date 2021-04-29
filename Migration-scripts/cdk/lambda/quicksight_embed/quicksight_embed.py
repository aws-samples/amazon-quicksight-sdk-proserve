import json
import boto3
import os
import logging
from botocore.exceptions import ClientError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

def assume_role(aws_account_number, role_name, aws_region):
    sts_client = boto3.client('sts', region_name=aws_region,
                          endpoint_url=f'https://sts.{aws_region}.amazonaws.com')
    response = sts_client.assume_role(
        RoleArn='arn:aws:iam::' + aws_account_number + ':role/' + role_name,
        RoleSessionName='quicksight'
    )
    # Storing STS credentials
    session = boto3.Session(
        aws_access_key_id=response['Credentials']['AccessKeyId'],
        aws_secret_access_key=response['Credentials']['SecretAccessKey'],
        aws_session_token=response['Credentials']['SessionToken'],
        region_name=aws_region
    )
    return session


def lambda_handler(event, context):
    logger.info(event)
    aws_region = os.getenv('AWS_REGION')
    sts_client = boto3.client('sts', region_name=aws_region,
                            endpoint_url=f'https://sts.{aws_region}.amazonaws.com')
    account_id = sts_client.get_caller_identity()['Account']
    role_name = "quicksight-migration-source-assume-role"
    dashboard_id = os.getenv('DASHBOARD_ID')
    quicksight_user_arn = os.getenv('QUICKSIGHT_USER_ARN')
    session = assume_role(account_id, role_name, aws_region)

    try:
        qs_client = session.client('quicksight',region_name='us-east-1')

        response = qs_client.get_dashboard_embed_url(
                AwsAccountId = account_id,
                DashboardId = dashboard_id,
                IdentityType = 'QUICKSIGHT',
                SessionLifetimeInMinutes = 30,
                UndoRedoDisabled = True,
                ResetDisabled = True,
                UserArn = quicksight_user_arn
        )

        return {
            'statusCode': 200,
            'headers': {
                "Access-Control-Allow-Headers" : "Content-Type",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "OPTIONS,POST,GET",
                "Content-Type": "application/json" 
            },
            'body': json.dumps(response),
            'isBase64Encoded':  bool('false')
        }
    except ClientError as ex:
        return "Error generating embeddedURL: " + str(ex)
