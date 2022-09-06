
"""
QuickSight Utils is a module of functions to interact with QuickSight APIs.
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

from datetime import date, datetime


logging.basicConfig(level=os.environ.get("LOGLEVEL", "INFO"))
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

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
    qs_client = session.client('quicksight')
    sts_client = session.client("sts")
    account_id = sts_client.get_caller_identity()["Account"]
    try:
        response = qs_client.describe_data_source(
            AwsAccountId=account_id,
            DataSourceId=DSID
        )
    except ClientError as exc:
        logger.error("Failed to describe data source %s", DSID)
        logger.error(exc.response['Error']['Message'])
    return response


def describe_data_set(session, DSID):
    qs_client = session.client('quicksight')
    sts_client = session.client("sts")
    account_id = sts_client.get_caller_identity()["Account"]
    try:
        response = qs_client.describe_data_set(
            AwsAccountId=account_id,
            DataSetId=DSID
        )
    except ClientError as exc:
        logger.error("Failed to describe data set %s", DSID)
        logger.error(exc.response['Error']['Message'])
        print(exc)
        raise exc
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
        return ('Failed to describe dashboard: ' + str(e))
    else:
        return response


def describe_template(session, tid):
    qs_client = session.client('quicksight')
    sts_client = session.client("sts")
    account_id = sts_client.get_caller_identity()["Account"]
    try:
        response = qs_client.describe_template(
            AwsAccountId=account_id,
            TemplateId=tid
        )
    except ClientError as exc:
        logger.error("Failed to describe template %s", tid)
        logger.error(exc.response['Error']['Message'])
        return False
    return response

def describe_template_permissions(session, template_id):
    qs_client = session.client('quicksight')
    sts_client = session.client("sts")
    account_id = sts_client.get_caller_identity()["Account"]
    try:
        response = qs_client.describe_template_permissions(
            AwsAccountId=account_id,
            TemplateId=template_id
        )
    except ClientError as exc:
        logger.error("Failed to describe template %s", template_id)
        logger.error(exc.response['Error']['Message'])
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
        return ('Failed to describe analysis: ' + str(e))
    else:
        return response


def describe_theme(session, theme_id):
    qs_client = session.client('quicksight')
    sts_client = session.client("sts")
    account_id = sts_client.get_caller_identity()["Account"]
    try:
        response = qs_client.describe_theme(
            AwsAccountId=account_id,
            ThemeId=theme_id
        )
    except ClientError as exc:
        logger.error("Failed to describe theme %s", theme_id)
        logger.error(exc.response['Error']['Message'])
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
def create_dataset(session, dataset_id, name, physical, logical, 
                    mode, permissions, column_groups=None,
                   RowLevelPermissionDataSet=None, RowLevelPermissionTagConfiguration=None,
                   FieldFolders=None, ColumnLevelPermissionRules=None, DataSetUsageConfiguration=None):
    qs_client = session.client('quicksight')
    sts_client = session.client("sts")
    account_id = sts_client.get_caller_identity()["Account"]
    logger.info('account_id is: %s', account_id)
    args: Dict[str, Any] = {
        "AwsAccountId": account_id,
        "DataSetId": dataset_id,
        "Name": name,
        "PhysicalTableMap": physical,
        "LogicalTableMap": logical,
        "ImportMode": mode,
        "Permissions": permissions,
    }
    if column_groups:
        args["ColumnGroups"] = column_groups
    if RowLevelPermissionDataSet:
        args["RowLevelPermissionDataSet"] = RowLevelPermissionDataSet
    if RowLevelPermissionTagConfiguration:
        args["RowLevelPermissionTagConfiguration"] = RowLevelPermissionTagConfiguration
    if FieldFolders:
        args["FieldFolders"] = FieldFolders
    if ColumnLevelPermissionRules:
        args["ColumnLevelPermissionRules"] = ColumnLevelPermissionRules
    if DataSetUsageConfiguration:
        args["DataSetUsageConfiguration"] = DataSetUsageConfiguration

    try:
        response = qs_client.create_data_set(**args)
    except ClientError as exc:
        logger.error("Failed to create data set %s", dataset_id)
        logger.error(exc.response['Error']['Message'])
    return response

#check again
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

#check again
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

#check again
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

#check again
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


def create_folder_membership(session, folderid, objectid, objecttype):
    qs_client = session.client('quicksight')
    sts_client = session.client("sts")
    account_id = sts_client.get_caller_identity()["Account"]
    try:
        response = qs_client.create_folder_membership(
            AwsAccountId = account_id,
            FolderId=folderid,
            MemberId=objectid,
            MemberType=objecttype
        )
    except ClientError as exc:
        logger.error("Failed to create folder membership with folder id: %s, object_id: %s", folderid, objectid)
        logger.error(exc.response['Error']['Message'])
    return response


"""
copy functions
"""

#check again
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
def update_dataset(session, dataset_id, name, physical, logical, mode,
                   column_groups=None, RowLevelPermissionDataSet=None, RowLevelPermissionTagConfiguration=None,
                   FieldFolders=None, ColumnLevelPermissionRules=None, DataSetUsageConfiguration=None):
    qs_client = session.client('quicksight')
    sts_client = session.client("sts")
    account_id = sts_client.get_caller_identity()["Account"]
    args: Dict[str, Any] = {
        "AwsAccountId": account_id,
        "DataSetId": dataset_id,
        "Name": name,
        "PhysicalTableMap": physical,
        "LogicalTableMap": logical,
        "ImportMode": mode,
    }
    if column_groups:
        args["ColumnGroups"] = column_groups
    if RowLevelPermissionDataSet:
        args["RowLevelPermissionDataSet"] = RowLevelPermissionDataSet
    if RowLevelPermissionTagConfiguration:
        args["RowLevelPermissionTagConfiguration"] = RowLevelPermissionTagConfiguration
    if FieldFolders:
        args["FieldFolders"] = FieldFolders
    if ColumnLevelPermissionRules:
        args["ColumnLevelPermissionRules"] = ColumnLevelPermissionRules
    if DataSetUsageConfiguration:
        args["DataSetUsageConfiguration"] = DataSetUsageConfiguration

    try:
        response = qs_client.update_data_set(**args)
    except ClientError as exc:
        logger.error("Failed to update data set %s", dataset_id)
        logger.error(exc.response['Error']['Message'])
    return response

#check again
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


def update_dashboard(session, dashboard, name, source_entity, version, 
                        filter='ENABLED',csv='ENABLED', sheetcontrol='EXPANDED'):
    qs_client = session.client('quicksight')
    sts_client = session.client("sts")
    account_id = sts_client.get_caller_identity()["Account"]

    try:
        response = qs_client.update_dashboard(
            AwsAccountId=account_id,
            DashboardId=dashboard,
            Name=name,
            SourceEntity=source_entity,
            VersionDescription=version,
            DashboardPublishOptions={
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
        )
    except ClientError as exc:
        logger.error("Failed to update dashboard %s", dashboard)
        logger.error(exc.response['Error']['Message'])
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


def update_data_source_permissions(session, datasourceid, principal):
    qs_client = session.client('quicksight')
    sts_client = session.client("sts")
    account_id = sts_client.get_caller_identity()["Account"]

    try:
        response = qs_client.update_data_source_permissions(
                        AwsAccountId=account_id,
                        DataSourceId=datasourceid,
                        GrantPermissions=[
                            {
                                'Principal': principal,
                                'Actions':[
                                    "quicksight:DescribeDataSource",
                                    "quicksight:DescribeDataSourcePermissions",
                                    "quicksight:PassDataSource",
                                    "quicksight:UpdateDataSource",
                                    "quicksight:DeleteDataSource",
                                    "quicksight:UpdateDataSourcePermissions"
                                ]
                            }
                        ]
                    )
    except ClientError as exc:
        logger.error("Failed to update data source permissions %s", datasourceid)
        logger.error(exc.response['Error']['Message'])
    return response


def update_data_set_permissions(session, datasetid, principal):
    qs_client = session.client('quicksight')
    sts_client = session.client("sts")
    account_id = sts_client.get_caller_identity()["Account"]

    try:
        response = qs_client.update_data_set_permissions(
                        AwsAccountId=account_id,
                        DataSetId=datasetid,
                        GrantPermissions=[
                            {
                                'Principal': principal,
                                'Actions':[
                                    'quicksight:UpdateDataSetPermissions',
                                    'quicksight:DescribeDataSet',
                                    'quicksight:DescribeDataSetPermissions',
                                    'quicksight:PassDataSet',
                                    'quicksight:DescribeIngestion',
                                    'quicksight:ListIngestions',
                                    'quicksight:UpdateDataSet',
                                    'quicksight:DeleteDataSet',
                                    'quicksight:CreateIngestion',
                                    'quicksight:CancelIngestion'
                                ]
                            }
                        ]
                    )
    except ClientError as exc:
        logger.error("Failed to update data set permissions %s", datasetid)
        logger.error(exc.response['Error']['Message'])
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


def delete_source(session, data_source_id):
    qs_client = session.client('quicksight')
    sts_client = session.client("sts")
    account_id = sts_client.get_caller_identity()["Account"]
    try:
        delsource = qs_client.delete_data_source(
            AwsAccountId=account_id,
            DataSourceId=data_source_id
        )
    except ClientError as exc:
        logger.error("Failed to delete data source %s", data_source_id)
        logger.error(exc.response['Error']['Message'])
    return delsource


def delete_dataset(session, dataset_id):
    qs_client = session.client('quicksight')
    sts_client = session.client("sts")
    account_id = sts_client.get_caller_identity()["Account"]
    try:
        response = qs_client.delete_data_set(
            AwsAccountId=account_id,
            DataSetId=dataset_id
        )
    except ClientError as exc:
        logger.error("Failed to delete data set %s", dataset_id)
        logger.error(exc.response['Error']['Message'])
    return response


def delete_template(session, tid, version=None):
    qs_client = session.client('quicksight')
    sts_client = session.client("sts")
    account_id = sts_client.get_caller_identity()["Account"]
    args: Dict[str, Any] = {
        "AwsAccountId": account_id,
        "TemplateId": tid,
    }
    if version:
        args["VersionNumber"] = version
    try:
        response = qs_client.delete_template(**args)
    except ClientError as exc:
        logger.error("Failed to delete template %s", tid)
        logger.error(exc.response['Error']['Message'])
    return response

def delete_dashboard(session, did):
    qs_client = session.client('quicksight')
    sts_client = session.client("sts")
    account_id = sts_client.get_caller_identity()["Account"]
    try:
        response = qs_client.delete_dashboard(
            AwsAccountId=account_id,
            DashboardId=did
        )
    except ClientError as exc:
        logger.error("Failed to delete dashboard %s", did)
        logger.error(exc.response['Error']['Message'])
    return response


def delete_analysis(session, did):
    qs_client = session.client('quicksight')
    sts_client = session.client("sts")
    account_id = sts_client.get_caller_identity()["Account"]
    try:
        response = qs_client.delete_analysis(
            AwsAccountId=account_id,
            AnalysisId=did
        )
    except ClientError as exc:
        logger.error("Failed to delete analysis %s", did)
        logger.error(exc.response['Error']['Message'])
    return response

def delete_theme(session, theme_id):
    qs_client = session.client('quicksight')
    sts_client = session.client("sts")
    account_id = sts_client.get_caller_identity()["Account"]
    try:
        response = qs_client.delete_theme(
            AwsAccountId=account_id,
            ThemeId=theme_id
        )
    except ClientError as exc:
        logger.error("Failed to delete theme %s", theme_id)
        logger.error(exc.response['Error']['Message'])
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

def get_data_source_migration_list(sourcesession,source_migrate_list):
    datasources = data_sources(sourcesession)  #get data source details with listdatasource API

    migration_list=[]
    for newsource in source_migrate_list:
        ids = get_datasource_ids(newsource, sourcesession) #Get id of data sources migration list
        for datasource in datasources:
            if ids[0] == datasource["DataSourceId"]:
                # migration_list is an array containing data source connection information and etc
                migration_list.append(datasource)

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

#List current Data sources/datasets
def data_sources(session):
    qs_client = session.client('quicksight')
    sts_client = session.client("sts")
    account_id = sts_client.get_caller_identity()["Account"]
    datasources = []
    try:
        response = qs_client.list_data_sources(AwsAccountId=account_id)
    except ClientError as exc:
        logger.error("Failed to list data sources")
        logger.error(exc.response['Error']['Message'])
    next_token: str = response.get("NextToken", None)
    datasources += response["DataSources"]
    while next_token is not None:
        try:
            response = qs_client.list_data_sources(AwsAccountId=account_id, NextToken=next_token)
        except ClientError as exc:
            logger.error("Failed to list data sources")
            logger.error(exc.response['Error']['Message'])
        next_token = response.get("NextToken", None)
        datasources += response["DataSources"]
    return datasources

def data_sets(session):
    qs_client = session.client('quicksight')
    sts_client = session.client("sts")
    account_id = sts_client.get_caller_identity()["Account"]
    datasets = []
    try:
        response = qs_client.list_data_sets(AwsAccountId=account_id)
    except ClientError as exc:
        logger.error("Failed to list data sets")
        logger.error(exc.response['Error']['Message'])
    next_token: str = response.get("NextToken", None)
    datasets += response["DataSetSummaries"]
    while next_token is not None:
        try:
            response = qs_client.list_data_sets(AwsAccountId=account_id, NextToken=next_token)
        except ClientError as exc:
            logger.error("Failed to list data sets")
            logger.error(exc.response['Error']['Message'])
        next_token = response.get("NextToken", None)
        datasets += response["DataSetSummaries"]
    return datasets

def templates(session):
    qs_client = session.client('quicksight')
    sts_client = session.client("sts")
    account_id = sts_client.get_caller_identity()["Account"]
    token=None

    args: Dict[str, Any] = {
        "AwsAccountId": account_id,
        "MaxResults": 100,
    }
    try:
        tlist = qs_client.list_templates(**args)
    except ClientError as exc:
        logger.error("Failed to list templates")
        logger.error(exc.response['Error']['Message'])
    templates=tlist['TemplateSummaryList']

    if 'NextToken' in tlist:
        token=tlist['NextToken']
        while token is not None:
            args["NextToken"] = token
            try:
                tlist=qs_client.list_templates(**args)
            except ClientError as exc:
                logger.error("Failed to list templates")
                logger.error(exc.response['Error']['Message'])
            templates.append(tlist['TemplateSummaryList'])
            token = tlist.get("NextToken", None)
    else:
        pass
    return templates

def dashboards(session)-> List[Dict[str, Any]]:
    qs_client = session.client('quicksight')
    sts_client = session.client("sts")
    account_id = sts_client.get_caller_identity()["Account"]
    dashboards = []
    try:
        response = qs_client.list_dashboards(AwsAccountId=account_id)
    except ClientError as exc:
        logger.error("Failed to list dashboards")
        logger.error(exc.response['Error']['Message'])
    next_token: str = response.get("NextToken", None)
    dashboards += response["DashboardSummaryList"]
    while next_token is not None:
        try:
            response = qs_client.list_dashboards(AwsAccountId=account_id, NextToken=next_token)
        except ClientError as exc:
            logger.error("Failed to list dashboards")
            logger.error(exc.response['Error']['Message'])
        next_token = response.get("NextToken", None)
        dashboards += response["DashboardSummaryList"]
    return dashboards

def analysis(session):
    qs_client = session.client('quicksight')
    sts_client = session.client("sts")
    account_id = sts_client.get_caller_identity()["Account"]
    analysis = []
    try:
        response = qs_client.list_analyses(AwsAccountId=account_id)
    except ClientError as exc:
        logger.error("Failed to list analyses")
        logger.error(exc.response['Error']['Message'])
    next_token: str = response.get("NextToken", None)
    analysis += response["AnalysisSummaryList"]
    while next_token is not None:
        try:
            response = qs_client.list_analyses(AwsAccountId=account_id, NextToken=next_token)
        except ClientError as exc:
            logger.error("Failed to list analyses")
            logger.error(exc.response['Error']['Message'])
        next_token = response.get("NextToken", None)
        analysis += response["AnalysisSummaryList"]
    return analysis

def themes(session):
    qs_client = session.client('quicksight')
    sts_client = session.client("sts")
    account_id = sts_client.get_caller_identity()["Account"]
    themes = []
    try:
        response = qs_client.list_themes(AwsAccountId=account_id)
    except ClientError as exc:
        logger.error("Failed to list themes")
        logger.error(exc.response['Error']['Message'])
    next_token: str = response.get("NextToken", None)
    themes += response["ThemeSummaryList"]
    while next_token is not None:
        try:
            response = qs_client.list_themes(AwsAccountId=account_id, NextToken=next_token)
        except ClientError as exc:
            logger.error("Failed to list themes")
            logger.error(exc.response['Error']['Message'])
        next_token = response.get("NextToken", None)
        themes += response["ThemeSummaryList"]
    return themes

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