import os
from aws_cdk import core


from cdk.quicksight_migration_stack import QuicksightMigrationStack # main migration stack
from cdk.quicksight_target_stack import QuicksightTargetStack # target acct stack

app = core.App()

QuicksightMigrationStack(
    app, id="quicksight-migration-stack",
    env=core.Environment(
    account=os.environ["CDK_CENTRAL_ACCOUNT"],
    region=os.environ["CDK_CENTRAL_REGION"]))

QuicksightTargetStack(
    app, id="quicksight-target-stack",
    env=core.Environment(
    account=os.environ["CDK_TARGET_ACCOUNT"],
    region=os.environ["CDK_TARGET_REGION"]),
    central_account=os.environ["CDK_CENTRAL_ACCOUNT"])

app.synth()