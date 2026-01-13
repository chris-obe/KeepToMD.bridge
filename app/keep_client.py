import threading
from typing import List, Optional, TypedDict

import gkeepapi


class KeepNote(TypedDict):
    id: str
    title: str
    text: str
    created: str
    updated: str


class KeepClient:
    def __init__(self) -> None:
        self._keep = gkeepapi.Keep()
        self._lock = threading.Lock()
        self._logged_in = False

    @property
    def logged_in(self) -> bool:
        return self._logged_in

    def login(self, email: str, password: str) -> bool:
        with self._lock:
            success = self._keep.login(email, password)
            self._logged_in = bool(success)
            return self._logged_in

    def logout(self) -> None:
        with self._lock:
            self._logged_in = False
            self._keep = gkeepapi.Keep()

    def list_notes(self) -> List[KeepNote]:
        with self._lock:
            if not self._logged_in:
                return []
            self._keep.sync()
            notes: List[KeepNote] = []
            for note in self._keep.all():
                notes.append(
                    {
                        "id": note.id,
                        "title": note.title or "",
                        "text": note.text or "",
                        "created": note.timestamps.created.isoformat(),
                        "updated": note.timestamps.updated.isoformat(),
                    }
                )
            return notes
