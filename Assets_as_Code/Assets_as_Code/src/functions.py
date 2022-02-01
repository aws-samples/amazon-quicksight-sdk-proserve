import traceback
import boto3
import botocore.session
import json
import time
import logging
import csv
from datetime import datetime
from typing import Any, Dict, List, Optional
from Assets_as_Code.Assets_as_Code.src import supportive_functions as s_func




#session = botocore.session.get_session()
#client = session.create_client("quicksight", region_name='us-east-1')
#response = client.create_ingestion(AwsAccountId = account_id, DataSetId=’MyDataSetId’, IngestionId='MyIngestion1')

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


def describe_data_source(session, DSID):
    qs = session.client('quicksight')
    sts_client = session.client("sts")
    AccountId = sts_client.get_caller_identity()["Account"]
    response = qs.describe_data_source(
        AwsAccountId=AccountId,
        DataSourceId=DSID)
    return response


# Describe a Dataset
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
        #print(response)
        return response
        #return response['Analysis']

def describe_dashboard_definition(session, id):
    qs = session.client('quicksight')
    sts_client = session.client("sts")
    account_id = sts_client.get_caller_identity()["Account"]
    try:
        response = qs.describe_dashboard_contents(
            AwsAccountId=account_id,
            AnalysisId=id)
    except Exception as e:
        return ('Faild to describe analysis: ' + str(e))
    else:
        return response['Dashboard']


