"""
Folder Migration, same account, cross account, theme support etc.

Start from Guardian's code

QuickSight Folder Migration - same account migration scripts
Author: Ian Liao (Senior Data Visualization Architect in ProServe GSP) Date: Sep 13 2021
Updated: May 6 2022

QuickSight Folder can be used to build deployment environments.
User can create DEV, UAT and PROD folders, and use them as corresponding environments.
This migration script helps to dashboards with dependencies from one folder to another.
Folders must be in the same QuickSight account, cross account migration support is built in a different script.

Requirements
The Dashboard name has to be unique globally Folder name has be to unique globally.
Always use CAPITAL LETTERS ONLY NO NUMBERS NO SPECIAL CHARACTERS for folder name.
A DEV folder has to exist, and it is used as the main folder.
Migrate backwards is not recommended, start a new development folder for hot-fix if necessary.
Migrate to development folder creates an analysis instead of a dashboard DO NOT use dash in dataset name

How it works?
The script will try to find quicksight assets in the staging sub-folder within the source folder and migrate them to destination folder.
This script will not search for the asset dependencies. Developer will make sure all modified assets are added to the staging sub-folder
Object migrated to any folder other than DEV will use “its ID in DEV - folder name” as the new ID.

What objects are migrated?
In same account migration, Datasets and Dashboards are migrated;
Themes are not migrated, migrated dashboard will reuse the same theme as in source.
Data sources are not migrated.
QuickSight admin need to create the data source in target environment following the name convention before migration.
Migrated dashboard will point to the data source based on name convention.

Limitations
Dataset refresh schedule is not set in target environment when a dataset is created for the first time
Migrate from HF to UAT will create a new dashboard.
Developer needs to delete or remove the older version dashboard manually.
"""

# UAT -> PROD
# Configure the migration scripts

# dashboard migration list
# dashboard_migrate_list = ['<name of dashboards to migrate>']
# theme_migrate_list = [] # provide theme name for cross account migration

# source info
sourceaccountid = '728932513184'
# source_role_name = '<execution role for the source account>'
source_aws_region = 'us-east-1'
source_folder_name = 'UAT'
source_folder_ID = 'e3e52bbc-bffb-466f-80e2-279318e43f2f'
source_staging_folder_name = 'Staging'
source_staging_folder_ID = 'b9048803-a5ad-4cc8-a842-c1bcb47974d7'
source_is_dev = False # analysis exists in dev folder
source_is_main = False # in main environment, object IDs don't have folder name suffix
source_admin_name = 'Admin-OneClick/liaoying-Isengard'


# target info
# test case 1, across account PROD
'''targetaccountid = '624969228231'
target_role_name = 'Admin'
target_aws_region = 'us-east-1'
target_folder_name = 'PROD'
target_folder_ID = '2b32cca0-4713-4220-b274-770512b277f7'
target_is_dev = False  # set this flag to true if analysis migration is necessary (in use case like roll back); by default analysis will not be migrated.
target_is_main = False
target_admin_name = 'Admin/liaoying-Isengard'
'''

# test case 2, same account PROD folder
targetaccountid = '728932513184'
# target_role_name = 'Admin'
target_aws_region = 'us-east-1'
target_folder_name = 'PROD'
target_folder_ID = '0e647a24-09a3-4cab-848a-3a18c05e2921'
target_is_dev = False  # set this flag to true if analysis migration is necessary (in use case like roll back); by default analysis will not be migrated.
target_is_main = False
target_admin_name = 'Admin-OneClick/liaoying-Isengard'

# migration settings
same_account_migration = (True if sourceaccountid == targetaccountid else False)

# CRP specific configuration
CRP_flag = True # whether to add 'CRP-' prefix to dashboard ID
CRP_dashboard_ID_prefix = 'CRP-'

