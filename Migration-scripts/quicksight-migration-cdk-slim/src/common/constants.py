# https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/quicksight.html#QuickSight.Client.create_data_source
conn_dict = {
    "aurora": "AuroraParameters",
    "aurora_postgresql": "AuroraPostgreSqlParameters",
    "mariadb": "MariaDbParameters",
    "mysql": "MySqlParameters",
    "postgresql": "PostgreSqlParameters",
    "sqlserver": "SqlServerParameters",
}

create_dataset_template = {
    "AwsAccountId": None,
    "DataSetId": None,
    "Name": None,
    "PhysicalTableMap": None,
    "LogicalTableMap": None,
    "ImportMode": None,
    "ColumnGroups": None,
    "FieldFolders": None,
    "Permissions": None,
    "RowLevelPermissionDataSet": None,
    "RowLevelPermissionTagConfiguration": None,
    "ColumnLevelPermissionRules": None,
    "Tags": None,
    "DataSetUsageConfiguration": None,
}
create_datasource_template = {
    "AwsAccountId": None,
    "DataSetId": None,
    "Name": None,
    "Type": None,
    "DataSourceParameters": None,
    "Credentials": None,
    "Permissions": None,
    "VpcConnectionProperties": None,
    "SslProperties": None,
    "Tags": None,
}
create_analysis_template = {
    "AwsAccountId": None,
    "AnalysisId": None,
    "Name": None,
    "Parameters": None,
    "Permissions": None,
    "SourceEntity": None,
    "ThemeArn": None,
    "Tags": None,
}
update_analysis_template = {
    "AwsAccountId": None,
    "AnalysisId": None,
    "Name": None,
    "Parameters": None,
    "SourceEntity": None,
    "ThemeArn": None
}
create_dashboard_template = {
    "AwsAccountId": None,
    "DashboardId": None,
    "Name": None,
    "Parameters": None,
    "Permissions": None,
    "SourceEntity": None,
    "Tags": None,
    "VersionDescription": None,
    "DashboardPublishOptions": None,
    "ThemeArn": None,
}
create_datasource_template = {
    "AwsAccountId": None,
    "DataSourceId": None,
    "Name": None,
    "Type": None,
    "DataSourceParameters": None,
    "Credentials": None,
    "Permissions": None,
    "VpcConnectionProperties": {"VpcConnectionArn": None},
    "SslProperties": None,
    "Tags": None,
}
admin_actions_datasource = [
    "quicksight:DescribeDataSource",
    "quicksight:DescribeDataSourcePermissions",
    "quicksight:PassDataSource",
    "quicksight:UpdateDataSource",
    "quicksight:DeleteDataSource",
    "quicksight:UpdateDataSourcePermissions",
]
admin_actions_dataset = [
    "quicksight:UpdateDataSetPermissions",
    "quicksight:DescribeDataSet",
    "quicksight:DescribeDataSetPermissions",
    "quicksight:PassDataSet",
    "quicksight:DescribeIngestion",
    "quicksight:ListIngestions",
    "quicksight:UpdateDataSet",
    "quicksight:DeleteDataSet",
    "quicksight:CreateIngestion",
    "quicksight:CancelIngestion",
]

admin_actions_dashboard = [
    "quicksight:DescribeDashboard",
    "quicksight:ListDashboardVersions",
    "quicksight:UpdateDashboardPermissions",
    "quicksight:QueryDashboard",
    "quicksight:UpdateDashboard",
    "quicksight:DeleteDashboard",
    "quicksight:DescribeDashboardPermissions",
    "quicksight:UpdateDashboardPublishedVersion",
]
admin_actions_analysis = [
    "quicksight:RestoreAnalysis",
    "quicksight:UpdateAnalysisPermissions",
    "quicksight:DeleteAnalysis",
    "quicksight:QueryAnalysis",
    "quicksight:DescribeAnalysisPermissions",
    "quicksight:DescribeAnalysis",
    "quicksight:UpdateAnalysis",
]
admin_actions_theme = [
    "quicksight:ListThemeVersions",
    "quicksight:UpdateThemeAlias",
    "quicksight:UpdateThemePermissions",
    "quicksight:DescribeThemeAlias",
    "quicksight:DeleteThemeAlias",
    "quicksight:DeleteTheme",
    "quicksight:ListThemeAliases",
    "quicksight:DescribeTheme",
    "quicksight:CreateThemeAlias",
    "quicksight:UpdateTheme",
    "quicksight:DescribeThemePermissions",
]
