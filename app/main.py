from enum import Enum
from typing import Dict, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import gkeepapi

from .keep_client import KeepClient


class AuthMode(str, Enum):
    app_password = "app_password"
    oauth_token = "oauth_token"


class LoginRequest(BaseModel):
    email: str
    token: Optional[str] = None
    password: Optional[str] = None
    mode: AuthMode = AuthMode.app_password


class LogoutRequest(BaseModel):
    forget: bool = False


class CompareRequest(BaseModel):
    known_hashes: Optional[Dict[str, str]] = None
    persist: bool = True


app = FastAPI(title="KeepToMD Bridge", version="0.1.0")
keep_client = KeepClient()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {
        "ok": True,
        "logged_in": keep_client.logged_in,
        "email": keep_client.email,
        "auth_mode": keep_client.auth_mode,
        "token_storage": keep_client.token_storage(),
        "device_id": keep_client.device_id,
    }


@app.get("/auth/status")
def auth_status():
    return {
        "ok": True,
        "logged_in": keep_client.logged_in,
        "email": keep_client.email,
        "auth_mode": keep_client.auth_mode,
        "token_storage": keep_client.token_storage(),
        "device_id": keep_client.device_id,
    }


@app.post("/login")
def login(payload: LoginRequest):
    token = payload.token or payload.password
    if not token:
        raise HTTPException(status_code=400, detail="Missing token.")
    try:
        if not keep_client.login(payload.email, token, payload.mode.value):
            raise HTTPException(status_code=401, detail="Login failed.")
    except gkeepapi.exception.BrowserLoginRequiredException as error:
        raise HTTPException(
            status_code=409,
            detail={
                "message": "Browser login required.",
                "url": error.args[0] if error.args else None,
            },
        )
    except Exception as error:
        message = str(error) if str(error) else "Login failed."
        raise HTTPException(status_code=401, detail=message)
    return {"ok": True}


@app.post("/logout")
def logout(payload: Optional[LogoutRequest] = None):
    keep_client.logout(forget=payload.forget if payload else False)
    return {"ok": True}


@app.get("/notes")
def notes():
    if not keep_client.logged_in:
        raise HTTPException(status_code=401, detail="Not logged in.")
    return {"notes": keep_client.list_notes()}


@app.post("/sync/compare")
def compare(payload: CompareRequest):
    if not keep_client.logged_in:
        raise HTTPException(status_code=401, detail="Not logged in.")
    return keep_client.compare_notes(payload.known_hashes, payload.persist)
