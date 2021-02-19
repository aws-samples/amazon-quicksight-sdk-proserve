import os
import json
from aws_cdk import (
    aws_apigateway as apigw,
    aws_events as events,
    aws_ec2 as ec2,
    aws_events_targets as targets,
    aws_lambda as _lambda,
    aws_iam as iam,
    aws_redshift as redshift,
    aws_rds as rds,
    aws_s3 as s3,
    aws_ssm as ssm,
    aws_secretsmanager as secrets,
    core
)

class InfraStack(core.Stack):

    def __init__(self, scope: core.Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)
        self.current_dir = os.path.dirname(__file__)

        self.quicksight_migration_source_assume_role = iam.Role(
            self, 'quicksight-migration-source-assume-role',
            description='Role for the Quicksight dashboard migration Lambdas to assume',
            role_name='quicksight-migration-source-assume-role',
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

        self.quicksight_migration_source_assume_role.assume_role_policy.add_statements(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=['sts:AssumeRole'],
                principals=[iam.AccountPrincipal("123456789123")]
            )
        )

        self.vpc = ec2.Vpc(self, "VPC",
            cidr="10.0.0.0/21",
            max_azs=3,
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    cidr_mask=28,
                    name="Database",
                    subnet_type=ec2.SubnetType.ISOLATED,
                )
            ]
        )

        self.vpc.add_interface_endpoint("redshift_endpoint",
            service=ec2.InterfaceVpcEndpointAwsService("redshift")
        )

        self.vpc.add_interface_endpoint("rds_endpoint",
            service=ec2.InterfaceVpcEndpointAwsService("rds")
        )

        self.redshift_secret = secrets.Secret(self,'redshift-admin',
            secret_name='redshift-admin',
            description="This secret has generated admin secret password for Redshift cluster",
            generate_secret_string=secrets.SecretStringGenerator(
                secret_string_template='{"username": "admin"}',
                generate_string_key='password',
                password_length=32,
                exclude_characters='"@\\\/',
                exclude_punctuation=True
            )
        )

        self.redshift_cluster = redshift.Cluster(self, "datasource-redshift",
            master_user=redshift.Login(
                master_username="admin",
                master_password=self.redshift_secret.secret_value_from_json('password')
            ),
            vpc=self.vpc,
            vpc_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.ISOLATED
            )
        )

        self.rds_secret = secrets.Secret(self,'rds-admin',
            secret_name='rds-admin',
            description="This secret has generated admin secret password for RDS cluster",
            generate_secret_string=secrets.SecretStringGenerator(
                secret_string_template='{"username": "admin"}',
                generate_string_key='password',
                password_length=32,
                exclude_characters='"@\\\/',
                exclude_punctuation=True
            )
        )

        self.rds_cluster = rds.DatabaseCluster(self, "datasource-rds",
            engine=rds.DatabaseClusterEngine.aurora_mysql(
                version=rds.AuroraMysqlEngineVersion.VER_2_08_1),
            instance_props={
                "vpc_subnets": {
                    "subnet_type": ec2.SubnetType.ISOLATED
                },
                "vpc": self.vpc
            },
            credentials=rds.Credentials.from_secret(self.rds_secret)
        )

        ssm.StringParameter(self, 'InfraConfigParam',
                            parameter_name='/infra/config',
                            string_value=json.dumps(self.to_dict()))

    def to_dict(self):
        config={}
        config['vpcId'] = self.vpc.vpc_id
        config['redshiftUsername'] = 'admin'
        config['redshiftPassword'] = self.redshift_secret.secret_name
        config['redshiftClusterId'] = self.redshift_cluster.cluster_name
        config['redshiftHost'] = self.redshift_cluster.cluster_endpoint.hostname
        config['redshiftDB'] = 'dev'
        config['rdsUsername'] = 'admin'
        config['rdsPassword'] = self.rds_secret.secret_name
        config['rdsClusterId'] = self.rds_cluster.cluster_identifier
        config['namespace'] = 'default'
        config['version'] = '1'

        return config
