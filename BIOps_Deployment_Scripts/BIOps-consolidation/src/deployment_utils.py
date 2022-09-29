
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

import quicksight_utils as qu

logging.basicConfig(level=os.environ.get("LOGLEVEL", "INFO"))
logger = logging.getLogger('deployment_utils')
logger.setLevel(logging.INFO)


"""
Deployment functions
"""

default_themes = ['CLASSIC', 'MIDNIGHT', 'SEASIDE']

# TODO: Create folder if missing
def validate_folder_hierarchy(now, dic, package, namespace, folderID, region, accountid, target_session, faillist, logs,
                              log_group,
                              error_log, success_log):
    folderarn = 'arn:aws:quicksight:' + region + ':' + accountid + ':folder/'
    for folder in dic:  # CDI ... Datasets
        folderID += '-' + folder
        subfolders = dic[folder]
        try:
            qu.search_folders(target_session, folderarn + folderID)
            qu.log_events_to_cloudwatch(
                {"account_id": accountid, "package": package, "deployment_time": now, "namespace": namespace,
                 "folder_id": folderID,
                 "success": "FolderID: " + folderID + " exists"}, logs,
                log_group, success_log)
        except Exception as e:
            message = {"account_id": accountid, "package": package, "deployment_time": now, "namespace": namespace,
                       "folder_id": folderID, "error": str(e)}
            faillist.append(message)
            qu.log_events_to_cloudwatch(message, logs, log_group, error_log)
            folderID = folderID.replace('-' + folder, "")
            continue
        if isinstance(subfolders, dict):
            validate_folder_hierarchy(now, subfolders, package, namespace, folderID, region, accountid, target_session,
                                      faillist,
                                      logs, log_group, error_log, success_log)
        folderID = folderID.replace('-' + folder, "")
    return faillist

'''
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
'''


