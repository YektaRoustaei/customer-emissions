from unittest.mock import MagicMock

import pytest
import requests

from services.carbon_client import CarbonIntensityClient


def _mock_response(forecast: float) -> MagicMock:
    resp = MagicMock()
    resp.json.return_value = {
        "data": [{"data": [{"intensity": {"forecast": forecast, "index": "moderate"}}]}]
    }
    resp.raise_for_status.return_value = None
    return resp


def _make_client(
    forecast: float, cached: bool = False
) -> tuple[CarbonIntensityClient, MagicMock, MagicMock]:
    session = MagicMock()
    session.get.return_value = _mock_response(forecast)

    redis_client = MagicMock()
    redis_client.get.return_value = str(forecast).encode() if cached else None

    client = CarbonIntensityClient(
        base_url="https://api.example.com",
        redis_client=redis_client,
        session=session,
    )
    return client, session, redis_client


class TestCarbonIntensityClient:
    def test_returns_forecast_value(self) -> None:
        client, _, _ = _make_client(115.0)
        assert client.get_intensity_forecast("G4") == 115.0

    def test_stores_result_in_redis(self) -> None:
        client, _, redis_client = _make_client(115.0)
        client.get_intensity_forecast("G4")
        redis_client.setex.assert_called_once()

    def test_cache_hit_skips_http_request(self) -> None:
        client, session, _ = _make_client(115.0, cached=True)
        client.get_intensity_forecast("G4")
        session.get.assert_not_called()

    def test_cache_hit_returns_cached_value(self) -> None:
        client, _, _ = _make_client(115.0, cached=True)
        assert client.get_intensity_forecast("G4") == 115.0

    def test_separate_postcodes_each_make_request(self) -> None:
        client, session, _ = _make_client(100.0)
        client.get_intensity_forecast("G4")
        client.get_intensity_forecast("TS1")
        assert session.get.call_count == 2

    def test_http_error_propagates(self) -> None:
        client, session, _ = _make_client(100.0)
        session.get.return_value.raise_for_status.side_effect = requests.HTTPError(
            "404"
        )
        with pytest.raises(requests.HTTPError):
            client.get_intensity_forecast("INVALID")
