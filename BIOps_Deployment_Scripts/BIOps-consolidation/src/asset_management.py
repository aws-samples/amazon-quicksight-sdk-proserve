
"""
Asset management is a module of functions to interact with QuickSight assets that is in code (files in JSON format).
QuickSight assets include: dataset definition, analysis definition, dashboard definition, etc.
"""


def add_asset_in_library(session, input_id, input_type, out_put_name, out_put_type):
    if out_put_type == 'parameter':
        lib = '../library/2nd_class_assets/parameter_library.json'
        new = get_parameter(session, input_id, input_type, out_put_name)
        write_lib(out_put_name, new, lib)
    if (input_type == 'analysis' and out_put_type == 'cf'):
        lib = '../library/2nd_class_assets/analysis_cf_library.json'
        new = get_cfs(session, input_id, input_type, out_put_name)
        write_lib(out_put_name, new, lib)
    if out_put_type == 'analysis':
        lib_def = '../library/1st_class_assets/analysis/' + out_put_name + '_Definition.json'
        lib = '../library/1st_class_assets/analysis/' + out_put_name + '.json'
        new = describe_analysis_definition(session, input_id)
        # print(new)
        file = open(lib_def, 'w')
        file.write(str(new['Definition']))
        file.close()
        file = open(lib, 'w')
        file.write(str(new))
        file.write(str(new['Analysis']))
        file.close()


def write_lib(out_put_name, new, library):
    with open(library, "r+") as lib:
        data = json.load(lib)
        new_data = {out_put_name: new}
        data.update(new_data)
        lib.seek(0)
        json.dump(data, lib, indent=1)


# load data set input pieces
def loaddsinput(file, part):
    import json
    with open(file) as f:
        data = json.load(f)
    res = data['DataSet'][part]
    return res

# get 2nd_class objects
def get_sheets(session, analysisid, page=0):
    analysis_contents = describe_analysis_definition(session, analysisid)
    if page != 0:
        return analysis_contents['Sheets'][page]
    else:
        return analysis_contents['Sheets']


def get_cfs(session, id, cfname='none'):
    contents = describe_analysis_definition(session, id)
    if cfname != 'none':
        for cf in contents['CalculatedFields']:
            if cf['Name'] == cfname:
                return cf['Expression']
            else:
                return cfname + ' is not exisitng! Please check the dataset definition again.'
    else:
        return contents['CalculatedFields']


def get_parameter(session, id, type, pname='none'):
    if type == 'analysis':
        contents = describe_analysis_definition(session, id)
    elif type == 'dashboard':
        contents = describe_dashboard_definition(session, id)
    if pname != 'none':
        for p in contents['ParameterDeclarations']:
            for key in p:
                if p[key]['Name'] == pname:
                    return p
                else:
                    return pname + ' is not exisitng! Please check the dataset definition again.'
    else:
        return contents['ParameterDeclarations']


# update target dataset with folders
def update_dataset_folders(session, DSID, Folders):
    qs = session.client('quicksight')
    sts_client = session.client("sts")
    AccountId = sts_client.get_caller_identity()["Account"]
    response = describe_data_set(session, DSID)
    args: Dict[str, Any] = {
        "AwsAccountId": AccountId,
        "DataSetId": DSID,
        "Name": response["DataSet"]["Name"],
        "PhysicalTableMap": response["DataSet"]["PhysicalTableMap"],
        "LogicalTableMap": response["DataSet"]["LogicalTableMap"],
        "ImportMode": response["DataSet"]["ImportMode"],
        "FieldFolders": Folders
    }
    response = qs.update_data_set(**args)
    return response


def update_dataset_2(session, DataSetId, component_type, component_body):
    qs = session.client('quicksight')
    sts_client = session.client("sts")
    AccountId = sts_client.get_caller_identity()["Account"]
    response = describe_data_set(session, DataSetId)
    args: Dict[str, Any] = {
        "AwsAccountId": AccountId,
        "DataSetId": DataSetId,
        "Name": response["DataSet"]["Name"],
        "PhysicalTableMap": response["DataSet"]["PhysicalTableMap"],
        "LogicalTableMap": response["DataSet"]["LogicalTableMap"],
        "ImportMode": response["DataSet"]["ImportMode"],
        "FieldFolders": response["DataSet"]["FieldFolders"]
    }
    if component_type == '':
        response = qs.update_data_set(**args)
    elif component_type == 'Cf':
        num = list(args["LogicalTableMap"].keys())[0]
        print(num)
        create_column = {"CreateColumnsOperation": {}}
        body = {"ColumnName": component_body["Name"], "ColumnId": component_body["Name"],
                "Expression": component_body["Expression"]}
        create_column["CreateColumnsOperation"]["Columns"] = [body]
        args["LogicalTableMap"][num]["DataTransforms"].append(create_column)
        for item in args["LogicalTableMap"][num]["DataTransforms"]:
            try:
                item["ProjectOperation"]["ProjectedColumns"].append(component_body["Name"])
            except:
                continue
        response = qs.update_data_set(**args)
    elif component_type == 'FilterOperation':
        num = list(args["LogicalTableMap"].keys())[0]
        filter = {}
        body = {"ConditionExpression": component_body}
        filter["FilterOperation"] = body
        args["LogicalTableMap"][num]["DataTransforms"].append(filter)
        response = qs.update_data_set(**args)
    else:
        args[component_type] = component_body
        response = qs.update_data_set(**args)
    return response


