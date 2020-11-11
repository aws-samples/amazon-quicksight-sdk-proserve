from aws_cdk import (
            core,
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
        #account_id = stack.account

        ssm_client = boto3.client('ssm', aws_region)
        # Prepare pipeline config details in SSM parameters
        if prefix == 'us':
            self.qs_reports_env_config = {"Permissions":
                                              [{"Group_Name": "Critical",
                                                "Reports": ["Results - Critical"]},
                                               {"Group_Name": "HighlyConfidential",
                                                "Reports": ["Field Operations Dashboard",
                                                            "Results - Highly Confidential"
                                                            ]},
                                               {"Group_Name": "BI-developer",
                                                "Reports": ["all"]},
                                               {"Group_Name": "BI-Admin",
                                                "Reports": ["all"]},
                                               {"Group_Name": "Power-reader",
                                                "Reports": ["read-all"]}
                                               ]
                                          }
        if prefix == 'eu':
            self.qs_reports_env_config = {"Permissions":
                                              [{"Group_Name": "EU-Critical",
                                                "Reports": ["EUResults - Critical"]},
                                               {"Group_Name": "BI-developer",
                                                "Reports": ["all"]},
                                               {"Group_Name": "BI-Admin",
                                                "Reports": ["all"]},
                                               {"Group_Name": "EU-HighlyConfidential",
                                                "Reports": ["EUField Operations Dashboard",
                                                            "EUResults - Highly Confidential"]},
                                               {"Group_Name": "Power-reader",
                                                "Reports": ["read-all"]}]}

        self.qs_reports_env_config_ssm = ssm.StringParameter(
            self, '/qs/config/access',
            string_value=json.dumps(self.qs_reports_env_config),
            parameter_name='/qs/config/access'
        )

        self.qs_user_group_config = {'bucket-name':"granular-access-demo"}

        self.qs_user_group_config_ssm = ssm.StringParameter(
            self, '/qs/config/groups',
            string_value=json.dumps(self.qs_user_group_config),
            parameter_name='/qs/config/groups'
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

        granular_access = _lambda.Function(self, 'granular_access',
                                                 handler='granular_access.lambda_handler',
                                                 runtime=_lambda.Runtime.PYTHON_3_7,
                                                 code=_lambda.Code.from_asset(os.path.join(current_dir,
                                                                                           '../lambda_functions/granular_access/')),
                                                 function_name='granular_access',
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
                                               targets=[targets.LambdaFunction(check_team_members),
                                                        targets.LambdaFunction(granular_access)]
                                               )

        quicksight_assume_condition_object = {"StringEquals": {
            "SAML:aud": "https://signin.aws.amazon.com/saml"}}

        quicksight_federated_prin_with_conditionb_obj = iam.FederatedPrincipal(
            f'arn:aws:iam::{core.Aws.ACCOUNT_ID}:saml-provider/amazon', quicksight_assume_condition_object,
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

