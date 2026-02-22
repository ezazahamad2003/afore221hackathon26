"""
calendar_service.py — Google Calendar integration (placeholder).

⚠️  API credentials not yet configured.
    To activate, fill in GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET,
    and GOOGLE_REFRESH_TOKEN in your .env file.

    Setup guide:
    https://developers.google.com/calendar/api/quickstart/python
"""

import os
from datetime import datetime, timedelta

from dotenv import load_dotenv

load_dotenv()

CALENDAR_ID = os.getenv("GOOGLE_CALENDAR_ID", "primary")
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_REFRESH_TOKEN = os.getenv("GOOGLE_REFRESH_TOKEN")

CREDENTIALS_READY = all([GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_REFRESH_TOKEN])


def _get_calendar_service():
    """Build and return an authenticated Google Calendar service client."""
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build

    creds = Credentials(
        token=None,
        refresh_token=GOOGLE_REFRESH_TOKEN,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=GOOGLE_CLIENT_ID,
        client_secret=GOOGLE_CLIENT_SECRET,
        scopes=["https://www.googleapis.com/auth/calendar"],
    )
    return build("calendar", "v3", credentials=creds)


def add_booking_to_calendar(
    restaurant_name: str,
    address: str,
    date: str,
    time: str,
    party_size: int,
    customer_name: str,
) -> dict:
    """
    Add a restaurant booking as a Google Calendar event.

    Args:
        restaurant_name: Name of the restaurant
        address:         Restaurant address
        date:            Date string e.g. "2026-02-22"
        time:            Time string e.g. "7:00 PM"
        party_size:      Number of people
        customer_name:   Name the reservation is under

    Returns:
        dict with event_id and html_link, or a placeholder if credentials missing
    """

    if not CREDENTIALS_READY:
        print("[CALENDAR] ⚠️  Google credentials not configured — skipping calendar event.")
        print(f"[CALENDAR] Would have created: '{restaurant_name}' on {date} at {time} for {party_size}")
        return {
            "status": "skipped",
            "reason": "Google Calendar credentials not configured yet",
            "event_summary": f"Dinner at {restaurant_name} for {party_size}",
            "event_date": date,
            "event_time": time,
        }

    try:
        service = _get_calendar_service()

        # Parse datetime
        dt_str = f"{date} {time}"
        try:
            start_dt = datetime.strptime(dt_str, "%Y-%m-%d %I:%M %p")
        except ValueError:
            start_dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M")

        end_dt = start_dt + timedelta(hours=2)

        event = {
            "summary": f"🍽️ Dinner at {restaurant_name}",
            "location": address,
            "description": (
                f"Table for {party_size} — reservation under {customer_name}.\n"
                f"Booked via AI assistant."
            ),
            "start": {
                "dateTime": start_dt.isoformat(),
                "timeZone": "America/Los_Angeles",
            },
            "end": {
                "dateTime": end_dt.isoformat(),
                "timeZone": "America/Los_Angeles",
            },
            "reminders": {
                "useDefault": False,
                "overrides": [
                    {"method": "popup", "minutes": 60},
                    {"method": "email", "minutes": 1440},
                ],
            },
        }

        created = service.events().insert(calendarId=CALENDAR_ID, body=event).execute()

        print(f"[CALENDAR] ✅ Event created: {created.get('htmlLink')}")
        return {
            "status": "created",
            "event_id": created.get("id"),
            "html_link": created.get("htmlLink"),
        }

    except Exception as e:
        print(f"[CALENDAR] ❌ Failed to create event: {e}")
        return {"status": "error", "reason": str(e)}
