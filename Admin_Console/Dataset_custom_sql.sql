-- Admin-Console-CFN-Main
SELECT COALESCE("d"."accountid", "l"."accountid")               "accountid"
     , COALESCE("d"."user_name", "l"."user_name", "g"."user")   "user_name"
     , "d"."awsregion"
     , "d"."dashboard_name"
     , "d"."dashboardId"
     , "d"."asset_type"
     , "d"."event_time"
     , "d"."latest_event_time"
     , "g"."namespace"
     , "g"."group"
     , "g"."email"
     , "g"."role"
     , "g"."identity_type"
     , "l"."firstlogin"
     , "l"."lastlogin"
     , COALESCE("do1"."principal_name", "do2"."principal_name") "owner_viewer"
     , COALESCE("do1"."ownership", "do2"."ownership")           "ownership"
FROM (((( (SELECT "useridentity"."accountid"
                , "useridentity"."type"
                , "split_part"("useridentity"."sessioncontext"."sessionissuer"."arn", '/', 2)    "assumed_role"
                , COALESCE(cast(json_extract("requestparameters", '$.roleSessionName') as varchar),
                           "concat"("split_part"("useridentity"."arn", '/', 2), '/',
                                    "split_part"("useridentity"."arn", '/', 3)))                 "user_name"
                , "awsregion"
                , "split_part"("split_part"("serviceeventdetails", 'analysisName":', 2), ',', 1) "dashboard_name"
                , "split_part"(
            "split_part"("split_part"("split_part"("serviceeventdetails", 'analysisId":', 2), ',', 1), 'analysis/',
                         2), '"}', 1)                                                            "dashboardId"
                , 'analysis'                                                                     "asset_type"
                , "date_parse"("eventtime", '%Y-%m-%dT%H:%i:%sZ')                                "event_time"
                , "max"("date_parse"("eventtime", '%Y-%m-%dT%H:%i:%sZ'))                         "latest_event_time"
           FROM "admin-console"."cloudtrail_logs"
           WHERE ((("eventsource" = 'quicksight.amazonaws.com') AND ("eventname" = 'GetAnalysis')) AND
                  ("date_trunc"('day', "date_parse"("eventtime", '%Y-%m-%dT%H:%i:%sZ')) >
                   CAST((current_date - INTERVAL '12' MONTH) AS date)))
           GROUP BY 1, 2, 3, 4, 5, 6, 7, 8, 9
           union
           SELECT "useridentity"."accountid"
                , "useridentity"."type"
                , "split_part"("useridentity"."sessioncontext"."sessionissuer"."arn", '/', 2)     "assumed_role"
                , COALESCE(cast(json_extract("requestparameters", '$.roleSessionName') as varchar),
                           "concat"("split_part"("useridentity"."arn", '/', 2), '/',
                                    "split_part"("useridentity"."arn", '/', 3)))                  "user_name"
                , "awsregion"
                , "split_part"("split_part"("serviceeventdetails", 'dashboardName":', 2), ',', 1) "dashboard_name"
                , "split_part"(
                   "split_part"("split_part"("split_part"("serviceeventdetails", 'dashboardId":', 2), ',', 1),
                                'dashboard/',
                                2), '"}', 1)                                                      "dashboardId"
                , 'dashboard'                                                                     "asset_type"
                , "date_parse"("eventtime", '%Y-%m-%dT%H:%i:%sZ')                                 "event_time"
                , "max"("date_parse"("eventtime", '%Y-%m-%dT%H:%i:%sZ'))                          "latest_event_time"
           FROM "admin-console"."cloudtrail_logs"
           WHERE ((("eventsource" = 'quicksight.amazonaws.com') AND ("eventname" = 'GetDashboard')) AND
                  ("date_trunc"('day', "date_parse"("eventtime", '%Y-%m-%dT%H:%i:%sZ')) >
                   CAST((current_date - INTERVAL '12' MONTH) AS date)))
           GROUP BY 1, 2, 3, 4, 5, 6, 7, 8, 9) d
    FULL JOIN (
        SELECT "user_name"
             , "accountid"
             , "min"("event_time") "firstlogin"
             , "max"("event_time") "lastlogin"
        FROM (SELECT "useridentity"."accountid"
                   , "useridentity"."type"
                   , "split_part"("useridentity"."sessioncontext"."sessionissuer"."arn", '/', 2)    "assumed_role"
                   , COALESCE(cast(json_extract("requestparameters", '$.roleSessionName') as varchar),
                              "concat"("split_part"("useridentity"."arn", '/', 2), '/',
                                       "split_part"("useridentity"."arn", '/', 3)))                 "user_name"
                   , "awsregion"
                   , "split_part"("split_part"("serviceeventdetails", 'analysisName":', 2), ',', 1) "dashboard_name"
                   , "split_part"(
                    "split_part"("split_part"("split_part"("serviceeventdetails", 'analysisId":', 2), ',', 1),
                                 'analysis/',
                                 2), '"}', 1)                                                       "dashboardId"
                   , 'analysis'                                                                     "asset_type"
                   , "date_parse"("eventtime", '%Y-%m-%dT%H:%i:%sZ')                                "event_time"
                   , "max"("date_parse"("eventtime", '%Y-%m-%dT%H:%i:%sZ'))                         "latest_event_time"
              FROM "admin-console"."cloudtrail_logs"
              WHERE ((("eventsource" = 'quicksight.amazonaws.com') AND ("eventname" = 'GetAnalysis')) AND
                     ("date_trunc"('day', "date_parse"("eventtime", '%Y-%m-%dT%H:%i:%sZ')) >
                      CAST((current_date - INTERVAL '12' MONTH) AS date)))
              GROUP BY 1, 2, 3, 4, 5, 6, 7, 8, 9
              union
              SELECT "useridentity"."accountid"
                   , "useridentity"."type"
                   , "split_part"("useridentity"."sessioncontext"."sessionissuer"."arn", '/', 2)     "assumed_role"
                   , COALESCE(cast(json_extract("requestparameters", '$.roleSessionName') as varchar),
                              "concat"("split_part"("useridentity"."arn", '/', 2), '/',
                                       "split_part"("useridentity"."arn", '/', 3)))                  "user_name"
                   , "awsregion"
                   , "split_part"("split_part"("serviceeventdetails", 'dashboardName":', 2), ',', 1) "dashboard_name"
                   , "split_part"(
                      "split_part"("split_part"("split_part"("serviceeventdetails", 'dashboardId":', 2), ',', 1),
                                   'dashboard/',
                                   2), '"}', 1)                                                      "dashboardId"
                   , 'dashboard'                                                                     "asset_type"
                   , "date_parse"("eventtime", '%Y-%m-%dT%H:%i:%sZ')                                 "event_time"
                   , "max"("date_parse"("eventtime", '%Y-%m-%dT%H:%i:%sZ'))                          "latest_event_time"
              FROM "admin-console"."cloudtrail_logs"
              WHERE ((("eventsource" = 'quicksight.amazonaws.com') AND ("eventname" = 'GetDashboard')) AND
                     ("date_trunc"('day', "date_parse"("eventtime", '%Y-%m-%dT%H:%i:%sZ')) >
                      CAST((current_date - INTERVAL '12' MONTH) AS date)))
              GROUP BY 1, 2, 3, 4, 5, 6, 7, 8, 9) sub1
        GROUP BY 1, 2
    ) l ON (("d"."user_name" = "l"."user_name") AND ("d"."accountid" = "l"."accountid")))
    FULL JOIN "admin-console".group_membership g
    ON (
            (("d"."accountid" = "g"."account_id") AND ("d"."user_name" = "g"."user"))
            OR
            (("l"."accountid" = "g"."account_id") AND ("l"."user_name" = "g"."user"))
        )
    )
    LEFT JOIN (
        SELECT *
        FROM (SELECT "account_id"
                   , "aws_region"
                   , "object_id"
                   , "object_name"
                   , "principal_type"
                   , "principal_name"
                   , "namespace"
                   , (CASE WHEN ("strpos"("permissions", 'Delete') <> 0) THEN 'Owner' ELSE 'Viewer' END) "Ownership"
              FROM "admin-console".object_access
              WHERE "object_type" = 'dashboard'
              GROUP BY 1, 2, 3, 4, 5, 6, 7, 8) sub2
        WHERE ("principal_type" = 'group')
    ) do1 ON ((((("d"."accountid" = "do1"."account_id") AND ("d"."awsregion" = "do1"."aws_region")) AND
                ("d"."dashboardId" = "do1"."object_id")) AND ("do1"."principal_name" = "g"."group")) AND
              ("do1"."namespace" = "g"."namespace")))
         LEFT JOIN (
    SELECT *
    FROM (SELECT "account_id"
               , "aws_region"
               , "object_id"
               , "object_name"
               , "principal_type"
               , "principal_name"
               , "namespace"
               , (CASE WHEN ("strpos"("permissions", 'Delete') <> 0) THEN 'Owner' ELSE 'Viewer' END) "Ownership"
          FROM "admin-console".object_access
          WHERE "object_type" = 'dashboard'
          GROUP BY 1, 2, 3, 4, 5, 6, 7, 8) sub3
    WHERE ("principal_type" = 'user')
) do2 ON ((((("d"."accountid" = "do2"."account_id") AND ("d"."awsregion" = "do2"."aws_region")) AND
            ("d"."dashboardId" = "do2"."object_id")) AND ("do2"."principal_name" = "d"."user_name")) AND
          ("do2"."namespace" = "g"."namespace")))
