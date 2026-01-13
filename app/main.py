from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .keep_client import KeepClient


class LoginRequest(BaseModel):
    email: str
    password: str


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
    return {"ok": True, "logged_in": keep_client.logged_in}


@app.post("/login")
def login(payload: LoginRequest):
    if not keep_client.login(payload.email, payload.password):
        raise HTTPException(status_code=401, detail="Login failed.")
    return {"ok": True}


@app.post("/logout")
def logout():
    keep_client.logout()
    return {"ok": True}


@app.get("/notes")
def notes():
    if not keep_client.logged_in:
        raise HTTPException(status_code=401, detail="Not logged in.")
    return {"notes": keep_client.list_notes()}
