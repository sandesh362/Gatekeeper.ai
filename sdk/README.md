# Gatekeeper.ai Python SDK

Put Gatekeeper in front of your existing LLM calls with a small, familiar client. The SDK sends requests to Gatekeeper's `/v1/chat` proxy; configure your provider credentials on the Gatekeeper backend as usual.

## Install

```bash
pip install -e ./sdk
```

The only runtime dependency is `httpx`. Python 3.10+ is required.

## Quick start

```python
from gatekeeper_ai import GatekeeperBlockedError, GatekeeperClient

with GatekeeperClient() as client:
    try:
        completion = client.chat(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Explain TLS simply."}],
            max_tokens=150,
        )
        print(completion.choices[0].message.content)
        print(completion.gatekeeper_metadata.risk_score)
    except GatekeeperBlockedError as exc:
        print(f"Blocked: {exc.risk_score=} {exc.category=} {exc.request_id=}")
```

`GatekeeperClient` defaults to `http://localhost:8000`. Set `GATEKEEPER_BASE_URL` and, if your deployment requires it, `GATEKEEPER_API_KEY`; constructor values take precedence.

## Drop-in OpenAI-style usage

For existing OpenAI chat-completions call sites, change the import:

```python
# Before: from openai import OpenAI
from gatekeeper_ai.compat import GatekeeperOpenAI as OpenAI

client = OpenAI()
completion = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "Hello"}],
)
print(completion.choices[0].message.content)
```

The compatibility layer has no OpenAI SDK dependency. It implements the chat-completions surface backed by the current Gatekeeper proxy; it is intentionally not a replacement for unrelated OpenAI APIs such as embeddings, files, streaming, or responses.

## API reference

### `GatekeeperClient(base_url=None, api_key=None, provider="openai", *, timeout=60.0)`

Creates a synchronous client. `provider` may be `"openai"` or `"anthropic"`. Use it as a context manager or call `close()` when done.

### `.chat(messages, model, **kwargs)`

Creates one protected completion. `messages` is a list of role/content dictionaries and `model` is the provider model name. The current Gatekeeper `/v1/chat` contract additionally supports `max_tokens` and `client_id` keyword arguments.

It returns `GatekeeperChatCompletion`, which exposes `choices[0].message.content`, `content`, `model`, `usage`, and `gatekeeper_metadata`. `gatekeeper_metadata` contains `risk_score`, `decision`, `request_id`, `categories`, and `canary_triggered`.

Blocked requests raise `GatekeeperBlockedError` before they reach the provider. Its `risk_score`, `category`, `categories`, and `request_id` attributes make it easy to handle or log safely. Timeouts and network failures raise `GatekeeperConnectionError`, including the proxy URL to check. Other non-success API responses raise `GatekeeperAPIError`.

### `AsyncGatekeeperClient`

The asynchronous counterpart has the same constructor and `await client.chat(...)` method. Use `async with` or `await client.aclose()`.

## Dashboard

Every returned metadata object and blocked exception includes the Gatekeeper `request_id`. Use it to find the request in the live dashboard at the Gatekeeper application URL (normally `http://localhost:5173` in local development).

## Examples

See `examples/basic_usage.py`, `examples/async_usage.py`, `examples/blocked_request_handling.py`, and `examples/drop_in_replacement.py`.

