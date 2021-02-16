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

class QuicksightEmbedStack(core.Stack):

    def __init__(self, scope: core.Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)
        self.current_dir = os.path.dirname(__file__)

        self.bucket = s3.Bucket(
            self, "qs-embed-bucket",
            bucket_name=f'quicksight-embed-{core.Aws.ACCOUNT_ID}'
        )

        self.quicksight_embed_lambda_role = iam.Role(
            self, 'quicksight-embed-lambda-role',
            description='Role for the Quicksight dashboard embed Lambdas',
            role_name='quicksight-embed-lambda-role',
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

        self.quicksight_migration_lambda = _lambda.Function(
            self, 'quicksight-migration-lambda',
            handler='quicksight_embed.lambda_handler',
            runtime=_lambda.Runtime.PYTHON_3_8,
            code=_lambda.Code.from_asset(os.path.join(self.current_dir,
                                                        '../lambda/quicksight_embed/')),
            function_name='quicksight_embed_lambda',
            role=self.quicksight_embed_lambda_role,
            timeout=core.Duration.minutes(3),
            memory_size=512,
            environment={
                'DASHBOARD_ID': '938b365e-c001-4723-9a27-029654da7531',
                'QUICKSIGHT_USER_ARN': f'arn:aws:quicksight:us-east-1:{core.Aws.ACCOUNT_ID}:user/default/quicksight-migration-user'
            }
        )

        self.apigw_lambda = ApiGatewayToLambda(
            self, "ApiGatewayToLambdaQSEmbed",
            existing_lambda_obj=self.quicksight_migration_lambda,
            api_gateway_props=apigw.LambdaRestApiProps(
                rest_api_name="quicksight-embed",
                handler=self.quicksight_migration_lambda,
                deploy=True,
                proxy=False,
                default_method_options=apigw.MethodOptions(
                    authorization_type=apigw.AuthorizationType.NONE
                ),
                default_cors_preflight_options=apigw.CorsOptions(
                    allow_origins = apigw.Cors.ALL_ORIGINS,
                    allow_methods = apigw.Cors.ALL_METHODS,
                    allow_headers = ['Access-Control-Allow-Origin','Access-Control-Allow-Headers','Content-Type']
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
            )
        )

        self.embedurl = self.apigw_lambda.api_gateway.root.add_resource("embedurl")
        self.embedurl.add_method("GET")
