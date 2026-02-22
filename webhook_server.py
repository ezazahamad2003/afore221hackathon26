import os
import requests
import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

load_dotenv()

VAPI_API_URL           = "https://api.vapi.ai/call"
PRIVATE_KEY            = os.getenv("VAPI_PRIVATE_KEY")
ASSISTANT_ID           = os.getenv("VAPI_ASSISTANT_ID")
PHONE_NUMBER_ID        = os.getenv("VAPI_PHONE_NUMBER_ID")
DEFAULT_CUSTOMER_PHONE = os.getenv("MY_PHONE_NUMBER")

app = FastAPI(title="Vapi Outbound Call Server")


class CallRequest(BaseModel):
    phone:           str  = DEFAULT_CUSTOMER_PHONE
    name:            str  = None
    account:         str  = None
    extra_variables: dict = {}


def _initiate_call(phone: str, variables: dict = None) -> dict:
    headers = {
        "Authorization": f"Bearer {PRIVATE_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "assistantId":   ASSISTANT_ID,
        "phoneNumberId": PHONE_NUMBER_ID,
        "customer":      {"number": phone},
    }
    if variables:
        payload["assistantOverrides"] = {"variableValues": variables}

    resp = requests.post(VAPI_API_URL, headers=headers, json=payload)
    if resp.status_code not in (200, 201):
        raise HTTPException(status_code=resp.status_code, detail=resp.text)
    return resp.json()


@app.post("/trigger-call")
async def trigger_call(req: CallRequest):
    variables = {**req.extra_variables}
    if req.name:
        variables["customerName"] = req.name
    if req.account:
        variables["accountId"] = req.account

    result = _initiate_call(phone=req.phone, variables=variables or None)
    return JSONResponse({
        "status":      "call_initiated",
        "call_id":     result.get("id"),
        "vapi_status": result.get("status"),
        "to":          req.phone,
    })


@app.post("/vapi-events")
async def vapi_events(request: Request):
    event      = await request.json()
    event_type = event.get("message", {}).get("type", "unknown")

    print(f"[VAPI EVENT] {event_type}")

    if event_type == "call-started":
        print(f"  Call started: {event['message'].get('call', {}).get('id')}")

    elif event_type == "call-ended":
        call        = event["message"].get("call", {})
        ended_reason = call.get("endedReason")
        print(f"  Call ended: {call.get('id')} | Reason: {ended_reason}")

    elif event_type == "transcript":
        role       = event["message"].get("role", "unknown")
        transcript = event["message"].get("transcript", "")
        print(f"  [{role}]: {transcript}")

    elif event_type == "function-call":
        fn_name   = event["message"].get("functionCall", {}).get("name")
        fn_params = event["message"].get("functionCall", {}).get("parameters", {})
        print(f"  Function call: {fn_name}({fn_params})")
        return JSONResponse({"result": f"Function {fn_name} executed successfully."})

    return JSONResponse({"status": "received"})


@app.get("/health")
async def health():
    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run("webhook_server:app", host="0.0.0.0", port=8000, reload=True)
