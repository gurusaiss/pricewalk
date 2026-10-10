import pytest
from fakeredis import FakeAsyncRedis

from api.routers import admin as admin_router


class _FakeArqPool:
    def __init__(self, jobs: list[object]) -> None:
        self._jobs = jobs

    async def queued_jobs(self) -> list[object]:
        return self._jobs

    async def close(self) -> None:
        pass


@pytest.mark.asyncio
async def test_admin_status_reports_queue_depth_and_paused_domains(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_redis = FakeAsyncRedis(decode_responses=True)
    await fake_redis.set("pricewalk:paused_domain:www.amazon.in", "1")
    await fake_redis.set("pricewalk:last_success:www.flipkart.com", "2026-01-01T00:00:00+00:00")

    monkeypatch.setattr(
        admin_router.Redis, "from_url", classmethod(lambda cls, *a, **k: fake_redis)
    )

    async def fake_create_pool(*_args: object, **_kwargs: object) -> _FakeArqPool:
        return _FakeArqPool(jobs=[object(), object(), object()])

    monkeypatch.setattr(admin_router, "create_pool", fake_create_pool)

    result = await admin_router.status()

    assert result["queue_depth"] == 3
    assert result["paused_domains"] == ["www.amazon.in"]
    assert result["last_success_by_domain"]["www.flipkart.com"] == "2026-01-01T00:00:00+00:00"
    assert result["last_success_by_domain"]["www.meesho.com"] is None
