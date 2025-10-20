# FILE: src/openai_rooms_pkg/services/credentials.py
from threading import RLock
from typing import Optional

# Pylance-friendly singleton without inline attr annotations triggering reportInvalidTypeForm.


class CredentialsRegistry:
    """In-memory singleton registry for secrets (key -> secret value)."""

    _instance = None  # type: Optional["CredentialsRegistry"]
    _lock = RLock()

    def __new__(cls) -> "CredentialsRegistry":
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._store = {}
        return cls._instance

    def store(self, key: str, value: str) -> None:
        if not isinstance(key, str) or not key:
            raise ValueError("CredentialsRegistry.store: key must be a non-empty string")
        self._store[key] = value

    def store_multiple(self, mapping: dict[str, str]) -> None:
        if not isinstance(mapping, dict):
            raise ValueError("CredentialsRegistry.store_multiple: mapping must be a dict[str, str]")
        for k, v in mapping.items():
            self.store(k, v)

    def get(self, key: str) -> Optional[str]:
        return self._store.get(key)

    def has(self, key: str) -> bool:
        return key in self._store

    def clear(self) -> None:
        self._store.clear()

    def keys(self) -> list[str]:
        return list(self._store.keys())
