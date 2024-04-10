# Copyright (c) Microsoft. All rights reserved.

import sys

if sys.version_info >= (3, 9):
    from typing import Annotated
else:
    from typing_extensions import Annotated

from semantic_kernel.functions.kernel_function_decorator import kernel_function

class BookingsPlugin:
