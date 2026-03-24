"""Constants used by the fraud feature-engineering pipeline."""

from __future__ import annotations


DEFAULT_STRING_IMPUTATIONS = {
    "user_id": "unknown_user",
    "device_id": "unknown_device",
    "transaction_amount": "0",
    "amt": "0",
    "status": "unknown_status",
    "merchant_category": "unknown_merchant_category",
    "user_location": "unknown_city",
    "merchant_location": "unknown_city",
    "ip_address": "0.0.0.0",
    "payment_method": "unknown_payment_method",
}

DEFAULT_NUMERIC_IMPUTATIONS = {
    "account_balance": 0.0,
}

COLUMN_ALIASES = {
    "timestamp": ["timestamp", "transaction_timestamp"],
    "status": ["status", "transaction_status"],
}

CITY_VARIATION_MAP = {
    "bom": "mumbai",
    "bombay": "mumbai",
    "mum": "mumbai",
    "del": "delhi",
    "new delhi": "delhi",
    "blr": "bangalore",
    "bengaluru": "bangalore",
    "hyd": "hyderabad",
    "hyde": "hyderabad",
    "hyderab": "hyderabad",
    "madras": "chennai",
    "cal": "kolkata",
    "calcutta": "kolkata",
    "ccu": "kolkata",
    "jai": "jaipur",
    "lko": "lucknow",
    "pnq": "pune",
    "pun": "pune",
    "pu": "pune",
    "amd": "ahmedabad",
    "maa": "chennai",
}

FAILED_STATUSES = {"failed", "failure", "declined", "rejected"}
SUCCESS_STATUSES = {"success", "successful", "approved", "completed"}

PATTERN_COLUMNS = [
    "pattern_location_mismatch",
    "pattern_odd_hour_transaction",
    "pattern_high_amount_vs_balance",
    "pattern_unknown_device",
    "pattern_failed_high_value",
    "pattern_ip_risk",
    "pattern_velocity",
    "pattern_post_failure_success",
]
