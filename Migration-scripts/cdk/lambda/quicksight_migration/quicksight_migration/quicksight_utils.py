import boto3
import json
import time
import logging
import base64
from botocore.exceptions import ClientError
from typing import Any, Dict, List, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

def assume_role(aws_account_number, role_name, aws_region):
    sts_client = boto3.client('sts')
    response = sts_client.assume_role(
        RoleArn='arn:aws:iam::' + aws_account_number + ':role/' + role_name,
        RoleSessionName='quicksight'
    )
    # Storing STS credentials
    session = boto3.Session(
        aws_access_key_id=response['Credentials']['AccessKeyId'],
        aws_secret_access_key=response['Credentials']['SecretAccessKey'],
        aws_session_token=response['Credentials']['SessionToken'],
        region_name=aws_region
    )
    return session

def get_ssm_parameters(session, ssm_string):
    ssm_client = session.client("ssm")
    config_str = ssm_client.get_parameter(
        Name=ssm_string
    )['Parameter']['Value']
    return json.loads(config_str)

def get_secret(session, secret_name):
    """Get the object from Secrets Manager"""

    # Create a Secrets Manager client
    client = session.client(
        service_name='secretsmanager'
    )

    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
    except ClientError as ex:
        if ex.response['Error']['Code'] == 'DecryptionFailureException':
            raise ex
        elif ex.response['Error']['Code'] == 'InternalServiceErrorException':
            raise ex
        elif ex.response['Error']['Code'] == 'InvalidParameterException':
            raise ex
        elif ex.response['Error']['Code'] == 'InvalidRequestException':
            raise ex
        elif ex.response['Error']['Code'] == 'ResourceNotFoundException':
            raise ex
    else:
        # Decrypts secret using the associated KMS CMK.
        # Depending on whether the secret is a string or binary,
        # one of these fields will be populated.
        if 'SecretString' in get_secret_value_response:
            secret = json.loads(get_secret_value_response['SecretString'])
            return secret['username'], secret['password']
        else:
            decoded_binary_secret = base64.b64decode(get_secret_value_response['SecretBinary'])
            return decoded_binary_secret

def get_user_arn(session, username, region='us-east-1', namespace='default'):
    sts_client = session.client("sts")
    account_id = sts_client.get_caller_identity()["Account"]
    if username == 'root':
        arn = 'arn:aws:iam::'+account_id+':'+username
    else:
        arn = "arn:aws:quicksight:"+region+":"+account_id+":user/"+namespace+"/"+username
    return arn

