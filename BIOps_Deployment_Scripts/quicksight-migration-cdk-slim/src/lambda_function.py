import logging
from quicksight_migration import MigrateAssets

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def lambda_handler(event, context):
    source_account_id = event["source_account_id"]
    source_role_name = event["source_role_name"]
    target_account_id = event["target_account_id"]
    target_role_name = event["target_role_name"]
    source_region = event["source_region"]
    target_region = event["target_region"]
    target_admin_users = event["target_admin_users"]
    target_admin_groups = event["target_admin_groups"]
    migration_items = event["migration_items"]

    if not migration_items or len(list(migration_items.keys())) < 1:
        logger.error("The migration_items is missing or migration_items list is empty")
        raise ValueError("Required parameters were not given")

    MigrateAssets(
        source_region,
        source_account_id,
        source_role_name,
        target_region,
        target_account_id,
        target_role_name,
        target_admin_users,
        target_admin_groups,
        migration_items
    )

