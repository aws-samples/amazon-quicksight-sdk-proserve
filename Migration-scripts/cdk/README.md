# BIOps: QuickSight Objects Migration and Version Control

Please refer to the AWS blogpost BIOps: QuickSight Objects Migration and Version Control for a complete walk-through.

## Prerequisites

For this walk-through, you should have the following prerequisites:

- Access to the following AWS services:
    - API Gateway
    - Amazon Athena
    - Lambda
    - QuickSight
    - Amazon SQS
    - Amazon S3
- Two different QuickSight accounts, such as development and production
- Basic knowledge of Python
- Basic AWS SDK knowledge
- Git and NPM installed
- CDK installed, see AWS CDK Intro Workshop: Python Workshop.

___

### Setup your environment

```bash
cd ~/amazon-quicksight-sdk-proserve/Migration-scripts/cdk/
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

___

### Deploy to central account

#### Deploy QuickSight Status and Migration stacks

```bash
export CDK_DEPLOY_ACCOUNT=CENTRAL_ACCOUNT_ID
export CDK_DEPLOY_REGION=CENTRAL_REGION
cdk bootstrap aws://CENTRAL_ACCOUNT_ID/TARGET_REGION
cdk deploy quicksight-status-stack quicksight-migration-stack
```

Note down the API Gateway endpoint from the output for a future step.

#### Create a dashboard

In the central account, you can run the following SQL query to create two Athena tables (group_membership and object_access):

```sql
CREATE EXTERNAL TABLE `group_membership`(
`namespace` string,   
`group` string, 
`user` string)
ROW FORMAT DELIMITED 
FIELDS TERMINATED BY ',' 
STORED AS INPUTFORMAT 'org.apache.hadoop.mapred.TextInputFormat' OUTPUTFORMAT 'org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat'
LOCATION 's3://quicksight-dash-<CENTRAL_ACCOUNT_ID>/monitoring/quicksight/group_membership/'
TBLPROPERTIES (
'areColumnsQuoted'='false', 
'classification'='csv', 
'columnsOrdered'='true', 
'compressionType'='none', 
'delimiter'=',',
'typeOfData'='file')

CREATE EXTERNAL TABLE `object_access`(
`aws_region` string,   
`object_type` string, 
`object_name` string,
`object_id` string,
`principal_type` string,
`principal_name` string,
`namespace` string,
`permissions` string)
ROW FORMAT DELIMITED 
FIELDS TERMINATED BY ',' 
STORED AS INPUTFORMAT 'org.apache.hadoop.mapred.TextInputFormat' OUTPUTFORMAT   'org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat'
LOCATION
's3://quicksight-dash-<CENTRAL_ACCOUNT_ID>/monitoring/quicksight/object_access/'
TBLPROPERTIES (
'areColumnsQuoted'='false', 
'classification'='csv', 
'columnsOrdered'='true', 
'compressionType'='none', 
  'delimiter'=',',
  'typeOfData'='file')
```

You can create a SPICE dataset in QuickSight with the two new Athena tables joined, and then, create a dashboard based on this dataset. You can refer to Using administrative dashboards for a centralized view of Amazon QuickSight objects for the detail.

#### Deploy QuickSight Embed stack

Update `DASHBOARD_ID` in `quicksight_embed_stack.py` file with the dashboard ID that you’ve just created above with the two joined Athena tables.

**Note:** For this POC, the `quicksight-embed-stack` creates a S3 public bucket to host the sample embedded QuickSight dashboard.

```bash
cdk deploy quicksight-embed-stack
```

In the `html/index.html` file, update the following `APIID` to the output value from QuicksightMigrationStack deployment step and QuicksightEmbedStack, then upload it to the S3 bucket (quicksight-embed-CENTRAL_ACCOUNT_ID) created by this stack:

- APIID of the embed URL endpoint – apiGatewayUrl: 'https://APIID.execute-api.us-east-1.amazonaws.com/prod/embedurl?'
- APIID of the migration endpoint – const apiGatewayUrl = 'https://APIID.execute-api.us-east-1.amazonaws.com/prod';

___

### Deploy to the target account(s)

**InfraTargetAccountStack** – Deploys an IAM role that can be assumed by the migration Lambda role. This stack should also be deployed to any target accounts that contain QuickSight resources.

**OptionalInfraTargetAccountStack** – Deploys Amazon Virtual Private Cloud (Amazon VPC), an Amazon Redshift cluster, and an Amazon Aurora cluster. This stack is optional and can be ignored if you have existing infrastructure for this POC. 

Update self.central_account_id = "123456789123" with the central account ID.

Update the `/infra/config` Systems Manager parameter with the values of your existing Amazon Redshift or RDS clusters. Set redshiftPassword and rdsPassword to the name of the secret found in Secrets Manager for these resources.

```bash
export CDK_DEPLOY_ACCOUNT=TARGET_ACCOUNT_ID
export CDK_DEPLOY_REGION=TARGET_REGION
cdk bootstrap aws://TARGET_ACCOUNT_ID/TARGET_REGION
cdk deploy infra-target-account-stack
```

Optionally, the optional-infra-stack deploys test Amazon Redshift and Amazon Relational Database Service (Amazon RDS) clusters in the target accounts:

```bash
cdk deploy optional-infra-target-account-stack
```

If OptionalInfraTargetAccountStack was deployed, update the `/infra/config` Systems Manager parameter with the values of your existing Amazon Redshift or RDS clusters. Set `redshiftPassword` and `rdsPassword` to the name of the secret found in Secrets Manager for these resources.

___

### Cleanup

#### Central account

```bash
cdk destroy quicksight-status-stack quicksight-migration-stack quicksight-embed-stack
```

#### Target account

```bash
cdk destroy infra-target-account-stack optional-infra-target-account-stack
```