GROUP BY 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17;

-- Admin-Console-analysis-usage
select a.*,
       b.sheet_id,
       b.visual_id,
       b.datasetid,
       b.sheet_name,
       b.visual_type,
       b.analysis_name,
       d.dataset_name,
       d.spicesize,
       d.importmode
from (
         SELECT "useridentity"."accountid"
              , "useridentity"."type"
              , "split_part"("useridentity"."sessioncontext"."sessionissuer"."arn", '/', 2)               "assumed_role"
              , COALESCE("useridentity"."username", "concat"("split_part"("useridentity"."arn", '/', 2), '/',
                                                             "split_part"("useridentity"."arn", '/', 3))) "user_name"
              , "awsregion"
              , "split_part"("split_part"("serviceeventdetails", 'analysisName":', 2), ',', 1)            "analysisName"
              , "split_part"(
                 "split_part"("split_part"("split_part"("serviceeventdetails", 'analysisId":', 2), ',', 1), 'analysis/',
                              2), '"}', 1)                                                                "analysisId"
              , "date_parse"("eventtime", '%Y-%m-%dT%H:%i:%sZ')                                           "event_time"
--   , serviceeventdetails
              , "max"("date_parse"("eventtime", '%Y-%m-%dT%H:%i:%sZ'))                                    "latest_event_time"
         FROM "admin-console"."cloudtrail_logs"
         WHERE ((("eventsource" = 'quicksight.amazonaws.com') AND ("eventname" = 'GetAnalysis')) AND
                ("date_trunc"('day', "date_parse"("eventtime", '%Y-%m-%dT%H:%i:%sZ')) >
                 CAST((current_date - INTERVAL '3' MONTH) AS date)))
         GROUP BY 1, 2, 3, 4, 5, 6, 7, 8
     ) a
         join (select * from "admin-console"."datasets_analysis_visual") b
              on a.analysisId = b.analysisid
         join (select *
               from "admin-console"."dataset_attributes"
               where "event_time" = (select max("event_time") from "admin-console"."dataset_attributes")) d
              on b."datasetid" = d."datasetid";


