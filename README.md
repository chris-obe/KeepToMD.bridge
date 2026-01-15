# KeepToMD Bridge

Local HTTP bridge for Google Keep using `gkeepapi`.

## What it does
- Exposes a local API your web app can call.
- Keeps credentials local to the machine.

## Requirements
- Python 3.10+
- Optional: OS keychain support via `keyring`

## Quick start
```bash
git clone https://github.com/chris-obe/KeepToMD.bridge.git
cd KeepToMD-bridge
./setup.sh
# or run immediately:
./setup.sh --run
```

## Manual setup
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
- `GET /auth/status` → `{ ok, logged_in, email, auth_mode, token_storage, device_id }`
- `POST /login` → body `{ email, mode, token }`
- `POST /logout`
- `GET /notes` → `{ notes: [...] }`
- `POST /sync/compare` → `{ summary, new, modified, hashes, notes }`

## Notes
- This service is for local use only.
- Use a Google app password where possible.

## Authentication (two modes)
KeepToMD-bridge supports two authentication paths:

### 1) App Password (recommended)
Use this if your account allows App Passwords (requires 2-Step Verification and no Advanced Protection).

Steps:
1. Open `https://myaccount.google.com/apppasswords`
2. Create a new App Password (name it `KeepToMD`).
3. Copy the 16-character password (remove spaces).
4. Use it with `POST /login`:
   ```json
   { "email": "you@gmail.com", "mode": "app_password", "token": "abcd efgh ijkl mnop" }
   ```

### 2) Browser Token (experimental)
Use this when App Passwords fail or are unavailable.

Steps:
1. Open `https://accounts.google.com/EmbeddedSetup` in Chrome/Firefox.
2. Sign in (2FA/captcha happens in the browser).
3. Open DevTools → Application (Chrome) / Storage (Firefox).
4. Select `accounts.google.com` cookies.
5. Copy the cookie named `oauth_token`.
6. Use it with `POST /login`:
   ```json
   { "email": "you@gmail.com", "mode": "oauth_token", "token": "oauth2_4/..." }
   ```

This flow is unofficial and may break if Google changes its login flow.

## Token storage
- If `keyring` is installed, the bridge stores the master token in your OS keychain.
- Otherwise it falls back to a local config file at `~/.keeptomd/bridge.json`.
