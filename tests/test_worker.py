import asyncio

from worker.main import WorkerSettings, heartbeat


def test_heartbeat_runs() -> None:
    asyncio.run(heartbeat({}))


def test_worker_settings_has_cron_job() -> None:
    assert len(WorkerSettings.cron_jobs) == 1
