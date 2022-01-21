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


"""
Now, please add this analysis into qa folder
"""
res = func.locate_folder_of_asset(qs_session, new_id, dev_config["qa_folder"], 'ANALYSIS')
print(new_name + " is successfully added into folder QA")

"""
Now, please add this analysis into prod folder
"""
#res = func.locate_folder_of_asset(qs_session, new_id, dev_config["prod_folder"], 'analysis')
#print(new_name + " is successfully added into folder Prod")

# res = func.incremental_migration(dev_config, prod_config,'analysis', ['copy_t_1'])

