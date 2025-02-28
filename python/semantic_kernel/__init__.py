# Copyright (c) Microsoft. All rights reserved.

from semantic_kernel.kernel import Kernel

__version__ = "1.22.0"

DEFAULT_RC_VERSION = f"{__version__}-rc1"

__all__ = ["DEFAULT_RC_VERSION", "Kernel", "__version__"]
