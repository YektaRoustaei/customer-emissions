from __future__ import annotations

import os

import redis

CACHE_TTL = int(os.environ.get("CACHE_TTL", 3600))


def create_redis_client() -> redis.Redis:
    return redis.from_url(os.environ["REDIS_URL"])


def carbon_intensity_key(postcode: str) -> str:
    return f"carbon:intensity:{postcode}"
