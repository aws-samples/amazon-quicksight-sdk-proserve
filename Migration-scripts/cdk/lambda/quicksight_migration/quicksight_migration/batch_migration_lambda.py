import json
import time
import os
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime
import quicksight_migration.quicksight_utils as qs_utils

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

def migrate(
    region,
    sourcesession,
    targetsession,
    target,
    sourceroot,
    sourceadmin,
    targetroot,
    targetadmin,
    ) -> None:

    # current date and time
    now = str(datetime.now().strftime("%m-%d-%Y_%H_%M"))

    #results output location
    successlocation = "/tmp/Migration_Results/Successful/"
    faillocation = "/tmp/Migration_Results/Fail/"

    try:
        os.makedirs(successlocation)
    except OSError:
        logger.error("Creation of the directory %s failed", successlocation)
    else:
        logger.info("Successfully created the directory %s", successlocation)

    try:
        os.makedirs(faillocation)
    except OSError:
        logger.error("Creation of the directory %s failed", faillocation)
    else:
        logger.info("Successfully created the directory %s", faillocation)

    #new account set up sample
    datasources = qs_utils.data_sources(sourcesession)

    #get data sources which already migrated
    targetsources = qs_utils.data_sources(targetsession)

    #already_migrated record the data source ids of target account
    already_migrated=[]
    for tsource in targetsources:
        already_migrated.append(tsource['DataSourceId'])

    newsourceslist = []
    faillist = []
    for i in datasources:
        if i['DataSourceId'] not in already_migrated and 'DataSourceParameters' in i:
            newdsource = qs_utils.create_data_source(i, targetsession, target)
            if 'Error' in newdsource:
                faillist.append(newdsource)
            else:
                newsourceslist.append(newdsource)

    with open(faillocation+now+'_Datasource_Creation_Error.json', "w") as file_:
        json.dump(faillist, file_, indent=4, sort_keys=True, default=str)

    faillist2 = []
    successfulls = []
    for news in newsourceslist:
        datasource = qs_utils.describe_source(targetsession, news['DataSourceId'])

        if datasource['DataSource']['Status'] == "CREATION_FAILED":
            qs_utils.delete_source(targetsession, news['DataSourceId'])
            faillist2.append(news['DataSourceId'])

        if datasource['DataSource']['Status'] == "CREATION_SUCCESSFUL":
            successfulls.append(datasource['DataSource'])

        while datasource['DataSource']['Status'] == "CREATION_IN_PROGRESS":
            time.sleep(5)
            datasource = qs_utils.describe_source(targetsession, news['DataSourceId'])
            if datasource['DataSource']['Status'] == "CREATION_SUCCESSFUL":
                successfulls.append(datasource['DataSource'])
                break
            elif datasource['DataSource']['Status'] == "CREATION_FAILED":
                qs_utils.delete_source(targetsession, news['DataSourceId'])
                faillist2.append(news['DataSourceId'])

    with open(faillocation+now+'_Datasource_Creation_Fail.json', "w") as file_:
        json.dump(faillist2, file_, indent=4, sort_keys=True, default=str)

    with open(successlocation+now+'_Datasource_Creation_Success.json', "w") as file_:
        json.dump(successfulls, file_, indent=4, sort_keys=True, default=str)

    datasets = qs_utils.data_sets(sourcesession)

    #get datasets which already migrated
    targetds = qs_utils.data_sets(targetsession)

    #already_migrated record the datasets ids of target account
    already_migrated=[]
    for dataset in targetds:
        already_migrated.append(dataset['DataSetId'])

    newsetslist=[]
    faillist=[]
    sts_client = targetsession.client("sts")
    account_id = sts_client.get_caller_identity()["Account"]
    for i in datasets:
        if i['DataSetId'] not in already_migrated:
            try:
                res = qs_utils.describe_dataset(sourcesession, i['DataSetId'])
            except Exception:
                faillist.append({"Dataset": i, "Error": str(Exception)})
                continue

            name=i['Name'].replace(" ", "_")
            datasetid=i['DataSetId']

            physical_table = res['DataSet']['PhysicalTableMap']
            for key, value in physical_table.items():
                for i,j in value.items():
                    dsid = j['DataSourceArn'].split("/")[1]
                    j['DataSourceArn'] = 'arn:aws:quicksight:us-east-1:'+account_id+':datasource/'+dsid

            logical_table = res['DataSet']['LogicalTableMap']

            try:
                newdataset = qs_utils.create_dataset(
                    targetsession, datasetid, name, physical_table, logical_table,
                    res['DataSet']['ImportMode'], target['datasetpermission']
                )
                newsetslist.append(newdataset)
            except Exception as ex:
                faillist.append({"DataSetId": datasetid, "Name": name, "Error": str(ex)})
                continue

    #print fail informations
    with open(faillocation+now+'Dataset_Creation_Error.json', "w") as file_:
        json.dump(faillist, file_, indent=4, sort_keys=True, default=str)

    successfulls=[]
    for news in newsetslist:
        dataset = qs_utils.describe_dataset(targetsession, news['DataSetId'])
        successfulls.append(dataset['DataSet'])

    with open(successlocation+now+'Datasets_Creation_Success.json', "w") as file_:
        json.dump(successfulls, file_, indent=4, sort_keys=True, default=str)

    themes_list = qs_utils.themes(sourcesession)

    #get themes which already migrated
    targetthemes = qs_utils.themes(targetsession)
    #already_migrated record the datasets ids of target account
    already_migrated = []
    for theme in targetthemes:
        already_migrated.append(theme['ThemeId'])

    newthemeslist = []
    faillist = []
    sts_client = targetsession.client("sts")
    account_id = sts_client.get_caller_identity()["Account"]
    for i in themes_list:
        if i['ThemeId'] not in already_migrated:
            try:
                res = qs_utils.describe_theme(sourcesession, i['ThemeId'])
            except Exception:
                faillist.append({"Theme": i, "Error": str(Exception)})
                continue
            theme_id = res['Theme']['ThemeId']
            theme_name = res['Theme']['Name']
            base_theme_id = res['Theme']['Version']['BaseThemeId']
            configuration = res['Theme']['Version']['Configuration']
            try:
                newtheme = qs_utils.create_theme(targetsession,theme_id, theme_name,
                                                base_theme_id, configuration)
                newthemeslist.append(newtheme)
            except Exception as ex:
                faillist.append({"ThemeID": theme_id, "Name": theme_name, "Error": str(ex)})
                continue
            try:
                qs_utils.update_theme_permissions(targetsession, theme_id, targetadmin)
            except Exception as ex:
                faillist.append({"ThemeID": theme_id, "Name": theme_name, "Error": str(ex)})
                continue

    #print fail informations
    with open(faillocation+now+'Themes_Creation_Error.json', "w") as file_:
        json.dump(faillist, file_, indent=4, sort_keys=True, default=str)

    successfulls=[]
    for news in newthemeslist:
        theme = qs_utils.describe_theme(targetsession, news['ThemeId'])
        successfulls.append(theme['Theme']['ThemeId'])

    with open(successlocation+now+'Themes_Creation_Success.json', "w") as file_:
        json.dump(successfulls, file_, indent=4, sort_keys=True, default=str)

    sourceanalysis_list = qs_utils.analysis(sourcesession)

    sourceanalysis_all = []
    for i in sourceanalysis_list:
        if i['Status'] != 'DELETED':
            sourceanalysis_all.append(i)

    success = []
    faillist = []
    sts_client = targetsession.client("sts")
    account_id = sts_client.get_caller_identity()["Account"]

    for i in sourceanalysis_all:
        sourceanalysis = qs_utils.describe_analysis(sourcesession, i['AnalysisId'])
        sourceanalysisid = sourceanalysis['Analysis']['AnalysisId']
        sourceanalysis_arn = sourceanalysis['Analysis']['Arn']
        sourceanalysisname = sourceanalysis['Analysis']['Name']
        dataset_arns = sourceanalysis['Analysis']['DataSetArns']
        sourcetid = sourceanalysisid
        sourcetname = sourceanalysisname
        targettid = sourcetid
        targettname = sourceanalysisname

        target_theme_arn=''
        if 'ThemeArn' in sourceanalysis['Analysis'].keys():
            source_theme_arn = sourceanalysis['Analysis']['ThemeArn']
            target_theme_arn = 'arn:aws:quicksight:'+region+':'+account_id+':theme/'+sourceanalysis['Analysis']['ThemeArn'].split("/")[1]

        sourcedsref = []
        for dataset in dataset_arns:
            missing = False
            did = dataset.split("/")[1]
            try:
                dname = qs_utils.get_dataset_name(did, sourcesession)
            except Exception as ex:
                faillist.append(
                    {
                        "Error Type": "Dataset: "+did+" is missing!",
                        "sourceanalysisid": sourcetid,
                        "Name": sourcetname,
                        "Error": str(ex)
                    }
                )
                missing = True
                break

            sourcedsref.append({'DataSetPlaceholder': dname,
                        'DataSetArn': dataset})
        if missing:
            continue
        try:
            sourcetemplate = qs_utils.create_template(
                sourcesession, sourcetid, sourcetname, sourcedsref, sourceanalysis_arn, '1')
            sourcetemplate = qs_utils.describe_template(sourcesession,sourcetid)
        except Exception as ex:
            faillist.append(
                {
                    "Error Type": "Create Source Template Error",
                    "sourceanalysisid": sourcetid,
                    "Name": sourcetname,
                    "Error": str(ex)
                }
            )
            continue

        while sourcetemplate['Template']['Version']['Status'] == "CREATION_IN_PROGRESS":
            time.sleep(5)
            sourcetemplate = qs_utils.describe_template(sourcesession,sourcetid)
            if sourcetemplate['Template']['Version']['Status'] == "CREATION_SUCCESSFUL":
                try:
                    updateres = qs_utils.update_template_permission(
                        sourcesession, sourcetid, targetroot)
                except Exception as ex:
                    qs_utils.delete_template(sourcesession, sourcetid)
                    faillist.append({"Error Type": "Update Source Template Permission Error",
                                    "sourceanalysisid": sourcetid,
                                    "Name": sourcetname,
                                    "Error": str(ex)})
        else:
            if sourcetemplate['Template']['Version']['Status'] == "CREATION_SUCCESSFUL":
                try:
                    updateres = qs_utils.update_template_permission(
                        sourcesession, sourcetid, targetroot)
                except Exception as ex:
                    qs_utils.delete_template(sourcesession, sourcetid)
                    faillist.append({"Error Type": "Update Source Template Permission Error",
                                    "sourceanalysisid": sourcetid,
                                    "Name": sourcetname,
                                    "Error": str(ex)})
                    continue

        datasets = qs_utils.data_sets(targetsession)
        template = sourcetemplate['Template']
        dsref = []
        missing = False

        for i in template['Version']['DataSetConfigurations']:
            config = template['Version']['DataSetConfigurations'].index(i)
            for j in datasets:
                if i['Placeholder']==j['Name']:
                    dsref.append({
                        'DataSetPlaceholder': i['Placeholder'],
                        'DataSetArn': j['Arn']
                    })
                if config>len(dsref):
                    place_holder = "Dataset "+i['Placeholder']+"is missing!"
                    faillist.append(
                        {
                            "Error Type": "Datasets in target env are missing for this analysis",
                            "sourceanalysisid": sourcetid,
                            "Name": sourcetname,
                            "Error": str(place_holder)
                        }
                    )
                    missing=True
                    break
            if missing:
                break
        if missing:
            continue

    # working
        source_entity = {
            'SourceTemplate': {
                'DataSetReferences': dsref,
                'Arn': template['Arn']
            }
        }

        analysis = qs_utils.describe_analysis(targetsession, targettid)
        if 'Faild to describe analysis:' in analysis or analysis['Analysis']['Status'] == 'DELETED':
            if 'analysis/'+targettid+' is not found' in analysis or analysis['Analysis']['Status'] == 'DELETED':
                logger.info("Create new anlaysis now:")
                try:
                    newanalysis = qs_utils.create_analysis(
                        targetsession, targettid, targettname,
                        targetadmin, source_entity, target_theme_arn
                    )
                except Exception as ex:
                    qs_utils.delete_template(sourcesession, targettid)
                    faillist.append({"Error Type": "Create New Analysis Error",
                                    "AnalysisID": targettid,
                                    "Name": targettname,
                                    "Error": str(ex)})
                    continue
            else:
                faillist.append({"Error Type": "Describe Target Analysis Error",
                                    "AnalysisID": targettid,
                                    "Name": targettname,
                                    "Error": str(analysis)})
                continue
        elif analysis['Analysis']['Status'] == "CREATION_FAILED":
            res = qs_utils.delete_analysis(sourcesession, targettid)
            try:
                newanalysis = qs_utils.create_analysis(
                    targetsession, targettid, targettname,
                    targetadmin, source_entity, target_theme_arn
                )
            except Exception as ex:
                qs_utils.delete_template(sourcesession, targettid)
                faillist.append({"Error Type": "Create Analysis Error",
                                    "AnalysisID": targettid,
                                    "Name": targettname,
                                    "Error": str(ex)})
                continue
        else:
            logger.info("analysis is existing. update it now.")
            try:
                newanalysis = qs_utils.update_analysis(
                    targetsession, targettid, targettname, source_entity)
            except Exception as ex:
                qs_utils.delete_template(sourcesession, targettid)
                faillist.append({"Error Type": "Update Analysis Error",
                                    "AnalysisID": targettid,
                                    "Name": targettname,
                                    "Error": str(ex)})
                continue
        time.sleep(20)
        res = qs_utils.describe_analysis(targetsession,newanalysis['AnalysisId'])
        if res['Status']==200:
            status = res['Analysis']['Status']
            if status == 'CREATION_SUCCESSFUL' or status == 'UPDATE_SUCCESSFUL':
                success.append(res['Analysis'])
            else:
                faillist.append({"Error Type": "Analysis Creation Status is not Successful",
                                "Analysis": res['Analysis']})

    with open(faillocation+now+'Analysis_Error.json', "w") as file_:
        json.dump(faillist, file_, indent=4, sort_keys=True, default=str)

    with open(successlocation+now+'Analysis_Success.json', "w") as file_:
        json.dump(success, file_, indent=4, sort_keys=True, default=str)

    # dashboards
    sourcedashboards = qs_utils.dashboards(sourcesession)
    success = []
    faillist = []

    for i in sourcedashboards:
        sourcedashboard = qs_utils.describe_dashboard(sourcesession, i['DashboardId'])
        source_entity_arn = sourcedashboard['Dashboard']['Version']['SourceEntityArn']

        if source_entity_arn.split("/")[0].split(":")[-1]=="analysis":
            sourceanalysis = sourcedashboard['Dashboard']['Version']['SourceEntityArn']
        else:
            faillist.append(
                {
                    "Error Type": "Source Analysis is missing!",
                    "DashboardId": sourcetid,
                    "Name": sourcetname,
                    "Error": "Source Analysis is missing!"
                }
            )
            continue

        sourceversion = sourcedashboard['Dashboard']['Version']['VersionNumber']
        sourcedid = sourcedashboard['Dashboard']['DashboardId']
        sourcedname = sourcedashboard['Dashboard']['Name']
        sourcetid = sourcedid
        sourcetname = sourcedname
        targettid = sourcetid
        targettname = sourcedname
        data_set_arns = sourcedashboard['Dashboard']['Version']['DataSetArns']
        sourcedsref = []

        for i in data_set_arns:
            missing = False
            did = i.split("/")[1]

            try:
                dname = qs_utils.get_dataset_name(did, sourcesession)
            except Exception as ex:
                faillist.append(
                    {
                        "Error Type": "Dataset: "+did+" is missing!",
                        "DashboardId": sourcetid,
                        "Name": sourcetname,
                        "Error": str(ex)
                    }
                )
                missing=True
                break

            sourcedsref.append({'DataSetPlaceholder': dname,
                        'DataSetArn': i})
        if missing:
            continue
        try:
            sourcetemplate = qs_utils.create_template(
                sourcesession, sourcetid, sourcetname, sourcedsref, sourceanalysis, '1')
            sourcetemplate = qs_utils.describe_template(sourcesession,sourcetid)
        except Exception as ex:
            faillist.append(
                {
                    "Error Type": "Create Source Template Error",
                    "DashboardId": sourcetid,
                    "Name": sourcetname,
                    "Error": str(ex)
                }
            )
            continue

        while sourcetemplate['Template']['Version']['Status'] == "CREATION_IN_PROGRESS":
            time.sleep(5)
            sourcetemplate = qs_utils.describe_template(sourcesession,sourcetid)
            if sourcetemplate['Template']['Version']['Status'] == "CREATION_SUCCESSFUL":
                try:
                    updateres = qs_utils.update_template_permission(
                        sourcesession, sourcetid, targetroot)
                except Exception as ex:
                    qs_utils.delete_template(sourcesession, sourcetid)
                    faillist.append({"Error Type": "Update Source Template Permission Error",
                                    "DashboardId": sourcetid,
                                    "Name": sourcetname,
                                    "Error": str(ex)})
        else:
            if sourcetemplate['Template']['Version']['Status'] == "CREATION_SUCCESSFUL":
                try:
                    updateres = qs_utils.update_template_permission(
                        sourcesession, sourcetid, targetroot
                    )
                except Exception as ex:
                    qs_utils.delete_template(sourcesession, sourcetid)
                    faillist.append({"Error Type": "Update Source Template Permission Error",
                                    "DashboardId": sourcetid,
                                    "Name": sourcetname,
                                    "Error": str(ex)})
                    continue

        if updateres['Status'] == 200:
            try:
                targettemplate = qs_utils.copy_template(
                    targetsession, targettid, targettname, updateres['TemplateArn'])
            except Exception as ex:
                qs_utils.delete_template(sourcesession, sourcetid)
                faillist.append({"Error Type": "Copy Template Error",
                                "DashboardId": sourcetid,
                                "Name": sourcetname,
                                "Error": str(ex)})
                continue
        else:
            qs_utils.delete_template(sourcesession, sourcetid)
            faillist.append({"Error Type": "Update Source Template Permission Error",
                                    "DashboardId": sourcetid,
                                    "Name": sourcetname,
                                    "Error": str(ex)})
            continue

        targettemplate = qs_utils.describe_template(targetsession,targettid)

        while targettemplate['Template']['Version']['Status'] == "CREATION_IN_PROGRESS":
            time.sleep(5)
            targettemplate = qs_utils.describe_template(targetsession,targettid)
            if targettemplate['Template']['Version']['Status'] == "CREATION_SUCCESSFUL":
                break
        else:
            if targettemplate['Template']['Version']['Status'] == "CREATION_SUCCESSFUL":
                logger.info("Template is successful copied!")
            else:
                qs_utils.delete_template(targetsession, targettid)
                faillist.append({"Error Type": "Copy Template Error",
                                    "DashboardId": sourcetid,
                                    "Name": sourcetname,
                                    "Error": str(e)})
                continue

        datasets = qs_utils.data_sets(targetsession)
        template = targettemplate['Template']
        dsref=[]

        missing = False
        for i in template['Version']['DataSetConfigurations']:
            config = template['Version']['DataSetConfigurations'].index(i)
            for j in datasets:
                if i['Placeholder'] == j['Name']:
                    dsref.append({
                        'DataSetPlaceholder': i['Placeholder'],
                        'DataSetArn': j['Arn']
                    })
                if config>len(dsref):
                    ex = "Dataset "+i['Placeholder']+"is missing!"
                    faillist.append(
                        {
                            "Error Type": "Datasets in target env are missing for this dashboard",
                            "DashboardId": sourcetid,
                            "Name": sourcetname,
                            "Error": str(ex)
                        }
                    )
                    missing = True
                    break
            if missing:
                break
        if missing:
            continue

        source_entity = {
            'SourceTemplate': {
                'DataSetReferences': dsref,
                'Arn': template['Arn']
            }
        }

        dashboard = qs_utils.describe_dashboard(targetsession, targettid)

        if 'Faild to describe dashboard:' in dashboard:
            if 'dashboard/'+targettid+' is not found' in dashboard:
                logger.info("Create new dashboard now:")
                try:
                    newdashboard = qs_utils.create_dashboard(
                        targetsession, targettid, targettname,
                        targetadmin, source_entity, '1', filter='ENABLED',
                        csv='ENABLED', sheetcontrol='COLLAPSED'
                    )
                except Exception as e:
                    qs_utils.delete_template(targetsession, targettid)
                    faillist.append({"Error Type": "Create New Dashboard Error",
                                    "DashboardId": targettid,
                                    "Name": targettname,
                                    "Error": str(ex)})
                    continue
            else:
                faillist.append({"Error Type": "Describe Target Dashboard Error",
                                    "DashboardId": targettid,
                                    "Name": targettname,
                                    "Error": str(dashboard)})
                continue
        elif dashboard['Dashboard']['Version']['Status'] == "CREATION_FAILED":
            res = qs_utils.delete_dashboard(targetsession, targettid)
            try:
                newdashboard = qs_utils.create_dashboard(
                    targetsession, targettid, targettname,
                    targetadmin, source_entity, '1', filter='ENABLED',
                    csv='ENABLED', sheetcontrol='COLLAPSED'
                )
            except Exception as ex:
                qs_utils.delete_template(targetsession, targettid)
                faillist.append({"Error Type": "Create Dashboard Error",
                                    "DashboardId": targettid,
                                    "Name": targettname,
                                    "Error": str(ex)})
                continue

        else:
            logger.info("dashboard is existing. update it now.")
            try:
                newdashboard = qs_utils.update_dashboard(
                    targetsession, targettid, targettname, 
                    source_entity, target['version'], filter='ENABLED',
                    csv='ENABLED', sheetcontrol='EXPANDED'
                )
            except Exception as ex:
                qs_utils.delete_template(targetsession, targettid)
                faillist.append({"Error Type": "Update Dashboard Error",
                                    "DashboardId": targettid,
                                    "Name": targettname,
                                    "Error": str(ex)})
                continue

        res = qs_utils.describe_dashboard(targetsession,newdashboard['DashboardId'])

        if res['Status']==200:
            status = res['Dashboard']['Version']['Status']
            if status=='CREATION_SUCCESSFUL' or status=='UPDATE_SUCCESSFUL':
                success.append(res['Dashboard'])
            else:
                faillist.append(
                    {
                        "Error Type": "Dashboard Creation Status is not Successful",
                        "Dashboard": res['Dashboard']
                    }
                )

    with open(faillocation+now+'Dashboard_Error.json', "w") as file_:
        json.dump(faillist, file_, indent=4, sort_keys=True, default=str)

    with open(successlocation+now+'Dashboard_Success.json', "w") as file_:
        json.dump(success, file_, indent=4, sort_keys=True, default=str)
