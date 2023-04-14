# Copyright (c) Microsoft. All rights reserved.

from typing import Any


class static_property(staticmethod):
    def __get__(self, obj: Any, obj_type: Any = None) -> Any:
        return super().__get__(obj, obj_type)()
