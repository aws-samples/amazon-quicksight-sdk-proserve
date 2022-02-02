import json
import boto3
import logging
import csv
import io
import os
import tempfile
from datetime import datetime
import botocore.config
# import awswrangler as wr
from typing import Any, Callable, Dict, List, Optional, Union

def default_botocore_config() -> botocore.config.Config:
    """Botocore configuration."""
    retries_config: Dict[str, Union[str, int]] = {
        "max_attempts": int(os.getenv("AWS_MAX_ATTEMPTS", "5")),
    }
    mode: Optional[str] = os.getenv("AWS_RETRY_MODE")
    if mode:
        retries_config["mode"] = mode
    return botocore.config.Config(
        retries=retries_config,
        connect_timeout=10,
        max_pool_connections=10,
        user_agent_extra=f"qs_sdk_granular_access",
    )

lambda_aws_region = os.environ['AWS_REGION']
aws_region = 'us-east-1'
ssm = boto3.client("ssm", region_name=lambda_aws_region, config=default_botocore_config())


def get_ssm_parameters(ssm_string):
    config_str = ssm.get_parameter(
        Name=ssm_string
    )['Parameter']['Value']
    return json.loads(config_str)


def describe_user(username, account_id, aws_region):
    qs_client = boto3.client('quicksight', region_name=aws_region, config=default_botocore_config())
    res = qs_client.describe_user(
        UserName=username,
        AwsAccountId=account_id,
        Namespace='default'
    )
    return res

def describe_namespace(Namespace, account_id, aws_region):
    qs_client = boto3.client('quicksight', region_name=aws_region, config=default_botocore_config())
    res = qs_client.describe_namespace(
        AwsAccountId=account_id,
        Namespace=Namespace
    )
    return res

def register_user(aws_region, Identity, Email, User, AccountId, Arn=None, Session=None, NS='default', Role='READER'):
    qs_client = boto3.client('quicksight', region_name=aws_region, config=default_botocore_config())
    if Identity == 'QUICKSIGHT':
        response = qs_client.register_user(
            IdentityType='QUICKSIGHT',
            Email=Email,
            UserRole=Role,
            AwsAccountId=AccountId,
            Namespace=NS,
            UserName=User)
    elif Identity == 'IAM' and Session is None:
        response = qs_client.register_user(
            IdentityType=Identity,
            Email=Email,
            UserRole=Role,
            IamArn=Arn,
            AwsAccountId=AccountId,
            Namespace=NS)
    elif Identity == 'IAM' and Session is not None:
        response = qs_client.register_user(
            IdentityType=Identity,
            Email=Email,
            UserRole=Role,
            IamArn=Arn,
            SessionName=Session,
            AwsAccountId=AccountId,
            Namespace=NS)

    return response


def delete_user(username, account_id, aws_region, ns):
    qs_client = boto3.client('quicksight', region_name=aws_region, config=default_botocore_config())
    res = qs_client.delete_user(
        UserName=username,
        AwsAccountId=account_id,
        Namespace=ns
    )
    return res


def create_group(userrole, account_id, aws_region, ns):
    qs_client = boto3.client('quicksight', region_name=aws_region, config=default_botocore_config())
    res = qs_client.create_group(
        GroupName=userrole,
        AwsAccountId=account_id,
        Namespace=ns
    )
    return res


def create_group_membership(username, userrole, account_id, aws_region, ns):
    qs_client = boto3.client('quicksight', region_name=aws_region, config=default_botocore_config())
    res = qs_client.create_group_membership(
        MemberName=username,
        GroupName=userrole,
        AwsAccountId=account_id,
        Namespace=ns
    )
    return res

def create_namespace(account_id, aws_region, ns, IdentityStore):
    qs_client = boto3.client('quicksight', region_name=aws_region, config=default_botocore_config())
    res = qs_client.create_namespace(
        AwsAccountId=account_id,
        Namespace=ns,
        IdentityStore=IdentityStore
    )
    return res

