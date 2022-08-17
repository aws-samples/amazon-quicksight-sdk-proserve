from pickle import TRUE
import argparse
import boto3
from datetime import datetime
from io import BytesIO
import json
import os
from os import listdir
import re
import requests
import shutil
import sys
import tarfile
import zipfile

# Usage: python build_credential_package.py --account  --region 'us-east-1' --partition 'aws' --db_version 1 --reports_version 1 --commit '' --cred_version '1.0.0'

def sanitize_args(args):
    for arg in vars(args):
        arg_input = getattr(args, arg)
        if isinstance(arg_input, str):
            if arg == "account":
                setattr(args, arg, re.sub(r"[^0-9]", "", arg_input))
            else:
                setattr(args, arg, re.sub(r"[^a-zA-Z0-9-\.\/]", "", arg_input))

#session construction
def _assume_role(role_arn, aws_region):
    sts_client = boto3.client('sts')
    response = sts_client.assume_role(
        RoleArn=role_arn,
        RoleSessionName='quicksight'
    )
    # Storing STS credentials
    session = boto3.Session(
        aws_access_key_id=response['Credentials']['AccessKeyId'],
        aws_secret_access_key=response['Credentials']['SecretAccessKey'],
        aws_session_token=response['Credentials']['SessionToken'],
        region_name=aws_region
    )

    print("Assumed session for " + role_arn + " in region " + aws_region + ".")
    return session

#tar a directory
def tardir(path, tar_name):
    with tarfile.open(tar_name, "w:gz") as tar_handle:
        for root, dirs, files in os.walk(path):
            for file in files:
                tar_handle.add(os.path.join(root, file))

CLI = argparse.ArgumentParser()
CLI.add_argument(
    "--account",
    required=True,
    help='Environment Account ID'
)
CLI.add_argument(
    "--region",
    required=False,
    help='AWS Region for DB connections',
    default='us-east-1'
)
CLI.add_argument(
    "--partition",
    required=True,
    help='The aws partition.',
)
CLI.add_argument(
    "--db_version",
    required=False,
    help='Database version',
    default='1'
)
CLI.add_argument(
    "--reports_version",
    required=False,
    help='Reports version',
    default='2'
)
CLI.add_argument(
    "--commit",
    required=False,
    help='Commit hash'
)
CLI.add_argument(
    "--cred_version",
    required=False,
    help='Credential version',
    default='1.0.0'
)

args = CLI.parse_args()
sanitize_args(args)
print('Print all arguments: ', sys.argv[1:])

# Create session
role_arn = "arn:" + args.partition + ":iam::" + args.account + ":role/"
session = _assume_role(role_arn, args.region)
sm = session.client('secretsmanager')
secret = json.loads(sm.get_secret_value(SecretId='')['SecretString'])

# retrieving QA artifact artifacts
print('Starting QS artifact download...')
urlQS = '' + args.reports_version + '/asset-model-' + args.reports_version + '.zip'
rQS = requests.get(urlQS)

print("Download of QS artifact complete. Extracting the zip file contents...")
qsfile = zipfile.ZipFile(BytesIO(rQS.content))
qsfile.extractall('./credential_build')
print('Extracting QS artifact complete.')

# Retrieving DB artifact
print('Starting DB artifact download...')
urlDB='' + args.db_version + '/redshift-' + args.db_version + '.gzip'
rDB = requests.get(urlDB, stream=TRUE)
print("Download of DB artifact complete. Extracting the zip file contents...")

dbfile = tarfile.open(fileobj=rDB.raw, mode="r|gz")
dbfile.extractall('./credential_build')
print('Extracting DB artifact complete.')
dbfile.close()

# retrieving Middleware-py artifacts
print('Starting Middleware artifact download...')
urlMW = ""
rMW = requests.get(urlMW)

print("Download of Middleware artifact complete. Extracting the zip file contents...")
mwfile_name = urlMW.split('/')[-1]
open('./credential_build/' + mwfile_name, 'wb').write(rMW.content)

# Add middleware-py file to requirements.txt
with open('./credential_build/requirements.txt', 'a') as f:
    f.write('\n' + mwfile_name)

#print list of everything that will be added to the tar.gz artifact
print("Credential build directory list: ", listdir("./credential_build"))

# Set version
dt = datetime.now().strftime('%Y%m%d%H%M%S')
version = args.cred_version + '-' + args.commit[:7] + '-' + dt
print("version: ", version)

# Zip directory
shutil.make_archive(
    'EnterpriseAnalytics' + version, 
    'zip', 
    base_dir='credential_build'
)

# Upload to Nexus
params = (
    ('repository', ''),
)
files = {
    'maven2.groupId': (None, '),
    'maven2.artifactId': (None, 'ea_credentialing'),
    'maven2.version': (None, version),
    'maven2.asset1': ('EnterpriseAnalytics' + version + '.zip', open('EnterpriseAnalytics' + version + '.zip', 'rb')),
    'maven2.asset1.extension': (None, 'zip')
}

response = requests.post('', params=params,
                             files=files, auth=(secret['username'], secret['password']))
print('Uploading package to Nexus...')
if response.status_code == 204:
    print('Upload successful')
else:
    print(response)
    print(response.reason)
