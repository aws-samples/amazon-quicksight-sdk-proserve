"""QuickSight"""
import os
from aws_cdk import core

from cdk.quicksight_status_stack import QuicksightStatusStack
from cdk.quicksight_migration_stack import QuicksightMigrationStack
from cdk.infra_stack import InfraStack
from cdk.infra_target_account_stack import InfraTargetAccountStack
from cdk.quicksight_embed_stack import QuicksightEmbedStack

ENV = core.Environment(
    account=os.environ.get("CDK_DEPLOY_ACCOUNT", os.environ["CDK_DEFAULT_ACCOUNT"]),
    region=os.environ.get("CDK_DEPLOY_REGION", os.environ["CDK_DEFAULT_REGION"])
)

app = core.App()

infra = InfraStack(
    app, id="infra-stack",
    env=ENV
)

infra_target_account = InfraTargetAccountStack(
    app, id="infra-target-account-stack",
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

quicksight_embed = QuicksightEmbedStack(
    app, id="quicksight-embed-stack",
    env=ENV
)

app.synth()
