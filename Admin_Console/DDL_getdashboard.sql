CREATE OR REPLACE VIEW getdashboard AS 
(SELECT 
"useridentity"."type",   "split_part"("useridentity"."sessioncontext"."sessionissuer"."arn",'/', 2) AS "assumed_role", COALESCE("useridentity"."username","concat"("split_part"("userid
entity"."arn", '/', 2), '/', "split_part"("useridentity"."arn",
'/', 3))) AS "user_name",
awsregion,
"split_part"("split_part"("serviceeventdetails", 'dashboardName":', 2),',', 1) AS dashboard_name, "split_part"("split_part"("split_part"("split_part"("serviceeventdetails", 'dashboardId":', 2),',', 1), 'dashboard/', 2),'"}',1) AS dashboardId,
date_parse(eventtime, '%Y-%m-%dT%H:%i:%sZ') AS event_time, max(date_parse(eventtime, '%Y-%m-%dT%H:%i:%sZ')) AS latest_event_time
FROM cloudtrail_logs
WHERE 
eventsource = 'quicksight.amazonaws.com' 
AND
eventname = 'GetDashboard' 
AND
DATE_TRUNC('day',date_parse(eventtime, '%Y-%m-%dT%H:%i:%sZ')) > cast(current_date - interval '3' month AS date)
GROUP BY  1,2,3,4,5,6,7)