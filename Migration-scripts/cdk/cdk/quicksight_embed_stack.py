import os
from aws_cdk import (
    aws_apigateway as apigw,
    aws_cloudfront as cloudfront,
    aws_cloudfront_origins as origins,
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

        self.website_bucket = s3.Bucket(
            self, "qs-embed-bucket",
            bucket_name=f'quicksight-embed-{core.Aws.ACCOUNT_ID}',
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL
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
                'DASHBOARD_ID': 'CHANGEME_DASHBOARD_ID',
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
        self.embedurl.add_method("GET",
            method_responses=[{
                'statusCode': '200',
                'responseParameters': {
                    'method.response.header.Access-Control-Allow-Headers': True,
                    'method.response.header.Access-Control-Allow-Methods': True,
                    'method.response.header.Access-Control-Allow-Origin': True
                }
            }],
            integration=apigw.LambdaIntegration(
                self.quicksight_migration_lambda,
                proxy=False,
                integration_responses=[{
                    'statusCode': '200',
                    'responseTemplates':{"application/json": ""},
                    'responseParameters': {
                        'method.response.header.Access-Control-Allow-Headers': "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'",
                        'method.response.header.Access-Control-Allow-Origin': "'*'",
                        'method.response.header.Access-Control-Allow-Methods': "'GET'"
                    }
                }]
            )
        )

        self.embedurl.add_method('OPTIONS', apigw.MockIntegration(
            integration_responses=[{
                'statusCode': '200',
                'responseParameters': {
                    'method.response.header.Access-Control-Allow-Headers': "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'",
                    'method.response.header.Access-Control-Allow-Origin': "'*'",
                    'method.response.header.Access-Control-Allow-Methods': "'GET,OPTIONS'"
                }
            }],
            passthrough_behavior=apigw.PassthroughBehavior.WHEN_NO_MATCH,
            request_templates={"application/json":"{\"statusCode\":200}"}
            ),
            method_responses=[{
                'statusCode': '200',
                'responseParameters': {
                    'method.response.header.Access-Control-Allow-Headers': True,
                    'method.response.header.Access-Control-Allow-Methods': True,
                    'method.response.header.Access-Control-Allow-Origin': True
                    }
                }
            ]
        )

        # Cloudfront Distribution for authentication
        self.embed_auth_lambda_role = iam.Role(
            self, 'embed-auth-lambda-role',
            description='Role for the Quicksight dashboard embed authentication Lambda',
            role_name='embed-auth-lambda-role',
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
                        )
                    ]
                )
            }
        )

        self.embed_auth_lambda = _lambda.Function(
            self, 'embed-auth-lambda',
            handler='index.handler',
            description="A Lambda@Edge function for QuickSight embed authentication via CloudFront Distribution",
            runtime=_lambda.Runtime.NODEJS_10_X,
            code=_lambda.Code.from_asset(os.path.join(self.current_dir,
                                                        '../lambda/embed_auth/')),
            function_name='embed_auth_lambda',
            role=self.embed_auth_lambda_role,
            timeout=core.Duration.seconds(5),
            memory_size=128
        )

        self.embed_auth_dist = cloudfront.Distribution(
            self, "embed-auth-dist",
            enabled=True,
            default_root_object="index.html",
            default_behavior=cloudfront.BehaviorOptions(
                origin=origins.S3Origin(self.website_bucket),
                allowed_methods= cloudfront.AllowedMethods.ALLOW_GET_HEAD,
                edge_lambdas=[
                    {
                        "functionVersion": self.embed_auth_lambda.current_version,
                        "eventType": cloudfront.LambdaEdgeEventType.VIEWER_REQUEST,
                        "includeBody": True
                    }
                ]
            )
        )

        core.CfnOutput(self, "EmbedAPIGatewayURL",
            value=self.apigw_lambda.api_gateway.url+"embedurl?",
            description="Embed API GW URL"
        )

        core.CfnOutput(self, "EmbedCloudFrontURL",
            value="https://"+self.embed_auth_dist.distribution_domain_name,
            description="CloudFront Distribution URL"
        )
