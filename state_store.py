import json
import os
import uuid
from datetime import datetime
from typing import Optional

STATE_FILE = "bookings.json"


def _load() -> dict:
    if not os.path.exists(STATE_FILE):
        return {}
    with open(STATE_FILE, "r") as f:
        return json.load(f)


def _save(data: dict):
    with open(STATE_FILE, "w") as f:
        json.dump(data, f, indent=2)


def create_booking(
    customer_name: str,
    customer_phone: str,
    restaurant_name: str,
    restaurant_phone: str,
    location: str,
    date: str,
    time: str,
    party_size: int,
) -> str:
    bookings   = _load()
    booking_id = str(uuid.uuid4())
    bookings[booking_id] = {
        "id":           booking_id,
        "status":       "pending",  # pending → calling_restaurant → confirmed → notifying_user → notified
        "created_at":   datetime.utcnow().isoformat(),
        "customer_name":    customer_name,
        "customer_phone":   customer_phone,
        "restaurant_name":  restaurant_name,
        "restaurant_phone": restaurant_phone,
        "location":     location,
        "date":         date,
        "time":         time,
        "party_size":   party_size,
        "restaurant_call_id":   None,
        "confirmation_call_id": None,
        "confirmation_details": None,
        "calendar_event_id":    None,
    }
    _save(bookings)
    return booking_id


def get_booking(booking_id: str) -> Optional[dict]:
    return _load().get(booking_id)


def get_booking_by_call_id(call_id: str) -> Optional[dict]:
    for booking in _load().values():
        if booking.get("restaurant_call_id") == call_id:
            return booking
        if booking.get("confirmation_call_id") == call_id:
            return booking
    return None


def update_booking(booking_id: str, **kwargs):
    bookings = _load()
    if booking_id not in bookings:
        raise KeyError(f"Booking {booking_id} not found")
    bookings[booking_id].update(kwargs)
    _save(bookings)


def all_bookings() -> list:
    return list(_load().values())
