# AI Restaurant Booking Agent

An end-to-end voice AI pipeline that finds Indian restaurants and books a table on your behalf — entirely through phone calls, with no manual steps.

> **Hackathon Demo:** [Watch on YouTube](https://www.youtube.com/watch?v=yIzozLUO2AI)

## How It Works

```
You call Vapi → speak your request
       ↓
AI searches for Indian restaurants via rtrvr.ai (real-time Google Maps data)
       ↓
AI reads you the top options → you confirm your choice
       ↓
AI calls the restaurant and books your table
       ↓
Google Calendar event is created automatically
       ↓
AI calls you back to confirm the reservation details
```

## Tech Stack

| Component | Technology |
|---|---|
| Voice AI | [Vapi](https://vapi.ai) with MiniMax voice |
| Web Scraping | [rtrvr.ai](https://rtrvr.ai) — real-time Google Maps agent |
| LLM | OpenAI GPT-4o |
| Server | FastAPI + Uvicorn |
| Calendar | Google Calendar API |
| State | JSON file store (`bookings.json`) |

## Project Structure

```
├── orchestrator.py      # Main FastAPI server — tool handlers, webhooks, call orchestration
├── scraper.py           # rtrvr.ai agent — finds restaurants with phone numbers in real time
├── calendar_service.py  # Google Calendar integration — creates event after confirmed booking
├── state_store.py       # Persists booking state across async Vapi calls
├── vapi_setup.py        # Configures the Vapi assistant with tools, voice, and server URL
├── make_call.py         # CLI utility to manually trigger an outbound Vapi call
├── webhook_server.py    # Lightweight event listener for basic Vapi webhooks
├── requirements.txt
├── .env.example
└── bookings.json        # Auto-generated at runtime (gitignored)
```

## Setup

### 1. Clone and install

```bash
git clone https://github.com/ezazahamad2003/afore221hackathon26.git
cd afore221hackathon26
pip install -r requirements.txt
```

### 2. Configure environment variables

```bash
cp .env.example .env
```

| Variable | Where to find it |
|---|---|
| `VAPI_PRIVATE_KEY` | [Vapi Dashboard](https://dashboard.vapi.ai) → Account → API Keys |
| `VAPI_ASSISTANT_ID` | Vapi Dashboard → Assistants |
| `VAPI_PHONE_NUMBER_ID` | Vapi Dashboard → Phone Numbers |
| `MY_PHONE_NUMBER` | Your number in E.164 format (e.g. `+15551234567`) |
| `RTRVR_API_KEY` | [rtrvr.ai Cloud](https://rtrvr.ai/cloud) → API Keys |
| `SERVER_BASE_URL` | Your public server URL (ngrok during dev) |
| `GOOGLE_*` | [Google Cloud Console](https://console.cloud.google.com) → Calendar API |

### 3. Expose your local server

```bash
ngrok http 8000
```

Copy the `https://...ngrok.io` URL into `.env` as `SERVER_BASE_URL`.

### 4. Configure the Vapi assistant

Registers the tools and sets MiniMax voice + server URL on your assistant:

```bash
python vapi_setup.py
```

### 5. Start the server

```bash
uvicorn orchestrator:app --reload --port 8000
```

### 6. Call your Vapi number

Speak naturally — for example:

> *"Find me an Indian restaurant near downtown San Jose for 2 people tonight at 7pm"*

The assistant will search, present options, book the table, and call you back with confirmation.

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/vapi/tools` | Handles Vapi tool calls (`search_restaurants`, `initiate_booking`) |
| `POST` | `/vapi/events` | Receives Vapi call lifecycle events |
| `GET` | `/bookings` | Returns all booking records |
| `GET` | `/health` | Health check |

## Booking State Machine

Each booking transitions through the following states:

```
pending → calling_restaurant → confirmed → notifying_user → notified
```

Tracked in `bookings.json` so no state is lost across async call events.

## Google Calendar Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com) and enable the **Google Calendar API**
2. Create OAuth 2.0 credentials (Desktop app type)
3. Generate a refresh token and add `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, and `GOOGLE_REFRESH_TOKEN` to `.env`

Without credentials, the system logs a notice and continues — all other pipeline steps run normally.

## Voice

This project uses **MiniMax** voice via Vapi (`Friendly_Person` voice ID) for all outbound calls — both to the restaurant and back to the user.
