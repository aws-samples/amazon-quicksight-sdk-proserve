
import boto3, time
from typing import Any, Dict, List, Optional

# Step 1: Change this to the week start day you want all your analyses to use
NEW_WEEK_START = 'MONDAY'

success=[]
faillist=[]

sts_client = boto3.client('sts')
response = sts_client.assume_role(
        # Step 2: Change the RoleArn to one that has access to QuickSight
        RoleArn='arn:aws:iam::EXAMPLE_ACCOUNT_ID:role/EXAMPLE_ROLE',
        RoleSessionName='quicksight'
    )

session = boto3.Session(
        aws_access_key_id=response['Credentials']['AccessKeyId'],
        aws_secret_access_key=response['Credentials']['SecretAccessKey'],
        aws_session_token=response['Credentials']['SessionToken'],
        # Step 3: Change the region_name to where your account is located
        region_name="EXAMPLE_REGION" 
    )

def get_analysis(session):
    qs = session.client('quicksight')
    sts_client = session.client("sts")
    account_id = sts_client.get_caller_identity()["Account"]
    analysis = []
    response = qs.list_analyses(AwsAccountId=account_id)
    next_token: str = response.get("NextToken", None)
    analysis += response["AnalysisSummaryList"]

    while next_token is not None:
        response = qs.list_analyses(AwsAccountId=account_id, NextToken=next_token)
        next_token = response.get("NextToken", None)
        analysis += response["AnalysisSummaryList"]
    return analysis

def describe_analysis_definition(session, analysis):
    qs = session.client('quicksight')
    sts_client = session.client("sts")
    account_id = sts_client.get_caller_identity()["Account"]
    try:
        response = qs.describe_analysis_definition(
        AwsAccountId=account_id,
        AnalysisId=analysis)
    except Exception as e:
                return ('Failed to describe analysis: '+str(e))
    else: return response

def update_analysis(session, analysis, name, definition, themearn):
    qs = session.client('quicksight')
    sts_client = session.client("sts")
    account_id = sts_client.get_caller_identity()["Account"]

    if themearn == '':
        response = qs.update_analysis(
            AwsAccountId=account_id,
            AnalysisId=analysis,
            Name=name,
            Definition=definition
        )
    else:
        response = qs.update_analysis(
            AwsAccountId=account_id,
            AnalysisId=analysis,
            Name=name,
            Definition=definition,
            ThemeArn=themearn
        )        
    return response

def update_weekStart(session):
    analysis_list=get_analysis(session)

    analysis_all=[]
    for i in analysis_list:
        print
        if i["Status"]!= "DELETED":
            analysis_all.append(i["AnalysisId"])

    for analysis_id in analysis_all:
        print(analysis_id)
        analysis=describe_analysis_definition(session, analysis_id)

        if "Options" not in analysis["Definition"]:
            analysis["Definition"]["Options"] = {}
        
        analysis["Definition"]["Options"]["WeekStart"]=NEW_WEEK_START

        # Optional: Uncomment out line 94 to update all your analyses timezones
        # analysis["Definition"]["Options"]["Timezone"]="EXAMPLE_TIMEZONE"

        themeArn=""
        if "ThemeArn" in analysis.keys():
            themeArn=analysis["ThemeArn"]

        try:
            update_analysis(session, analysis_id, analysis["Name"], analysis["Definition"], themeArn)
        except Exception as e:
            faillist.append(res["AnalysisId"] + ", ")
            continue;

        time.sleep(20)
        res=describe_analysis_definition(session, analysis_id)
        if res["Status"]==200:
            status=res["ResourceStatus"]
            if status=="CREATION_SUCCESSFUL" or status=="UPDATE_SUCCESSFUL":
                success.append(res["AnalysisId"])
            else:
                faillist.append(res["AnalysisId"] + ", ")
    
    if faillist:
        print("Update failed for the following analysis ids: ")
        print(faillist)
    else:
        print("Successfully updated all analyses to use " + NEW_WEEK_START + " as week start day")

update_weekStart(session)



