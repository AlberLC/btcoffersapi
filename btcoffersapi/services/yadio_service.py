from typing import Any

import aiohttp

from config import config


async def fetch_yadio_data(session: aiohttp.ClientSession()) -> dict[str, Any]:
    async with session.get(config.yadio_api_endpoint) as response:
        return await response.json()
