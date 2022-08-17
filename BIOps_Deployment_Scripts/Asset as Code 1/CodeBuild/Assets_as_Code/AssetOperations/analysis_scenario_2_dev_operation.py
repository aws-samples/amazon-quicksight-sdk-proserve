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
import src
import src.functions as func
import src.supportive_functions as s_func

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

# provide the name of sample analysis we would like to copy
name = 'template_1'
# provide the id and name of the new analysis
new_id = 'copy_t_1'
new_name = 'copy_t_1'

# please provide the template analysis name you would like to copy
analysisid = l_analysis[name]    # analysisid = l_analysis['sample_analysis_name']

"""automation process
step 1 of scenario 1: copy a template analysis and then edit in dev account/folder
"""
faillist = [] #define log array to record errors
successlist = [] #define log array to record success

try:
    sample_analysis = func.describe_analysis_definition(qs_session, analysisid)
except Exception as e:
    faillist.append({
        "Action": "scenario_2_dev: get sample analysis contents",
        "Error Type": "describe_analysis_definition Error",
        "AnalysisID": analysisid,
        "Name": 'template_1',
        "Error": str(e)
    })
if sample_analysis['Analysis']['AnalysisId']  is not None:
    print(name + "'s contents is successfully get!")
try:
    res = func.copy_analysis(qs_session, sample_analysis, new_id, new_name, dev_config["assets_owner"])
except Exception as e:
    faillist.append({
        "Action": "scenario_2_dev: copy analysis",
        "Error Type": "copy_analysis Error",
        "AnalysisID": analysisid,
        "Name": name,
        "Error": str(e)
    })
time.sleep(20)
status = func.check_object_status('analysis', new_id, qs_session)
while status=="CREATION_IN_PROGRESS":
        time.sleep(5)
        status = func.check_object_status('analysis', new_id, qs_session)
        if status=='CREATION_SUCCESSFUL':
            break
else:
        if status=='CREATION_SUCCESSFUL':
            print("Analysis" + name + " is successful copied as " + new_name + "!")
            res = func.locate_folder_of_asset(qs_session, new_id, dev_config["dev_folder"], 'ANALYSIS')
        else:
            faillist.append({
                "Action": "scenario_2_dev: copy analysis",
                "Error Type": "copy_analysis Error",
                "AnalysisID": analysisid,
                "Name": name,
                "Error": str(e)
            })

new_analysis = func.describe_analysis_definition(qs_session, new_id)
"""
Now, please add CalculatedFields
"""
f = open('library/2nd_class_assets/analysis_cf_library.json')
l_cf = json.load(f)
cf_name = 'most_recent'
try:
    res = func.update_analysis(qs_session,new_id, new_name, new_analysis, 'CalculatedFields', l_cf[cf_name])
except Exception as e:
    faillist.append({
        "Action": "scenario_2_dev: add CalculatedFields",
        "Error Type": "update_analysis Error",
        "AnalysisID": new_id,
        "Name": new_name,
        "Error": str(e)
    })
print(cf_name + " is successfully added into analysis " + new_name)
"""
Now, please add parameters (keyword: ParameterDeclarations)
"""
new_analysis = func.describe_analysis_definition(qs_session, new_id)
f = open('library/2nd_class_assets/parameter_library.json')
l_p = json.load(f)
p_name = "StartDate"
try:
    res = func.update_analysis(qs_session,new_id, new_name, new_analysis, 'ParameterDeclarations', l_p[p_name])
except Exception as e:
    faillist.append({
        "Action": "scenario_2_dev: add ParameterDeclarations",
        "Error Type": "update_analysis Error",
        "AnalysisID": new_id,
        "Name": new_name,
        "Error": str(e)
    })
print(p_name + " is successfully added into analysis " + new_name)
"""
Now, please add Sheets
"""
new_analysis = func.describe_analysis_definition(qs_session, new_id)
f = open('library/2nd_class_assets/analysis_sheet_library.json')
l_s = json.load(f)
s_name = "Pie"
try:
    res = func.update_analysis(qs_session,new_id, new_name, new_analysis, 'Sheets', l_s[s_name])
except Exception as e:
    faillist.append({
        "Action": "scenario_2_dev: add ParameterDeclarations",
        "Error Type": "update_analysis Error",
        "AnalysisID": new_id,
        "Name": new_name,
        "Error": str(e)
    })
print(s_name + " is successfully added into analysis " + new_name)
"""
Now, please add FilterGroups
"""

"""
Now, please add controls
"""

"""
Now, please add this analysis into qa folder
"""
#res = func.locate_folder_of_asset(qs_session, new_id, dev_config["qa_folder"], 'ANALYSIS')
#print(new_name + " is successfully added into folder QA")

"""
Now, please add this analysis into prod folder
"""
#res = func.locate_folder_of_asset(qs_session, new_id, dev_config["prod_folder"], 'analysis')
#print(new_name + " is successfully added into folder Prod")

# res = func.incremental_migration(dev_config, prod_config,'analysis', ['copy_t_1'])

