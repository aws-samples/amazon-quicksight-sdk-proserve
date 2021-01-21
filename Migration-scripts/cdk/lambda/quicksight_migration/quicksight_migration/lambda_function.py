import os
import logging
import sys
import json
from typing import Any, Dict, List, Optional
from quicksight_migration.batch_migration_lambda import migrate as batch
from quicksight_migration.incremental_migration_lambda import migrate as incremental
import quicksight_migration.quicksight_utils as qs_utils

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    logger.info(event)
    aws_region = 'us-east-1'

    request_dict = json.loads(event['body'])
    source_account_id = request_dict['source_account_id']
    source_role_name = request_dict['source_role_name']
    target_account_id = request_dict['target_account_id']
    target_role_name = request_dict['target_role_name']

    infra_config_param_name = os.getenv('INFRA_CONFIG_PARAM')
    s3_bucket = os.getenv('BUCKET_NAME')
    s3_key = os.getenv('S3_KEY')

    sourcesession = qs_utils.assume_role(source_account_id, source_role_name, aws_region)
    targetsession = qs_utils.assume_role(target_account_id, target_role_name, aws_region)

    sourceroot = qs_utils.get_user_arn(sourcesession, 'root')
    sourceadmin = qs_utils.get_user_arn(sourcesession, 'Administrator/wangzyn-Isengard')

    targetroot = qs_utils.get_user_arn(targetsession, 'root')
    targetadmin = qs_utils.get_user_arn(targetsession, 'Admin/wangzyn-Isengard')

    infra_details = qs_utils.get_ssm_parameters(targetsession, infra_config_param_name)


    redshift_password = qs_utils.get_secret(targetsession, infra_details['redshiftPassword'])
    rds_password = qs_utils.get_secret(targetsession, infra_details['rdsPassword'])

    vpc = infra_details['vpcId']

    owner = targetadmin

    rds = infra_details['rdsClusterId']
    rdscredential = {
        'CredentialPair': {
            'Username': infra_details['rdsUsername'],
            'Password': redshift_password
        }
    }
    redshift = {
        "ClusterId": infra_details['redshiftClusterId'],
        "Host": infra_details['redshiftHost'],
        "Database": infra_details['redshiftDB']
    }
    redshiftcredential = {
        'CredentialPair': {
            'Username': infra_details['redshiftUsername'],
            'Password': rds_password
        }
    }
    namespace = infra_details['namespace']
    version = infra_details['version']
    tag = [
            {
                'Key': 'testmigration',
                'Value': 'true'
            }
        ]

    target = qs_utils.get_target(
        targetsession, rds, redshift, s3_bucket, s3_key,
        vpc, tag, owner, rdscredential, redshiftcredential)

    if request_dict['migration_type'] == "BATCH":
        batch(
            aws_region,
            sourcesession,
            targetsession,
            target,
            sourceroot,
            sourceadmin,
            targetroot,
            targetadmin
        )
    elif request_dict['migration_type'] == "INCREMENTAL" and request_dict['migrate_resource']:
        incremental(
            aws_region,
            sourcesession,
            targetsession,
            target,
            sourceroot,
            sourceadmin,
            targetroot,
            targetadmin,
            request_dict['migrate_resource']
        )
    else:
        logger.error(
            "The migration_type %s is not allowed or missing migrate_resource\
                for 'INCREMENTAL' migration", request_dict['migration_type'])
        raise ValueError("Required parameters were not given")
