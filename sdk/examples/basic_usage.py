"""Run with Gatekeeper on http://localhost:8000 and provider credentials configured there."""

import os
from gatekeeper_ai import GatekeeperClient

with GatekeeperClient(api_key=os.environ["GATEKEEPER_API_KEY"]) as client:
    completion = client.chat(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "Explain recursion in one sentence."}],
        max_tokens=100,
    )

print(completion.choices[0].message.content)
print(completion.gatekeeper_metadata)
