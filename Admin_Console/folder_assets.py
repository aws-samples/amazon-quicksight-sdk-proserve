import json
import boto3
import logging
import csv
import io
import os
import tempfile
from typing import Any, Callable, Dict, List, Optional, Union

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
qs_client = boto3.client('quicksight', config=default_botocore_config())
qs_local_client = boto3.client('quicksight', region_name=lambda_aws_region, config=default_botocore_config())


# print(lambda_aws_region)

def lambda_handler(event, context):
    sts_client = boto3.client("sts", region_name=aws_region, config=default_botocore_config())
    account_id = sts_client.get_caller_identity()["Account"]

    # call s3 bucket
    s3 = boto3.resource('s3')
    bucketname = 'admin-console' + account_id
    bucket = s3.Bucket(bucketname)

    tmpdir = tempfile.mkdtemp()

    key_relation = 'monitoring/quicksight/folder_assets/folder_assets.csv'
    local_file_name = 'folder_assets.csv'
    path_relation = os.path.join(tmpdir, local_file_name)
    # print(path)

    key_lk = 'monitoring/quicksight/folder_lk/folder_lk.csv'
    local_file_name = 'folder_lk.csv'
    path_lk = os.path.join(tmpdir, local_file_name)

    folder_assets = []
    access = []

    folders = list_folders(account_id, lambda_aws_region)

    for folder in folders:
        folderid = folder['FolderId']
        folderarn = folder['Arn']
        foldername = folder['Name']
        permissions = describe_folder_permissions(account_id,folderid,lambda_aws_region)
        for principal in permissions:
            actions = '|'.join(principal['Actions'])
            principal = principal['Principal'].split("/")
            ptype = principal[0].split(":")
            ptype = ptype[-1]
            additional_info = principal[-2]
            if len(principal) == 4:
                principal = principal[2] + '/' + principal[3]
            elif len(principal) == 3:
                principal = principal[2]

            access.append(
                [account_id, lambda_aws_region, 'folder', foldername, folderid, folderarn, ptype, principal,
                 additional_info, actions])

        members = list_folder_members(account_id, folderid, lambda_aws_region)
        for member in members:
            memberid = member['MemberId']
            #get member which is not a folder
            folder_assets.append([lambda_aws_region, folderid, memberid])

        try: #get member which is a folder
            folder_details = describe_folder(account_id, folderid, lambda_aws_region)
            parent = folder_details['FolderPath'][-1]
            # print(parent)
            folder_assets.append([lambda_aws_region, parent, folderid])
        except Exception as e:
            if str(e).find('is not found'):
                pass
            else:
                raise e

    with open(path_relation, 'w', newline='') as outfile:
        writer = csv.writer(outfile, delimiter=',')
        for line in folder_assets:
            writer.writerow(line)
    outfile.close()
    # upload file from tmp to s3 key

    bucket.upload_file(path_relation, key_relation)

    with open(path_lk, 'w', newline='') as outfile:
        writer = csv.writer(outfile, delimiter=',')
        for line in access:
            writer.writerow(line)
    outfile.close()
    # upload file from tmp to s3 key
    bucket.upload_file(path_lk, key_lk)

def _list(
        func_name: str,
        attr_name: str,
        account_id: str,
        aws_region: str,
        **kwargs, ) -> List[Dict[str, Any]]:
    qs_client = boto3.client('quicksight', region_name=aws_region, config=default_botocore_config())
    func: Callable = getattr(qs_client, func_name)
    response = func(AwsAccountId=account_id, **kwargs)
    next_token: str = response.get("NextToken", None)
    result: List[Dict[str, Any]] = response[attr_name]
    while next_token is not None:
        response = func(AwsAccountId=account_id, NextToken=next_token, **kwargs)
        next_token = response.get("NextToken", None)
        result += response[attr_name]
    return result


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


def list_analyses(
        account_id,
        aws_region
) -> List[Dict[str, Any]]:
    return _list(
        func_name="list_analyses",
        attr_name="AnalysisSummaryList",
        account_id=account_id,
        aws_region=aws_region
    )


def list_themes(
        account_id,
        aws_region
) -> List[Dict[str, Any]]:
    return _list(
        func_name="list_themes",
        attr_name="ThemeSummaryList",
        account_id=account_id,
        aws_region=aws_region
    )


