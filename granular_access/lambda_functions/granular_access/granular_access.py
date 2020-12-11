import json
import boto3
import logging
import csv
import io
import os
import tempfile
# import awswrangler as wr
from typing import Any, Callable, Dict, List, Optional

lambda_aws_region = os.environ['AWS_REGION']
aws_region = 'us-east-1'
ssm = boto3.client("ssm", region_name=lambda_aws_region)


def get_ssm_parameters(ssm_string):
    config_str = ssm.get_parameter(
        Name=ssm_string
    )['Parameter']['Value']
    return json.loads(config_str)


def describe_user(username, account_id, aws_region):
    qs_client = boto3.client('quicksight', region_name=aws_region)
    res = qs_client.describe_user(
        UserName=username,
        AwsAccountId=account_id,
        Namespace='default'
    )
    return res


def create_namespace(account_id, aws_region, ns):
    qs_client = boto3.client('quicksight', region_name=aws_region)
    res = qs_client.create_namespace(
        AwsAccountId=account_id,
        Namespace=ns,
        IdentityStore='QUICKSIGHT'
    )
    return res


def register_user(aws_region, Identity, Email, User, AccountId, Arn=None, Session=None, NS='default', Role='READER'):
    qs_client = boto3.client('quicksight', region_name=aws_region)
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


def delete_group_membership(username, userrole, account_id, aws_region):
    qs_client = boto3.client('quicksight', region_name=aws_region)
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
    qs_client = boto3.client('quicksight', region_name=aws_region)
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


