import json
import botocore.session
from botocore.session import Session
import boto3
import uuid

def lambda_handler(event, context):
  i_id=str(uuid.uuid4())
  default_namespace = 'default'
  account_id = 'AWS-Account-ID'
  ds_id='SPICE-ID'
  session = botocore.session.get_session()
  client = session.create_client("quicksight", region_name='us-east-1')
  response = client.create_ingestion(AwsAccountId = account_id, DataSetId=ds_id, IngestionId=i_id)
  responseIngestionArn = response['IngestionArn']
  describeResponse = client.describe_ingestion(AwsAccountId = account_id, DataSetId=ds_id, IngestionId=i_id)
  while (describeResponse['Ingestion']['IngestionStatus'] != 'COMPLETED'):
    describeResponse = client.describe_ingestion(AwsAccountId=account_id, DataSetId=ds_id, IngestionId=i_id)
  else:
    sns =boto3.client('sns')
    responsesns = sns.publish(TopicArn='arn:aws:sns:us-east-1:<AwsAccountId>:IngestionDone',
    Message='Ingestion is finished successfully!!')

  return {
 'statusCode': 200,
     }
