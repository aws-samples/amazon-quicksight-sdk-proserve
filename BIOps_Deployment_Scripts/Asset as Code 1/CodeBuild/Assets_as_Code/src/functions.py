"""
This file contains all the functions related to QS services.
1st version: 2021-10
Author: Ying Wang
Email: ywangufl@gmail.com
github id: ywang103
2nd version: 2021-12
Author: AWS proserve and 3M alchemist
"""

import hashlib
import traceback
import boto3
import botocore.exceptions
import botocore.session
import gzip, json
import time
import logging
import csv
import os
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional

from Assets_as_Code.src import supportive_functions as s_func

from datetime import date, datetime

"""
list functions to get list of qs objects
"""


def list_data_sources(session):
    qs = session.client('quicksight')
    sts_client = session.client("sts")
    account_id = sts_client.get_caller_identity()["Account"]
    datasources = []
    response = qs.list_data_sources(AwsAccountId=account_id)
    next_token: str = response.get("NextToken", None)
    datasources += response["DataSources"]
    while next_token is not None:
        response = qs.list_data_sources(AwsAccountId=account_id, NextToken=next_token)
        next_token = response.get("NextToken", None)
        datasources += response["DataSources"]
    return datasources


def list_data_sets(session):
    qs = session.client('quicksight')
    sts_client = session.client("sts")
    account_id = sts_client.get_caller_identity()["Account"]
    datasets = []
    response = qs.list_data_sets(AwsAccountId=account_id)
    next_token: str = response.get("NextToken", None)
    datasets += response["DataSetSummaries"]
    while next_token is not None:
        response = qs.list_data_sets(AwsAccountId=account_id, NextToken=next_token)
        next_token = response.get("NextToken", None)
        datasets += response["DataSetSummaries"]
    return datasets


def list_namespaces(session) -> List[Dict[str, Any]]:
    qs = session.client('quicksight')
    sts_client = session.client("sts")
    account_id = sts_client.get_caller_identity()["Account"]
    namespaces = []
    response = qs.list_namespaces(AwsAccountId=account_id)
    next_token: str = response.get("NextToken", None)
    namespaces += response["Namespaces"]
    while next_token is not None:
        response = qs.list_namespaces(AwsAccountId=account_id, NextToken=next_token)
        next_token = response.get("NextToken", None)
        namespaces += response["Namespaces"]
    return namespaces


def list_folders(session) -> List[Dict[str, Any]]:
    qs = session.client('quicksight')
    sts_client = session.client("sts")
    account_id = sts_client.get_caller_identity()["Account"]
    folders = []
    response = qs.list_folders(AwsAccountId=account_id)
    next_token: str = response.get("NextToken", None)
    folders += response["FolderSummaryList"]
    while next_token is not None:
        response = qs.list_folders(AwsAccountId=account_id, NextToken=next_token)
        next_token = response.get("NextToken", None)
        folders += response["FolderSummaryList"]
    return folders


def list_templates(session):
    qs = session.client('quicksight')
    sts_client = session.client("sts")
    account_id = sts_client.get_caller_identity()["Account"]
    token = None

    args: Dict[str, Any] = {
        "AwsAccountId": account_id,
        "MaxResults": 100,
    }

    tlist = qs.list_templates(**args)

    templates = tlist['TemplateSummaryList']

    if 'NextToken' in tlist:
        token = tlist['NextToken']
        while token is not None:
            args["NextToken"] = token
            tlist = qs.list_templates(**args)
            templates.append(tlist['TemplateSummaryList'])
            token = tlist.get("NextToken", None)
    else:
        pass
    # print('token is none. No further action.')

    return templates


def list_dashboards(session) -> List[Dict[str, Any]]:
    qs = session.client('quicksight')
    sts_client = session.client("sts")
    account_id = sts_client.get_caller_identity()["Account"]
    dashboards = []
    response = qs.list_dashboards(AwsAccountId=account_id)
    next_token: str = response.get("NextToken", None)
    dashboards += response["DashboardSummaryList"]
    while next_token is not None:
        response = qs.list_dashboards(AwsAccountId=account_id, NextToken=next_token)
        next_token = response.get("NextToken", None)
        dashboards += response["DashboardSummaryList"]
    return dashboards


def list_analysis(session):
    qs = session.client('quicksight')
    sts_client = session.client("sts")
    account_id = sts_client.get_caller_identity()["Account"]
    analysis = []
    response = qs.list_analyses(AwsAccountId=account_id)
    next_token: str = response.get("NextToken", None)
    analysis += response["AnalysisSummaryList"]
    while next_token is not None:
        response = qs.list_analyses(AwsAccountId=account_id, NextToken=next_token)
        next_token = response.get("NextToken", None)
        analysis += response["AnalysisSummaryList"]
    return analysis


def list_folder_members(session, FID):
    qs = session.client('quicksight')
    sts_client = session.client("sts")
    account_id = sts_client.get_caller_identity()["Account"]
    folder_members = []
    response = qs.list_folder_members(
        AwsAccountId=account_id,
        FolderId=FID)
    next_token: str = response.get("NextToken", None)
    folder_members += response["FolderMemberList"]
    while next_token is not None:
        response = qs.list_folder_members(AwsAccountId=account_id, FolderId=FID, NextToken=next_token)
        next_token = response.get("NextToken", None)
        folder_members += response["FolderMemberList"]
    return folder_members


def list_themes(session):
    qs = session.client('quicksight')
    sts_client = session.client("sts")
    account_id = sts_client.get_caller_identity()["Account"]
    themes = []
    response = qs.list_themes(AwsAccountId=account_id)
    next_token: str = response.get("NextToken", None)
    themes += response["ThemeSummaryList"]
    while next_token is not None:
        response = qs.list_themes(AwsAccountId=account_id, NextToken=next_token)
        next_token = response.get("NextToken", None)
        themes += response["ThemeSummaryList"]
    return themes


"""
desc functions to get contents of an asset
"""


def describe_data_source(session, DSID):
    qs = session.client('quicksight')
    sts_client = session.client("sts")
    AccountId = sts_client.get_caller_identity()["Account"]
    response = qs.describe_data_source(
        AwsAccountId=AccountId,
        DataSourceId=DSID)
    return response


def describe_data_set(session, DSID):
    qs = session.client('quicksight')
    sts_client = session.client("sts")
    AccountId = sts_client.get_caller_identity()["Account"]
    response = qs.describe_data_set(
        AwsAccountId=AccountId,
        DataSetId=DSID)
    return response


def describe_dashboard(session, dashboard):
    qs = session.client('quicksight')
    sts_client = session.client("sts")
    account_id = sts_client.get_caller_identity()["Account"]
    try:
        response = qs.describe_dashboard(
            AwsAccountId=account_id,
            DashboardId=dashboard)
    except Exception as e:
        return ('Faild to describe dashboard: ' + str(e))
    else:
        return response


def describe_template(session, tid):
    qs = session.client('quicksight')
    sts_client = session.client("sts")
    account_id = sts_client.get_caller_identity()["Account"]
    response = qs.describe_template(
        AwsAccountId=account_id,
        TemplateId=tid)
    return response


def describe_analysis(session, analysis):
    qs = session.client('quicksight')
    sts_client = session.client("sts")
    account_id = sts_client.get_caller_identity()["Account"]
    try:
        response = qs.describe_analysis(
            AwsAccountId=account_id,
            AnalysisId=analysis)
    except Exception as e:
        return ('Faild to describe analysis: ' + str(e))
    else:
        return response


def describe_theme(session, THEMEID):
    qs = session.client('quicksight')
    sts_client = session.client("sts")
    AccountId = sts_client.get_caller_identity()["Account"]
    response = qs.describe_theme(
        AwsAccountId=AccountId,
        ThemeId=THEMEID)
    return response


def describe_folder(session, folderID):
    qs = session.client('quicksight')
    sts_client = session.client("sts")
    AccountId = sts_client.get_caller_identity()["Account"]
    response = qs.describe_folder(
        AwsAccountId=AccountId,
        FolderId=folderID)
    return response


def describe_analysis_definition(session, id):
    qs = session.client('quicksight')
    sts_client = session.client("sts")
    account_id = sts_client.get_caller_identity()["Account"]
    try:
        response = qs.describe_analysis_definition(
            AwsAccountId=account_id,
            AnalysisId=id)
    except Exception as e:
        return ('Faild to describe analysis: ' + str(e))
    else:
        return response


# RG EDIT
def describe_dashboard_definition(session, id):
    qs = session.client('quicksight')
    sts_client = session.client("sts")
    account_id = sts_client.get_caller_identity()["Account"]
    try:
        response = qs.describe_dashboard_definition(
            AwsAccountId=account_id,
            DashboardId=id)
    except Exception as e:
        return ('Failed to describe dashboard: ' + str(e))
    else:
        return response


def describe_analysis_permissions(session, analysis):
    qs = session.client('quicksight')
    sts_client = session.client("sts")
    account_id = sts_client.get_caller_identity()["Account"]
    try:
        response = qs.describe_analysis_permissions(
            AwsAccountId=account_id,
            AnalysisId=analysis)
    except Exception as e:
        return ('Failed to describe analysis: ' + str(e))
    else:
        return response


def describe_theme_permissions(session, THEMEID):
    qs = session.client('quicksight')
    sts_client = session.client("sts")
    account_id = sts_client.get_caller_identity()["Account"]

    response = qs.describe_theme_permissions(
        AwsAccountId=account_id,
        ThemeId=THEMEID
    )
    return response

def describe_namespace(session, namespace):
    qs = session.client('quicksight')
    sts_client = session.client("sts")
    account_id = sts_client.get_caller_identity()["Account"]

    response = qs.describe_namespace(
        AwsAccountId=account_id,
        Namespace=namespace
    )
    return response['Namespace']


def describe_namespace(session, namespace):
    qs = session.client('quicksight')
    sts_client = session.client("sts")
    account_id = sts_client.get_caller_identity()["Account"]

    response = qs.describe_namespace(
        AwsAccountId=account_id,
        Namespace=namespace
    )
    return response['Namespace']


"""
create functions to create assets
"""


def create_data_source(source, session, target):
    qs = session.client('quicksight')
    sts_client = session.client("sts")
    account_id = sts_client.get_caller_identity()["Account"]
    credential = None

    # https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/quicksight.html#QuickSight.Client.create_data_source
    conn_dict = {
        "aurora": "AuroraParameters",
        "aurora_postgresql": "AuroraPostgreSqlParameters",
        "mariadb": "MariaDbParameters",
        "mysql": "MySqlParameters",
        "postgresql": "PostgreSqlParameters",
        "sqlserver": "SqlServerParameters"
    }

    # rds
    if source['Type'].lower() in [
        'aurora', 'aurora_postgresql', 'mariadb', 'mysql', 'postgresql',
        'sqlserver'] and 'RdsParameters' in source['DataSourceParameters']:
        # Update data source instance name
        instance_id = source['DataSourceParameters']['RdsParameters']
        instance_id['InstanceId'] = target['rds']['rdsinstanceid']
        credential = target['credential']['rdscredential']
    elif source['Type'].lower() in [
        'aurora', 'aurora_postgresql', 'mariadb', 'mysql', 'postgresql',
        'sqlserver'] and conn_dict.get(source['Type'].lower()) in source['DataSourceParameters']:
        # Update data source parameters
        conn_name = conn_dict.get(source['Type'].lower())
        conn_params = source['DataSourceParameters'][conn_name]
        conn_params['Host'] = target['rds']['rdsinstanceid']
        credential = target['credential']['rdscredential']

        # redshift
    if source['Type'] == "REDSHIFT":

        # Update data source instance name
        Cluster = source['DataSourceParameters']['RedshiftParameters']
        if 'ClusterId' in Cluster:
            Cluster['ClusterId'] = target['redshift']['ClusterId']
        Cluster['Host'] = target['redshift']['Host']
        if target['redshift']['Database'] is not None and 'Database' in Cluster:
            Cluster['Database'] = target['redshift']['Database']
        credential = target['credential']['redshiftcredential']

    if 'VpcConnectionProperties' in source and target['vpc'] is not None:
        source['VpcConnectionProperties']['VpcConnectionArn'] = target['vpc']
    elif 'VpcConnectionProperties' in source and target['vpc'] is None:
        raise Exception("Sorry, you need the targetvpc information")

    args: Dict[str, Any] = {
        "AwsAccountId": account_id,
        "DataSourceId": source['DataSourceId'],
        "Name": source['Name'],
        "Type": source['Type'],
    }

    if "SslProperties" in source:
        args["SslProperties"] = source['SslProperties']

    if 'DataSourceParameters' in source:
        args["DataSourceParameters"] = source['DataSourceParameters']

    if target['tag'] is not None:
        args["Tags"] = target['tag']

    if credential is not None:
        args["Credentials"] = credential

    if 'VpcConnectionProperties' in source:
        args["VpcConnectionProperties"] = source['VpcConnectionProperties']

    args["Permissions"] = target['datasourcepermission']

    try:
        NewSource = qs.create_data_source(**args)
        return NewSource
    except Exception as e:
        error = {"DataSource": args, "Error": str(e)}
        return error


