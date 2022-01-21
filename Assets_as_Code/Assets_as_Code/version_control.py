import boto3
import src.functions as func
import src.supportive_functions as s_func
import json

#load dev and prod account configuration
f = open('config/dev_configuration.json', )
dev_config = json.load(f)
f = open('config/prod_configuration.json', )
prod_config = json.load(f)

#start quicksight session
qs_session = s_func._assume_role(dev_config["aws_account_number"], dev_config["role_name"],  dev_config["aws_region"])


#res = func.describe_analysis_permissions(qs_session, 'copy_t_1')
#res = func.delete_analysis(qs_session, 'copy_t_1')
"""analysis_contents = func.describe_analysis_contents(qs_session, '0b35736a-fdc2-4d71-b561-7990de169acf')
file = open('exported_results/analysis.json', 'w')
file.write(str(analysis_contents))
file.close()"""



new_analysis = func.describe_analysis_contents(qs_session, 'copy_t_1')
file = open('exported_results/new_analysis.json', 'w')
file.write(str(new_analysis))
file.close()
f = open('library/2nd_class_assets/analysis_sheet_library.json')
l_s = json.load(f)
s_name = "Pie"

res = func.update_analysis(qs_session,'copy_t_1', 'copy_t_1', new_analysis, 'Sheets', l_s[s_name])
print(res)