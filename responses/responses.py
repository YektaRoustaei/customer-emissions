import json
from typing import Any

import azure.functions as func


def success_response(data: Any) -> func.HttpResponse:
    return func.HttpResponse(
        json.dumps(data, default=str),
        status_code=200,
        mimetype="application/json",
    )


def error_response(message: str, status_code: int) -> func.HttpResponse:
    return func.HttpResponse(
        json.dumps({"error": message}),
        status_code=status_code,
        mimetype="application/json",
    )
