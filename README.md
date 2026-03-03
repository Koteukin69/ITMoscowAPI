# ITMoscow API

Unofficial REST API for [IT Moscow College](https://it-moscow.pro) (formerly МГКЭИТ).
Provides access to buildings, groups, and class schedules via HTML scraping.

Built with **Python + FastAPI**. Deployable as a serverless app on [Vercel](https://vercel.com).

> The project may break at any time if the website structure changes.

---

## Authentication

All endpoints require a Bearer token:

```
Authorization: Bearer <your-token>
```

The token is set via the `API_TOKEN` environment variable. You create the token yourself — no registration needed.

---

## Endpoints

### `GET /api/buildings`

Returns the list of all buildings.

**Response**
```json
[
  { "name": "Коренчева", "key": "korencheva" },
  { "name": "Каховка", "key": "kahovka" }
]
```

---

### `GET /api/groups`

Returns all groups from all buildings.

**Response**
```json
[
  { "name": "ИС-24-9", "building": "korencheva", "key": "%D0%98%D0%A1-24-9" }
]
```

- `building` — building key
- `key` — URL-encoded group name (for filtering)

---

### `POST /api/groups`

Filter groups by building key and/or group key. Both fields are optional.

**Request body**
```json
{
  "building": "korencheva",
  "key": "%D0%98%D0%A1-24-9"
}
```

**Response** — same format as `GET /api/groups`

---

### `POST /itmoscow/api/v1/schedule/day`

Get the schedule for a group on a specific weekday.

**Request body**
```json
{
  "group": "ИС-24-9",
  "building": "korencheva",
  "weekday": 0,
  "replacements": false
}
```

| Field          | Type   | Description                                                        |
|----------------|--------|--------------------------------------------------------------------|
| `group`        | string | Group name (from `/api/groups` → `name`)                          |
| `building`     | string | Building key (from `/api/groups` → `building`)                    |
| `weekday`      | int    | 0 = Monday … 5 = Saturday                                         |
| `replacements` | bool   | Apply today's replacements. Only valid when `weekday` == today.   |

**Response**
```json
{
  "weekday": "Понедельник",
  "lessons": [
    {
      "number": 1,
      "time": "08:00 - 09:35",
      "subject": "Математика",
      "teacher": "Иванов И.И.",
      "room": "Кабинет 301"
    }
  ]
}
```

> Returns `400` if `replacements: true` but `weekday` is not today (Moscow time, UTC+3).

---

## Local Development

**Requirements:** Python 3.11+

```bash
# 1. Clone and enter the repo
git clone https://github.com/Koteukin69/ITMoscowAPI.git
cd ITMoscowAPI

# 2. Create a virtual environment
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set up environment
cp .env.example .env
# Edit .env — set API_TOKEN to any secret string you choose

# 5. Run
uvicorn app.main:app --reload
```

- API: `http://localhost:8000`
- Interactive docs: `http://localhost:8000/docs`

---

## Deploy to Vercel

### Prerequisites

- GitHub account with this repo
- [Vercel account](https://vercel.com/signup) (free tier is enough)

### Step 1 — Import the repository

Go to [vercel.com/new](https://vercel.com/new) → **Add New Project** → import your GitHub repo.

### Step 2 — Project settings

On the configuration screen:
- **Framework Preset:** Other
- **Root Directory:** `/` (leave default)
- No build command needed

### Step 3 — Set environment variables

In **Settings → Environment Variables**, add:

| Name           | Value                   | Notes                              |
|----------------|-------------------------|------------------------------------|
| `API_TOKEN`    | your secret token       | Required. Any string you choose.   |
| `ITMOSCOW_URL` | `https://it-moscow.pro` | Optional, this is the default.     |

### Step 4 — Deploy

Click **Deploy**. Vercel installs `requirements.txt` and deploys the app.

Your API will be live at `https://<your-project>.vercel.app`.

### How it works

- `vercel.json` routes all requests to `api/index.py`
- `api/index.py` exposes the FastAPI ASGI app to Vercel's Python runtime
- Each invocation runs as a serverless function
- Building and group data is cached in-memory on warm instances (30 min TTL)
- Schedule data is always fetched fresh (no caching)

### Updates

Push to GitHub → Vercel redeploys automatically.

---

## Project Structure

```
├── api/
│   └── index.py              # Vercel entry point
├── app/
│   ├── main.py               # FastAPI app
│   ├── config.py             # Settings (API_TOKEN, ITMOSCOW_URL)
│   ├── auth.py               # Bearer token verification
│   ├── models.py             # Pydantic models
│   ├── routers/
│   │   ├── buildings.py      # GET /api/buildings
│   │   ├── groups.py         # GET/POST /api/groups
│   │   └── schedule.py       # POST /itmoscow/api/v1/schedule/day
│   └── services/
│       ├── html_service.py   # Async HTTP fetching
│       ├── building_service.py
│       ├── group_service.py
│       └── schedule_service.py
├── requirements.txt
├── vercel.json
└── .env.example
```
