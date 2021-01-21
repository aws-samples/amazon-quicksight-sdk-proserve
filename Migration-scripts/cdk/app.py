"""QuickSight"""
import os
from aws_cdk import core

from cdk.quicksight_status_stack import QuicksightStatusStack
from cdk.quicksight_migration_stack import QuicksightMigrationStack
from cdk.infra_stack import InfraStack

ENV = core.Environment(
    account=os.environ.get("CDK_DEPLOY_ACCOUNT", os.environ["CDK_DEFAULT_ACCOUNT"]),
    region=os.environ.get("CDK_DEPLOY_REGION", os.environ["CDK_DEFAULT_REGION"])
)

app = core.App()

infra = InfraStack(
    app, id="infra-stack",
    env=ENV
)

quicksight_dynamodb = QuicksightStatusStack(
    app, id="quicksight-status-stack",
    env=ENV
)

quicksight_migration = QuicksightMigrationStack(
    app, id="quicksight-migration-stack",
    env=ENV
)

app.synth()
