import json
import boto3
import logging
import csv
import io
import os
import tempfile
import time
from typing import Any, Callable, Dict, List, Optional, Union
from datetime import datetime

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
        user_agent_extra=f"qs_sdk_admin_console",
    )


sts_client = boto3.client("sts", config=default_botocore_config())
account_id = sts_client.get_caller_identity()["Account"]
aws_region = 'us-east-1'
lambda_aws_region = os.environ['AWS_REGION']
# qs_client = boto3.client('quicksight', config=default_botocore_config())
# qs_local_client = boto3.client('quicksight', region_name=lambda_aws_region, config=default_botocore_config())
cw_client = boto3.client('cloudwatch', config=default_botocore_config())


# print(lambda_aws_region)

def _list(
        func_name: str,
        attr_name: str,
        account_id: str,
        aws_region: str,
        **kwargs, ) -> List[Dict[str, Any]]:
    cw_client = boto3.client('cloudwatch', region_name=aws_region, config=default_botocore_config())
    func: Callable = getattr(cw_client, func_name)
    response = func(
        # AwsAccountId=account_id,
        **kwargs)
    next_token: str = response.get("NextToken", None)
    result: List[Dict[str, Any]] = response[attr_name]
    while next_token is not None:
        response = func(AwsAccountId=account_id, NextToken=next_token, **kwargs)
        next_token = response.get("NextToken", None)
        result += response[attr_name]
    return result


def get_metric_data(
        account_id,
        aws_region,
        **kwargs
) -> List[Dict[str, Any]]:
    return _list(
        func_name="get_metric_data",
        attr_name="MetricDataResults",
        account_id=account_id,
        aws_region=aws_region,
        **kwargs
    )


def lambda_handler(event, context):
    sts_client = boto3.client("sts", region_name=aws_region, config=default_botocore_config())
    account_id = sts_client.get_caller_identity()["Account"]

    # call s3 bucket
    s3 = boto3.resource('s3')
    bucketname = 'admin-console' + account_id
    bucket = s3.Bucket(bucketname)

    end = int(time.time())
    start = end - 1800
    key = 'monitoring/quicksight/visual_load_time/visual_load_time' + str(end) + '.csv'
    key2 = 'monitoring/quicksight/visual_load_count/visual_load_count' + str(end) + '.csv'
    # key3 = 'monitoring/quicksight/data_dictionary/data_dictionary.csv'
    tmpdir = tempfile.mkdtemp()
    local_file_name = 'visual_load_time.csv'
    local_file_name2 = 'visual_load_count.csv'
    # local_file_name3 = 'data_dictionary.csv'
    path = os.path.join(tmpdir, local_file_name)
    # print(path)e

    path2 = os.path.join(tmpdir, local_file_name2)
    # print(path2)

    # path3 = os.path.join(tmpdir, local_file_name3)
    # print(path3)

    visual_load_time = []
    visual_load_count = []

    # data_dictionary = []
    args = {
        'StartTime': start,
        'EndTime': end,
        'MetricDataQueries': [
            {
                'Expression': 'SELECT AVG(VisualLoadTime) FROM SCHEMA(\"AWS/QuickSight\", DashboardId,SheetId,VisualId) GROUP BY SheetId, VisualId,DashboardId',
                'Id': 'testt',
                'Label': 'qs_visuals',
                'Period': 300}
        ]
    }
    cw_metrics = get_metric_data(account_id, lambda_aws_region, **args)

    for item in cw_metrics:
        label_split = item['Label'].split(' ')
        sheetId = label_split[1]
        visualId = label_split[2]
        dashboardId = label_split[3]

        timestamp = int(item['Timestamps'][0].timestamp())


        value = item['Values'][0]

        visual_load_time.append([timestamp, dashboardId, sheetId, visualId, value])

    print(visual_load_time)

    with open(path, 'w', newline='') as outfile:
        writer = csv.writer(outfile, delimiter=',')
        for line in visual_load_time:
            writer.writerow(line)
    outfile.close()
    # upload file from tmp to s3 key
    bucket.upload_file(path, key)

    args2 = {
        'StartTime': start,
        'EndTime': end,
        'MetricDataQueries': [
            {
                'Expression': 'SELECT COUNT(VisualLoadTime) FROM SCHEMA(\"AWS/QuickSight\", DashboardId,SheetId,VisualId) GROUP BY SheetId, VisualId,DashboardId',
                'Id': 'testt',
                'Label': 'qs_visuals',
                'Period': 300}
        ]
    }
    cw_metrics2 = get_metric_data(account_id, lambda_aws_region, **args2)

    for item in cw_metrics2:
        label_split = item['Label'].split(' ')
        sheetId = label_split[1]
        visualId = label_split[2]
        dashboardId = label_split[3]

        timestamp = int(item['Timestamps'][0].timestamp())

        value = item['Values'][0]

        visual_load_count.append([timestamp, dashboardId, sheetId, visualId, value])

    print(visual_load_count)

    with open(path2, 'w', newline='') as outfile:
        writer = csv.writer(outfile, delimiter=',')
        for line in visual_load_count:
            writer.writerow(line)
    outfile.close()
    # upload file from tmp to s3 key
    bucket.upload_file(path2, key2)


