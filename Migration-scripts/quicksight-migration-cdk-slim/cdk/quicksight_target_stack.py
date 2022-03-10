import os
import json
from aws_cdk import aws_iam as iam, aws_ssm as ssm, core


class QuicksightTargetStack(core.Stack):
    def __init__(self, scope: core.Construct, id: str, central_account, **kwargs) -> None:
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
                    sid="QuickSightAccess",
                    effect=iam.Effect.ALLOW,
                    actions=["quicksight:*"],
                    resources=["*"],
                    conditions={
                        "StringEquals": {
                            "quicksight:UserName": self.quicksight_migration_target_assume_role.role_name
                        }
                    },
                ),
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
