import os
from aws_cdk import (
    aws_dynamodb as dynamodb,
    aws_events as events,
    aws_events_targets as targets,
    aws_lambda as _lambda,
    aws_iam as iam,
    aws_s3 as s3,
    core
)

class QuicksightStatusStack(core.Stack):

    def __init__(self, scope: core.Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)
        self.current_dir = os.path.dirname(__file__)

        self.bucket = s3.Bucket(
            self, "qs-bucket",
            bucket_name=f'quicksight-dash-{core.Aws.ACCOUNT_ID}',
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,

        )

        self.quicksight_dash_info_table = dynamodb.Table(
            self,
            "quicksight-dash-info-table",
            table_name="quicksight-dash-info",
            partition_key=dynamodb.Attribute(
                name="dashboardId",
                type=dynamodb.AttributeType.STRING
            )
        )

        self.quicksight_dash_info_lambda_role = iam.Role(
            self, 'quicksight-dash-info-lambda-role',
            description='Role for the Quicksight dashboard information Lambda',
            role_name='quicksight-dash-info-lambda-role',
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
                                "dynamodb:DescribeTable", 
                                "dynamodb:PutItem",
                                "dynamodb:GetItem",
                                "dynamodb:Scan",
                                "dynamodb:UpdateItem"
                            ],
                            resources=[self.quicksight_dash_info_table.table_arn]
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
                                "quicksight:*",
                            ],
                            resources=["*"]
                        )
                    ]
                )
            }
        )

        self.quicksight_dash_info_lambda = _lambda.Function(
            self, 'quicksight-dash-info-lambda',
            handler='quicksight_dash_info.lambda_handler',
            runtime=_lambda.Runtime.PYTHON_3_7,
            code=_lambda.Code.from_asset(os.path.join(self.current_dir,
                                                        '../lambda/quicksight_dash_info/')),
            function_name='quicksight_dash_info',
            role=self.quicksight_dash_info_lambda_role,
            timeout=core.Duration.minutes(5),
            memory_size=128,
            environment={
                "TABLE_NAME": self.quicksight_dash_info_table.table_name
            }
        )

        events.Rule(
            self, 'quicksight_dash_info_event',
            description='CloudWatch cron to get QuickSight dashboards information',
            rule_name='quicksight-dash-info-event-rule',
            targets=[targets.LambdaFunction(self.quicksight_dash_info_lambda)],
            schedule=events.Schedule.rate(core.Duration.minutes(15))
        )

        self.quicksight_status = _lambda.Function(
            self, 'quicksight_status',
            handler='quicksight_status.lambda_handler',
            runtime=_lambda.Runtime.PYTHON_3_7,
            code=_lambda.Code.from_asset(os.path.join(self.current_dir,
                                                        '../lambda/quicksight_status/')),
            function_name='quicksight_status',
            role=self.quicksight_dash_info_lambda_role,
            timeout=core.Duration.minutes(15),
            memory_size=512,
            environment={
                'BUCKET_NAME': self.bucket.bucket_name
            }
        )

        events.Rule(
            self, 'quicksight_schedule_rule',
            description='CloudWatch rule to query Quicksight for service details',
            rule_name='qs-status-every-hour',
            schedule=events.Schedule.cron(minute="0"),
            targets=[targets.LambdaFunction(self.quicksight_status)]
        )
