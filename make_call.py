"""
make_call.py — Manually trigger a Vapi outbound call.

Usage:
    python make_call.py
    python make_call.py --phone "+15559876543"          # override phone number
    python make_call.py --name "John" --account "A123"  # pass custom variables
"""

import argparse
import json
import os

import requests
from dotenv import load_dotenv

load_dotenv()

VAPI_API_URL = "https://api.vapi.ai/call"

PRIVATE_KEY = os.getenv("VAPI_PRIVATE_KEY")
ASSISTANT_ID = os.getenv("VAPI_ASSISTANT_ID")
PHONE_NUMBER_ID = os.getenv("VAPI_PHONE_NUMBER_ID")
DEFAULT_CUSTOMER_PHONE = os.getenv("CUSTOMER_PHONE_NUMBER")


def make_outbound_call(
    customer_phone: str,
    assistant_overrides: dict = None,
) -> dict:
    """Initiate an outbound call via Vapi."""

    headers = {
        "Authorization": f"Bearer {PRIVATE_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "assistantId": ASSISTANT_ID,
        "phoneNumberId": PHONE_NUMBER_ID,
        "customer": {
            "number": customer_phone,
        },
    }

    # Inject dynamic variables into the assistant at call time
    if assistant_overrides:
        payload["assistantOverrides"] = {
            "variableValues": assistant_overrides
        }

    response = requests.post(VAPI_API_URL, headers=headers, json=payload)

    if response.status_code in (200, 201):
        data = response.json()
        print(f"[SUCCESS] Call initiated!")
        print(f"  Call ID  : {data.get('id')}")
        print(f"  Status   : {data.get('status')}")
        print(f"  To       : {customer_phone}")
        return data
    else:
        print(f"[ERROR] {response.status_code}: {response.text}")
        response.raise_for_status()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Trigger a Vapi outbound call.")
    parser.add_argument("--phone", default=DEFAULT_CUSTOMER_PHONE, help="Customer phone number (E.164 format)")
    parser.add_argument("--name", default=None, help="Customer name to pass as variable")
    parser.add_argument("--account", default=None, help="Account ID to pass as variable")
    args = parser.parse_args()

    overrides = {}
    if args.name:
        overrides["customerName"] = args.name
    if args.account:
        overrides["accountId"] = args.account

    make_outbound_call(
        customer_phone=args.phone,
        assistant_overrides=overrides if overrides else None,
    )
