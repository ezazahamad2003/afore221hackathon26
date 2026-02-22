# AI Restaurant Booking Agent

An end-to-end voice AI pipeline that finds Indian restaurants and books a table on your behalf — all via phone calls.

## How It Works

```
You call Vapi → speak your request
       ↓
AI searches for Indian restaurants (via rtrvr.ai)
       ↓
AI reads you the options → you confirm
       ↓
AI calls the restaurant and books your table
       ↓
Google Calendar event is created
       ↓
AI calls you back to confirm the booking
```

## Tech Stack

| Component | Technology |
|---|---|
| Voice AI | [Vapi](https://vapi.ai) |
| Web scraping | [rtrvr.ai](https://rtrvr.ai) |
| Server | FastAPI + Uvicorn |
| Calendar | Google Calendar API |
| State | JSON file store |

## Project Structure

```
├── orchestrator.py      # Main FastAPI server — Vapi tool handlers & webhooks
├── scraper.py           # rtrvr.ai integration — finds restaurants with phone numbers
├── calendar_service.py  # Google Calendar integration
├── state_store.py       # Persists booking state across async calls
├── vapi_setup.py        # Configures the Vapi assistant with tools & server URL
├── make_call.py         # Utility — manually trigger an outbound call
├── requirements.txt
├── .env.example
└── bookings.json        # Auto-generated — tracks all bookings (gitignored)
```

## Setup

### 1. Clone and install dependencies

```bash
git clone <repo-url>
cd <repo-folder>
pip install -r requirements.txt
```

### 2. Configure environment variables

```bash
cp .env.example .env
```

Fill in your `.env` with:

| Variable | Where to get it |
|---|---|
| `VAPI_PRIVATE_KEY` | [Vapi Dashboard](https://dashboard.vapi.ai) → Account → API Keys |
| `VAPI_ASSISTANT_ID` | Vapi Dashboard → Assistants |
| `VAPI_PHONE_NUMBER_ID` | Vapi Dashboard → Phone Numbers |
| `MY_PHONE_NUMBER` | Your phone number in E.164 format (e.g. `+15551234567`) |
| `RTRVR_API_KEY` | [rtrvr.ai](https://rtrvr.ai/cloud) → API Keys |
| `SERVER_BASE_URL` | Your public server URL (see ngrok step below) |
| `GOOGLE_*` | [Google Cloud Console](https://console.cloud.google.com) → Calendar API |

### 3. Expose your local server with ngrok

```bash
ngrok http 8000
```

Copy the `https://...ngrok.io` URL into `.env` as `SERVER_BASE_URL`.

### 4. Configure your Vapi assistant

This registers the two tools (`search_restaurants`, `initiate_booking`) and sets the server URL on your assistant:

```bash
python vapi_setup.py
```

### 5. Start the orchestrator server

```bash
uvicorn orchestrator:app --reload --port 8000
```

### 6. Call your Vapi number and speak your request

Example: *"Find me an Indian restaurant near downtown San Jose for 2 people tonight at 7pm"*

The AI will:
1. Search for restaurants using rtrvr.ai
2. Read you the options
3. Book the table once you confirm
4. Call you back with confirmation

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/vapi/tools` | Vapi tool call handler |
| `POST` | `/vapi/events` | Vapi call lifecycle events |
| `GET` | `/bookings` | View all booking records |
| `GET` | `/health` | Health check |

## Google Calendar Setup

> Calendar integration is included but requires OAuth credentials.

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Enable the **Google Calendar API**
3. Create OAuth 2.0 credentials (Desktop app)
4. Download `credentials.json` and generate a refresh token
5. Add `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, and `GOOGLE_REFRESH_TOKEN` to `.env`

Until configured, the system will skip calendar creation and log a notice — everything else works normally.

## Notes

- `bookings.json` is auto-created and gitignored — it tracks all booking states
- The Vapi assistant uses GPT-4o for reasoning
- Restaurant calls and user confirmation calls use dynamic system prompts injected at call time via `assistantOverrides`
