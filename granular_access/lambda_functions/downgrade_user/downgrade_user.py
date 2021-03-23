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
ssm = boto3.client("ssm", region_name=lambda_aws_region)


def get_ssm_parameters(ssm_string):
    config_str = ssm.get_parameter(
        Name=ssm_string
    )['Parameter']['Value']
    return json.loads(config_str)


def get_s3_info():
    bucket_name = get_ssm_parameters('/qs/config/groups')
    bucket_name = bucket_name['bucket-name']
    return bucket_name


def delete_user(username, account_id, aws_region, ns):
    qs_client = boto3.client('quicksight', region_name=aws_region)
    res = qs_client.delete_user(
        UserName=username,
        AwsAccountId=account_id,
        Namespace=ns
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


def list_users(account_id, aws_region, ns) -> List[Dict[str, Any]]:
    return _list(
        func_name="list_users",
        attr_name="UserList",
        Namespace=ns,
        account_id=account_id,
        aws_region=aws_region
    )


def list_user_groups(UserName, account_id, aws_region, ns) -> List[Dict[str, Any]]:
    return _list(
        func_name="list_user_groups",
        attr_name="GroupList",
        Namespace=ns,
        UserName=UserName,
        account_id=account_id,
        aws_region=aws_region
    )


def list_namespaces(
        account_id, aws_region
) -> List[Dict[str, Any]]:
    return _list(
        func_name="list_namespaces",
        attr_name="Namespaces",
        account_id=account_id,
        aws_region=aws_region
    )


def lambda_handler(event, context):
    # get account_id
    sts_client = boto3.client("sts", region_name=aws_region)
    account_id = sts_client.get_caller_identity()["Account"]

    qs_client = boto3.client('quicksight', region_name='us-east-1')
    qs_local_client = boto3.client('quicksight', region_name=lambda_aws_region)

    s3 = boto3.resource('s3')
    bucketname = get_s3_info()
    bucket = s3.Bucket(bucketname)

    key = 'monitoring/quicksight/logs/delete_user_log.csv'
    tmpdir = tempfile.mkdtemp()
    local_file_name = 'delete_user_log.csv'
    path = os.path.join(tmpdir, local_file_name)

    delete_user_lists = []

    # load qs user role information
    roles = get_ssm_parameters('/qs/config/roles')
    # dict {groupname:role}
    print(roles)

    namespaces = list_namespaces(account_id, aws_region)
    for ns in namespaces:
        ns = ns['Name']
        users = list_users(account_id, aws_region, ns)
        for user in users:
            print(user['UserName'])
            email = user['UserName'].split('/')[-1]
            role = user['Role']
            print(role)
            groups = list_user_groups(user['UserName'], account_id, aws_region, ns)
            # print(groups)
            author = False
            admin = False
            for group in groups:
                if 'quicksight-fed' in group['GroupName']:
                    nsplusgroup = ns + '_' + group['GroupName'].split('-', 2)[2]
                    if nsplusgroup in roles:
                        if roles[nsplusgroup] == 'AUTHOR':
                            author = True
                            break
                        elif roles[nsplusgroup] == 'ADMIN':
                            admin = True
                            break
                else:
                    author = True

            if not author:
                if not admin:
                    if role != 'READER':
                        try:
                            delete_user(user['UserName'], account_id, aws_region, ns)
                            print(user[
                                      'UserName'] + " is deleted because of permissions downgrade from author/admin to reader!")
                            delete_user_lists.append(['Deleted', ns, user['UserName'], user['Role']])
                        except Exception as e:
                            if str(e).find('does not exist'):
                                print(e)
                                pass
                            else:
                                raise e

    with open(path, 'w', newline='') as outfile:
        writer = csv.writer(outfile)
        for line in delete_user_lists:
            writer.writerow(line)
    bucket.upload_file(path, key)

