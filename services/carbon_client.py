from __future__ import annotations

import logging
from typing import Optional

import redis
import requests

from config.cache import CACHE_TTL, carbon_intensity_key

logger = logging.getLogger(__name__)


class CarbonIntensityClient:
    def __init__(
        self,
        base_url: str,
        redis_client: redis.Redis,
        session: Optional[requests.Session] = None,
    ) -> None:
        self._base_url = base_url
        self._redis = redis_client
        self._session = session or requests.Session()

    def get_intensity_forecast(self, postcode: str) -> float:
        cache_key = carbon_intensity_key(postcode)

        cached = self._redis.get(cache_key)
        if cached is not None:
            logger.debug("Cache hit for %s", postcode)
            return float(cached)

        url = f"{self._base_url}/{postcode}"
        response = self._session.get(url, timeout=10)
        response.raise_for_status()

        payload = response.json()
        forecast: float = payload["data"][0]["data"][0]["intensity"]["forecast"]

        self._redis.setex(cache_key, CACHE_TTL, forecast)
        logger.debug("Carbon intensity for %s: %s gCO2/kWh", postcode, forecast)
        return forecast