# visual embedding specific configuration
visual_embed_prefix = 'visual-embed'
contentID_bucket = 'migration-scripts-guardian'
contentID_s3_prefix = 'quicksight/output/'  # no slash at the beginning, but keep the slash at the end
contentID_local_path = '/home/ec2-user/environment/quicksight/output/'  # keep slash on the end



import boto3
import time
import json
import sys
import os
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime
import re
import quicksight_utils as qu
import csv
from botocore.exceptions import ClientError
import deployment_utils as du


logging.basicConfig(level=os.environ.get("LOGLEVEL", "INFO"))
logger = logging.getLogger('Folder-Deployment')
logger.setLevel(logging.INFO)

print('start migration')
# current date and time
now = str(datetime.now().strftime("%Y%m%d%H%M"))

# TODO: will simplify this section after we decide how to implement at Guardian
# Static Profile
# You can also configure AWS profile from terminal and call the profile in below cell

# sourceprofile=''
# targetprofile=''
sourcesession = boto3.Session(region_name=source_aws_region)
targetsession = boto3.Session(region_name=target_aws_region)

# Assume Role
# You can also assume an IAM role and create session based on the role permissions
#source account
# sourcesession = qu.assume_role(sourceaccountid, source_role_name, source_aws_region)

# target account
# targetsession = qu.assume_role(targetaccountid, target_role_name, target_aws_region)

#targetsession = boto3.Session(
#        aws_access_key_id="",
#        aws_secret_access_key="",
#        aws_session_token="",
#        region_name=aws_region
#    )


# Set root and admin users
# root user is for the template. By default, we assign full permissions of objects to admin.
sourceroot = qu.get_user_arn(sourcesession, 'root')
sourceadmin = qu.get_user_arn(sourcesession, source_admin_name)

targetroot = qu.get_user_arn(targetsession, 'root')
targetadmin = qu.get_user_arn(targetsession, target_admin_name)

# set up default permissions in target
target_permission: Dict[str, Any] = {
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
    ]
}

##############################################################################################################
# Populate migration List from the staging folder

##############################################################################################################
dataset_migrate_list = []
# analysis_migrate_list = []
dashboard_migrate_list = []
theme_migrate_list = []
default_themes = ['CLASSIC', 'MIDNIGHT', 'SEASIDE']

assets = qu.folder_members(sourcesession, source_staging_folder_ID)
for each in assets:
    logger.info('Asset found in staging: %s', json.dumps(each))
    asset_type = each['MemberArn'].rsplit(':', 1)[1].split('/', 1)[0]
    if asset_type == 'dataset':
        dataset_migrate_list.append(each['MemberId'])
    elif asset_type == 'dashboard':
        dashboard_migrate_list.append(each['MemberId'])

# populate theme migration list
if not same_account_migration:
    for dashboardID in dashboard_migrate_list:
        dashboard = qu.describe_dashboard(sourcesession, dashboardID)
        if 'ThemeArn' in dashboard['Dashboard']['Version']:
            theme_id = dashboard['Dashboard']['Version']['ThemeArn'].split("/")[1]
            if theme_id not in default_themes:
                theme_migrate_list.append(theme_id)

logger.info('datasets to migrate %s', dataset_migrate_list)
logger.info('dashboard to migrate %s', dashboard_migrate_list)


# logic to map source name and ID to target
def get_target_id(source_id):
    if same_account_migration:
        if source_is_main:
            target_id = source_id + '-' + target_folder_name
        elif target_is_main:
            target_id = source_id.replace(('-' + source_folder_name), '')
        else:
            target_id = source_id.replace(('-' + source_folder_name), '') + ('-' + target_folder_name)
    else:
        if source_folder_name != 'DEV':
            target_id = source_id.replace(('-' + source_folder_name), '')
        else:
            target_id = source_id
    return target_id


