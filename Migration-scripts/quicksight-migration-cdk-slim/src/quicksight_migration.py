import logging
import utils.quicksight_utils as qs_utils
import utils.aws_utils as aws_utils
import time

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

SSM_PARAMETER_NAME = "/infra/config"
S3_KEY = ""
S3_BUCKET_NAME = ""


def MigrateAssets(
    source_region,
    source_account_id,
    source_role_name,
    target_region,
    target_account_id,
    target_role_name,
    target_admin_users,
    target_admin_groups,
    migration_items,
) -> None:
    """Moves QuickSight assets from a source account to target account

    Args:
    source_region (str): source account region
    source_account_id (int): aws account number for QuickSight source account
    source_role_name (str): the name of the IAM role with access to resources
    target_region (str): target account region
    target_account_id (int): aws account number for QuickSight target account
    target_role_name (str): the name of the IAM role with access to resources
    target_admin_users (list): QuickSight UserNames to be granted admin permissions
    target_admin_groups (list): QuickSight Groups to be granted admin permissions
    migrate_items (dict): QuickSight assets to be migrated


    Returns:
        None
    """
    migration_start_time = time.time()
    # Source Account - Boto3 Session
    logger.info(
        "Creating source Boto3 session for source account {} using role {}".format(
            source_account_id, source_role_name
        )
    )
    source_session = aws_utils.aws_boto3(
        source_account_id, source_role_name, source_region
    ).session

    logger.info("Creating QuickSight client")
    source_acct = qs_utils.QuickSightAccount(source_session, source_region)
    source_acct_name = source_acct.name

    # Target Account
    logger.info(
        "Creating Boto3 session for target account {} using role {}".format(
            target_account_id, target_role_name
        )
    )
    target_session = aws_utils.aws_boto3(
        target_account_id, target_role_name, target_region
    ).session

    logger.info("Creating QuickSight client")
    target_acct = qs_utils.QuickSightAccount(target_session, target_region)
    target_acct_name = target_acct.name

    logger.info(
        "{} [{}:{}]: Retrieving account parameters".format(
            source_acct_name, source_region, source_account_id
        )
    )
    source_acct.config_parameters.add_parameter("namespace", "default")
    logger.debug(
        "{} [{}:{}]: Namespace: {}".format(
            source_acct_name,
            source_region,
            source_account_id,
            source_acct.config_parameters.parameters["namespace"],
        )
    )

    # Target Config
    # TODO: Need validation checks. Check what types of datasources are being
    # used and make sure that needed parameters have been stored
    # in parameter store.
    # ssm parameters
    logger.info(
        "{} [{}:{}]: Retrieving account parameters".format(
            target_acct_name, target_region, target_account_id
        )
    )
    infra_details = aws_utils.aws_boto3.get_ssm_parameters(
        target_session, SSM_PARAMETER_NAME
    )
    for key, value in infra_details.items():
        target_acct.config_parameters.add_parameter(key, value)

    # s3 bucket
    target_acct.config_parameters.add_parameter("s3_key", S3_KEY)
    target_acct.config_parameters.add_parameter("s3_bucket", S3_BUCKET_NAME)

    # resource taggings
    target_acct.config_parameters.add_parameter(
        "tag", [{"Key": "testmigration", "Value": "true"}]
    )

    # secrets
    # redshift password
    logger.info(
        "{} [{}:{}]: Getting account secrets".format(
            target_acct_name, target_region, target_account_id
        )
    )

    if infra_details.get("redshiftSecretId"):
        target_acct.config_parameters.add_parameter(
            "redshiftPassword",
            aws_utils.aws_boto3.get_secret(
                target_session, infra_details.get("redshiftSecretId")
            ),
        )
    # rds/other password
    if infra_details.get("rdsSecretId"):
        target_acct.config_parameters.add_parameter(
            "rdsPassword",
            aws_utils.aws_boto3.get_secret(
                target_session, infra_details.get("rdsSecretId")
            ),
        )
    logger.info("Retrieve Migration Assets".center(80, "="))

    logger.info(
        "{} [{}:{}]: Retrieving admin users(s) {}".format(
            target_acct_name,
            target_region,
            target_account_id,
            target_admin_users,
        )
    )

    if target_admin_users:
        # Store the target admin users in a class
        target_acct.add_admin_users(target_admin_users)
    # Manual Admin User Add
    # target_acct.add_admin_users(["quicksight-migration-user"])

    # Store the target admin groups in a class
    if any(x.strip() for x in target_admin_groups):
        target_acct.add_admin_groups(target_admin_groups)
        logger.info(
            "{} [{}:{}]: Retrieving admin group(s) {}".format(
                target_acct_name,
                target_region,
                target_account_id,
                target_admin_groups,
            )
        )

    # Retrieve source dashboards and store in a class
    logger.info(
        "{} [{}:{}]: Retrieving dashboard(s) {}".format(
            source_acct_name,
            source_region,
            source_account_id,
            migration_items["dashboards"],
        )
    )
    migrate_dashboard_ids = source_acct.get_dashboard_ids(migration_items["dashboards"])    
    source_acct.add_dashboards(migrate_dashboard_ids)

    # Retrieve source analyses and store in a class
    logger.info(
        "{} [{}:{}]: Retrieving analyses(s) {}".format(
            source_acct_name,
            source_region,
            source_account_id,
            migration_items["analyses"],
        )
    )
    migrate_analyses_ids = source_acct.get_analysis_ids(migration_items["analyses"])
    source_acct.add_analyses(migrate_analyses_ids)

    # Retrieve source themes and store in a class
    logger.info(
        "{} [{}:{}]: Retrieving themes(s) {}".format(
            source_acct_name,
            source_region,
            source_account_id,
            migration_items["themes"],
        )
    )
    migrate_theme_ids = source_acct.get_theme_ids(migration_items["themes"])
    source_acct.add_themes(migrate_theme_ids)

    # MIGRATE DATASOURCES
    logger.info("Migrating DataSources".center(80, "="))

    for key in source_acct.migrate_datasources:
        source_datasource = source_acct.migrate_datasources[key].response

        # check if datasource already exists
        data_source_exists = target_acct.DescribeDataSource(
            source_datasource["DataSourceId"]
        )

        # if the datasource is in deleted or creation_failed status delete it. this is usually due to API operations
        if data_source_exists and data_source_exists.get("Status") in (
            "CREATION_FAILED",
            "DELETED",
        ):
            target_acct.DeleteDataSource(data_source_exists["DataSourceId"])
            logger.info(
                "{} [{}:{}]: DataSource {} is in {} status. Deleting.".format(
                    target_acct_name,
                    target_region,
                    target_account_id,
                    source_datasource["Name"],
                    data_source_exists.get("Status"),
                )
            )
            data_source_exists = None

        if data_source_exists:
            logger.info(
                "{} [{}:{}]: DataSource {} already exists. Using existing.".format(
                    target_acct_name,
                    target_region,
                    target_account_id,
                    source_datasource["Name"],
                )
            )

            continue
        elif source_datasource["Type"] == "TIMESTREAM":
            logger.info(
                "{} [{}:{}]: DataSource {} is timestream. Skipping.".format(
                    target_acct_name,
                    target_region,
                    target_account_id,
                    source_datasource["Name"],
                )
            )
            continue
        else:
            # If the datasource doesn't exist create a new datasource in destination account
            try:
                new_datasource = target_acct.CreateDataSource(source_datasource)
                logger.info(
                    "{} [{}:{}]: Created Datasource {}. ExecTime: {}sec".format(
                        target_acct_name,
                        target_region,
                        target_account_id,
                        source_datasource["Name"],
                        round(new_datasource["timetocreate"], 2),
                    )
                )
                source_acct.migrate_datasources[key].status = "migrated"
            except Exception as ex:
                logger.info(
                    "{} [{}:{}]: Failed to create data source {} {}".format(
                        target_acct_name,
                        target_region,
                        target_account_id,
                        source_datasource["Name"],
                        ex,
                    )
                )
                source_acct.migrate_datasources[key].status = "failed"
                continue
  
    # MIGRATE DATASETS
    logger.info("Migrating DataSets".center(80, "="))

    for key in source_acct.migrate_datasets:

        source_dataset = source_acct.migrate_datasets[key].response

        # check if dataset already exists
        data_set_exists = target_acct.DescribeDataSet(source_dataset["DataSetId"])

        # if the dataset is in deleted or creation_failed status delete it. this is usually due to API operations
        if data_set_exists and data_set_exists.get("Status") in (
            "CREATION_FAILED",
            "DELETED",
        ):
            target_acct.DeleteDataSet(data_set_exists["DataSetId"])
            logger.info(
                "{} [{}:{}]: DataSet {} is in {} status. Deleting.".format(
                    target_acct_name,
                    target_region,
                    target_account_id,
                    source_dataset["Name"],
                    data_set_exists.get("Status"),
                )
            )
            data_set_exists = None

        if data_set_exists:
            try:
                new_dataset = target_acct.UpdateDataSet(source_dataset)
                logger.info(
                    "{} [{}:{}]: Updated DataSet {}. ExecTime {}sec".format(
                        target_acct_name,
                        target_region,
                        target_account_id,
                        source_dataset["Name"],
                        round(new_dataset["timetocreate"], 2),
                    )
                )
                source_acct.migrate_datasets[key].status = "migrated"
            except Exception as ex:
                logger.info(
                    "{} [{}:{}]: Failed to update DataSet {} {}".format(
                        target_acct_name,
                        target_region,
                        target_account_id,
                        source_dataset["Name"],
                        ex,
                    )
                )
                continue
        else:
            try:
                new_dataset = target_acct.CreateDataSet(source_dataset)
                logger.info(
                    "{} [{}:{}]: Created DataSet {}. ExecTime: {}sec".format(
                        target_acct_name,
                        target_region,
                        target_account_id,
                        source_dataset["Name"],
                        round(new_dataset["timetocreate"], 2),
                    )
                )
                source_acct.migrate_datasets[key].status = "migrated"
            except Exception as ex:
                logger.info(
                    "{} [{}:{}]: Failed to create DataSet {} {}".format(
                        target_acct_name,
                        target_region,
                        target_account_id,
                        source_dataset["Name"],
                        ex,
                    )
                )
                source_acct.migrate_datasets[key].status = "failed"
                continue

    # MIGRATE THEMES
    logger.info("Migrating Themes".center(80, "="))

    for key in source_acct.migrate_themes:
        source_theme = source_acct.migrate_themes[key].response
        # check if datasource already exists
        theme_exists = target_acct.DescribeTheme(source_theme["ThemeId"])

        # if the datasource is in deleted or creation_failed status delete it. this is usually due to API operations
        if theme_exists and theme_exists.get("Status") in (
            "CREATION_FAILED",
            "DELETED",
        ):
            target_acct.DeleteTheme(theme_exists["ThemeId"])
            logger.info(
                "{} [{}:{}]: Theme {} is in {} status. Deleting.".format(
                    target_acct_name,
                    target_region,
                    target_account_id,
                    source_theme["Name"],
                    theme_exists.get("Status"),
                )
            )
            theme_exists = None

        if theme_exists:
            logger.info(
                "{} [{}:{}]: Theme {} already exists. Using existing.".format(
                    target_acct_name,
                    target_region,
                    target_account_id,
                    source_theme["Name"],
                )
            )
        else:
            try:
                new_theme = target_acct.CreateTheme(source_theme)
                logger.info(
                    "{} [{}:{}]: Created Theme {}. ExecTime: {}sec".format(
                        target_acct_name,
                        target_region,
                        target_account_id,
                        source_theme["Name"],
                        round(new_theme["timetocreate"], 2),
                    )
                )
                source_acct.migrate_themes[key].status = "migrated"
            except Exception:
                source_acct.migrate_themes[key].status = "failed"
                continue
            try:
                target_acct.UpdateThemePermissions(source_theme["ThemeId"])
                logger.info(
                    "{} [{}:{}]: Updating theme permissions in target account {}".format(
                        target_acct_name,
                        target_region,
                        target_account_id,
                        target_acct.accountid,
                    )
                )
            except Exception as ex:
                logger.info(
                    "{} [{}:{}]: Failed to update theme permissions. Deleting theme {} {}".format(
                        target_acct_name,
                        target_region,
                        target_account_id,
                        source_theme["Name"],
                        ex,
                    )
                )
                target_acct.DeleteTheme(source_theme["ThemeId"])
                source_acct.migrate_themes[key].status = "failed"
                continue

    # MIGRATE ANALYSES
    logger.info("Migrating Analyses".center(80, "="))
    for key in source_acct.migrate_analyses:
        source_analysis = source_acct.migrate_analyses[key].response
        source_analysis_id = source_acct.migrate_analyses[key].id

        try:
            create_template_response = source_acct.CreateTemplate(
                source_type="analysis",
                source=source_analysis,
                source_datasets=source_acct.migrate_datasets,
            )
            logger.info(
                "{} [{}:{}]: Created template for {}. ExecTime: {}sec".format(
                    source_acct_name,
                    source_region,
                    source_account_id,
                    source_analysis["Name"],
                    round(create_template_response["timetocreate"], 2),
                )
            )
        except Exception as ex:
            logger.info(
                "{} [{}:{}]: Failed to create template for {} {}".format(
                    source_acct_name,
                    source_region,
                    source_account_id,
                    source_analysis["Name"],
                    ex,
                )
            )
            continue

        new_template = source_acct.DescribeTemplate(
            create_template_response["TemplateId"]
        )

        # grant target account permissions to the source account template
        try:
            source_acct.UpdateTemplatePermissions(
                create_template_response["TemplateId"], target_acct.accountid
            )
            logger.info(
                "{} [{}:{}]: Granted template permissions to account {}".format(
                    source_acct_name,
                    source_region,
                    source_account_id,
                    target_acct.accountid,
                )
            )
        except Exception as ex:
            logger.info(
                "{} [{}:{}]: Failed to grant permissions. Deleting template {} {}".format(
                    source_acct_name,
                    source_region,
                    source_account_id,
                    source_analysis["Name"],
                    ex,
                )
            )
            source_acct.DeleteTemplate(create_template_response["TemplateId"])
            continue

        # TODO: needs error handling this checks if datasets needed for analyis exist in target
        # if target_acct.CheckAnalysisDependencies(source_analysis):
        #     pass
        # else:
        #     pass

        # Check if analysis already exists in target. Update if exists.
        analysis_exists = target_acct.DescribeAnalysis(source_analysis["AnalysisId"])

        if analysis_exists and analysis_exists.get("Status") in (
            "CREATION_FAILED",
            "DELETED",
        ):
            target_acct.DeleteAnalysis(analysis_exists["AnalysisId"])
            logger.info(
                "{} [{}:{}]: Analysis {} is in {} status. Deleting.".format(
                    target_acct_name,
                    target_region,
                    target_account_id,
                    source_analysis["Name"],
                    analysis_exists.get("Status"),
                )
            )
            analysis_exists = None

        if analysis_exists:
            try:
                new_analysis = target_acct.UpdateAnalysis(
                    new_template, source_analysis, source_acct.migrate_datasets
                )
                logger.info(
                    "{} [{}:{}]: Analysis {} already exists updating. ExecTime: {}sec".format(
                        target_acct_name,
                        target_region,
                        target_account_id,
                        source_analysis["Name"],
                        round(new_analysis["timetocreate"], 2),
                    )
                )
                source_acct.migrate_analyses[key].status = "migrated"

            except Exception as ex:
                logger.info(
                    "{} [{}:{}]: Failed to update analysis {} {}".format(
                        target_acct_name,
                        target_region,
                        target_account_id,
                        source_analysis["Name"],
                        ex,
                    )
                )

        else:
            try:
                new_analysis = target_acct.CreateAnalysis(
                    new_template, source_analysis, source_acct.migrate_datasets
                )
                logger.info(
                    "{} [{}:{}]: Created analysis {}. ExecTime: {}sec".format(
                        target_acct_name,
                        target_region,
                        target_account_id,
                        source_analysis["Name"],
                        round(new_analysis["timetocreate"], 2),
                    )
                )
                source_acct.migrate_analyses[key].status = "migrated"
            except Exception as ex:
                logger.info(
                    "{} [{}:{}]: Failed to create analysis {} {}".format(
                        target_acct_name,
                        target_region,
                        target_account_id,
                        source_analysis["Name"],
                        ex,
                    )
                )

                source_acct.DeleteTemplate(source_analysis_id)
                continue

    # MIGRATE DASHBOARDS
    logger.info("Migrating Dashboards".center(80, "="))

    for key in source_acct.migrate_dashboards:
        source_dashboard = source_acct.migrate_dashboards[key].response

        source_dashboard_analysis = source_acct.DescribeAnalysis(
            source_dashboard["Version"]["SourceEntityArn"]
        )
        source_analysis_id = source_dashboard_analysis["AnalysisId"]

        try:
            create_template_response = source_acct.CreateTemplate(
                source_type="analysis",
                source=source_dashboard_analysis,
                source_datasets=source_acct.migrate_datasets,
            )
            logger.info(
                "{} [{}:{}]: Created template for {}".format(
                    source_acct_name,
                    source_region,
                    source_account_id,
                    source_dashboard_analysis["Name"],
                )
            )
        except Exception as ex:
            logger.info(
                "{} [{}:{}]: Failed to create template for {} {}".format(
                    source_acct_name,
                    source_region,
                    source_account_id,
                    source_dashboard_analysis["Name"],
                    str(ex),
                )
            )
            continue

        new_template = source_acct.DescribeTemplate(
            create_template_response["TemplateId"]
        )

        # grant target account permissions to the source account template
        try:
            logger.info(
                "{} [{}:{}]: Granting template permissions to account {}".format(
                    source_acct_name,
                    source_region,
                    source_account_id,
                    target_acct.accountid,
                )
            )

            source_acct.UpdateTemplatePermissions(
                source_analysis_id, target_acct.accountid
            )

        except Exception:
            logger.info(
                "{} [{}:{}]: Deleting template for dashboard {}".format(
                    source_acct_name,
                    source_region,
                    source_account_id,
                    source_dashboard_analysis["Name"],
                )
            )
            source_acct.DeleteTemplate(source_dashboard_analysis["AnalysisId"])
            continue

        # Create template on target account using source account template arn
        try:
            new_template_response = target_acct.CreateTemplate(
                source_type="template", source=new_template
            )
            logger.info(
                "{} [{}:{}]: Copied template from source account {} {}sec".format(
                    target_acct_name,
                    target_region,
                    target_account_id,
                    source_acct.accountid,
                    round(new_template_response["timetocreate"], 2),
                )
            )
        except Exception as err:
            # Copy template error
            source_acct.DeleteTemplate(source_analysis_id)
            logger.info(
                "{} [{}:{}]: Failed to copy template from source account {} {}".format(
                    target_acct_name,
                    target_region,
                    target_account_id,
                    source_acct.accountid,
                    err,
                )
            )
            continue

        target_template = target_acct.DescribeTemplate(
            new_template_response["TemplateId"]
        )

        # check if dashboard already exists.
        dashboard_exists = target_acct.DescribeDashboard(
            source_dashboard["DashboardId"]
        )

        # if the dashboard is in deleted or creation_failed status delete it. this is usually due to API operations
        if dashboard_exists:
            if dashboard_exists and dashboard_exists.get("Status") in (
                "CREATION_FAILED",
                "DELETED",
            ):
                target_acct.DeleteDashboard(dashboard_exists["DashboardId"])
                logger.info(
                    "{} [{}:{}]: Dashboard {} is in {} status. Deleting.".format(
                        target_acct_name,
                        target_region,
                        target_account_id,
                        source_dashboard["Name"],
                        dashboard_exists.get("Status"),
                    )
                )
                dashboard_exists = None
            try:
                new_dashboard = target_acct.UpdateDashboard(
                    target_template,
                    source_dashboard,
                    source_acct.migrate_datasets,
                )
                target_acct.UpdateDashboardVersion(new_dashboard)
                logger.info(
                    "{} [{}:{}]: Dashboard {} already exists updating. New Version Number: {} ExecTime: {}sec".format(
                        target_acct_name,
                        target_region,
                        target_account_id,
                        source_dashboard["Name"],
                        new_dashboard["VersionArn"].split("version/")[1],
                        round(new_dashboard["timetocreate"], 2),
                    )
                )
                source_acct.migrate_dashboards[key].status = "migrated"

            except Exception as ex:
                logger.info(
                    "{} [{}:{}]: Failed to update dashboard {} {}".format(
                        target_acct_name,
                        target_region,
                        target_account_id,
                        source_dashboard["Name"],
                        ex,
                    )
                )
        else:
            # Create Dashboard on target
            try:
                target_acct.CreateDashboard(
                    target_template,
                    source_dashboard,
                    source_acct.migrate_datasets,
                )
                logger.info(
                    "{} [{}:{}]: Created new dashboard {}. ExecTime: {}sec".format(
                        target_acct_name,
                        target_region,
                        target_account_id,
                        source_dashboard["Name"],
                        round(new_analysis["timetocreate"], 2),
                    )
                )

                source_acct.migrate_dashboards[key].status = "migrated"
            except Exception as ex:
                source_acct.DeleteTemplate(source_analysis_id)
                logger.error("create new dashboard error {}".format(ex))
                source_acct.migrate_dashboards[key].status = "failed"
                continue

    logger.info("Migration Summary".center(80, "="))

    # Results
    dashboard_success = list(
        x.name
        for x in source_acct.migrate_dashboards.values()
        if x.status == "migrated"
    )
    dashboard_failed = list(
        x.name for x in source_acct.migrate_dashboards.values() if x.status == "failed"
    )
    dataset_success = list(
        x.name for x in source_acct.migrate_datasets.values() if x.status == "migrated"
    )
    dataset_failed = list(
        x.name for x in source_acct.migrate_datasets.values() if x.status == "failed"
    )
    analyses_success = list(
        x.name for x in source_acct.migrate_analyses.values() if x.status == "migrated"
    )
    analyses_failed = list(
        x.name for x in source_acct.migrate_analyses.values() if x.status == "failed"
    )
    theme_success = list(
        x.name for x in source_acct.migrate_themes.values() if x.status == "migrated"
    )
    theme_failed = list(
        x.name for x in source_acct.migrate_themes.values() if x.status == "failed"
    )
    datasource_success = list(
        x.name
        for x in source_acct.migrate_datasources.values()
        if x.status in ("skipped", "migrated")
    )
    datasource_failed = list(
        x.name
        for x in source_acct.migrate_datasources.values()
        if x.status in ("failed")
    )
    migration_stop_time = time.time()
    migration_time = migration_stop_time - migration_start_time
    # Log Results
    logger.info("Total Migration Time: {}sec".format(round(migration_time, 2)))
    logger.info("Themes(s) Created: {}".format(theme_success))
    logger.info("Themes(s) Failed: {}".format(theme_failed))
    logger.info("Dashboard(s) Created: {}".format(dashboard_success))
    logger.info("Dashboard(s) Failed: {}".format(dashboard_failed))
    logger.info("Analyses Created: {}".format(analyses_success))
    logger.info("Analyses Failed: {}".format(analyses_failed))
    logger.info("DataSet Created: {}".format(dataset_success))
    logger.info("DataSet Failed: {}".format(dataset_failed))
    logger.info("DataSource(s) Created: {}".format(datasource_success))
    logger.info("DataSource(s) Failed: {}".format(datasource_failed))
