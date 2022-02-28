# Centralized granular access control in Amazon QuickSight

Please follow the step by step tutorial in here: https://aws.amazon.com/blogs/big-data/build-a-centralized-granular-access-control-to-manage-assets-and-data-access-in-amazon-quicksight/

## Prerequisites

For this walkthrough, you should have the following prerequisites:

- A QuickSight Enterprise account
- Basic knowledge of Python
- Basic knowledge of SQL
- Basic knowledge of BI
- The AWS CDK installed (see AWS CDK Intro Workshop: Python Workshop)
- Access to the following AWS services:
    1. Amazon QuickSight
    2. Amazon Athena
    3. AWS Lambda
    4. Amazon S3 

***

### Create Resources
Create your resources by cloning the following AWS CDK stack from the [GitHub repo](https://github.com/aws-samples/amazon-quicksight-sdk-proserve/tree/master/granular_access)
```bash
git clone https://github.com/aws-samples/amazon-quicksight-sdk-proserve.git ~/amazon-quicksight-sdk-proserve
```

***

### Set up your environment
Set up your environment with the following code
```bash
cd ~/amazon-quicksight-sdk-proserve/granular-access/
source .venv/bin/activate
pip install -r requirements.txt
```

***

### Deployment
Deploy the granular access using the following code
```bash
cdk bootstrap
cdk deploy granular-access
```
After successfully deploying the stack, verify:
- If a ‘check_team_members’ lambda function is created
- If a ‘downgrade_user’ lambda function is created
- If a ‘granular_access_assets_governance’ lambda function is created
- If a ‘granular_user_governance’ lambda function is created
- If a ‘user_init’ lambda function is created
- If a S3 bucket: qs-granular-access-demo-[Account ID] is created
- If a ‘Membership’ and ‘Monitoring’ folders are created in the above S3 bucket
- Additionally, following supporting resources are created after deploying the stack
    - /qs/config/access
    - /qs/config/groups
    - /qs/config/ns
    - /qs/config/roles

### Access setup
- Set the destination of ‘granular_user_governance’ to another Lambda function, ‘downgrade_user’ with ‘source=Asynchronous invocation’ and ‘condition=On Success’
- Set the destination of ‘downgrade_user’ to the Lambda function, ‘granular_access_assets_govenance’ with ‘source=Asynchronous invocation’ and ‘condition=On Success’.
- Set the destination of ‘downgrade_user’ to the Lambda function ‘check_team_members’ with ‘source=Asynchronous invocation’ and ‘condition=On Failure’.

The ‘check_team_members’ function simply calls QuickSight APIs to get the namespaces, groups, users, and assets information, and saves the results in the S3 bucket. The S3 key is ‘monitoring/quicksight/group_membership/group_membership.csv’ and ‘monitoring/quicksight/object_access/object_access.csv’.
Besides the two output files of the previous step, the error logs and user deletion logs (logs of ‘downgrade_user’) are also saved in the ‘monitoring/quicksight’ folder.
- Set the destination of ‘granular_access_assets_govenance’ to the Lambda function ‘check_team_members’ with ‘source=Asynchronous invocation’ and ‘condition=On Success’ or ‘condition=On Failure’.

***

## Create row-level security datasets

### Create Athena table

Run the following SQL query to create an Athena table (membership):

```sql
CREATE EXTERNAL TABLE `mem`(
  `namespace` string, 
  `group` string, 
  `username` string, 
  `email` string)
ROW FORMAT DELIMITED 
  FIELDS TERMINATED BY ',' 
STORED AS INPUTFORMAT 
  'org.apache.hadoop.mapred.TextInputFormat' 
OUTPUTFORMAT 
  'org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat'
LOCATION
  's3://qs-granular-access-demo-<ACCOUNT ID>/membership'
TBLPROPERTIES (
  'has_encrypted_data'='false'
```

Run the following SQL query to create a view called ‘rls’ for an RLS dataset:

```sql
create view
rls(groupname, username, country, city)
as
(SELECT 
concat('quicksight-fed-'::text, lower(employee_information.country::text)) AS groupname,
concat(concat('quicksight-fed-us-users/'::text, employee_information.employee_login::text),'@oktank.com'::text) AS username,
employee_information.country,
employee_information.city
FROM 
employee_information)
```

Create an RLS dataset using custom SQL:

```sql
select distinct 
r.groupname as GroupName,
null as UserName,
r.country,
null as city 
from 
rls as r 
join fact_revenue as f 
on r.country=f.country
union
select distinct 'quicksight-fed-all-countries' as GroupName,
null as UserName,
null as country,
null as city
from rls as r
union
select distinct null as GroupName,
r.username as UserName,
r.country,
r.city 
from 
rls as r
join fact_revenue as f 
on r.country=f.country 
and 
r.city=f.city
```

In QuickSight, multiple rules in an RLS dataset are combined together with OR. With these multi-faceted RLS rules, we can define a comprehensive data access pattern.

***

## Clean up
To avoid incurring future charges, delete the resources you created by running the following command:
```bash
cdk destroy granular_access
```



