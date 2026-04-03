import asyncio
import time
from typing import Any

import aiohttp

from config import config


class YadioCache:
    def __init__(self, session: aiohttp.ClientSession):
        self._session = session
        self._data: dict[str, Any] = {}
        self._last_refreshed = 0.0
        self._lock = asyncio.Lock()

    @property
    def btc_price(self) -> float:
        return self._data['BTC']

    @property
    def eur_dolar_rate(self) -> float:
        return self._data['EUR']['USD']

    async def refresh(self) -> None:
        async with self._lock:
            if time.monotonic() - self._last_refreshed < config.yadio_cache_ttl:
                return

            async with self._session.get(config.yadio_api_endpoint) as response:
                self._data = await response.json()

        self._last_refreshed = time.monotonic()
