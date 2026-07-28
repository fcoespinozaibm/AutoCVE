from __future__ import annotations

import base64
import json

import httpx
import pytest

from app.services.talos_audit.callback import build_talos_completion_payload, send_talos_completion


def test_build_talos_completion_payload_base64_encodes_utf8_json():
    final_payload = {"findings": [{"title": "路径遍历"}], "summary": "已完成"}

    payload = build_talos_completion_payload(taskid="task-1", finalize_finding=final_payload)

    assert payload | {"data": ""} == {
        "taskid": "task-1",
        "scantype": "ai",
        "antype": "normal",
        "platformType": "formal",
        "isShift": "scan",
        "data": "",
    }
    assert json.loads(base64.b64decode(payload["data"]).decode("utf-8")) == final_payload


@pytest.mark.asyncio
async def test_send_talos_completion_posts_expected_contract(monkeypatch):
    captured: dict[str, object] = {}

    def callback(request: httpx.Request) -> httpx.Response:
        captured["headers"] = dict(request.headers)
        captured["json"] = json.loads(request.content)
        return httpx.Response(200, json={"ok": True})

    transport = httpx.MockTransport(callback)
    real_async_client = httpx.AsyncClient

    class FakeAsyncClient:
        def __init__(self, *args, **kwargs):
            self._client = real_async_client(transport=transport)

        async def __aenter__(self):
            return self._client

        async def __aexit__(self, *args):
            await self._client.aclose()

    from app.services.talos_audit import callback as callback_module

    monkeypatch.setattr(callback_module.settings, "TALOS_CALLBACK_URL", "http://talos.test/api/v1/complete")
    monkeypatch.setattr(callback_module.settings, "TALOS_CALLBACK_TOKEN", "callback-secret")
    monkeypatch.setattr(callback_module.httpx, "AsyncClient", FakeAsyncClient)

    assert await send_talos_completion(taskid="task-1", finalize_finding={"ok": True}) is True
    assert captured["headers"]["x-talos-callback-token"] == "callback-secret"
    assert captured["json"]["taskid"] == "task-1"
    assert json.loads(base64.b64decode(captured["json"]["data"]).decode("utf-8")) == {"ok": True}
