import os
import json
from aws_cdk import aws_iam as iam, aws_ssm as ssm, core
from aws_cdk.custom_resources import (
    AwsCustomResource,
    AwsCustomResourcePolicy,
    PhysicalResourceId,
    AwsSdkCall,
)


class QuicksightTargetStack(core.Stack):
    def __init__(
        self, scope: core.Construct, id: str, central_account, **kwargs
    ) -> None:
        super().__init__(scope, id, **kwargs)
        self.current_dir = os.path.dirname(__file__)

        # Change to your central account
        self.central_account_id = central_account

        self.quicksight_migration_target_assume_role = iam.Role(
            self,
            "quicksight-migration-target-assume-role",
            description="Role for the Quicksight dashboard migration Lambda function to assume",
            role_name="quicksight-migration-target-assume-role",
            max_session_duration=core.Duration.seconds(3600),
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            inline_policies={
                "AllowAccess": iam.PolicyDocument(
                    statements=[
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=[
                                "quicksight:*",
                            ],
                            resources=["*"],
                        ),
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=[
                                "ssm:GetParameter",
                            ],
                            resources=[
                                f"arn:aws:ssm:{core.Aws.REGION}:{core.Aws.ACCOUNT_ID}:parameter/infra/config"
                            ],
                        ),
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=["secretsmanager:GetSecretValue"],
                            resources=[
                                f"arn:aws:secretsmanager:{core.Aws.REGION}:{core.Aws.ACCOUNT_ID}:secret:*"
                            ],
                        ),
                    ]
                )
            },
        )

        self.quicksight_migration_target_assume_role.assume_role_policy.add_statements(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=["sts:AssumeRole"],
                principals=[iam.AccountPrincipal(self.central_account_id)],
            )
        )

        ssm.StringParameter(
            self,
            "InfraConfigParam",
            parameter_name="/infra/config",
            string_value=json.dumps(self.to_dict()),
        )

        self.quicksight_managed_resources_policy = iam.ManagedPolicy(
            self,
            "iam_policy",
            managed_policy_name="QuickSightMigrationPolicy",
            statements=[
                iam.PolicyStatement(
                    sid="AWSResourceAccess",
                    effect=iam.Effect.ALLOW,
                    actions=[
                        "iam:List*",
                        "redshift:Describe*",
                        "rds:Describe*",
                        "athena:Get*",
                        "athena:List*",
                        "athena:BatchGetQueryExecution",
                        "athena:StartQueryExecution",
                        "athena:StopQueryExecution",
                        "s3:GetBucketLocation",
                        "s3:GetObject",
                        "s3:ListBucket",
                        "s3:ListBucketMultipartUploads",
                        "s3:ListMultipartUploadParts",
                        "s3:AbortMultipartUpload",
                        "s3:CreateBucket",
                        "s3:PutObject",
                        "s3:PutBucketPublicAccessBlock",
                    ],
                    resources=["*"],
                ),
            ],
        )
        # create a custom resource that will create a quicksight user using the IAM target role
        self.qs_user = AwsCustomResource(
            self,
            "AWSCustomResourceQSUser",
            role=self.quicksight_migration_target_assume_role,
            policy=AwsCustomResourcePolicy.from_sdk_calls(
                resources=AwsCustomResourcePolicy.ANY_RESOURCE
            ),
            on_create=self.create_qsuser(),
            on_delete=self.delete_qsuser(),
            resource_type="Custom::QuickSightMigrationUser",
        )
        self.qs_user.node.add_dependency(self.quicksight_managed_resources_policy)

        # create a custom resource that will create a quicksight policy assignment
        self.qs_policy_assignment = AwsCustomResource(
            self,
            "AWSCustomResourceQSPolicyAssignment",
            role=self.quicksight_migration_target_assume_role,
            policy=AwsCustomResourcePolicy.from_sdk_calls(
                resources=AwsCustomResourcePolicy.ANY_RESOURCE
            ),
            on_create=self.create_policy_assignment(),
            on_delete=self.delete_policy_assignment(),
            resource_type="Custom::QuickSightPolicyAssignment",
        )
        self.qs_policy_assignment.node.add_dependency(self.qs_user)

    # create quicksight user
    def create_qsuser(self):
        create_params = {
            "IdentityType": "IAM",
            "Email": " ",
            "UserRole": "ADMIN",
            "IamArn": self.quicksight_migration_target_assume_role.role_arn,
            "SessionName": "quicksight",
            "AwsAccountId": core.Aws.ACCOUNT_ID,
            "Namespace": "default",
        }

        return AwsSdkCall(
            action="registerUser",
            service="QuickSight",
            parameters=create_params,
            physical_resource_id=PhysicalResourceId.of("cdksdk_qsuser"),
        )

    # delete quicksight user
    def delete_qsuser(self):
        params = {
            "UserName": self.quicksight_migration_target_assume_role.role_name
            + "/quicksight",
            "AwsAccountId": core.Aws.ACCOUNT_ID,
            "Namespace": "default",
        }

        return AwsSdkCall(
            action="deleteUser",
            service="QuickSight",
            parameters=params,
            physical_resource_id=PhysicalResourceId.of("cdksdk_qsuser"),
        )

    # create policy assignment
    def create_policy_assignment(self):
        create_params = {
            "AssignmentName": "QuickSightMigration",
            "AssignmentStatus": "ENABLED",
            "AwsAccountId": core.Aws.ACCOUNT_ID,
            "Namespace": "default",
            "Identities": {
                "user": [
                    self.quicksight_migration_target_assume_role.role_name
                    + "/quicksight"
                ]
            },
            "PolicyArn": self.quicksight_managed_resources_policy.managed_policy_arn,
        }

        return AwsSdkCall(
            action="createIAMPolicyAssignment",
            service="QuickSight",
            assumed_role_arn=self.quicksight_migration_target_assume_role.role_arn,
            parameters=create_params,
            physical_resource_id=PhysicalResourceId.of("cdksdk_policyassignment"),
        )

    # delete policy assignment
    def delete_policy_assignment(self):
        delete_params = {
            "AssignmentName": "QuickSightMigration",
            "AwsAccountId": core.Aws.ACCOUNT_ID,
            "Namespace": "default",
        }

        return AwsSdkCall(
            action="deleteIAMPolicyAssignment",
            service="QuickSight",
            assumed_role_arn=self.quicksight_migration_target_assume_role.role_arn,
            parameters=delete_params,
            physical_resource_id=PhysicalResourceId.of("cdksdk_policyassignment"),
        )

    def to_dict(self):
        config = {}
        config["vpcId"] = ""
        config["redshiftUsername"] = "admin"
        config["redshiftSecretId"] = ""
        config["redshiftClusterId"] = ""
        config["redshiftHost"] = ""
        config["redshiftDB"] = ""
        config["rdsUsername"] = "admin"
        config["rdsSecretId"] = ""
        config["rdsInstanceId"] = ""
        config["rdsDB"] = ""
        config["rdsPort"] = ""
        config["rdsPort"] = ""
        config["namespace"] = "default"
        config["version"] = "1"

        return config
