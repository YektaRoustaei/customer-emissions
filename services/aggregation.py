from __future__ import annotations

import datetime

from .carbon_client import CarbonIntensityClient
from .data_loader import DataLoader
from models import EmissionRecord


def aggregate_customer_data(
    customer_id: str,
    loader: DataLoader,
    carbon_client: CarbonIntensityClient,
) -> list[EmissionRecord]:
    cycles = loader.get_customer_cycles(customer_id)

    grouped = cycles.groupby(["Date", "AssetId", "CustomerName"], as_index=False).agg(
        TotalKWH=("TotalkW", "sum")
    )

    results: list[EmissionRecord] = []
    for _, row in grouped.iterrows():
        asset_id: str = row["AssetId"]
        postcode = loader.get_postcode(asset_id)
        intensity = carbon_client.get_intensity_forecast(postcode)

        date = row["Date"]
        date_str = date.isoformat() if isinstance(date, datetime.date) else str(date)

        results.append(
            EmissionRecord(
                date=date_str,
                customerId=customer_id,
                customerName=row["CustomerName"],
                assetId=asset_id,
                totalKWH=round(float(row["TotalKWH"]), 4),
                totalCO2=round(float(row["TotalKWH"]) * intensity, 4),
            )
        )

    return results
