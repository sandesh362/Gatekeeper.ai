import asyncio

from gatekeeper_ai import AsyncGatekeeperClient


async def main() -> None:
    async with AsyncGatekeeperClient() as client:
        completion = await client.chat(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Say hello."}],
        )
    print(completion.content)


asyncio.run(main())

