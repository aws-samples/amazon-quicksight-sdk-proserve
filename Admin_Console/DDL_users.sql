CREATE OR REPLACE VIEW users AS
(select Namespace,
 Group,
 User,
(case 
when Group in ('quicksight-fed-bi-developer', 'quicksight-fed-bi-admin') 
then 'Author' 
else 'Reader' 
end) 
as author_status
from "group_membership" )