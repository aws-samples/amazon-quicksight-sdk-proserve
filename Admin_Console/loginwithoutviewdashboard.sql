CREATE OR REPLACE VIEW "loginwithoutviewdashboard" AS
with login as
(SELECT COALESCE("useridentity"."username", "split_part"("useridentity"."arn", '/', 3)) AS "user_name", awsregion,
date_parse(eventtime, '%Y-%m-%dT%H:%i:%sZ') AS event_time
FROM cloudtrail_logs
WHERE
eventname = 'AssumeRoleWithSAML'
GROUP BY  1,2,3),
dashboard as
(SELECT COALESCE("useridentity"."username", "split_part"("useridentity"."arn", '/', 3)) AS "user_name", awsregion,
date_parse(eventtime, '%Y-%m-%dT%H:%i:%sZ') AS event_time
FROM cloudtrail_logs
WHERE
eventsource = 'quicksight.amazonaws.com'
AND
eventname = 'GetDashboard'
GROUP BY  1,2,3),
users as
(select Namespace,
Group,
User,
(case
when Group in (‘quicksight-fed-bi-developer’, ‘quicksight-fed-bi-admin’)
then ‘Author’
else ‘Reader’
end)
as author_status
from "group_membership" )
select l.*
from login as l
join dashboard as d
join users as u
on l.user_name=d.user_name
and
l.awsregion=d.awsregion
and
l.user_name=u.user_name
where d.event_time>(l.event_time + interval '30' minute )
and
d.event_time<l.event_time
and
u.author_status='Reader'