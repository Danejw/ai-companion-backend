# app/context/store.py

from typing import Any, Dict
from threading import Lock

# Shared in-memory context store (per user)
user_context_store: Dict[str, Dict[str, Any]] = {}
store_lock = Lock()

def get_context(user_id: str) -> Dict[str, Any]:
    with store_lock:
        return user_context_store.get(user_id, {})

def update_context(user_id: str, key: str, value: Any) -> None:
    with store_lock:
        user_context_store.setdefault(user_id, {})[key] = value

def delete_context(user_id: str) -> None:
    with store_lock:
        user_context_store.pop(user_id, None)

def dump_context(user_id: str) -> Dict[str, Any]:
    with store_lock:
        return dict(user_context_store.get(user_id, {}))