def get_target_dashboard_id(source_dashboard_id, source_dashboard_name):
    target_dashboard_id = get_target_id(source_dashboard_id)
    if CRP_flag and CRP_dashboard_ID_prefix not in target_dashboard_id:
        target_dashboard_id = CRP_dashboard_ID_prefix + target_dashboard_id
    if visual_embed_prefix in source_dashboard_name and target_folder_name == 'PROD':
        target_dashboard_id = target_dashboard_id + '-' + now
    return target_dashboard_id


def get_target_dashboard_name(source_dashboard_name):
    target_dashboard_name = get_target_id(source_dashboard_name)
    if CRP_flag:
        target_dashboard_name = target_dashboard_name
    if visual_embed_prefix in source_dashboard_name and target_folder_name == 'PROD':
        target_dashboard_name = target_dashboard_name + '-' + now
    return target_dashboard_name


def get_target_placeholder(placeholder):
    if same_account_migration:
        if target_is_main:
            target_placeholder = re.sub(r'-[A-Z]+', '', placeholder)
        else:
            target_placeholder = re.sub(r'-[A-Z]+', '', placeholder) + '-' + target_folder_name
    else:
        if source_folder_name != 'DEV':
            target_placeholder = placeholder.replace(('-' + source_folder_name), '')
        else:
            target_placeholder = placeholder
    return target_placeholder

datasources = qu.data_sources(sourcesession)


# data source naming convention: name-DEV, name-UAT, name-PROD
def get_target_data_source_id(data_source_id):
    try:
        res = qu.describe_source(sourcesession, data_source_id)
        source_name = res['DataSource']['Name']
        target_name = source_name.replace(('-' + source_folder_name), '') + ('-' + target_folder_name)
        logger.info('target data source name is: %s', target_name)
        target_datasource = qu.get_datasource_ids(target_name, targetsession)
        target_data_source_id = target_datasource[0]
        return target_data_source_id
    except ClientError as ex:
        logger.error('Client Error when trying to find the data source, %s', ex)
        raise ex
    else:
        logger.error('Unable to find matching data source')
        raise

deployment_config = {
    "get_target_id_func": get_target_id,
    "get_target_dashboard_id_func": get_target_dashboard_id,
    "get_target_dashboard_name_func": get_target_dashboard_name,
    "get_target_placeholder_func": get_target_placeholder,
    "get_target_data_source_id_func": get_target_data_source_id,
    "target_permission": target_permission,
    "source_account_id": sourceaccountid,
    "target_account_id": targetaccountid
}

##############################################################################################################
# Migrate Data Sets

##############################################################################################################
# Data Set Migration Get datasets list
datasets = qu.data_sets(sourcesession)


# Get already migrated datasets list
#get datasets which already migrated
targetds = qu.data_sets(targetsession)
#already_migrated record the datasets ids of target account
already_migrated = []
for ds in targetds:
    already_migrated.append(ds['DataSetId'])

newsetslist=[]
faillist=[]
sts_client = targetsession.client("sts")
account_id = sts_client.get_caller_identity()["Account"]

'''
# Describe a Dataset
def dd(session, dataset_id):
    qs_client = session.client('quicksight')
    sts_client = session.client("sts")
    account_id = sts_client.get_caller_identity()["Account"]
    print(account_id)
    try:
        print('start to describe dataset')
        response = qs_client.describe_data_set(
            AwsAccountId=account_id,
            DataSetId=dataset_id
        )
    except be.ClientError as exc:
        print('error out when describe')
        logger.error("Failed to describe data set %s", dataset_id)
        logger.error(exc.response['Error']['Message'])
        print(exc)
        raise exc
    except Exception as exc:
        print('error out when describe as general exception')
    return response
'''

deployment_config['already_migrated_dataset'] = already_migrated
deployment_config['dataset_fail_list'] = faillist
deployment_config['dataset_new_list'] = newsetslist


