"""
This script is for dev/admin to run unit test
"""


import boto3
import src.functions as func

aws_account_number = '889399602426'
role_name = 'admin'
aws_region = 'us-east-1'

sts_client = boto3.client('sts')
response = sts_client.assume_role(
        RoleArn='arn:aws:iam::' + aws_account_number + ':role/' + role_name,
        RoleSessionName='quicksight'
    )
# Storing STS credentials
session = boto3.Session(
        aws_access_key_id=response['Credentials']['AccessKeyId'],
        aws_secret_access_key=response['Credentials']['SecretAccessKey'],
        aws_session_token=response['Credentials']['SessionToken'],
        region_name=aws_region
    )
"""
analysis = '54f9584c-f332-4202-a05a-9d64104d7191'

analysis_contents = func.describe_analysis_contents(session, analysis)

file = open('exported_results/analysis.json', 'w')
file.write(str(analysis_contents))
file.close()

new = func.copy_analysis(session, analysis_contents, 'copy_t_1', 'copy_t_1', 'arn:aws:quicksight:us-east-1:889399602426:user/default/Administrator/wangzyn-Isengard')
#copy_analysis(session, source, Id, Name, principal, Permissions = 'owner', region='us-east-1'):
#analysis_contents = analysis_contents['Analysis']
print(new)
file = open('exported_results/analysis.json', 'w')
file.write(str(analysis_contents))
file.close()
"""
#get contents from the sample analysis
#analysis = func.describe_analysis_contents(session, 'copy_t_1')

#get sheets from the sample analysis
#sheets = func.get_sheets(session, analysisid)

#get caclulated fields from the sample analysis
#cf =
#get caclulated fields from the sample analysis
parameter = func.get_parameter(session, "0b35736a-fdc2-4d71-b561-7990de169acf", 'analysis', 'Country')
file = open('exported_results/new_parameter.json', 'w')
file.write(str(parameter))
file.close()


#file = open('exported_results/sheets.json', 'w')
#file.write(str(sheets))
#file.close()
