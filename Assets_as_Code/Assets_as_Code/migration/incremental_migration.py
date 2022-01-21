"""
This script is for dev/admin to migrate quicksight assets accross accounts or regions
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
f = open('config/dev_configuration.json', )
dev_config = json.load(f)

f = open('config/prod_configuration.json', )
prod_config = json.load(f)

"""
Migration List:
* for migrate_p
    "all" will migrate data source, dataset, theme, analysis and dashboard;
    "source" means data sources only; 
    "dataset" means datasets only; 
    "theme" means theme only;
    "analysis" means analysis only;
    "dashboard" means dashboard only
"""
migrate_p = 'dashboard'

"""
Sample migration list input, please pick up one of them and then comment out the others
"""
data_source_migrate_list = ["redshift-auto", "mssql", "athena_1","redshift_manual"]
data_set_migrate_list = ["patient_info"]
theme_migrate_list= ["orange"]
analysis_migrate_list= ["QuickSight_Access_Last_24_H_Analysis","Marketing Analysis"]
dashboard_migrate_list = ["QuickSight_Access_Last_24_H", "Marketing Dashboard"]

"""
Process the input to get the finalized migration list
"""
m_list = func.process_migration_list(migrate_p, analysis_migrate_list, dev_config)

"""
Run the migration
"""
res = func.incremental_migration(dev_config, prod_config, migrate_p, m_list)

