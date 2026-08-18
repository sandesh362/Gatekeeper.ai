import asyncio
import unittest

import httpx
from gatekeeper_ai import AsyncGatekeeperClient, GatekeeperBlockedError, GatekeeperClient


def _response(request: httpx.Request) -> httpx.Response:
    assert request.url.path == "/v1/chat"
    assert request.json() if hasattr(request, "json") else True
    return httpx.Response(
        200,
        json={
            "request_id": "req-123",
            "provider": "openai",
            "model": "gpt-4o-mini",
            "content": "Hello!",
            "latency_ms": 12,
            "usage": {"prompt_tokens": 2, "completion_tokens": 3, "total_tokens": 5},
            "detection": {"risk_score": 10, "decision": "PASS", "categories": []},
        },
    )


class ClientTests(unittest.TestCase):
    def test_successful_chat_returns_openai_like_shape(self) -> None:
        http_client = httpx.Client(transport=httpx.MockTransport(_response))
        client = GatekeeperClient(http_client=http_client)
        completion = client.chat([{"role": "user", "content": "Hi"}], "gpt-4o-mini", max_tokens=10)
        self.assertEqual(completion.choices[0].message.content, "Hello!")
        self.assertEqual(completion.content, "Hello!")
        self.assertEqual(completion.usage.total_tokens, 5)

    def test_blocked_response_exposes_attributes(self) -> None:
        def blocked(_: httpx.Request) -> httpx.Response:
            return httpx.Response(403, headers={"X-Request-ID": "abc-123"}, json={"risk_score": 87, "categories": ["jailbreak"]})

        client = GatekeeperClient(http_client=httpx.Client(transport=httpx.MockTransport(blocked)))
        with self.assertRaises(GatekeeperBlockedError) as caught:
            client.chat([{"role": "user", "content": "bad"}], "gpt-4o-mini")
        self.assertEqual(caught.exception.risk_score, 87)
        self.assertEqual(caught.exception.category, "jailbreak")
        self.assertEqual(caught.exception.request_id, "abc-123")

    def test_flagged_response_attaches_metadata(self) -> None:
        def flagged(_: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json={"request_id": "flag-1", "provider": "openai", "model": "x", "content": "OK", "latency_ms": 4, "detection": {"risk_score": 48, "decision": "FLAG", "categories": ["prompt_injection"]}})

        client = GatekeeperClient(http_client=httpx.Client(transport=httpx.MockTransport(flagged)))
        completion = client.chat([{"role": "user", "content": "Hi"}], "x")
        self.assertEqual(completion.gatekeeper_metadata.decision, "FLAG")
        self.assertEqual(completion.gatekeeper_metadata.risk_score, 48)
        self.assertEqual(completion.gatekeeper_metadata.request_id, "flag-1")

    def test_async_client(self) -> None:
        async def run() -> None:
            http_client = httpx.AsyncClient(transport=httpx.MockTransport(_response))
            client = AsyncGatekeeperClient(http_client=http_client)
            completion = await client.chat([{"role": "user", "content": "Hi"}], "gpt-4o-mini")
            self.assertEqual(completion.content, "Hello!")
            await http_client.aclose()

        asyncio.run(run())
