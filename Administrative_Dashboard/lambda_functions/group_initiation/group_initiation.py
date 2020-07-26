import json
import boto3
import logging
from typing import Any, Callable, Dict, List, Optional

sts_client = boto3.client("sts")
account_id = sts_client.get_caller_identity()["Account"]
qs_client = boto3.client('quicksight')


def lambda_handler(event, context):
    group = str(event['detail']['requestParameters']['groupName'])
    arn="arn:aws:quicksight:us-east-1:"+account_id+":group/default/"+group
    print("group arn is: "+arn)

    aws_region = str(event['detail']['awsRegion'])
    if "Marketing" in group:
        ids = get_dashboard_ids("Marketing Dashboard", qs_client, account_id)

        try:
            response = qs_client.update_dashboard_permissions(
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

    if "HR" in group:
        ids=get_dashboard_ids("HR Dashboard", qs_client, account_id)
    
        try:
            response = qs_client.update_dashboard_permissions(
                AwsAccountId=account_id,
                DashboardId=ids[0],
                GrantPermissions=[
                    {
                        'Principal': arn,
                        'Actions':['quicksight:DescribeDashboard',
                                    'quicksight:ListDashboardVersions',
                                    'quicksight:QueryDashboard']
                    },
                ]
            )
            
        except Exception as e:
            print (e)

    if "BI-Developer" in group or "BI-Admin" in group:
        datasets = list_datasets(account_id)
        datasources = list_data_sources(account_id)
        dashboards = list_dashboards(account_id)
    
        for datasource in datasources:
            datasourceid=datasource['DataSourceId']
            try:
                response = qs_client.update_data_source_permissions(
                    AwsAccountId=account_id,
                    DataSourceId=datasourceid,
                    GrantPermissions=[
                        {
                            'Principal': arn,
                            'Actions':["quicksight:DescribeDataSource",
                            "quicksight:DescribeDataSourcePermissions",
                            "quicksight:PassDataSource",
                            "quicksight:UpdateDataSource",
                            "quicksight:DeleteDataSource",
                            "quicksight:UpdateDataSourcePermissions"]
                        },
                    ]
                )
            
            except Exception as e:
                print (e)
            
        for dataset in datasets:
            datasetid=dataset['DataSetId']
            try:
                response = qs_client.update_data_set_permissions(
                    AwsAccountId=account_id,
                    DataSetId=datasetid,
                    GrantPermissions=[
                        {
                            'Principal': arn,
                            'Actions':['quicksight:UpdateDataSetPermissions',
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
                print (e)
                
        for dashboard in dashboards:
            dashboardid=dashboard['DashboardId']
            try:
                response = qs_client.update_dashboard_permissions(
                    AwsAccountId=account_id,
                    DashboardId=dashboardid,
                    GrantPermissions=[
                        {
                            'Principal': arn,
                            'Actions':['quicksight:DescribeDashboard',
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
                print (e)

def get_dataset_ids(name: str, qs, account_id) -> List[str]:
    ids: List[str] = []
    for dataset in list_datasets(account_id):
        if dataset["Name"] == name:
            ids.append(dataset["DataSetId"])
    return ids

def get_dashboard_ids(name: str, qs, account_id) -> List[str]:
    ids: List[str] = []
    for dashboard in list_dashboards(account_id):
        if dashboard["Name"] == name:
            ids.append(dashboard["DashboardId"])
    return ids

def list_dashboards(
    account_id: Optional[str] = None
) -> List[Dict[str, Any]]:
    
    return _list(
        func_name="list_dashboards",
        attr_name="DashboardSummaryList",
        account_id=account_id,
        aws_region='us-east-1'
    )

def list_datasets(
    account_id,
    aws_region='us-east-1'
) -> List[Dict[str, Any]]:
    
    return _list(
        func_name="list_data_sets",
        attr_name="DataSetSummaries",
        account_id=account_id,
        aws_region=aws_region
    )

def list_data_sources(
    account_id: Optional[str] = None
) -> List[Dict[str, Any]]:
    return _list(
        func_name="list_data_sources", 
        attr_name="DataSources", 
        account_id=account_id,
        aws_region='us-east-1'
    )

def _list(
    func_name: str,
    attr_name: str,
    account_id: str,
    aws_region: str,
    **kwargs,) -> List[Dict[str, Any]]:
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