import asyncio
import os

from gatekeeper_ai import AsyncGatekeeperClient


async def main() -> None:
    async with AsyncGatekeeperClient(api_key=os.environ["GATEKEEPER_API_KEY"]) as client:
        completion = await client.chat(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Say hello."}],
        )
    print(completion.content)


asyncio.run(main())