def migrate_dataset(source_dataset_ID, source_ses, target_ses, deployment_config):
    # Todo: handle parent child relationship

    logger.info('Migrating dataset: from %s to %s', source_dataset_ID, deployment_config["get_target_id_func"](source_dataset_ID))
    try:
        res = qu.describe_data_set(source_ses, source_dataset_ID)
        # res = dd(source_ses, 'Admin-Console-Object-Access')
        # print(res)
    except Exception:
        # print(Exception)
        deployment_config['dataset_fail_list'].append({"Dataset": source_dataset_ID, "Error": Exception})
        return

    if 'RowLevelPermissionDataSet' in res['DataSet']:
        rls_flag = True
        rls_arn = res['DataSet']['RowLevelPermissionDataSet']['Arn']
        # print('rls data set exists: ' + rls_arn)
        rls_id = rls_arn.split('/')[1]

        try:
            rls_res = qu.describe_data_set(source_ses, rls_id)
        except Exception:
            deployment_config['dataset_fail_list'].append({"Dataset": source_dataset_ID, "RLS": rls_id, "Error": str(Exception)})
            return

        # migrate the rls dataset to target
        migrate_dataset(rls_id, source_ses, target_ses)
        deployment_config['already_migrated_dataset'].append(deployment_config["get_target_id_func"](rls_id))

        RowLevelPermissionDataSet = res['DataSet']['RowLevelPermissionDataSet']
        RowLevelPermissionDataSet['Arn'] = deployment_config["get_target_id_func"](RowLevelPermissionDataSet['Arn']).\
            replace(deployment_config["source_account_id"], deployment_config["target_account_id"])
        RowLevelPermissionDataSet['Status'] = 'ENABLED'

    else:
        rls_flag = False
        RowLevelPermissionDataSet = None

    name = res['DataSet']['Name']

    PT = res['DataSet']['PhysicalTableMap']
    try:
        for key, value in PT.items():
            for k, v in value.items():
                data_source_id = v['DataSourceArn'].split("/")[1]
                v['DataSourceArn'] = 'arn:aws:quicksight:us-east-1:' + deployment_config["target_account_id"] + ':datasource/' + deployment_config["get_target_data_source_id_func"](data_source_id)
    except Exception as e:
        deployment_config['dataset_fail_list'].append({"DataSetId": source_dataset_ID,
                         "Name": name,
                         "Error": str(e)})
        return

    LT = res['DataSet']['LogicalTableMap']

    if 'ColumnGroups' in res['DataSet']:
        ColumnGroups = res['DataSet']['ColumnGroups']
    else:
        ColumnGroups = None


    if 'RowLevelPermissionTagConfiguration' in res['DataSet']:
        RowLevelPermissionTagConfiguration = res['DataSet']['RowLevelPermissionTagConfiguration']
    else:
        RowLevelPermissionTagConfiguration = None

    if 'FieldFolders' in res['DataSet']:
        FieldFolders = res['DataSet']['FieldFolders']
    else:
        FieldFolders = None

    if 'ColumnLevelPermissionRules' in res['DataSet']:
        ColumnLevelPermissionRules = res['DataSet']['ColumnLevelPermissionRules']
    else:
        ColumnLevelPermissionRules = None

    if 'DataSetUsageConfiguration' in res['DataSet']:
        DataSetUsageConfiguration = res['DataSet']['DataSetUsageConfiguration']
    else:
        DataSetUsageConfiguration = None

    # get datasets in target account
    targetds = qu.data_sets(target_ses)
    # already_migrated record the datasets ids of target account
    # todo: move already_migrated_ds to deployment config
    already_migrated_ds = []
    for ds in targetds:
        already_migrated_ds.append(ds['DataSetId'])
    # print(already_migrated)
    # print(get_target_id(source_dataset_ID))

    if deployment_config["get_target_id_func"](source_dataset_ID) not in already_migrated_ds:
        logger.info('creating new dataset: %s', deployment_config["get_target_id_func"](source_dataset_ID))
        try:
            newdataset = qu.create_dataset(target_ses, deployment_config["get_target_id_func"](source_dataset_ID), deployment_config["get_target_id_func"](name), PT, LT,
                                        res['DataSet']['ImportMode'], deployment_config["target_permission"]["datasetpermission"], ColumnGroups,
                                        RowLevelPermissionDataSet, RowLevelPermissionTagConfiguration,
                                           FieldFolders, ColumnLevelPermissionRules, DataSetUsageConfiguration)
            #print("new dataset: ", newdataset)

            deployment_config['dataset_new_list'].append(deployment_config["get_target_id_func"](source_dataset_ID))
        except Exception as e:
            print('failed: ' + str(e))
            deployment_config['dataset_fail_list'].append({"DataSetId": source_dataset_ID, "Name": name, "Error": str(e)})
            return

    if deployment_config["get_target_id_func"](source_dataset_ID) in already_migrated_ds:
        logger.info('updating already migrated dataset: %s', deployment_config["get_target_id_func"](source_dataset_ID))
        try:
            newdataset = qu.update_dataset(target_ses, deployment_config["get_target_id_func"](source_dataset_ID), deployment_config["get_target_id_func"](name), PT, LT,
                                        res['DataSet']['ImportMode'], ColumnGroups, RowLevelPermissionDataSet,
                                           RowLevelPermissionTagConfiguration,
                                           FieldFolders, ColumnLevelPermissionRules, DataSetUsageConfiguration)
            # print("update dataset: ", newdataset)
            deployment_config['dataset_new_list'].append(deployment_config["get_target_id_func"](source_dataset_ID))
        except Exception as e:
            # print('failed: ' + str(e))
            deployment_config['dataset_fail_list'].append({"DataSetId": source_dataset_ID, "Name": name, "Error": str(e)})
            return

def migrate_theme(source_theme_ID, source_ses, target_ses, deployment_config):
    if source_theme_ID in default_themes:
        return
    try:
        res = qu.describe_theme(source_ses, source_theme_ID)
    except Exception:
        deployment_config['theme_fail_list'].append({"Theme": source_theme_ID, "Error": str(Exception)})
        return
    THEMEID = deployment_config['get_target_theme_id_func'](res['Theme']['ThemeId'])
    Name = res['Theme']['Name']
    BaseThemeId = res['Theme']['Version']['BaseThemeId']
    Configuration = res['Theme']['Version']['Configuration']
    try:
        if source_theme_ID not in deployment_config['already_migrated_theme']:
            newtheme = qu.create_theme(target_ses, THEMEID, Name, BaseThemeId, Configuration)
        else:
            newtheme = qu.update_theme(target_ses, THEMEID, Name, BaseThemeId, Configuration)
        deployment_config['theme_new_list'].append(newtheme)
    except Exception as e:
        # print('failed: '+str(e))
        deployment_config['theme_fail_list'].append({"ThemeID": THEMEID, "Name": Name, "Error": str(e)})
        return
    try:
        qu.update_theme_permissions(target_ses, THEMEID, deployment_config['target_permission']['themepermission'][0]['Principal'])
    except Exception as e:
        # print('failed: '+str(e))
        deployment_config['theme_fail_list'].append({"ThemeID": THEMEID, "Name": Name, "Error": str(e)})

