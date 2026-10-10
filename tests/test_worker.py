import asyncio

from worker.main import WorkerSettings, heartbeat


def test_heartbeat_runs() -> None:
    asyncio.run(heartbeat({}))


def test_worker_settings_has_cron_jobs() -> None:
    assert len(WorkerSettings.cron_jobs) == 4


def test_worker_settings_registers_fetch_product() -> None:
    assert len(WorkerSettings.functions) == 1
