import json
import boto3
import logging
import csv
import io
import os
import tempfile
# import awswrangler as wr
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
        user_agent_extra=f"qs_sdk_granular_access",
    )

lambda_aws_region = os.environ['AWS_REGION']
aws_region = 'us-east-1'
ssm = boto3.client("ssm", region_name=lambda_aws_region, config=default_botocore_config())


def get_ssm_parameters(ssm_string):
    config_str = ssm.get_parameter(
        Name=ssm_string
    )['Parameter']['Value']
    return json.loads(config_str)


def describe_user(username, account_id, aws_region):
    qs_client = boto3.client('quicksight', region_name=aws_region, config=default_botocore_config())
    res = qs_client.describe_user(
        UserName=username,
        AwsAccountId=account_id,
        Namespace='default'
    )
    return res


def create_namespace(account_id, aws_region, ns):
    qs_client = boto3.client('quicksight', region_name=aws_region, config=default_botocore_config())
    res = qs_client.create_namespace(
        AwsAccountId=account_id,
        Namespace=ns,
        IdentityStore='QUICKSIGHT'
    )
    return res


def register_user(aws_region, Identity, Email, User, AccountId, Arn=None, Session=None, NS='default', Role='READER'):
    qs_client = boto3.client('quicksight', region_name=aws_region, config=default_botocore_config())
    if Identity == 'QUICKSIGHT':
        response = qs_client.register_user(
            IdentityType='QUICKSIGHT',
            Email=Email,
            UserRole=Role,
            AwsAccountId=AccountId,
            Namespace=NS,
            UserName=User)
    elif Identity == 'IAM' and Session is None:
        response = qs_client.register_user(
            IdentityType=Identity,
            Email=Email,
            UserRole=Role,
            IamArn=Arn,
            AwsAccountId=AccountId,
            Namespace=NS)
    elif Identity == 'IAM' and Session is not None:
        response = qs_client.register_user(
            IdentityType=Identity,
            Email=Email,
            UserRole=Role,
            IamArn=Arn,
            SessionName=Session,
            AwsAccountId=AccountId,
            Namespace=NS)

    return response


def delete_user(username, account_id, aws_region):
    qs_client = boto3.client('quicksight', region_name=aws_region, config=default_botocore_config())
    res = qs_client.delete_user(
        UserName=username,
        AwsAccountId=account_id,
        Namespace='default'
    )
    return res


def create_group(userrole, account_id, aws_region):
    qs_client = boto3.client('quicksight', region_name=aws_region, config=default_botocore_config())
    res = qs_client.create_group(
        GroupName=userrole,
        AwsAccountId=account_id,
        Namespace='default'
    )
    return res


def create_group_membership(username, userrole, account_id, aws_region):
    qs_client = boto3.client('quicksight', region_name=aws_region, config=default_botocore_config())
    res = qs_client.create_group_membership(
        MemberName=username,
        GroupName=userrole,
        AwsAccountId=account_id,
        Namespace='default'
    )
    return res


def delete_group_membership(username, userrole, account_id, aws_region):
    qs_client = boto3.client('quicksight', region_name=aws_region, config=default_botocore_config())
    res = qs_client.delete_group_membership(
        MemberName=username,
        GroupName=userrole,
        AwsAccountId=account_id,
        Namespace='default'
    )
    return res


def describe_dashboard_permissions(account_id, dashboardid, lambda_aws_region, qs_client):
    res = qs_client.describe_dashboard_permissions(
        AwsAccountId=account_id,
        DashboardId=dashboardid
    )
    return res


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


