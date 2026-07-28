"""Completion callback for the private Talos source-archive integration."""

from __future__ import annotations

import base64
import json
import logging
from typing import Any

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


def build_talos_completion_payload(*, taskid: str, finalize_finding: dict[str, Any]) -> dict[str, str]:
    """Serialize FinalizeFinding exactly once, then encode its UTF-8 JSON as Base64."""
    serialized_result = json.dumps(finalize_finding, ensure_ascii=False, separators=(",", ":"))
    encoded_result = base64.b64encode(serialized_result.encode("utf-8")).decode("ascii")
    return {
        "taskid": taskid,
        "scantype": "ai",
        "antype": "normal",
        "platformType": "formal",
        "isShift": "scan",
        "data": encoded_result,
    }


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