'''
def migrate_themes(now, account_id, env, package, target_session, dir, logs, log_group, error_log, success_log):
    faillist = []
    newthemeslist = []
    # Get themes which already migrated
    targetthemes = qu.list_themes(target_session)
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
            qu.log_events_to_cloudwatch(message, logs, log_group,
                                     success_log)
        except Exception:
            message = {"account_id": account_id, "package": package, "deployment_time": now, "dir_file": theme_file,
                       "error": str(Exception)}
            faillist.append(message)
            qu.log_events_to_cloudwatch(message, logs, log_group, error_log)
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
                newtheme = qu.create_theme(target_session, target_theme_id, Name, BaseThemeId, Configuration)
                newthemeslist.append(newtheme)
                qu.log_events_to_cloudwatch(
                    {"account_id": account_id, "package": package, "deployment_time": now, "asset_type": "Themes",
                     "asset_guid": target_theme_id, "asset_name": Name,
                     "success": "Theme: " + Name + " is successfully migrated"}, logs, log_group, success_log)
            except Exception as e:
                message = {"account_id": account_id, "package": package, "deployment_time": now, "theme_id": target_theme_id,
                           "name": Name, "error": str(e)}
                faillist.append(message)
                qu.log_events_to_cloudwatch(message, logs, log_group, error_log)
                continue
        elif target_theme_id in already_migrated:
            try:
                newtheme = qu.update_theme(target_session, target_theme_id, Name, BaseThemeId, Configuration)
                newthemeslist.append(newtheme)
                qu.log_events_to_cloudwatch(
                    {"account_id": account_id, "package": package, "deployment_time": now, "asset_type": "Themes",
                     "asset_guid": target_theme_id, "asset_name": Name,
                     "success": "Theme " + target_theme_id + " is successfully updated"}, logs, log_group, success_log)
            except Exception as e:
                message = {"account_id": account_id, "package": package, "deployment_time": now, "theme_id": target_theme_id,
                           "name": Name, "error": str(e)}
                faillist.append(message)
                qu.log_events_to_cloudwatch(message, logs, log_group, error_log)
                continue

    return faillist

'''
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
            qu.log_events_to_cloudwatch(message, logs, log_group,
                                     success_log)
        except Exception:
            message = {"account_id": account_id, "package": package, "deployment_time": now, "dir_file": dashboard_path,
                       "error": str(Exception)}
            faillist.append(message)
            qu.log_events_to_cloudwatch(message, logs, log_group, error_log)
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

        dashboard = qu.describe_dashboard_definition(target_session, targettid)
        if 'Failed to describe dashboard:' in dashboard:
            if 'dashboard/' + targettid + ' is not found' in dashboard:
                try:
                    print('Creating Dashboard: ' + targettid)
                    newdashboard = qu.create_dashboard(target_session, targettid, sourcedid, targettname, res,
                                                    'ENABLED', 'ENABLED', 'COLLAPSED', ('VersionDescription', '1'),
                                                    ('ThemeArn', TargetThemeArn), namespace_name)
                    print(newdashboard)
                    qu.log_events_to_cloudwatch(
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
                    qu.log_events_to_cloudwatch(message, logs, log_group, error_log)
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
                qu.log_events_to_cloudwatch(message, logs, log_group, error_log)
                continue
        elif dashboard['Dashboard']['Version']['Status'] == "CREATION_FAILED":
            try:
                qu.delete_dashboard(target_session, targettid)
                print('Creating Dashboard: ' + targettid)
                newdashboard = qu.create_dashboard(target_session, targettid, sourcedid, targettname, res,
                                                'ENABLED', 'ENABLED', 'COLLAPSED', ('VersionDescription', '1'),
                                                ('ThemeArn', TargetThemeArn), namespace_name)
                qu.log_events_to_cloudwatch(
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
                qu.log_events_to_cloudwatch(message, logs, log_group, error_log)
                continue

        else:
            print('Updating Dashboard: ' + targettid)
            try:
                qu.delete_dashboard(target_session, targettid)
                newdashboard = qu.create_dashboard(target_session, targettid, sourcedid, targettname, res,
                                                'ENABLED', 'ENABLED', 'COLLAPSED', ('VersionDescription', '1'),
                                                ('ThemeArn', TargetThemeArn), namespace_name)
                qu.log_events_to_cloudwatch(
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

        res = qu.describe_dashboard_definition(target_session, targettid)
        if res['Status'] == 200:
            status = res['Dashboard']['Version']['Status']
            while 'PROGRESS' in status:
                time.sleep(3)
                res = qu.describe_dashboard_definition(target_session, targettid)
                status = res['Dashboard']['Version']['Status']
            if 'SUCCESSFUL' in status:
                success.append(res)
            else:
                message = {"account_id": account_id,
                           "package": package, "deployment_time": now,
                           "namespace": namespace, "hashed_namespace": namespace_name, "asset_type": "Dashboards",
                           "error_type": "Dashboard Creation Status is not Successful", "dashboard": res}
                faillist.append(message)
                qu.log_events_to_cloudwatch(message, logs, log_group, error_log)
    return faillist


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


# list data source of source account. This function could be removed
def get_data_source_migration_list(sourcesession, source_migrate_list):
    datasources = qu.list_data_sources(sourcesession)  # get data source details with listdatasource API

    migration_list = []
    for newsource in source_migrate_list:
        ids = qu.get_datasource_ids(newsource, sourcesession)  # Get id of data sources migration list
        for datasource in datasources:
            if ids[0] == datasource["DataSourceId"]:
                migration_list.append(
                    datasource)  # migration_list is an array containing data source connection information and etc

    return migration_list


def migrate_analysis(source_session, target_session, id):
    # please provide the analysis name you would like to migrate to get the id
    faillist = []
    try:
        analysisid = qu.get_analysis_ids('analysis_name', source_session)
    except Exception as e:
        faillist.append({"object_id": 'id', "Name": 'name', "object_type": 'type',
                         "action": 'incremental_migration:get_source_analysis_id', "Error": str(e)})

    if len(analysisid) > 1:
        raise ValueError('There are more than one analysis with the same name. Please check it.')
    return


def process_migration_list(migrate_p, dashboard_migrate_list, analysis_migrate_list, dev_config):
    source_migrate_list = []
    dataset_migrate_list = []
    source_session = qu.assume_role(dev_config["aws_account_number"], dev_config["role_name"],
                                         dev_config["aws_region"])

    if migrate_p in ['dashboard']:
        for dashboard in dashboard_migrate_list:
            print(dashboard)
            datasources = qu.data_sources_ls_of_dashboard(dashboard, source_session)
            print(datasources)  # issue
            for datasource in datasources:
                source_migrate_list.append(datasource)
            datasets = qu.data_sets_ls_of_dashboard(dashboard, source_session)
            print(datasets)
            for dataset in datasets:
                dataset_migrate_list.append(dataset)

    if migrate_p in ['analysis']:
        for analysis_name in analysis_migrate_list:
            print(analysis_name)
            datasources = qu.data_sources_ls_of_analysis(analysis_name, source_session)
            print(datasources)
            for datasource in datasources:
                source_migrate_list.append(datasource)
            datasets = qu.data_sets_ls_of_analysis(analysis_name, source_session)
            print(datasets)
            for dataset in datasets:
                dataset_migrate_list.append(dataset)
            print(dataset_migrate_list)

    if migrate_p in ['all']:
        for dashboard in dashboard_migrate_list:
            datasources = qu.data_sources_ls_of_dashboard(dashboard, source_session)
            for datasource in datasources:
                source_migrate_list.append(datasource)
            datasets = qu.data_sets_ls_of_dashboard(dashboard, source_session)
            for dataset in datasets:
                dataset_migrate_list.append(dataset)

        for analysis_name in analysis_migrate_list:
            datasources = qu.data_sources_ls_of_analysis(analysis_name, source_session)
            for datasource in datasources:
                source_migrate_list.append(datasource)
            datasets = qu.data_sets_ls_of_analysis(analysis_name, source_session)
            for dataset in datasets:
                dataset_migrate_list.append(dataset)
    results = {"source_migrate_list": source_migrate_list, "dataset_migrate_list": dataset_migrate_list}
    print(results)

    return results
