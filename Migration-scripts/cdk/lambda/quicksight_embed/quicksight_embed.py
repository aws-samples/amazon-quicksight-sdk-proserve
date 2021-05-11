import json
import boto3
import os
import logging
from botocore.exceptions import ClientError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

def lambda_handler(event, context):
    logger.info(event)
    aws_region = os.getenv('AWS_REGION')
    sts_client = boto3.client('sts', region_name=aws_region,
                            endpoint_url=f'https://sts.{aws_region}.amazonaws.com')
    account_id = sts_client.get_caller_identity()['Account']
    dashboard_id = os.getenv('DASHBOARD_ID')
    quicksight_user_arn = os.getenv('QUICKSIGHT_USER_ARN')

    try:
        qs_client = boto3.client('quicksight',region_name='us-east-1')

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
            'isBase64Encoded': bool('false')
        }
    except ClientError as ex:
        return "Error generating embeddedURL: " + str(ex)
