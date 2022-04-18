import os
import json
from aws_cdk import (
    aws_iam as iam,
    aws_ssm as ssm,
    core
)

class InfraTargetAccountStack(core.Stack):

    def __init__(self, scope: core.Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)
        self.current_dir = os.path.dirname(__file__)

        # Change to your central account
        self.central_account_id = "175760604100"

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
                            resources=[f"arn:aws:ssm:{core.Aws.REGION}:{core.Aws.ACCOUNT_ID}:parameter/infra/config"]
                        ),
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=[
                                "secretsmanager:GetSecretValue"
                            ],
                            resources=[
                                f"arn:aws:secretsmanager:{core.Aws.REGION}:{core.Aws.ACCOUNT_ID}:secret:*"
                            ]
                        ),
                    ]
                )
            }
        )

        self.quicksight_migration_target_assume_role.assume_role_policy.add_statements(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=['sts:AssumeRole'],
                principals=[iam.AccountPrincipal(self.central_account_id)]
            )
        )

        ssm.StringParameter(self, 'InfraConfigParam',
                            parameter_name='/infra/config',
                            string_value=json.dumps(self.to_dict()))

    def to_dict(self):
        config={}
        config['vpcId'] = 'vpc-035986c8ae7d23bb6'
        config['redshiftUsername'] = 'admin'
        config['redshiftPassword'] = 'redshift-admin'
        config['redshiftClusterId'] = 'datasourceredshifta2a4c071-nhrnz8a6smzb'
        config['redshiftHost'] = 'datasourceredshifta2a4c071-nhrnz8a6smzb.cpoeyrlwhvgx.us-east-1.redshift.amazonaws.com'
        config['redshiftDB'] = 'dev'
        config['rdsUsername'] = 'administrator'
        config['rdsPassword'] = 'rds-admin'
        config['rdsClusterId'] = 'optional-infra-target-accou-datasourcerds82b36008-bi5o63jmx978'
        config['namespace'] = 'default'
        config['version'] = '1'

        return config
