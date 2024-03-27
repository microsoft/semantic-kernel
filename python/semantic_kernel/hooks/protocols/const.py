# Copyright (c) Microsoft. All rights reserved.
from __future__ import annotations

from semantic_kernel.hooks.protocols.post_function_invoke import PostFunctionInvokeProtocol
from semantic_kernel.hooks.protocols.pre_function_invoke import PreFunctionInvokeProtocol

HOOK_PROTOCOLS = {"pre_function_invoke": PreFunctionInvokeProtocol, "post_function_invoke": PostFunctionInvokeProtocol}
