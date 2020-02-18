import json
import boto3
import pandas as pd
import os, tempfile
import sys
import uuid
from urllib.parse import unquote_plus

s3_client = boto3.client('s3')

def lambda_handler(event, context):
    message = event['Records'][0]['Sns']['Message']
    bucket = 'Excel-raw-data-YourName'
    newbucket = 'Cleaned-data-YourName'
    jmessage = json.loads(message)
    key = unquote_plus(jmessage["Records"][0]['s3']['object']['key'])
    directory_name = tempfile.mkdtemp()
    download_path = os.path.join(directory_name, 'raw.xlsx')
    newkey= 'cleaned.csv'
    upload_path = os.path.join(directory_name, newkey)
    s3_client.download_file(bucket, key, download_path)
    df = pd.read_Excel(download_path, skiprows=3)
    header2 = ['K', 'GEN STATUS']
    df.to_csv(upload_path, columns=header2, index=False)
    s3_client.upload_file(upload_path, newbucket, newkey)

    sns = boto3.client('sns')
    response = sns.publish(
        TopicArn='arn:aws:sns:us-east-1:AWS Account ID: Data-Cleaned',
        Message='Data is cleaned and save into bucket Cleaned-data. Auto data ingestion is running.'
    )
    return {
        'statusCode': 200,
        'body': json.dumps('Done with cleansing!!')
    }
