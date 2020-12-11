import json
import boto3
import logging
import csv
import io
import os
import tempfile
from typing import Any, Callable, Dict, List, Optional

lambda_aws_region = os.environ['AWS_REGION']
aws_region = 'us-east-1'

def delete_user(username, account_id, aws_region):
    qs_client = boto3.client('quicksight', region_name=aws_region)
    res = qs_client.delete_user(
        UserName=username,
        AwsAccountId=account_id,
        Namespace='default'
    )
    return res

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


def list_users(account_id, aws_region) -> List[Dict[str, Any]]:
    return _list(
        func_name="list_users",
        attr_name="UserList",
        Namespace='default',
        account_id=account_id,
        aws_region=aws_region
    )


def list_user_groups(UserName, account_id, aws_region) -> List[Dict[str, Any]]:
    return _list(
        func_name="list_user_groups",
        attr_name="GroupList",
        Namespace='default',
        UserName=UserName,
        account_id=account_id,
        aws_region=aws_region
    )


def lambda_handler(event, context):
    # get account_id
    sts_client = boto3.client("sts", region_name=aws_region)
    account_id = sts_client.get_caller_identity()["Account"]

    qs_client = boto3.client('quicksight', region_name='us-east-1')
    qs_local_client = boto3.client('quicksight', region_name=lambda_aws_region)

    users = list_users(account_id, aws_region)
    for user in users:
        print(user['UserName'])
        email = user['UserName'].split('/')[-1]
        role = user['Role']
        print(role)
        groups = list_user_groups(user['UserName'], account_id, aws_region)
        # print(groups)
        author = False
        admin = False
        for group in groups:
            if group['GroupName'] in ['quicksight-fed-bi-developer',
                                      'quicksight-fed-power-reader']:
                author = True
                break
            elif group['GroupName'] in ['quicksight-fed-bi-admin']:
                admin = True
                break

        if not author:
            if not admin:
                if role != 'READER':
                    try:
                        delete_user(user['UserName'], account_id, aws_region)
                        print(user[
                                  'UserName'] + " is deleted because of permissions downgrade from author/admin to reader!")
                    except Exception as e:
                        if str(e).find('does not exist'):
                            print(e)
                            pass
                        else:
                            raise e

