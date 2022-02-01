"""
This script is for dev/admin to add quicksight 2nd_class assets into library
Author: Ying Wang
Email: wangzyn@amazon.com or ywangufl@gmail.com
Version: Nov-30-2021
Note:
    configuration are in ./config folder
    library are in ./library folder
    imported functions are in ./src folder
    migration folder is for migrating exisiting QS assets accross differnt accounts/regions.
    exported_results folder stores some sample QS API exported results.
    log folder stores logs
    utils folder has all the utility scripts
Thank you and enjoy the open source self-service BI!
"""

"""
Import libraries
"""
import sys
import boto3
import json
import time
from Migration_scripts.Assets_as_Code.src import functions as func
from Migration_scripts.Assets_as_Code.src import supportive_functions as s_func
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime

"""
#load dev account configuration
#load prod account configuration
"""
f = open('../config/dev_configuration.json', )
dev_config = json.load(f)

f = open('../config/prod_configuration.json', )
prod_config = json.load(f)

#start quicksight session
qs_session = s_func._assume_role(dev_config["aws_account_number"], dev_config["role_name"],  dev_config["aws_region"])

# provide asset information
id = '0b35736a-fdc2-4d71-b561-7990de169acf' #'asset_id'
region = 'us-east-1'
input_type = 'analysis' #datasource, dataset, analysis, dashboard, theme
#assets_arn = func.get_asset_arn(qs_session, id, input_type, region)

# what we would like to add into library
#output_type = 'parameter' # 2nd class object: parameter, cf, sheet, ds_folder, filter; 1st class obj: analysis, dashboard, theme, data_set, data_source, folder
#name = 'Country'
#output_type = 'analysis'
#name = 'template_1'
output_type = 'sheet'
name = 'Pie'

# add this asset into library
res = func.add_asset_in_library(qs_session, id, input_type, name, output_type)