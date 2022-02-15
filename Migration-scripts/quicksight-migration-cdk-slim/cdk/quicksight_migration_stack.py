import os
from constructs import Construct
from aws_cdk import aws_lambda, aws_iam as iam, core


class QuicksightMigrationStack(core.Stack):
    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)
        self.current_dir = os.path.dirname(__file__)

        self.quicksight_migration_lambda_role = iam.Role(
            self,
            "quicksight-migration-lambda-role",
            description="Role for the Quicksight dashboard migration Lambdas",
            role_name="quicksight-migration-lambda-role",
            max_session_duration=core.Duration.seconds(3600),
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            inline_policies={
                "AllowAccess": iam.PolicyDocument(
                    statements=[
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=[
                                "logs:CreateLogGroup",
                                "logs:CreateLogStream",
                                "logs:PutLogEvents",
                            ],
                            resources=[
                                f"arn:aws:logs:{core.Aws.REGION}:{core.Aws.ACCOUNT_ID}:*"
                            ],
                        ),
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=["sts:AssumeRole", "iam:ListRoles"],
                            resources=["arn:aws:iam::*:role/quicksight-migration-*"],
                        ),
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=["secrets:GetSecretValue"],
                            resources=[
                                f"arn:aws:secretsmanager:{core.Aws.REGION}:{core.Aws.ACCOUNT_ID}:secret:*"
                            ],
                        ),
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=["quicksight:*"],
                            resources=["*"],
                        ),
                        iam.PolicyStatement(
                            effect=iam.Effect.DENY,
                            actions=["quicksight:Unsubscribe"],
                            resources=["*"],
                        ),
                    ]
                )
            },
        )
        self.quicksight_migration_lambda_role.assume_role_policy.add_statements(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=["sts:AssumeRole"],
                principals=[iam.AccountPrincipal(core.Aws.ACCOUNT_ID)]
            )
        )

        self.QuickSightMigration = aws_lambda.Function(
            self,
            "quicksight-migration-lambda",
            handler="lambda_function.lambda_handler",
            runtime=aws_lambda.Runtime.PYTHON_3_8,
            code=aws_lambda.Code.from_asset(os.path.join(self.current_dir, "../src/")),
            function_name="quicksight_migration_lambda",
            role=self.quicksight_migration_lambda_role,
            timeout=core.Duration.minutes(15),
            memory_size=1024,
        )