def get_target(
    targetsession, rds, redshift, s3Bucket, s3Key, vpc, tag, targetadmin,
     rdscredential,redshiftcredential, region='us-east-1', namespace='default',
     version='1'):
    sts_client = targetsession.client("sts")
    account_id = sts_client.get_caller_identity()["Account"]
    target: Dict[str, Any] = {
        "rds": {"rdsinstanceid": ''},
        "s3":{"manifestBucket": '',
        "manifestkey": ''},
        "vpc": '',
        "tag": '',
        "credential": {
            "rdscredential": rdscredential,
            "redshiftcredential": redshiftcredential
        },
        "datasourcepermission": [
            {
                'Principal': targetadmin,
                'Actions': [
                    "quicksight:DescribeDataSource",
                    "quicksight:DescribeDataSourcePermissions",
                    "quicksight:PassDataSource",
                    "quicksight:UpdateDataSource",
                    "quicksight:DeleteDataSource",
                    "quicksight:UpdateDataSourcePermissions"
                ]
            }
        ],
        "datasetpermission": [
            {
                'Principal': targetadmin,
                'Actions': [
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
        ],
        "version": '1'
    }

    if rds:
        target["rds"]["rdsinstanceid"] = rds
    if redshift:
        target["redshift"] = redshift
    if s3Bucket:
        target["s3"]["manifestBucket"] = s3Bucket
        target["s3"]["manifestkey"]=s3Key
    if vpc:
        target["vpc"] = "arn:aws:quicksight:"+region+":"+account_id+":vpcConnection/"+vpc
    if tag:
        target["tag"]=tag
    if rdscredential:
        target["credential"]["rdscredential"]=rdscredential
    if redshiftcredential:
        target["credential"]["redshiftcredential"]=redshiftcredential
    return target

#get datasets of dashboards in migration list
def data_sets_ls_of_dashboard(dashboard, sourcesession):
    dashboardid = get_dashboard_ids(dashboard, sourcesession)
    sourcedashboard = describe_dashboard(sourcesession, dashboardid[0])
    DataSetArns = sourcedashboard['Dashboard']['Version']['DataSetArns']
    sourcedsref = []
    for i in DataSetArns:
        did = i.split("/")[1]
        try:
            dname=get_dataset_name(did, sourcesession)
        except Exception as e:
            logger.error({
                "Error Type": "Dataset: "+did+" is missing!",
                "DashboardId": dashboardid[0],
                "Name": dashboard,
                "Error": str(e)
            })
            break
        sourcedsref.append(dname)
    return sourcedsref

#get datasets of analysis in migration list
def data_sets_ls_of_analysis(analysis, sourcesession):
    analysisid = get_analysis_ids(analysis, sourcesession)
    sourceanalysis = describe_analysis(sourcesession, analysisid[0])
    DataSetArns = sourceanalysis['Analysis']['DataSetArns']
    sourcedsref = []
    for i in DataSetArns:
        did = i.split("/")[1]
        try:
            dname = get_dataset_name(did, sourcesession)
        except Exception as e:
            logger.error({
                "Error Type": "Dataset: "+did+" is missing!",
                "AnalysisId": analysisid[0],
                "Name": analysis,
                "Error": str(e)
                }
            )
            break
        sourcedsref.append(dname)
    return sourcedsref

#get data sources of dashboards in migration list
def data_sources_ls_of_dashboard(dashboard, sourcesession):
    datasets = data_sets_ls_of_dashboard(dashboard, sourcesession)
    sourcedsref = []
    for dataset in datasets:
        ids = get_dataset_ids(dataset, sourcesession)
        res = describe_dataset(sourcesession, ids[0])

        PT = res['DataSet']['PhysicalTableMap']
        for key, value in PT.items():
            for i,j in value.items():
                dsid = j['DataSourceArn'].split("/")[1]
                dsname=get_datasource_name(dsid, sourcesession)
                if dsname not in sourcedsref:
                    sourcedsref.append(dsname)
    return sourcedsref

#get data sources of analysis in migration list
def data_sources_ls_of_analysis(analysis, sourcesession):
    datasets = data_sets_ls_of_analysis(analysis, sourcesession)
    sourcedsref = []
    for dataset in datasets:
        ids = get_dataset_ids(dataset, sourcesession)
        res = describe_dataset(sourcesession, ids[0])

        PT = res['DataSet']['PhysicalTableMap']
        for key, value in PT.items():
            for i,j in value.items():
                dsid = j['DataSourceArn'].split("/")[1]
                dsname=get_datasource_name(dsid, sourcesession)
                if dsname not in sourcedsref:
                    sourcedsref.append(dsname)
    return sourcedsref

def get_data_source_migration_list(sourcesession,source_migrate_list):
    datasources=data_sources(sourcesession)  #get data source details with listdatasource API

    migration_list=[]
    for newsource in source_migrate_list:
        ids = get_datasource_ids(newsource, sourcesession) #Get id of data sources migration list
        for datasource in datasources:
            if ids[0] == datasource["DataSourceId"]:
                #migration_list is an array containing data source connection information and etc
                migration_list.append(datasource)

    return migration_list

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
            name=dashboard["Name"]
    return name

def get_dataset_name(did: str, session) -> List[str]:
    qs = session.client('quicksight')
    sts_client = session.client("sts")
    AccountId = sts_client.get_caller_identity()["Account"]

    name: str
    for dataset in data_sets(session):
        if dataset["DataSetId"] == did:
            name=dataset["Name"]
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
            name=datasource["Name"]
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

def data_sources(session):
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

def data_sets(session):
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

def templates(session):
    qs = session.client('quicksight')
    sts_client = session.client("sts")
    account_id = sts_client.get_caller_identity()["Account"]
    token=None

    args: Dict[str, Any] = {
        "AwsAccountId": account_id,
        "MaxResults": 100,
    }

    tlist=qs.list_templates(**args)
    templates=tlist['TemplateSummaryList']

    if 'NextToken' in tlist:
        token=tlist['NextToken']
        while token is not None:
            args["NextToken"] = token
            tlist=qs.list_templates(**args)
            templates.append(tlist['TemplateSummaryList'])
            token = tlist.get("NextToken", None)
    else:
        pass
    return templates

def dashboards(session)-> List[Dict[str, Any]]:
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

def analysis (session):
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
        analysis += response["analysis"]
    return analysis

def themes (session):
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

def describe_source(session, DSID):
    qs = session.client('quicksight')
    sts_client = session.client("sts")
    AccountId = sts_client.get_caller_identity()["Account"]
    response = qs.describe_data_source(
        AwsAccountId=AccountId,
        DataSourceId=DSID
    )
    return response


#Describe a Dataset
def describe_dataset(session, DSID):
    qs = session.client('quicksight')
    sts_client = session.client("sts")
    AccountId = sts_client.get_caller_identity()["Account"]
    response = qs.describe_data_set(
        AwsAccountId=AccountId,
        DataSetId=DSID
    )
    return response

def describe_dashboard(session, dashboard):
    qs = session.client('quicksight')
    sts_client = session.client("sts")
    account_id = sts_client.get_caller_identity()["Account"]
    try:
        response = qs.describe_dashboard(
        AwsAccountId=account_id,
        DashboardId=dashboard
    )
    except Exception as e:
        return('Faild to describe dashboard: '+str(e))
    else: return response

def describe_template(session,tid):
    qs = session.client('quicksight')
    sts_client = session.client("sts")
    account_id = sts_client.get_caller_identity()["Account"]
    response = qs.describe_template(
        AwsAccountId=account_id,
        TemplateId=tid
    )
    return response

def describe_analysis(session, analysis):
    qs = session.client('quicksight')
    sts_client = session.client("sts")
    account_id = sts_client.get_caller_identity()["Account"]
    try:
        response = qs.describe_analysis(
        AwsAccountId=account_id,
        AnalysisId=analysis
    )
    except Exception as e:
        return('Faild to describe analysis: '+str(e))
    else: return response

def describe_theme(session, THEMEID):
    qs = session.client('quicksight')
    sts_client = session.client("sts")
    AccountId = sts_client.get_caller_identity()["Account"]
    response = qs.describe_theme(
        AwsAccountId=AccountId,
        ThemeId=THEMEID
    )
    return response

def delete_source(session, DataSourceId):
    qs = session.client('quicksight')
    sts_client = session.client("sts")
    AccountId = sts_client.get_caller_identity()["Account"]
    delsource = qs.delete_data_source(
        AwsAccountId=AccountId,
        DataSourceId=DataSourceId
    )
    return delsource

def delete_dataset(session, DataSetId):
    qs = session.client('quicksight')
    sts_client = session.client("sts")
    AccountId = sts_client.get_caller_identity()["Account"]
    response = qs.delete_data_set(
        AwsAccountId=AccountId,
        DataSetId=DataSetId
    )
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
        DashboardId=did
    )
    return response

def delete_analysis(session, did):
    qs = session.client('quicksight')
    sts_client = session.client("sts")
    account_id = sts_client.get_caller_identity()["Account"]
    response = qs.delete_analysis(
        AwsAccountId=account_id,
        AnalysisId=did
    )
    return response

def delete_theme(session, THEMEID):
    qs = session.client('quicksight')
    sts_client = session.client("sts")
    AccountId = sts_client.get_caller_identity()["Account"]
    response = qs.delete_theme(
        AwsAccountId=AccountId,
        ThemeId=THEMEID
    )
    return response

def create_data_source(source, session, target):
    qs = session.client('quicksight')
    sts_client = session.client("sts")
    account_id = sts_client.get_caller_identity()["Account"]
    credential=None

    #rds
    if source['Type'].lower() in [
        'aurora',
        'aurorapostgresql',
        'mariadb',
        'mysql',
        'postgresql',
        'sqlserver'] and 'RdsParameters' in source[
            'DataSourceParameters']:
        #Update data source instance name
        instance_id=source['DataSourceParameters']['RdsParameters']
        instance_id['InstanceId'] = target['rds']['rdsinstanceid']
        credential=target['credential']['rdscredential']

    #redshift
    if source['Type']=="REDSHIFT":
        #Update data source instance name
        Cluster=source['DataSourceParameters']['RedshiftParameters']
        if 'ClusterId' in Cluster:
            Cluster['ClusterId'] = target['redshift']['ClusterId']
        Cluster['Host'] = target['redshift']['Host']
        if target['redshift']['Database'] is not None and 'Database' in Cluster:
            Cluster['Database'] = target['redshift']['Database']
        credential=target['credential']['redshiftcredential']

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

def loaddsinput (file, part):
    import json
    with open(file) as f:
        data = json.load(f)
    res = data['DataSet'][part]

    return res

#AccountId string; DataSetId string; Name string; Physical: json; Logical: json; Mode: string;
#ColumnGroups: json array; Permissions: json array; RLS: json; Tags: json array
def create_dataset (session, DataSetId, Name, Physical, Logical, Mode, Permissions, ColumnGroups=None):
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

def create_dashboard(session, dashboard, name,principal, SourceEntity, version, filter='ENABLED',csv='ENABLED', sheetcontrol='EXPANDED'):
    qs = session.client('quicksight')
    sts_client = session.client("sts")
    account_id = sts_client.get_caller_identity()["Account"]
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

    return response

def create_analysis(session, analysis, name,principal, SourceEntity,ThemeArn):
    qs = session.client('quicksight')
    sts_client = session.client("sts")
    account_id = sts_client.get_caller_identity()["Account"]
    if ThemeArn:
        response = qs.create_analysis(
        AwsAccountId=account_id,
        AnalysisId=analysis,
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
        AnalysisId=analysis,
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

def create_theme(session,THEMEID, Name,BaseThemeId,Configuration):
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

def update_dashboard(session, dashboard, name, SourceEntity, version, filter='ENABLED',csv='ENABLED', sheetcontrol='EXPANDED'):
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
        }
    )

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
    return response

