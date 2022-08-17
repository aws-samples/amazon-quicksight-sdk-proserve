"""
This script template is for dev/admin to copy a sample analysis in dev account, manually edit it, and then promote it
into higher environment (UAT, PROD).
Author: Ying Wang
Email: wangzyn@amazon.com or ywangufl@gmail.com
Version: Nov-20-2021
Note:
    configuration are in ./config folder
    library are in ./library folder
    imported functions are in ./src folder
    migration folder is for migrating exisiting QS assets accross differnt accounts/regions.
    exported_results folder stores some sample QS API exported results.
    log folder stores logs
Thank you and enjoy the open source self-service BI!
"""

"""
import libraries
"""
import boto3
import time
import json
import sys
import Assets_as_Code.src
import Assets_as_Code.src.functions as func
import Assets_as_Code.src.supportive_functions as s_func

#load analysis library
f = open('library/1st_class_assets/analysis_library.json')
l_analysis = json.load(f)

#load dev and prod account configuration
f = open('config/dev_configuration.json', )
dev_config = json.load(f)
f = open('config/prod_configuration.json', )
prod_config = json.load(f)

#start quicksight session
qs_session = s_func._assume_role(dev_config["aws_account_number"], dev_config["role_name"],  dev_config["aws_region"])

# please provide the template analysis name you would like to copy
analysisid = l_analysis['template_1']    # analysisid = l_analysis['sample_analysis_name']

"""automation process
step 1 of scenario 1: copy a sample analysis and then edit in dev account/folder
"""
faillist = [] #define log array to record errors
successlist = [] #define log array to record success

try:
    sample_analysis = func.describe_analysis_contents(qs_session, analysisid)
except Exception as e:
    faillist.append({
        "Action": "scenario_1_dev: get sample analysis contents",
        "Error Type": "describe_analysis_contents Error",
        "AnalysisID": analysisid,
        "Name": 'template_1',
        "Error": str(e)
    })
new_id = 'copy_t_1'
new_name = 'copy_t_1'
try:
    res = func.copy_analysis(qs_session, sample_analysis, new_id, new_name, 'owner', dev_config["assets_owner"])
except Exception as e:
    faillist.append({
        "Action": "scenario_1_dev: copy analysis",
        "Error Type": "copy_analysis Error",
        "AnalysisID": analysisid,
        "Name": 'template_1',
        "Error": str(e)
    })
time.sleep(20)
status = func.check_object_status('analysis', new_id, qs_session)
if status == 'CREATION_SUCCESSFUL':
    res = func.locate_folder_of_asset(qs_session, new_id, dev_config["def_folder"], 'analysis')

"""
Now, please do any editing in your dev folder of dev account
"""

res = func.incremental_migration(dev_config, prod_config,'analysis', [new_id])

