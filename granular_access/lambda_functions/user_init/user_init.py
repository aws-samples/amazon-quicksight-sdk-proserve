import json
import boto3
import logging
import csv
import io
import os
import tempfile
from typing import Any, Callable, Dict, List, Optional


def get_s3_info(account_id, aws_region):
    ssm_client = boto3.client('ssm', region_name=aws_region)
    bucket_parameter = ssm_client.get_parameter(Name="/qs/config/groups", WithDecryption=True)
    bucket_name = bucket_parameter['Parameter']['Value']
    bucket_name = json.loads(bucket_name)  # bucket_name.split("\"")
    bucket_name = bucket_name['bucket-name']
    return bucket_name


def describe_user(username, account_id, aws_region):
    qs_client = boto3.client('quicksight', region_name=aws_region)
    res = qs_client.describe_user(
        UserName=username,
        AwsAccountId=account_id,
        Namespace='gademo'
    )
    return res


def delete_user(username, account_id, aws_region):
    qs_client = boto3.client('quicksight', region_name=aws_region)
    res = qs_client.delete_user(
        UserName=username,
        AwsAccountId=account_id,
        Namespace='gademo'
    )
    return res


def create_group(userrole, account_id, aws_region):
    qs_client = boto3.client('quicksight', region_name=aws_region)
    res = qs_client.create_group(
        GroupName=userrole,
        AwsAccountId=account_id,
        Namespace='gademo'
    )
    return res


def create_group_membership(username, userrole, account_id, aws_region):
    qs_client = boto3.client('quicksight', region_name=aws_region)
    res = qs_client.create_group_membership(
        MemberName=username,
        GroupName=userrole,
        AwsAccountId=account_id,
        Namespace='gademo'
    )
    return res

def lambda_handler(event, context):
    aws_region = 'us-east-1'
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
        Namespace='gademo',
        account_id=account_id,
        aws_region=aws_region
    )

def list_group_memberships(
        group_name: str,
        account_id: str,
        aws_region: str,
        namespace: str = "gademo"
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
        Namespace='gademo',
        account_id=account_id,
        aws_region=aws_region
    )







