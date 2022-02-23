from botocore.exceptions import ClientError
from common.constants import custom_config
import logging
import abc
import time
import common.constants as const
import utils.utils as utils


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class QuickSightAPI:
    def execute(self, api_method):
        self.api_method = api_method
        self.session = api_method.session
        self.qs_client = self.session.client("quicksight", config=custom_config)
        self.params = api_method.get_params()
        self.describe_action = self.__get_describe_action()
        self.describe_params = self.__get_describe_params()
        results = self.__call_api(self.params)

        return api_method.parse_response(results)

    def get_response_status(self, response):
        if self.api_method.action in ("create_template", "update_template"):
            describe_object = response.get("Template")
            describe_version = describe_object.get("Version")
            describe_status = describe_version.get("Status")
        elif self.api_method.action in ("create_dashboard", "update_dashboard"):
            describe_object = response.get("Dashboard")
            describe_version = describe_object.get("Version")
            describe_status = describe_version.get("Status")
        elif self.api_method.action in ("create_analysis", "update_analysis"):
            describe_object = response.get("Analysis")
            describe_status = describe_object.get("Status")
        elif self.api_method.action in ("create_data_source", "update_data_source"):
            describe_object = response.get("DataSource")
            describe_status = describe_object.get("Status")
        elif self.api_method.action in ("create_data_set", "update_data_set"):
            describe_object = response.get("DataSet")
            describe_status = describe_object.get("Status")

        return describe_status

    def __get_describe_action(self):
        describe_object = self.api_method.action.split("_", 1)[1]
        describe_action = "describe_" + describe_object
        return describe_action

    def __get_describe_params(self):
        describe_params = {}
        describe_params["AwsAccountId"] = self.params["AwsAccountId"]
        if self.describe_action == "describe_template":
            describe_params["TemplateId"] = self.params["TemplateId"]
        elif self.describe_action == "describe_dashboard":
            describe_params["DashboardId"] = self.params["DashboardId"]
        elif self.describe_action == "describe_analysis":
            describe_params["AnalysisId"] = self.params["AnalysisId"]
        elif self.describe_action == "describe_data_set":
            describe_params["DataSetId"] = self.params["DataSetId"]
        elif self.describe_action == "describe_data_source":
            describe_params["DataSourceId"] = self.params["DataSourceId"]
        return describe_params

    def __call_api(self, params):
        response = {}
        results = {}
        api_start_time = time.time()
        try:
            response = getattr(self.qs_client, self.api_method.action)(**params)
            results = response

            while "NextToken" in response:
                params["NextToken"] = response["NextToken"]
                response = getattr(self.qs_client, self.api_method.action)(**params)
                results.extend(response)

            # check if action is create or update
            if any(action in self.api_method.action for action in ["create", "update"]):
                if not any(
                    action in self.api_method.action for action in ["permissions"]
                ):
                    response = getattr(self.qs_client, self.describe_action)(
                        **self.describe_params
                    )
                    response_status = self.get_response_status(response)

                    try:
                        timeout = time.time() + 120  # 2 minutes

                        while response_status in (
                            "CREATION_IN_PROGRESS",
                            "UPDATE_IN_PROGRESS",
                        ):
                            response = getattr(self.qs_client, self.describe_action)(
                                **self.describe_params
                            )
                            response_status = self.get_response_status(response)

                            if response_status in (
                                "CREATION_SUCCESSFUL",
                                "UPDATE_SUCCESSFUL",
                            ):
                                break
                            elif time.time() > timeout:
                                raise TimeoutError
                            time.sleep(5)

                    except TimeoutError:
                        logger.error("{} Timed out ".format(self.api_method.action))
                    timetocreate = time.time() - api_start_time
                    results["timetocreate"] = timetocreate

            return results

        except ClientError as err:
            logger.debug(str(err))


