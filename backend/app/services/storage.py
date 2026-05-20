from pathlib import Path

from app.core.config import get_settings


class LocalObjectStorage:
    def __init__(self) -> None:
        self.root = get_settings().object_storage_dir
        self.root.mkdir(parents=True, exist_ok=True)

    def write_bytes(self, key: str, content: bytes) -> Path:
        path = self.root / key
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        return path

    def public_key(self, key: str) -> str:
        return key

    def public_url(self, key: str) -> str:
        normalized = key.lstrip("/")
        return f"/static/{normalized}"
