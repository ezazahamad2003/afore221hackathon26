import os
import requests
from dotenv import load_dotenv

load_dotenv()

PRIVATE_KEY        = os.getenv("VAPI_PRIVATE_KEY")
ASSISTANT_ID       = os.getenv("VAPI_ASSISTANT_ID")
SERVER_URL         = os.getenv("SERVER_BASE_URL", "http://localhost:8000")
VAPI_ASSISTANT_URL = f"https://api.vapi.ai/assistant/{ASSISTANT_ID}"

SYSTEM_PROMPT = """
You are a friendly AI assistant that helps users find and book Indian restaurants.

Your job:
1. Listen to what the user wants — location, date, time, and party size.
2. Use the search_restaurants tool to find matching restaurants near them.
3. Present the options and ask which one they'd like to book.
4. Once they confirm, use the initiate_booking tool to place the reservation.
5. Let them know you'll call them back once the booking is confirmed.

Always confirm details before booking. If date is missing, assume today.
If time or party size is missing, ask for it before proceeding.
"""

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_restaurants",
            "description": "Search for Indian restaurants near a given location using real-time web data.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query":      {"type": "string",  "description": "Full user request in natural language"},
                    "location":   {"type": "string",  "description": "Location to search near, e.g. 'downtown San Jose, CA'"},
                    "date":       {"type": "string",  "description": "Date of the reservation, e.g. '2026-02-22' or 'tonight'"},
                    "time":       {"type": "string",  "description": "Time of the reservation, e.g. '7:00 PM'"},
                    "party_size": {"type": "integer", "description": "Number of people"},
                },
                "required": ["query", "location"],
            },
        },
        "server": {"url": f"{SERVER_URL}/vapi/tools"},
    },
    {
        "type": "function",
        "function": {
            "name": "initiate_booking",
            "description": "Book a table at the selected restaurant by placing an outbound call to them.",
            "parameters": {
                "type": "object",
                "properties": {
                    "restaurant_name":    {"type": "string",  "description": "Name of the restaurant"},
                    "restaurant_phone":   {"type": "string",  "description": "Restaurant phone number in E.164 format"},
                    "restaurant_address": {"type": "string",  "description": "Full address of the restaurant"},
                    "date":               {"type": "string",  "description": "Reservation date"},
                    "time":               {"type": "string",  "description": "Reservation time"},
                    "party_size":         {"type": "integer", "description": "Number of people"},
                    "customer_name":      {"type": "string",  "description": "Name for the reservation"},
                },
                "required": ["restaurant_name", "restaurant_phone", "date", "time", "party_size"],
            },
        },
        "server": {"url": f"{SERVER_URL}/vapi/tools"},
    },
]

ASSISTANT_CONFIG = {
    "model": {
        "provider": "openai",
        "model": "gpt-4o",
        "systemPrompt": SYSTEM_PROMPT,
        "tools": TOOLS,
    },
    "voice": {
        "provider": "minimax",
        "voiceId": "Friendly_Person",
    },
    "firstMessage": "Hi! I'm your restaurant booking assistant. Tell me where you'd like to eat, when, and for how many people!",
    "serverUrl": f"{SERVER_URL}/vapi/events",
    "endCallMessage": "I'll take it from here and call you back once your table is confirmed. Goodbye!",
}


def update_assistant():
    headers = {
        "Authorization": f"Bearer {PRIVATE_KEY}",
        "Content-Type": "application/json",
    }
    resp = requests.patch(VAPI_ASSISTANT_URL, headers=headers, json=ASSISTANT_CONFIG)

    if resp.status_code in (200, 201):
        data = resp.json()
        print("Assistant updated successfully!")
        print(f"  ID     : {data.get('id')}")
        print(f"  Name   : {data.get('name')}")
        print(f"  Tools  : {[t['function']['name'] for t in TOOLS]}")
        print(f"  Server : {SERVER_URL}")
    else:
        print(f"Failed to update assistant: {resp.status_code}")
        print(resp.text)


if __name__ == "__main__":
    print(f"Updating Vapi assistant: {ASSISTANT_ID}")
    print(f"Server URL: {SERVER_URL}\n")
    update_assistant()
