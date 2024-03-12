"""
A fast serialization method for lists of integers.
"""

from typing import List


def dump(data: List[int]) -> str:
    return ",".join(str(x) for x in data)


def load(source: str) -> List[int]:
    return [int(x) for x in source.split(",")]
