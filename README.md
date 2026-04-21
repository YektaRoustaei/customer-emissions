# customer-emissions

An Azure Functions HTTP API that calculates CO2 emissions for a given customer by combining their energy cycle data with real-time carbon intensity forecasts from the [Carbon Intensity API](https://api.carbonintensity.org.uk).

## Endpoint

```
GET /api/customer-emissions/{customer_id}
```

Returns a JSON array of emission records — one per unique date/asset combination — with total kWh consumed and total CO2 produced (kWh × gCO2/kWh forecast for that asset's postcode).

---

## Project structure

```
.
├── function_app.py          # Azure Function entrypoint
├── host.json                # Azure Functions host configuration
├── local.settings.json      # Local environment variables (not committed)
├── requirements.txt         # Python dependencies
├── .env                     # Default env values for local development
│
├── config/
│   └── cache.py             # Redis client factory and cache key helpers
│
├── data/
│   ├── Asset Postcode.xlsx  # Maps asset IDs to UK postcodes
│   └── Cycle information.xlsx  # Energy cycle records per customer/asset/date
│
├── models/
│   └── emission_record.py   # EmissionRecord dataclass (date, customer, asset, kWh, CO2)
│
├── responses/
│   ├── messages.py          # ErrorMessage enum (standard error strings)
│   └── responses.py         # success_response / error_response HTTP helpers
│
├── services/
│   ├── aggregation.py       # Core logic: groups cycles by date+asset, fetches intensity, builds records
│   ├── carbon_client.py     # HTTP client for the Carbon Intensity API with Redis caching
│   └── data_loader.py       # Lazy-loading Excel reader; filters cycles by customer, looks up postcodes
│
└── tests/
    ├── fixtures/            # Copies of the Excel files used by tests
    ├── test_aggregation.py  # Unit tests for the aggregation logic
    ├── test_carbon_client.py# Unit tests for CarbonIntensityClient (cache hit/miss, HTTP)
    ├── test_data_loader.py  # Unit tests for DataLoader (filtering, postcode lookup, error cases)
    ├── test_function_app.py # Integration tests for the HTTP endpoint
    └── test_responses.py    # Unit tests for the HTTP response helpers
```

---

## How it works

1. `function_app.py` receives a `GET` request with a `customer_id` path parameter.
2. `DataLoader` (`services/data_loader.py`) reads the two Excel files (lazily, cached in memory) and returns the cycle rows that belong to the requested customer.
3. `aggregate_customer_data` (`services/aggregation.py`) groups those rows by date + asset, sums the kWh, then fetches the carbon intensity forecast for each asset's postcode.
4. `CarbonIntensityClient` (`services/carbon_client.py`) calls the Carbon Intensity API and caches the result in Redis for `CACHE_TTL` seconds to avoid redundant external calls.
5. Each group becomes an `EmissionRecord` (`models/emission_record.py`) with `totalCO2 = totalKWH × intensity`.
6. The response helpers (`responses/`) serialise the records to JSON and return the appropriate HTTP status code.

---

## Local setup

**Requirements:** Python 3.11, Azure Functions Core Tools v4, Redis running on `localhost:6379`.

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
func start
```

Environment variables are loaded from `.env` (via `python-dotenv`) and from `local.settings.json` (by the Functions runtime):

| Variable             | Description                                      | Default                                              |
|----------------------|--------------------------------------------------|------------------------------------------------------|
| `CARBON_API_BASE_URL`| Base URL for the Carbon Intensity API            | `https://api.carbonintensity.org.uk/regional/postcode` |
| `REDIS_URL`          | Redis connection URL                             | `redis://localhost:6379`                             |
| `CACHE_TTL`          | Seconds to cache carbon intensity results        | `3600`                                               |

---

## Running tests

```bash
python -m pytest
```

With coverage:

```bash
python -m pytest tests/ --cov=services --cov-report=term-missing
```

---

## CI

| Workflow | Trigger | What it does |
|---|---|---|
| `.github/workflows/tests.yml` | Push / PR to `main` | Lints with `ruff`, runs the full test suite, posts a coverage summary comment on PRs |
| `.github/workflows/format.yml` | PR to `main` | Auto-fixes formatting with `ruff` and commits the result |
