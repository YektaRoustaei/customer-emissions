from enum import Enum


class ErrorMessage(str, Enum):
    CUSTOMER_ID_REQUIRED = "customerId is required"
    INTERNAL_SERVER_ERROR = "Internal server error"
