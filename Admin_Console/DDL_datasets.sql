CREATE EXTERNAL TABLE `admin-console.data_dict`(
`dataset_name` string,
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
  'typeOfData'='file');


 CREATE EXTERNAL TABLE `admin-console.datasets_info`(
  `aws_region` string COMMENT 'from deserializer',
  `dashboard_name` string COMMENT 'from deserializer',
  `dashboardid` string COMMENT 'from deserializer',
  `analysis` string COMMENT 'from deserializer',
  `analysis_id` string COMMENT 'from deserializer',
  `dataset_name` string COMMENT 'from deserializer',
  `datasetid` string COMMENT 'from deserializer',
  `lastupdatedtime` string COMMENT 'from deserializer',
  `spicesize` string COMMENT 'from deserializer',
  `importmode` string COMMENT 'from deserializer',
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
  's3://<<bucket-name>>/monitoring/quicksight/datasets_info'
TBLPROPERTIES (
  'columnsOrdered'='true',
  'compressionType'='none',
  'delimiter'='|',
  'transient_lastDdlTime'='1619204644',
  'typeOfData'='file')

CREATE EXTERNAL TABLE `admin-console.dataset_attributes`(
`dataset_name` string,
`datasetid` string,
`spicesize` string,
`importmode` string,
`lastupdatedtime` string,
`event_epoch_time` int
)
ROW FORMAT DELIMITED
  FIELDS TERMINATED BY ','
STORED AS INPUTFORMAT
  'org.apache.hadoop.mapred.TextInputFormat'
OUTPUTFORMAT
  'org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat'
LOCATION
  's3://<<bucket-name>>/monitoring/quicksight/dataset_attributes/'
TBLPROPERTIES (
  'areColumnsQuoted'='false',
  'classification'='csv',
  'columnsOrdered'='true',
  'compressionType'='none',
  'delimiter'=',',
  'typeOfData'='file');