# create objects
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
def create_data_set(session, DataSetId, Name, Physical, Logical, Mode, Permissions, ColumnGroups=None, FieldFolders=None):
    qs = session.client('quicksight')
    sts_client = session.client("sts")
    AccountId = sts_client.get_caller_identity()["Account"]
    args: Dict[str, Any] = {
        "AwsAccountId": AccountId,
        "DataSetId": DataSetId,
        "Name": Name,
        "PhysicalTableMap": Physical,
        "LogicalTableMap": Logical,
        "ImportMode": Mode,
        "Permissions": Permissions,
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
    #assert isinstance(TemplateId, int), ''
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

def copy_template(session, TemplateId, tname, SourceTemplatearn):
    qs = session.client('quicksight')
    sts_client = session.client("sts")
    account_id = sts_client.get_caller_identity()["Account"]
    try:
        delete_template(session, TemplateId)
    except Exception:
        print(traceback.format_exc())
    #assert isinstance(TemplateId, int), ''
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

def copy_analysis(session, source, Id, Name, principal, Permissions = 'owner', region='us-east-1'):
    qs = session.client('quicksight')
    sts_client = session.client("sts")
    AccountId = sts_client.get_caller_identity()["Account"]
    args: Dict[str, Any] = {
        "AwsAccountId":  AccountId,
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
    if Permissions == 'owner':
        args["Permissions"] = [
                {
                    'Principal': principal,
                    'Actions': [
                        'quicksight:RestoreAnalysis',
                        'quicksight:UpdateAnalysisPermissions',
                        'quicksight:DeleteAnalysis',
                        'quicksight:QueryAnalysis',
                        'quicksight:DescribeAnalysisPermissions',
                        'quicksight:DescribeAnalysis',
                        'quicksight:UpdateAnalysis'

                    ]
                }
            ]
    elif Permissions == 'user':
        args["Permissions"] = [
                {
                    'Principal': principal,
                    'Actions': [
                        'quicksight:QueryAnalysis',
                        'quicksight:DescribeAnalysis'
                    ]
                }
            ]
    print(args)
    response = qs.create_analysis(**args)
    return response

def incremental_migration(dev_config, prod_config,migrate_p, m_list):
    source_session = s_func._assume_role(dev_config["aws_account_number"], dev_config["role_name"],
                                         dev_config["aws_region"])
    target_session = s_func._assume_role(prod_config["aws_account_number"], prod_config["role_name"],
                                         prod_config["aws_region"])
    """
    # current date and time
    """
    now = str(datetime.now().strftime("%m-%d-%Y_%H_%M"))
    return

def migrate_analysis(source_session, target_session, id):
    # please provide the analysis name you would like to migrate to get the id
    faillist = []
    try:
        analysisid = func.get_analysis_ids('analysis_name', source_session)
    except Exception as e:
        faillist.append({"object_id": 'id', "Name": 'name', "object_type": 'type',
                         "action": 'incremental_migration:get_source_analysis_id', "Error": str(e)})

    if len(analysisid) > 1:
        raise ValueError('There are more than one analysis with the same name. Please check it.')
    return

def process_migration_list(migrate_p, list, dev_config):
    source_migrate_list = []
    dataset_migrate_list = []
    source_session = s_func._assume_role(dev_config["aws_account_number"], dev_config["role_name"],
                                         dev_config["aws_region"])
    if migrate_p in ['dashboard']:
        for dashboard in list:
            print(dashboard)
            datasources = data_sources_ls_of_dashboard(dashboard, source_session)
            print(datasources)
            for datasource in datasources:
                source_migrate_list.append(datasource)
            datasets = data_sets_ls_of_dashboard(dashboard, source_session)
            print(datasets)
            for dataset in datasets:
                dataset_migrate_list.append(dataset)

    if migrate_p in ['analysis']:
        for analysis_name in list:
            print(analysis_name)
            datasources = data_sources_ls_of_analysis(analysis_name, sourcesession)
            print(datasources)
            for datasource in datasources:
                source_migrate_list.append(datasource)
            datasets = data_sets_ls_of_analysis(analysis_name, sourcesession)
            print(datasets)
            for dataset in datasets:
                dataset_migrate_list.append(dataset)

    if migrate_p in ['all']:
        for dashboard in list:
            datasources = data_sources_ls_of_dashboard(dashboard, sourcesession)
            for datasource in datasources:
                source_migrate_list.append(datasource)
            datasets = data_sets_ls_of_dashboard(dashboard, sourcesession)
            for dataset in datasets:
                dataset_migrate_list.append(dataset)

        for analysis_name in list:
            datasources = data_sources_ls_of_analysis(analysis_name, sourcesession)
            for datasource in datasources:
                source_migrate_list.append(datasource)
            datasets = data_sets_ls_of_analysis(analysis_name, sourcesession)
            for dataset in datasets:
                dataset_migrate_list.append(dataset)
    results = {"source_migrate_list": source_migrate_list, "dataset_migrate_list": dataset_migrate_list}
    return results

def create_dashboard(session, dashboard, name, principal, SourceEntity, version, themearn, filter='ENABLED',
                     csv='ENABLED', sheetcontrol='EXPANDED'):
    qs = session.client('quicksight')
    sts_client = session.client("sts")
    account_id = sts_client.get_caller_identity()["Account"]
    if themearn == '':
        response = qs.create_dashboard(
            AwsAccountId=account_id,
            DashboardId=dashboard,
            Name=name,
            Permissions=[
                {
                    'Principal': principal,
                    'Actions': [
                        'quicksight:DescribeDashboard',
                        'quicksight:ListDashboardVersions',
                        'quicksight:UpdateDashboardPermissions',
                        'quicksight:QueryDashboard',
                        'quicksight:UpdateDashboard',
                        'quicksight:DeleteDashboard',
                        'quicksight:DescribeDashboardPermissions',
                        'quicksight:UpdateDashboardPublishedVersion'
                    ]
                },
            ],
            SourceEntity=SourceEntity,
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
    else:
        response = qs.create_dashboard(
            AwsAccountId=account_id,
            DashboardId=dashboard,
            Name=name,
            Permissions=[
                {
                    'Principal': principal,
                    'Actions': [
                        'quicksight:DescribeDashboard',
                        'quicksight:ListDashboardVersions',
                        'quicksight:UpdateDashboardPermissions',
                        'quicksight:QueryDashboard',
                        'quicksight:UpdateDashboard',
                        'quicksight:DeleteDashboard',
                        'quicksight:DescribeDashboardPermissions',
                        'quicksight:UpdateDashboardPublishedVersion'
                    ]
                },
            ],
            SourceEntity=SourceEntity,
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
            },
            ThemeArn=themearn
        )

    return response


def create_analysis_old(session, analysis_id, name, principal, SourceEntity, ThemeArn):
    qs = session.client('quicksight')
    sts_client = session.client("sts")
    account_id = sts_client.get_caller_identity()["Account"]
    if ThemeArn != '':
        response = qs.create_analysis(
            AwsAccountId=account_id,
            AnalysisId=analysis_id,
            Name=name,
            Permissions=[
                {
                    'Principal': principal,
                    'Actions': [
                        'quicksight:RestoreAnalysis',
                        'quicksight:UpdateAnalysisPermissions',
                        'quicksight:DeleteAnalysis',
                        'quicksight:QueryAnalysis',
                        'quicksight:DescribeAnalysisPermissions',
                        'quicksight:DescribeAnalysis',
                        'quicksight:UpdateAnalysis'

                    ]
                }
            ],
            SourceEntity=SourceEntity,
            ThemeArn=ThemeArn
        )
    else:
        response = qs.create_analysis(
            AwsAccountId=account_id,
            AnalysisId=analysis_id,
            Name=name,
            Permissions=[
                {
                    'Principal': principal,
                    'Actions': [
                        'quicksight:RestoreAnalysis',
                        'quicksight:UpdateAnalysisPermissions',
                        'quicksight:DeleteAnalysis',
                        'quicksight:QueryAnalysis',
                        'quicksight:DescribeAnalysisPermissions',
                        'quicksight:DescribeAnalysis',
                        'quicksight:UpdateAnalysis'

                    ]
                }
            ],
            SourceEntity=SourceEntity
        )

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

#AccountId string; DataSetId string; Name string; Physical: json; Logical: json; Mode: string;
#ColumnGroups: json array; Permissions: json array; RLS: json; Tags: json array
def update_dataset (session, DataSetId, Name, Physical, Logical, Mode, ColumnGroups=None):
    qs = session.client('quicksight')
    sts_client = session.client("sts")
    AccountId = sts_client.get_caller_identity()["Account"]
    args: Dict[str, Any] = {
        "AwsAccountId": AccountId,
        "DataSetId": DataSetId,
        "Name": Name,
        "PhysicalTableMap": Physical,
        "LogicalTableMap": Logical,
        "ImportMode": Mode,
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

    response = qs.update_dashboard(
        AwsAccountId=account_id,
        DashboardId=dashboard,
        Name=name,
        SourceEntity=SourceEntity,
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
        })

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


def update_analysis(session, id, name, source, component_type, component_body):
    qs = session.client('quicksight')
    sts_client = session.client("sts")
    account_id = sts_client.get_caller_identity()["Account"]
    args: Dict[str, Any] = {
        "AwsAccountId":  account_id,
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
    #if component_type == 'Parameters':
        #args["Parameters"] = component_body
    if component_type == '':
        response = qs.update_analysis(**args)
    elif component_type == 'theme':
        args["ThemeArn"] = component_body
        response = qs.update_analysis(**args)
    else:
        args["SourceEntity"]["Definition"][component_type].append(component_body)
        response = qs.update_analysis(**args)
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
        return ('Faild to describe analysis: ' + str(e))
    else:
        return response


def update_theme(session, THEMEID, name, BaseThemeId):
    qs = session.client('quicksight')
    sts_client = session.client("sts")
    account_id = sts_client.get_caller_identity()["Account"]

    response = qs.update_theme(
        AwsAccountId=account_id,
        ThemeId=THEMEID,
        Name=name,
        BaseThemeId=BaseThemeId
    )
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


def update_theme_permissions(session, THEMEID, Principal):
    qs = session.client('quicksight')
    sts_client = session.client("sts")
    account_id = sts_client.get_caller_identity()["Account"]
    response = qs.update_theme_permissions(
        AwsAccountId=account_id,
        ThemeId=THEMEID,
        GrantPermissions=[
            {
                'Principal': Principal,
                'Actions': ['quicksight:ListThemeVersions',
                            'quicksight:UpdateThemeAlias',
                            'quicksight:UpdateThemePermissions',
                            'quicksight:DescribeThemeAlias',
                            'quicksight:DeleteThemeAlias',
                            'quicksight:DeleteTheme',
                            'quicksight:ListThemeAliases',
                            'quicksight:DescribeTheme',
                            'quicksight:CreateThemeAlias',
                            'quicksight:UpdateTheme',
                            'quicksight:DescribeThemePermissions']
            }
        ]
    )
    return response

# get 2nd_class objects
def get_sheets(session, analysisid, page=0):
    analysis_contents = describe_analysis_contents(session, analysisid)
    if page != 0:
        return analysis_contents['Sheets'][page]
    else: return analysis_contents['Sheets']

def get_cfs(session, id, cfname='none'):
    contents = describe_analysis_contents(session, id)
    if cfname != 'none':
        for cf in contents['CalculatedFields']:
            if cf['Name'] == cfname:
                return cf['Expression']
            else: return cfname + ' is not exisitng! Please check the dataset definition again.'
    else: return contents['CalculatedFields']

def get_parameter(session, id, type, pname='none'):
    if type == 'analysis':
        contents = describe_analysis_contents(session, id)
    elif type == 'dashboard':
        contents = describe_dashboard_contents(session, id)
    if pname != 'none':
        for p in contents['ParameterDeclarations']:
            for key in p:
                if p[key]['Name'] == pname:
                    return p
                else: return pname + ' is not exisitng! Please check the dataset definition again.'
    else: return contents['ParameterDeclarations']

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
        #print(new)
        file = open(lib_def, 'w')
        file.write(str(new['Definition']))
        file.close()
        file = open(lib, 'w')
        file.write(str(new['Analysis']))
        file.close()

def write_lib(out_put_name, new, library):
    with open(library, "r+") as lib:
        data = json.load(lib)
        new_data = {out_put_name: new}
        data.update(new_data)
        lib.seek(0)
        json.dump(data, lib, indent=1)

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

#get data sources of dashboards in migration list
def data_sources_ls_of_dashboard(dashboard, sourcesession):
    datasets=data_sets_ls_of_dashboard(dashboard, sourcesession)
    sourcedsref = []
    for dataset in datasets:
        ids = get_dataset_ids(dataset, sourcesession)
        res=describe_data_set(sourcesession, ids[0])

        PT=res['DataSet']['PhysicalTableMap']
        for key, value in PT.items():
            for i,j in value.items():
                dsid = j['DataSourceArn'].split("/")[1]
                dsname=get_datasource_name(dsid, sourcesession)
                if dsname not in sourcedsref:
                    sourcedsref.append(dsname)
    return sourcedsref

#get data sources of analysis in migration list
def data_sources_ls_of_analysis(analysis, sourcesession):
    datasets=data_sets_ls_of_analysis(analysis, sourcesession)
    sourcedsref = []
    for dataset in datasets:
        ids = get_dataset_ids(dataset, sourcesession)
        res=describe_data_set(sourcesession, ids[0])

        PT=res['DataSet']['PhysicalTableMap']
        for key, value in PT.items():
            for i,j in value.items():
                dsid = j['DataSourceArn'].split("/")[1]
                dsname=get_datasource_name(dsid, sourcesession)
                if dsname not in sourcedsref:
                    sourcedsref.append(dsname)
    return sourcedsref


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


#get object ids from name, or get object name from id
def get_dashboard_ids(name: str, session) -> List[str]:
    qs = session.client('quicksight')
    sts_client = session.client("sts")
    AccountId = sts_client.get_caller_identity()["Account"]

    ids: List[str] = []
    for dashboard in dashboards(session):
        if dashboard["Name"] == name:
            ids.append(dashboard["DashboardId"])
    return ids


def get_analysis_ids(name: str, session) -> List[str]:
    qs = session.client('quicksight')
    sts_client = session.client("sts")
    AccountId = sts_client.get_caller_identity()["Account"]

    ids: List[str] = []
    for analysis_list in analysis(session):
        if analysis_list["Name"] == name:
            ids.append(analysis_list["AnalysisId"])
    return ids


def get_dashboard_name(did: str, session) -> List[str]:
    qs = session.client('quicksight')
    sts_client = session.client("sts")
    AccountId = sts_client.get_caller_identity()["Account"]

    name: str
    for dashboard in dashboards(session):
        if dashboard["DashboardId"] == did:
            name = dashboard["Name"]
    return name


def get_dataset_name(did: str, session) -> List[str]:
    qs = session.client('quicksight')
    sts_client = session.client("sts")
    AccountId = sts_client.get_caller_identity()["Account"]

    name: str
    for dataset in data_sets(session):
        if dataset["DataSetId"] == did:
            name = dataset["Name"]
    return name


def get_dataset_ids(name: str, session) -> List[str]:
    qs = session.client('quicksight')
    sts_client = session.client("sts")
    AccountId = sts_client.get_caller_identity()["Account"]

    ids: List[str] = []
    for dataset in data_sets(session):
        if dataset["Name"] == name:
            ids.append(dataset["DataSetId"])
    return ids


def get_datasource_name(did: str, session) -> List[str]:
    qs = session.client('quicksight')
    sts_client = session.client("sts")
    AccountId = sts_client.get_caller_identity()["Account"]

    name: str
    for datasource in data_sources(session):
        if datasource["DataSourceId"] == did:
            name = datasource["Name"]
    return name


def get_datasource_ids(name: str, session) -> List[str]:
    qs = session.client('quicksight')
    sts_client = session.client("sts")
    AccountId = sts_client.get_caller_identity()["Account"]

    ids: List[str] = []
    for datasource in data_sources(session):
        if datasource["Name"] == name:
            ids.append(datasource["DataSourceId"])
    return ids

#delete objects
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

# load data set input pieces
def loaddsinput(file, part):
    import json
    with open(file) as f:
        data = json.load(f)
    res = data['DataSet'][part]
    return res

def check_object_status(type, id, session):
    if type == 'analysis':
        res = describe_analysis(session,id)
        if res['Status']==200:
            status=res['Analysis']['Status']
            return status
        else: raise ValueError("describe analysis status failed")

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

#update target dataset with folders
def update_dataset_folders (session, DSID, Folders):
    qs = session.client('quicksight')
    sts_client = session.client("sts")
    AccountId = sts_client.get_caller_identity()["Account"]
    response = describe_data_set (session, DSID)
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

#full or partial folder creation from source dataset, 
#folder_list can either be [] for all folders or be a list of desired folders
def folder_creation_source_dataset (session, source_dataset_id, target_dataset_id, folder_list):
    target_columns = describe_data_set (session, target_dataset_id)['DataSet']['OutputColumns']
    source_dictionary = describe_data_set (session, source_dataset_id)['DataSet']['FieldFolders']
    dictionary = {}
    #check for (folder, column) pair in dictionary
    for column in target_columns:
        keys = [k for k, v in source_dictionary.items() if column['Name'] in v['columns']]
        if keys != []:
            key = keys[0]
            if folder_list == [] or key in folder_list:
                #add keys to new folder dictionary if it doesn't already exist
                if key not in dictionary:
                    dictionary[key] = {}
                    if 'description' in source_dictionary[key]:
                        dictionary[key]['description'] = source_dictionary[key]['description']
                    dictionary[key]['columns'] = list()
                dictionary[key]['columns'].append(column['Name'])           
    update_dataset_folders (session, target_dataset_id, dictionary)
    return

#folder creation with dictionary of folders as input             
def folder_creation_dictionary (session, target_dataset_id, folder_dict):
    target_columns = describe_data_set (session, target_dataset_id)['DataSet']['OutputColumns']
    dictionary = {}
    #check for (folder, column) pair in dictionary
    for column in target_columns:
        keys = [k for k, v in folder_dict.items() if column['Name'] in v['columns']]
        if keys != []:
            key = keys[0]
            #add keys to new folder dictionary if it doesn't already exist
            if key not in dictionary:
                dictionary[key] = {}
                if 'description' in folder_dict[key]:
                    dictionary[key]['description'] = folder_dict[key]['description']
                dictionary[key]['columns'] = list()
            dictionary[key]['columns'].append(column['Name'])
    update_dataset_folders (session, target_dataset_id, dictionary)
    return

#folder creation with csv of folders as input             
def folder_creation_csv (session, target_dataset_id, csv):
    folder_dict = dict()
    f = open(csv)
    #parse csv file
    for line in f:
        line = line.strip('\n')
        splitted = line.split(",")
        folder_dict[splitted[0]] = list()
        for word in splitted[1:]:
            folder_dict[splitted[0]].append(word.strip('"'))
    target_columns = describe_data_set (session, target_dataset_id)['DataSet']['OutputColumns']
    dictionary = {}
    #check for (folder, column) pair in dictionary
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
    update_dataset_folders (session, target_dataset_id, dictionary)
    return
