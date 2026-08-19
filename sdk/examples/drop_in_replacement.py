"""Only the import line changes from a typical OpenAI script."""

# Change: from openai import OpenAI
from gatekeeper_ai.compat import GatekeeperOpenAI as OpenAI
import os

client = OpenAI(api_key=os.environ["GATEKEEPER_API_KEY"])
completion = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "Give me a short haiku about secure software."}],
)
print(completion.choices[0].message.content)
print(completion.gatekeeper_metadata)
