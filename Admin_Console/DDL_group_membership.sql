CREATE EXTERNAL TABLE `group_membership`(
`namespace` string,
`group` string,
`user` string)
ROW FORMAT DELIMITED
  FIELDS TERMINATED BY ','
STORED AS INPUTFORMAT
  'org.apache.hadoop.mapred.TextInputFormat'
OUTPUTFORMAT
  'org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat'
LOCATION
  's3:// admin-console<aws_account_id>/monitoring/quicksight/group_membership/'
TBLPROPERTIES (
  'areColumnsQuoted'='false',
  'classification'='csv',
  'columnsOrdered'='true',
  'compressionType'='none',
  'delimiter'=',',
  'typeOfData'='file')