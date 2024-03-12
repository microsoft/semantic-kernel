from typing import Generic, TypeVar, List, Optional
import heapq

_T = TypeVar("_T")


class SortedList(Generic[_T]):
    _vals: List[_T]

    def __init__(self):
        self._vals = []

    def push(self, val: _T):
        heapq.heappush(self._vals, val)

    def peek(self) -> Optional[_T]:
        if self.empty():
            return None
        return self._vals[0]

    def pop(self):
        heapq.heappop(self._vals)

    def empty(self) -> bool:
        return not bool(self._vals)