def delete_group_membership(username, userrole, account_id, aws_region, ns):
    qs_client = boto3.client('quicksight', region_name=aws_region, config=default_botocore_config())
    res = qs_client.delete_group_membership(
        MemberName=username,
        GroupName=userrole,
        AwsAccountId=account_id,
        Namespace=ns
    )
    return res


def describe_dashboard_permissions(account_id, dashboardid, lambda_aws_region, qs_client):
    res = qs_client.describe_dashboard_permissions(
        AwsAccountId=account_id,
        DashboardId=dashboardid
    )
    return res


def _list(
        func_name: str,
        attr_name: str,
        account_id: str,
        aws_region: str,
        **kwargs, ) -> List[Dict[str, Any]]:
    qs_client = boto3.client('quicksight', region_name=aws_region, config=default_botocore_config())
    func: Callable = getattr(qs_client, func_name)
    response = func(AwsAccountId=account_id, **kwargs)
    next_token: str = response.get("NextToken", None)
    result: List[Dict[str, Any]] = response[attr_name]
    while next_token is not None:
        response = func(AwsAccountId=account_id, NextToken=next_token, **kwargs)
        next_token = response.get("NextToken", None)
        result += response[attr_name]
    return result


def list_groups(
        account_id, aws_region, ns
) -> List[Dict[str, Any]]:
    return _list(
        func_name="list_groups",
        attr_name="GroupList",
        Namespace=ns,
        account_id=account_id,
        aws_region=aws_region
    )


def list_dashboards(
        account_id,
        aws_region
) -> List[Dict[str, Any]]:
    return _list(
        func_name="list_dashboards",
        attr_name="DashboardSummaryList",
        account_id=account_id,
        aws_region=aws_region
    )


def list_analyses(
        account_id,
        aws_region
) -> List[Dict[str, Any]]:
    return _list(
        func_name="list_analyses",
        attr_name="AnalysisSummaryList",
        account_id=account_id,
        aws_region=aws_region
    )


def list_themes(
        account_id,
        aws_region
) -> List[Dict[str, Any]]:
    return _list(
        func_name="list_themes",
        attr_name="ThemeSummaryList",
        account_id=account_id,
        aws_region=aws_region
    )


def list_group_memberships(
        group_name: str,
        account_id: str,
        aws_region: str,
        namespace: str = "default"
) -> List[Dict[str, Any]]:
    return _list(
        func_name="list_group_memberships",
        attr_name="GroupMemberList",
        account_id=account_id,
        GroupName=group_name,
        Namespace=namespace,
        aws_region=aws_region
    )

def list_namespaces(account_id, aws_region) -> List[Dict[str, Any]]:
    return _list(
        func_name="list_namespaces",
        attr_name="Namespaces",
        account_id=account_id,
        aws_region=aws_region
    )

def list_users(account_id, aws_region,ns) -> List[Dict[str, Any]]:
    return _list(
        func_name="list_users",
        attr_name="UserList",
        Namespace=ns,
        account_id=account_id,
        aws_region=aws_region
    )


def list_user_groups(UserName, account_id, aws_region, ns) -> List[Dict[str, Any]]:
    return _list(
        func_name="list_user_groups",
        attr_name="GroupList",
        Namespace=ns,
        UserName=UserName,
        account_id=account_id,
        aws_region=aws_region
    )


def list_datasets(
        account_id,
        aws_region
) -> List[Dict[str, Any]]:
    return _list(
        func_name="list_data_sets",
        attr_name="DataSetSummaries",
        account_id=account_id,
        aws_region=aws_region
    )


def list_data_sources(
        account_id,
        aws_region
) -> List[Dict[str, Any]]:
    return _list(
        func_name="list_data_sources",
        attr_name="DataSources",
        account_id=account_id,
        aws_region=aws_region
    )


def describe_data_set_permissions(account_id, datasetid, aws_region):
    qs_client = boto3.client('quicksight', region_name=aws_region, config=default_botocore_config())
    res = qs_client.describe_data_set_permissions(
        AwsAccountId=account_id,
        DataSetId=datasetid
    )
    return res


