import asyncio

import aiohttp

from config import config


async def fetch_html(url: str, session: aiohttp.ClientSession, delay: float = 0.0) -> str | None:
    for _ in range(config.html_fetch_attempts):
        await asyncio.sleep(delay)

        try:
            async with session.get(url) as response:
                return await response.text()
        except TimeoutError, aiohttp.ClientError:
            delay = 1
