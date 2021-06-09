# Steps to deploy the CloudFormation Template:
1. Deploy **admin_console_lambda.template**, and verify:
- Check if a lambda function data_prepare is created
- Check if a S3 bucket: admin-console<<AWS-account-ID>> is created
- Check if the lambda function can run flawlessly
- Check if /monitoring/quicksight/group_membership and /monitoring/quicksight/object_access folders are created in the S3 bucket above

2. Note the outputs from step 1, and replace corresponding values in **admin-console-athena-tables.json**:
|Key|Value|Description
|cloudtraillog|s3://cloudtrail-awslogs-<<aws-account-id>>-do-not-delete/AWSLogs/<<aws-account-id>>/CloudTrail|The s3 location of cloudtrail log for you to utilize in next Athena tables creation stack
|cloudtraillogtablename|cloudtrail_logs|The table name of cloudtrail log for you to utilize in next Athena tables creation stack
|groupmembership|s3://admin-console<<aws-account-id>>/monitoring/quicksight/group_membership|The s3 location of group_membership.csv for you to utilize in next Athena tables creation stack
|objectaccess|s3://admin-console<<aws-account-id>>/monitoring/quicksight/object_access|The s3 location of object_access.csv for you to utilize in next Athena tables creation stack

Key             Value                                                                               Description
cloudtraillog	s3://cloudtrail-awslogs-<<aws-account-id>>-do-not-delete/AWSLogs/<<aws-account-id>>/CloudTrail	The s3 location of cloudtrail log for you to utilize in next Athena tables creation stack	-
cloudtraillogtablename	cloudtrail_logs	The table name of cloudtrail log for you to utilize in next Athena tables creation stack	-
groupmembership	s3://admin-console<<aws-account-id>>/monitoring/quicksight/group_membership	The s3 location of group_membership.csv for you to utilize in next Athena tables creation stack	-
objectaccess	s3://admin-console<<aws-account-id>>/monitoring/quicksight/object_access	The s3 location of object_access.csv for you to utilize in next Athena tables creation stack
3. Create cloudtrail log: https://docs.aws.amazon.com/awscloudtrail/latest/userguide/cloudtrail-create-a-trail-using-the-console-first-time.html. Note down the S3 bucket name if it is different from the outputs in step 2. 
4. Edit admin_console_tables.json: replace the corresponding fields by searching the key and replace the text with the value
5. Deploy admin_console_athena_tables.json as CFN template
6. In quicksight UI, go to security permissions, enable S3 access of both cloudtrail bucket (cloudtrail-awslogs-<<aws-account-id>>-do-not-delete) and the lambda output buckets (admin-console<<aws-account-id>>). Enable athena access.
7. Deploy admin_console_qs-objects.template
8. Set the SPICE refresh schedule
