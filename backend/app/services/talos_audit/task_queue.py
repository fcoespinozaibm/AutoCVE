from __future__ import annotations

import inspect
from typing import Any, Optional
from uuid import uuid4

from app.core.config import settings

TALOS_AUDIT_JOB_NAME = "run_talos_audit"


class TalosAuditQueue:
    """Enqueue Talos jobs on the existing agent-worker ARQ queue."""

    def __init__(self, *, arq_pool: Optional[Any] = None, redis_url: Optional[str] = None):
        self.arq_pool = arq_pool
        self.redis_url = redis_url or settings.REDIS_URL
        self._owns_pool = arq_pool is None

    async def _pool(self):
        if self.arq_pool is None:
            from arq import create_pool
            from arq.connections import RedisSettings

            self.arq_pool = await create_pool(
                RedisSettings.from_dsn(self.redis_url),
                default_queue_name=settings.AGENT_TASK_QUEUE_NAME,
            )
        return self.arq_pool

    async def enqueue(self, job_id: str) -> Any:
        """Submit one execution attempt and fail closed when ARQ deduplicates it.

        A Talos task ID may be retried after a failed or cancelled execution.
        Therefore the ARQ job ID identifies an individual dispatch attempt, not
        merely the persistent ``TalosAuditJob`` database record.
        """
        pool = await self._pool()
        dispatch_id = f"talos-audit:{job_id}:{uuid4()}"
        enqueued_job = await pool.enqueue_job(
            TALOS_AUDIT_JOB_NAME,
            str(job_id),
            _job_id=dispatch_id,
            _queue_name=settings.AGENT_TASK_QUEUE_NAME,
        )
        if enqueued_job is None:
            # ARQ returns None when a job with the supplied _job_id already
            # exists.  This should never occur with a per-dispatch UUID, and
            # treating it as success leaves a database-only "queued" job.
            raise RuntimeError(f"ARQ did not accept Talos audit dispatch {dispatch_id}")
        return enqueued_job

    async def close(self) -> None:
        if not self._owns_pool or self.arq_pool is None:
            return
        close = getattr(self.arq_pool, "close", None)
        if callable(close):
            result = close()
            if inspect.isawaitable(result):
                await result


async def enqueue_talos_audit_job(job_id: str) -> Any:
    queue = TalosAuditQueue()
    try:
        return await queue.enqueue(job_id)
    finally:
        await queue.close()