-- Admin-Console-dashboard-visual-load-time
select a.*,
       b.time_stamp,
       b.avg_visual_load_time,
       c.count_visual_load_time,
       d.dataset_name,
       d.spicesize,
       d.importmode
from "admin-console"."datasets_dashboard_visual" a
         join "admin-console"."visual_load_time" b
              on a."dashboardid" = b."dashboardId"
                  and a."sheet_id" = b."sheetId"
                  and a."visual_id" = b."visualId"
         join "admin-console"."visual_load_count" c
              on b."dashboardId" = c."dashboardId"
                  and b."sheetId" = c."sheetId"
                  and b."visualId" = c."visualId"
                  and b."time_stamp" = c."time_stamp"
         join (select *
               from "admin-console"."dataset_attributes"
               where "event_time" = (select max("event_time") from "admin-console"."dataset_attributes")) d
              on a."datasetid" = d."datasetid";

-- Admin-Console-dataset-info
SELECT i.*,
       d."columnname",
       d."columntype",
       d."columndesc"
FROM "admin-console".datasets_info i
         join "admin-console".data_dict d
              on i.datasetid = d.datasetid;


-- Admin-Console-Object-Access
select o.account_id,
       o.aws_region,
       o.object_type,
       o.object_name,
       o.object_id,
       o.principal_type,
       o.principal_name,
       o.permissions,
       g.namespace,
       g.account_id as user_aws_account_id,
       g."group",
       g."user",
       g.email,
       g."role",
       g.identity_type