def list_ingestions(
        account_id,
        aws_region,
        DataSetId
) -> List[Dict[str, Any]]:
    return _list(
        func_name="list_ingestions",
        attr_name="Ingestions",
        account_id=account_id,
        aws_region=aws_region,
        DataSetId=DataSetId
    )

def list_folders(
        account_id,
        aws_region
) -> List[Dict[str, Any]]:
    return _list(
        func_name="list_folders",
        attr_name="FolderSummaryList",
        account_id=account_id,
        aws_region=aws_region
    )

def list_folder_members(
        account_id,
        aws_region
) -> List[Dict[str, Any]]:
    return _list(
        func_name="list_folder_members",
        attr_name="FolderMemberList",
        account_id=account_id,
        aws_region=aws_region
    )

def _describe(
        func_name: str,
        attr_name: str,
        account_id: str,
        aws_region: str,
        **kwargs, ) -> List[Dict[str, Any]]:
    qs_client = boto3.client('quicksight', region_name=aws_region, config=default_botocore_config())
    func: Callable = getattr(qs_client, func_name)
    response = func(AwsAccountId=account_id, **kwargs)
    result = response[attr_name]
    return result

def describe_folder(
        account_id,
        id,
        aws_region) -> Dict[str, Any]:
    return _describe(
        func_name="describe_folder",
        attr_name="Folder",
        account_id=account_id,
        aws_region=aws_region,
        FolderId=id
    )

def describe_dashboard(account_id, dashboardid, aws_region):
    qs_client = boto3.client('quicksight', region_name=aws_region, config=default_botocore_config())
    res = qs_client.describe_dashboard(
        AwsAccountId=account_id,
        DashboardId=dashboardid
    )
    return res


def describe_analysis(account_id, id, aws_region):
    qs_client = boto3.client('quicksight', region_name=aws_region, config=default_botocore_config())
    res = qs_client.describe_analysis(
        AwsAccountId=account_id,
        AnalysisId=id
    )
    return res


def describe_data_set(account_id, id, aws_region):
    qs_client = boto3.client('quicksight', region_name=aws_region, config=default_botocore_config())
    res = qs_client.describe_data_set(
        AwsAccountId=account_id,
        DataSetId=id
    )
    return res


def describe_data_source(account_id, id, aws_region):
    qs_client = boto3.client('quicksight', region_name=aws_region, config=default_botocore_config())
    res = qs_client.describe_data_source(
        AwsAccountId=account_id,
        DataSourceId=id
    )
    return res

def describe_folder_permissions(
        account_id,
        id,
        aws_region) -> Dict[str, Any]:
    return _describe(
        func_name="describe_folder_permissions",
        attr_name="Permissions",
        account_id=account_id,
        aws_region=aws_region,
        FolderId=id
    )


def describe_dashboard_permissions(account_id, dashboardid, aws_region):
    qs_client = boto3.client('quicksight', region_name=aws_region, config=default_botocore_config())
    res = qs_client.describe_dashboard_permissions(
        AwsAccountId=account_id,
        DashboardId=dashboardid
    )
    return res


def describe_analysis_permissions(account_id, aid, aws_region):
    qs_client = boto3.client('quicksight', region_name=aws_region, config=default_botocore_config())
    res = qs_client.describe_analysis_permissions(
        AwsAccountId=account_id,
        AnalysisId=aid
    )
    return res


def describe_theme_permissions(account_id, aid, aws_region):
    qs_client = boto3.client('quicksight', region_name=aws_region, config=default_botocore_config())
    res = qs_client.describe_theme_permissions(
        AwsAccountId=account_id,
        ThemeId=aid
    )
    return res


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
    qs_client = boto3.client('quicksight', region_name=aws_region, config=default_botocore_config())
    res = qs_client.describe_data_set_permissions(
        AwsAccountId=account_id,
        DataSetId=datasetid
    )
    return res


def describe_data_source_permissions(account_id, DataSourceId, aws_region):
    qs_client = boto3.client('quicksight', region_name=aws_region, config=default_botocore_config())
    res = qs_client.describe_data_source_permissions(
        AwsAccountId=account_id,
        DataSourceId=DataSourceId
    )
    return res
