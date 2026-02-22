import os
import requests
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

import state_store
from scraper import search_restaurants, format_for_vapi
from calendar_service import add_booking_to_calendar

load_dotenv()

VAPI_API_URL    = "https://api.vapi.ai/call"
PRIVATE_KEY     = os.getenv("VAPI_PRIVATE_KEY")
ASSISTANT_ID    = os.getenv("VAPI_ASSISTANT_ID")
PHONE_NUMBER_ID = os.getenv("VAPI_PHONE_NUMBER_ID")
MY_PHONE        = os.getenv("MY_PHONE_NUMBER")
MY_NAME         = os.getenv("MY_NAME", "User")
SERVER_URL      = os.getenv("SERVER_BASE_URL", "http://localhost:8000")

app = FastAPI(title="Restaurant Booking Orchestrator")


def _make_vapi_call(customer_phone: str, system_prompt: str, first_message: str, variables: dict = None) -> dict:
    headers = {
        "Authorization": f"Bearer {PRIVATE_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "phoneNumberId": PHONE_NUMBER_ID,
        "customer": {"number": customer_phone},
        "assistantId": ASSISTANT_ID,
        "assistantOverrides": {
            "model": {
                "provider": "openai",
                "model": "gpt-4o",
                "systemPrompt": system_prompt,
            },
            "voice": {
                "provider": "minimax",
                "voiceId": "Friendly_Person",
            },
            "firstMessage": first_message,
            "serverUrl": f"{SERVER_URL}/vapi/events",
        },
    }
    if variables:
        payload["assistantOverrides"]["variableValues"] = variables

    resp = requests.post(VAPI_API_URL, headers=headers, json=payload)
    resp.raise_for_status()
    return resp.json()


def handle_search_restaurants(args: dict) -> dict:
    query      = args.get("query", "")
    location   = args.get("location", "")
    date       = args.get("date", "today")
    time       = args.get("time", "")
    party_size = args.get("party_size", 2)

    print(f"[TOOL] search_restaurants | location={location} | date={date} | time={time} | party={party_size}")

    restaurants = search_restaurants(query=query, location=location)

    if not restaurants:
        return {"message": "Sorry, I couldn't find any Indian restaurants in that area. Can you try a different location?"}

    return {
        "message": format_for_vapi(restaurants),
        "restaurants": restaurants,
    }


def handle_initiate_booking(args: dict, call_metadata: dict) -> dict:
    restaurant_name  = args.get("restaurant_name", "")
    restaurant_phone = args.get("restaurant_phone", "")
    address          = args.get("restaurant_address", "")
    date             = args.get("date", "")
    time_str         = args.get("time", "")
    party_size       = args.get("party_size", 2)
    customer_name    = args.get("customer_name", MY_NAME)

    print(f"[TOOL] initiate_booking | {restaurant_name} | {restaurant_phone} | {date} {time_str} for {party_size}")

    booking_id = state_store.create_booking(
        customer_name=customer_name,
        customer_phone=MY_PHONE,
        restaurant_name=restaurant_name,
        restaurant_phone=restaurant_phone,
        location=address,
        date=date,
        time=time_str,
        party_size=party_size,
    )

    restaurant_system_prompt = f"""
You are an AI assistant calling {restaurant_name} to make a table reservation.

Reservation details:
- Name: {customer_name}
- Date: {date}
- Time: {time_str}
- Party size: {party_size} people

Be polite and concise. Confirm the booking and repeat back the confirmed date, time, and name.
When the booking is confirmed, say: "Booking confirmed for {customer_name}, {party_size} people on {date} at {time_str}. Thank you!"
Then end the call politely.
"""
    restaurant_first_message = (
        f"Hello! I'm calling to make a reservation for {party_size} people on {date} at {time_str} "
        f"under the name {customer_name}. Is that available?"
    )

    try:
        call = _make_vapi_call(
            customer_phone=restaurant_phone,
            system_prompt=restaurant_system_prompt,
            first_message=restaurant_first_message,
            variables={"booking_id": booking_id},
        )
        state_store.update_booking(booking_id, restaurant_call_id=call.get("id"), status="calling_restaurant")
        print(f"[ORCHESTRATOR] Restaurant call initiated: {call.get('id')}")
    except Exception as e:
        print(f"[ORCHESTRATOR] Failed to call restaurant: {e}")
        state_store.update_booking(booking_id, status="error")
        return {"message": f"I had trouble connecting to {restaurant_name}. Please try again."}

    return {
        "message": (
            f"I'm now calling {restaurant_name} to book your table for {party_size} on {date} at {time_str}. "
            f"I'll call you back on {MY_PHONE} once the booking is confirmed!"
        ),
        "booking_id": booking_id,
    }


