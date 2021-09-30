import json
import boto3
import logging
import csv
import io
import os
import tempfile
from typing import Any, Callable, Dict, List, Optional

sts_client = boto3.client("sts")
account_id = sts_client.get_caller_identity()["Account"]
aws_region = 'us-east-1'
lambda_aws_region = os.environ['AWS_REGION']
qs_client = boto3.client('quicksight')
qs_local_client = boto3.client('quicksight', region_name=lambda_aws_region)


# print(lambda_aws_region)

def lambda_handler(event, context):
    sts_client = boto3.client("sts", region_name=aws_region)
    account_id = sts_client.get_caller_identity()["Account"]

    # call s3 bucket
    s3 = boto3.resource('s3')
    bucketname = 'admin-console' + account_id
    bucket = s3.Bucket(bucketname)

    key = 'monitoring/quicksight/datsets_info/datsets_info.csv'
    key2 = 'monitoring/quicksight/datsets_ingestion/datsets_ingestion.csv'
    tmpdir = tempfile.mkdtemp()
    local_file_name = 'datsets_info.csv'
    local_file_name2 = 'datsets_ingestion.csv'
    path = os.path.join(tmpdir, local_file_name)
    # print(path)

    path2 = os.path.join(tmpdir, local_file_name2)
    # print(path2)

    access = []

    dashboards = list_dashboards(account_id, lambda_aws_region)

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
                print(dsname)
                LastUpdatedTime = dataset['DataSet']['LastUpdatedTime']
                print(LastUpdatedTime)
                PhysicalTableMap = dataset['DataSet']['PhysicalTableMap']
                print(PhysicalTableMap)
                for sql in PhysicalTableMap:
                    # print(sql)
                    sql = PhysicalTableMap[sql]
                    print(sql)
                    if 'RelationalTable' in sql:
                        DataSourceArn = sql['RelationalTable']['DataSourceArn']
                        DataSourceid = DataSourceArn.split("/")
                        DataSourceid = DataSourceid[-1]
                        datasource = describe_data_source(account_id, DataSourceid, lambda_aws_region)
                        datasourcename = datasource['DataSource']['Name']
                        Catalog = sql['RelationalTable']['Catalog']
                        Schema = sql['RelationalTable']['Schema']
                        sqlName = sql['RelationalTable']['Name']

                        access.append(
                            [lambda_aws_region, Name, dashboardid, SourceName, Sourceid, dsname, dsid, LastUpdatedTime,
                             datasourcename, DataSourceid, Catalog, Schema, sqlName])
                        print(access)

                    if 'CustomSql' in sql:
                        DataSourceArn = sql['CustomSql']['DataSourceArn']
                        DataSourceid = DataSourceArn.split("/")
                        DataSourceid = DataSourceid[-1]
                        datasource = describe_data_source(account_id, DataSourceid, lambda_aws_region)
                        datasourcename = datasource['DataSource']['Name']
                        SqlQuery = sql['CustomSql']['SqlQuery'].replace("\n", " ")
                        sqlName = sql['CustomSql']['Name']

                        access.append(
                            [lambda_aws_region, Name, dashboardid, SourceName, Sourceid, dsname, dsid, LastUpdatedTime,
                             datasourcename, DataSourceid, 'N/A', sqlName, SqlQuery])
                    print(access)
            except Exception as e:
                if str(e).find('flat file'):
                    pass
                else:
                    raise e

    print(access)
    with open(path, 'w', newline='') as outfile:
        writer = csv.writer(outfile, delimiter='|')
        for line in access:
            writer.writerow(line)

    # upload file from tmp to s3 key

    bucket.upload_file(path, key)


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
    qs_client = boto3.client('quicksight', region_name=aws_region)
    res = qs_client.describe_dashboard(
        AwsAccountId=account_id,
        DashboardId=dashboardid
    )
    return res


def describe_analysis(account_id, id, aws_region):
    qs_client = boto3.client('quicksight', region_name=aws_region)
    res = qs_client.describe_analysis(
        AwsAccountId=account_id,
        AnalysisId=id
    )
    return res


def describe_data_set(account_id, id, aws_region):
    qs_client = boto3.client('quicksight', region_name=aws_region)
    res = qs_client.describe_data_set(
        AwsAccountId=account_id,
        DataSetId=id
    )
    return res


def describe_data_source(account_id, id, aws_region):
    qs_client = boto3.client('quicksight', region_name=aws_region)
    res = qs_client.describe_data_source(
        AwsAccountId=account_id,
        DataSourceId=id
    )
    return res


def describe_dashboard_permissions(account_id, dashboardid, aws_region):
    qs_client = boto3.client('quicksight', region_name=aws_region)
    res = qs_client.describe_dashboard_permissions(
        AwsAccountId=account_id,
        DashboardId=dashboardid
    )
    return res


def describe_analysis_permissions(account_id, aid, aws_region):
    qs_client = boto3.client('quicksight', region_name=aws_region)
    res = qs_client.describe_analysis_permissions(
        AwsAccountId=account_id,
        AnalysisId=aid
    )
    return res


def describe_theme_permissions(account_id, aid, aws_region):
    qs_client = boto3.client('quicksight', region_name=aws_region)
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
    qs_client = boto3.client('quicksight', region_name=aws_region)
    res = qs_client.describe_data_set_permissions(
        AwsAccountId=account_id,
        DataSetId=datasetid
    )
    return res


def describe_data_source_permissions(account_id, DataSourceId, aws_region):
    qs_client = boto3.client('quicksight', region_name=aws_region)
    res = qs_client.describe_data_source_permissions(
        AwsAccountId=account_id,
        DataSourceId=DataSourceId
    )
    return res
