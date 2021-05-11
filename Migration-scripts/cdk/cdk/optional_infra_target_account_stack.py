import os
from aws_cdk import (
    aws_ec2 as ec2,
    aws_iam as iam,
    aws_redshift as redshift,
    aws_rds as rds,
    aws_secretsmanager as secrets,
    core
)

class OptionalInfraTargetAccountStack(core.Stack):

    def __init__(self, scope: core.Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)
        self.current_dir = os.path.dirname(__file__)

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

        self.rs_security_group = ec2.SecurityGroup(
            self, "redshift-sg",
            vpc=self.vpc,
            allow_all_outbound=False,
            description="Redshift SG"
        )

        self.rs_security_group.add_ingress_rule(
            self.rs_security_group,
            ec2.Port.all_tcp(),
            'Redshift-basic'
        )

        self.rs_security_group.add_ingress_rule(
            # https://docs.aws.amazon.com/quicksight/latest/user/regions.html
            ec2.Peer.ipv4('52.23.63.224/27'),
            ec2.Port.tcp(5439),
            'QuickSight-basic'
        )

        self.rs_security_group.add_egress_rule(
            self.rs_security_group,
            ec2.Port.all_tcp(),
            'Allow outbound for QuickSight'
        )

        self.redshift_cluster = redshift.Cluster(self, "datasource-redshift",
            master_user=redshift.Login(
                master_username="admin",
                master_password=self.redshift_secret.secret_value_from_json('password')
            ),
            vpc=self.vpc,
            vpc_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.ISOLATED
            ),
            security_groups=[self.rs_security_group]
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
                version=rds.AuroraMysqlEngineVersion.VER_2_08_1
            ),
            instance_props={
                "vpc_subnets": {
                    "subnet_type": ec2.SubnetType.ISOLATED
                },
                "vpc": self.vpc
            },
            credentials=rds.Credentials.from_secret(self.rds_secret)
        )

        core.CfnOutput(self, "vpcId", value=self.vpc.vpc_id)
        core.CfnOutput(self, "redshiftUsername", value="admin")
        core.CfnOutput(self, "redshiftPassword", value=self.redshift_secret.secret_name)
        core.CfnOutput(self, "redshiftClusterId", value=self.redshift_cluster.cluster_name)
        core.CfnOutput(self, "redshiftHost", value=self.redshift_cluster.cluster_endpoint.hostname)
        core.CfnOutput(self, "redshiftDB", value="dev")
        core.CfnOutput(self, "rdsUsername", value="admin")
        core.CfnOutput(self, "rdsPassword", value=self.rds_secret.secret_name)
        core.CfnOutput(self, "rdsClusterId", value=self.rds_cluster.cluster_identifier)
        core.CfnOutput(self, "namespace", value="default")
        core.CfnOutput(self, "version", value="1")
