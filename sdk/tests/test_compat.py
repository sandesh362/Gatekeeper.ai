import httpx
import os
import unittest
from unittest.mock import patch

from gatekeeper_ai.compat import GatekeeperOpenAI

os.environ["GATEKEEPER_API_KEY"] = "gk_test_key"


class CompatibilityTests(unittest.TestCase):
    def test_compat_exposes_openai_style_chat_completion(self) -> None:
        def handler(_: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json={"request_id": "r1", "provider": "openai", "model": "gpt", "content": "Compatible", "latency_ms": 1, "detection": {"risk_score": 0, "decision": "PASS"}})

        from gatekeeper_ai import compat
        from gatekeeper_ai import GatekeeperClient

        protected_client = GatekeeperClient(http_client=httpx.Client(transport=httpx.MockTransport(handler)))
        with patch.object(compat, "GatekeeperClient", return_value=protected_client):
            client = GatekeeperOpenAI()
            response = client.chat.completions.create(model="gpt", messages=[{"role": "user", "content": "Hi"}])
        self.assertEqual(response.choices[0].message.content, "Compatible")
        self.assertEqual(response.gatekeeper_metadata.request_id, "r1")
