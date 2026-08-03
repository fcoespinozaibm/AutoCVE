"""Completion callback for the private Talos source-archive integration."""

from __future__ import annotations

import base64
import json
import logging
from typing import Any

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

_PROGRESS_NODES = ("receive", "upload", "scan")


def build_talos_completion_payload(*, taskid: str, finalize_finding: dict[str, Any]) -> dict[str, str]:
    """Serialize FinalizeFinding exactly once, then encode its UTF-8 JSON as Base64."""
    serialized_result = json.dumps(finalize_finding, ensure_ascii=False, separators=(",", ":"))
    encoded_result = base64.b64encode(serialized_result.encode("utf-8")).decode("ascii")
    return {
        "taskid": taskid,
        "scantype": "sast-ai",
        "antype": "normal",
        "platformType": "formal",
        "isShift": "scan",
        "data": encoded_result,
    }


async def report_talos_progress(
    *,
    taskid: str,
    status: str,
    progress: int,
    stage: str,
    message: str,
    node_status: str,
    node_progress: int,
) -> bool:
    """Best-effort progress callback that must not interrupt a source audit."""
    callback_url = str(settings.TALOS_PROGRESS_CALLBACK_URL or "").strip()
    callback_token = str(settings.TALOS_CALLBACK_TOKEN or "").strip()
    if not callback_url or not callback_token:
        logger.warning(
            "Talos progress for taskid=%s is not configured; "
            "set TALOS_PROGRESS_CALLBACK_URL and TALOS_CALLBACK_TOKEN",
            taskid,
        )
        return False

    bounded_progress = max(0, min(100, int(progress)))
    bounded_node_progress = max(0, min(100, int(node_progress)))
    try:
        current_index = _PROGRESS_NODES.index(stage)
    except ValueError:
        logger.error("Unknown Talos progress stage %r for taskid=%s", stage, taskid)
        return False

    running_details = [
        {
            "key": key,
            "status": "completed" if index < current_index else node_status if index == current_index else "pending",
            "progress": 100 if index < current_index else bounded_node_progress if index == current_index else 0,
        }
        for index, key in enumerate(_PROGRESS_NODES)
    ]
    payload = {
        "taskid": taskid,
        "status": status,
        "progress": bounded_progress,
        "stage": stage,
        "message": message,
        "node_id": "sast-ai",
        "running_details": running_details,
    }
    try:
        timeout = httpx.Timeout(settings.TALOS_CALLBACK_TIMEOUT_SECONDS)
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(
                callback_url,
                headers={"X-Talos-Callback-Token": callback_token},
                json=payload,
            )
            response.raise_for_status()
    except Exception:
        logger.exception(
            "Talos progress callback failed for taskid=%s stage=%s node_id=%s",
            taskid,
            stage,
            payload["node_id"],
        )
        return False

    logger.info(
        "Talos progress callback delivered for taskid=%s progress=%s stage=%s node_id=%s",
        taskid,
        payload["progress"],
        stage,
        payload["node_id"],
    )
    return True


async def send_talos_completion(*, taskid: str, finalize_finding: dict[str, Any]) -> bool:
    """Post a completed audit's FinalizeFinding payload to Talos.

    A callback failure must not erase an otherwise completed audit.  The full
    result remains available from AutoCVE's Talos status endpoint for recovery.
    """
    callback_url = str(settings.TALOS_CALLBACK_URL or "").strip()
    callback_token = str(settings.TALOS_CALLBACK_TOKEN or "").strip()
    if not callback_url or not callback_token:
        logger.warning(
            "Talos audit %s completed, but callback is not configured; "
            "set TALOS_CALLBACK_URL and TALOS_CALLBACK_TOKEN",
            taskid,
        )
        return False

    payload = build_talos_completion_payload(taskid=taskid, finalize_finding=finalize_finding)
    timeout = httpx.Timeout(settings.TALOS_CALLBACK_TIMEOUT_SECONDS)
    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.post(
            callback_url,
            headers={"X-Talos-Callback-Token": callback_token},
            json=payload,
        )
        response.raise_for_status()
    logger.info("Talos completion callback delivered for taskid=%s", taskid)
    return True
