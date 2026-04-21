import json
from unittest.mock import patch

import azure.functions as func
import pytest

from models import EmissionRecord
from responses import ErrorMessage


SAMPLE_RECORD = EmissionRecord(
    date="2026-03-22",
    customerId="CI-01",
    customerName="Customer 01",
    assetId="Asset1",
    totalKWH=12.255,
    totalCO2=1412.38,
)
SAMPLE_RESULTS = [SAMPLE_RECORD]


def _make_request(customer_id: str | None = None) -> func.HttpRequest:
    route_params = {"customer_id": customer_id} if customer_id else {}
    return func.HttpRequest(
        method="GET",
        url=f"http://localhost/api/customer-emissions/{customer_id or ''}",
        route_params=route_params,
        params={},
        body=b"",
    )


@pytest.fixture(autouse=True)
def patch_dependencies():
    with (
        patch("function_app._loader") as mock_loader,
        patch("function_app._carbon_client") as mock_client,
        patch(
            "function_app.aggregate_customer_data", return_value=SAMPLE_RESULTS
        ) as mock_agg,
    ):
        yield mock_loader, mock_client, mock_agg


class TestCustomerEmissionsFunction:
    def test_returns_400_when_no_customer_id(self, patch_dependencies) -> None:
        from function_app import customer_emissions

        response = customer_emissions(_make_request())

        assert response.status_code == 400
        assert ErrorMessage.CUSTOMER_ID_REQUIRED in response.get_body().decode()

    def test_accepts_customer_id_from_route(self, patch_dependencies) -> None:
        from function_app import customer_emissions, aggregate_customer_data

        response = customer_emissions(_make_request("CI-01"))

        assert response.status_code == 200
        aggregate_customer_data.assert_called_once()
        assert aggregate_customer_data.call_args[0][0] == "CI-01"

    def test_returns_json_content_type(self, patch_dependencies) -> None:
        from function_app import customer_emissions

        response = customer_emissions(_make_request("CI-01"))

        assert response.mimetype == "application/json"

    def test_returns_results_in_body(self, patch_dependencies) -> None:
        from function_app import customer_emissions

        response = customer_emissions(_make_request("CI-01"))

        body = json.loads(response.get_body())
        assert body == [r.to_dict() for r in SAMPLE_RESULTS]

    def test_returns_404_for_unknown_customer(self, patch_dependencies) -> None:
        _, _, mock_agg = patch_dependencies
        mock_agg.side_effect = ValueError("No data found for customer 'UNKNOWN'")

        from function_app import customer_emissions

        response = customer_emissions(_make_request("UNKNOWN"))

        assert response.status_code == 404
        assert "No data found" in response.get_body().decode()

    def test_returns_500_on_unexpected_error(self, patch_dependencies) -> None:
        _, _, mock_agg = patch_dependencies
        mock_agg.side_effect = RuntimeError("boom")

        from function_app import customer_emissions

        response = customer_emissions(_make_request("CI-01"))

        assert response.status_code == 500
        assert ErrorMessage.INTERNAL_SERVER_ERROR in response.get_body().decode()
