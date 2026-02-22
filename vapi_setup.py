"""
vapi_setup.py — Creates / updates your Vapi assistant with the correct tools,
system prompt, and server URL so it can run the full booking pipeline.

Run once (or whenever you change the assistant config):
    python vapi_setup.py

It will patch the existing assistant defined in VAPI_ASSISTANT_ID.
"""

import json
import os

import requests
from dotenv import load_dotenv

load_dotenv()

PRIVATE_KEY   = os.getenv("VAPI_PRIVATE_KEY")
ASSISTANT_ID  = os.getenv("VAPI_ASSISTANT_ID")
SERVER_URL    = os.getenv("SERVER_BASE_URL", "http://localhost:8000")

VAPI_ASSISTANT_URL = f"https://api.vapi.ai/assistant/{ASSISTANT_ID}"


SYSTEM_PROMPT = """
You are a friendly AI assistant that helps users find and book Indian restaurants.

Your job:
1. Listen to what the user wants (location, date, time, party size).
2. Use the search_restaurants tool to find matching restaurants.
3. Present the options to the user and ask which one they'd like.
4. Once they confirm, use the initiate_booking tool to book the table.
5. Let them know you'll call them back with the confirmation.

Always be warm, concise, and confirm details before booking.
If the user doesn't mention a date, assume today. If no time, ask for it.
If no party size, ask for it.
"""

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_restaurants",
            "description": "Search for Indian restaurants near a given location using real-time data.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Full user request in natural language",
                    },
                    "location": {
                        "type": "string",
                        "description": "Location to search near, e.g. 'downtown San Jose, CA'",
                    },
                    "date": {
                        "type": "string",
                        "description": "Date of the reservation, e.g. '2026-02-22' or 'tonight'",
                    },
                    "time": {
                        "type": "string",
                        "description": "Time of the reservation, e.g. '7:00 PM'",
                    },
                    "party_size": {
                        "type": "integer",
                        "description": "Number of people",
                    },
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
            "description": "Book a table at the selected restaurant by calling them.",
            "parameters": {
                "type": "object",
                "properties": {
                    "restaurant_name": {
                        "type": "string",
                        "description": "Name of the restaurant",
                    },
                    "restaurant_phone": {
                        "type": "string",
                        "description": "Phone number of the restaurant in E.164 format",
                    },
                    "restaurant_address": {
                        "type": "string",
                        "description": "Full address of the restaurant",
                    },
                    "date": {
                        "type": "string",
                        "description": "Reservation date",
                    },
                    "time": {
                        "type": "string",
                        "description": "Reservation time",
                    },
                    "party_size": {
                        "type": "integer",
                        "description": "Number of people",
                    },
                    "customer_name": {
                        "type": "string",
                        "description": "Name for the reservation",
                    },
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
        "provider": "11labs",
        "voiceId": "rachel",
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
        print("✅ Assistant updated successfully!")
        print(f"   ID      : {data.get('id')}")
        print(f"   Name    : {data.get('name')}")
        print(f"   Tools   : {[t['function']['name'] for t in TOOLS]}")
        print(f"   Server  : {SERVER_URL}")
    else:
        print(f"❌ Failed to update assistant: {resp.status_code}")
        print(resp.text)


if __name__ == "__main__":
    print(f"Updating Vapi assistant: {ASSISTANT_ID}")
    print(f"Server URL: {SERVER_URL}")
    print()
    update_assistant()