@app.post("/vapi/tools")
async def vapi_tools(request: Request):
    body = await request.json()
    print(f"[VAPI TOOL CALL] {body}")

    message    = body.get("message", {})
    tool_calls = message.get("toolCalls", [])
    call_meta  = message.get("call", {})
    results    = []

    for tool_call in tool_calls:
        fn      = tool_call.get("function", {})
        name    = fn.get("name", "")
        args    = fn.get("arguments", {})
        call_id = tool_call.get("id", "")

        if name == "search_restaurants":
            result = handle_search_restaurants(args)
        elif name == "initiate_booking":
            result = handle_initiate_booking(args, call_meta)
        else:
            result = {"message": f"Unknown tool: {name}"}

        results.append({"toolCallId": call_id, "result": result.get("message", "Done.")})

    return JSONResponse({"results": results})


@app.post("/vapi/events")
async def vapi_events(request: Request):
    body       = await request.json()
    message    = body.get("message", {})
    event_type = message.get("type", "unknown")
    call       = message.get("call", {})
    call_id    = call.get("id", "")

    print(f"[VAPI EVENT] {event_type} | call_id={call_id}")

    if event_type == "end-of-call-report":
        booking = state_store.get_booking_by_call_id(call_id)

        if booking and booking["status"] == "calling_restaurant":
            transcript   = message.get("transcript", "")
            summary      = message.get("summary", "")
            ended_reason = call.get("endedReason", "")

            print(f"[ORCHESTRATOR] Restaurant call ended | reason={ended_reason}")

            confirmed = (
                ended_reason in ("assistant-ended-call", "customer-ended-call", "silence-timed-out")
                or "confirmed" in transcript.lower()
                or "reservation" in transcript.lower()
            )

            if confirmed:
                state_store.update_booking(
                    booking["id"],
                    status="confirmed",
                    confirmation_details=summary or transcript[:300],
                )
                cal_result = add_booking_to_calendar(
                    restaurant_name=booking["restaurant_name"],
                    address=booking["location"],
                    date=booking["date"],
                    time=booking["time"],
                    party_size=booking["party_size"],
                    customer_name=booking["customer_name"],
                )
                state_store.update_booking(booking["id"], calendar_event_id=cal_result.get("event_id"))
                _notify_user(booking)
            else:
                state_store.update_booking(booking["id"], status="failed")
                print(f"[ORCHESTRATOR] Booking may have failed — check transcript.")

        elif booking and booking["status"] == "notifying_user":
            state_store.update_booking(booking["id"], status="notified")
            print(f"[ORCHESTRATOR] Pipeline complete for booking {booking['id']}")

    return JSONResponse({"status": "received"})


def _notify_user(booking: dict):
    system_prompt = f"""
You are an AI assistant calling {booking['customer_name']} to confirm their restaurant reservation.

Booking details:
- Restaurant: {booking['restaurant_name']}
- Address: {booking['location']}
- Date: {booking['date']}
- Time: {booking['time']}
- Party size: {booking['party_size']} people
- Reservation name: {booking['customer_name']}

Tell them the booking is confirmed, share the details, and let them know it has been added 
to their Google Calendar. Be warm and brief, then say goodbye.
"""
    first_message = (
        f"Hi {booking['customer_name']}! I'm calling to confirm your table reservation "
        f"at {booking['restaurant_name']} for {booking['party_size']} people on "
        f"{booking['date']} at {booking['time']}. It's all set and I've added it to your calendar!"
    )

    try:
        call = _make_vapi_call(
            customer_phone=booking["customer_phone"],
            system_prompt=system_prompt,
            first_message=first_message,
        )
        state_store.update_booking(
            booking["id"],
            confirmation_call_id=call.get("id"),
            status="notifying_user",
        )
        print(f"[ORCHESTRATOR] User confirmation call initiated: {call.get('id')}")
    except Exception as e:
        print(f"[ORCHESTRATOR] Failed to call user: {e}")


@app.get("/bookings")
async def get_bookings():
    return JSONResponse(state_store.all_bookings())


@app.get("/health")
async def health():
    return {"status": "ok", "server": SERVER_URL}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("orchestrator:app", host="0.0.0.0", port=8000, reload=True)
