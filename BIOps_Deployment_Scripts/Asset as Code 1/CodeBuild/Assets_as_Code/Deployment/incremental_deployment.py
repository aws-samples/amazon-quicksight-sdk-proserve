"""
This script is for dev/admin to migrate quicksight assets across accounts or regions
Author: Roshni Ghosh
Email: rghosh2@mmm.com
Version: Jan-05-2022
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
from Assets_as_Code.src import functions as func
from Assets_as_Code.src import supportive_functions as s_func
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime

import os
import re
import argparse
import requests
import zipfile
from io import BytesIO

# python -m Assets_as_Code.Deployment.incremental_deployment --account --region us-east-1 --env 


def sanitize_args(args):
    for arg in vars(args):
        arg_input = getattr(args, arg)
        if isinstance(arg_input, str):
            if arg == "account":
                setattr(args, arg, re.sub(r"[^0-9]", "", arg_input))
            else:
                setattr(args, arg, re.sub(r"[^a-zA-Z0-9-_\.\/]", "", arg_input))

CLI = argparse.ArgumentParser()
CLI.add_argument(
    "--account",
    required=True,
    help='Environment Account ID'
)
CLI.add_argument(
    "--region",
    required=False,
    help='AWS Region',
    default='us-east-1'
)
CLI.add_argument(
    "--env",
    required=True,
    help='Environment',
)

args = CLI.parse_args()
sanitize_args(args)

"""
Unzip Nexus package
"""
awsrole = "ADD-" + args.env + "-"
session = s_func._assume_role(args.account, awsrole, args.region)

if args.env == "u3npnp":
    print('Retrieving artifact')
    r = requests.get(""")
else:
    print('Retrieving release artifact')
    r = requests.get("")
file = zipfile.ZipFile(BytesIO(r.content))
file.extractall()

package = str(r.url).split('/')[-1]

"""
Log the results into Cloudwatch
"""
logs = session.client('logs')

now = str(datetime.now().strftime("%m-%d-%Y_%H_%M"))

log_group = '' + args.env + ''


# Check if log group exists
group_list = logs.describe_log_groups(logGroupNamePrefix=log_group)['logGroups']
exists = False
for group in group_list:
    if group['logGroupName'] == log_group:
        exists = True
        break

if not exists:
    log_tags = {
        'ApplicationID': '390',
        'ApplicationName': 'biat',
        'Environment': args.env,
        'ProductOwnerEmail': 'crange@mmm.com',
        'AlternateEmail': 'mqduong@mmm.com',
        'ResourceCreator': 'rghosh2@mmm.com',
        'CountryCode': 'US'
    }
    logs.create_log_group(logGroupName=log_group, tags=log_tags)


error_log = now + '' + args.env + ''
success_log = now + '' + args.env + ''

"""
Run the migration.
"""
func.incremental_migration(args.account, awsrole, args.env, args.region, package, logs, log_group, error_log, success_log, now, 'SourceAssets/')