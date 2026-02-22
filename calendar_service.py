import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

CALENDAR_ID          = os.getenv("GOOGLE_CALENDAR_ID", "primary")
GOOGLE_CLIENT_ID     = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_REFRESH_TOKEN = os.getenv("GOOGLE_REFRESH_TOKEN")

CREDENTIALS_READY = all([GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_REFRESH_TOKEN])


def _get_calendar_service():
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
    if not CREDENTIALS_READY:
        print(f"[CALENDAR] Credentials not configured — skipping. Would have created: {restaurant_name} on {date} at {time}")
        return {
            "status": "skipped",
            "event_summary": f"Dinner at {restaurant_name} for {party_size}",
            "event_date": date,
            "event_time": time,
        }

    try:
        service = _get_calendar_service()

        dt_str = f"{date} {time}"
        try:
            start_dt = datetime.strptime(dt_str, "%Y-%m-%d %I:%M %p")
        except ValueError:
            start_dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M")

        end_dt = start_dt + timedelta(hours=2)

        event = {
            "summary": f"Dinner at {restaurant_name}",
            "location": address,
            "description": f"Table for {party_size} — reservation under {customer_name}. Booked via AI assistant.",
            "start": {"dateTime": start_dt.isoformat(), "timeZone": "America/Los_Angeles"},
            "end":   {"dateTime": end_dt.isoformat(),   "timeZone": "America/Los_Angeles"},
            "reminders": {
                "useDefault": False,
                "overrides": [
                    {"method": "popup", "minutes": 60},
                    {"method": "email", "minutes": 1440},
                ],
            },
        }

        created = service.events().insert(calendarId=CALENDAR_ID, body=event).execute()
        print(f"[CALENDAR] Event created: {created.get('htmlLink')}")
        return {"status": "created", "event_id": created.get("id"), "html_link": created.get("htmlLink")}

    except Exception as e:
        print(f"[CALENDAR] Failed to create event: {e}")
        return {"status": "error", "reason": str(e)}