for mds in dataset_migrate_list:
    du.migrate_dataset(mds, sourcesession, targetsession, deployment_config)
    # print(newsetslist)
    # print(mds)
    if get_target_id(mds) in newsetslist:
        qu.create_folder_membership(targetsession, target_folder_ID, get_target_id(mds), 'DATASET')
        logger.info('added DATASET {} to target folder'.format(get_target_id(mds)))
        qu.delete_folder_membership(sourcesession, source_staging_folder_ID, mds, 'DATASET')
        logger.info('removed DATASET {} from staging folder'.format(mds))

logger.info('Successfully migrated datasets: %s', newsetslist)
logger.info('failed to migrate datasets: %s', faillist)


##############################################################################################################
# Migrate Themes

##############################################################################################################


if same_account_migration is False:
    #get themes which already migrated
    targetthemes=qu.themes(targetsession)
    #already_migrated record the datasets ids of target account
    already_migrated=[]
    for th in targetthemes:
        already_migrated.append(th['ThemeId'])
    #already_migrated

    newthemeslist=[]
    faillist=[]
    sts_client = targetsession.client("sts")
    account_id = sts_client.get_caller_identity()["Account"]
    for themeID in theme_migrate_list:
        try:
            res = qu.describe_theme(sourcesession, themeID)
        except Exception:
            faillist.append({"Theme": themeID, "Error": str(Exception)})
            continue
        THEMEID=res['Theme']['ThemeId']
        Name=res['Theme']['Name']
        BaseThemeId=res['Theme']['Version']['BaseThemeId']
        Configuration=res['Theme']['Version']['Configuration']
        try:
            if themeID not in already_migrated:
                newtheme = qu.create_theme(targetsession,THEMEID, Name,BaseThemeId,Configuration)
            else:
                newtheme = qu.update_theme(targetsession, THEMEID, Name, BaseThemeId, Configuration)
            newthemeslist.append(newtheme)
        except Exception as e:
            #print('failed: '+str(e))
            faillist.append({"ThemeID": THEMEID, "Name": Name, "Error": str(e)})
            continue
        try:
            qu.update_theme_permissions(targetsession, THEMEID, targetadmin)
        except Exception as e:
            #print('failed: '+str(e))
            faillist.append({"ThemeID": THEMEID, "Name": Name, "Error": str(e)})
            continue

    logger.info('Successfully migrated themes: %s', newthemeslist)
    logger.info('failed to migrate themes: %s', faillist)


##############################################################################################################
# Migrate Dashboards

