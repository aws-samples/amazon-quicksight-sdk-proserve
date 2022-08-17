"""
This script template is for dev/admin to copy a sample analysis in dev account, programmable edit it, and then promote it
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
f = open('library/1st_class_assets/dashboard_library.json')
l_dashboard = json.load(f)

#load dev and prod account configuration
f = open('config/dev_configuration.json', )
dev_config = json.load(f)
f = open('config/prod_configuration.json', )
prod_config = json.load(f)

#start quicksight session
qs_session = s_func._assume_role(dev_config["aws_account_number"], dev_config["role_name"],  dev_config["aws_region"])


# provide the name of sample dashboard we would like to copy
name = 'WorkItems_test_dashboard'
# provide the id and name of the new dashboard
new_id = 'WorkItems_test_dashboard_t_3'
new_name = 'WorkItems_test_dashboard_t_3'

# please provide the template dashboard name you would like to copy
dashboardid = l_dashboard[name]

"""automation process
step 1 of scenario 1: copy a dashboard and then add in dev account/folder
"""
faillist = [] #define log array to record errors
successlist = [] #define log array to record success

try:
    sample_dashboard = func.describe_dashboard_contents(qs_session, dashboardid)
    print(sample_dashboard)
except Exception as e:
    faillist.append({
        "Action": "scenario_2_dev: get sample dashboard contents",
        "Error Type": "describe_dashboard_contents Error",
        "DashboardID": dashboardid,
        "Name": 'WorkItems_test_dashboard_t_3',
        "Error": str(e)
    })
    print(faillist)
if sample_dashboard['DashboardId']  is not None:
    print(name + "'s contents is successfully get!")
    # print(sample_dashboard['Version'])

try:
    res = func.copy_dashboard(qs_session, sample_dashboard, new_id, new_name, dev_config["assets_owner"])
except Exception as e:
    faillist.append({
        "Action": "scenario_2_dev: copy dashboard",
        "Error Type": "copy_dashboard Error",
        "DashboardID": dashboardid,
        "Name": name,
        "Error": str(e)
    })
    print(faillist)
time.sleep(20)
'''
status = func.check_object_status('dashboard', new_id, qs_session)
while status=="CREATION_IN_PROGRESS":
        time.sleep(5)
        status = func.check_object_status('dashboard', new_id, qs_session)
        if status=='CREATION_SUCCESSFUL':
            break
else:
        if status=='CREATION_SUCCESSFUL':
            print("Dashboard" + name + " is successful copied as " + new_name + "!")
            res = func.locate_folder_of_asset(qs_session, new_id, dev_config["dev_folder"], 'DASHBOARD')
        else:
            # Notify Ying
            faillist.append({
                "Action": "scenario_2_dev: copy dashboard",
                "Error Type": "copy_dashboard Error",
                "AnalysisID": dashboardid,
                "Name": name,
                # "Error": str(e)
            })

new_dashboard = func.describe_dashboard_contents(qs_session, new_id)'''

"""
Now, please add this analysis into qa folder
"""
# res = func.locate_folder_of_asset(qs_session, new_id, dev_config["qa_folder"], 'ANALYSIS')
# print(new_name + " is successfully added into folder QA")

"""
Now, please add this analysis into prod folder
"""
#res = func.locate_folder_of_asset(qs_session, new_id, dev_config["prod_folder"], 'analysis')
#print(new_name + " is successfully added into folder Prod")

# res = func.incremental_migration(dev_config, prod_config,'analysis', ['copy_t_1'])

