import datetime
from pathlib import Path

import pytest

from services.data_loader import DataLoader

DATA_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture(scope="module")
def loader() -> DataLoader:
    return DataLoader(DATA_DIR)


class TestAssets:
    def test_loads_asset_postcode(self, loader: DataLoader) -> None:
        assert not loader.assets.empty
        assert set(loader.assets.columns) >= {"AssetId", "PostalCode"}

    def test_get_postcode_known_asset(self, loader: DataLoader) -> None:
        postcode = loader.get_postcode("Asset1")
        assert postcode == "G4"

    def test_get_postcode_unknown_asset_raises(self, loader: DataLoader) -> None:
        with pytest.raises(ValueError, match="No postcode found for asset"):
            loader.get_postcode("NonExistentAsset")


class TestCycles:
    def test_loads_cycle_information(self, loader: DataLoader) -> None:
        assert not loader.cycles.empty
        required = {
            "CustomerId",
            "AssetId",
            "Date",
            "NrOfCycles",
            "TotalkW",
            "CustomerName",
        }
        assert required.issubset(loader.cycles.columns)

    def test_date_column_is_date_type(self, loader: DataLoader) -> None:
        sample = loader.cycles["Date"].iloc[0]
        assert isinstance(sample, datetime.date)

    def test_get_customer_cycles_returns_filtered_rows(
        self, loader: DataLoader
    ) -> None:
        df = loader.get_customer_cycles("CI-01")
        assert (df["CustomerId"] == "CI-01").all()

    def test_get_customer_cycles_unknown_customer_raises(
        self, loader: DataLoader
    ) -> None:
        with pytest.raises(ValueError, match="No data found for customer"):
            loader.get_customer_cycles("UNKNOWN-999")
