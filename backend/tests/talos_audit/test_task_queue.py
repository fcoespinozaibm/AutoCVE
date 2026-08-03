import pytest

from app.services.talos_audit.task_queue import TALOS_AUDIT_JOB_NAME, TalosAuditQueue


class _FakeArqPool:
    def __init__(self, *, enqueue_result=object()):
        self.enqueue_result = enqueue_result
        self.jobs = []

    async def enqueue_job(self, function, *args, **kwargs):
        self.jobs.append((function, args, kwargs))
        return self.enqueue_result


@pytest.mark.asyncio
async def test_talos_queue_uses_a_unique_arq_id_for_each_dispatch(monkeypatch):
    from app.core.config import settings

    monkeypatch.setattr(settings, "AGENT_TASK_QUEUE_NAME", "agent:q")
    pool = _FakeArqPool()
    queue = TalosAuditQueue(arq_pool=pool)

    await queue.enqueue("talos-job")
    await queue.enqueue("talos-job")

    first_job_id = pool.jobs[0][2]["_job_id"]
    second_job_id = pool.jobs[1][2]["_job_id"]
    assert first_job_id.startswith("talos-audit:talos-job:")
    assert second_job_id.startswith("talos-audit:talos-job:")
    assert first_job_id != second_job_id
    assert pool.jobs[0][0] == TALOS_AUDIT_JOB_NAME
    assert pool.jobs[0][1] == ("talos-job",)
    assert pool.jobs[0][2]["_queue_name"] == "agent:q"


@pytest.mark.asyncio
async def test_talos_queue_rejects_unaccepted_arq_dispatch():
    queue = TalosAuditQueue(arq_pool=_FakeArqPool(enqueue_result=None))

    with pytest.raises(RuntimeError, match="ARQ did not accept Talos audit dispatch"):
        await queue.enqueue("talos-job")
