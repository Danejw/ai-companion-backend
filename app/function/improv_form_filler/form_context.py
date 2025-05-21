# app/context/store.py
from typing import Any, Dict
from threading import Lock


class FormContext:
    def __init__(self):
        self.user_context_store = {}
        self.store_lock = Lock()

    def get_context(self, user_id: str) -> Dict[str, Any]:
        with self.store_lock:
            return self.user_context_store.get(user_id, {})
    
    def get_context_key(self, user_id: str, key: str) -> Any:
        with self.store_lock:
            return self.user_context_store.get(user_id, {}).get(key)

    def update_context(self, user_id: str, key: str, value: Any) -> None:
        with self.store_lock:
            self.user_context_store.setdefault(user_id, {})[key] = value

    def delete_context(self, user_id: str) -> None:
        with self.store_lock:
            self.user_context_store.pop(user_id, None)
        
    def delete_context_key(self, user_id: str, key: str) -> None:
        with self.store_lock:
            user_data = self.user_context_store.get(user_id)
            if user_data and key in user_data:
                del user_data[key]

    def dump_context(self, user_id: str) -> Dict[str, Any]:
        with self.store_lock:
            return dict(self.user_context_store.get(user_id, {}))
      
    def replace_context(self, user_id: str, key: str, value: Any) -> None:
        with self.store_lock:
            if user_id in self.user_context_store:
                self.user_context_store[user_id][key] = value


