# Steps to deploy the CloudFormation Template:
1. Deploy **admin_console_lambda.template**, and verify:
  - Check if a lambda function data_prepare is created
  - Check if a S3 bucket: admin-console<<AWS-account-ID>> is created
  - Check if the lambda function can run flawlessly
  - Check if /monitoring/quicksight/group_membership and /monitoring/quicksight/object_access folders are created in the S3 bucket above

2. Create [Cloudtrail](https://docs.aws.amazon.com/awscloudtrail/latest/userguide/cloudtrail-create-a-trail-using-the-console-first-time.html) log if it is not done yet. Note down the S3 bucket name.  
  
3. Note the outputs from step 1 and step 2. If the S3 bucket from step 2 is different from the one in Step 1's output, use the S3 bucket from step 2:
  
| Key | Value | Description |
| -------- | ------------- | ------------- |   
| cloudtraillog | s3://cloudtrail-awslogs-<<aws-account-id>>-do-not-delete/AWSLogs/<<aws-account-id>>/CloudTrail | The s3 location of cloudtrail log for you to utilize in next Athena tables creation stack |
| cloudtraillogtablename | cloudtrail_logs | The table name of cloudtrail log for you to utilize in next Athena tables creation stack |
| groupmembership | s3://admin-console<<aws-account-id>>/monitoring/quicksight/group_membership | The s3 location of group_membership.csv for you to utilize in next Athena tables creation stack |
| objectaccess | s3://admin-console<<aws-account-id>>/monitoring/quicksight/object_access | The s3 location of object_access.csv for you to utilize in next Athena tables creation stack |

4. Edit **admin_console_tables.json**: replace the corresponding fields by searching the key and replace the text with the value
  
5. Deploy **admin_console_athena_tables.json** as CFN template, and verify:
  - In Athena, check if a database with the name of **admin-console** is created in AwsDataCatalog
  - Three tables were created in the database, **cloudtrail_logs**, **group_membership**, **object_access**
  - Preview the tables from Athena
  - In QuickSight, go to security permissions, enable bucket access to s3://admin-console<<AWS-account-ID>> and s3://cloudtrail-awslogs-<<aws-account-id>>-do-not-delete
  - In Quicksight, enable Athena access
  - Verify QuickSight can access the tables through Athena
  
6. Deploy **admin_console_qs-objects.template**
  -- Check 

7. Set the SPICE refresh schedule
