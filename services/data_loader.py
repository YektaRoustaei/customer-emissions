from pathlib import Path

import pandas as pd


class DataLoader:
    def __init__(self, data_dir: Path) -> None:
        self._data_dir = data_dir
        self._assets: pd.DataFrame | None = None
        self._cycles: pd.DataFrame | None = None

    @property
    def assets(self) -> pd.DataFrame:
        if self._assets is None:
            self._assets = pd.read_excel(self._data_dir / "Asset Postcode.xlsx")
        return self._assets

    @property
    def cycles(self) -> pd.DataFrame:
        if self._cycles is None:
            df = pd.read_excel(self._data_dir / "Cycle information.xlsx")
            df["Date"] = pd.to_datetime(df["Date"]).dt.date
            self._cycles = df
        return self._cycles

    def get_customer_cycles(self, customer_id: str) -> pd.DataFrame:
        df = self.cycles[self.cycles["CustomerId"] == customer_id].copy()
        if df.empty:
            raise ValueError(f"No data found for customer '{customer_id}'")
        return df

    def get_postcode(self, asset_id: str) -> str:
        row = self.assets[self.assets["AssetId"] == asset_id]
        if row.empty:
            raise ValueError(f"No postcode found for asset '{asset_id}'")
        return str(row.iloc[0]["PostalCode"])
