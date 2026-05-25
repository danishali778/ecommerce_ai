from app.repositories.models import Integration, Store


def schedule_all_store_syncs(module) -> list[str]:
    queued_sync_run_ids: list[str] = []
    connected_stores = (
        module.db.query(Store)
        .join(Integration, Integration.store_id == Store.id)
        .filter(Store.connection_status == "connected", Integration.status == "connected")
        .all()
    )
    for store in connected_stores:
        if module.sync_repository.get_active_sync_run(store.id):
            continue
        integration = (
            module.db.query(Integration).filter(Integration.store_id == store.id, Integration.provider == "shopify").one_or_none()
        )
        if integration is None:
            continue
        sync_run = module.sync_repository.create_sync_run(
            organization_id=store.organization_id,
            store_id=store.id,
            integration_id=integration.id,
            mode="scheduled_full",
            status="queued",
            triggered_by_user_id=None,
            entity_counts_json={},
            error_details_json={},
        )
        module.db.commit()
        queued_sync_run_ids.append(str(sync_run.id))
    return queued_sync_run_ids