from "admin-console".object_access as o
         full outer join
     "admin-console".group_membership as g
     on o.account_id = g.account_id AND o.principal_name = g."group" AND o.namespace = g.namespace
where o.principal_type in ('group')
union all
select o.account_id,
       o.aws_region,
       o.object_type,
       o.object_name,
       o.object_id,
       o.principal_type,
       o.principal_name,
       o.permissions,
       g.namespace,
       g.account_id as user_aws_account_id,
       g."group",
       g."user",
       g.email,
       g."role",
       g.identity_type
from "admin-console".object_access o
         full outer join
     "admin-console".group_membership g
     on o.account_id = g.account_id AND o.principal_name = g.user AND o.namespace = g.namespace
where o.principal_type in ('user')

-- Admin-Console-Group-Membership
select *
from "admin-console".group_membership;

-- Admin-Console-Unused-Datasets-Reference
select alldatasets.*,
       datasets_asset_visual."assetid",
       datasets_asset_visual."asset_name",
       datasets_asset_visual."asset_type",
       datasets_asset_visual."sheet_id",
       datasets_asset_visual."sheet_name",
       datasets_asset_visual."visual_id",
       datasets_asset_visual."visual_type"
from (select *
      from "admin-console"."dataset_attributes"
      where "event_time" = (select max("event_time") from "admin-console"."dataset_attributes")) alldatasets
         left join
     (
         select "dashboardid"    as "assetid",
                "dashboard_name" as "asset_name",
                'dashboard'      as "asset_type",
                "sheet_id",
                "sheet_name",
                "visual_id",
                "visual_type",
                "datasetid"
         from "admin-console"."datasets_dashboard_visual"
         union
         select "analysisid"    as "assetid",
                "analysis_name" as "asset_name",
                'analysis'      as "asset_type",
                "sheet_id",
                "sheet_name",
                "visual_id",
                "visual_type",
                "datasetid"
         from "admin-console"."datasets_analysis_visual"
     ) datasets_asset_visual
     on alldatasets.datasetid = datasets_asset_visual.datasetid;


-- Admin-Console-Unused-Datasets-Query-History
select alldatasets."dataset_name",
       alldatasets."datasetid",
       alldatasets."spicesize",
       alldatasets."importmode",
       alldatasets."lastupdatedtime",
       asset_query_log."assetid",
       asset_query_log."asset_name",
       asset_query_log."asset_type",
       asset_query_log."sheet_id",
       asset_query_log."sheet_name",
       asset_query_log."visual_id",
       asset_query_log."visual_type",
       asset_query_log.event_time,
       asset_query_log.usage_count
