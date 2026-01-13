# KeepToMD Bridge

Local HTTP bridge for Google Keep using `gkeepapi`.

## What it does
- Exposes a local API your web app can call.
- Keeps credentials local to the machine.

## Requirements
- Python 3.10+

## Setup
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run
```bash
uvicorn app.main:app --host 127.0.0.1 --port 3717
```

## Endpoints
- `GET /health` → `{ ok: true, logged_in: boolean }`
- `POST /login` → body `{ email, password }`
- `POST /logout`
- `GET /notes` → `{ notes: [...] }`

## Notes
- This service is for local use only.
- Use a Google app password where possible.
