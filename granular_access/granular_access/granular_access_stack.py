from aws_cdk import (
            core,
            aws_s3 as s3,
            aws_s3_deployment as s3deploy,
            aws_iam as iam,
            aws_ssm as ssm,
            aws_lambda as _lambda,
            aws_events as events,
            aws_events_targets as targets
        )
import boto3
import json
import os

current_dir = os.path.dirname(__file__)

if os.environ.get("CDK_DEPLOY_REGION", os.environ["CDK_DEFAULT_REGION"]) == 'us-east-1':
    prefix = 'us'
elif os.environ.get("CDK_DEPLOY_REGION", os.environ["CDK_DEFAULT_REGION"]) == 'eu-west-1':
    prefix = 'eu'

class GranularAccessStack(core.Stack):

    def __init__(self, scope: core.Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        stack = core.Stack.of(self)
        aws_region = os.environ.get("CDK_DEPLOY_REGION", os.environ["CDK_DEFAULT_REGION"])
        account_id = stack.account

        granular_access = GranularAccess(self, 'granular_access')

class GranularAccess(core.Construct):
    def __init__(self, scope: core.Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        aws_region = os.environ.get("CDK_DEPLOY_REGION", os.environ["CDK_DEFAULT_REGION"])
        account_id = os.environ.get("CDK_DEPLOY_ACCOUNT", os.environ["CDK_DEFAULT_ACCOUNT"])

        ssm_client = boto3.client('ssm', aws_region)
        # Prepare pipeline config details in SSM parameters
        if prefix == 'us':
            self.qs_reports_env_config = {"Permissions":
                                              [{"Group_Name": "critical",
                                                "Reports": ["Sales Results - Critical"],
                                                "ns_name": "default"},
                                               {"Group_Name": "highlyconfidential",
                                                "Reports": ["Field Operations Dashboard",
                                                            "Sales Results - Highly Confidential"
                                                            ],
                                                "ns_name": "default"},
                                               {"Group_Name": "bi-developer",
                                                "Reports": ["all"],
                                                "ns_name": "default"},
                                               {"Group_Name": "bi-admin",
                                                "Reports": ["all"],
                                                "ns_name": "default"},
                                               {"Group_Name": "power-reader",
                                                "Reports": ["read-all"],
                                                "ns_name": "default"},
                                               {"Group_Name": "3rd-party",
                                                "Reports": ["Marketing KPIs"],
                                                "ns_name": "3rd-party"},
                                               {"Group_Name": "3rd-party-reader",
                                                "Reports": ["Marketing KPIs"],
                                                "ns_name": "3rd-party"}
                                               ]
                                          }
        if prefix == 'eu':
            self.qs_reports_env_config = {"Permissions":
                                              [{"Group_Name": "eu-critical",
                                                "Reports": ["EUResults - Critical"]},
                                               {"Group_Name": "bi-developer",
                                                "Reports": ["all"]},
                                               {"Group_Name": "bi-admin",
                                                "Reports": ["all"]},
                                               {"Group_Name": "eu-highlyconfidential",
                                                "Reports": ["EUField Operations Dashboard",
                                                            "EUResults - Highly Confidential"]},
                                               {"Group_Name": "power-reader",
                                                "Reports": ["read-all"]}]}

        self.qs_reports_env_config_ssm = ssm.StringParameter(
            self, '/qs/config/access',
            string_value=json.dumps(self.qs_reports_env_config),
            parameter_name='/qs/config/access'
        )

        #group-user mapping information is stored in s3 bucket. A ssm parameter stores the bucket name.
        self.qs_user_group_config = {'bucket-name':f'qs-granular-access-demo-{account_id}'}

        bucket = s3.Bucket(self, f'qs-granular-access-demo-{account_id}',
                           bucket_name=f'qs-granular-access-demo-{account_id}',
                           versioned=True,
                           removal_policy=core.RemovalPolicy.DESTROY,
                           auto_delete_objects=True)

        s3deploy.BucketDeployment(self, "DeployMembership",
                                  sources=[s3deploy.Source.asset('membership.zip')],
                                destination_bucket=bucket,
                                destination_key_prefix='membership',
                                                  prune=False)

        self.qs_user_group_config_ssm = ssm.StringParameter(
            self, '/qs/config/groups',
            string_value=json.dumps(self.qs_user_group_config),
            parameter_name='/qs/config/groups'
        )

        # group-role mapping information is stored in a ssm parameter.
        self.qs_role_config = {'default_bi-developer': 'AUTHOR',
                               'default_bi-admin': 'ADMIN',
                               'default_power-reader': 'AUTHOR',
                               'default_critical': 'READER',
                               'default_highlyconfidential': 'READER',
                               'default_marketing': 'AUTHOR',
                               '3rd-party_3rd-party': 'AUTHOR',
                               '3rd-party_3rd-party-reader': 'READER'
                               }

        self.qs_role_config_ssm = ssm.StringParameter(
            self, '/qs/config/roles',
            string_value=json.dumps(self.qs_role_config),
            parameter_name='/qs/config/roles'
        )

        # group-namespace mapping information is stored in a ssm parameter.
        self.qs_ns_config = {"ns":['default',
                             '3rd-party']}

        self.qs_ns_config_ssm = ssm.StringParameter(
            self, '/qs/config/ns',
            string_value=json.dumps(self.qs_ns_config),
            parameter_name='/qs/config/ns'
        )

        lambda_role = iam.Role(
            self,
            id='lambda-role',
            description='Role for the quicksight lambda',
            role_name=f'{aws_region}-role-quicksight-lambda',
            max_session_duration=core.Duration.seconds(3600),
            assumed_by=iam.ServicePrincipal('lambda.amazonaws.com'),
            inline_policies={
                'AllowS3Access': iam.PolicyDocument(
                    statements=[
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=["kms:GetParametersForImport",
                                     "kms:GetPublicKey",
                                     "kms:ListKeyPolicies",
                                     "kms:ListRetirableGrants",
                                     "kms:GetKeyPolicy",
                                     "kms:ListResourceTags",
                                     "kms:ListGrants",
                                     "kms:GetParametersForImport",
                                     "kms:GetKeyRotationStatus",
                                     "kms:DescribeKey",
                                     "kms:CreateGrant",
                                     "kms:ListAliases",
                                     "kms:ListKeys",
                                     "kms:DescribeCustomKeyStores",
                                     "ssm:GetParameters",
                                     "ssm:GetParameter",
                                     "ssm:GetParametersByPath"
                                     ],
                            resources=['*']
                        ),
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=["lambda:InvokeFunction",
                                     "logs:CreateLogStream",
                                     "logs:CreateLogGroup",
                                     "logs:PutLogEvents",
                                     "quicksight:*",
                                     "ds:CreateIdentityPoolDirectory",
                                     "s3:HeadBucket",
                                     "s3:ListAllMyBuckets",
                                     "s3:PutObject",
                                     "s3:GetObject",
                                     "s3:ListBucket",
                                     "s3:GetObjectVersionForReplication",
                                     "s3:GetBucketPolicy",
                                     "s3:GetObjectVersion",
                                     "cloudwatch:PutMetricData",
                                     "sts:GetCallerIdentity"],
                            resources=['*']
                        )
                    ]
                )
            }
        )

        user_init = _lambda.Function(self, 'user_init',
                                           handler='user_init.lambda_handler',
                                           runtime=_lambda.Runtime.PYTHON_3_7,
                                           code=_lambda.Code.from_asset(os.path.join(current_dir,
                                                                                     '../lambda_functions/user_init/')),
                                           function_name='user_init',
                                           role=lambda_role,
                                           timeout=core.Duration.minutes(15),
                                           memory_size=512
                                           )

        check_team_members = _lambda.Function(self, 'check_team_members',
                                                    handler='check_team_members.lambda_handler',
                                                    runtime=_lambda.Runtime.PYTHON_3_7,
                                                    code=_lambda.Code.from_asset(os.path.join(current_dir,
                                                                                              '../lambda_functions/check_team_members/')),
                                                    function_name='check_team_members',
                                                    role=lambda_role,
                                                    timeout=core.Duration.minutes(15),
                                                    memory_size=512,
                                                    environment={'aws_region': f'{core.Aws.REGION}'}
                                                    )

        downgrade_user = _lambda.Function(self, 'downgrade_user',
                                                handler='downgrade_user.lambda_handler',
                                                runtime=_lambda.Runtime.PYTHON_3_8,
                                                code=_lambda.Code.from_asset(os.path.join(current_dir,
                                                                                          '../lambda_functions/downgrade_user/')),
                                                function_name='downgrade_user',
                                                role=lambda_role,
                                                timeout=core.Duration.minutes(15),
                                                memory_size=2048,
                                                environment={'aws_region': f'{core.Aws.REGION}'}
                                                )

        granular_user_govenance = _lambda.Function(self, 'granular_user_govenance',
                                                 handler='granular_user_govenance.lambda_handler',
                                                 runtime=_lambda.Runtime.PYTHON_3_7,
                                                 code=_lambda.Code.from_asset(os.path.join(current_dir,
                                                                                           '../lambda_functions/granular_user_govenance')),
                                                 function_name='granular_user_govenance',
                                                 role=lambda_role,
                                                 timeout=core.Duration.minutes(15),
                                                 memory_size=2048,
                                                 environment={'aws_region': f'{core.Aws.REGION}'}
                                                )

        granular_access_assets_govenance = _lambda.Function(self, 'granular_access_assets_govenance',
                                                   handler='granular_access_assets_govenance.lambda_handler',
                                                   runtime=_lambda.Runtime.PYTHON_3_7,
                                                   code=_lambda.Code.from_asset(os.path.join(current_dir,
                                                                                             '../lambda_functions/granular_access_assets_govenance')),
                                                   function_name='granular_access_assets_govenance',
                                                   role=lambda_role,
                                                   timeout=core.Duration.minutes(15),
                                                   memory_size=2048,
                                                   environment={'aws_region': f'{core.Aws.REGION}'}
                                                   )

        quicksight_event_rule = events.Rule(self, 'QuickSightCWEventRule',
                                             description='CloudWatch rule to detect new QuickSight user creation',
                                             rule_name='qs-gc-user-creation',
                                             targets=[targets.LambdaFunction(user_init)],
                                             event_pattern=events.EventPattern(source=['aws.quicksight'],
                                                                               detail_type=[
                                                                                   'AWS Service Event via CloudTrail'],
                                                                               detail={
                                                                                   "eventSource": [
                                                                                       "quicksight.amazonaws.com"],
                                                                                   "eventName": ["CreateUser"]
                                                                               }
                                                                               )
                                             )

        quicksight_schedule_rule = events.Rule(self, 'quicksight_schedule_rule',
                                               description='CloudWatch rule to run QS objects/groups assignment every hour',
                                               rule_name='qs-gc-every-hour',
                                               schedule=events.Schedule.cron(minute="0"),
                                               targets=[targets.LambdaFunction(granular_user_govenance)]
                                               )

        quicksight_assume_condition_object = {"StringEquals": {
            "SAML:aud": "https://signin.aws.amazon.com/saml"}}

        quicksight_federated_prin_with_conditionb_obj = iam.FederatedPrincipal(
            f'arn:aws:iam::{core.Aws.ACCOUNT_ID}:saml-provider/saml', quicksight_assume_condition_object,
            'sts:AssumeRoleWithSAML')

        quicksight_resource_scope = '${aws:userid}'
        quicksight_reader_saml_inline_policies = {
            'AllowQuicksightAccessSAML': iam.PolicyDocument(
                statements=[
                    iam.PolicyStatement(
                        effect=iam.Effect.ALLOW,
                        actions=['quicksight:CreateReader'],
                        resources=[
                            f'arn:aws:quicksight::{core.Aws.ACCOUNT_ID}:user/{quicksight_resource_scope}']
                    )
                ]
            )
        }

        quicksight_users = iam.Role(
            self,
            id=f"quicksight-fed-{prefix}-users",  # this is the default group with no access
            description='Role for the quicksight reader SAML',
            role_name=f"quicksight-fed-{prefix}-users",
            max_session_duration=core.Duration.seconds(3600),
            assumed_by=quicksight_federated_prin_with_conditionb_obj,
            inline_policies=quicksight_reader_saml_inline_policies
        )

