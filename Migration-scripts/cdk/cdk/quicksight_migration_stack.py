import os
from aws_cdk import (
    aws_apigateway as apigw,
    aws_lambda as _lambda,
    aws_lambda_event_sources as event_sources,
    aws_iam as iam,
    aws_s3 as s3,
    aws_sqs as sqs,
    core
)

from aws_solutions_constructs.aws_apigateway_sqs import (
    ApiGatewayToSqs,
    ApiGatewayToSqsProps
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
                                "quicksight:Create*",
                                "quicksight:Delete*",
                                "quicksight:Describe*",
                                "quicksight:List*",
                                "quicksight:Search*",
                                "quicksight:Update*"
                            ],
                            resources=["*"]
                        )
                    ]
                )
            }
        )

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
                                "quicksight:Create*",
                                "quicksight:Delete*",
                                "quicksight:Describe*",
                                "quicksight:List*",
                                "quicksight:Search*",
                                "quicksight:Update*"
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
                principals=[iam.AccountPrincipal(core.Aws.ACCOUNT_ID)]
            )
        )

        # API Gateway to SQS
        self.apigw_sqs = ApiGatewayToSqs(
            self, "ApiGatewayToSQSqsMigration",
            allow_create_operation=True,
            allow_read_operation=False,
            allow_delete_operation=False,
            api_gateway_props=apigw.RestApiProps(
                rest_api_name="quicksight-migration-sqs",
                deploy=True,
                default_method_options=apigw.MethodOptions(
                    authorization_type=apigw.AuthorizationType.NONE
                ),
                default_cors_preflight_options=apigw.CorsOptions(
                    allow_origins = apigw.Cors.ALL_ORIGINS,
                    allow_methods = apigw.Cors.ALL_METHODS,
                    allow_headers=['Access-Control-Allow-Origin','Access-Control-Allow-Headers','Content-Type']
                ),
                policy=iam.PolicyDocument(
                    statements=[
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=[
                                'execute-api:Invoke'
                            ],
                            resources=["execute-api:/prod/*"],
                            principals=[
                                iam.ArnPrincipal("*")
                            ]
                        )
                    ]
                )
            ),
            queue_props=sqs.QueueProps(
                queue_name="quicksight-migration-sqs",
                visibility_timeout=core.Duration.minutes(15)
            )
        )

        self.quicksight_migration_lambda = _lambda.Function(
            self, 'quicksight-migration-lambda',
            handler='quicksight_migration.lambda_function.lambda_handler',
            runtime=_lambda.Runtime.PYTHON_3_8,
            code=_lambda.Code.from_asset(os.path.join(self.current_dir,
                                                        '../lambda/quicksight_migration/')),
            function_name='quicksight_migration_lambda',
            role=self.quicksight_migration_lambda_role,
            timeout=core.Duration.minutes(15),
            memory_size=1024,
            environment={
                'BUCKET_NAME': self.bucket.bucket_name,
                'S3_KEY': 'None',
                'INFRA_CONFIG_PARAM': '/infra/config',
                'SQS_URL': self.apigw_sqs.sqs_queue.queue_url
            }
        )

        self.quicksight_migration_lambda.add_event_source(
            event_sources.SqsEventSource(
                enabled=True,
                queue=self.apigw_sqs.sqs_queue,
            )
        )

        core.CfnOutput(self, "MigrationAPIGatewayURL",
            value=self.apigw_sqs.api_gateway.url,
            description="Migration API GW URL"
        )
