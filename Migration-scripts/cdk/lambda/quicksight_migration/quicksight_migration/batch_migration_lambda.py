import time
import logging
from typing import Any, Dict, List, Optional
import quicksight_migration.quicksight_utils as qs_utils

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

def migrate(
    source_region,
    target_region,
    sourcesession,
    targetsession,
    target,
    targetadmin,
    ) -> None:

    # Source Quicksight data sources
    datasources = qs_utils.data_sources(sourcesession)
    # Target Quicksight data sources
    targetsources = qs_utils.data_sources(targetsession)
    # Already migrated data source IDs
    already_migrated=[]
    for tsource in targetsources:
        already_migrated.append(tsource['DataSourceId'])

    newsourceslist = []
    datasource_failed = []
    for datasource in datasources:
        if datasource['DataSourceId'] not in already_migrated and ['DataSourceParameters', 'TIMESTREAM'] in datasource:
            newdsource = qs_utils.create_data_source(datasource, targetsession, target)
            if 'Error' in newdsource:
                datasource_failed.append(newdsource)
            else:
                newsourceslist.append(newdsource)

    logger.info("Datasource creation failed: %s", datasource_failed)

    datasource_error = []
    datasource_success = []
    for news in newsourceslist:
        datasource = qs_utils.describe_source(targetsession, news['DataSourceId'])

        if datasource['DataSource']['Status'] == "CREATION_FAILED":
            qs_utils.delete_source(targetsession, news['DataSourceId'])
            datasource_error.append(news['DataSourceId'])

        if datasource['DataSource']['Status'] == "CREATION_SUCCESSFUL":
            datasource_success.append(datasource['DataSource'])

        while datasource['DataSource']['Status'] == "CREATION_IN_PROGRESS":
            time.sleep(5)
            datasource = qs_utils.describe_source(targetsession, news['DataSourceId'])
            if datasource['DataSource']['Status'] == "CREATION_SUCCESSFUL":
                datasource_success.append(datasource['DataSource'])
                break
            elif datasource['DataSource']['Status'] == "CREATION_FAILED":
                qs_utils.delete_source(targetsession, news['DataSourceId'])
                datasource_error.append(news['DataSourceId'])

    logger.info("Datasource creation errors: %s", datasource_error)
    logger.info("Datasource creation successes: %s", datasource_success)

    # Source Quicksight datasets
    datasets = qs_utils.data_sets(sourcesession)
    # Target Quicksight datasets
    targetds = qs_utils.data_sets(targetsession)
    # Already migrated datasets IDs
    already_migrated=[]
    for dataset in targetds:
        already_migrated.append(dataset['DataSetId'])

    dataset_new=[]
    dataset_failed=[]
    sts_client = targetsession.client("sts")
    account_id = sts_client.get_caller_identity()["Account"]
    for dataset in datasets:
        if dataset['DataSetId'] not in already_migrated:
            try:
                res = qs_utils.describe_dataset(sourcesession, dataset['DataSetId'])
            except Exception:
                dataset_failed.append({"Dataset": dataset, "Error": str(Exception)})
                continue

            name = dataset['Name'].replace(" ", "_")
            dataset_id = dataset['DataSetId']

            physical_table = res['DataSet']['PhysicalTableMap']
            for key, value in physical_table.items():
                for i, j in value.items():
                    dsid = j['DataSourceArn'].split("/")[1]
                    j['DataSourceArn'] = f'arn:aws:quicksight:{target_region}:{account_id}:datasource/{dsid}'

            logical_table = res['DataSet']['LogicalTableMap']

            try:
                newdataset = qs_utils.create_dataset(
                    targetsession, dataset_id, name, physical_table, logical_table,
                    res['DataSet']['ImportMode'], target['datasetpermission']
                )
                dataset_new.append(newdataset)
            except Exception as ex:
                dataset_failed.append({"DataSetId": dataset_id, "Name": name, "Error": str(ex)})
                continue

    logger.info("Dataset creation failed: %s", dataset_failed)
    logger.info("Dataset created: %s", dataset_new)

    dataset_success=[]
    for news in dataset_new:
        dataset = qs_utils.describe_dataset(targetsession, news['DataSetId'])
        dataset_success.append(dataset['DataSet'])

    logger.info("Dataset successes: %s", dataset_success)

    # Source Quicksight themes
    source_themes = qs_utils.themes(sourcesession)
    # Target Quicksight themes
    target_themes = qs_utils.themes(targetsession)
    # Already migrated theme ID's
    already_migrated = []
    for theme in target_themes:
        already_migrated.append(theme['ThemeId'])

    themes_new = []
    themes_failed = []
    sts_client = targetsession.client("sts")
    account_id = sts_client.get_caller_identity()["Account"]
    for theme in source_themes:
        if theme['ThemeId'] not in already_migrated:
            try:
                res = qs_utils.describe_theme(sourcesession, theme['ThemeId'])
            except Exception:
                themes_failed.append({"Theme": theme, "Error": str(Exception)})
                continue
            theme_id = res['Theme']['ThemeId']
            theme_name = res['Theme']['Name']
            base_theme_id = res['Theme']['Version']['BaseThemeId']
            configuration = res['Theme']['Version']['Configuration']
            try:
                new_theme = qs_utils.create_theme(targetsession, theme_id, theme_name,
                                                    base_theme_id, configuration)
                themes_new.append(new_theme)
            except Exception as ex:
                themes_failed.append({"ThemeID": theme_id, "Name": theme_name, "Error": str(ex)})
                continue
            try:
                qs_utils.update_theme_permissions(targetsession, theme_id, targetadmin)
            except Exception as ex:
                themes_failed.append({"ThemeID": theme_id, "Name": theme_name, "Error": str(ex)})
                continue

    logger.info("Themes creation failed: %s", themes_failed)

    themes_success=[]
    for news in themes_new:
        theme = qs_utils.describe_theme(targetsession, news['ThemeId'])
        themes_success.append(theme['Theme']['ThemeId'])

    logger.info("Themes successes: %s", themes_success)

    source_analyses_all = qs_utils.analysis(sourcesession)

    source_analyses = []
    for analysis in source_analyses_all:
        if analysis['Status'] != 'DELETED':
            source_analyses.append(analysis)

    analysis_success = []
    analysis_failed = []
    sts_client = targetsession.client("sts")
    account_id = sts_client.get_caller_identity()["Account"]

    for analysis in source_analyses:
        source_analysis = qs_utils.describe_analysis(sourcesession, analysis['AnalysisId'])
        source_analysis_id = source_analysis['Analysis']['AnalysisId']
        source_analysis_arn = source_analysis['Analysis']['Arn']
        source_analysis_name = source_analysis['Analysis']['Name']
        dataset_arns = source_analysis['Analysis']['DataSetArns']

        target_theme_arn=''
        if 'ThemeArn' in source_analysis['Analysis'].keys():
            target_theme_arn = f'arn:aws:quicksight:{target_region}:{account_id}:theme/'+source_analysis['Analysis']['ThemeArn'].split("/")[1]

        sourcedsref = []
        for dataset in dataset_arns:
            missing = False
            did = dataset.split("/")[1]
            try:
                dname = qs_utils.get_dataset_name(did, sourcesession)
            except Exception as ex:
                analysis_failed.append(
                    {
                        "Error Type": f"Dataset: {did} is missing!",
                        "sourceanalysisid": source_analysis_id,
                        "Name": source_analysis_name,
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
            qs_utils.create_template(sourcesession, source_analysis_id, source_analysis_name,
                sourcedsref, source_analysis_arn, '1')
            source_template = qs_utils.describe_template(sourcesession, source_analysis_id)
        except Exception as ex:
            analysis_failed.append(
                {
                    "Error Type": "Create Source Template Error",
                    "sourceanalysisid": source_analysis_id,
                    "Name": source_analysis_name,
                    "Error": str(ex)
                }
            )
            continue

        while source_template['Template']['Version']['Status'] == "CREATION_IN_PROGRESS":
            time.sleep(5)
            source_template = qs_utils.describe_template(sourcesession, source_analysis_id)
            if source_template['Template']['Version']['Status'] == "CREATION_SUCCESSFUL":
                try:
                    updateres = qs_utils.update_template_permission(
                        sourcesession, source_analysis_id, targetadmin)
                except Exception as ex:
                    qs_utils.delete_template(sourcesession, source_analysis_id)
                    analysis_failed.append(
                        {
                            "Error Type": "Update Source Template Permission Error",
                            "sourceanalysisid": source_analysis_id,
                            "Name": source_analysis_name,
                            "Error": str(ex)
                        }
                    )
        else:
            if source_template['Template']['Version']['Status'] == "CREATION_SUCCESSFUL":
                try:
                    updateres = qs_utils.update_template_permission(
                        sourcesession, source_analysis_id, targetadmin)
                except Exception as ex:
                    qs_utils.delete_template(sourcesession, source_analysis_id)
                    analysis_failed.append(
                        {
                            "Error Type": "Update Source Template Permission Error",
                            "sourceanalysisid": source_analysis_id,
                            "Name": source_analysis_name,
                            "Error": str(ex)
                        }
                    )
                    continue

        datasets = qs_utils.data_sets(targetsession)
        template = source_template['Template']
        dsref = []
        missing = False

        for dsc in template['Version']['DataSetConfigurations']:
            config = template['Version']['DataSetConfigurations'].index(dsc)
            for dataset in datasets:
                if dsc['Placeholder'] == dataset['Name']:
                    dsref.append({
                        'DataSetPlaceholder': dsc['Placeholder'],
                        'DataSetArn': dataset['Arn']
                    })
                if config > len(dsref):
                    place_holder = f"Dataset {dsc['Placeholder']} is missing!"
                    analysis_failed.append(
                        {
                            "Error Type": "Datasets in target env are missing for this analysis",
                            "sourceanalysisid": source_analysis_id,
                            "Name": source_analysis_name,
                            "Error": str(place_holder)
                        }
                    )
                    missing=True
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

        analysis = qs_utils.describe_analysis(targetsession, source_analysis_id)
        if 'Faild to describe analysis:' in analysis or analysis['Analysis']['Status'] == 'DELETED':
            if 'analysis/'+source_analysis_id+' is not found' in analysis or analysis['Analysis']['Status'] == 'DELETED':
                logger.info("Create new analysis: %s", source_analysis_name)
                try:
                    newanalysis = qs_utils.create_analysis(
                        targetsession, source_analysis_id, source_analysis_name,
                        targetadmin, source_entity, target_theme_arn
                    )
                except Exception as ex:
                    qs_utils.delete_template(sourcesession, source_analysis_id)
                    analysis_failed.append({"Error Type": "Create New Analysis Error",
                                    "AnalysisID": source_analysis_id,
                                    "Name": source_analysis_name,
                                    "Error": str(ex)})
                    continue
            else:
                analysis_failed.append({"Error Type": "Describe Target Analysis Error",
                                    "AnalysisID": source_analysis_id,
                                    "Name": source_analysis_name,
                                    "Error": str(analysis)})
                continue
        elif analysis['Analysis']['Status'] == "CREATION_FAILED":
            res = qs_utils.delete_analysis(sourcesession, source_analysis_id)
            try:
                newanalysis = qs_utils.create_analysis(
                    targetsession, source_analysis_id, source_analysis_name,
                    targetadmin, source_entity, target_theme_arn
                )
            except Exception as ex:
                qs_utils.delete_template(sourcesession, source_analysis_id)
                analysis_failed.append({"Error Type": "Create Analysis Error",
                                    "AnalysisID": source_analysis_id,
                                    "Name": source_analysis_name,
                                    "Error": str(ex)})
                continue
        else:
            logger.info("Analysis already exists, updating instead: %s", source_analysis_name)
            try:
                newanalysis = qs_utils.update_analysis(
                    targetsession, source_analysis_id, source_analysis_name, source_entity)
            except Exception as ex:
                qs_utils.delete_template(sourcesession, source_analysis_id)
                analysis_failed.append({"Error Type": "Update Analysis Error",
                                    "AnalysisID": source_analysis_id,
                                    "Name": source_analysis_name,
                                    "Error": str(ex)})
                continue
        time.sleep(20)
        res = qs_utils.describe_analysis(targetsession, newanalysis['AnalysisId'])
        if res['Status']==200:
            status = res['Analysis']['Status']
            if status == 'CREATION_SUCCESSFUL' or status == 'UPDATE_SUCCESSFUL':
                analysis_success.append(res['Analysis'])
            else:
                analysis_failed.append({"Error Type": "Analysis Creation Status is not Successful",
                                "Analysis": res['Analysis']})

    logger.info("Analysis creation failed: %s", analysis_failed)
    logger.info("Analysis creation successes: %s", analysis_success)

    # DASHBOARDS
    source_dashboards = qs_utils.dashboards(sourcesession)
    dashboard_success = []
    dashboard_failed = []

    for dashboard in source_dashboards:
        source_dashboard = qs_utils.describe_dashboard(sourcesession, dashboard['DashboardId'])
        source_entity_arn = source_dashboard['Dashboard']['Version']['SourceEntityArn']

        if source_entity_arn.split("/")[0].split(":")[-1] == "analysis":
            source_analysis = source_dashboard['Dashboard']['Version']['SourceEntityArn']
        else:
            dashboard_failed.append(
                {
                    "Error Type": "Source Analysis is missing!",
                    "DashboardId": source_analysis_id,
                    "Name": source_analysis_name,
                    "Error": "Source Analysis is missing!"
                }
            )
            continue

        source_version = source_dashboard['Dashboard']['Version']['VersionNumber']
        source_dash_id = source_dashboard['Dashboard']['DashboardId']
        source_dash_name = source_dashboard['Dashboard']['Name']
        dataset_arns = source_dashboard['Dashboard']['Version']['DataSetArns']
        sourcedsref = []

        for dataset_arn in dataset_arns:
            missing = False
            dataset_id = dataset_arn.split("/")[1]

            try:
                dname = qs_utils.get_dataset_name(dataset_id, sourcesession)
            except Exception as ex:
                dashboard_failed.append(
                    {
                        "Error Type": f"Dataset: {dataset_id} is missing!",
                        "DashboardId": source_dash_id,
                        "Name": source_dash_name,
                        "Error": str(ex)
                    }
                )
                missing=True
                break

            sourcedsref.append({'DataSetPlaceholder': dname,
                        'DataSetArn': dataset_arn})
        if missing:
            continue
        try:
            source_template = qs_utils.create_template(
                sourcesession, source_dash_id, source_dash_name, sourcedsref, source_analysis, '1')
            source_template = qs_utils.describe_template(sourcesession, source_dash_id)
        except Exception as ex:
            dashboard_failed.append(
                {
                    "Error Type": "Create Source Template Error",
                    "DashboardId": source_dash_id,
                    "Name": source_dash_name,
                    "Error": str(ex)
                }
            )
            continue

        while source_template['Template']['Version']['Status'] == "CREATION_IN_PROGRESS":
            time.sleep(5)
            source_template = qs_utils.describe_template(sourcesession, source_dash_id)
            if source_template['Template']['Version']['Status'] == "CREATION_SUCCESSFUL":
                try:
                    updateres = qs_utils.update_template_permission(
                        sourcesession, source_dash_id, targetadmin)
                except Exception as ex:
                    qs_utils.delete_template(sourcesession, source_dash_id)
                    dashboard_failed.append(
                        {
                            "Error Type": "Update Source Template Permission Error",
                            "DashboardId": source_dash_id,
                            "Name": source_dash_name,
                            "Error": str(ex)
                        }
                    )
        else:
            if source_template['Template']['Version']['Status'] == "CREATION_SUCCESSFUL":
                try:
                    updateres = qs_utils.update_template_permission(
                        sourcesession, source_dash_id, targetadmin
                    )
                except Exception as ex:
                    qs_utils.delete_template(sourcesession, source_dash_id)
                    dashboard_failed.append(
                        {
                            "Error Type": "Update Source Template Permission Error",
                            "DashboardId": source_dash_id,
                            "Name": source_dash_name,
                            "Error": str(ex)
                        }
                    )
                    continue

        if updateres['Status'] == 200:
            try:
                targettemplate = qs_utils.copy_template(
                    targetsession, source_dash_id, source_dash_name, updateres['TemplateArn'])
            except Exception as ex:
                qs_utils.delete_template(sourcesession, source_dash_id)
                dashboard_failed.append(
                    {
                        "Error Type": "Copy Template Error",
                        "DashboardId": source_dash_id,
                        "Name": source_dash_name,
                        "Error": str(ex)
                    }
                )
                continue
        else:
            qs_utils.delete_template(sourcesession, source_dash_id)
            dashboard_failed.append(
                {
                    "Error Type": "Update Source Template Permission Error",
                    "DashboardId": source_dash_id,
                    "Name": source_dash_name,
                    "Error": str(ex)
                }
            )
            continue

        targettemplate = qs_utils.describe_template(targetsession, source_dash_id)

        while targettemplate['Template']['Version']['Status'] == "CREATION_IN_PROGRESS":
            time.sleep(5)
            targettemplate = qs_utils.describe_template(targetsession, source_dash_id)
            if targettemplate['Template']['Version']['Status'] == "CREATION_SUCCESSFUL":
                break
        else:
            if targettemplate['Template']['Version']['Status'] == "CREATION_SUCCESSFUL":
                logger.info("Template is successfully copied!")
            else:
                qs_utils.delete_template(targetsession, source_dash_id)
                dashboard_failed.append(
                    {
                        "Error Type": "Copy Template Error",
                        "DashboardId": source_dash_id,
                        "Name": source_dash_name,
                        "Error": str(ex)
                    }
                )
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
                    ex = "Dataset "+i['Placeholder']+" is missing!"
                    dashboard_failed.append(
                        {
                            "Error Type": "Datasets in target env are missing for this dashboard",
                            "DashboardId": source_dash_id,
                            "Name": source_dash_name,
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

        dashboard = qs_utils.describe_dashboard(targetsession, source_dash_id)

        if 'Faild to describe dashboard:' in dashboard:
            if 'dashboard/'+source_dash_id+' is not found' in dashboard:
                logger.info("Create new dashboard: %s", source_dash_name)
                try:
                    newdashboard = qs_utils.create_dashboard(
                        targetsession, source_dash_id, source_dash_name,
                        targetadmin, source_entity, '1', filter='ENABLED',
                        csv='ENABLED', sheetcontrol='COLLAPSED'
                    )
                except Exception as ex:
                    qs_utils.delete_template(targetsession, source_dash_id)
                    dashboard_failed.append(
                        {
                            "Error Type": "Create New Dashboard Error",
                            "DashboardId": source_dash_id,
                            "Name": source_dash_name,
                            "Error": str(ex)
                        }
                    )
                    continue
            else:
                dashboard_failed.append(
                    {
                        "Error Type": "Describe Target Dashboard Error",
                        "DashboardId": source_dash_id,
                        "Name": source_dash_name,
                        "Error": str(dashboard)
                    }
                )
                continue
        elif dashboard['Dashboard']['Version']['Status'] == "CREATION_FAILED":
            res = qs_utils.delete_dashboard(targetsession, source_dash_id)
            try:
                newdashboard = qs_utils.create_dashboard(
                    targetsession, source_dash_id, source_dash_name,
                    targetadmin, source_entity, '1', filter='ENABLED',
                    csv='ENABLED', sheetcontrol='COLLAPSED'
                )
            except Exception as ex:
                qs_utils.delete_template(targetsession, source_dash_id)
                dashboard_failed.append(
                    {
                        "Error Type": "Create Dashboard Error",
                        "DashboardId": source_dash_id,
                        "Name": source_dash_name,
                        "Error": str(ex)
                    }
                )
                continue

        else:
            logger.info("Dashboard already exists, updating instead: %s", source_dash_name)
            try:
                newdashboard = qs_utils.update_dashboard(
                    targetsession, source_dash_id, source_dash_name,
                    source_entity, target['version'], filter='ENABLED',
                    csv='ENABLED', sheetcontrol='EXPANDED'
                )
            except Exception as ex:
                qs_utils.delete_template(targetsession, source_dash_id)
                dashboard_failed.append(
                    {
                        "Error Type": "Update Dashboard Error",
                        "DashboardId": source_dash_id,
                        "Name": source_dash_name,
                        "Error": str(ex)
                    }
                )
                continue

        res = qs_utils.describe_dashboard(targetsession, newdashboard['DashboardId'])

        if res['Status']==200:
            status = res['Dashboard']['Version']['Status']
            if status in ['CREATION_SUCCESSFUL', 'UPDATE_SUCCESSFUL']:
                dashboard_success.append(res['Dashboard'])
            else:
                dashboard_failed.append(
                    {
                        "Error Type": "Dashboard Creation Status is not Successful",
                        "Dashboard": res['Dashboard']
                    }
                )

    logger.info("Dashboard creation failed: %s", dashboard_failed)
    logger.info("Dashboard creation successes: %s", dashboard_success)