def get_dashboard_ids(name: str, account_id, aws_region) -> List[str]:
    ids: List[str] = []
    for dashboard in list_dashboards(account_id, aws_region):
        if dashboard["Name"] == name:
            ids.append(dashboard["DashboardId"])
    return ids


def lambda_handler(event, context):
    # get account_id
    sts_client = boto3.client("sts", region_name=aws_region)
    account_id = sts_client.get_caller_identity()["Account"]

    # call s3 bucket to get group information
    s3 = boto3.resource('s3', region_name=lambda_aws_region)
    bucketname = get_ssm_parameters('/qs/config/groups')
    bucketname = bucketname['bucket-name']
    bucket = s3.Bucket(bucketname)
    mkey = 'membership/membership.csv'
    tmpdir = tempfile.mkdtemp()
    local_file_name = 'membership.csv'
    path = os.path.join(tmpdir, local_file_name)
    bucket.download_file(mkey, path)

    # qs_client is in us-east-1 region for users/groups;
    # qs_local_client is the local region of lambda function for other qs assets
    qs_client = boto3.client('quicksight', region_name='us-east-1')
    qs_local_client = boto3.client('quicksight', region_name=lambda_aws_region)

    # define which iam role to register user according to region
    if lambda_aws_region == 'us-east-1':
        iamrole = 'quicksight-fed-us-users'
        arn = 'arn:aws:iam::' + account_id + ':role/quicksight-fed-us-users'
    elif lambda_aws_region == 'eu-west-1':
        iamrole = 'quicksight-fed-eu-users'
        arn = 'arn:aws:iam::' + account_id + ':role/quicksight-fed-eu-users'

    nslogkey = 'monitoring/quicksight/logs/create_namespace_log.csv'
    local_file_name2 = 'create_namespace_log.csv'
    nslogpath = os.path.join(tmpdir, local_file_name2)

    # load qs namespace information. in QS account, there might be some namespaces which are not list in the ssm.
    # But this solution only controls the namespaces stored in ssm.
    ns_list = get_ssm_parameters('/qs/config/ns')
    ns_list = ns_list['ns']
    print(ns_list)

    nslog=[]
    currentnslist=[]
    lscurrentnsres=list_namespaces(account_id, aws_region)
    for i in lscurrentnsres:
        currentnslist.append(i['Name'])
    for i in ns_list:
        if i in currentnslist:
            if lscurrentnsres[currentnslist.index(i)]['CreationStatus']=='CREATED':
                nslog.append(['CREATED', i, 'N/A'])
            continue
        elif i not in currentnslist:
            create_namespace(account_id, aws_region, i, 'QUICKSIGHT')
            desnsres=describe_namespace(i, account_id, aws_region)
            while (desnsres['Namespace']['CreationStatus'] == 'CREATING'):
                desnsres = describe_namespace(i, account_id, aws_region)
            else:
                if desnsres['Namespace']['CreationStatus'] == 'CREATED':
                    nslog.append(['CREATED', i, datetime.now().strftime("%d/%m/%Y %H:%M:%S")])
                    continue
                else:
                    nslog.append([desnsres['Namespace']['CreationStatus'], i, datetime.now().strftime("%d/%m/%Y %H:%M:%S")])
                    ns_list.remove(i)

    #upload namespace creation results:
    with open(nslogpath, 'w', newline='') as outfile:
        writer = csv.writer(outfile)
        for line in nslog:
            writer.writerow(line)
    bucket.upload_file(nslogpath, nslogkey)

    #place holder to store the group/users info
    new = []

    #dict to store the current group/user info
    currentmembership = {}

    # get current quicksight groups
    for namespace in ns_list:
        groups = list_groups(account_id, aws_region, namespace)
        for group in groups:
            new.append(namespace + '_' + group['GroupName']) #['default_quicksight-fed-critical','3rd-party_3rd-party']

            # get current quicksight users-groups mapping
            if (namespace + '_' + group['GroupName']) in currentmembership:
                pass
            else:
                currentmembership[namespace + '_' + group['GroupName']] = []
            #members=list_group_memberships(group['GroupName'],account_id,aws_region,namespace)

    groups = new # an array of groups with ns information
    new = {} # a dict placeholder to store user alias and QS username mapping

    #get users in current QS account, per different namespace
    for namespace in ns_list:
        users = list_users(account_id, aws_region, namespace)
    # print(users)
        for user in users:
            useralias = user['UserName'].split('/')[-1]
            useralias = useralias.split('@')[0]
            useralias = namespace + '_' + useralias #default_yingwang for example
            new[useralias] = user['UserName'] #{'default_yingwang': 'yingwang@sample.com'}
            # print(user['UserName'])
            usergroups = list_user_groups(user['UserName'], account_id, aws_region, namespace)
            if len(usergroups) == 0:
                if (namespace+'_None') in currentmembership:
                    currentmembership[namespace+'_None'].append(user['UserName'])
                else:
                    currentmembership[namespace+'_None'] = []
                    currentmembership[namespace+'_None'].append(user['UserName'])
            else:
                for group in usergroups:
                    # print(group)
                    fullgroupname = namespace + '_' + group['GroupName']
                    if fullgroupname in currentmembership:
                        currentmembership[fullgroupname].append(user['UserName'])
                    else:
                        currentmembership[fullgroupname] = []
                        currentmembership[fullgroupname].append(user['UserName'])
    users = new #{'default_yingwang': 'yingwang@sample.com', ...}
    print(users)
    print(currentmembership) #{'default_groupname': ['qsusrname', ...], }

    # build new group-members mapping from membership.csv file
    memberships = {}

    # load qs user role information
    roles = get_ssm_parameters('/qs/config/roles')
    # dict {groupname:role} {'default_bi-developer': 'AUTHOR',
    #                                'default_bi-admin': 'ADMIN',
    print(roles)

    # load group mapping information
    with open(path) as csv_file:
        members = csv.reader(csv_file, delimiter=',')
        for member in members:
            namespace = member[0]
            alias = member[2]
            email = member[3]
            # create group
            group = member[1]
            nsplusgroup = namespace + '_' + group.lower() #ns_groupname without qs-fed.
            group = 'quicksight-fed-' + group.lower()
            fullgroupname = namespace + '_' + group
            # print("process this group: " + newgroup)
            if fullgroupname not in groups:
                print("Creating this new group: " + group + "in namespace: " + namespace)
                try:
                    response = create_group(group, account_id, aws_region, namespace)
                    currentmembership[fullgroupname] = []
                    groups.append(fullgroupname)
                except Exception as e:
                    if str(e).find('already exists.'):
                        # print(e)
                        pass
                    else:
                        raise e

            # handle every user
            if alias:
                # register user is user is new
                fullalias = namespace + '_' + alias
                if fullalias not in users:
                    try:
                        response = register_user(aws_region, 'IAM', email, alias, account_id,
                                                 Arn=arn, Session=email, NS=namespace, Role=roles[nsplusgroup])
                        qs_usr_name = iamrole + '/' + email
                        print(qs_usr_name + " is registered")
                        users[fullalias] = qs_usr_name
                    except Exception as e:
                        print(e)
                        pass
                    #assign user into group
                    try:
                        response = create_group_membership(qs_usr_name, group, account_id, aws_region, namespace)
                        print(qs_usr_name + " is added into " + group + "of namespace: " + namespace)
                        currentmembership[fullgroupname].append(qs_usr_name)

                    except Exception as e:
                        if str(e).find('does not exist'):
                            # print(e)
                            pass
                        else:
                            raise e

                # add user into the group if user exists
                if fullalias in users: #existing user
                    qs_usr_name = users[fullalias]
                    email = users[fullalias].split('/')[-1]
                    # print(qs_usr_name)
                    # print(email)
                    if qs_usr_name not in currentmembership[fullgroupname]:
                        # print(qs_usr_name)
                        try:
                            response = create_group_membership(qs_usr_name, group, account_id, aws_region, namespace)
                            print(qs_usr_name + " is added into " + group + "of namespace: " + namespace)
                            currentmembership[fullgroupname].append(qs_usr_name)
                        except Exception as e:
                            if str(e).find('does not exist'):
                                # print(e)
                                pass
                            else:
                                raise e
                    if ((nsplusgroup in roles) and (roles[nsplusgroup] != 'READER')):
                        print("update role")
                        try:
                            qs_client.update_user(
                                UserName=qs_usr_name,
                                AwsAccountId=account_id,
                                Namespace=namespace,
                                Email=email,
                                Role=roles[nsplusgroup]
                            )
                        except Exception as e:
                            if str(e).find('does not exist'):
                                # print(e)
                                pass
                            else:
                                raise e
                        """elif newgroup in ['quicksight-fed-bi-developer',
                                          'quicksight-fed-power-reader']:
                            print("add new dev")
                            if qs_usr_name not in memberships['quicksight-fed-bi-admin']:
                                try:
                                    qs_client.update_user(
                                        UserName=qs_usr_name,
                                        AwsAccountId=account_id,
                                        Namespace='default',
                                        Email=email,
                                        Role='AUTHOR'
                                    )
                                except Exception as e:
                                    if str(e).find('does not exist'):
                                        # print(e)
                                        pass
                                    else:
                                        raise e"""

                # write current group-users mapping into a dict "membership"
                if fullgroupname in memberships:
                    if 'qs_usr_name' in locals():  # User in membership.csv already registered as a QS user
                        memberships[fullgroupname].append(qs_usr_name)
                    #else:  # User in membership.csv do not register as a QS user yet
                        #memberships[fullgroupname].append(alias)

                else:
                    memberships[fullgroupname] = []
                    if 'qs_usr_name' in locals():
                        memberships[fullgroupname].append(qs_usr_name)
                    #else:
                        #memberships[fullgroupname].append(alias)

    # remove current user permissions or memberships if membership file changed
    print(memberships)
    for namespace in ns_list:
        users = list_users(account_id, aws_region, namespace)

        for user in users:
            # print(user['UserName'])
            groups = list_user_groups(user['UserName'], account_id, aws_region, namespace)
            # print(groups)
            if len(groups) == 0:
                if user['UserName'].split("/", 1)[0] != 'Administrator':
                    #delete orphan user who is not in any group
                    delete_user(user['UserName'], account_id, aws_region, namespace)
            else:
                for group in groups:
                    # currentmembership[group['GroupName']] = user['UserName']
                    nsplusgroup = namespace + '_' + group['GroupName']
                    if nsplusgroup in memberships:
                        # print(group['GroupName'])
                        if user['UserName'] not in memberships[nsplusgroup]:
                            delete_group_membership(user['UserName'], group['GroupName'], account_id, aws_region,
                                                    namespace)
                            print(user['UserName'] + " is removed from " + group['GroupName']
                                  + 'of namespace: ' + namespace)

    # get current quicksight groups
    """groups = list_groups(account_id, aws_region)
    new = []
    for group in groups:
        new.append(group['GroupName'])
    groups = new
    new = []
    # get current quicksight users-groups mapping
    currentmembership = {}
    for group in groups:
        if group in currentmembership:
            pass
        else:
            currentmembership[group] = []

    users = list_users(account_id, aws_region)
    for user in users:
        new.append(user['UserName'])
        print(user['UserName'])
        usergroups = list_user_groups(user['UserName'], account_id, aws_region)
        if len(usergroups) == 0:
            if 'None' in currentmembership:
                currentmembership['None'].append(user['UserName'])
            else:
                currentmembership['None'] = []
                currentmembership['None'].append(user['UserName'])
        else:
            for group in usergroups:
                # print(group)
                if group['GroupName'] in currentmembership:
                    currentmembership[group['GroupName']].append(user['UserName'])
                else:
                    currentmembership[group['GroupName']] = []
                    currentmembership[group['GroupName']].append(user['UserName'])
    print("here it is current users mapping:")
    print(currentmembership)"""

