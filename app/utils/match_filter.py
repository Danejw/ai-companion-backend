from datetime import datetime
from typing import Callable, List, Any, Dict

class MemoryFilter:
    def __init__(self):
        self.conditions: List[Callable[[Dict[str, Any]], bool]] = []
        self.or_conditions: List[Callable[[Dict[str, Any]], bool]] = [] 
        self.sort_order: str = None
        self.sort_key: str = "timestamp"

        
    def match(self, key: str, expected_value: Any) -> "MemoryFilter":
        self.conditions.append(lambda memory: self._get_value(memory, key) == expected_value)
        return self
    
    def or_match(self, key: str, expected_value: Any) -> "MemoryFilter":
        self.or_conditions.append(lambda memory: self._get_value(memory, key) == expected_value)
        return self

    def greater_than_or_equal(self, key: str, threshold: Any) -> "MemoryFilter":
        self.conditions.append(lambda memory: self._compare(self._get_value(memory, key), threshold, op="gte"))
        return self

    def less_than_or_equal(self, key: str, threshold: Any) -> "MemoryFilter":
        self.conditions.append(lambda memory: self._compare(self._get_value(memory, key), threshold, op="lte"))
        return self

    def contains(self, key: str, expected_item: Any) -> "MemoryFilter":
        self.conditions.append(lambda memory: expected_item in self._get_value(memory, key, default=[]))
        return self
    
    def or_contains(self, key: str, expected_item: Any) -> "MemoryFilter":
        self.or_conditions.append(lambda memory: expected_item in self._get_value(memory, key, default=[]))
        return self
    
    def contains_any(self, key: str, items: List[Any]) -> "MemoryFilter":
        print("contains_any: ", key, items)
        self.conditions.append(lambda memory: any(item in self._get_value(memory, key, default=[]) for item in items))
        return self
    
    def contains_all(self, key: str, items: List[Any]) -> "MemoryFilter":
        self.conditions.append(lambda memory: all(item in self._get_value(memory, key, default=[]) for item in items))
        return self

    def sort_by_date(self, order: str = "desc") -> "MemoryFilter":
        if order not in ["asc", "desc"]:
            raise ValueError("Order must be 'asc' or 'desc'")
        self.sort_order = order
        return self
    
    def sort_by_similarity(self, order: str = "desc") -> "MemoryFilter":
        if order not in ["asc", "desc"]:
            raise ValueError("Order must be 'asc' or 'desc'")
        self.sort_order = order
        self.sort_key = "similarity"
        return self

    def apply(self, memories: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        filtered = [
            memory for memory in memories
            if (all(condition(memory) for condition in self.conditions) or
                any(condition(memory) for condition in self.or_conditions))
        ]
        
        if self.sort_order:
            if self.sort_key == "timestamp":
                filtered = sorted(
                    filtered,
                    key=lambda m: datetime.fromisoformat(str(m.get("timestamp"))) if m.get("timestamp") else datetime.min,
                    reverse=(self.sort_order == "desc")
                )
            elif self.sort_key == "similarity":
                filtered = sorted(
                    filtered,
                    key=lambda m: m.get("similarity", 0.0),
                    reverse=(self.sort_order == "desc")
                )
                
        return filtered
    
    def _get_value(self, memory: Dict[str, Any], key: str, default: Any = None) -> Any:
        """
        Supports nested metadata retrieval: prioritizes memory['metadata'][key] if exists,
        otherwise checks top-level.
        """
        if "metadata" in memory and key in memory["metadata"]:
            return memory["metadata"].get(key, default)
        return memory.get(key, default)

    def _compare(self, value: Any, threshold: Any, op: str) -> bool:
        """
        Handles numerical and datetime comparisons.
        """
        if value is None:
            return False

        if isinstance(value, str) and self._is_date_string(value):
            value = datetime.fromisoformat(value)
        if isinstance(threshold, str) and self._is_date_string(threshold):
            threshold = datetime.fromisoformat(threshold)

        if op == "gte":
            return value >= threshold
        elif op == "lte":
            return value <= threshold
        return False

    def _is_date_string(self, value: str) -> bool:
        try:
            datetime.fromisoformat(value)
            return True
        except ValueError:
            return False
