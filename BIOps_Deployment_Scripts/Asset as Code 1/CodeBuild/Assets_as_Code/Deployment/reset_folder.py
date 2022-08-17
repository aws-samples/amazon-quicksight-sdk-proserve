"""
This script is for removing all assets from a quicksight folder
Author: Andrew Kristanto
Email: akristanto@mmm.com
Version: Jan-18-2021
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
import re
import argparse
from Assets_as_Code.src import functions as func
from Assets_as_Code.src import supportive_functions as s_func


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
    "--folder",
    required=True,
    help='Folder ARN to folder'
)

args = CLI.parse_args()
sanitize_args(args)

# Create session
awsrole = ""
session = s_func._assume_role(args.account, awsrole, args.region)

func.reset_folder(session, args.account, args.folder)
