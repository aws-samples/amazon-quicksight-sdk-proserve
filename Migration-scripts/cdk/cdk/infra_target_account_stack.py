import os
from aws_cdk import (
    aws_iam as iam,
    core
)

class InfraTargetAccountStack(core.Stack):

    def __init__(self, scope: core.Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)
        self.current_dir = os.path.dirname(__file__)

        self.quicksight_migration_target_assume_role = iam.Role(
            self, 'quicksight-migration-target-assume-role',
            description='Role for the Quicksight dashboard migration Lambdas to assume',
            role_name='quicksight-migration-target-assume-role',
            max_session_duration=core.Duration.seconds(3600),
            assumed_by=iam.ServicePrincipal('lambda.amazonaws.com'),
            inline_policies={
                'AllowAccess': iam.PolicyDocument(
                    statements=[
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=[
                                "quicksight:*",
                            ],
                            resources=["*"]
                        ),
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=[
                                "ssm:GetParameter",
                            ],
                            resources=["arn:aws:ssm:*:*:parameter/infra/config"]
                        )
                    ]
                )
            }
        )

        self.quicksight_migration_target_assume_role.assume_role_policy.add_statements(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=['sts:AssumeRole'],
                principals=[iam.AccountPrincipal("123456789123")]
            )
        )