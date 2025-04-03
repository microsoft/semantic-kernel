# Copyright (c) Microsoft. All rights reserved.

from typing import TypeVar

from samples.concepts.resources.utils import Colors, print_with_color
from semantic_kernel.data import VectorSearchResult

_T = TypeVar("_T")


def print_record(result: VectorSearchResult[_T] | None = None, record: _T | None = None):
    if result:
        record = result.record
    print_with_color(f"  Found id: {record.id}", Colors.CGREEN)
    if result and result.score is not None:
        print_with_color(f"    Score: {result.score}", Colors.CWHITE)
    print_with_color(f"    Content: {record.content}", Colors.CWHITE)
    print_with_color(f"    Tag: {record.tag}", Colors.CWHITE)
    if record.vector is not None:
        print_with_color(f"    Vector (first five): {record.vector[:5]}", Colors.CWHITE)
