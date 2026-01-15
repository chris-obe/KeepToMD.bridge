import hashlib
import json
import threading
from typing import Dict, List, Optional, TypedDict

import gkeepapi
import gpsoauth

from .storage import BridgeStorage


class KeepNote(TypedDict):
    id: str
    title: str
    text: str
    created: str
    updated: str
    labels: List[str]
    is_list: bool
    hash: str


class KeepCompareResult(TypedDict):
    summary: Dict[str, int]
    new: List[KeepNote]
    modified: List[KeepNote]
    hashes: Dict[str, str]
    notes: List[KeepNote]


class KeepClient:
    def __init__(self, storage: Optional[BridgeStorage] = None) -> None:
        self._keep = gkeepapi.Keep()
        self._lock = threading.Lock()
        self._logged_in = False
        self._email: Optional[str] = None
        self._auth_mode: Optional[str] = None
        self._storage = storage or BridgeStorage()
        self._device_id = self._storage.get_or_create_device_id()
        self._try_restore_session()

    @property
    def logged_in(self) -> bool:
        return self._logged_in

    @property
    def email(self) -> Optional[str]:
        return self._email

    @property
    def auth_mode(self) -> Optional[str]:
        return self._auth_mode

    @property
    def device_id(self) -> str:
        return self._device_id

    def token_storage(self) -> str:
        return self._storage.get_token_storage()

    def _try_restore_session(self) -> None:
        data_email = self._storage.get_email()
        if not data_email:
            return
        master_token = self._storage.get_master_token(data_email)
        if not master_token:
            return
        try:
            self._authenticate_with_master_token(data_email, master_token)
            self._auth_mode = "stored"
        except Exception:
            self._logged_in = False

    def _authenticate_with_master_token(self, email: str, master_token: str) -> None:
        auth = gkeepapi.APIAuth(self._keep.OAUTH_SCOPES)
        auth.load(email, master_token, self._device_id)
        self._keep.load(auth, sync=True)
        self._logged_in = True
        self._email = email

    def login(self, email: str, token: str, mode: str) -> bool:
        with self._lock:
            if mode == "oauth_token":
                master_token = self._exchange_oauth_token(email, token)
            else:
                master_token = self._exchange_app_password(email, token)
            self._authenticate_with_master_token(email, master_token)
            self._storage.set_master_token(email, master_token)
            self._auth_mode = mode
            return self._logged_in

    def logout(self, forget: bool = False) -> None:
        with self._lock:
            if forget:
                self._storage.clear_master_token(self._email)
            self._logged_in = False
            self._auth_mode = None
            self._email = None
            self._keep = gkeepapi.Keep()

    def list_notes(self) -> List[KeepNote]:
        with self._lock:
            if not self._logged_in:
                return []
            self._keep.sync()
            return [self._build_note_summary(note) for note in self._keep.all()]

    def compare_notes(
        self, known_hashes: Optional[Dict[str, str]] = None, persist: bool = True
    ) -> KeepCompareResult:
        notes = self.list_notes()
        if known_hashes is None:
            known_hashes = {
                note_id: data.get("hash", "")
                for note_id, data in self._storage.get_note_state().items()
            }
        new_notes: List[KeepNote] = []
        modified_notes: List[KeepNote] = []
        hashes: Dict[str, str] = {}
        for note in notes:
            note_hash = note["hash"]
            hashes[note["id"]] = note_hash
            known_hash = known_hashes.get(note["id"]) if known_hashes else None
            if not known_hash:
                new_notes.append(note)
            elif known_hash != note_hash:
                modified_notes.append(note)

        summary = {
            "total": len(notes),
            "new": len(new_notes),
            "modified": len(modified_notes),
            "unchanged": len(notes) - len(new_notes) - len(modified_notes),
        }

        if persist:
            self._storage.set_note_state(
                {
                    note["id"]: {
                        "hash": note["hash"],
                        "updated": note["updated"],
                    }
                    for note in notes
                }
            )

        return {
            "summary": summary,
            "new": new_notes,
            "modified": modified_notes,
            "hashes": hashes,
            "notes": notes,
        }

    def _exchange_app_password(self, email: str, password: str) -> str:
        res = gpsoauth.perform_master_login(email, password, self._device_id)
        if res.get("Error") == "NeedsBrowser":
            raise gkeepapi.exception.BrowserLoginRequiredException(res.get("Url"))
        if "Token" not in res:
            raise gkeepapi.exception.LoginException(
                res.get("Error"), res.get("ErrorDetail")
            )
        return res["Token"]

    def _exchange_oauth_token(self, email: str, oauth_token: str) -> str:
        res = gpsoauth.exchange_token(email, oauth_token, self._device_id)
        if "Token" not in res:
            raise gkeepapi.exception.LoginException(
                res.get("Error"), res.get("ErrorDetail")
            )
        return res["Token"]

    def _build_note_summary(self, note: gkeepapi.node.Node) -> KeepNote:
        labels = []
        try:
            labels = [label.name for label in note.labels.all() if label is not None]
        except Exception:
            labels = []
        if not labels:
            try:
                labels = [label_id for label_id in note.labels._labels.keys()]  # type: ignore[attr-defined]
            except Exception:
                labels = []

        payload = {
            "id": note.id,
            "title": note.title or "",
            "text": note.text or "",
            "labels": labels,
            "created": note.timestamps.created.isoformat(),
            "updated": note.timestamps.updated.isoformat(),
            "archived": getattr(note, "archived", False),
            "pinned": getattr(note, "pinned", False),
            "is_list": isinstance(note, gkeepapi.node.List),
        }
        note_hash = hashlib.sha256(
            json.dumps(
                payload,
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=True,
            ).encode("utf-8")
        ).hexdigest()

        return {
            "id": note.id,
            "title": note.title or "",
            "text": note.text or "",
            "created": note.timestamps.created.isoformat(),
            "updated": note.timestamps.updated.isoformat(),
            "labels": labels,
            "is_list": isinstance(note, gkeepapi.node.List),
            "hash": note_hash,
        }