from (select *
      from "admin-console"."dataset_attributes"
      where "event_time" = (select max("event_time") from "admin-console"."dataset_attributes")) alldatasets
         left join (select a."dashboardid"             as "assetid",
                           a."dashboard_name"          as "asset_name",
                           'dashboard'                 as "asset_type",
                           a."sheet_id",
                           a."sheet_name",
                           a."visual_id",
                           a."visual_type",
                           a."datasetid",
                           from_unixtime(b.time_stamp) as event_time,
                           b.count_visual_load_time    as usage_count
                    from "admin-console"."datasets_dashboard_visual" a
                             join "admin-console"."visual_load_count" b
                                  on a."dashboardid" = b."dashboardId"
                                      and a."sheet_id" = b."sheetId"
                                      and a."visual_id" = b."visualId"

                    union

                    select dav."analysisid"    as "assetid",
                           dav."analysis_name" as "asset_name",
                           'analysis'          as "asset_type",
                           dav.sheet_id,
                           dav.sheet_name,
                           dav.visual_id,
                           dav.visual_type,
                           dav.datasetid,
                           al."event_time",
                           1                   as usage_count
                    from (
                             SELECT "useridentity"."accountid"
                                  , "useridentity"."type"
                                  , "split_part"("useridentity"."sessioncontext"."sessionissuer"."arn", '/',
                                                 2)                                                      "assumed_role"
                                  , COALESCE("useridentity"."username",
                                             "concat"("split_part"("useridentity"."arn", '/', 2), '/',
                                                      "split_part"("useridentity"."arn", '/', 3)))       "user_name"
                                  , "awsregion"
                                  , "split_part"("split_part"("serviceeventdetails", 'analysisName":', 2), ',',
                                                 1)                                                      "analysisName"
                                  , "split_part"("split_part"("split_part"(
                                                                      "split_part"("serviceeventdetails", 'analysisId":', 2),
                                                                      ',', 1), 'analysis/', 2), '"}', 1) "analysisId"
                                  , "date_parse"("eventtime", '%Y-%m-%dT%H:%i:%sZ')                      "event_time"
--   , serviceeventdetails
                                  , "max"("date_parse"("eventtime", '%Y-%m-%dT%H:%i:%sZ'))               "latest_event_time"
                             FROM "admin-console"."cloudtrail_logs"
                             WHERE ((("eventsource" = 'quicksight.amazonaws.com') AND ("eventname" = 'GetAnalysis')) AND
                                    ("date_trunc"('day', "date_parse"("eventtime", '%Y-%m-%dT%H:%i:%sZ')) >
                                     CAST((current_date - INTERVAL '3' MONTH) AS date)))
                             GROUP BY 1, 2, 3, 4, 5, 6, 7, 8
                         ) al
                             join (select * from "admin-console"."datasets_analysis_visual") dav
                                  on al.analysisId = dav.analysisid) asset_query_log
                   on alldatasets.datasetid = asset_query_log.datasetid;

-- Admin-Console-Dataset-History
select *
from "admin-console"."dataset_attributes";


-- playground
select distinct analysisId
from (
         SELECT "useridentity"."accountid"
              , "useridentity"."type"
              , "split_part"("useridentity"."sessioncontext"."sessionissuer"."arn", '/', 2)               "assumed_role"
              , COALESCE("useridentity"."username", "concat"("split_part"("useridentity"."arn", '/', 2), '/',
                                                             "split_part"("useridentity"."arn", '/', 3))) "user_name"
              , "awsregion"
              , "split_part"("split_part"("serviceeventdetails", 'analysisName":', 2), ',', 1)            "analysisName"
              , "split_part"(
                 "split_part"("split_part"("split_part"("serviceeventdetails", 'analysisId":', 2), ',', 1), 'analysis/',
                              2), '"}', 1)                                                                "analysisId"
              , "date_parse"("eventtime", '%Y-%m-%dT%H:%i:%sZ')                                           "event_time"
--   , serviceeventdetails
              , "max"("date_parse"("eventtime", '%Y-%m-%dT%H:%i:%sZ'))                                    "latest_event_time"
         FROM "admin-console"."cloudtrail_logs"
         WHERE ((("eventsource" = 'quicksight.amazonaws.com') AND ("eventname" = 'GetAnalysis')) AND
                ("date_trunc"('day', "date_parse"("eventtime", '%Y-%m-%dT%H:%i:%sZ')) >
                 CAST((current_date - INTERVAL '3' MONTH) AS date)))
         GROUP BY 1, 2, 3, 4, 5, 6, 7, 8
     ) a;



select *
from (
         SELECT "eventtime"
              , "awsregion"
              , "sourceipaddress"
              , "concat"("split_part"("split_part"("resources"[1]."arn", ':', 6), '/', 2), '/',
                         "useridentity"."username") "username"
              , "resources"[1]."accountid"          "accountid"
         FROM "admin-console"."cloudtrail_logs"
         WHERE ("eventname" = 'AssumeRoleWithSAML')
         GROUP BY 1, 2, 3, 4, 5) a
where "username" = '';