import json
import boto3
import logging
import csv
import io
import os
import tempfile
from typing import Any, Callable, Dict, List, Optional


def describe_user(username, account_id, aws_region):
    qs_client = boto3.client('quicksight', region_name=aws_region)
    res = qs_client.describe_user(
        UserName=username,
        AwsAccountId=account_id,
        Namespace='default'
    )
    return res


def delete_user(username, account_id, aws_region):
    qs_client = boto3.client('quicksight', region_name=aws_region)
    res = qs_client.delete_user(
        UserName=username,
        AwsAccountId=account_id,
        Namespace='default'
    )
    return res


def create_group(userrole, account_id, aws_region):
    qs_client = boto3.client('quicksight', region_name=aws_region)
    res = qs_client.create_group(
        GroupName=userrole,
        AwsAccountId=account_id,
        Namespace='default'
    )
    return res


def create_group_membership(username, userrole, account_id, aws_region):
    qs_client = boto3.client('quicksight', region_name=aws_region)
    res = qs_client.create_group_membership(
        MemberName=username,
        GroupName=userrole,
        AwsAccountId=account_id,
        Namespace='default'
    )
    return res


def describe_dashboard_permissions(account_id, dashboardid, aws_region):
    qs_client = boto3.client('quicksight', region_name=aws_region)
    res = qs_client.describe_dashboard_permissions(
        AwsAccountId=account_id,
        DashboardId=dashboardid
    )
    return res


def lambda_handler(event, context):
    aws_region = str(event['detail']['awsRegion'])
    sts_client = boto3.client("sts", region_name=aws_region)
    account_id = sts_client.get_caller_identity()["Account"]

    username = str(event['detail']['serviceEventDetails']['eventRequestDetails']['userName']).replace(":", "/")
    print(username)
    userrole = username.split('/')[0]

    # create group
    groups = list_groups(account_id, aws_region)
    new = []
    for group in groups:
        new.append(group['GroupName'])
    groups = new
    if userrole not in groups:
        try:
            response = create_group(userrole, account_id, aws_region)

        except Exception as e:
            if str(e).find('already exists.'):
                print(e)
            else:
                raise e

    # add user into group
    try:
        response = create_group_membership(username, userrole, account_id, aws_region)
        print(username + "is added into " + userrole)
    except Exception as e:
        raise e

def _list(
        func_name: str,
        attr_name: str,
        account_id: str,
        aws_region: str,
        **kwargs, ) -> List[Dict[str, Any]]:
    qs_client = boto3.client('quicksight', region_name=aws_region)
    func: Callable = getattr(qs_client, func_name)
    response = func(AwsAccountId=account_id, **kwargs)
    next_token: str = response.get("NextToken", None)
    result: List[Dict[str, Any]] = response[attr_name]
    while next_token is not None:
        response = func(AwsAccountId=account_id, NextToken=next_token, **kwargs)
        next_token = response.get("NextToken", None)
        result += response[attr_name]
    return result


def list_groups(
        account_id, aws_region
) -> List[Dict[str, Any]]:
    return _list(
        func_name="list_groups",
        attr_name="GroupList",
        Namespace='default',
        account_id=account_id,
        aws_region=aws_region
    )


def list_dashboards(
        account_id,
        aws_region
) -> List[Dict[str, Any]]:
    return _list(
        func_name="list_dashboards",
        attr_name="DashboardSummaryList",
        account_id=account_id,
        aws_region=aws_region
    )


def list_group_memberships(
        group_name: str,
        account_id: str,
        aws_region: str,
        namespace: str = "default"
) -> List[Dict[str, Any]]:
    return _list(
        func_name="list_group_memberships",
        attr_name="GroupMemberList",
        account_id=account_id,
        GroupName=group_name,
        Namespace=namespace,
        aws_region=aws_region
    )


def list_users(account_id, aws_region) -> List[Dict[str, Any]]:
    return _list(
        func_name="list_users",
        attr_name="UserList",
        Namespace='default',
        account_id=account_id,
        aws_region=aws_region
    )


def list_datasets(
        account_id,
        aws_region
) -> List[Dict[str, Any]]:
    return _list(
        func_name="list_data_sets",
        attr_name="DataSetSummaries",
        account_id=account_id,
        aws_region=aws_region
    )


def list_datasources(
        account_id,
        aws_region
) -> List[Dict[str, Any]]:
    return _list(
        func_name="list_data_sources",
        attr_name="DataSources",
        account_id=account_id,
        aws_region=aws_region
    )


def describe_data_set_permissions(account_id, datasetid, aws_region):
    qs_client = boto3.client('quicksight', region_name=aws_region)
    res = qs_client.describe_data_set_permissions(
        AwsAccountId=account_id,
        DataSetId=datasetid
    )
    return res


def describe_data_source_permissions(account_id, DataSourceId, aws_region):
    qs_client = boto3.client('quicksight', region_name=aws_region)
    res = qs_client.describe_data_source_permissions(
        AwsAccountId=account_id,
        DataSourceId=DataSourceId
    )
    return res