##############################################################################################################
success = []
faillist = []
for each_id in dashboard_migrate_list:
    sourcedashboard = qu.describe_dashboard(sourcesession, each_id)
    SourceEntityArn = sourcedashboard['Dashboard']['Version']['SourceEntityArn']
    # print(SourceEntityArn)
    if SourceEntityArn.split("/")[0].split(":")[-1] == "analysis" or SourceEntityArn.split("/")[0].split(":")[
        -1] == 'template':
        sourceanalysis = sourcedashboard['Dashboard']['Version']['SourceEntityArn']
    else:
        faillist.append({"Error Type": "Source Analysis is missing!", "DashboardId": each_id, "Name": sourcetname,
                         "Error": "Source Analysis is missing!"})
        continue

    sourceversion = sourcedashboard['Dashboard']['Version']['VersionNumber']
    sourcedid = sourcedashboard['Dashboard']['DashboardId']
    sourcedname = sourcedashboard['Dashboard']['Name']
    sourcetid = sourcedid
    sourcetname = sourcedname
    targetdid = get_target_dashboard_id(sourcedid, sourcedname)
    targetdname = get_target_dashboard_name(sourcedname)
    # print('1')

    DataSetArns = sourcedashboard['Dashboard']['Version']['DataSetArns']
    TargetThemeArn = ''
    if 'ThemeArn' in sourcedashboard['Dashboard']['Version'].keys():
        SourceThemearn = sourcedashboard['Dashboard']['Version']['ThemeArn']
        theme_id = SourceThemearn.split("/")[1]
        if theme_id in default_themes:
            TargetThemeArn = 'arn:aws:quicksight::aws:theme/' + theme_id
        else:
            TargetThemeArn = 'arn:aws:quicksight:' + target_aws_region + ':' + account_id + ':theme/' + SourceThemearn.split("/")[1]
    sourcedsref = []
    # print('2')
    for i in DataSetArns:
        missing = False
        did = i.split("/")[1]
        try:
            dname = qu.get_dataset_name(did, sourcesession)
        except Exception as e:
            faillist.append(
                {"Error Type": "Dataset: " + did + " is missing!", "DashboardId": sourcetid, "Name": sourcetname,
                 "Error": str(e)})
            missing = True
            break

        sourcedsref.append({'DataSetPlaceholder': dname,
                            'DataSetArn': i})
    if missing:
        continue

    if SourceEntityArn.split("/")[0].split(":")[-1] == "analysis" and same_account_migration == True:

        try:
            sourcetemplate = qu.create_template(sourcesession, sourcetid, sourcetname, sourcedsref, sourceanalysis, '1')
            # print('template created')
        except Exception as e:
            faillist.append(
                {"Error Type": "Create Source Template Error", "DashboardId": sourcetid, "Name": sourcetname,
                 "Error": str(e)})
            continue
        # print('3')
        time.sleep(10)
        sourcetemplate = qu.describe_template(sourcesession, sourcetid)
        while sourcetemplate['Template']['Version']['Status'] == "CREATION_IN_PROGRESS":
            time.sleep(5)
            sourcetemplate = qu.describe_template(sourcesession, sourcetid)
            # print(sourcetemplate)

        # print('4')
        sourcetemplate = qu.describe_template(sourcesession, sourcetid)
        targettemplate = qu.describe_template(targetsession,
                                           sourcetid)  # there is no need to copy template within the same account

        while targettemplate['Template']['Version']['Status'] == "CREATION_IN_PROGRESS":
            time.sleep(5)
            targettemplate = qu.describe_template(targetsession, sourcetid)
            if targettemplate['Template']['Version']['Status'] == "CREATION_SUCCESSFUL":
                break
        else:
            if targettemplate['Template']['Version']['Status'] == "CREATION_SUCCESSFUL":
                logger.info("Template is successful created!")
            else:
                qu.delete_template(targetsession, sourcetid)
                faillist.append({"Error Type": "Copy Template Error",
                                 "DashboardId": sourcetid,
                                 "Name": sourcetname,
                                 "Error": str(e)})
                continue

    elif SourceEntityArn.split("/")[0].split(":")[-1] == "template" and same_account_migration == True:
        sourcetid = SourceEntityArn.split("/")[1]
        sourcetemplate = qu.describe_template(sourcesession, sourcetid)
        targettemplate = qu.describe_template(targetsession, sourcetid)

    elif SourceEntityArn.split("/")[0].split(":")[-1] == "analysis" and same_account_migration == False:
        # Need to first create the template and then copy over
        try:
            sourcetemplate = qu.create_template(sourcesession, sourcetid, sourcetname, sourcedsref, sourceanalysis, '1')
        except Exception as e:
            faillist.append(
                {"Error Type": "Create Source Template Error", "DashboardId": sourcetid, "Name": sourcetname,
                 "Error": str(e)})
            continue
        # print('3')
        time.sleep(10)
        sourcetemplate = qu.describe_template(sourcesession, sourcetid)
        while sourcetemplate['Template']['Version']['Status'] == "CREATION_IN_PROGRESS":
            time.sleep(5)
            sourcetemplate = qu.describe_template(sourcesession, sourcetid)
            # print(sourcetemplate)

        if sourcetemplate['Template']['Version']['Status'] == "CREATION_SUCCESSFUL":
            logger.info("Source Template is successful created!")
        else:
            faillist.append(
                {"Error Type": "Create Source Template Error", "DashboardId": sourcetid, "Name": sourcetname,
                 "Error": sourcetemplate['Template']['Version']['Status']})
            continue
        # print('4')
        # there is need to copy template across account
        sourcetemplate = qu.describe_template(sourcesession, sourcetid)
        updateres = qu.update_template_permission(
            sourcesession, sourcetid, targetadmin)
        if updateres['Status'] == 200:
            try:
                targettemplate = qu.copy_template(
                    targetsession, sourcetid, sourcetname, updateres['TemplateArn'])
            except Exception as ex:
                faillist.append({"Error Type": "Copy Template Error",
                                 "DashboardId": sourcetid,
                                 "Name": sourcetname,
                                 "Error": str(e)})
                continue
        else:
            faillist.append({"Error Type": "Update Template Permission Error",
                             "DashboardId": sourcetid,
                             "Name": sourcetname,
                             "Error": "Template Update Failed"})
            continue
        targettemplate = qu.describe_template(targetsession,
                                           sourcetid)

        while targettemplate['Template']['Version']['Status'] == "CREATION_IN_PROGRESS":
            time.sleep(5)
            targettemplate = qu.describe_template(targetsession, sourcetid)
            if targettemplate['Template']['Version']['Status'] == "CREATION_SUCCESSFUL":
                break
        else:
            if targettemplate['Template']['Version']['Status'] == "CREATION_SUCCESSFUL":
                logger.info("Template is successful copied!")
            else:
                qu.delete_template(targetsession, sourcetid)
                faillist.append({"Error Type": "Create Template Error",
                                 "DashboardId": sourcetid,
                                 "Name": sourcetname,
                                 "Error": "Template Creation Failed"})
                continue

    elif SourceEntityArn.split("/")[0].split(":")[-1] == "template" and same_account_migration == False:
        sourcetid = SourceEntityArn.split("/")[1]
        sourcetemplate = qu.describe_template(sourcesession, sourcetid)
        updateres = qu.update_template_permission(
            sourcesession, sourcetid, targetadmin)
        if updateres['Status'] == 200:
            try:
                targettemplate = qu.copy_template(
                    targetsession, sourcetid, sourcetname, updateres['TemplateArn'])
            except Exception as ex:
                faillist.append({"Error Type": "Copy Template Error",
                                 "DashboardId": sourcetid,
                                 "Name": sourcetname,
                                 "Error": str(e)})
                continue
        else:
            faillist.append({"Error Type": "Update Template Permission Error",
                             "DashboardId": sourcetid,
                             "Name": sourcetname,
                             "Error": "Update Template Failed"})
            continue
        targettemplate = qu.describe_template(targetsession, sourcetid)

        while targettemplate['Template']['Version']['Status'] == "CREATION_IN_PROGRESS":
            time.sleep(5)
            targettemplate = qu.describe_template(targetsession, sourcetid)
            if targettemplate['Template']['Version']['Status'] == "CREATION_SUCCESSFUL":
                break
        else:
            if targettemplate['Template']['Version']['Status'] == "CREATION_SUCCESSFUL":
                logger.info("Template is successful copied!")
            else:
                qu.delete_template(targetsession, sourcetid)
                faillist.append({"Error Type": "Copy Template Error",
                                 "DashboardId": sourcetid,
                                 "Name": sourcetname,
                                 "Error": "Template Copy Failed"})
                continue

    logger.info('Setting up dataset placeholders')

    # ds=data_sets (targetsession)
    ds = qu.folder_members(targetsession, target_folder_ID)
    Template = targettemplate['Template']
    dsref = []
    # print(Template['Version']['DataSetConfigurations'])
    missing = False
    # print(Template['Version']['DataSetConfigurations'])
    for i in Template['Version']['DataSetConfigurations']:
        # print("i is "+str(i))
        n = Template['Version']['DataSetConfigurations'].index(i)
        # print("n is "+str(n))
        for j in ds:
            member_type = j['MemberArn'].split('/')[0].split(':')[-1]
            if member_type != 'dataset':
                continue
            j['Arn'] = j['MemberArn']
            ds_des = qu.describe_dataset(targetsession, j['MemberId'])
            j['Name'] = ds_des['DataSet']['Name']
            # print(i['Placeholder'])
            # print(get_target_id(i['Placeholder']))
            # print(j['Name'])
            # print(j['Arn'])
            if get_target_id(i['Placeholder']) == j['Name']:
                dsref.append({
                    'DataSetPlaceholder': i['Placeholder'],
                    'DataSetArn': j['Arn']
                })
                break
                # print("len of dsref is " + str(len(dsref)))
                # print(dsref)
        if (n + 1) > len(dsref):
            e = "Dataset " + i['Placeholder'] + " is missing!"
            faillist.append({"Error Type": "Datasets in target env are missing for this dashboard",
                             "DashboardId": sourcetid,
                             "Name": sourcetname,
                             "Error": str(e)})
            missing = True
            break
        if missing:
            break
    if missing:
        continue
    # print("len of dsref is "+str(len(dsref)))
    # print(dsref)
    logger.info('Found all required datasets!')

    if target_is_dev == True:  # create an analysis for dev purposes first
        # print('create an analysis for dev purposes first')
        SourceEntity = {
            'SourceTemplate': {
                'DataSetReferences': dsref,
                'Arn': Template['Arn']
            }
        }
        newanalysis = qu.create_analysis(targetsession, targetdid, targetdname, targetadmin, SourceEntity, TargetThemeArn)
        # print(newanalysis)
        time.sleep(30)
        qu.create_folder_membership(targetsession, target_folder_ID, targetdid, 'ANALYSIS')
        continue

    else:
        SourceEntity = {
            'SourceTemplate': {
                'DataSetReferences': dsref,
                'Arn': Template['Arn']
            }
        }
    # print(SourceEntity)
    dashboard = qu.describe_dashboard(targetsession, targetdid)

    if 'Faild to describe dashboard:' in dashboard:
        if 'dashboard/' + targetdid + ' is not found' in dashboard:
            logger.info("Create new dashboard now:")
            try:
                newdashboard = qu.create_dashboard(targetsession, targetdid, targetdname, targetadmin, SourceEntity, '1',
                                                TargetThemeArn, filter='DISABLED', csv='ENABLED',
                                                sheetcontrol='COLLAPSED')
            except Exception as e:
                qu.delete_template(targetsession, targetdid)
                faillist.append({"Error Type": "Create New Dashboard Error",
                                 "DashboardId": targetdid,
                                 "Name": targetdname,
                                 "Error": str(e)})
                continue
        else:
            faillist.append({"Error Type": "Describe Target Dashboard Error",
                             "DashboardId": targetdid,
                             "Name": targetdname,
                             "Error": str(dashboard)})
            continue
    elif dashboard['Dashboard']['Version']['Status'] == "CREATION_FAILED":
        res = qu.delete_dashboard(targetsession, targetdid)
        try:
            newdashboard = qu.create_dashboard(targetsession, targetdid, targetdname, targetadmin, SourceEntity, '1',
                                            TargetThemeArn, filter='DISABLED', csv='ENABLED', sheetcontrol='COLLAPSED')
        except Exception as e:
            qu.delete_template(targetsession, targetdid)
            # print('fail to create dashboard, add to faillist')
            faillist.append({"Error Type": "Create Dashboard Error",
                             "DashboardId": targetdid,
                             "Name": targetdname,
                             "Error": str(e)})
            continue

    else:
        logger.info("dashboard is existing. update it now.")
        try:
            res = qu.delete_dashboard(targetsession, targetdid)
            newdashboard = qu.create_dashboard(targetsession, targetdid, targetdname, targetadmin, SourceEntity, '1',
                                            TargetThemeArn, filter='DISABLED', csv='ENABLED', sheetcontrol='COLLAPSED')
        except Exception as e:
            # print(newdashboard)
            qu.delete_template(targetsession, targetdid)
            # print('fail to update dashboard, add to faillist')
            faillist.append({"Error Type": "Create Dashboard Error",
                             "DashboardId": targetdid,
                             "Name": targetdname,
                             "Error": str(e)})
            continue
    while (True):
        res = qu.describe_dashboard(targetsession, newdashboard['DashboardId'])

        if res['Status'] == 200:
            status = res['Dashboard']['Version']['Status']
            if status == 'CREATION_SUCCESSFUL' or status == 'UPDATE_SUCCESSFUL':
                success.append(targetdid)
                qu.create_folder_membership(targetsession, target_folder_ID, targetdid, 'DASHBOARD')
                qu.delete_folder_membership(sourcesession, source_staging_folder_ID, each_id, 'DASHBOARD')
                logger.info('added dashboard {} to target folder'.format(targetdid))
                logger.info('Removed dashboard {} from staging folder'.format(each_id))
                break
            elif status == 'CREATION_IN_PROGRESS':
                time.sleep(10)
                continue
            else:
                faillist.append(
                    {"Error Type": "Dashboard Creation Status is not Successful", "Dashboard": res['Dashboard']})
                break
                # filename="Migration_Results/Fail/Dashboard_"+res['Dashboard']['Name']+".json"

