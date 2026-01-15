import json
import secrets
from pathlib import Path
from typing import Any, Dict, Optional

try:
    import keyring  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    keyring = None


BRIDGE_SERVICE = "KeepToMD Bridge"
DEFAULT_CONFIG_DIR = Path.home() / ".keeptomd"
DEFAULT_CONFIG_PATH = DEFAULT_CONFIG_DIR / "bridge.json"


class BridgeStorage:
    def __init__(self, path: Path = DEFAULT_CONFIG_PATH) -> None:
        self._path = path

    @property
    def path(self) -> Path:
        return self._path

    def _load_raw(self) -> Dict[str, Any]:
        if not self._path.exists():
            return {}
        try:
            return json.loads(self._path.read_text())
        except Exception:
            return {}

    def _save_raw(self, data: Dict[str, Any]) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(json.dumps(data, indent=2, sort_keys=True))

    def get_or_create_device_id(self) -> str:
        data = self._load_raw()
        device_id = data.get("device_id")
        if isinstance(device_id, str) and len(device_id) == 16:
            return device_id
        device_id = secrets.token_hex(8)
        data["device_id"] = device_id
        self._save_raw(data)
        return device_id

    def get_email(self) -> Optional[str]:
        data = self._load_raw()
        email = data.get("email")
        return email if isinstance(email, str) else None

    def get_master_token(self, email: str) -> Optional[str]:
        if keyring is not None:
            try:
                return keyring.get_password(BRIDGE_SERVICE, email)
            except Exception:
                return None
        data = self._load_raw()
        return data.get("master_token")

    def set_master_token(self, email: str, token: str) -> str:
        data = self._load_raw()
        if keyring is not None:
            try:
                keyring.set_password(BRIDGE_SERVICE, email, token)
                data["token_storage"] = "keyring"
                data.pop("master_token", None)
                data["email"] = email
                self._save_raw(data)
                return "keyring"
            except Exception:
                pass
        data["master_token"] = token
        data["token_storage"] = "file"
        data["email"] = email
        self._save_raw(data)
        return "file"

    def clear_master_token(self, email: Optional[str]) -> None:
        data = self._load_raw()
        if keyring is not None and email:
            try:
                keyring.delete_password(BRIDGE_SERVICE, email)
            except Exception:
                pass
        data.pop("master_token", None)
        data.pop("email", None)
        data["token_storage"] = "file"
        self._save_raw(data)

    def get_token_storage(self) -> str:
        data = self._load_raw()
        return data.get("token_storage", "file")

    def get_note_state(self) -> Dict[str, Dict[str, str]]:
        data = self._load_raw()
        state = data.get("note_state")
        if isinstance(state, dict):
            return state
        return {}

    def set_note_state(self, state: Dict[str, Dict[str, str]]) -> None:
        data = self._load_raw()
        data["note_state"] = state
        self._save_raw(data)
