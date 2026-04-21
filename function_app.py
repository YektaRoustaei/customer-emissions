import logging
import os
from pathlib import Path

import azure.functions as func
from dotenv import load_dotenv

from responses import ErrorMessage, error_response, success_response
from services.aggregation import aggregate_customer_data
from config.cache import create_redis_client
from services.carbon_client import CarbonIntensityClient
from services.data_loader import DataLoader

load_dotenv()

app = func.FunctionApp()

_DATA_DIR = Path(__file__).parent / "data"
_loader = DataLoader(_DATA_DIR)
_carbon_client = CarbonIntensityClient(
    base_url=os.environ["CARBON_API_BASE_URL"],
    redis_client=create_redis_client(),
)


@app.route(
    route="customer-emissions/{customer_id}", auth_level=func.AuthLevel.ANONYMOUS
)
def customer_emissions(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("customer_emissions triggered")

    customer_id = req.route_params.get("customer_id")

    if not customer_id:
        return error_response(ErrorMessage.CUSTOMER_ID_REQUIRED, 400)

    try:
        results = aggregate_customer_data(customer_id, _loader, _carbon_client)
        return success_response([r.to_dict() for r in results])
    except ValueError as exc:
        return error_response(str(exc), 404)
    except Exception:
        logging.exception("Unhandled error for customerId=%s", customer_id)
        return error_response(ErrorMessage.INTERNAL_SERVER_ERROR, 500)