# full or partial folder creation from source dataset,
# folder_list can either be [] for all folders or be a list of desired folders
def folder_creation_source_dataset(session, source_dataset_id, target_dataset_id, folder_list):
    target_columns = describe_data_set(session, target_dataset_id)['DataSet']['OutputColumns']
    source_dictionary = describe_data_set(session, source_dataset_id)['DataSet']['FieldFolders']
    dictionary = {}
    # check for (folder, column) pair in dictionary
    for column in target_columns:
        keys = [k for k, v in source_dictionary.items() if column['Name'] in v['columns']]
        if keys != []:
            key = keys[0]
            if folder_list == [] or key in folder_list:
                # add keys to new folder dictionary if it doesn't already exist
                if key not in dictionary:
                    dictionary[key] = {}
                    if 'description' in source_dictionary[key]:
                        dictionary[key]['description'] = source_dictionary[key]['description']
                    dictionary[key]['columns'] = list()
                dictionary[key]['columns'].append(column['Name'])
    update_dataset_2(session, target_dataset_id, "FieldFolders", dictionary)
    return


# folder creation with dictionary of folders as input
def folder_creation_dictionary(session, target_dataset_id, folder_dict):
    target_columns = describe_data_set(session, target_dataset_id)['DataSet']['OutputColumns']
    dictionary = {}
    # check for (folder, column) pair in dictionary
    for column in target_columns:
        keys = [k for k, v in folder_dict.items() if column['Name'] in v['columns']]
        if keys != []:
            key = keys[0]
            # add keys to new folder dictionary if it doesn't already exist
            if key not in dictionary:
                dictionary[key] = {}
                if 'description' in folder_dict[key]:
                    dictionary[key]['description'] = folder_dict[key]['description']
                dictionary[key]['columns'] = list()
            dictionary[key]['columns'].append(column['Name'])
    update_dataset_2(session, target_dataset_id, "FieldFolders", dictionary)
    return


# folder creation with csv of folders as input
def folder_creation_csv(session, target_dataset_id, csv):
    folder_dict = dict()
    f = open(csv)
    # parse csv file
    for line in f:
        line = line.strip('\n')
        splitted = line.split(",")
        folder_dict[splitted[0]] = list()
        for word in splitted[1:]:
            folder_dict[splitted[0]].append(word.strip('"'))
    target_columns = describe_data_set(session, target_dataset_id)['DataSet']['OutputColumns']
    dictionary = {}
    # check for (folder, column) pair in dictionary
    for column in target_columns:
        keys = [k for k, v in folder_dict.items() if column['Name'] in v['columns']]
        if keys != []:
            key = keys[0]
            if key not in dictionary:
                dictionary[key] = {}
                if 'description' in folder_dict[key]:
                    dictionary[key]['description'] = folder_dict[key]['description']
                dictionary[key]['columns'] = list()
            dictionary[key]['columns'].append(column['Name'])
    update_dataset_2(session, target_dataset_id, "FieldFolders", dictionary)
    return

# DELETES ALL ASSETS IN FOLDER
# Used for Release folder
def reset_folder(session, account, folder):
    print('Deleting all assets in folder: ', folder)
    folder_queue = [folder]
    while len(folder_queue) > 0:
        cur_folder = folder_queue.pop()
        cur_fid = cur_folder.split("/")[1]
        try:
            message = []
            for member in list_folder_members(session, cur_fid):
                member_type = ''
                if 'release' not in member['MemberArn']:
                    raise Exception('WARNING Unexpected ARN does not contain \'release\': ' + member['MemberArn'])
                if 'dataset' in member['MemberArn']:
                    delete_dataset(session, member['MemberId'])
                elif 'dashboard' in member['MemberArn']:
                    delete_dashboard(session, member['MemberId'])
                elif 'analysis' in member['MemberArn']:
                    raise Exception('Analysis migration is not supported.')
                else:
                    raise Exception('Member Type not found')
                print('Deleted -', member['MemberArn'])
                message.append(member['MemberId'])
            for folder in search_folders(session, cur_folder):
                folder_queue.append(folder['Arn'])
            print('Finished deleting assets.')
            return message
        except Exception as e:
            message = {"account_id": account, "folder_id": cur_fid, "error": str(e)}
            return message