"""
scraper.py — Uses rtrvr.ai /agent to find Indian restaurants.

Given a natural-language query (e.g. "Indian restaurants near downtown San Jose
open tonight for 2 people at 7pm"), it returns a list of restaurants with:
  - name, address, phone, rating, cuisine, hours
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

RTRVR_API_KEY = os.getenv("RTRVR_API_KEY")
RTRVR_AGENT_URL = "https://api.rtrvr.ai/agent"


def search_restaurants(query: str, location: str, max_results: int = 5) -> list[dict]:
    """
    Search for Indian restaurants using rtrvr.ai agent.

    Args:
        query:       Full natural-language request from user
                     e.g. "Indian restaurants near downtown San Jose for 2 tonight at 7pm"
        location:    Extracted location string e.g. "San Jose, CA"
        max_results: How many restaurants to return

    Returns:
        List of restaurant dicts with keys:
            name, address, phone, rating, hours, google_maps_url
    """

    task = f"""
Search Google Maps for Indian restaurants near {location}.

For each of the top {max_results} results, extract:
- Restaurant name
- Full address
- Phone number (must include area code)
- Google rating (out of 5)
- Opening hours (today)
- Google Maps URL

Context from user: "{query}"

Return results as a JSON array with keys: name, address, phone, rating, hours, google_maps_url.
Only include restaurants that have a phone number listed.
"""

    headers = {
        "Authorization": f"Bearer {RTRVR_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "input": task,
        "urls": [f"https://www.google.com/maps/search/indian+restaurants+near+{location.replace(' ', '+')}"],
        "response": {"verbosity": "final"},
    }

    response = requests.post(RTRVR_AGENT_URL, headers=headers, json=payload, timeout=60)

    if response.status_code not in (200, 201):
        print(f"[SCRAPER ERROR] {response.status_code}: {response.text}")
        response.raise_for_status()

    data = response.json()

    # rtrvr.ai returns the agent result — parse the JSON array out of the response
    result = data.get("result") or data.get("output") or data.get("data") or []

    if isinstance(result, str):
        import json
        import re
        # Extract JSON array from markdown or plain text response
        match = re.search(r"\[.*\]", result, re.DOTALL)
        if match:
            result = json.loads(match.group())
        else:
            result = []

    print(f"[SCRAPER] Found {len(result)} restaurants for: {location}")
    for r in result:
        print(f"  - {r.get('name')} | {r.get('phone')} | {r.get('rating')}★")

    return result[:max_results]


def format_for_vapi(restaurants: list[dict]) -> str:
    """
    Format restaurant list as a readable string for Vapi to speak to the user.
    """
    if not restaurants:
        return "I'm sorry, I couldn't find any Indian restaurants matching your request."

    lines = [f"I found {len(restaurants)} Indian restaurants for you:"]
    for i, r in enumerate(restaurants, 1):
        lines.append(
            f"{i}. {r.get('name')} — rated {r.get('rating', 'N/A')} stars, "
            f"located at {r.get('address', 'address not available')}. "
            f"Open: {r.get('hours', 'hours not available')}."
        )
    lines.append("Which one would you like me to book, or shall I book the highest-rated one?")
    return " ".join(lines)