def lambda_handler(event, context):
    # get account_id
    sts_client = boto3.client("sts", region_name=aws_region)
    account_id = sts_client.get_caller_identity()["Account"]

    # call s3 bucket to get group information
    s3 = boto3.resource('s3', region_name=lambda_aws_region)
    bucketname = get_ssm_parameters('/qs/config/groups')
    bucketname = bucketname['bucket-name']
    bucket = s3.Bucket(bucketname)
    mkey = 'membership/membership.csv'
    tmpdir = tempfile.mkdtemp()
    local_file_name = 'membership.csv'
    path = os.path.join(tmpdir, local_file_name)
    bucket.download_file(mkey, path)

    qs_client = boto3.client('quicksight', region_name='us-east-1')
    qs_local_client = boto3.client('quicksight', region_name=lambda_aws_region)

    # get current quicksight groups
    groups = list_groups(account_id, aws_region)
    new = []
    for group in groups:
        new.append(group['GroupName'])
    groups = new
    new = {}

    # get current quicksight users-groups mapping
    currentmembership = {}
    for group in groups:
        if group in currentmembership:
            pass
        else:
            currentmembership[group] = []

    users = list_users(account_id, aws_region)
    # print(users)
    for user in users:
        useralias = user['UserName'].split('/')[-1]
        useralias = useralias.split('@')[0]
        new[useralias] = user['UserName']
        # print(user['UserName'])
        usergroups = list_user_groups(user['UserName'], account_id, aws_region)
        if len(usergroups) == 0:
            if 'None' in currentmembership:
                currentmembership['None'].append(user['UserName'])
            else:
                currentmembership['None'] = []
                currentmembership['None'].append(user['UserName'])
        else:
            for group in usergroups:
                # print(group)
                if group['GroupName'] in currentmembership:
                    currentmembership[group['GroupName']].append(user['UserName'])
                else:
                    currentmembership[group['GroupName']] = []
                    currentmembership[group['GroupName']].append(user['UserName'])
    users = new
    # print(users)
    print(currentmembership)
    # build group-members mapping from membership file
    memberships = {}

    # load qs user role information
    roles = get_ssm_parameters('/qs/config/roles')
    print(roles)

    # load qs namespace information
    ns = get_ssm_parameters('/qs/config/ns')
    print(ns)

    # load group mapping information
    with open(path) as csv_file:
        members = csv.reader(csv_file, delimiter=',')
        for member in members:
            alias = member[1]
            email = member[2]
            # create group
            group = member[0]
            newgroup = 'quicksight-fed-' + group.lower()
            # print("process this group")
            # print(newgroup)
            if newgroup not in groups:
                print("Creating this new group:")
                print(newgroup)
                try:
                    response = create_group(newgroup, account_id, aws_region)
                except Exception as e:
                    if str(e).find('already exists.'):
                        # print(e)
                        pass
                    else:
                        raise e

            # handle every user
            if alias:
                # register user is user is new
                if alias not in users:
                    try:
                        response = register_user(aws_region, 'IAM', email, alias, account_id,
                                                 Arn='arn:aws:iam::' + account_id + ':role/quicksight-fed-us-users',
                                                 Session=email, NS=ns[group], Role=roles[group])
                        qs_usr_name = 'quicksight-fed-us-users/' + email
                        print(qs_usr_name + " is registered")
                    except Exception as e:
                        print(e)
                        pass

                    try:
                        response = create_group_membership(qs_usr_name, newgroup, account_id, aws_region)
                        print(qs_usr_name + " is added into " + newgroup)

                    except Exception as e:
                        if str(e).find('does not exist'):
                            # print(e)
                            pass
                        else:
                            raise e

                # add user into the group if user exists
                if alias in users:
                    qs_usr_name = users[alias]
                    email = users[alias].split('/')[-1]
                    # print(qs_usr_name)
                    # print(email)
                    if qs_usr_name not in currentmembership[newgroup]:
                        # print(qs_usr_name)
                        try:
                            response = create_group_membership(qs_usr_name, newgroup, account_id, aws_region)
                            print(qs_usr_name + " is added into " + newgroup)

                        except Exception as e:
                            if str(e).find('does not exist'):
                                # print(e)
                                pass
                            else:
                                raise e
                        # if newgroup in ['quicksight-fed-bi-admin']:
                        if group in roles:
                            print("update role")
                            try:
                                qs_client.update_user(
                                    UserName=qs_usr_name,
                                    AwsAccountId=account_id,
                                    Namespace=ns[group],
                                    Email=email,
                                    Role=roles[group]
                                )
                            except Exception as e:
                                if str(e).find('does not exist'):
                                    # print(e)
                                    pass
                                else:
                                    raise e
                        """elif newgroup in ['quicksight-fed-bi-developer',
                                          'quicksight-fed-power-reader']:
                            print("add new dev")
                            if qs_usr_name not in memberships['quicksight-fed-bi-admin']:
                                try:
                                    qs_client.update_user(
                                        UserName=qs_usr_name,
                                        AwsAccountId=account_id,
                                        Namespace='default',
                                        Email=email,
                                        Role='AUTHOR'
                                    )
                                except Exception as e:
                                    if str(e).find('does not exist'):
                                        # print(e)
                                        pass
                                    else:
                                        raise e"""

                # write current group-users mapping into a dict "membership"
                if newgroup in memberships:
                    if 'qs_usr_name' in locals():  # User in membership.csv already registered as a QS user
                        memberships[newgroup].append(qs_usr_name)
                    else:  # User in membership.csv do not register as a QS user yet
                        memberships[newgroup].append(alias)

                else:
                    memberships[newgroup] = []
                    if 'qs_usr_name' in locals():
                        memberships[newgroup].append(qs_usr_name)
                    else:
                        memberships[newgroup].append(alias)

    # remove current user permissions or memberships if membership file changed
    print(memberships)
    # currentmembership = {}
    users = list_users(account_id, aws_region)
    for user in users:
        # print(user['UserName'])
        groups = list_user_groups(user['UserName'], account_id, aws_region)
        # print(groups)
        if len(groups) == 0:
            # currentmembership['None'] = user['UserName']
            if user['UserName'].split("/", 1)[0] != 'Administrator':
                delete_user(user['UserName'], account_id, aws_region)
        else:
            for group in groups:
                # currentmembership[group['GroupName']] = user['UserName']
                if group['GroupName'] in memberships:
                    # print(group['GroupName'])
                    if user['UserName'] not in memberships[group['GroupName']]:
                        delete_group_membership(user['UserName'], group['GroupName'], account_id, aws_region)
                        print(user['UserName'] + " is removed from " + group['GroupName'])

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
    for permission in permissions:
        arn = 'arn:aws:quicksight:' + aws_region + ':' + account_id + ":group/" + ns[
            permission['Group_Name']] + "/quicksight-fed-" + permission[
                  'Group_Name'].lower()
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
                    if len(ids) > 0:
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
        # revoke dashboard access of a group
        group = "quicksight-fed-" + permission['Group_Name'].lower()
        print(reportlist)
        # get dashboards list
        dashboards = list_dashboards(account_id, lambda_aws_region)
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

    # get current quicksight groups
    """groups = list_groups(account_id, aws_region)
    new = []
    for group in groups:
        new.append(group['GroupName'])
    groups = new
    new = []
    # get current quicksight users-groups mapping
    currentmembership = {}
    for group in groups:
        if group in currentmembership:
            pass
        else:
            currentmembership[group] = []

    users = list_users(account_id, aws_region)
    for user in users:
        new.append(user['UserName'])
        print(user['UserName'])
        usergroups = list_user_groups(user['UserName'], account_id, aws_region)
        if len(usergroups) == 0:
            if 'None' in currentmembership:
                currentmembership['None'].append(user['UserName'])
            else:
                currentmembership['None'] = []
                currentmembership['None'].append(user['UserName'])
        else:
            for group in usergroups:
                # print(group)
                if group['GroupName'] in currentmembership:
                    currentmembership[group['GroupName']].append(user['UserName'])
                else:
                    currentmembership[group['GroupName']] = []
                    currentmembership[group['GroupName']].append(user['UserName'])
    print("here it is current users mapping:")
    print(currentmembership)"""