logger.info('Successfully migrated dashboards: %s', success)
logger.info('failed to migrate dashboards: %s', faillist)


def get_sheet_id_visual_id(dashboard_id):
    sheet_id_visual_id = []
    dashboard_def = qu.describe_dashboard_definition(targetsession, dashboard_id)
    for sheet in dashboard_def['Definition']['Sheets']:
        sheet_id = sheet['SheetId']
        sheet_name = sheet['Name']
        for visual in sheet['Visuals']:
            visual_def = list(visual.values())[0]
            visual_id = visual_def['VisualId']
            if 'FormatText' in visual_def['Title'] and ('PlainText' in visual_def['Title']['FormatText'] or 'RichText' in visual_def['Title']['FormatText']):
                visual_name = visual_def['Title']['FormatText']['PlainText'] if 'PlainText' in visual_def['Title']['FormatText'] else 'PlainText' in visual_def['Title']['RichText']
                sheet_id_visual_id.append(
                    {'Timestamp': now, 'DashboardId': dashboard_id, 'SheetId': sheet_id, 'SheetName': sheet_name, 'VisualId': visual_id, 'VisualName': visual_name}
                                          )
            else:
                continue
    return sheet_id_visual_id


csv_output = []
for dashboard_id in success:
    dashboard_name = qu.get_dashboard_name(dashboard_id, targetsession)
    if visual_embed_prefix in dashboard_name:
        logger.info('Fetching sheet IDs and visual IDs in migrated dashboard %s', dashboard_id)
        output_ids = get_sheet_id_visual_id(dashboard_id)
        # logger.info(json.dumps(output_ids))
        csv_output.extend(output_ids)

field_names = ['Timestamp', 'DashboardId', 'SheetId', 'SheetName', 'VisualId', 'VisualName']
output_file_name = 'contentID-' + now + '.csv'
local_file = contentID_local_path + output_file_name
if len(csv_output) > 0:
    with open(local_file, 'w') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=field_names)
        writer.writeheader()
        writer.writerows(csv_output)
        csvfile.close()
    logger.info('Successfully created output.csv file')

    try:
        s3_client = targetsession.client('s3')
        s3_client.upload_file(local_file, contentID_bucket, contentID_s3_prefix + output_file_name)
    except ClientError as exc:
        logger.error('Failed to upload output.csv to s3 bucket: '+str(exc))
    logger.info('Successfully uploaded output.csv to s3')
else:
    logger.info('No need to generate output.csv for sheet ID and visual ID')