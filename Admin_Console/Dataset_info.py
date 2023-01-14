import json
import boto3
import logging
import csv
import io
import os
import tempfile
from typing import Any, Callable, Dict, List, Optional, Union
import time

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
    now = int(time.time())
    key = 'monitoring/quicksight/datasets_info/dataset_info.csv'
    key2 = 'monitoring/quicksight/dataset_attributes/dataset_attributes_' + str(now) + '.csv'
    key3 = 'monitoring/quicksight/data_dictionary/data_dictionary.csv'
    key4 = 'monitoring/quicksight/datasets_dashboard_visual/datasets_dashboard_visual.csv'
    key5 = 'monitoring/quicksight/datasets_analysis_visual/datasets_analysis_visual.csv'
    tmpdir = tempfile.mkdtemp()
    local_file_name = 'datsets_info.csv'
    local_file_name2 = 'dataset_attributes_' + str(now) + '.csv'
    local_file_name3 = 'data_dictionary.csv'
    local_file_name4 = 'datasets_dashboard_visual.csv'
    local_file_name5 = 'datasets_analysis_visual.csv'
    path = os.path.join(tmpdir, local_file_name)
    # print(path)

    path2 = os.path.join(tmpdir, local_file_name2)
    # print(path2)

    path3 = os.path.join(tmpdir, local_file_name3)
    # print(path3)

    path4 = os.path.join(tmpdir, local_file_name4)
    # print(path4)

    path5 = os.path.join(tmpdir, local_file_name5)
    # print(path5)

    dataset_info = []  # dataset - dashboard level for datasets that are used in dashboards only
    dataset_attributes = []  # dataset level for all datasets - timestamp - level: datasetname, dsid, SpiceSize, ImportMode, LastUpdatedTime, now
    data_dictionary = []  # dataset - column level for all datasets
    datasets_dashboard_visual = []  # dashboardid, sheet_id, visual_id, visual_type, datasetId
    datasets_analysis_visual = []  # analysisid, sheet_id, visual_id, visual_type, datasetId



    dashboards = list_dashboards(account_id, lambda_aws_region)
    analyses = list_analyses(account_id, lambda_aws_region)


    for dashboard in dashboards:
        dashboardid = dashboard['DashboardId']
        response = describe_dashboard(account_id, dashboardid, lambda_aws_region)
        Dashboard = response['Dashboard']
        Name = Dashboard['Name']
        # print(Name)
        Sourceid = Dashboard['Version']['SourceEntityArn'].split("/")
        # print(Sourceid)
        Sourceid = Sourceid[-1]
        # print(Sourceid)
        try:
            Source = describe_analysis(account_id, Sourceid, lambda_aws_region)
            SourceName = Source['Analysis']['Name']
            # print(SourceName)
        except Exception as e:
            if str(e).find('is not found'):
                pass
            else:
                raise e

        DataSetArns = Dashboard['Version']['DataSetArns']
        # print(DataSetArns)
        for ds in DataSetArns:
            dsid = ds.split("/")
            dsid = dsid[-1]
            # print(dsid)
            try:
                dataset = describe_data_set(account_id, dsid, lambda_aws_region)
                dsname = dataset['DataSet']['Name']
                # print(dsname)
                LastUpdatedTime = dataset['DataSet']['LastUpdatedTime']
                # print(LastUpdatedTime)
                PhysicalTableMap = dataset['DataSet']['PhysicalTableMap']
                # print(PhysicalTableMap)
                SpiceSize = dataset['DataSet']['ConsumedSpiceCapacityInBytes']
                # print(SpiceSize)
                ImportMode = dataset['DataSet']['ImportMode']
                for sql in PhysicalTableMap:
                    # print(sql)
                    sql = PhysicalTableMap[sql]
                    # print(sql)
                    if 'RelationalTable' in sql:
                        DataSourceArn = sql['RelationalTable']['DataSourceArn']
                        DataSourceid = DataSourceArn.split("/")
                        DataSourceid = DataSourceid[-1]
                        datasource = describe_data_source(account_id, DataSourceid, lambda_aws_region)
                        datasourcename = datasource['DataSource']['Name']
                        Catalog = sql['RelationalTable']['Catalog']
                        Schema = sql['RelationalTable']['Schema']
                        sqlName = sql['RelationalTable']['Name']

                        dataset_info.append(
                            [lambda_aws_region, Name, dashboardid, SourceName, Sourceid, dsname, dsid, LastUpdatedTime, SpiceSize, ImportMode,
                             datasourcename, DataSourceid, Catalog, Schema, sqlName])

                    if 'CustomSql' in sql:
                        DataSourceArn = sql['CustomSql']['DataSourceArn']
                        DataSourceid = DataSourceArn.split("/")
                        DataSourceid = DataSourceid[-1]
                        datasource = describe_data_source(account_id, DataSourceid, lambda_aws_region)
                        datasourcename = datasource['DataSource']['Name']
                        SqlQuery = sql['CustomSql']['SqlQuery'].replace("\n", " ")
                        sqlName = sql['CustomSql']['Name']

                        dataset_info.append(
                            [lambda_aws_region, Name, dashboardid, SourceName, Sourceid, dsname, dsid, LastUpdatedTime, SpiceSize, ImportMode,
                             datasourcename, DataSourceid, 'N/A', sqlName, SqlQuery])

            except Exception as e:
                if str(e).find('flat file'):
                    pass
                else:
                    raise e


    with open(path, 'w', newline='') as outfile:
        writer = csv.writer(outfile, delimiter='|')
        for line in dataset_info:
            writer.writerow(line)
    outfile.close()
    # upload file from tmp to s3 key

    bucket.upload_file(path, key)

    datasets = list_datasets(account_id, lambda_aws_region)
    for item in datasets:
        try:
            dsid = item['DataSetId']
            datasetname = item['Name']
            dataset_details = describe_data_set(account_id, dsid, lambda_aws_region)
            OutputColumns = dataset_details['DataSet']['OutputColumns']
            LastUpdatedTime = dataset_details['DataSet']['LastUpdatedTime']
            SpiceSize = dataset_details['DataSet']['ConsumedSpiceCapacityInBytes']
            ImportMode = dataset_details['DataSet']['ImportMode']
            for column in OutputColumns:
                columnname = column['Name']
                columntype = column['Type']
                if 'Description' in column.keys():
                    columndesc = column['Description']
                else:
                    columndesc = None
                data_dictionary.append(
                    [datasetname, dsid, columnname, columntype, columndesc]
                )
            dataset_attributes.append(
                [datasetname, dsid, SpiceSize, ImportMode, LastUpdatedTime, now]
            )
        except Exception as e:
            if str(e).find('data set type is not supported'):
                pass
            else:
                raise e

    # print(data_dictionary)
    with open(path2, 'w', newline='') as outfile:
        writer = csv.writer(outfile, delimiter=',')
        for line in dataset_attributes:
            writer.writerow(line)
    outfile.close()
    # upload file from tmp to s3 key
    bucket.upload_file(path2, key2)

    # print(data_dictionary)
    with open(path3, 'w', newline='') as outfile:
        writer = csv.writer(outfile, delimiter=',')
        for line in data_dictionary:
            writer.writerow(line)
    outfile.close()
    # upload file from tmp to s3 key
    bucket.upload_file(path3, key3)

    for dashboard in dashboards:
        dashboardid = dashboard['DashboardId']
        try:
            dashboard_def = describe_dashboard_definition(account_id, dashboardid, lambda_aws_region)
            dashboard_name = dashboard_def['Name']
            # print(dashboard_def)
            for sheet in dashboard_def['Definition']['Sheets']:
                sheet_id = sheet['SheetId']
                sheet_name = sheet['Name']
                for visual in sheet['Visuals']:
                    visual_type = list(visual.keys())[0]
                    visual_def = visual[visual_type]
                    visual_id = visual_def['VisualId']
                    dataset_identifier = search_key(visual_def, 'DataSetIdentifier')
                    for DataSet in dashboard_def['Definition']['DataSetIdentifierDeclarations']:
                        if dataset_identifier is not None and DataSet['Identifier'] == dataset_identifier:
                            datasetId = DataSet['DataSetArn'].split('/')[-1]
                            datasets_dashboard_visual.append([dashboardid, dashboard_name, sheet_id, sheet_name, visual_id, visual_type, datasetId])
        except Exception as e:
            print(e)
            pass

    with open(path4, 'w', newline='') as outfile:
        writer = csv.writer(outfile, delimiter=',')
        for line in datasets_dashboard_visual:
            writer.writerow(line)
    outfile.close()
    # upload file from tmp to s3 key
    bucket.upload_file(path4, key4)


    for analysis in analyses:
        analysisid = analysis['AnalysisId']
        try:
            analysis_def = describe_analysis_definition(account_id, analysisid, lambda_aws_region)
            analysis_name = analysis_def['Name']
            # print(analysis_def)
            for sheet in analysis_def['Definition']['Sheets']:
                sheet_id = sheet['SheetId']
                sheet_name = sheet['Name']
                for visual in sheet['Visuals']:
                    visual_type = list(visual.keys())[0]
                    visual_def = visual[visual_type]
                    visual_id = visual_def['VisualId']
                    dataset_identifier = search_key(visual_def, 'DataSetIdentifier')
                    for DataSet in analysis_def['Definition']['DataSetIdentifierDeclarations']:
                        if dataset_identifier is not None and DataSet['Identifier'] == dataset_identifier:
                            datasetId = DataSet['DataSetArn'].split('/')[-1]
                            datasets_analysis_visual.append([analysisid, analysis_name, sheet_id, sheet_name, visual_id, visual_type, datasetId])
        except Exception as e:
            print(e)
            pass

    with open(path5, 'w', newline='') as outfile:
        writer = csv.writer(outfile, delimiter=',')
        for line in datasets_analysis_visual:
            writer.writerow(line)
    outfile.close()
    # upload file from tmp to s3 key
    bucket.upload_file(path5, key5)



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

def describe_dashboard_definition(account_id, dashboardid, aws_region):
    qs_client = boto3.client('quicksight', region_name=aws_region, config=default_botocore_config())
    res = qs_client.describe_dashboard_definition(
        AwsAccountId=account_id,
        DashboardId=dashboardid
    )
    return res


def describe_analysis_definition(account_id, id, aws_region):
    qs_client = boto3.client('quicksight', region_name=aws_region, config=default_botocore_config())
    res = qs_client.describe_analysis_definition(
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


def search_key(dict_obj, key):
    if type(dict_obj) is dict:
        if key in dict_obj:
            return dict_obj[key]
        else:
            for k in dict_obj:
                res = search_key(dict_obj[k], key)
                if res is not None:
                    return res
    elif type(dict_obj) is list:
        for item in dict_obj:
            res = search_key(item, key)
            if res is not None:
                return res
    return None
