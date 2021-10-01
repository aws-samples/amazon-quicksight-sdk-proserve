CREATE EXTERNAL TABLE `admin_console.data_dict`(
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
  's3://administrative-dashboard624969228231/monitoring/quicksight/data_dictionary/'
TBLPROPERTIES (
  'areColumnsQuoted'='false',
  'classification'='csv',
  'columnsOrdered'='true',
  'compressionType'='none',
  'delimiter'=',',
  'typeOfData'='file')