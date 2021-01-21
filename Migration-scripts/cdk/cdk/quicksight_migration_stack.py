import os
from aws_cdk import (
    aws_apigateway as apigw,
    aws_events as events,
    aws_events_targets as targets,
    aws_lambda as _lambda,
    aws_iam as iam,
    aws_s3 as s3,
    core
)

from aws_solutions_constructs.aws_apigateway_lambda import (
    ApiGatewayToLambda
)

class QuicksightMigrationStack(core.Stack):

    def __init__(self, scope: core.Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)
        self.current_dir = os.path.dirname(__file__)

        self.bucket = s3.Bucket(
            self, "qs-migration-bucket",
            bucket_name=f'quicksight-migration-{core.Aws.ACCOUNT_ID}',
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
        )

        self.quicksight_migration_lambda_role = iam.Role(
            self, 'quicksight-migration-lambda-role',
            description='Role for the Quicksight dashboard migration Lambdas',
            role_name='quicksight-migration-lambda-role',
            max_session_duration=core.Duration.seconds(3600),
            assumed_by=iam.ServicePrincipal('lambda.amazonaws.com'),
            inline_policies={
                'AllowAccess': iam.PolicyDocument(
                    statements=[
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=[
                                'logs:CreateLogGroup',
                                'logs:CreateLogStream',
                                'logs:PutLogEvents'
                            ],
                            resources=[f'arn:aws:logs:{core.Aws.REGION}:{core.Aws.ACCOUNT_ID}:*']
                        ),
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=[
                                "sts:AssumeRole",
                                "iam:ListRoles"
                            ],
                            resources=[
                                "arn:aws:iam::*:role/quicksight-migration-*-assume-role"
                            ]
                        ),
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=[
                                "s3:PutObject",
                                "s3:ListBucket"
                            ],
                            resources=[
                                self.bucket.bucket_arn,
                                f"{self.bucket.bucket_arn}/*"
                            ]
                        ),
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=[
                                "secrets:GetSecretValue"
                            ],
                            resources=[
                                f"arn:aws:secretsmanager:{core.Aws.REGION}:{core.Aws.ACCOUNT_ID}:secret:*"
                            ]
                        ),
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=[
                                "quicksight:*",
                            ],
                            resources=["*"]
                        )
                    ]
                )
            }
        )

        self.apigw_lambda = ApiGatewayToLambda(
            self, "ApiGatewayToLambdaQSMigration",
            api_gateway_props=apigw.RestApiProps(
                rest_api_name="quicksight-migration",
                default_method_options=apigw.MethodOptions(
                    authorization_type=apigw.AuthorizationType.IAM
                )
            ),
            lambda_function_props=_lambda.FunctionProps(
                handler='lambda_handler.lambda_handler',
                runtime=_lambda.Runtime.PYTHON_3_8,
                code=_lambda.Code.from_asset(os.path.join(self.current_dir,
                                                            '../lambda/quicksight_migration/')),
                function_name='quicksight_migration',
                role=self.quicksight_migration_lambda_role,
                timeout=core.Duration.minutes(15),
                memory_size=512,
                environment={
                    'BUCKET_NAME': self.bucket.bucket_name,
                    'S3_KEY': 'sales/manifest.json',
                    'INFRA_CONFIG_PARAM': '/infra/config'
                }
            )
        )
