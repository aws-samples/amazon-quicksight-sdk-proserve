"""
This script is for moving all assets from review to qa folder
Author: Andrew Kristanto
Email: akristanto@mmm.com
Version: Mar-07-2022
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
import json
import re
import argparse
from Assets_as_Code.src import functions as func
from Assets_as_Code.src import supportive_functions as s_func

# python -m Assets_as_Code.Deployment.qa_to_release --account 694267443573 --region us-east-1 --foldersrc 'arn:aws:quicksight:us-east-1:694267443573:folder/7978c2f6-87ca-4f0e-bb36-c42e9b91ff3b-Create-CDI' --foldertgt 'arn:aws:quicksight:us-east-1:694267443573:folder/550ddbdd-4f67-496f-9211-7504367e3e1e' --assetids 'f628cb2c-6210-4026-b71f-2a779b714a3a'
# python -m Assets_as_Code.Deployment.qa_to_release --account 694267443573 --region us-east-1 --ids Assets_as_Code/Deployment/Mapping/review_qa_release.json
def sanitize_args(args):
    for arg in vars(args):
        arg_input = getattr(args, arg)
        if isinstance(arg_input, str):
            if arg == "account":
                setattr(args, arg, re.sub(r"[^0-9]", "", arg_input))
            else:
                setattr(args, arg, re.sub(r"[^a-zA-Z0-9-_:\.\/]", "", arg_input))

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
    "--ids",
    required=True,
    help='Path to json of folder arns and assetids'
)

args = CLI.parse_args()
sanitize_args(args)

# Create session
awsrole = ""
session = s_func._assume_role(args.account, awsrole, args.region)

with open(args.ids, "r") as f:
    ids = json.load(f)

func.qa_to_release(session, ids)
