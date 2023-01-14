CREATE EXTERNAL TABLE `admin-console.datasets_dashboard_visual`(
`dashboardid` string,
`dashboard_name` string,
`sheet_id` string,
`sheet_name` string,
`visual_id` string,
`visual_type` string,
`datasetid` string)
ROW FORMAT DELIMITED
  FIELDS TERMINATED BY ','
STORED AS INPUTFORMAT
  'org.apache.hadoop.mapred.TextInputFormat'
OUTPUTFORMAT
  'org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat'
LOCATION
  's3://<<bucket-name>>/monitoring/quicksight/datasets_dashboard_visual/'
TBLPROPERTIES (
  'areColumnsQuoted'='false',
  'classification'='csv',
  'columnsOrdered'='true',
  'compressionType'='none',
  'delimiter'=',',
  'typeOfData'='file');


CREATE EXTERNAL TABLE `admin-console.datasets_analysis_visual`(
`analysisid` string,
`analysis_name` string,
`sheet_id` string,
`sheet_name` string,
`visual_id` string,
`visual_type` string,
`datasetid` string)
ROW FORMAT DELIMITED
  FIELDS TERMINATED BY ','
STORED AS INPUTFORMAT
  'org.apache.hadoop.mapred.TextInputFormat'
OUTPUTFORMAT
  'org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat'
LOCATION
  's3://<<bucket-name>>/monitoring/quicksight/datasets_analysis_visual/'
TBLPROPERTIES (
  'areColumnsQuoted'='false',
  'classification'='csv',
  'columnsOrdered'='true',
  'compressionType'='none',
  'delimiter'=',',
  'typeOfData'='file');


CREATE EXTERNAL TABLE `admin-console.visual_load_time`(
`time_stamp` int,
`dashboardId` string,
`sheetId` string,
`visualId` string,
`avg_visual_load_time` double
    )
ROW FORMAT DELIMITED
  FIELDS TERMINATED BY ','
STORED AS INPUTFORMAT
  'org.apache.hadoop.mapred.TextInputFormat'
OUTPUTFORMAT
  'org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat'
LOCATION
  's3://<<bucket-name>>/monitoring/quicksight/visual_load_time/'
TBLPROPERTIES (
  'areColumnsQuoted'='false',
  'classification'='csv',
  'columnsOrdered'='true',
  'compressionType'='none',
  'delimiter'=',',
  'typeOfData'='file');


CREATE EXTERNAL TABLE `admin-console.visual_load_count`(
`time_stamp` int,
`dashboardId` string,
`sheetId` string,
`visualId` string,
`count_visual_load_time` double
    )
ROW FORMAT DELIMITED
  FIELDS TERMINATED BY ','
STORED AS INPUTFORMAT
  'org.apache.hadoop.mapred.TextInputFormat'
OUTPUTFORMAT
  'org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat'
LOCATION
  's3://<<bucket-name>>/monitoring/quicksight/visual_load_count/'
TBLPROPERTIES (
  'areColumnsQuoted'='false',
  'classification'='csv',
  'columnsOrdered'='true',
  'compressionType'='none',
  'delimiter'=',',
  'typeOfData'='file');