def update_analysis(session, analysis, name, SourceEntity):
    qs = session.client('quicksight')
    sts_client = session.client("sts")
    account_id = sts_client.get_caller_identity()["Account"]

    response = qs.update_analysis(
        AwsAccountId=account_id,
        AnalysisId=analysis,
        Name=name,
        SourceEntity=SourceEntity
    )
    return response


def describe_analysis_permissions(session, analysis):
    qs = session.client('quicksight')
    sts_client = session.client("sts")
    account_id = sts_client.get_caller_identity()["Account"]
    try:
        response = qs.describe_analysis_permissions(
            AwsAccountId=account_id,
            AnalysisId=analysis
        )
    except Exception as e:
        return('Faild to describe analysis: '+str(e))
    else:
        return response

def update_theme(session, THEMEID, name,BaseThemeId):
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
                            'Principal':Principal,
                            'Actions':[
                                'quicksight:ListThemeVersions',
                                'quicksight:UpdateThemeAlias',
                                'quicksight:UpdateThemePermissions',
                                'quicksight:DescribeThemeAlias',
                                'quicksight:DeleteThemeAlias',
                                'quicksight:DeleteTheme',
                                'quicksight:ListThemeAliases',
                                'quicksight:DescribeTheme',
                                'quicksight:CreateThemeAlias',
                                'quicksight:UpdateTheme',
                                'quicksight:DescribeThemePermissions'
                            ]
                        }
                    ]
                )
    return response
