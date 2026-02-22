"""
webhook_server.py — Event-based outbound call trigger via FastAPI.

Endpoints:
    POST /trigger-call          — Trigger a call with a JSON body
    POST /vapi-events           — Receive status events from Vapi (call-started, call-ended, etc.)

Start server:
    uvicorn webhook_server:app --reload --port 8000

Example trigger:
    curl -X POST http://localhost:8000/trigger-call \
         -H "Content-Type: application/json" \
         -d '{"phone": "+16503377133", "name": "Alice", "account": "ACC001"}'
"""

import os

import requests
import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

load_dotenv()

VAPI_API_URL = "https://api.vapi.ai/call"

PRIVATE_KEY = os.getenv("VAPI_PRIVATE_KEY")
ASSISTANT_ID = os.getenv("VAPI_ASSISTANT_ID")
PHONE_NUMBER_ID = os.getenv("VAPI_PHONE_NUMBER_ID")
DEFAULT_CUSTOMER_PHONE = os.getenv("CUSTOMER_PHONE_NUMBER")

app = FastAPI(title="Vapi Outbound Call Server")


# ── Request schema ────────────────────────────────────────────────────────────

class CallRequest(BaseModel):
    phone: str = DEFAULT_CUSTOMER_PHONE
    name: str = None
    account: str = None
    extra_variables: dict = {}


# ── Helper ────────────────────────────────────────────────────────────────────

def _initiate_call(phone: str, variables: dict = None) -> dict:
    headers = {
        "Authorization": f"Bearer {PRIVATE_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "assistantId": ASSISTANT_ID,
        "phoneNumberId": PHONE_NUMBER_ID,
        "customer": {"number": phone},
    }

    if variables:
        payload["assistantOverrides"] = {"variableValues": variables}

    resp = requests.post(VAPI_API_URL, headers=headers, json=payload)

    if resp.status_code not in (200, 201):
        raise HTTPException(status_code=resp.status_code, detail=resp.text)

    return resp.json()


# ── Routes ────────────────────────────────────────────────────────────────────

@app.post("/trigger-call")
async def trigger_call(req: CallRequest):
    """
    Manually or programmatically trigger an outbound call.
    Send a POST request with phone, name, account, or any extra_variables.
    """
    variables = {**req.extra_variables}
    if req.name:
        variables["customerName"] = req.name
    if req.account:
        variables["accountId"] = req.account

    result = _initiate_call(phone=req.phone, variables=variables or None)

    return JSONResponse({
        "status": "call_initiated",
        "call_id": result.get("id"),
        "vapi_status": result.get("status"),
        "to": req.phone,
    })


@app.post("/vapi-events")
async def vapi_events(request: Request):
    """
    Vapi posts call lifecycle events here.
    Configure this URL in your Vapi dashboard under Server URL.
    """
    event = await request.json()
    event_type = event.get("message", {}).get("type", "unknown")

    print(f"[VAPI EVENT] {event_type}: {event}")

    # ── Handle specific events ────────────────────────────────────────────────
    if event_type == "call-started":
        call_id = event["message"].get("call", {}).get("id")
        print(f"  Call started: {call_id}")

    elif event_type == "call-ended":
        call_id = event["message"].get("call", {}).get("id")
        ended_reason = event["message"].get("call", {}).get("endedReason")
        print(f"  Call ended: {call_id} | Reason: {ended_reason}")

    elif event_type == "transcript":
        transcript = event["message"].get("transcript", "")
        role = event["message"].get("role", "unknown")
        print(f"  [{role}]: {transcript}")

    elif event_type == "function-call":
        # Handle tool/function calls from the assistant
        fn_name = event["message"].get("functionCall", {}).get("name")
        fn_params = event["message"].get("functionCall", {}).get("parameters", {})
        print(f"  Function call: {fn_name}({fn_params})")
        # Return a result back to the assistant
        return JSONResponse({"result": f"Function {fn_name} executed successfully."})

    return JSONResponse({"status": "received"})


@app.get("/health")
async def health():
    return {"status": "ok"}


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    uvicorn.run("webhook_server:app", host="0.0.0.0", port=8000, reload=True)