class QuickSightAPI_BaseMethod(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def get_params(self):
        pass

    @abc.abstractmethod
    def parse_response(self):
        pass


class ListDashboardsApiMethod(QuickSightAPI_BaseMethod):
    def __init__(self, session):
        self.action = "list_dashboards"
        self.session = session
        self.accountid = session.accountid

    def get_params(self):
        return {"AwsAccountId": self.accountid}

    def parse_response(self, response):
        return response["DashboardSummaryList"]


class ListDataSetsApiMethod(QuickSightAPI_BaseMethod):
    def __init__(self, session):
        self.action = "list_data_sets"
        self.session = session
        self.accountid = session.accountid

    def get_params(self):
        return {"AwsAccountId": self.accountid}

    def parse_response(self, response):
        return response["DataSetSummaries"]


class ListAnalysesApiMethod(QuickSightAPI_BaseMethod):
    def __init__(self, session):
        self.action = "list_analyses"
        self.session = session
        self.accountid = session.accountid

    def get_params(self):
        return {"AwsAccountId": self.accountid}

    def parse_response(self, response):
        return response["AnalysisSummaryList"]


class ListDataSourcesApiMethod(QuickSightAPI_BaseMethod):
    def __init__(self, session):
        self.action = "list_data_sources"
        self.session = session
        self.accountid = session.accountid

    def get_params(self):
        return {"AwsAccountId": self.accountid}

    def parse_response(self, response):
        return response["DataSources"]


class ListThemesApiMethod(QuickSightAPI_BaseMethod):
    def __init__(self, session):
        self.action = "list_themes"
        self.session = session
        self.accountid = session.accountid

    def get_params(self):
        return {"AwsAccountId": self.accountid}

    def parse_response(self, response):
        return response["ThemeSummaryList"]


class ListTemplatesApiMethod(QuickSightAPI_BaseMethod):
    def __init__(self, session):
        self.action = "list_templates"
        self.session = session
        self.accountid = session.accountid

    def get_params(self):
        return {"AwsAccountId": self.accountid, "MaxResults": 100}

    def parse_response(self, response):
        return response["TemplateSummaryList"]


class DescribeDashboardApiMethod(QuickSightAPI_BaseMethod):
    def __init__(self, session, id):
        self.action = "describe_dashboard"
        self.session = session
        self.accountid = session.accountid
        self.id = id

    def get_params(self):
        return {"AwsAccountId": self.accountid, "DashboardId": self.id}

    def parse_response(self, response):
        if response:
            if response["Status"] == 200:
                return response["Dashboard"]


class DescribeDataSetApiMethod(QuickSightAPI_BaseMethod):
    def __init__(self, session, id):
        self.action = "describe_data_set"
        self.session = session
        self.accountid = session.accountid
        self.id = id

    def get_params(self):
        return {"AwsAccountId": self.accountid, "DataSetId": self.id}

    def parse_response(self, response):
        if response:
            if response["Status"] == 200:
                return response


class DescribeAnalysisApiMethod(QuickSightAPI_BaseMethod):
    def __init__(self, session, id):
        self.action = "describe_analysis"
        self.session = session
        self.accountid = session.accountid
        self.id = id

    def get_params(self):
        return {"AwsAccountId": self.accountid, "AnalysisId": self.id}

    def parse_response(self, response):
        if response:
            if response["Status"] == 200:
                return response["Analysis"]


class DescribeDataSourceApiMethod(QuickSightAPI_BaseMethod):
    def __init__(self, session, id):
        self.action = "describe_data_source"
        self.session = session
        self.accountid = session.accountid
        self.id = id

    def get_params(self):
        return {"AwsAccountId": self.accountid, "DataSourceId": self.id}

    def parse_response(self, response):
        if response:
            if response["Status"] == 200:
                return response["DataSource"]


class DescribeThemeApiMethod(QuickSightAPI_BaseMethod):
    def __init__(self, session, id):
        self.action = "describe_theme"
        self.session = session
        self.accountid = session.accountid
        self.id = id

    def get_params(self):
        return {"AwsAccountId": self.accountid, "ThemeId": self.id}

    def parse_response(self, response):
        if response:
            if response["Status"] == 200:
                return response


class DescribeTemplateApiMethod(QuickSightAPI_BaseMethod):
    def __init__(self, session, id):
        self.action = "describe_template"
        self.session = session
        self.accountid = session.accountid
        self.id = id

    def get_params(self):
        return {"AwsAccountId": self.accountid, "TemplateId": self.id}

    def parse_response(self, response):
        if response:
            if response["Status"] == 200:
                return response


class DescribeAccountApiMethod(QuickSightAPI_BaseMethod):
    def __init__(self, session):
        self.action = "describe_account_settings"
        self.session = session
        self.accountid = session.accountid

    def get_params(self):
        return {"AwsAccountId": self.accountid}

    def parse_response(self, response):
        if response:
            if response["Status"] == 200:
                return response


class DescribeTemplatePermissionsApiMethod(QuickSightAPI_BaseMethod):
    def __init__(self, session, id):
        self.action = "describe_template_permissions"
        self.session = session
        self.accountid = session.accountid
        self.id = id

    def get_params(self):
        return {"AwsAccountId": self.accountid, "TemplateId": self.id}

    def parse_response(self, response):
        return response


class DescribeAnalysisPermissionsApiMethod(QuickSightAPI_BaseMethod):
    def __init__(self, session, id):
        self.action = "describe_analysis_permissions"
        self.session = session
        self.accountid = session.accountid
        self.id = id

    def get_params(self):
        return {"AwsAccountId": self.accountid, "AnalysisId": self.id}

    def parse_response(self, response):
        return response


class UpdateAnalysisPermissionsApiMethod(QuickSightAPI_BaseMethod):
    def __init__(self, session, id, grant_permissions):
        self.action = "update_analysis_permissions"
        self.session = session
        self.accountid = session.accountid
        self.id = id
        self.grant_permissions = grant_permissions

    def get_params(self):
        return {
            "AwsAccountId": self.accountid,
            "AnalysisId": self.id,
            "GrantPermissions": self.grant_permissions,
        }

    def parse_response(self, response):
        return response


class UpdateDashboardPermissionsApiMethod(QuickSightAPI_BaseMethod):
    def __init__(self, session, id, grant_permissions):
        self.action = "update_dashboard_permissions"
        self.session = session
        self.accountid = session.accountid
        self.id = id
        self.grant_permissions = grant_permissions

    def get_params(self):
        return {
            "AwsAccountId": self.accountid,
            "DashboardId": self.id,
            "GrantPermissions": self.grant_permissions,
        }

    def parse_response(self, response):
        return response


class UpdateDataSetPermissionsApiMethod(QuickSightAPI_BaseMethod):
    def __init__(self, session, id, grant_permissions):
        self.action = "update_data_set_permissions"
        self.session = session
        self.accountid = session.accountid
        self.id = id
        self.grant_permissions = grant_permissions

    def get_params(self):
        return {
            "AwsAccountId": self.accountid,
            "DataSetId": self.id,
            "GrantPermissions": self.grant_permissions,
        }

    def parse_response(self, response):
        return response


class UpdateDataSourcePermissionsApiMethod(QuickSightAPI_BaseMethod):
    def __init__(self, session, id, grant_permissions):
        self.action = "update_data_source_permissions"
        self.session = session
        self.accountid = session.accountid
        self.id = id
        self.grant_permissions = grant_permissions

    def get_params(self):
        return {
            "AwsAccountId": self.accountid,
            "DataSourceId": self.id,
            "GrantPermissions": self.grant_permissions,
        }

    def parse_response(self, response):
        return response


class UpdateThemePermissionsApiMethod(QuickSightAPI_BaseMethod):
    def __init__(self, session, id, grant_permissions):
        self.action = "update_theme_permissions"
        self.session = session
        self.accountid = session.accountid
        self.id = id
        self.grant_permissions = grant_permissions

    def get_params(self):
        return {
            "AwsAccountId": self.accountid,
            "ThemeId": self.id,
            "GrantPermissions": self.grant_permissions,
        }

    def parse_response(self, response):
        return response


class UpdateTemplatePermissionsApiMethod(QuickSightAPI_BaseMethod):
    def __init__(self, session, templateid, target_accountid):
        self.action = "update_template_permissions"
        self.session = session
        self.accountid = session.accountid
        self.templateid = templateid
        self.target_accountid = target_accountid
        self.principal = f"arn:aws:iam::{target_accountid}:root"
        self.grant_permissions = [
            {
                "Principal": self.principal,
                "Actions": ["quicksight:DescribeTemplate"],
            }
        ]

    def get_params(self):
        return {
            "AwsAccountId": self.accountid,
            "TemplateId": self.templateid,
            "GrantPermissions": self.grant_permissions,
        }

    def parse_response(self, response):
        return response


class DescribeUserApiMethod(QuickSightAPI_BaseMethod):
    def __init__(self, session, name, namespace):
        self.action = "describe_user"
        self.session = session
        self.accountid = session.accountid
        self.name = name
        self.namespace = namespace

    def get_params(self):
        return {
            "AwsAccountId": self.accountid,
            "UserName": self.name,
            "Namespace": self.namespace,
        }

    def parse_response(self, response):
        return response


class DescribeGroupApiMethod(QuickSightAPI_BaseMethod):
    def __init__(self, session, name, namespace):
        self.action = "describe_group"
        self.session = session
        self.accountid = session.accountid
        self.name = name
        self.namespace = namespace

    def get_params(self):
        return {
            "AwsAccountId": self.accountid,
            "GroupName": self.name,
            "Namespace": self.namespace,
        }

    def parse_response(self, response):
        return response


class DeleteDashboardApiMethod(QuickSightAPI_BaseMethod):
    def __init__(self, session, id):
        self.action = "delete_dashboard"
        self.session = session
        self.accountid = session.accountid
        self.id = id

    def get_params(self):
        return {"AwsAccountId": self.accountid, "DashboardId": self.id}

    def parse_response(self, response):
        return response


class DeleteDataSetApiMethod(QuickSightAPI_BaseMethod):
    def __init__(self, session, id):
        self.action = "delete_data_set"
        self.session = session
        self.accountid = session.accountid
        self.id = id

    def get_params(self):
        return {"AwsAccountId": self.accountid, "DataSetId": self.id}

    def parse_response(self, response):
        return response


class DeleteAnalysisApiMethod(QuickSightAPI_BaseMethod):
    def __init__(self, session, id):
        self.action = "delete_analysis"
        self.session = session
        self.accountid = session.accountid
        self.id = id

    def get_params(self):
        return {"AwsAccountId": self.accountid, "AnalysisId": self.id}

    def parse_response(self, response):
        return response


class DeleteDataSourceApiMethod(QuickSightAPI_BaseMethod):
    def __init__(self, session, id):
        self.action = "delete_data_source"
        self.session = session
        self.accountid = session.accountid
        self.id = id

    def get_params(self):
        return {"AwsAccountId": self.accountid, "DataSourceId": self.id}

    def parse_response(self, response):
        return response


class DeleteThemeApiMethod(QuickSightAPI_BaseMethod):
    def __init__(self, session, id):
        self.action = "delete_theme"
        self.session = session
        self.accountid = session.accountid
        self.id = id

    def get_params(self):
        return {"AwsAccountId": self.accountid, "ThemeId": self.id}

    def parse_response(self, response):
        return response


class DeleteTemplateApiMethod(QuickSightAPI_BaseMethod):
    def __init__(self, session, id):
        self.action = "delete_template"
        self.session = session
        self.accountid = session.accountid
        self.id = id

    def get_params(self):
        return {"AwsAccountId": self.accountid, "TemplateId": self.id}

    def parse_response(self, response):
        return response


class CreateThemeApiMethod(QuickSightAPI_BaseMethod):
    def __init__(self, session, id, name, basethemeid, configuation):
        self.action = "create_theme"
        self.session = session
        self.accountid = session.accountid
        self.id = id
        self.name = name
        self.basethemeid = basethemeid
        self.configuation = configuation

    def get_params(self):
        return {
            "AwsAccountId": self.accountid,
            "ThemeId": self.id,
            "Name": self.name,
            "BaseThemeId": self.basethemeid,
            "Configuration": self.configuation,
        }

    def parse_response(self, response):
        return response


class CreateTemplateApiMethod(QuickSightAPI_BaseMethod):
    def __init__(self, session, id, name, source_entity, version):
        self.action = "create_template"
        self.session = session
        self.accountid = session.accountid
        self.id = id
        self.name = name
        self.source_entity = source_entity
        self.version = version

    def get_params(self):
        return {
            "AwsAccountId": self.accountid,
            "TemplateId": self.id,
            "Name": self.name,
            "SourceEntity": self.source_entity,
            "VersionDescription": self.version,
        }

    def parse_response(self, response):
        return response


class CreateDashboardApiMethod(QuickSightAPI_BaseMethod):
    def __init__(self, session, params):
        self.action = "create_dashboard"
        self.session = session
        self.params = params

    def get_params(self):
        return self.params

    def parse_response(self, response):
        return response


class CreateAnalysisApiMethod(QuickSightAPI_BaseMethod):
    def __init__(self, session, params):
        self.action = "create_analysis"
        self.session = session
        self.params = params

    def get_params(self):
        return self.params

    def parse_response(self, response):
        return response


class CreateDataSourceApiMethod(QuickSightAPI_BaseMethod):
    def __init__(self, session, params):
        self.action = "create_data_source"
        self.session = session
        self.params = params

    def get_params(self):
        return self.params

    def parse_response(self, response):
        return response


class CreateDataSetApiMethod(QuickSightAPI_BaseMethod):
    def __init__(self, session, params):
        self.action = "create_data_set"
        self.session = session
        self.params = params

    def get_params(self):
        return self.params

    def parse_response(self, response):
        return response


class UpdateDataSetApiMethod(QuickSightAPI_BaseMethod):
    def __init__(self, session, params):
        self.action = "update_data_set"
        self.session = session
        self.params = params

    def get_params(self):
        return self.params

    def parse_response(self, response):
        return response


class UpdateAnalysisApiMethod(QuickSightAPI_BaseMethod):
    def __init__(self, session, params):
        self.action = "update_analysis"
        self.session = session
        self.params = params

    def get_params(self):
        return self.params

    def parse_response(self, response):
        return response


class QuickSightAccount(object):
    def __init__(self, session, region):
        self.session = session        
        self.qs_client = session.client("quicksight", config=custom_config)
        self.accountid = session.client("sts", config=custom_config).get_caller_identity()["Account"]
        setattr(self.session, "accountid", self.accountid)
        self.name = self.DescribeAccount()["AccountSettings"]["AccountName"]
        self.default_namespace = self.DescribeAccount()["AccountSettings"][
            "DefaultNamespace"
        ]

        self.region = region
        self.config_parameters = QuickSightConfig(self.accountid, self.region)
        self.migrate_dashboards = {}
        self.migrate_analyses = {}
        self.migrate_datasets = {}
        self.migrate_datasources = {}
        self.migrate_themes = {}
        self.migrate_admin_users = {}
        self.migrate_admin_groups = {}        
    

    def ListDashboards(self):
        api_method = ListDashboardsApiMethod(self.session)
        response = QuickSightAPI().execute(api_method)
        return response

    def ListDataSets(self):
        api_method = ListDataSetsApiMethod(self.session)
        response = QuickSightAPI().execute(api_method)
        return response

    def ListAnalyses(self):
        api_method = ListAnalysesApiMethod(self.session)
        response = QuickSightAPI().execute(api_method)
        return response

    def ListDataSources(self):
        api_method = ListDataSourcesApiMethod(self.session)
        response = QuickSightAPI().execute(api_method)
        return response

    def ListThemes(self):
        api_method = ListThemesApiMethod(self.session)
        response = QuickSightAPI().execute(api_method)
        return response

    def ListTemplates(self):
        api_method = ListTemplatesApiMethod(self.session)
        response = QuickSightAPI().execute(api_method)
        return response

    def DescribeDashboard(self, id):
        api_method = DescribeDashboardApiMethod(self.session, id)
        response = QuickSightAPI().execute(api_method)
        return response

    def DescribeDataSet(self, id):
        api_method = DescribeDataSetApiMethod(self.session, id)
        response = QuickSightAPI().execute(api_method)
        return response

    def DescribeAnalysis(self, id):
        id = id.split("/")[1] if "arn:" in id else id
        api_method = DescribeAnalysisApiMethod(self.session, id)
        response = QuickSightAPI().execute(api_method)
        return response

    def DescribeDataSource(self, id):
        api_method = DescribeDataSourceApiMethod(self.session, id)
        response = QuickSightAPI().execute(api_method)
        return response

    def DescribeTheme(self, id):
        api_method = DescribeThemeApiMethod(self.session, id)
        response = QuickSightAPI().execute(api_method)
        return response

    def DescribeTemplate(self, id):
        api_method = DescribeTemplateApiMethod(self.session, id)
        response = QuickSightAPI().execute(api_method)
        return response

    def DescribeAccount(self):
        api_method = DescribeAccountApiMethod(self.session)
        response = QuickSightAPI().execute(api_method)
        return response

    def DescribeTemplatePermissions(self, id):
        api_method = DescribeTemplatePermissionsApiMethod(self.session, id)
        response = QuickSightAPI().execute(api_method)
        return response

    def DescribeAnalysisPermissions(self, id):
        api_method = DescribeAnalysisPermissionsApiMethod(self.session, id)
        response = QuickSightAPI().execute(api_method)
        return response

    def DescribeUser(self, name):
        api_method = DescribeUserApiMethod(
            self.session, name, self.config_parameters.parameters["namespace"]
        )
        response = QuickSightAPI().execute(api_method)
        return response

    def DescribeGroup(self, name):
        api_method = DescribeGroupApiMethod(
            self.session, name, self.config_parameters.parameters["namespace"]
        )
        response = QuickSightAPI().execute(api_method)
        return response

    def DeleteDashboard(self, id):
        api_method = DeleteDashboardApiMethod(self.session, id)
        response = QuickSightAPI().execute(api_method)
        return response

    def DeleteDataSet(self, id):
        api_method = DeleteDataSetApiMethod(self.session, id)
        response = QuickSightAPI().execute(api_method)
        return response

    def DeleteAnalysis(self, id):
        api_method = DeleteAnalysisApiMethod(self.session, id)
        response = QuickSightAPI().execute(api_method)
        return response

    def DeleteDataSource(self, id):
        api_method = DeleteDataSourceApiMethod(self.session, id)
        response = QuickSightAPI().execute(api_method)
        return response

    def DeleteTheme(self, id):
        api_method = DeleteThemeApiMethod(self.session, id)
        response = QuickSightAPI().execute(api_method)
        return response

    def DeleteTemplate(self, id):
        api_method = DeleteTemplateApiMethod(self.session, id)
        response = QuickSightAPI().execute(api_method)
        return response

    def CreateTheme(self, source_theme):
        api_method = CreateThemeApiMethod(
            self.session,
            source_theme["Theme"]["ThemeId"],
            source_theme["Theme"]["Name"],
            source_theme["Theme"]["Version"]["BaseThemeId"],
            source_theme["Theme"]["Version"]["Configuration"],
        )
        response = QuickSightAPI().execute(api_method)
        return response

    def CreateTemplate(self, source_type, source, source_datasets=None):

        if source_type == "template":
            template_id = source.get("Template").get("TemplateId")
            template_name = source.get("Template").get("Name")
            source_entity = {
                "SourceTemplate": {"Arn": source.get("Template").get("Arn")}
            }
        else:
            template_id = source.get("AnalysisId")
            template_name = source.get("Name")
            source_datasets_arns = source["DataSetArns"]
            source_dataset_refs = []
            for source_dataset_arn in source_datasets_arns:
                source_dataset_id = source_dataset_arn.split("/")[1]
                source_dataset_name = source_datasets[source_dataset_id].name
                source_dataset_arn = f"arn:aws:quicksight:{self.region}:{self.accountid}:dataset/{source_dataset_id}"
                source_dataset_refs.append(
                    {
                        "DataSetPlaceholder": source_dataset_name,
                        "DataSetArn": source_dataset_arn,
                    }
                )
            source_entity = {
                "SourceAnalysis": {
                    "DataSetReferences": source_dataset_refs,
                    "Arn": source["Arn"],
                }
            }

        version = "1"
        existing_template = self.DescribeTemplate(template_id)
        if existing_template:
            self.DeleteTemplate(template_id)

        api_method = CreateTemplateApiMethod(
            self.session,
            template_id,
            template_name,
            source_entity,
            version,
        )

        try:
            response = QuickSightAPI().execute(api_method)

        except ClientError as exc:
            logger.error("Failed to create template %s error: %s", template_name, exc)
            logger.error(exc.response["Error"]["Message"])

        return response

    def UpdateAnalysisPermissions(self, id):
        permissions_users = [
            self.migrate_admin_users[key].permissions_dashboard
            for key in self.migrate_admin_users
        ]

        permissions_group = [
            self.migrate_admin_groups[key].permissions_dashboard
            for key in self.migrate_admin_groups
        ]

        permissions = permissions_users + permissions_group

        api_method = UpdateAnalysisPermissionsApiMethod(self.session, id, permissions)
        response = QuickSightAPI().execute(api_method)
        return response

    def UpdateDashboardPermissions(self, id):
        permissions_users = [
            self.migrate_admin_users[key].permissions_dashboard
            for key in self.migrate_admin_users
        ]

        permissions_group = [
            self.migrate_admin_groups[key].permissions_dashboard
            for key in self.migrate_admin_groups
        ]

        permissions = permissions_users + permissions_group

        api_method = UpdateDashboardPermissionsApiMethod(self.session, id, permissions)
        response = QuickSightAPI().execute(api_method)
        return response

    def UpdateDataSetPermissions(self, id):
        permissions_users = [
            self.migrate_admin_users[key].permissions_dashboard
            for key in self.migrate_admin_users
        ]

        permissions_group = [
            self.migrate_admin_groups[key].permissions_dashboard
            for key in self.migrate_admin_groups
        ]

        permissions = permissions_users + permissions_group

        api_method = UpdateDataSetPermissionsApiMethod(self.session, id, permissions)
        response = QuickSightAPI().execute(api_method)
        return response

    def UpdateDataSourcePermissions(self, id):
        permissions_users = [
            self.migrate_admin_users[key].permissions_dashboard
            for key in self.migrate_admin_users
        ]

        permissions_group = [
            self.migrate_admin_groups[key].permissions_dashboard
            for key in self.migrate_admin_groups
        ]

        permissions = permissions_users + permissions_group

        api_method = UpdateDataSourcePermissionsApiMethod(self.session, id, permissions)
        response = QuickSightAPI().execute(api_method)
        return response

    def UpdateThemePermissions(self, id):
        permissions_users = [
            self.migrate_admin_users[key].permissions_dashboard
            for key in self.migrate_admin_users
        ]

        permissions_group = [
            self.migrate_admin_groups[key].permissions_dashboard
            for key in self.migrate_admin_groups
        ]

        permissions = permissions_users + permissions_group

        api_method = UpdateThemePermissionsApiMethod(self.session, id, permissions)
        response = QuickSightAPI().execute(api_method)
        return response

    def UpdateTemplatePermissions(self, templateid, target_accountid):

        api_method = UpdateTemplatePermissionsApiMethod(
            self.session, templateid, target_accountid
        )
        response = QuickSightAPI().execute(api_method)
        return response

    def CheckAnalysisDependencies(self, source_analysis):
        # check if datasets used by analysis exist in target account
        source_datasets = source_analysis["DataSetArns"]
        target_datasets = [DataSet["DataSetId"] for DataSet in self.ListDataSets()]
        if all(
            source_dataset.split("/")[1] in target_datasets
            for source_dataset in source_datasets
        ):
            return True

    def CreateAnalysis(self, source_template, source_analysis, source_datasets):

        # Blueprint for create analysis
        bp = const.create_analysis_template
        source_datasets_arns = source_analysis["DataSetArns"]
        source_dataset_refs = []

        # UPDATE VALUES:
        # Replace the values in the source that need to be updated with values from target
        #
        for source_dataset_arn in source_datasets_arns:
            source_dataset_id = source_dataset_arn.split("/")[1]
            source_dataset_name = source_datasets[source_dataset_id].name
            source_dataset_refs.append(
                {
                    "DataSetPlaceholder": source_dataset_name,
                    "DataSetArn": "arn:aws:quicksight:{}:{}:dataset/{}".format(
                        self.region, self.accountid, source_dataset_id
                    ),
                }
            )

        source_entity = {
            "SourceTemplate": {
                "DataSetReferences": source_dataset_refs,
                "Arn": source_template["Template"]["Arn"],
            }
        }

        if source_analysis.get("ThemeArn"):
            source_analysis["ThemeArn"] = "arn:aws:quicksight:{}:{}:theme/{}".format(
                self.region,
                self.accountid,
                source_analysis.get("ThemeArn").split("/")[1],
            )

        # UPDATE CREATE TEMPLATE:
        # Create asset template and fills in the values from the source
        #
        utils.update_nested_dict(bp, "AwsAccountId", self.accountid)

        utils.update_nested_dict(
            bp,
            "AnalysisId",
            source_analysis.get("AnalysisId"),
        )

        utils.update_nested_dict(bp, "Name", source_analysis.get("Name"))

        permissions_users = [
            self.migrate_admin_users[key].permissions_dashboard
            for key in self.migrate_admin_users
        ]

        permissions_group = [
            self.migrate_admin_groups[key].permissions_dashboard
            for key in self.migrate_admin_groups
        ]

        permissions = permissions_users + permissions_group

        utils.update_nested_dict(bp, "Permissions", permissions)
        utils.update_nested_dict(bp, "SourceEntity", source_entity)

        utils.update_nested_dict(bp, "ThemeArn", source_analysis.get("ThemeArn"))

        utils.update_nested_dict(bp, "Tags", self.config_parameters.parameters["tag"])

        new_analysis_args = {k: v for k, v in bp.items() if v and v != ""}

        api_method = CreateAnalysisApiMethod(self.session, new_analysis_args)
        try:
            response = QuickSightAPI().execute(api_method)

        except ClientError as err:
            logger.error(
                "Failed to create analysis %s Error: %s",
                source_analysis["Name"],
                err,
            )
        return response

    def UpdateAnalysis(self, source_template, source_analysis, source_datasets):
        # Blueprint for create analysis
        bp = const.update_analysis_template
        source_datasets_arns = source_analysis["DataSetArns"]
        source_dataset_refs = []

        # UPDATE VALUES:
        # Replace the values in the source that need to be updated with values from target
        #
        for source_dataset_arn in source_datasets_arns:
            source_dataset_id = source_dataset_arn.split("/")[1]
            source_dataset_name = source_datasets[source_dataset_id].name
            source_dataset_refs.append(
                {
                    "DataSetPlaceholder": source_dataset_name,
                    "DataSetArn": "arn:aws:quicksight:{}:{}:dataset/{}".format(
                        self.region, self.accountid, source_dataset_id
                    ),
                }
            )

        source_entity = {
            "SourceTemplate": {
                "DataSetReferences": source_dataset_refs,
                "Arn": source_template["Template"]["Arn"],
            }
        }

        if source_analysis.get("ThemeArn"):
            source_analysis["ThemeArn"] = "arn:aws:quicksight:{}:{}:theme/{}".format(
                self.region,
                self.accountid,
                source_analysis.get("ThemeArn").split("/")[1],
            )

        # UPDATE CREATE TEMPLATE:
        # Create asset template and fills in the values from the source
        #
        utils.update_nested_dict(bp, "AwsAccountId", self.accountid)
        utils.update_nested_dict(
            bp,
            "AnalysisId",
            source_analysis.get("AnalysisId"),
        )

        utils.update_nested_dict(bp, "Name", source_analysis.get("Name"))

        utils.update_nested_dict(bp, "SourceEntity", source_entity)

        utils.update_nested_dict(bp, "ThemeArn", source_analysis.get("ThemeArn"))

        new_analysis_args = {k: v for k, v in bp.items() if v and v != ""}

        api_method = UpdateAnalysisApiMethod(self.session, new_analysis_args)
        try:
            response = QuickSightAPI().execute(api_method)

        except ClientError as err:
            logger.error(
                "Failed to update analysis %s Error: %s",
                source_analysis["Name"],
                err,
            )
        return response

    def get_dataset_name(self, did):
        for dataset in self.ListDataSets():
            if dataset["DataSetId"] == did:
                name = dataset["Name"]
        return name

    # Get Dashboard Ids By Name
    def get_dashboard_ids(self, names):
        ids = []
        for dashboard in self.ListDashboards():
            for name in names:
                if dashboard["Name"] == name:
                    ids.append(dashboard["DashboardId"])
        return ids

    # Get Analysis By Name
    def get_analysis_ids(self, names):
        ids = []
        for analysis in self.ListAnalyses():
            for name in names:
                if analysis["Name"] == name:
                    ids.append(analysis["AnalysisId"])
        return ids

    # Get Theme By Name
    def get_theme_ids(self, names):
        ids = []
        for analysis in self.ListThemes():
            for name in names:
                if analysis["Name"] == name:
                    ids.append(analysis["ThemeId"])
        return ids

    def add_dashboards(self, dashboard_ids):
        for dashboard_id in dashboard_ids:
            if dashboard_id not in self.migrate_dashboards:
                Response = self.DescribeDashboard(dashboard_id)
                Dashboard = QuickSightDashboard(Response)

                self.migrate_dashboards[Dashboard.id] = Dashboard
                self.add_datasets(Dashboard.datasets)

    def add_analyses(self, analyses_ids):
        for analysis_id in analyses_ids:
            if analysis_id not in self.migrate_analyses:
                Response = self.DescribeAnalysis(analysis_id)
                Analysis = QuickSightAnalysis(Response)
                self.migrate_analyses[Analysis.id] = Analysis
                self.add_datasets(Analysis.datasets)

    def add_datasets(self, dataset_ids):
        for dataset_id in dataset_ids:
            if dataset_id not in self.migrate_datasets:
                Response = self.DescribeDataSet(dataset_id)
                DataSet = QuickSightDataSet(Response)
                self.migrate_datasets[DataSet.id] = DataSet
                self.add_datasources(DataSet.datasources)

    def add_datasources(self, datasource_ids):
        for datasource_id in datasource_ids:
            if datasource_id not in self.migrate_datasources:
                Response = self.DescribeDataSource(datasource_id)
                DataSource = QuickSightDataSource(Response)
                self.migrate_datasources[DataSource.id] = DataSource

    def add_themes(self, theme_ids):
        for theme_id in theme_ids:
            if theme_id not in self.migrate_themes:
                Response = self.DescribeTheme(theme_id)
                Theme = QuickSightTheme(Response)
                self.migrate_themes[Theme.id] = Theme

    def add_admin_users(self, user_names):
        for user_name in user_names:
            if user_name not in self.migrate_admin_users:
                Response = self.DescribeUser(user_name)
                User = QuickSightUser(Response)
                self.migrate_admin_users[User.name] = User

    def add_admin_groups(self, group_names):
        for group_name in group_names:
            if group_name not in self.migrate_admin_groups:
                Response = self.DescribeGroup(group_name)
                Group = QuickSightGroup(Response)
                self.migrate_admin_groups[Group.name] = Group

    def create_dataset(self, source_dataset):
        self.source_dataset = source_dataset
        bp = const.create_dataset_template

        utils.update_nested_dict(
            bp,
            "LogicalTableMap",
            source_dataset.get("DataSet").get("LogicalTableMap"),
        )

        physical_table = source_dataset["DataSet"]["PhysicalTableMap"]
        for key, value in physical_table.items():
            for i, j in value.items():
                dsid = j["DataSourceArn"].split("/")[1]
                j[
                    "DataSourceArn"
                ] = f"arn:aws:quicksight:{self.region}:{self.accountid}:datasource/{dsid}"

        utils.update_nested_dict(bp, "AwsAccountId", self.accountid)

        utils.update_nested_dict(
            bp,
            "DataSetId",
            self.source_dataset.get("DataSet").get("DataSetId"),
        )

        utils.update_nested_dict(
            bp, "Name", self.source_dataset.get("DataSet").get("Name")
        )
        utils.update_nested_dict(bp, "PhysicalTableMap", physical_table)

        utils.update_nested_dict(
            bp,
            "LogicalTableMap",
            source_dataset.get("DataSet").get("LogicalTableMap"),
        )
        utils.update_nested_dict(
            bp,
            "ColumnGroups",
            source_dataset.get("DataSet").get("ColumnGroups"),
        )

        utils.update_nested_dict(
            bp, "ImportMode", source_dataset.get("DataSet").get("ImportMode")
        )
        utils.update_nested_dict(
            bp,
            "FieldFolders",
            source_dataset.get("DataSet").get("FieldFolders"),
        )

        permissions_users = [
            self.migrate_admin_users[key].permissions_dashboard
            for key in self.migrate_admin_users
        ]

        permissions_group = [
            self.migrate_admin_groups[key].permissions_dashboard
            for key in self.migrate_admin_groups
        ]

        permissions = permissions_users + permissions_group

        utils.update_nested_dict(bp, "Permissions", permissions)

        new_dataset_args = {k: v for k, v in bp.items() if v and v != ""}

        api_method = CreateDataSetApiMethod(self.session, new_dataset_args)
        try:
            response = QuickSightAPI().execute(api_method)

        except ClientError as err:
            logger.error(
                "Failed to create dataset %s Error: %s",
                source_dataset["Name"],
                err,
            )
        return response

    def UpdateDataSet(self, source_dataset):

        self.source_dataset = source_dataset

        bp = const.create_dataset_template

        utils.update_nested_dict(
            bp,
            "LogicalTableMap",
            source_dataset.get("DataSet").get("LogicalTableMap"),
        )

        physical_table = source_dataset["DataSet"]["PhysicalTableMap"]
        for key, value in physical_table.items():
            for i, j in value.items():
                dsid = j["DataSourceArn"].split("/")[1]
                j[
                    "DataSourceArn"
                ] = f"arn:aws:quicksight:{self.region}:{self.accountid}:datasource/{dsid}"

        utils.update_nested_dict(bp, "AwsAccountId", self.accountid)

        utils.update_nested_dict(
            bp,
            "DataSetId",
            self.source_dataset.get("DataSet").get("DataSetId"),
        )

        utils.update_nested_dict(
            bp, "Name", self.source_dataset.get("DataSet").get("Name")
        )
        utils.update_nested_dict(bp, "PhysicalTableMap", physical_table)

        utils.update_nested_dict(
            bp,
            "LogicalTableMap",
            source_dataset.get("DataSet").get("LogicalTableMap"),
        )
        utils.update_nested_dict(
            bp,
            "ColumnGroups",
            source_dataset.get("DataSet").get("ColumnGroups"),
        )

        utils.update_nested_dict(
            bp, "ImportMode", source_dataset.get("DataSet").get("ImportMode")
        )
        utils.update_nested_dict(
            bp,
            "FieldFolders",
            source_dataset.get("DataSet").get("FieldFolders"),
        )

        new_dataset_args = {k: v for k, v in bp.items() if v and v != ""}

        api_method = UpdateDataSetApiMethod(self.session, new_dataset_args)
        try:
            response = QuickSightAPI().execute(api_method)

        except ClientError as err:
            logger.error(
                "Failed to update dataset %s Error: %s",
                source_dataset["Name"],
                err,
            )
        return response

    def create_data_source(self, source_datasource):

        source_datasource_params = source_datasource["DataSourceParameters"]

        # TODO Supported data source validation
        # AlternateDataSourceParameters
        # Check if the Datasource Type supported by the migration tool
        if source_datasource["Type"].lower() in const.conn_dict:

            # Replace datasource parameters with config values

            credentials = utils.create_credential(
                self.config_parameters.parameters.get("rdsUsername"),
                self.config_parameters.parameters.get("rdsPassword"),
            )

            utils.update_nested_dict(
                source_datasource_params,
                "InstanceId",
                self.config_parameters.parameters.get("rdsInstanceId"),
            )
            utils.update_nested_dict(
                source_datasource_params,
                "Database",
                self.config_parameters.parameters.get("rdsDB"),
            )
            utils.update_nested_dict(
                source_datasource_params,
                "Host",
                self.config_parameters.parameters.get("rdsHost"),
            )
            utils.update_nested_dict(
                source_datasource_params,
                "Port",
                self.config_parameters.parameters.get("rdsPort"),
            )
            utils.update_nested_dict(
                source_datasource_params, "Credentials", credentials
            )

        # REDSHIFT Cluster
        # Replace datasource parameters with config values
        if source_datasource["Type"] == "REDSHIFT":
            # Create Credenital Pair
            credentials = utils.create_credential(
                self.config_parameters.parameters["redshiftUsername"],
                self.config_parameters.parameters["redshiftPassword"],
            )

            utils.update_nested_dict(
                source_datasource_params,
                "ClusterId",
                self.config_parameters.parameters.get("redshiftClusterId"),
            )
            utils.update_nested_dict(
                source_datasource_params,
                "Database",
                self.config_parameters.parameters.get("redshiftDB"),
            )
            utils.update_nested_dict(
                source_datasource_params,
                "Host",
                self.config_parameters.parameters.get("redshiftHost"),
            )
            utils.update_nested_dict(
                source_datasource_params,
                "Port",
                self.config_parameters.parameters.get("rdsPort"),
            )
            utils.update_nested_dict(
                source_datasource_params, "Credentials", credentials
            )

        # remove empty values from data source parameters
        source_datasource_params = utils.remove_nested_dict(source_datasource_params)

        # blueprint for create datasource request
        bp = const.create_datasource_template
        # TODO: Validation for if datasource has vpc then config parameter must exist

        utils.update_nested_dict(bp, "AwsAccountId", self.accountid)
        utils.update_nested_dict(
            bp, "DataSourceId", source_datasource.get("DataSourceId")
        )

        utils.update_nested_dict(bp, "Name", source_datasource.get("Name"))

        utils.update_nested_dict(bp, "Type", source_datasource.get("Type"))

        utils.update_nested_dict(bp, "DataSourceParameters", source_datasource_params)

        utils.update_nested_dict(
            bp,
            "VpcConnectionArn",
            self.config_parameters.parameters["vpcId"],
        )

        utils.update_nested_dict(
            bp, "SslProperties", source_datasource.get("SslProperties")
        )

        utils.update_nested_dict(bp, "Tags", self.config_parameters.parameters["tag"])

        utils.update_nested_dict(
            bp, "Credentials", source_datasource.get("Credentials")
        )
        permissions_users = [
            self.migrate_admin_users[key].permissions_dashboard
            for key in self.migrate_admin_users
        ]

        permissions_group = [
            self.migrate_admin_groups[key].permissions_dashboard
            for key in self.migrate_admin_groups
        ]

        permissions = permissions_users + permissions_group
        utils.update_nested_dict(bp, "Permissions", permissions)

        # remove empty values from template
        new_datasource_args = {k: v for k, v in bp.items() if v and v != ""}

        api_method = CreateDataSourceApiMethod(self.session, new_datasource_args)
        try:
            response = QuickSightAPI().execute(api_method)

        except ClientError as err:
            logger.error(
                "Failed to create datasource %s Error: %s",
                source_datasource["Name"],
                err,
            )
        return response

    def CreateDashboard(self, source_template, source_dashboard, source_datasets):

        # Blueprint for create dashboard

        source_datasets_arns = source_dashboard["Version"]["DataSetArns"]
        source_dataset_refs = []

        # UPDATE VALUES:
        # Replace the values in the source that need to be updated with values from target
        #
        for source_dataset_arn in source_datasets_arns:
            source_dataset_id = source_dataset_arn.split("/")[1]
            source_dataset_name = source_datasets[source_dataset_id].name
            source_dataset_refs.append(
                {
                    "DataSetPlaceholder": source_dataset_name,
                    "DataSetArn": "arn:aws:quicksight:{}:{}:dataset/{}".format(
                        self.region, self.accountid, source_dataset_id
                    ),
                }
            )

        # Replace the Source Entity with the updated dataset arns
        source_dashboard["Version"]["SourceEntity"] = {
            "SourceTemplate": {
                "DataSetReferences": source_dataset_refs,
                "Arn": source_template["Template"]["Arn"],
            }
        }

        DashboardPublishOptions = {
            "AdHocFilteringOption": {"AvailabilityStatus": "DISABLED"},
            "ExportToCSVOption": {"AvailabilityStatus": "ENABLED"},
            "SheetControlsOption": {"VisibilityState": "COLLAPSED"},
        }

        if source_dashboard.get("ThemeArn"):
            source_dashboard["ThemeArn"] = "arn:aws:quicksight:{}:{}:theme/{}".format(
                self.region,
                self.accountid,
                source_dashboard.get("Version").get("ThemeArn").split("/")[1],
            )

        # UPDATE CREATE TEMPLATE:
        # Create asset template and fills in the values from the source
        #
        bp = const.create_dashboard_template
        utils.update_nested_dict(bp, "AwsAccountId", self.accountid)
        utils.update_nested_dict(
            bp,
            "DashboardId",
            source_dashboard.get("DashboardId"),
        )

        utils.update_nested_dict(bp, "Name", source_dashboard.get("Name"))

        permissions_users = [
            self.migrate_admin_users[key].permissions_dashboard
            for key in self.migrate_admin_users
        ]

        permissions_group = [
            self.migrate_admin_groups[key].permissions_dashboard
            for key in self.migrate_admin_groups
        ]

        permissions = permissions_users + permissions_group

        utils.update_nested_dict(
            bp,
            "Permissions",
            permissions,
        )
        utils.update_nested_dict(
            bp,
            "SourceEntity",
            source_dashboard.get("Version").get("SourceEntity"),
        )

        utils.update_nested_dict(
            bp, "ThemeArn", source_dashboard.get("Version").get("ThemeArn")
        )

        utils.update_nested_dict(bp, "Tags", self.config_parameters.parameters["tag"])
        utils.update_nested_dict(
            bp,
            "VersionDescription",
            source_dashboard.get("Version").get("Description"),
        )
        utils.update_nested_dict(bp, "DashboardPublishOptions", DashboardPublishOptions)

        new_dashboard_args = {k: v for k, v in bp.items() if v and v != ""}

        api_method = CreateDashboardApiMethod(self.session, new_dashboard_args)
        try:
            QuickSightAPI().execute(api_method)

        except ClientError as err:
            logger.error(
                "Failed to create dashboard %s Error: %s",
                source_dashboard["Name"],
                err,
            )


class QuickSightDashboard:
    def __init__(self, response):
        self.response = response
        self.id = self.__get_id()
        self.name = self.__get_name()
        self.datasets = self.__get_datasets()
        self.status = "imported"

    def __get_datasets(self):
        datasets = [x.split("/")[1] for x in self.response["Version"]["DataSetArns"]]
        return datasets

    def __get_name(self):
        name = self.response["Name"]
        return name

    def __get_id(self):
        id = self.response["DashboardId"]
        return id


class QuickSightAnalysis:
    def __init__(self, response):
        self.response = response
        self.id = self.__get_id()
        self.name = self.__get_name()
        self.datasets = self.__get_datasets()
        self.status = "imported"

    def __get_datasets(self):
        datasets = [x.split("/")[1] for x in self.response["DataSetArns"]]
        return datasets

    def __get_name(self):
        name = self.response["Name"]
        return name

    def __get_id(self):
        id = self.response["AnalysisId"]
        return id


class QuickSightDataSet:
    def __init__(self, response):
        self.response = response
        self.id = self.__get_id()
        self.name = self.__get_name()
        self.datasources = self.__get_datasources()
        self.status = "imported"

    def __get_datasources(self):
        datasources = []
        physical_table = self.response["DataSet"]["PhysicalTableMap"]
        for key, value in physical_table.items():
            for i, j in value.items():
                data_source_id = j["DataSourceArn"].split("/")[1]
                datasources.append(data_source_id)
        return datasources

    def __get_name(self):
        name = self.response["DataSet"]["Name"]
        return name

    def __get_id(self):
        id = self.response["DataSet"]["DataSetId"]
        return id
        self.migrated = False


class QuickSightDataSource:
    def __init__(self, response):
        self.response = response
        self.id = self.__get_id()
        self.name = self.__get_name()
        self.status = "imported"

    def __get_name(self):
        name = self.response["Name"]
        return name

    def __get_id(self):
        id = self.response["DataSourceId"]
        return id


class QuickSightTheme:
    def __init__(self, response):
        self.response = response
        self.id = self.__get_id()
        self.name = self.__get_name()
        self.status = "imported"

    def __get_name(self):
        name = self.response["Theme"]["Name"]
        return name

    def __get_id(self):
        id = self.response["Theme"]["ThemeId"]
        return id


class QuickSightUser:
    def __init__(self, response):
        self.response = response
        self.id = self.__get_id()
        self.name = self.__get_name()
        self.arn = self.__get_arn()
        self.permissions_datasource = {
            "Principal": self.arn,
            "Actions": const.admin_actions_datasource,
        }
        self.permissions_dataset = {
            "Principal": self.arn,
            "Actions": const.admin_actions_dataset,
        }
        self.permissions_dashboard = {
            "Principal": self.arn,
            "Actions": const.admin_actions_dashboard,
        }
        self.permissions_analysis = {
            "Principal": self.arn,
            "Actions": const.admin_actions_analysis,
        }
        self.permissions_theme = {
            "Principal": self.arn,
            "Actions": const.admin_actions_theme,
        }

    def __get_name(self):
        name = self.response["User"]["UserName"]
        return name

    def __get_id(self):
        id = self.response["User"]["PrincipalId"]
        return id

    def __get_arn(self):
        arn = self.response["User"]["Arn"]
        return arn


class QuickSightGroup:
    def __init__(self, response):
        self.response = response
        self.id = self.__get_id()
        self.name = self.__get_name()
        self.arn = self.__get_arn()
        self.permissions_datasource = {
            "Principal": self.arn,
            "Actions": const.admin_actions_datasource,
        }
        self.permissions_dataset = {
            "Principal": self.arn,
            "Actions": const.admin_actions_dataset,
        }
        self.permissions_dashboard = {
            "Principal": self.arn,
            "Actions": const.admin_actions_dashboard,
        }
        self.permissions_analysis = {
            "Principal": self.arn,
            "Actions": const.admin_actions_analysis,
        }
        self.permissions_theme = {
            "Principal": self.arn,
            "Actions": const.admin_actions_theme,
        }

    def __get_name(self):
        name = self.response["Group"]["GroupName"]
        return name

    def __get_id(self):
        id = self.response["Group"]["PrincipalId"]
        return id

    def __get_arn(self):
        arn = self.response["Group"]["Arn"]
        return arn


class QuickSightConfig:
    def __init__(self, accountid, region):
        self.accountid = accountid
        self.region = region
        self.parameters = {}

    def add_parameter(self, parameter, value):
        if not value and parameter == "namespace":
            value = "default"
        if not value and parameter == "version":
            value = "1"
        if parameter == "vpcId":
            value = f"arn:aws:quicksight:{self.region}:{self.accountid}:vpcConnection/{value}"

        self.parameters[parameter] = value