def list_groups(
        account_id, aws_region, ns
) -> List[Dict[str, Any]]:
    return _list(
        func_name="list_groups",
        attr_name="GroupList",
        Namespace=ns,
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


def list_users(account_id, aws_region,ns) -> List[Dict[str, Any]]:
    return _list(
        func_name="list_users",
        attr_name="UserList",
        Namespace=ns,
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


def list_data_sources(
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


def get_dashboard_ids(name: str, account_id, aws_region) -> List[str]:
    ids: List[str] = []
    for dashboard in list_dashboards(account_id, aws_region):
        if dashboard["Name"] == name:
            ids.append(dashboard["DashboardId"])
    return ids

def get_s3_info():
    bucket_name = get_ssm_parameters('/qs/config/groups')
    bucket_name = bucket_name['bucket-name']
    return bucket_name

def lambda_handler(event, context):
    # get account_id
    sts_client = boto3.client("sts", region_name=aws_region)
    account_id = sts_client.get_caller_identity()["Account"]

    qs_client = boto3.client('quicksight', region_name='us-east-1')
    qs_local_client = boto3.client('quicksight', region_name=lambda_aws_region)

    s3 = boto3.resource('s3')
    bucketname = get_s3_info()
    bucket = s3.Bucket(bucketname)

    key = 'monitoring/quicksight/errors/assets_governance_error_log.csv'
    tmpdir = tempfile.mkdtemp()
    local_file_name = 'assets_governance_error_log.csv'
    path = os.path.join(tmpdir, local_file_name)

    # update access permissions
    dashboards = list_dashboards(account_id, lambda_aws_region)
    analyses = list_analyses(account_id, lambda_aws_region)
    datasets = list_datasets(account_id, lambda_aws_region)
    datasources = list_data_sources(account_id, lambda_aws_region)
    themes = list_themes(account_id, lambda_aws_region)
    permissions = get_ssm_parameters('/qs/config/access')
    print(permissions)
    permissions = permissions['Permissions']
    reportlist = []
    errorlists = []
    for permission in permissions:
        arn = 'arn:aws:quicksight:' + aws_region + ':' + account_id + ":group/" + permission['ns_name'] +\
              "/quicksight-fed-" + permission['Group_Name'].lower()
        reportnamels = permission['Reports']
        print(reportnamels)
        if len(reportnamels) > 0:
            if reportnamels[0] == 'all':
                for dashboard in dashboards:
                    dashboardid = dashboard['DashboardId']
                    try:
                        response = qs_local_client.update_dashboard_permissions(
                            AwsAccountId=account_id,
                            DashboardId=dashboardid,
                            GrantPermissions=[
                                {
                                    'Principal': arn,
                                    'Actions': ['quicksight:DescribeDashboard',
                                                'quicksight:ListDashboardVersions',
                                                'quicksight:UpdateDashboardPermissions',
                                                'quicksight:QueryDashboard',
                                                'quicksight:UpdateDashboard',
                                                'quicksight:DeleteDashboard',
                                                'quicksight:DescribeDashboardPermissions',
                                                'quicksight:UpdateDashboardPublishedVersion']
                                },
                            ]
                        )

                    except Exception as e:
                        print(e)

                for dataset in datasets:
                    if dataset['Name'] not in ['Business Review', 'People Overview',
                                               'Sales Pipeline',
                                               'Web and Social Media Analytics']:
                        datasetid = dataset['DataSetId']
                        try:
                            response = qs_local_client.update_data_set_permissions(
                                AwsAccountId=account_id,
                                DataSetId=datasetid,
                                GrantPermissions=[
                                    {
                                        'Principal': arn,
                                        'Actions': ['quicksight:UpdateDataSetPermissions',
                                                    'quicksight:DescribeDataSet',
                                                    'quicksight:DescribeDataSetPermissions',
                                                    'quicksight:PassDataSet',
                                                    'quicksight:DescribeIngestion',
                                                    'quicksight:ListIngestions',
                                                    'quicksight:UpdateDataSet',
                                                    'quicksight:DeleteDataSet',
                                                    'quicksight:CreateIngestion',
                                                    'quicksight:CancelIngestion']
                                    },
                                ]
                            )

                        except Exception as e:
                            if str(e).find('FILE'):
                                pass
                            else:
                                print(e)

                for datasource in datasources:
                    datasourceid = datasource['DataSourceId']
                    try:
                        response = qs_local_client.update_data_source_permissions(
                            AwsAccountId=account_id,
                            DataSourceId=datasourceid,
                            GrantPermissions=[
                                {
                                    'Principal': arn,
                                    'Actions': ["quicksight:DescribeDataSource",
                                                "quicksight:DescribeDataSourcePermissions",
                                                "quicksight:PassDataSource",
                                                "quicksight:UpdateDataSource",
                                                "quicksight:DeleteDataSource",
                                                "quicksight:UpdateDataSourcePermissions"]
                                },
                            ]
                        )

                    except Exception as e:
                        if str(e).find('FILE'):
                            pass
                        else:
                            print(e)

                for analysis in analyses:
                    if analysis['Status'] != 'DELETED':
                        analysisid = analysis['AnalysisId']
                        try:
                            response = qs_local_client.update_analysis_permissions(
                                AwsAccountId=account_id,
                                AnalysisId=analysisid,
                                GrantPermissions=[
                                    {
                                        'Principal': arn,
                                        'Actions': ['quicksight:RestoreAnalysis',
                                                    'quicksight:UpdateAnalysisPermissions',
                                                    'quicksight:DeleteAnalysis',
                                                    'quicksight:QueryAnalysis',
                                                    'quicksight:DescribeAnalysisPermissions',
                                                    'quicksight:DescribeAnalysis',
                                                    'quicksight:UpdateAnalysis']
                                    },
                                ]
                            )

                        except Exception as e:
                            print(e)

                for theme in themes:
                    if theme['ThemeId'] not in ['SEASIDE', 'CLASSIC', 'MIDNIGHT']:
                        themeid = theme['ThemeId']
                        try:
                            response = qs_local_client.update_theme_permissions(
                                AwsAccountId=account_id,
                                ThemeId=themeid,
                                GrantPermissions=[
                                    {
                                        'Principal': arn,
                                        'Actions': ["quicksight:DescribeTheme",
                                                    "quicksight:DescribeThemeAlias",
                                                    "quicksight:ListThemeAliases",
                                                    "quicksight:ListThemeVersions",
                                                    "quicksight:DeleteTheme",
                                                    "quicksight:UpdateTheme",
                                                    "quicksight:CreateThemeAlias",
                                                    "quicksight:DeleteThemeAlias",
                                                    "quicksight:UpdateThemeAlias",
                                                    "quicksight:UpdateThemePermissions",
                                                    "quicksight:DescribeThemePermissions"
                                                    ]
                                    },
                                ]
                            )

                        except Exception as e:
                            print(e)

            elif reportnamels[0] == 'read-all':
                for dashboard in dashboards:
                    dashboardid = dashboard['DashboardId']
                    try:
                        response = qs_local_client.update_dashboard_permissions(
                            AwsAccountId=account_id,
                            DashboardId=dashboardid,
                            GrantPermissions=[
                                {
                                    'Principal': arn,
                                    'Actions': ['quicksight:DescribeDashboard',
                                                'quicksight:ListDashboardVersions',
                                                'quicksight:QueryDashboard']
                                },
                            ]
                        )

                    except Exception as e:
                        print(e)

                for dataset in datasets:
                    if dataset['Name'] not in ['Business Review', 'People Overview',
                                               'Sales Pipeline',
                                               'Web and Social Media Analytics', 'rls', 'user_attributes'
                                                                                        'groups_users', 'data_access',
                                               'object_access']:
                        datasetid = dataset['DataSetId']
                        try:
                            response = qs_local_client.update_data_set_permissions(
                                AwsAccountId=account_id,
                                DataSetId=datasetid,
                                GrantPermissions=[
                                    {
                                        'Principal': arn,
                                        'Actions': ['quicksight:DescribeDataSet',
                                                    'quicksight:DescribeDataSetPermissions',
                                                    'quicksight:PassDataSet',
                                                    'quicksight:DescribeIngestion',
                                                    'quicksight:ListIngestions',
                                                    'quicksight:CreateIngestion',
                                                    'quicksight:CancelIngestion']
                                    },
                                ]
                            )

                        except Exception as e:
                            if str(e).find('FILE'):
                                pass
                            else:
                                print(e)

                for datasource in datasources:
                    datasourceid = datasource['DataSourceId']
                    try:
                        response = qs_local_client.update_data_source_permissions(
                            AwsAccountId=account_id,
                            DataSourceId=datasourceid,
                            GrantPermissions=[
                                {
                                    'Principal': arn,
                                    'Actions': ["quicksight:DescribeDataSource",
                                                "quicksight:DescribeDataSourcePermissions",
                                                "quicksight:PassDataSource"]
                                },
                            ]
                        )

                    except Exception as e:
                        if str(e).find('FILE'):
                            pass
                        else:
                            print(e)
            else:
                for reportname in reportnamels:
                    ids = get_dashboard_ids(reportname, account_id, lambda_aws_region)
                    if len(ids) == 1:
                        reportlist.append(ids[0])
                        try:
                            response = qs_local_client.update_dashboard_permissions(
                                AwsAccountId=account_id,
                                DashboardId=ids[0],
                                GrantPermissions=[
                                    {
                                        'Principal': arn,
                                        'Actions': ['quicksight:DescribeDashboard',
                                                    'quicksight:ListDashboardVersions',
                                                    'quicksight:QueryDashboard']
                                    },
                                ]
                            )

                        except Exception as e:
                            print(e)

                    elif len(ids) > 1:
                        for id in ids:
                            errorlists.append(['Duplicate Dashboard Name', reportname, id])

                    elif len(ids) == 0:
                        errorlists.append(['Dashboard not existed', reportname, 'None'])

        # revoke dashboard access of a group
        group = "quicksight-fed-" + permission['Group_Name'].lower()
        print(group + 'can view ')
        print(reportnamels)
        print('and ids are: ')
        print(reportlist)
        # get dashboards list
        #dashboards = list_dashboards(account_id, lambda_aws_region)
        for dashboard in dashboards:
            dashboardid = dashboard['DashboardId']
            if dashboardid not in reportlist:
                # print(dashboardid)
                if group not in ['quicksight-fed-bi-developer', 'quicksight-fed-bi-admin',
                                 'quicksight-fed-power-reader']:
                    print("revoke " + group + "dashboard id: " + dashboardid + "(name: " + dashboard['Name'] + ")")
                    try:
                        response = qs_local_client.update_dashboard_permissions(
                            AwsAccountId=account_id,
                            DashboardId=dashboardid,
                            RevokePermissions=[
                                {
                                    'Principal': arn,
                                    'Actions': ['quicksight:DescribeDashboard',
                                                'quicksight:ListDashboardVersions',
                                                'quicksight:QueryDashboard']
                                },
                            ]
                        )
                    except Exception as e:
                        if str(e).find('Invalid principals given'):
                            pass
                        else:
                            raise e

    with open(path, 'w', newline='') as outfile:
        writer = csv.writer(outfile)
        for line in errorlists:
            writer.writerow(line)
    bucket.upload_file(path, key)
