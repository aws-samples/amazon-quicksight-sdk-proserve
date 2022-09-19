import deployment_utils as du
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
from botocore.exceptions import ClientError
import deployment_utils as du

logging.basicConfig(level=os.environ.get("LOGLEVEL", "INFO"))
logger = logging.getLogger('Folder-Deployment')
logger.setLevel(logging.INFO)

#analysisID = 'ddea1363-0ecc-47d1-9931-18212384e9da'
#analysisName = 'sample analysis'
datasetID = '5813ee12-2c1e-481a-8d8a-3ad8a3443ca9'
# source info
sourceaccountid = '841207543475'
# source_role_name = '<execution role for the source account>'
source_aws_region = 'us-east-1'
source_folder_name = 'Staging'
source_folder_ID = '05b880a9-fa54-4835-bff6-fb5f040b45c3'
# source_staging_folder_name = 'Staging'
# source_staging_folder_ID = '05b880a9-fa54-4835-bff6-fb5f040b45c3'
source_is_dev = False # analysis exists in dev folder
source_is_main = False # in main environment, object IDs don't have folder name suffix
source_admin_name = 'Admin/qinyaw-Isengard'

# target info
# test case 1, across account PROD
targetaccountid = '045559142339'
target_role_name = 'Admin'
target_aws_region = 'us-east-1'
# target_folder_name = 'Prod'
# target_folder_ID = 'b8b6c49e-6f96-471b-b579-60f7d7966bea'
target_is_dev = False  # set this flag to true if analysis migration is necessary (in use case like roll back); by default analysis will not be migrated.
target_is_main = False
target_admin_name = 'Admin/qinyaw-Isengard'


# # test case 2, same account PROD folder
# targetaccountid = '841207543475'
# # target_role_name = 'Admin'
# target_aws_region = 'us-east-1'
# target_folder_name = 'PROD'
# target_folder_ID = '0e647a24-09a3-4cab-848a-3a18c05e2921'
# target_is_dev = False  # set this flag to true if analysis migration is necessary (in use case like roll back); by default analysis will not be migrated.
# target_is_main = False
# target_admin_name = 'Admin-OneClick/liaoying-Isengard'

sourcesession = boto3.Session(region_name=source_aws_region, profile_name='account2-admin')
targetsession = boto3.Session(region_name=target_aws_region, profile_name='account1-admin')

# Set root and admin users
# root user is for the template. By default, we assign full permissions of objects to admin.
# sourceroot = qu.get_user_arn(sourcesession, 'root')
sourceadmin = qu.get_user_arn(sourcesession, source_admin_name)
#
# targetroot = qu.get_user_arn(targetsession, 'root')
targetadmin = qu.get_user_arn(targetsession, target_admin_name)
# migration settings
same_account_migration = (True if sourceaccountid == targetaccountid else False)

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

        target_id = source_id
    return target_id


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


# data source naming convention: name-DEV, name-UAT, name-PROD
def get_target_data_source_id(data_source_id):
    try:
        res = qu.describe_data_source(sourcesession, data_source_id)
        source_name = res['DataSource']['Name']
        target_name = source_name.replace(('-' + source_folder_name), '')
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

# Get already migrated datasets list

faillist=[]
newlist=[]
deployment_config = {
    "get_target_id_func": get_target_id,
    #"get_target_dashboard_id_func": get_target_dashboard_id,
    #"get_target_dashboard_name_func": get_target_dashboard_name,
    "get_target_placeholder_func": get_target_placeholder,
    "get_target_data_source_id_func": get_target_data_source_id,
    "target_permission": target_permission,
    "source_account_id": sourceaccountid,
    "target_account_id": targetaccountid,
    #'already_migrated_dataset': already_migrated_ds,
    'dataset_fail_list' : faillist,
    'dataset_new_list': newlist
}
# test migrate dataset
migrate_dataset = du.migrate_dataset(datasetID,sourcesession, targetsession, deployment_config)

# test migrate dashboard
# dsc = qu.list_data_sources(targetsession)
# print(dsc)