# AccountId string; DataSetId string; Name string; Physical: json; Logical: json; Mode: string;
# ColumnGroups: json array; Permissions: json array; RLS: json; Tags: json array
def create_data_set(session, DataSetId, Name, Physical, Logical, Mode, ColumnGroups=None,
                    FieldFolders=None):
    qs = session.client('quicksight')
    sts_client = session.client("sts")
    AccountId = sts_client.get_caller_identity()["Account"]
    args: Dict[str, Any] = {
        "AwsAccountId": AccountId,
        "DataSetId": DataSetId,
        "Name": Name,
        "PhysicalTableMap": Physical,
        "LogicalTableMap": Logical,
        "ImportMode": Mode
    }
    if ColumnGroups:
        args["ColumnGroups"] = ColumnGroups
    if FieldFolders:
        args["FieldFolders"] = FieldFolders
    response = qs.create_data_set(**args)
    return response


def create_template(session, TemplateId, tname, dsref, sourceanalysis, version):
    qs = session.client('quicksight')
    sts_client = session.client("sts")
    account_id = sts_client.get_caller_identity()["Account"]
    try:
        delete_template(session, TemplateId)
    except Exception:
        print(traceback.format_exc())
    # assert isinstance(TemplateId, int), ''
    finally:
        response = qs.create_template(
            AwsAccountId=account_id,
            TemplateId=TemplateId,
            Name=tname,
            SourceEntity={
                'SourceAnalysis': {
                    'Arn': sourceanalysis,
                    'DataSetReferences': dsref
                }
            },
            VersionDescription=version
        )
        return response


def create_dashboard(session, dashboard_id, source_id, name, source, filter='ENABLED',
                     csv='ENABLED', sheetcontrol='EXPANDED', *components):
    qs = session.client('quicksight')
    sts_client = session.client("sts")
    account_id = sts_client.get_caller_identity()["Account"]
    args: Dict[str, Any] = {
        "AwsAccountId": account_id,
        "DashboardId": dashboard_id,
        "Name": name,
        "SourceEntity": {
            "Definition": {
                "DataSetIdentifierDeclarations": source['Definition']['DataSetIdentifierDeclarations']
            }
        },
        "DashboardPublishOptions": {
            'AdHocFilteringOption': {
                'AvailabilityStatus': filter
            },
            'ExportToCSVOption': {
                'AvailabilityStatus': csv
            },
            'SheetControlsOption': {
                'VisibilityState': sheetcontrol
            }
        }
    }
    # Add non-required params
    # TODO: Uncomment out first line when bugfix for dashboard definition is in
    rawsource_parameters = ["CalculatedFields", "ColumnConfigurations", "DefaultConfiguration", "FilterGroups",
                            "Sheets", "ParameterDeclarations"]
    for param in rawsource_parameters:
        if param in source['Definition'].keys():
            args['SourceEntity']['Definition'][param] = source['Definition'][param]

    for component in components:
        if component[0] == 'ThemeArn':
            if component[1] == '':
                continue
            args['ThemeArn'] = component[1]
        if component[0] == 'Parameters':
            args['Parameters'] = component[1]
        if component[0] == 'Tags':
            args['Tags'] = component[1]
        if component[0] == 'VersionDescription':
            args['VersionDescription'] = component[1]

    # Describe definition returns SheetId, ElementId, VisualId as DashboardId_GUID
    # Edit these values from DashboardId_GUID -> GUID
    args_str = json.dumps(args)
    args = json.loads(args_str.replace(source_id + '_', ''))
    response = qs.create_dashboard(**args)
    return response


def create_analysis(session, analysis_id, name, source, *components):
    qs = session.client('quicksight')
    sts_client = session.client("sts")
    account_id = sts_client.get_caller_identity()["Account"]
    args: Dict[str, Any] = {
        "AwsAccountId": account_id,
        "AnalysisId": analysis_id,
        "Name": name,
        "SourceEntity": {
            "Definition": {
                "DataSetIdentifierDeclarations": source['Definition']['DataSetIdentifierDeclarations']
            }
        }
    }
    # Add non-required params
    rawsource_parameters = ["CalculatedFields", "ColumnConfigurations", "DefaultConfigurations", "FilterGroups",
                            "Sheets", "ParameterDeclarations"]
    for param in rawsource_parameters:
        if param in source.keys():
            args['SourceEntity']['Definition'][param] = source['Definition'][param]

    for component in components:
        if component[0] == 'ThemeArn':
            args['ThemeArn'] = component[1]
        if component[0] == 'Parameters':
            args['Parameters'] = component[1]
        if component[0] == 'Tags':
            args['Tags'] = component[1]
    response = qs.create_analysis(**args)
    return response


def create_theme(session, THEMEID, Name, BaseThemeId, Configuration):
    qs = session.client('quicksight')
    sts_client = session.client("sts")
    AccountId = sts_client.get_caller_identity()["Account"]
    response = qs.create_theme(
        AwsAccountId=AccountId,
        ThemeId=THEMEID,
        Name=Name,
        BaseThemeId=BaseThemeId,
        Configuration=Configuration
    )
    return response


def create_folder_membership(session, folderID, memberID, memberType):
    qs = session.client('quicksight')
    sts_client = session.client("sts")
    account_id = sts_client.get_caller_identity()["Account"]
    response = qs.create_folder_membership(
        AwsAccountId=account_id,
        FolderId=folderID,
        MemberId=memberID,
        MemberType=memberType
    )
    return response


"""
copy functions
"""


def copy_template(session, TemplateId, tname, SourceTemplatearn):
    qs = session.client('quicksight')
    sts_client = session.client("sts")
    account_id = sts_client.get_caller_identity()["Account"]
    try:
        delete_template(session, TemplateId)
    except Exception:
        print(traceback.format_exc())
    # assert isinstance(TemplateId, int), ''
    finally:
        response = qs.create_template(
            AwsAccountId=account_id,
            TemplateId=TemplateId,
            Name=tname,
            SourceEntity={
                'SourceTemplate': {
                    'Arn': SourceTemplatearn
                }
            },
            VersionDescription='1'
        )
        return response


# RG ADDED - NEED TO REVISIT
def copy_dashboard(session, dashboardContents, Id, Name, region='us-east-1'):
    qs = session.client('quicksight')
    sts_client = session.client("sts")
    AccountId = sts_client.get_caller_identity()["Account"]

    sheets = dashboardContents['Version']['Sheets']
    # print(sheets)
    for sheet in sheets:
        # print(sheet['SheetId'])
        sheetid = sheet['SheetId'].split('_')[1]
        # print(sheetid)
        sheet['SheetId'] = sheetid
        # print(sheet['SheetId'])
        # print(sheet)

    '''sourceEntityArn = dashboardContents['Version']['SourceEntityArn']
    analysisid = sourceEntityArn.split('/')[1]
    print(analysisid)

    source = describe_analysis_definition(session, analysisid)'''

    args: Dict[str, Any] = {
        "AwsAccountId": AccountId,
        "DashboardId": Id,
        "Name": Name,
        # "ThemeArn": source['ThemeArn'],
        "SourceEntity": {
            "Definition": {
                "DataSetIdentifierDeclarations": dashboardContents['Version']['Definition'][
                    'DataSetIdentifierDeclarations'],
                "Sheets": dashboardContents['Version']['Definition']['Sheets'],
                "CalculatedFields": dashboardContents['Version']['Definition']['CalculatedFields'],
                "ParameterDeclarations": dashboardContents['Version']['Definition']['ParameterDeclarations'],
                "FilterGroups": dashboardContents['Version']['Definition']['FilterGroups']
            }
        }
    }
    response = qs.create_dashboard(**args)  # Use the existing function in this API py script
    return response


def copy_analysis(session, source, Id, Name, region='us-east-1'):
    qs = session.client('quicksight')
    sts_client = session.client("sts")
    AccountId = sts_client.get_caller_identity()["Account"]
    args: Dict[str, Any] = {
        "AwsAccountId": AccountId,
        "AnalysisId": Id,
        "Name": Name,
        "ThemeArn": source['Analysis']['ThemeArn'],
        "SourceEntity": {
            "Definition": {
                "DataSetIdentifierDeclarations": source['Definition']['DataSetIdentifierDeclarations'],
                "Sheets": source['Definition']['Sheets'],
                "CalculatedFields": source['Definition']['CalculatedFields'],
                "ParameterDeclarations": source['Definition']['ParameterDeclarations'],
                "FilterGroups": source['Definition']['FilterGroups'],
                "DefaultConfiguration": source['Definition']['DefaultConfiguration']
            }
        }
    }
    if "Parameters" in source:
        args["Parameters"] = source["Parameters"]
    response = qs.create_analysis(**args)
    return response


"""
update functions to update an asset
"""


# AccountId string; DataSetId string; Name string; Physical: json; Logical: json; Mode: string;
# ColumnGroups: json array; Permissions: json array; RLS: json; Tags: json array
def update_dataset(session, DataSetId, Name, Physical, Logical, Mode, ColumnGroups=None):
    qs = session.client('quicksight')
    sts_client = session.client("sts")
    AccountId = sts_client.get_caller_identity()["Account"]
    args: Dict[str, Any] = {
        "AwsAccountId": AccountId,
        "DataSetId": DataSetId,
        "Name": Name,
        "PhysicalTableMap": Physical,
        "LogicalTableMap": Logical,
        "ImportMode": Mode
    }
    if ColumnGroups:
        args["ColumnGroups"] = ColumnGroups
    response = qs.update_data_set(**args)
    return response


def update_template_permission(session, TemplateId, Principal):
    qs = session.client('quicksight')
    sts_client = session.client("sts")
    account_id = sts_client.get_caller_identity()["Account"]
    response = qs.update_template_permissions(
        AwsAccountId=account_id,
        TemplateId=TemplateId,
        GrantPermissions=[
            {
                'Principal': Principal,
                'Actions': [
                    'quicksight:DescribeTemplate',
                ]
            }
        ]
    )
    return response


def update_dashboard(session, dashboard, name, SourceEntity, version, filter='ENABLED', csv='ENABLED',
                     sheetcontrol='EXPANDED'):
    qs = session.client('quicksight')
    sts_client = session.client("sts")
    account_id = sts_client.get_caller_identity()["Account"]
    args: Dict[str, Any] = {
        "AwsAccountId": account_id,
        "DashboardId": dashboard,
        "Name": name,
        "SourceEntity": SourceEntity,
        "VersionDescription": version,
        "DashboardPublishOptions": {
            'AdHocFilteringOption': {
                'AvailabilityStatus': filter
            },
            'ExportToCSVOption': {
                'AvailabilityStatus': csv
            },
            'SheetControlsOption': {
                'VisibilityState': sheetcontrol
            }
        }
    }
    response = qs.update_dashboard(**args)

    return response


# RG ADDED
def update_dashboards_published_version(session, dashboard, version):
    qs = session.client('quicksight')
    sts_client = session.client("sts")
    account_id = sts_client.get_caller_identity()["Account"]

    response = qs.update_dashboard_published_version(
        AwsAccountId=account_id,
        DashboardId=dashboard,
        VersionNumber=version)

    return response


def update_data_source_permissions(session, datasourceid, Principal):
    qs = session.client('quicksight')
    sts_client = session.client("sts")
    account_id = sts_client.get_caller_identity()["Account"]
    response = qs.update_data_source_permissions(
        AwsAccountId=account_id,
        DataSourceId=datasourceid,
        GrantPermissions=[
            {
                'Principal': Principal,
                'Actions': ["quicksight:DescribeDataSource",
                            "quicksight:DescribeDataSourcePermissions",
                            "quicksight:PassDataSource",
                            "quicksight:UpdateDataSource",
                            "quicksight:DeleteDataSource",
                            "quicksight:UpdateDataSourcePermissions"]
            },
        ]
    )
    return response


