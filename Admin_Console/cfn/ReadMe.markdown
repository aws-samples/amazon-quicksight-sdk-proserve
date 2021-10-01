# Steps to deploy the CloudFormation Templates:
## 1. Deploy *admin_console_lambda.template*, and verify:
  - Check if a lambda function data_prepare is created
  - Check if a S3 bucket: admin-console[AWS-account-ID] is created
  - Check if the lambda function can run flawlessly
  - Check if /monitoring/quicksight/group_membership and /monitoring/quicksight/object_access folders are created in the S3 bucket above

## 2. Create [Cloudtrail](https://docs.aws.amazon.com/awscloudtrail/latest/userguide/cloudtrail-create-a-trail-using-the-console-first-time.html) log if it is not done yet. Note down the S3 bucket name.  
  
## 3. Note the outputs from step 1 and step 2. If the cloudtraillog S3 bucket from step 2 is different from the one in Step 1's output, use the S3 bucket from step 2:
  
| Key | Value | Description |
| -------- | ------------- | ------------- |   
| cloudtraillog | s3://cloudtrail-awslogs-[aws-account-id]-do-not-delete/AWSLogs/[aws-account-id]/CloudTrail | The s3 location of cloudtrail log for you to utilize in next Athena tables creation stack |
| cloudtraillogtablename | cloudtrail_logs | The table name of cloudtrail log for you to utilize in next Athena tables creation stack |
| groupmembership | s3://admin-console[aws-account-id]/monitoring/quicksight/group_membership | The s3 location of group_membership.csv for you to utilize in next Athena tables creation stack |
| objectaccess | s3://admin-console[aws-account-id]/monitoring/quicksight/object_access | The s3 location of object_access.csv for you to utilize in next Athena tables creation stack |
| dataset_info | s3://admin-console[aws-account-id]/monitoring/quicksight/datsets_info | The s3 location of datsets_info.csv for you to utilize in next Athena tables creation stack |
| data_dictionary | s3://admin-console[aws-account-id]/monitoring/quicksight/data_dictionary | The s3 location of data_dictionary.csv for you to utilize in next Athena tables creation stack |

## 4. Edit *admin_console_tables.json*: replace the corresponding fields by searching the key and replace the text with the value
  
## 5. Deploy *admin_console_athena_tables.json* as CFN template, and verify:
  - In Athena, check if a database with the name of **admin-console** is created in AwsDataCatalog
  - Three tables were created in the database, **cloudtrail_logs**, **group_membership**, **object_access**
  - Preview the tables from Athena
  - Run this DDL to create dataset_info table: 
  
```sql
    CREATE EXTERNAL TABLE `admin-console.datasets_info`(
  `aws_region` string COMMENT 'from deserializer', 
  `dashboard_name` string COMMENT 'from deserializer', 
  `dashboardid` string COMMENT 'from deserializer', 
  `analysis` string COMMENT 'from deserializer', 
  `analysis_id` string COMMENT 'from deserializer', 
  `dataset_name` string COMMENT 'from deserializer', 
  `dataset_id` string COMMENT 'from deserializer', 
  `lastupdatedtime` string COMMENT 'from deserializer', 
  `data_source_name` string COMMENT 'from deserializer', 
  `data_source_id` string COMMENT 'from deserializer', 
  `catalog` string COMMENT 'from deserializer', 
  `sqlname/schema` string COMMENT 'from deserializer', 
  `sqlquery/table_name` string COMMENT 'from deserializer')
ROW FORMAT DELIMITED 
  FIELDS TERMINATED BY '|' 
STORED AS INPUTFORMAT 
  'org.apache.hadoop.mapred.TextInputFormat' 
OUTPUTFORMAT 
  'org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat'
LOCATION
  's3://<<bucket-name>>/monitoring/quicksight/datsets_info'
TBLPROPERTIES (
  'columnsOrdered'='true', 
  'compressionType'='none', 
  'delimiter'='|', 
  'transient_lastDdlTime'='1619204644', 
  'typeOfData'='file')
 ``` 
  - Run this DDL to create dataset_dict table: 
  
```sql
CREATE EXTERNAL TABLE `admin-console.data_dict`(
`datasetname` string,
`datasetid` string,
`columnname` string,
`columntype` string,
`columndesc` string)
ROW FORMAT DELIMITED
  FIELDS TERMINATED BY ','
STORED AS INPUTFORMAT
  'org.apache.hadoop.mapred.TextInputFormat'
OUTPUTFORMAT
  'org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat'
LOCATION
  's3://<<bucket-name>>/monitoring/quicksight/data_dictionary/'
TBLPROPERTIES (
  'areColumnsQuoted'='false',
  'classification'='csv',
  'columnsOrdered'='true',
  'compressionType'='none',
  'delimiter'=',',
  'typeOfData'='file')
```
  - In QuickSight, go to security permissions, enable bucket access to s3://admin-console[AWS-account-ID] and s3://cloudtrail-awslogs-[aws-account-id]-do-not-delete
  - In QuickSight, enable Athena access
  - Verify QuickSight can access the tables through Athena

## 6. Get QuickSight admin user's ARN, this is a required parameter for the next step
  ```
  aws quicksight describe-user --aws-account-id [aws-account-id] --namespace default --user-name [admin-user-name]
  ```
  
## 7. Deploy *admin_console_qs-objects.template*, using QuickSight admin user's ARN from last step
  - Check if three SPICE datesets created in this step are successfully imported
  - If modifying the dashboard is preferred, enable dashboard save-as option, then recreate the analysis, make modification, and publish a new dashboard

## 8. Set preferred SPICE refresh schedule for three SPICE datasets, and share the dashboard in your organization properly
