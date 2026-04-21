import datetime
from unittest.mock import MagicMock
import pandas as pd
from services.aggregation import aggregate_customer_data
from models import EmissionRecord


def _make_loader(cycles: pd.DataFrame, postcode: str = "G4") -> MagicMock:
    loader = MagicMock()
    loader.get_customer_cycles.return_value = cycles
    loader.get_postcode.return_value = postcode
    return loader


def _make_carbon_client(forecast: float = 100.0) -> MagicMock:
    client = MagicMock()
    client.get_intensity_forecast.return_value = forecast
    return client


def _make_cycles(**overrides) -> pd.DataFrame:
    defaults = {
        "CustomerId": ["CI-01"],
        "AssetId": ["Asset1"],
        "Date": [datetime.date(2026, 3, 22)],
        "NrOfCycles": [1],
        "TotalkW": [10.0],
        "CustomerName": ["Customer 01"],
        "ProgramName": ["Low Temperature Cycle"],
    }
    defaults.update(overrides)
    return pd.DataFrame(defaults)


class TestAggregateCustomerData:
    def test_single_row_produces_expected_output(self) -> None:
        loader = _make_loader(_make_cycles())
        client = _make_carbon_client(forecast=100.0)

        results = aggregate_customer_data("CI-01", loader, client)

        assert len(results) == 1
        record = results[0]
        assert isinstance(record, EmissionRecord)
        assert record.customerId == "CI-01"
        assert record.customerName == "Customer 01"
        assert record.assetId == "Asset1"
        assert record.date == "2026-03-22"
        assert record.totalKWH == 10.0
        assert record.totalCO2 == 1000.0

    def test_multiple_cycles_same_day_same_asset_are_summed(self) -> None:
        cycles = _make_cycles(
            CustomerId=["CI-01", "CI-01"],
            AssetId=["Asset1", "Asset1"],
            Date=[datetime.date(2026, 3, 22), datetime.date(2026, 3, 22)],
            NrOfCycles=[1, 1],
            TotalkW=[4.0, 8.0],
            CustomerName=["Customer 01", "Customer 01"],
            ProgramName=["Low Temp", "High Temp"],
        )
        loader = _make_loader(cycles)
        client = _make_carbon_client(forecast=50.0)

        results = aggregate_customer_data("CI-01", loader, client)

        assert len(results) == 1
        assert results[0].totalKWH == 12.0
        assert results[0].totalCO2 == 600.0

    def test_different_dates_produce_separate_rows(self) -> None:
        cycles = _make_cycles(
            CustomerId=["CI-01", "CI-01"],
            AssetId=["Asset1", "Asset1"],
            Date=[datetime.date(2026, 3, 22), datetime.date(2026, 3, 23)],
            NrOfCycles=[1, 1],
            TotalkW=[5.0, 7.0],
            CustomerName=["Customer 01", "Customer 01"],
            ProgramName=["Low Temp", "Low Temp"],
        )
        loader = _make_loader(cycles)
        client = _make_carbon_client(forecast=100.0)

        results = aggregate_customer_data("CI-01", loader, client)

        assert len(results) == 2
        dates = {r.date for r in results}
        assert dates == {"2026-03-22", "2026-03-23"}

    def test_different_assets_produce_separate_rows(self) -> None:
        cycles = _make_cycles(
            CustomerId=["CI-01", "CI-01"],
            AssetId=["Asset1", "Asset2"],
            Date=[datetime.date(2026, 3, 22), datetime.date(2026, 3, 22)],
            NrOfCycles=[1, 1],
            TotalkW=[5.0, 6.0],
            CustomerName=["Customer 01", "Customer 01"],
            ProgramName=["Low Temp", "Low Temp"],
        )
        loader = _make_loader(cycles)
        client = _make_carbon_client(forecast=200.0)

        results = aggregate_customer_data("CI-01", loader, client)

        assert len(results) == 2
        asset_ids = {r.assetId for r in results}
        assert asset_ids == {"Asset1", "Asset2"}

    def test_co2_uses_postcode_specific_intensity(self) -> None:
        cycles = _make_cycles(
            CustomerId=["CI-01", "CI-01"],
            AssetId=["Asset1", "Asset2"],
            Date=[datetime.date(2026, 3, 22), datetime.date(2026, 3, 22)],
            NrOfCycles=[1, 1],
            TotalkW=[10.0, 10.0],
            CustomerName=["Customer 01", "Customer 01"],
            ProgramName=["Low Temp", "Low Temp"],
        )
        loader = MagicMock()
        loader.get_customer_cycles.return_value = cycles
        loader.get_postcode.side_effect = lambda asset_id: (
            "G4" if asset_id == "Asset1" else "TS1"
        )

        client = MagicMock()
        client.get_intensity_forecast.side_effect = lambda pc: (
            100.0 if pc == "G4" else 200.0
        )

        results = aggregate_customer_data("CI-01", loader, client)

        by_asset = {r.assetId: r for r in results}
        assert by_asset["Asset1"].totalCO2 == 1000.0
        assert by_asset["Asset2"].totalCO2 == 2000.0

    def test_to_dict_has_all_required_keys(self) -> None:
        loader = _make_loader(_make_cycles())
        client = _make_carbon_client()

        results = aggregate_customer_data("CI-01", loader, client)

        required_keys = {
            "date",
            "customerId",
            "customerName",
            "assetId",
            "totalKWH",
            "totalCO2",
        }
        assert required_keys == set(results[0].to_dict().keys())
