import aws_cdk
from aws_cdk import (
    core,
    aws_iam as iam,
    aws_s3 as s3,
    aws_lambda as _lambda,
    aws_events as events,
    aws_events_targets as targets
)
from aws_cdk.core import Aws
import boto3
import json
import os


current_dir = os.path.dirname(__file__)

class QuickSightStack(core.Stack):
    def __init__(self, scope: core.Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        stack = core.Stack.of(self)
        aws_region = stack.region
        account_id = stack.account

        quicksight = QuickSight(self, 'quicksight', aws_region=aws_region, account_id=account_id)


class QuickSight(core.Construct):
    def __init__(self, scope: core.Construct, id: str, aws_region: str, account_id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        s3.Bucket(self, 'administrativedashboard',
                                    bucket_name='administrative-dashboard'+account_id,
                                    block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
                                    versioned=True
                                    )

        lambda_role = iam.Role(
            self,
            id='lambda-role',
            description='Role for the quicksight administrative dashboard lambda',
            role_name='qs-administrative-dashboard-lambda',
            max_session_duration=core.Duration.seconds(3600),
            assumed_by=iam.ServicePrincipal('lambda.amazonaws.com'),
            inline_policies={
                'AllowS3Access': iam.PolicyDocument(
                    statements=[
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

        user_initiation = _lambda.Function(self, 'user_initiation',
                                           handler='user_initiation.lambda_handler',
                                           runtime=_lambda.Runtime.PYTHON_3_7,
                                           code=_lambda.Code.from_asset(os.path.join(current_dir,'../lambda_functions/user_initiation/')),
                                           function_name='user_initiation',
                                           role=lambda_role,
                                           timeout=core.Duration.minutes(15),
                                           memory_size=512
                                           )

        group_initiation = _lambda.Function(self, 'group_initiation',
                                            handler='group_initiation.lambda_handler',
                                            runtime=_lambda.Runtime.PYTHON_3_7,
                                            code=_lambda.Code.from_asset(os.path.join(current_dir,'../lambda_functions/group_initiation/')),
                                            function_name='group_initiation',
                                            role=lambda_role,
                                            timeout=core.Duration.minutes(15),
                                            memory_size=512
                                            )

        data_prepare = _lambda.Function(self, 'data_prepare',
                                                    handler='data_prepare.lambda_handler',
                                                    runtime=_lambda.Runtime.PYTHON_3_7,
                                                    code=_lambda.Code.from_asset(os.path.join(current_dir,'../lambda_functions/data_prepare/')),
                                                    function_name='data_prepare',
                                                    role=lambda_role,
                                                    timeout=core.Duration.minutes(15),
                                                    memory_size=512
                                                    )

        usercreation = events.Rule(self, 'usercreation',
                                             description='CloudWatch rule to detect new QuickSight user creation',
                                             rule_name='quicksight-user-creation',
                                             targets=[targets.LambdaFunction(user_initiation),
                                                      targets.LambdaFunction(data_prepare)],
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
        groupcreation = events.Rule(self, 'groupcreation',
                                             description='CloudWatch rule to detect new QuickSight group creation',
                                             rule_name='quicksight-group-creation',
                                             targets=[targets.LambdaFunction(group_initiation),
                                                      targets.LambdaFunction(data_prepare)],
                                             event_pattern=events.EventPattern(source=['aws.quicksight'],
                                                                               detail_type=[
                                                                                   'AWS API Call via CloudTrail'],
                                                                               detail={
                                                                                   "eventSource": [
                                                                                       "quicksight.amazonaws.com"],
                                                                                   "eventName": ["CreateGroup"]
                                                                               }
                                                                               )
                                             )
        groupdeletion = events.Rule(self, 'groupdeletion',
                                             description='CloudWatch rule to detect QuickSight group deletion',
                                             rule_name='quicksight-group-deletion',
                                             targets=[targets.LambdaFunction(data_prepare)],
                                             event_pattern=events.EventPattern(source=['aws.quicksight'],
                                                                               detail_type=[
                                                                                   'AWS API Call via CloudTrail'],
                                                                               detail={
                                                                                   "eventSource": [
                                                                                       "quicksight.amazonaws.com"],
                                                                                   "eventName": ["DeleteGroup"]
                                                                               }
                                                                               )
                                             )
        userdeletion = events.Rule(self, 'userdeletion',
                                             description='CloudWatch rule to detect QuickSight user deletion',
                                             rule_name='quicksight-user-deletion',
                                             targets=[targets.LambdaFunction(data_prepare)],
                                             event_pattern=events.EventPattern(source=['aws.quicksight'],
                                                                               detail_type=[
                                                                                   'AWS Service Event via CloudTrail'],
                                                                               detail={
                                                                                   "eventSource": [
                                                                                       "quicksight.amazonaws.com"],
                                                                                   "eventName": ["DeleteUser"]
                                                                               }
                                                                               )
                                             )
        addgroupmember = events.Rule(self, 'addgroupmember',
                                   description='CloudWatch rule to detect QuickSight user add into a group',
                                   rule_name='quicksight-user-add-into-a-group',
                                   targets=[targets.LambdaFunction(data_prepare)],
                                   event_pattern=events.EventPattern(source=['aws.quicksight'],
                                                                     detail_type=[
                                                                         'AWS API Call via CloudTrail'],
                                                                     detail={
                                                                         "eventSource": [
                                                                             "quicksight.amazonaws.com"],
                                                                         "eventName": ["CreateGroupMembership"]
                                                                     }
                                                                     )
                                   )
        dashboardupdate = events.Rule(self, 'dashboardupdate',
                                   description='CloudWatch rule to detect QuickSight dashboard permissions update',
                                   rule_name='quicksight-dashboard-permissions-update',
                                   targets=[targets.LambdaFunction(data_prepare)],
                                   event_pattern=events.EventPattern(source=['aws.quicksight'],
                                                                     detail_type=[
                                                                         'AWS API Call via CloudTrail'],
                                                                     detail={
                                                                         "eventSource": [
                                                                             "quicksight.amazonaws.com"],
                                                                         "eventName": ["UpdateDashboardPermissions"]
                                                                     }
                                                                     )
                                   )
        datasetupdate = events.Rule(self, 'datasetupdate',
                                      description='CloudWatch rule to detect QuickSight dataset permissions update',
                                      rule_name='quicksight-dataset-permissions-update',
                                      targets=[targets.LambdaFunction(data_prepare)],
                                      event_pattern=events.EventPattern(source=['aws.quicksight'],
                                                                        detail_type=[
                                                                            'AWS API Call via CloudTrail'],
                                                                        detail={
                                                                            "eventSource": [
                                                                                "quicksight.amazonaws.com"],
                                                                            "eventName": ["UpdateDataSetPermissions"]
                                                                        }
                                                                        )
                                      )
        datasourceupdate = events.Rule(self, 'datasourceupdate',
                                    description='CloudWatch rule to detect QuickSight data source permissions update',
                                    rule_name='quicksight-datasource-permissions-update',
                                    targets=[targets.LambdaFunction(data_prepare)],
                                    event_pattern=events.EventPattern(source=['aws.quicksight'],
                                                                      detail_type=[
                                                                          'AWS API Call via CloudTrail'],
                                                                      detail={
                                                                          "eventSource": [
                                                                              "quicksight.amazonaws.com"],
                                                                          "eventName": ["UpdateDataSourcePermissions"]
                                                                      }
                                                                      )
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
                        resources=[f'arn:aws:quicksight::{core.Aws.ACCOUNT_ID}:user/{quicksight_resource_scope}']
                    )
                ]
            )
        }

        Marketing = iam.Role(
            self,
            id="Marketing", #quicksight-saml-<ldap group name>
            description='Role for the quicksight reader SAML',
            role_name="Marketing",
            max_session_duration=core.Duration.seconds(3600),
            assumed_by=quicksight_federated_prin_with_conditionb_obj,
            inline_policies=quicksight_reader_saml_inline_policies
        )
        HR = iam.Role(
            self,
            id="HR",
            description='Role for the quicksight reader SAML',
            role_name="HR",
            max_session_duration=core.Duration.seconds(3600),
            assumed_by=quicksight_federated_prin_with_conditionb_obj,
            inline_policies=quicksight_reader_saml_inline_policies
        )

        quicksight_author_saml_inline_policies = {
            'AllowQuicksightAuthorAccessSAML': iam.PolicyDocument(
                statements=[
                    iam.PolicyStatement(
                        effect=iam.Effect.ALLOW,
                        actions=['quicksight:CreateUser'],
                        resources=[f'arn:aws:quicksight::{core.Aws.ACCOUNT_ID}:user/{quicksight_resource_scope}']
                    )
                ]
            )
        }

        bideveloper = iam.Role(
            self,
            id="bideveloper",
            description='Role for the quicksight author SAML',
            role_name="BI-Developer",
            max_session_duration=core.Duration.seconds(3600),
            assumed_by=quicksight_federated_prin_with_conditionb_obj,
            inline_policies=quicksight_author_saml_inline_policies
        )
        quicksight_admin_saml_inline_policies = {
            'AllowQuicksightAdminAccessSAML': iam.PolicyDocument(
                statements=[
                    iam.PolicyStatement(
                        effect=iam.Effect.ALLOW,
                        actions=['quicksight:CreateAdmin'],
                        resources=[f'arn:aws:quicksight::{core.Aws.ACCOUNT_ID}:user/{quicksight_resource_scope}']
                    )
                ]
            )
        }

        Admin = iam.Role(
            self,
            id="Admin",
            description='Role for the quicksight admin SAML',
            role_name="BI-Admin",
            max_session_duration=core.Duration.seconds(3600),
            assumed_by=quicksight_federated_prin_with_conditionb_obj,
            inline_policies=quicksight_admin_saml_inline_policies
        )
