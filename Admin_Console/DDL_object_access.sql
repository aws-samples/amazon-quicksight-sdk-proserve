CREATE EXTERNAL TABLE `object_access`(
`aws_region` string,
`object_type` string,
`object_name` string,
`object_id` string,
`principal_type` string,
`principal_name` string,
`namespace` string,
`permissions` string
)
ROW FORMAT DELIMITED
  FIELDS TERMINATED BY ','
STORED AS INPUTFORMAT
  'org.apache.hadoop.mapred.TextInputFormat'
OUTPUTFORMAT   'org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat'
LOCATION
  's3:// admin-console<aws_account_id>/monitoring/quicksight/object_access/'
TBLPROPERTIES (
  'areColumnsQuoted'='false',
  'classification'='csv',
  'columnsOrdered'='true',
  'compressionType'='none',
  'delimiter'=',',
  'typeOfData'='file')