def update_data_set_permissions(session, datasetid, Principal):
    qs = session.client('quicksight')
    sts_client = session.client("sts")
    account_id = sts_client.get_caller_identity()["Account"]
    response = qs.update_data_set_permissions(
        AwsAccountId=account_id,
        DataSetId=datasetid,
        GrantPermissions=[
            {
                'Principal': Principal,
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
    return response


def update_analysis(session, id, name, source, *components):
    qs = session.client('quicksight')
    sts_client = session.client("sts")
    account_id = sts_client.get_caller_identity()["Account"]
    args: Dict[str, Any] = {
        "AwsAccountId": account_id,
        "AnalysisId": id,
        "Name": name,
        "ThemeArn": source['Analysis']['ThemeArn'],
        "SourceEntity": {
            "Definition": {
                "DataSetIdentifierDeclarations": source['Definition']['DataSetIdentifierDeclarations'],
                "Sheets": source['Definition']['Sheets'],
                "CalculatedFields": source['Definition']['CalculatedFields'],
                "ParameterDeclarations": source['Definition']['ParameterDeclarations'],
                "FilterGroups": source['Definition']['FilterGroups'],
                "DefaultConfiguration": source['Definition']['DefaultConfiguration']
            }
        }
    }
    for component in components:
        if component[0] == 'Parameters':
            args["Parameters"] = component[1]
        elif component[0] == 'ThemeArn':
            args["ThemeArn"] = component[1]
        else:
            args["SourceEntity"]["Definition"][component[0]].append(component[1])
    response = qs.update_analysis(**args)
    return response


def update_theme(session, THEMEID, name, BaseThemeId, Configuration=None):
    qs = session.client('quicksight')
    sts_client = session.client("sts")
    account_id = sts_client.get_caller_identity()["Account"]

    response = qs.update_theme(
        AwsAccountId=account_id,
        ThemeId=THEMEID,
        Name=name,
        BaseThemeId=BaseThemeId,
        Configuration=Configuration
    )
    return response


def update_theme_permissions(session, THEMEID):
    qs = session.client('quicksight')
    sts_client = session.client("sts")
    account_id = sts_client.get_caller_identity()["Account"]
    response = qs.update_theme_permissions(
        AwsAccountId=account_id,
        ThemeId=THEMEID
    )
    return response


"""
delete functions to delete an asset
"""


def delete_source(session, DataSourceId):
    qs = session.client('quicksight')
    sts_client = session.client("sts")
    AccountId = sts_client.get_caller_identity()["Account"]
    delsource = qs.delete_data_source(
        AwsAccountId=AccountId,
        DataSourceId=DataSourceId)
    return delsource


def delete_dataset(session, DataSetId):
    qs = session.client('quicksight')
    sts_client = session.client("sts")
    AccountId = sts_client.get_caller_identity()["Account"]
    response = qs.delete_data_set(
        AwsAccountId=AccountId,
        DataSetId=DataSetId)
    return response


def delete_template(session, tid, version=None):
    qs = session.client('quicksight')
    sts_client = session.client("sts")
    AccountId = sts_client.get_caller_identity()["Account"]
    args: Dict[str, Any] = {
        "AwsAccountId": AccountId,
        "TemplateId": tid,
    }
    if version:
        args["VersionNumber"] = version

    response = qs.delete_template(**args)
    return response


def delete_dashboard(session, did):
    qs = session.client('quicksight')
    sts_client = session.client("sts")
    account_id = sts_client.get_caller_identity()["Account"]
    response = qs.delete_dashboard(
        AwsAccountId=account_id,
        DashboardId=did)
    return response


def delete_analysis(session, did):
    qs = session.client('quicksight')
    sts_client = session.client("sts")
    account_id = sts_client.get_caller_identity()["Account"]
    response = qs.delete_analysis(
        AwsAccountId=account_id,
        AnalysisId=did)
    return response


def delete_theme(session, THEMEID):
    qs = session.client('quicksight')
    sts_client = session.client("sts")
    AccountId = sts_client.get_caller_identity()["Account"]
    response = qs.delete_theme(
        AwsAccountId=AccountId,
        ThemeId=THEMEID)
    return response


def delete_folder_membership(session, folderID, memberID, memberType):
    qs = session.client('quicksight')
    sts_client = session.client("sts")
    account_id = sts_client.get_caller_identity()["Account"]
    response = qs.delete_folder_membership(
        AwsAccountId=account_id,
        FolderId=folderID,
        MemberId=memberID,
        MemberType=memberType
    )
    return response


"""
Deployment functions
"""

def search_folders(session, FARN):
    qs = session.client('quicksight')
    sts_client = session.client("sts")
    account_id = sts_client.get_caller_identity()["Account"]
    response = qs.search_folders(
        AwsAccountId=account_id,
        Filters=[
            {
                'Operator': 'StringEquals',
                'Name': 'PARENT_FOLDER_ARN',
                'Value': FARN
            }
        ]
    )
    return response['FolderSummaryList']


def incremental_migration(accountid, awsrole, env, region, package, logs, log_group, error_log, success_log, now,
                          filepath):
    # Get target session
    target_session = s_func._assume_role(accountid, awsrole, region)
    print(package)
    theme_dir = filepath + "Theme/"
    datasets_dir = filepath + "Dataset/"
    dashboard_dir = filepath + "Dashboard/"
    folder_struct = filepath + "Mapping/folder_structure.json"
    delete_assets_path = filepath + "Mapping/delete_asset.json"
    delete_folder_members = filepath + "Mapping/delete_folder_membership.json"
    create_folder_members = filepath + "Mapping/create_folder_membership.json"

    # results output location
    success_location, fail_location = results_output_location()
    faillist = []

    # Perform incremental migration on themes to target account
    try:
        if len(os.listdir(theme_dir)) > 0:
            result = migrate_themes(now, accountid, env, package, target_session, theme_dir, logs, log_group, error_log,
                                    success_log)
            if result:
                faillist.append(result)
            print('Themes migrated')
        else:
            print('No themes to migrate')
    except:
        print('Theme migrate error')

    # Load files from nexus package
    try:
        # Load folder structure json static file
        with open(folder_struct, "r") as f:
            res = json.load(f)
            message = {"account_id": accountid, "package": package, "deployment_time": now,
                       "success": "folder_structure.json loaded successfully"}
            log_events_to_cloudwatch(message, logs, log_group, success_log)

        # Load assets from Release/Create folder of Source Account
        with open(create_folder_members, "r") as f:
            create_members_json = json.load(f)
            message = {"account_id": accountid, "package": package, "deployment_time": now,
                       "success": "create_folder_membership.json loaded successfully"}
            log_events_to_cloudwatch(message, logs, log_group, success_log)

        # Load assets from Release/Remove folder of Source Account
        with open(delete_folder_members, "r") as f:
            delete_members_json = json.load(f)
            message = {"account_id": accountid, "package": package, "deployment_time": now,
                       "success": "delete_folder_membership.json loaded successfully"}
            log_events_to_cloudwatch(message, logs, log_group, success_log)

        # Load assets from Release/Delete folder of Source Account
        with open(delete_assets_path, "r") as f:
            delete_assets_json = json.load(f)
            message = {"account_id": accountid, "package": package, "deployment_time": now,
                       "success": "delete_assets.json loaded successfully"}
            log_events_to_cloudwatch(message, logs, log_group, success_log)
        print('Asset files loaded')
    except Exception:
        message = {"account_id": accountid, "package": package, "deployment_time": now, "error": str(Exception)}
        faillist.append(message)
        print('Error loading files: ' + str(Exception))
        log_events_to_cloudwatch(message, logs, log_group, error_log)
        sys.exit(1)
    qs = target_session.client('quicksight')
    namespaces = []
    if accountid != '694267443573':
        namespaces = list_namespaces(target_session)
    else:
        namespaces = [describe_namespace(target_session, 'u3npnp_390_Model'),
                      describe_namespace(target_session, 'u3npnp_390_Model2'),
                      describe_namespace(target_session, 'u3npnp_390_biat_55298')]
    for namespace in namespaces:
        try:
            namespace_name = namespace['Name']
            if namespace_name == 'default':
                continue
            print('Migrating assets to: ' + namespace_name)
            namespace_hash = hashlib.md5(namespace_name.encode('utf-8')).hexdigest()

            # Check folder structure of target namespace
            parent_folder_arn = 'arn:aws:quicksight:' + region + ':' + accountid + ':folder/' + namespace_hash
            search_folders(target_session, parent_folder_arn)
            log_events_to_cloudwatch(
                {"account_id": accountid, "package": package, "deployment_time": now, "namespace": namespace,
                 "hashed_namespace": namespace_hash,
                 "parent_folder_arn": parent_folder_arn, "success": "Parent folder exists"}, logs, log_group,
                success_log)

            folder_mismatch = validate_folder_hierarchy(now, res, package, namespace_name, namespace_hash, region,
                                                        accountid,
                                                        target_session,
                                                        [], logs, log_group, error_log, success_log)
            print(namespace_name + ': Folder structure validated')

            if len(folder_mismatch) > 0:
                faillist.append(folder_mismatch)
                raise Exception(folder_mismatch)

            # Start migration of dashboards and datasets if there are no issues with folder structure
            # Perform incremental migration on datasets to target account namespaces
            if len(os.listdir(datasets_dir)) > 0:
                result = migrate_data_sets(now, accountid, package, target_session, region, datasets_dir,
                                           namespace_name, namespace_hash, logs, log_group, error_log, success_log)
                if result:
                    faillist.append(result)
            print(namespace_name + ': Datasets migrated')

            # Perform incremental migration on dashboards to target account namespaces
            if len(os.listdir(dashboard_dir)) > 0:
                result = migrate_dashboards(now, accountid, package, target_session, region, dashboard_dir,
                                            namespace_name, namespace_hash, logs, log_group, error_log, success_log)
                if result:
                    faillist.append(result)
            print(namespace_name + ': Dashboards migrated')

            # Creating folder memberships for assets of target namespace
            result = create_folder_membership_of_assets(now, create_members_json, accountid, package, namespace_name,
                                                        namespace_hash,
                                                        target_session, [], logs, log_group, error_log, success_log)
            if result:
                faillist.append(result)
            print(namespace_name + ': Folder memberships created')

            # Removing folder memberships for assets of target namespace
            result = delete_folder_membership_of_assets(now, delete_members_json, accountid, package, namespace_name,
                                                        namespace_hash,
                                                        target_session, [], logs, log_group, error_log, success_log)
            if result:
                faillist.append(result)
            print(namespace_name + ': Folder memberships removed')

            # Deleting assets in target namespaces
            result = delete_assets(now, delete_assets_json, accountid, package, namespace_name, namespace_hash,
                                   target_session, [],
                                   logs, log_group, error_log, success_log)
            if result:
                faillist.append(result)
            print(namespace_name + ': Assets deleted')

            print('Finished migrating assets to: ' + namespace_name)

        except Exception as e:
            error = {"account_id": accountid, "package": package, "deployment_time": now, "namespace": namespace,
                     "hashed_namespace": namespace_hash, "error": e}
            log_events_to_cloudwatch(error, logs, log_group, error_log)
            continue
    if faillist != []:
        failure_file = fail_location + now + 'fail_results_incremental.gz'
        with gzip.open(failure_file, 'at', encoding='utf-8') as fout:
            for list_item in faillist:
                for dict in list_item:
                    json.dump(dict, fout, sort_keys=True, default=str)
                    fout.write('\n')

        # Upload failure file to S3
        key = 'admin-console/monitoring/quicksight/deployment_results/incremental/deployment_results_' + now + '.gz'
        s_func.send_to_s3('3m-his-' + env + '-390-biat-tool', 'alias/' + env + '-biat-tool-KMS', key, failure_file, target_session)

        raise Exception('Did not deploy to all namespaces successfully')

def log_events_to_cloudwatch(message, logs, log_group, log_stream):
    # Check if log stream exists
    timestamp = int(round(time.time() * 1000))
    exists = False
    stream_list = logs.describe_log_streams(logGroupName=log_group, logStreamNamePrefix=log_stream)['logStreams']
    for stream in stream_list:
        if stream['logStreamName'] == log_stream:
            exists = True
            sequence_token = stream['uploadSequenceToken']
        break

    if exists:
        log_events = [{'timestamp': timestamp, 'message': str(message)}]
        logs.put_log_events(logGroupName=log_group, logStreamName=log_stream, logEvents=log_events,
                            sequenceToken=sequence_token)
    else:
        logs.create_log_stream(logGroupName=log_group, logStreamName=log_stream)
        log_events = [{'timestamp': timestamp, 'message': str(message)}]
        logs.put_log_events(logGroupName=log_group, logStreamName=log_stream, logEvents=log_events)
    return log_stream


def delete_folder_membership_of_assets(now, dic, accountid, package, namespace, namespace_hash, target_session,
                                       faillist, logs,
                                       log_group, error_log, success_log):
    timestamp = int(round(time.time() * 1000))
    for assetType in dic:  # Datasets or Dashboardsin
        source_asset_ids = dic[assetType]
        if isinstance(source_asset_ids, dict):
            for id in source_asset_ids:
                source_folder_names = source_asset_ids[id]
                if isinstance(source_folder_names, list):
                    for folderName in source_folder_names:
                        # pass in new naming convention for assets
                        assetGUID = namespace_hash + '-' + id.split("-", 1)[1]
                        folderID = namespace_hash + '-' + folderName
                        try:
                            if assetType == 'Datasets':
                                delete_folder_membership(target_session, folderID, assetGUID, 'DATASET')
                                log_events_to_cloudwatch(
                                    {"account_id": accountid, "package": package, "deployment_time": now,
                                     "namespace": namespace, "hashed_namespace": namespace_hash,
                                     "folder_id": folderID, "asset_type": assetType, "asset_guid": assetGUID,
                                     "success": assetGUID + "successfully removed membership from folderID: " + folderID},
                                    logs,
                                    log_group, success_log)
                            elif assetType == 'Dashboards':
                                delete_folder_membership(target_session, folderID, assetGUID, 'DASHBOARD')
                                log_events_to_cloudwatch(
                                    {"account_id": accountid, "package": package, "deployment_time": now,
                                     "namespace": namespace, "hashed_namespace": namespace_hash,
                                     "folder_id": folderID, "asset_type": assetType, "asset_guid": assetGUID,
                                     "success": assetGUID + "successfully removed membership from folderID: " + folderID},
                                    logs,
                                    log_group, success_log)
                            else:
                                raise Exception("AssetType is neither Datasets or Dashboards")
                        except Exception as e:
                            message = {"account_id": accountid, "package": package, "deployment_time": now,
                                       "namespace": namespace,
                                       "hashed_namespace": namespace_hash, "folder_id": folderID,
                                       "asset_guid": assetGUID, "asset_type": assetType, "error": str(e)}
                            faillist.append(message)
                            log_events_to_cloudwatch(message, logs, log_group, error_log)
                            continue
    return faillist


def create_folder_membership_of_assets(now, dic, accountid, package, namespace, namespace_hash, target_session,
                                       faillist, logs,
                                       log_group, error_log, success_log):
    for assetType in dic:  # Datasets or Dashboards
        source_asset_ids = dic[assetType]
        if isinstance(source_asset_ids, dict):
            for id in source_asset_ids:
                source_folder_names = source_asset_ids[id]
                if isinstance(source_folder_names, list):
                    for folderName in source_folder_names:
                        # pass in new naming convention for assets
                        assetGUID = namespace_hash + '-' + id.split("-", 1)[1]
                        folderID = namespace_hash + '-' + folderName
                        try:
                            if assetType == 'Datasets':
                                create_folder_membership(target_session, folderID, assetGUID, 'DATASET')
                                log_events_to_cloudwatch(
                                    {"account_id": accountid, "package": package, "deployment_time": now,
                                     "namespace": namespace, "hashed_namespace": namespace_hash,
                                     "folder_id": folderID, "asset_type": assetType, "asset_guid": assetGUID,
                                     "success": assetGUID + " successfully created membership with folderID: " + folderID},
                                    logs,
                                    log_group, success_log)
                            elif assetType == 'Dashboards':
                                create_folder_membership(target_session, folderID, assetGUID, 'DASHBOARD')
                                log_events_to_cloudwatch(
                                    {"account_id": accountid, "package": package, "deployment_time": now,
                                     "namespace": namespace, "hashed_namespace": namespace_hash,
                                     "folder_id": folderID, "asset_type": assetType, "asset_guid": assetGUID,
                                     "success": assetGUID + " successfully created membership with folderID: " + folderID},
                                    logs,
                                    log_group, success_log)
                            else:
                                raise Exception("AssetType is neither Datasets or Dashboards")
                        except Exception as e:
                            message = {"account_id": accountid, "package": package, "deployment_time": now,
                                       "namespace": namespace,
                                       "hashed_namespace": namespace_hash, "folder_id": folderID,
                                       "asset_guid": assetGUID, "asset_type": assetType, "error": str(e)}
                            faillist.append(message)
                            log_events_to_cloudwatch(message, logs, log_group, error_log)
                            continue
    return faillist


def delete_assets(now, dic, accountid, package, namespace, namespace_hash, target_session, faillist, logs, log_group,
                  error_log,
                  success_log):
    for assetType in dic:  # Datasets or Dashboards
        source_asset_ids = dic[assetType]
        if isinstance(source_asset_ids, list):
            for id in source_asset_ids:  # Hash(MNS)-CDI
                # pass in new naming convention for assets
                assetGUID = namespace_hash + '-' + id.split("-", 1)[1]
                try:
                    if assetType == 'Datasets':  # Delete asset per namespace
                        print('deleting dataset')
                        delete_dataset(target_session, assetGUID)
                        log_events_to_cloudwatch(
                            {"account_id": accountid, "package": package, "deployment_time": now,
                             "namespace": namespace, "hashed_namespace": namespace_hash,
                             "asset_type": assetType, "asset_guid": assetGUID,
                             "success": assetGUID + " successfully deleted from " + accountid}, logs,
                            log_group, success_log)
                    elif assetType == 'Dashboards':
                        print('deleting dashboard')
                        delete_dashboard(target_session, assetGUID)
                        log_events_to_cloudwatch(
                            {"account_id": accountid, "package": package, "deployment_time": now,
                             "namespace": namespace, "hashed_namespace": namespace_hash,
                             "asset_type": assetType, "asset_guid": assetGUID,
                             "success": assetGUID + " successfully deleted from " + accountid}, logs,
                            log_group, success_log)
                    else:
                        raise Exception("AssetType is neither Datasets or Dashboards")
                except Exception as e:
                    message = {"account_id": accountid, "package": package, "deployment_time": now,
                               "namespace": namespace, "hashed_namespace": namespace_hash,
                               "asset_guid": assetGUID,
                               "error": str(e)}
                    faillist.append(message)
                    log_events_to_cloudwatch(message, logs, log_group, error_log)
                    continue
    return faillist


# TODO: Create folder if missing
def validate_folder_hierarchy(now, dic, package, namespace, folderID, region, accountid, target_session, faillist, logs,
                              log_group,
                              error_log, success_log):
    folderarn = 'arn:aws:quicksight:' + region + ':' + accountid + ':folder/'
    for folder in dic:  # CDI ... Datasets
        folderID += '-' + folder
        subfolders = dic[folder]
        try:
            search_folders(target_session, folderarn + folderID)
            log_events_to_cloudwatch(
                {"account_id": accountid, "package": package, "deployment_time": now, "namespace": namespace,
                 "folder_id": folderID,
                 "success": "FolderID: " + folderID + " exists"}, logs,
                log_group, success_log)
        except Exception as e:
            message = {"account_id": accountid, "package": package, "deployment_time": now, "namespace": namespace,
                       "folder_id": folderID, "error": str(e)}
            faillist.append(message)
            log_events_to_cloudwatch(message, logs, log_group, error_log)
            folderID = folderID.replace('-' + folder, "")
            continue
        if isinstance(subfolders, dict):
            validate_folder_hierarchy(now, subfolders, package, namespace, folderID, region, accountid, target_session,
                                      faillist,
                                      logs, log_group, error_log, success_log)
        folderID = folderID.replace('-' + folder, "")
    return faillist


def migrate_data_sets(now, account_id, package, target_session, region, dir, namespace, namespace_name, logs,
                      log_group, error_log, success_log):
    faillist = []
    newsetslist = []
    # Get datasets which already migrated in target account
    targetds = list_data_sets(target_session)
    # already_migrated record the datasets ids of target account
    already_migrated = set({})
    for ds in targetds:
        already_migrated.add(ds['DataSetId'])

    # Unzip all datasets from Release folder of Source Account
    # Migrate parent datasets first
    dataset_parent_dir = dir + "/Parent"
    if (len(os.listdir(dataset_parent_dir)) > 0):
        for dataset_file in os.listdir(dataset_parent_dir):
            try:
                dataset_path = os.path.join(dataset_parent_dir, dataset_file)
                with open(dataset_path, "r") as f:
                    res = json.load(f)
                message = {"account_id": account_id, "package": package, "deployment_time": now, "namespace": namespace,
                           "hashed_namespace": namespace_name, "dir_file": dataset_file,
                           "success": dataset_file + " loaded successfully"}
                log_events_to_cloudwatch(message, logs, log_group, success_log)
            except Exception:
                message = {"account_id": account_id, "package": package, "deployment_time": now, "namespace": namespace,
                           "hashed_namespace": namespace_name, "dir_file": dataset_file, "error": str(Exception)}
                faillist.append(message)
                log_events_to_cloudwatch(message, logs, log_group, error_log)
                continue
            name = res['DataSet']['Name']
            sourcedsid = res['DataSet']['DataSetId']
            LT = res['DataSet']['LogicalTableMap']

            targetdsid = namespace_name + '-' + res['DataSet']['DataSetId'].split("-", 1)[1]

            PT = res['DataSet']['PhysicalTableMap']
            for key, value in PT.items():
                for i, j in value.items():
                    # use namespace hash to identify unique datasource
                    j['DataSourceArn'] = 'arn:aws:quicksight:' + region + ':' + account_id + ':datasource/' + namespace_name + '-DW_DataSource'

            if targetdsid not in already_migrated:
                try:
                    print("Creating dataset: ", targetdsid)
                    newdataset = create_data_set(target_session, targetdsid, name, PT, LT, res['DataSet']['ImportMode'])
                    newsetslist.append(newdataset)
                    log_events_to_cloudwatch(
                        {"account_id": account_id, "package": package, "deployment_time": now, "namespace": namespace,
                         "hashed_namespace": namespace_name, "asset_type": "Datasets",
                         "asset_guid": targetdsid, "asset_name": name,
                         "success": "Dataset: " + targetdsid + " is successfully created"}, logs, log_group,
                        success_log)
                except Exception as e:
                    message = {"accountID": account_id, "package": package, "deployment_time": now,
                               "namespace": namespace, "hashed_namespace": namespace_name, "asset_type": "Datasets",
                               "asset_guid": targetdsid, "asset_name": name, "error": str(e)}
                    faillist.append(message)
                    log_events_to_cloudwatch(message, logs, log_group, error_log)
                    continue

            elif targetdsid in already_migrated:
                try:
                    print("Updating dataset: ", targetdsid)
                    newdataset = update_dataset(target_session, targetdsid, name, PT, LT, res['DataSet']['ImportMode'])
                    newsetslist.append(newdataset)
                    log_events_to_cloudwatch(
                        {"account_id": account_id, "package": package, "deployment_time": now, "namespace": namespace,
                         "hashed_namespace": namespace_name, "asset_type": "Datasets",
                         "asset_guid": targetdsid, "asset_name": name,
                         "success": "Dataset: " + targetdsid + " is successfully updated"}, logs, log_group,
                        success_log)
                except Exception as e:
                    message = {"account_id": account_id, "package": package, "deployment_time": now,
                               "namespace": namespace, "hashed_namespace": namespace_name, "asset_type": "Datasets",
                               "asset_guid": targetdsid, "asset_name": name, "error": str(e)}
                    faillist.append(message)
                    log_events_to_cloudwatch(message, logs, log_group, error_log)
                    continue
    # Migrate child datasets
    dataset_child_dir = dir + "/Child"
    try:
        if (len(os.listdir(dataset_child_dir)) > 0):
            for dataset_file in os.listdir(dataset_child_dir):
                try:
                    dataset_path = os.path.join(dataset_child_dir, dataset_file)
                    with open(dataset_path, "r") as f:
                        res = json.load(f)
                    message = {"account_id": account_id, "package": package, "deployment_time": now,
                               "namespace": namespace, "hashed_namespace": namespace_name, "dir_file": dataset_file,
                               "success": dataset_file + " loaded successfully"}
                    log_events_to_cloudwatch(message, logs, log_group, success_log)
                except Exception:
                    message = {"account_id": account_id, "package": package, "deployment_time": now,
                               "namespace": namespace, "hashed_namespace": namespace_name, "dir_file": dataset_file,
                               "error": str(Exception)}
                    faillist.append(message)
                    log_events_to_cloudwatch(message, logs, log_group, error_log)
                    continue

                name = res['DataSet']['Name']
                sourcedsid = res['DataSet']['DataSetId']
                PT = res['DataSet']['PhysicalTableMap']
                LT = res['DataSet']['LogicalTableMap']
                targetdsid = namespace_name + '-' + res['DataSet']['DataSetId'].split("-", 1)[1]

                dsid = LT['Source']['DataSetArn'].split("/")[1]
                LT['Source'][
                    'DataSetArn'] = 'arn:aws:quicksight:' + region + ':' + account_id + ':dataset/' + namespace_name + '-' + dsid

                if targetdsid not in already_migrated:
                    try:
                        print("Creating dataset: ", targetdsid)
                        newdataset = create_data_set(target_session, targetdsid, name, PT, LT,
                                                     res['DataSet']['ImportMode'])
                        newsetslist.append(newdataset)
                        log_events_to_cloudwatch(
                            {"account_id": account_id, "package": package, "deployment_time": now,
                             "namespace": namespace, "hashed_namespace": namespace_name, "asset_type": "Datasets",
                             "asset_guid": targetdsid, "asset_name": name,
                             "success": "Dataset: " + targetdsid + " is successfully created"}, logs, log_group,
                            success_log)
                    except Exception as e:
                        message = {"account_id": account_id, "package": package, "deployment_time": now,
                                   "namespace": namespace, "hashed_namespace": namespace_name, "asset_type": "Datasets",
                                   "asset_guid": targetdsid, "asset_name": name, "error": str(e)}
                        faillist.append(message)
                        print(message)
                        log_events_to_cloudwatch(message, logs, log_group, error_log)
                        continue
                elif targetdsid in already_migrated:
                    try:
                        newdataset = update_dataset(target_session, targetdsid, name, PT, LT,
                                                    res['DataSet']['ImportMode'])
                        newsetslist.append(newdataset)
                        log_events_to_cloudwatch(
                            {"account_id": account_id, "package": package, "deployment_time": now,
                             "namespace": namespace, "hashed_namespace": namespace_name, "asset_type": "Datasets",
                             "asset_guid": targetdsid, "asset_name": name,
                             "success": "Dataset: " + targetdsid + " is successfully updated"}, logs, log_group,
                            success_log)
                    except Exception as e:
                        message = {"account_id": account_id, "package": package, "deployment_time": now,
                                   "namespace": namespace, "hashed_namespace": namespace_name, "asset_type": "Datasets",
                                   "asset_guid": targetdsid, "asset_name": name, "error": str(e)}
                        faillist.append(message)
                        log_events_to_cloudwatch(message, logs, log_group, error_log)
                        continue
    except:
        print('No child datasets')
    return faillist


def migrate_themes(now, account_id, env, package, target_session, dir, logs, log_group, error_log, success_log):
    faillist = []
    newthemeslist = []
    # Get themes which already migrated
    targetthemes = list_themes(target_session)
    # already_migrated record the datasets ids of target account
    already_migrated = set({})
    for th in targetthemes:
        already_migrated.add(th['ThemeId'])

    for theme_file in os.listdir(dir):
        try:
            theme_path = os.path.join(dir, theme_file)
            with open(theme_path, "r") as f:
                res = json.load(f)
            message = {"account_id": account_id, "package": package, "deployment_time": now, "dir_file": theme_file,
                       "success": theme_file + " loaded successfully"}
            log_events_to_cloudwatch(message, logs, log_group,
                                     success_log)
        except Exception:
            message = {"account_id": account_id, "package": package, "deployment_time": now, "dir_file": theme_file,
                       "error": str(Exception)}
            faillist.append(message)
            log_events_to_cloudwatch(message, logs, log_group, error_log)
            continue

        source_theme_id = res['Theme']['ThemeId']
        Name = res['Theme']['Name']
        BaseThemeId = res['Theme']['Version']['BaseThemeId']
        Configuration = res['Theme']['Version']['Configuration']

        if '_390_' in source_theme_id:
            target_theme_id = '3m_his_' + env + '_bia_390_' + source_theme_id.split('_', 5)[5]
        else:
            target_theme_id = source_theme_id

        if target_theme_id not in already_migrated:
            try:
                newtheme = create_theme(target_session, target_theme_id, Name, BaseThemeId, Configuration)
                newthemeslist.append(newtheme)
                log_events_to_cloudwatch(
                    {"account_id": account_id, "package": package, "deployment_time": now, "asset_type": "Themes",
                     "asset_guid": target_theme_id, "asset_name": Name,
                     "success": "Theme: " + Name + " is successfully migrated"}, logs, log_group, success_log)
            except Exception as e:
                message = {"account_id": account_id, "package": package, "deployment_time": now, "theme_id": target_theme_id,
                           "name": Name, "error": str(e)}
                faillist.append(message)
                log_events_to_cloudwatch(message, logs, log_group, error_log)
                continue
        elif target_theme_id in already_migrated:
            try:
                newtheme = update_theme(target_session, target_theme_id, Name, BaseThemeId, Configuration)
                newthemeslist.append(newtheme)
                log_events_to_cloudwatch(
                    {"account_id": account_id, "package": package, "deployment_time": now, "asset_type": "Themes",
                     "asset_guid": target_theme_id, "asset_name": Name,
                     "success": "Theme " + target_theme_id + " is successfully updated"}, logs, log_group, success_log)
            except Exception as e:
                message = {"account_id": account_id, "package": package, "deployment_time": now, "theme_id": target_theme_id,
                           "name": Name, "error": str(e)}
                faillist.append(message)
                log_events_to_cloudwatch(message, logs, log_group, error_log)
                continue

    return faillist


def migrate_dashboards(now, account_id, package, target_session, region, dir, namespace, namespace_name, logs,
                       log_group, error_log, success_log):
    success = []
    faillist = []
    for dashboard_path in os.listdir(dir):
        try:
            dashboard_path = os.path.join(dir, dashboard_path)
            with open(dashboard_path, "r") as f:
                res = json.load(f)
            message = {"account_id": account_id, "package": package, "deployment_time": now, "dir_file": dashboard_path,
                       "success": dashboard_path + " loaded successfully"}
            log_events_to_cloudwatch(message, logs, log_group,
                                     success_log)
        except Exception:
            message = {"account_id": account_id, "package": package, "deployment_time": now, "dir_file": dashboard_path,
                       "error": str(Exception)}
            faillist.append(message)
            log_events_to_cloudwatch(message, logs, log_group, error_log)
            continue

        sourcedid = res['Dashboard']['DashboardId']
        sourcedname = res['Dashboard']['Name']
        sourcetid = sourcedid
        sourcetname = sourcedname
        targettid = namespace_name + '-' + sourcetid.split('-', 1)[1]
        targettname = sourcedname
        dataset_arns = res['Definition']['DataSetIdentifierDeclarations']

        # Set dashboard datasets on client's: Hash(namespace)-guid
        for dataset_arn in dataset_arns:
            if "DataSetArn" in dataset_arn:
                target_dataset_id = namespace_name + '-' + dataset_arn['DataSetArn'].split("/")[1].split("-", 1)[1]
                target_dataset_arn = 'arn:aws:quicksight:' + region + ':' + account_id + ':dataset/' + target_dataset_id
                dataset_arn['DataSetArn'] = target_dataset_arn

        TargetThemeArn = ''
        if 'ThemeArn' in res['Dashboard']['Version'].keys():
            SourceThemearn = res['Dashboard']['Version']['ThemeArn']  # region
            TargetThemeArn = 'arn:aws:quicksight:' + region + ':' + account_id + ':theme/' + \
                             SourceThemearn.split("/")[1]

        dashboard = describe_dashboard_definition(target_session, targettid)
        if 'Failed to describe dashboard:' in dashboard:
            if 'dashboard/' + targettid + ' is not found' in dashboard:
                try:
                    print('Creating Dashboard: ' + targettid)
                    newdashboard = create_dashboard(target_session, targettid, sourcedid, targettname, res,
                                                    'ENABLED', 'ENABLED', 'COLLAPSED', ('VersionDescription', '1'),
                                                    ('ThemeArn', TargetThemeArn), namespace_name)
                    print(newdashboard)
                    log_events_to_cloudwatch(
                        {"account_id": account_id, "package": package, "deployment_time": now, "namespace": namespace,
                         "hashed_namespace": namespace_name, "asset_type": "Dashboards",
                         "asset_guid": targettid, "asset_name": targettname,
                         "success": "Dashboard: " + targettid + " is successfully created"}, logs, log_group,
                        success_log)
                except Exception as e:
                    message = {"account_id": account_id,
                               "package": package,
                               "deployment_time": now,
                               "namespace": namespace,
                               "hashed_namespace": namespace_name,
                               "asset_type": "Dashboards",
                               "error_type": "Create New Dashboard Error",
                               "asset_guid": targettid,
                               "asset_name": targettname,
                               "error": str(e)}
                    faillist.append(message)
                    log_events_to_cloudwatch(message, logs, log_group, error_log)
                    continue
            else:
                message = {"account_id": account_id,
                           "package": package,
                           "deployment_time": now,
                           "namespace": namespace,
                           "hashed_namespace": namespace_name,
                           "asset_type": "Dashboards",
                           "error_type": "Describe Target Dashboard Error",
                           "asset_guid": targettid,
                           "asset_name": targettname,
                           "error": str(dashboard)}
                faillist.append(message)
                log_events_to_cloudwatch(message, logs, log_group, error_log)
                continue
        elif dashboard['Dashboard']['Version']['Status'] == "CREATION_FAILED":
            try:
                delete_dashboard(target_session, targettid)
                print('Creating Dashboard: ' + targettid)
                newdashboard = create_dashboard(target_session, targettid, sourcedid, targettname, res,
                                                'ENABLED', 'ENABLED', 'COLLAPSED', ('VersionDescription', '1'),
                                                ('ThemeArn', TargetThemeArn), namespace_name)
                log_events_to_cloudwatch(
                    {"account_id": account_id, "package": package, "deployment_time": now, "namespace": namespace,
                     "hashed_namespace": namespace_name, "asset_type": "Dashboards",
                     "asset_guid": targettid, "asset_name": targettname,
                     "success": "Dashboard: " + targettid + " is successfully created"}, logs, log_group,
                    success_log)
            except Exception as e:
                message = {
                    "account_id": account_id,
                    "package": package,
                    "deployment_time": now,
                    "namespace": namespace,
                    "hashed_namespace": namespace_name,
                    "asset_type": "Dashboards",
                    "error_type": "Create Dashboard Error",
                    "asset_guid": targettid,
                    "asset_name": targettname,
                    "error": str(e)}
                faillist.append(message)
                log_events_to_cloudwatch(message, logs, log_group, error_log)
                continue

        else:
            print('Updating Dashboard: ' + targettid)
            try:
                delete_dashboard(target_session, targettid)
                newdashboard = create_dashboard(target_session, targettid, sourcedid, targettname, res,
                                                'ENABLED', 'ENABLED', 'COLLAPSED', ('VersionDescription', '1'),
                                                ('ThemeArn', TargetThemeArn), namespace_name)
                log_events_to_cloudwatch(
                    {"account_id": account_id, "package": package, "deployment_time": now, "namespace": namespace,
                     "hashed_namespace": namespace_name, "asset_type": "Dashboards",
                     "asset_guid": targettid, "asset_name": targettname,
                     "success": "Dashboard: " + targettid + " is successfully created"}, logs, log_group,
                    success_log)
            except Exception as e:
                faillist.append({
                    "account_id": account_id,
                    "package": package,
                    "deployment_time": now,
                    "namespace": namespace,
                    "hashed_namespace": namespace_name,
                    "asset_type": "Dashboards",
                    "error_type": "Update Dashboard Error",
                    "asset_guid": targettid,
                    "asset_name": targettname,
                    "error": str(e)})
                continue

        res = describe_dashboard_definition(target_session, targettid)
        if res['Status'] == 200:
            status = res['Dashboard']['Version']['Status']
            while 'PROGRESS' in status:
                time.sleep(3)
                res = describe_dashboard_definition(target_session, targettid)
                status = res['Dashboard']['Version']['Status']
            if 'SUCCESSFUL' in status:
                success.append(res)
            else:
                message = {"account_id": account_id,
                           "package": package, "deployment_time": now,
                           "namespace": namespace, "hashed_namespace": namespace_name, "asset_type": "Dashboards",
                           "error_type": "Dashboard Creation Status is not Successful", "dashboard": res}
                faillist.append(message)
                log_events_to_cloudwatch(message, logs, log_group, error_log)
    return faillist

def initialization(account_id, awsrole, env, region, package, namespace, logs, log_group, error_log, success_log,
                   now):
    # path of assets
    zip_path = "SourceAssets/"

    # assume role
    target_session = s_func._assume_role(account_id, awsrole, region)

    # results output location
    success_location, fail_location = results_output_location()

    faillist = []
    # Creating folder membership of assets
    # Unzip all assets from Release/Create folder of Source Account
    create_folder_members = zip_path + "/Mapping/create_folder_membership.json"
    print(create_folder_members)
    try:
        with open(create_folder_members, "r") as f:
            create_members_json = json.load(f)
            message = {"account_id": account_id, "package": package, "deployment_time": now,
                       "success": "create_folder_membership.json loaded successfully"}
            log_events_to_cloudwatch(message, logs, log_group, success_log)
    except Exception:
        message = {"account_id": account_id, "package": package, "deployment_time": now, "error": str(Exception)}
        faillist.append(message)
        print('Error loading files: ' + str(Exception))
        log_events_to_cloudwatch(message, logs, log_group, error_log)
        sys.exit(1)

    """
    # migrate themes
    """
    print('---Creating Themes---')

    # get themes which already migrated
    target_themes = list_themes(target_session)

    already_migrated = set()
    for th in target_themes:
        already_migrated.add(th['ThemeId'])

    new_themes_list = []

    theme_dir = zip_path + "Theme"
    for theme_file in os.listdir(theme_dir):
        try:
            theme_path = os.path.join(theme_dir, theme_file)
            with open(theme_path, "r") as f:
                res = json.load(f)
                message = {"account_id": account_id, "package": package, "deployment_time": now, "dir_file": theme_file,
                           "success": theme_file + " loaded successfully"}
                log_events_to_cloudwatch(message, logs, log_group,
                                         success_log)
        except Exception:
            message = {"account_id": account_id, "package": package, "deployment_time": now, "dir_file": theme_file,
                       "error": str(Exception)}
            faillist.append(message)
            log_events_to_cloudwatch(message, logs, log_group, error_log)
            continue

        source_theme_id = res['Theme']['ThemeId']
        name = res['Theme']['Name']
        base_theme_id = res['Theme']['Version']['BaseThemeId']
        configuration = res['Theme']['Version']['Configuration']

        if '_390_' in source_theme_id:
            target_theme_id = '3m_his_' + env + '_bia_390_' + source_theme_id.split('_', 5)[5]
        else:
            target_theme_id = source_theme_id

        if target_theme_id not in already_migrated:
            try:
                newtheme = create_theme(target_session, target_theme_id, name, base_theme_id, configuration)
                new_themes_list.append(newtheme)
                log_events_to_cloudwatch(
                    {"account_id": account_id, "package": package, "deployment_time": now, "asset_type": "Themes",
                     "asset_guid": target_theme_id, "asset_name": name,
                     "success": "Theme: " + name + " is successfully migrated"}, logs, log_group, success_log)
            except Exception as e:
                message = {"account_id": account_id, "package": package, "deployment_time": now, "asset_type": "Themes",
                           "theme_id": target_theme_id, "name": name, "error": str(e)}
                faillist.append(message)
                log_events_to_cloudwatch(message, logs, log_group, error_log)
                continue

    """
    migrate data sets

    """
    print('---Creating Datasets---')
    new_sets_list = []
    faillist = []

    print('Migrating datasets to: ' + namespace)
    hashed = hashlib.md5(namespace.encode('utf-8')).hexdigest()

    # Migrate parent datasets first
    dataset_dir = zip_path + "Dataset/Parent"
    for dataset_file in os.listdir(dataset_dir):
        try:
            dataset_path = os.path.join(dataset_dir, dataset_file)
            with open(dataset_path, "r") as f:
                res = json.load(f)
            message = {"account_id": account_id, "package": package, "deployment_time": now, "namespace": namespace,
                       "hashed_namespace": hashed, "dir_file": dataset_file,
                       "success": dataset_file + " loaded successfully"}
            log_events_to_cloudwatch(message, logs, log_group, success_log)
        except Exception:
            message = {"account_id": account_id, "package": package, "deployment_time": now, "namespace": namespace,
                       "hashed_namespace": hashed, "dir_file": dataset_file, "error": str(Exception)}
            faillist.append(message)
            log_events_to_cloudwatch(message, logs, log_group, error_log)
            continue

        name = res['DataSet']['Name']
        sourcedsid = res['DataSet']['DataSetId']
        LT = res['DataSet']['LogicalTableMap']
        targetdsid = hashed + '-' + sourcedsid.split("-", 1)[1]
        PT = res['DataSet']['PhysicalTableMap']
        for key, value in PT.items():
            for i, j in value.items():
                dsid = j['DataSourceArn'].split("/")[1]
                # use namespace to identify unique datasource
                j['DataSourceArn'] = 'arn:aws:quicksight:' + region + ':' + account_id + ':datasource/' + hashed + '-DW_DataSource'

        try:
            print("Creating dataset: ", targetdsid)
            new_data_set = create_data_set(target_session, targetdsid, name, PT, LT, res['DataSet']['ImportMode'])
            log_events_to_cloudwatch(
                {"account_id": account_id, "package": package, "deployment_time": now, "namespace": namespace,
                 "hashed_namespace": hashed, "asset_type": "Datasets",
                 "asset_guid": targetdsid, "asset_name": name,
                 "success": "Dataset: " + targetdsid + " is successfully created"}, logs, log_group,
                success_log)
            new_sets_list.append(new_data_set)
        except Exception as e:
            message = {"accountID": account_id, "package": package, "deployment_time": now, "namespace": namespace,
                       "hashed_namespace": hashed, "asset_type": "Datasets",
                       "asset_guid": targetdsid, "asset_name": name, "error": str(e)}
            faillist.append(message)
            log_events_to_cloudwatch(message, logs, log_group, error_log)
            continue

    # Migrate child datasets
    dataset_dir = zip_path + "Dataset/Child"
    for dataset_file in os.listdir(dataset_dir):
        try:
            dataset_path = os.path.join(dataset_dir, dataset_file)
            with open(dataset_path, "r") as f:
                res = json.load(f)
            message = {"account_id": account_id, "package": package, "deployment_time": now, "namespace": namespace,
                       "hashed_namespace": hashed, "dir_file": dataset_file,
                       "success": dataset_file + " loaded successfully"}
            log_events_to_cloudwatch(message, logs, log_group, success_log)
        except Exception:
            message = {"account_id": account_id, "package": package, "deployment_time": now, "namespace": namespace,
                       "hashed_namespace": hashed, "dir_file": dataset_file, "error": str(Exception)}
            faillist.append(message)
            log_events_to_cloudwatch(message, logs, log_group, error_log)
            continue

        name = res['DataSet']['Name']
        sourcedsid = res['DataSet']['DataSetId']
        PT = res['DataSet']['PhysicalTableMap']
        LT = res['DataSet']['LogicalTableMap']

        targetdsid = hashed + '-' + sourcedsid.split("-", 1)[1]

        dsid = LT['Source']['DataSetArn'].split("/")[1]
        LT['Source'][
            'DataSetArn'] = 'arn:aws:quicksight:' + region + ':' + account_id + ':dataset/' + hashed + '-' + dsid

        try:
            print("Creating dataset: ", targetdsid)
            new_dataset = create_data_set(target_session, targetdsid, name, PT, LT, res['DataSet']['ImportMode'])
            log_events_to_cloudwatch(
                {"account_id": account_id, "package": package, "deployment_time": now, "namespace": namespace,
                 "hashed_namespace": hashed, "asset_type": "Datasets",
                 "asset_guid": targetdsid, "asset_name": name,
                 "success": "Dataset: " + targetdsid + " is successfully created"}, logs, log_group,
                success_log)
        except Exception as e:
            message = {"account_id": account_id, "package": package, "deployment_time": now, "namespace": namespace,
                       "hashed_namespace": hashed, "asset_type": "Datasets",
                       "asset_guid": targetdsid, "asset_name": name, "error": str(e)}
            faillist.append(message)
            log_events_to_cloudwatch(message, logs, log_group, error_log)
            continue
    print(namespace + ': Datasets migrated')
    """
    # migrate dashboards
    """
    print('---Creating Dashboards---')

    success = []
    faillist = []

    dashboard_dir = zip_path + "Dashboard"
    print('Migrating dashboards to: ' + namespace)
    hashed = hashlib.md5(namespace.encode('utf-8')).hexdigest()
    for dashboard_path in os.listdir(dashboard_dir):
        try:
            dashboard_path = os.path.join(dashboard_dir, dashboard_path)
            with open(dashboard_path, "r") as f:
                res = json.load(f)
            message = {"account_id": account_id, "package": package, "deployment_time": now,
                       "dir_file": dashboard_path, "success": dashboard_path + " loaded successfully"}
            log_events_to_cloudwatch(message, logs, log_group,
                                     success_log)
        except Exception:
            message = {"account_id": account_id, "package": package, "deployment_time": now,
                       "dir_file": dashboard_path, "error": str(Exception)}
            faillist.append(message)
            log_events_to_cloudwatch(message, logs, log_group, error_log)
            continue

        target_theme_arn = ''
        if 'ThemeArn' in res['Dashboard']['Version'].keys():
            source_theme_arn = res['Dashboard']['Version']['ThemeArn']
            target_theme_arn = 'arn:aws:quicksight:' + region + ':' + account_id + ':theme/' + \
                               source_theme_arn.split("/")[1]

        sourcedid = res['Dashboard']['DashboardId']
        targetdname = res['Dashboard']['Name']
        targetdid = hashed + sourcedid.split("-", 1)[1]
        dataset_arns = res['Definition']['DataSetIdentifierDeclarations']

        # Set dashboard datasets on client's: Hash(namespace)-guid
        for dataset_arn in dataset_arns:
            if "DataSetArn" in dataset_arn:
                target_dataset_id = hashed + '-' + dataset_arn['DataSetArn'].split("/")[1].split("-", 1)[1]
                target_dataset_arn = 'arn:aws:quicksight:' + region + ':' + account_id + ':dataset/' + target_dataset_id
                dataset_arn['DataSetArn'] = target_dataset_arn

        try:
            print("Creating dashboard: ", targetdid)
            new_dashboard = create_dashboard(target_session, targetdid, sourcedid, targetdname,
                                             res, 'ENABLED', 'ENABLED', 'COLLAPSED', ('VersionDescription', '1'),
                                             ('ThemeArn', target_theme_arn))
            log_events_to_cloudwatch(
                {"account_id": account_id, "package": package, "deployment_time": now, "namespace": namespace,
                 "hashed_namespace": hashed, "asset_type": "Dashboards",
                 "asset_guid": targetdid, "asset_name": targetdname,
                 "success": "Dashboard: " + targetdid + " is successfully created"}, logs, log_group,
                success_log)
        except Exception as e:
            message = {"account_id": account_id,
                       "package": package,
                       "deployment_time": now,
                       "namespace": namespace,
                       "hashed_namespace": hashed,
                       "asset_type": "Dashboards",
                       "error_type": "Create New Dashboard Error",
                       "asset_guid": targetdid,
                       "asset_name": targetdname,
                       "error": str(e)}
            faillist.append(message)
            log_events_to_cloudwatch(message, logs, log_group, error_log)
            continue

        res = describe_dashboard_definition(target_session, new_dashboard['DashboardId'])
        if res['Status'] == 200:
            status = res['Dashboard']['Version']['Status']
            while 'PROGRESS' in status:
                time.sleep(3)
                res = describe_dashboard_definition(target_session, new_dashboard['DashboardId'])
                status = res['Dashboard']['Version']['Status']
            if 'SUCCESSFUL' in status:
                success.append(res)
            else:
                message = {"account_id": account_id,
                           "package": package, "deployment_time": now,
                           "namespace": namespace, "hashed_namespace": hashed, "asset_type": "Dashboards",
                           "error_type": "Dashboard Creation Status is not Successful", "dashboard": res}
                faillist.append(message)
                log_events_to_cloudwatch(message, logs, log_group, error_log)
    print(namespace + ': Dashboards migrated')

    # After resources are created, add folder memberships to assets:
    # Creating folder memberships for assets of target namespace
    result = create_folder_membership_of_assets(now, create_members_json, account_id, package, namespace, hashed,
                                                target_session, [], logs, log_group, error_log, success_log)
    if result:
        faillist.append(result)
    if faillist != []:
        failure_file = fail_location + now + 'fail_results_initialization.gz'

        for list_item in faillist:
            for dict in list_item:
                with gzip.open(failure_file, 'at', encoding='utf-8') as fout:
                    json.dump(dict, fout, sort_keys=True, default=str)
                    fout.write('\n')

        # Upload failure file to S3
        key = 'admin-console/monitoring/quicksight/deployment_results/initialization/deployment_results_' + now + '.gz'
        s_func.send_to_s3('3m-his-' + env + '-390-biat-tool', 'alias/' + env + '-biat-tool-KMS', key, failure_file, target_session)

        raise Exception('Did not deploy to all namespaces successfully')



def results_output_location():
    # Results output location
    successlocation = "Deployment_Results/Successful/"
    faillocation = "Deployment_Results/Fail/"

    try:
        os.makedirs(os.path.dirname(successlocation), exist_ok=True)
    except OSError:
        print("Creation of the directory %s failed" % successlocation)
    else:
        print("Successfully created the directory %s" % successlocation)

    try:
        os.makedirs(os.path.dirname(faillocation), exist_ok=True)
    except OSError:
        print("Creation of the directory %s failed" % faillocation)
    else:
        print("Successfully created the directory %s" % faillocation)

    return successlocation, faillocation


"""
library processing functions
"""


def add_asset_in_library(session, input_id, input_type, out_put_name, out_put_type):
    if out_put_type == 'parameter':
        lib = '../library/2nd_class_assets/parameter_library.json'
        new = get_parameter(session, input_id, input_type, out_put_name)
        write_lib(out_put_name, new, lib)
    if (input_type == 'analysis' and out_put_type == 'cf'):
        lib = '../library/2nd_class_assets/analysis_cf_library.json'
        new = get_cfs(session, input_id, input_type, out_put_name)
        write_lib(out_put_name, new, lib)
    if out_put_type == 'analysis':
        lib_def = '../library/1st_class_assets/analysis/' + out_put_name + '_Definition.json'
        lib = '../library/1st_class_assets/analysis/' + out_put_name + '.json'
        new = describe_analysis_definition(session, input_id)
        # print(new)
        file = open(lib_def, 'w')
        file.write(str(new['Definition']))
        file.close()
        file = open(lib, 'w')
        file.write(str(new))
        file.write(str(new['Analysis']))
        file.close()


def write_lib(out_put_name, new, library):
    with open(library, "r+") as lib:
        data = json.load(lib)
        new_data = {out_put_name: new}
        data.update(new_data)
        lib.seek(0)
        json.dump(data, lib, indent=1)


"""
get dependent list of one asset: for migration list 
"""


# get datasets of dashboards in migration list
def data_sets_ls_of_dashboard(dashboard, sourcesession):
    dashboardid = get_dashboard_ids(dashboard, sourcesession)

    sourcedashboard = describe_dashboard(sourcesession, dashboardid[0])

    DataSetArns = sourcedashboard['Dashboard']['Version']['DataSetArns']

    sourcedsref = []
    for i in DataSetArns:
        missing = False
        did = i.split("/")[1]
        # print(did)
        faillist = []
        try:
            dname = get_dataset_name(did, sourcesession)
        except Exception as e:
            faillist.append(
                {"Error Type": "Dataset: " + did + " is missing!", "DashboardId": dashboardid[0], "Name": dashboard,
                 "Error": str(e)})
            missing = True
            break

        sourcedsref.append(dname)
    return sourcedsref


# get datasets of analysis in migration list
def data_sets_ls_of_analysis(analysis, sourcesession):
    analysisid = get_analysis_ids(analysis, sourcesession)
    sourceanalysis = describe_analysis(sourcesession, analysisid[0])
    DataSetArns = sourceanalysis['Analysis']['DataSetArns']
    sourcedsref = []
    for i in DataSetArns:
        missing = False
        did = i.split("/")[1]
        # print(did)
        try:
            dname = get_dataset_name(did, sourcesession)
        except Exception as e:
            return {"Error Type": "Dataset: " + did + " is missing!", "AnalysisId": analysisid[0], "Name": analysis,
                    "Error": str(e)}
            missing = True
            break

        sourcedsref.append(dname)
    return sourcedsref


# get data sources of dashboards in migration list
def data_sources_ls_of_dashboard(dashboard, sourcesession):
    datasets = data_sets_ls_of_dashboard(dashboard, sourcesession)

    sourcedsref = []
    for dataset in datasets:
        ids = get_dataset_ids(dataset, sourcesession)
        res = describe_data_set(sourcesession, ids[0])

        PT = res['DataSet']['PhysicalTableMap']
        for key, value in PT.items():
            for i, j in value.items():
                dsid = j['DataSourceArn'].split("/")[1]
                dsname = get_datasource_name(dsid, sourcesession)
                if dsname not in sourcedsref:
                    sourcedsref.append(dsname)
    return sourcedsref


# get data sources of analysis in migration list
def data_sources_ls_of_analysis(analysis, sourcesession):
    datasets = data_sets_ls_of_analysis(analysis, sourcesession)
    sourcedsref = []
    for dataset in datasets:
        ids = get_dataset_ids(dataset, sourcesession)
        res = describe_data_set(sourcesession, ids[0])

        PT = res['DataSet']['PhysicalTableMap']
        for key, value in PT.items():
            for i, j in value.items():
                dsid = j['DataSourceArn'].split("/")[1]
                dsname = get_datasource_name(dsid, sourcesession)
                if dsname not in sourcedsref:
                    sourcedsref.append(dsname)
    return sourcedsref


# list data source of source account. This function could be removed
def get_data_source_migration_list(sourcesession, source_migrate_list):
    datasources = list_data_sources(sourcesession)  # get data source details with listdatasource API

    migration_list = []
    for newsource in source_migrate_list:
        ids = get_datasource_ids(newsource, sourcesession)  # Get id of data sources migration list
        for datasource in datasources:
            if ids[0] == datasource["DataSourceId"]:
                migration_list.append(
                    datasource)  # migration_list is an array containing data source connection information and etc

    return migration_list


# get object ids from name, or get object name from id
def get_dashboard_ids(name: str, session) -> List[str]:
    qs = session.client('quicksight')
    sts_client = session.client("sts")
    AccountId = sts_client.get_caller_identity()["Account"]

    ids: List[str] = []
    for dashboard in list_dashboards(session):

        if dashboard["Name"] == name:
            ids.append(dashboard["DashboardId"])

    return ids


def get_analysis_ids(name: str, session) -> List[str]:
    qs = session.client('quicksight')
    sts_client = session.client("sts")
    AccountId = sts_client.get_caller_identity()["Account"]

    ids: List[str] = []
    for analysis_list in list_analysis(session):
        if analysis_list["Name"] == name:
            ids.append(analysis_list["AnalysisId"])
    return ids


def get_dashboard_name(did: str, session) -> List[str]:
    qs = session.client('quicksight')
    sts_client = session.client("sts")
    AccountId = sts_client.get_caller_identity()["Account"]

    name: str
    for dashboard in list_dashboards(session):
        if dashboard["DashboardId"] == did:
            name = dashboard["Name"]
    return name


def get_dataset_name(did: str, session) -> List[str]:
    qs = session.client('quicksight')
    sts_client = session.client("sts")
    AccountId = sts_client.get_caller_identity()["Account"]

    name: str
    for dataset in list_data_sets(session):
        if dataset["DataSetId"] == did:
            name = dataset["Name"]
    return name


def get_dataset_ids(name: str, session) -> List[str]:
    qs = session.client('quicksight')
    sts_client = session.client("sts")
    AccountId = sts_client.get_caller_identity()["Account"]

    ids: List[str] = []
    for dataset in list_data_sets(session):
        if dataset["Name"] == name:
            ids.append(dataset["DataSetId"])
    return ids


def get_datasource_name(did: str, session) -> List[str]:
    qs = session.client('quicksight')
    sts_client = session.client("sts")
    AccountId = sts_client.get_caller_identity()["Account"]

    name: str
    for datasource in list_data_sources(session):
        if datasource["DataSourceId"] == did:
            name = datasource["Name"]
    return name


def get_datasource_ids(name: str, session) -> List[str]:
    qs = session.client('quicksight')
    sts_client = session.client("sts")
    AccountId = sts_client.get_caller_identity()["Account"]

    ids: List[str] = []
    for datasource in list_data_sources(session):
        if datasource["Name"] == name:
            ids.append(datasource["DataSourceId"])
    return ids


# load data set input pieces
def loaddsinput(file, part):
    import json
    with open(file) as f:
        data = json.load(f)
    res = data['DataSet'][part]
    return res


def check_object_status(type, id, session):
    if type == 'analysis':
        res = describe_analysis(session, id)
        if res['Status'] == 200:
            status = res['Analysis']['Status']
            return status
        else:
            raise ValueError("describe analysis status failed")


def locate_folder_of_asset(session, MemberId, FolderId, MemberType):
    qs = session.client('quicksight')
    sts_client = session.client("sts")
    account_id = sts_client.get_caller_identity()["Account"]
    response = qs.create_folder_membership(
        AwsAccountId=account_id,
        FolderId=FolderId,
        MemberId=MemberId,
        MemberType=MemberType
    )
    return response

def migrate_analysis(source_session, target_session, id):
    # please provide the analysis name you would like to migrate to get the id
    faillist = []
    try:
        analysisid = get_analysis_ids('analysis_name', source_session)
    except Exception as e:
        faillist.append({"object_id": 'id', "Name": 'name', "object_type": 'type',
                         "action": 'incremental_migration:get_source_analysis_id', "Error": str(e)})

    if len(analysisid) > 1:
        raise ValueError('There are more than one analysis with the same name. Please check it.')
    return


def process_migration_list(migrate_p, dashboard_migrate_list, analysis_migrate_list, dev_config):
    source_migrate_list = []
    dataset_migrate_list = []
    source_session = s_func._assume_role(dev_config["aws_account_number"], dev_config["role_name"],
                                         dev_config["aws_region"])

    if migrate_p in ['dashboard']:
        for dashboard in dashboard_migrate_list:
            print(dashboard)
            datasources = data_sources_ls_of_dashboard(dashboard, source_session)
            print(datasources)  # issue
            for datasource in datasources:
                source_migrate_list.append(datasource)
            datasets = data_sets_ls_of_dashboard(dashboard, source_session)
            print(datasets)
            for dataset in datasets:
                dataset_migrate_list.append(dataset)

    if migrate_p in ['analysis']:
        for analysis_name in analysis_migrate_list:
            print(analysis_name)
            datasources = data_sources_ls_of_analysis(analysis_name, source_session)
            print(datasources)
            for datasource in datasources:
                source_migrate_list.append(datasource)
            datasets = data_sets_ls_of_analysis(analysis_name, source_session)
            print(datasets)
            for dataset in datasets:
                dataset_migrate_list.append(dataset)
            print(dataset_migrate_list)

    if migrate_p in ['all']:
        for dashboard in dashboard_migrate_list:
            datasources = data_sources_ls_of_dashboard(dashboard, source_session)
            for datasource in datasources:
                source_migrate_list.append(datasource)
            datasets = data_sets_ls_of_dashboard(dashboard, source_session)
            for dataset in datasets:
                dataset_migrate_list.append(dataset)

        for analysis_name in analysis_migrate_list:
            datasources = data_sources_ls_of_analysis(analysis_name, source_session)
            for datasource in datasources:
                source_migrate_list.append(datasource)
            datasets = data_sets_ls_of_analysis(analysis_name, source_session)
            for dataset in datasets:
                dataset_migrate_list.append(dataset)
    results = {"source_migrate_list": source_migrate_list, "dataset_migrate_list": dataset_migrate_list}
    print(results)

    return results


# get 2nd_class objects
def get_sheets(session, analysisid, page=0):
    analysis_contents = describe_analysis_definition(session, analysisid)
    if page != 0:
        return analysis_contents['Sheets'][page]
    else:
        return analysis_contents['Sheets']


def get_cfs(session, id, cfname='none'):
    contents = describe_analysis_definition(session, id)
    if cfname != 'none':
        for cf in contents['CalculatedFields']:
            if cf['Name'] == cfname:
                return cf['Expression']
            else:
                return cfname + ' is not exisitng! Please check the dataset definition again.'
    else:
        return contents['CalculatedFields']


def get_parameter(session, id, type, pname='none'):
    if type == 'analysis':
        contents = describe_analysis_definition(session, id)
    elif type == 'dashboard':
        contents = describe_dashboard_definition(session, id)
    if pname != 'none':
        for p in contents['ParameterDeclarations']:
            for key in p:
                if p[key]['Name'] == pname:
                    return p
                else:
                    return pname + ' is not exisitng! Please check the dataset definition again.'
    else:
        return contents['ParameterDeclarations']


# update target dataset with folders
def update_dataset_folders(session, DSID, Folders):
    qs = session.client('quicksight')
    sts_client = session.client("sts")
    AccountId = sts_client.get_caller_identity()["Account"]
    response = describe_data_set(session, DSID)
    args: Dict[str, Any] = {
        "AwsAccountId": AccountId,
        "DataSetId": DSID,
        "Name": response["DataSet"]["Name"],
        "PhysicalTableMap": response["DataSet"]["PhysicalTableMap"],
        "LogicalTableMap": response["DataSet"]["LogicalTableMap"],
        "ImportMode": response["DataSet"]["ImportMode"],
        "FieldFolders": Folders
    }
    response = qs.update_data_set(**args)
    return response


def update_dataset_2(session, DataSetId, component_type, component_body):
    qs = session.client('quicksight')
    sts_client = session.client("sts")
    AccountId = sts_client.get_caller_identity()["Account"]
    response = describe_data_set(session, DataSetId)
    args: Dict[str, Any] = {
        "AwsAccountId": AccountId,
        "DataSetId": DataSetId,
        "Name": response["DataSet"]["Name"],
        "PhysicalTableMap": response["DataSet"]["PhysicalTableMap"],
        "LogicalTableMap": response["DataSet"]["LogicalTableMap"],
        "ImportMode": response["DataSet"]["ImportMode"],
        "FieldFolders": response["DataSet"]["FieldFolders"]
    }
    if component_type == '':
        response = qs.update_data_set(**args)
    elif component_type == 'Cf':
        num = list(args["LogicalTableMap"].keys())[0]
        print(num)
        create_column = {"CreateColumnsOperation": {}}
        body = {"ColumnName": component_body["Name"], "ColumnId": component_body["Name"],
                "Expression": component_body["Expression"]}
        create_column["CreateColumnsOperation"]["Columns"] = [body]
        args["LogicalTableMap"][num]["DataTransforms"].append(create_column)
        for item in args["LogicalTableMap"][num]["DataTransforms"]:
            try:
                item["ProjectOperation"]["ProjectedColumns"].append(component_body["Name"])
            except:
                continue
        response = qs.update_data_set(**args)
    elif component_type == 'FilterOperation':
        num = list(args["LogicalTableMap"].keys())[0]
        filter = {}
        body = {"ConditionExpression": component_body}
        filter["FilterOperation"] = body
        args["LogicalTableMap"][num]["DataTransforms"].append(filter)
        response = qs.update_data_set(**args)
    else:
        args[component_type] = component_body
        response = qs.update_data_set(**args)
    return response


# full or partial folder creation from source dataset,
# folder_list can either be [] for all folders or be a list of desired folders
def folder_creation_source_dataset(session, source_dataset_id, target_dataset_id, folder_list):
    target_columns = describe_data_set(session, target_dataset_id)['DataSet']['OutputColumns']
    source_dictionary = describe_data_set(session, source_dataset_id)['DataSet']['FieldFolders']
    dictionary = {}
    # check for (folder, column) pair in dictionary
    for column in target_columns:
        keys = [k for k, v in source_dictionary.items() if column['Name'] in v['columns']]
        if keys != []:
            key = keys[0]
            if folder_list == [] or key in folder_list:
                # add keys to new folder dictionary if it doesn't already exist
                if key not in dictionary:
                    dictionary[key] = {}
                    if 'description' in source_dictionary[key]:
                        dictionary[key]['description'] = source_dictionary[key]['description']
                    dictionary[key]['columns'] = list()
                dictionary[key]['columns'].append(column['Name'])
    update_dataset_2(session, target_dataset_id, "FieldFolders", dictionary)
    return


# folder creation with dictionary of folders as input
def folder_creation_dictionary(session, target_dataset_id, folder_dict):
    target_columns = describe_data_set(session, target_dataset_id)['DataSet']['OutputColumns']
    dictionary = {}
    # check for (folder, column) pair in dictionary
    for column in target_columns:
        keys = [k for k, v in folder_dict.items() if column['Name'] in v['columns']]
        if keys != []:
            key = keys[0]
            # add keys to new folder dictionary if it doesn't already exist
            if key not in dictionary:
                dictionary[key] = {}
                if 'description' in folder_dict[key]:
                    dictionary[key]['description'] = folder_dict[key]['description']
                dictionary[key]['columns'] = list()
            dictionary[key]['columns'].append(column['Name'])
    update_dataset_2(session, target_dataset_id, "FieldFolders", dictionary)
    return


# folder creation with csv of folders as input
def folder_creation_csv(session, target_dataset_id, csv):
    folder_dict = dict()
    f = open(csv)
    # parse csv file
    for line in f:
        line = line.strip('\n')
        splitted = line.split(",")
        folder_dict[splitted[0]] = list()
        for word in splitted[1:]:
            folder_dict[splitted[0]].append(word.strip('"'))
    target_columns = describe_data_set(session, target_dataset_id)['DataSet']['OutputColumns']
    dictionary = {}
    # check for (folder, column) pair in dictionary
    for column in target_columns:
        keys = [k for k, v in folder_dict.items() if column['Name'] in v['columns']]
        if keys != []:
            key = keys[0]
            if key not in dictionary:
                dictionary[key] = {}
                if 'description' in folder_dict[key]:
                    dictionary[key]['description'] = folder_dict[key]['description']
                dictionary[key]['columns'] = list()
            dictionary[key]['columns'].append(column['Name'])
    update_dataset_2(session, target_dataset_id, "FieldFolders", dictionary)
    return

# DELETES ALL ASSETS IN FOLDER
# Used for Release folder
def reset_folder(session, account, folder):
    print('Deleting all assets in folder: ', folder)
    folder_queue = [folder]
    while len(folder_queue) > 0:
        cur_folder = folder_queue.pop()
        cur_fid = cur_folder.split("/")[1]
        try:
            message = []
            for member in list_folder_members(session, cur_fid):
                member_type = ''
                if 'release' not in member['MemberArn']:
                    raise Exception('WARNING Unexpected ARN does not contain \'release\': ' + member['MemberArn'])
                if 'dataset' in member['MemberArn']:
                    delete_dataset(session, member['MemberId'])
                elif 'dashboard' in member['MemberArn']:
                    delete_dashboard(session, member['MemberId'])
                elif 'analysis' in member['MemberArn']:
                    raise Exception('Analysis migration is not supported.')
                else:
                    raise Exception('Member Type not found')
                print('Deleted -', member['MemberArn'])
                message.append(member['MemberId'])
            for folder in search_folders(session, cur_folder):
                folder_queue.append(folder['Arn'])
            print('Finished deleting assets.')
            return message
        except Exception as e:
            message = {"account_id": account, "folder_id": cur_fid, "error": str(e)}
            return message

# Makes copies of assets and moves them from Review to QA folder
def review_to_qa(session, account, region, ids):
    print('Copying and removing all assets from folder: ', ids["Review"], 'to ', ids["QA"])
    message = []
    if ids["QAAssetIds"] == []:
        return message
    folder_queue = [ids["Review"]]
    tgt_fid = ids["QA"].split("/")[1]
    parent_fid = ids["Review"].split("/")[1]
    already_created = set()
    while len(folder_queue) > 0:
        cur_folder = folder_queue.pop()
        cur_fid = cur_folder.split("/")[1]
        folder_members = list_folder_members(session, cur_fid)
        print('cur_fid: ' + cur_fid)
        print(folder_members)
        print(already_created)
        for member in folder_members:
            if member['MemberId'] in ids["QAAssetIds"]:
                newid = 'release-' + member['MemberId']
                print(member['MemberId'])
                member_type = ''
                if 'dataset' in member['MemberArn']:
                    member_type = 'DATASET'
                    if newid not in already_created:
                        already_created.add(newid)
                        res = describe_data_set(session, member['MemberId'])
                        create_data_set(session, newid, res['DataSet']['Name'], res['DataSet']['PhysicalTableMap'],
                                        res['DataSet']['LogicalTableMap'],
                                        res['DataSet']['ImportMode'])
                elif 'dashboard' in member['MemberArn']:
                    member_type = 'DASHBOARD'
                    if newid not in already_created:
                        already_created.add(newid)
                        res = describe_dashboard_definition(session, member['MemberId'])
                        dataset_arns = res['Definition']['DataSetIdentifierDeclarations']
                        for dataset_arn in dataset_arns:
                            if 'DataSetArn' in dataset_arn.keys():
                                target_dataset_id = 'release-' + dataset_arn['DataSetArn'].split("/")[1]
                                target_dataset_arn = 'arn:aws:quicksight:' + region + ':' + account + ':dataset/' + target_dataset_id
                                dataset_arn['DataSetArn'] = target_dataset_arn
                        TargetThemeArn = ''
                        if 'ThemeArn' in res['Definition'].keys():
                            TargetThemeArn = res['Definition']['ThemeArn']
                        create_dashboard(session, newid, member['MemberId'], res['Dashboard']['Name'], res,
                                        'ENABLED', 'ENABLED', 'COLLAPSED', ('VersionDescription', '1'),
                                        ('ThemeArn', TargetThemeArn))
                elif 'analysis' in member['MemberArn']:
                    raise Exception('Analysis migration is not supported. Please publish as a dashboard')
                else:
                    raise Exception('Member Type not found')
                delete_folder_membership(session, cur_fid, member['MemberId'], member_type)
                create_folder_membership(session, cur_fid.replace(parent_fid, tgt_fid), newid, member_type)
                print('Copied from Review folder to QA folder - ', member['MemberArn'])
                message.append(member['MemberId'])
        for folder in search_folders(session, cur_folder):
            folder_queue.append(folder['Arn'])
    print('Finished copying and removing all assets.')
    return message

# Moves assets from QA to Release folder
def qa_to_release(session, ids):
    print('Moving and removing all assets from folder: ', ids["QA"], 'to ', ids["Release"])
    message = []
    if ids["ReleaseAssetIds"] == []:
        return message
    folder_queue = [ids["QA"]]
    tgt_fid = ids["Release"].split("/")[1]
    parent_fid = ids["QA"].split("/")[1]
    while len(folder_queue) > 0:
        cur_folder = folder_queue.pop()
        cur_fid = cur_folder.split("/")[1]
        folder_members = list_folder_members(session, cur_fid)
        print('cur_fid: ' + cur_fid)
        print(folder_members)
        for member in folder_members:
            if member['MemberId'] in ids["ReleaseAssetIds"]:
                member_type = ''
                if 'dataset' in member['MemberArn']:
                    member_type = 'DATASET'
                elif 'dashboard' in member['MemberArn']:
                    member_type = 'DASHBOARD'
                elif 'analysis' in member['MemberArn']:
                    raise Exception('Analysis migration is not supported. Please publish as a dashboard')
                else:
                    raise Exception('Member Type not found')
                delete_folder_membership(session, cur_fid, member['MemberId'], member_type)
                create_folder_membership(session, cur_fid.replace(parent_fid, tgt_fid), member['MemberId'],
                                            member_type)
                print('Moved from QA folder to Release folder - ', member['MemberArn'])
                message.append(member['MemberId'])
        for folder in search_folders(session, cur_folder):
            folder_queue.append(folder['Arn'])
    print('Finished moving and removing all assets.')
    return message
