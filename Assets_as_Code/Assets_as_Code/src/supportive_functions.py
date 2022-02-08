import boto3
import json
import time
from IPython.display import JSON
from IPython.display import IFrame
from typing import Any, Dict, List, Optional
import botocore
import os

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
        user_agent_extra=f"qs_sdk_assets_as_code",
    )

# display json string in json format
def display_json(doc, root='root'):
    return JSON(doc)

#session construction
def _assume_role(aws_account_number, role_name, aws_region):
    sts_client = boto3.client('sts', default_botocore_config())
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

    #logger.info("Assumed session for " + aws_account_number + " in region " + aws_region + ".")

    return session

# get QS user arn
def get_user_arn(session, username, region='us-east-1', namespace='default'):
    sts_client = session.client("sts")
    account_id = sts_client.get_caller_identity()["Account"]
    if username == 'root':
        arn = 'arn:aws:iam::' + account_id + ':' + username
    else:
        arn = "arn:aws:quicksight:" + region + ":" + account_id + ":user/" + namespace + "/" + username

    return arn

# get QS asset arn
def get_asset_arn(session, id, type, region='us-east-1'):
    sts_client = session.client("sts")
    account_id = sts_client.get_caller_identity()["Account"]
    arn = "arn:aws:quicksight:" + region + ":" + account_id + ":" + type + "/" + id
    return arn

def get_target(targetsession, rds, redshift, s3Bucket, s3Key, vpc, tag, targetadmin, rdscredential, redshiftcredential,
               region='us-east-1', namespace='default', version='1'):
    sts_client = targetsession.client("sts")
    account_id = sts_client.get_caller_identity()["Account"]
    target: Dict[str, Any] = {
        "rds": {"rdsinstanceid": ''},
        "s3": {"manifestBucket": '',
               "manifestkey": ''},
        "vpc": '',
        "tag": '',
        "credential": {"rdscredential": rdscredential,
                       "redshiftcredential": redshiftcredential},
        "datasourcepermission": [
            {'Principal': targetadmin,
             'Actions': ["quicksight:DescribeDataSource",
                         "quicksight:DescribeDataSourcePermissions",
                         "quicksight:PassDataSource",
                         "quicksight:UpdateDataSource",
                         "quicksight:DeleteDataSource",
                         "quicksight:UpdateDataSourcePermissions"]
             }
        ],
        "datasetpermission": [{'Principal': targetadmin,
                               'Actions': ['quicksight:UpdateDataSetPermissions',
                                           'quicksight:DescribeDataSet',
                                           'quicksight:DescribeDataSetPermissions',
                                           'quicksight:PassDataSet',
                                           'quicksight:DescribeIngestion',
                                           'quicksight:ListIngestions',
                                           'quicksight:UpdateDataSet',
                                           'quicksight:DeleteDataSet',
                                           'quicksight:CreateIngestion',
                                           'quicksight:CancelIngestion']}],
        "version": '1',
    }

    if rds:
        target["rds"]["rdsinstanceid"] = rds

    if redshift:
        target["redshift"] = redshift

    if s3Bucket:
        target["s3"]["manifestBucket"] = s3Bucket
        target["s3"]["manifestkey"] = s3Key

    if vpc:
        target["vpc"] = "arn:aws:quicksight:" + region + ":" + account_id + ":vpcConnection/" + vpc

    if tag:
        target["tag"] = tag

    if rdscredential:
        target["credential"]["rdscredential"] = rdscredential

    if redshiftcredential:
        target["credential"]["redshiftcredential"] = redshiftcredential

    return target