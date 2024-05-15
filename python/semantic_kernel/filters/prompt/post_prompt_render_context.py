# Copyright (c) Microsoft. All rights reserved.
from __future__ import annotations

from semantic_kernel.filters.prompt.prompt_hook_context_base import PromptHookContextBase


class PostPromptRenderContext(PromptHookContextBase):
    """Post Prompt Render Context

    Receives relevant parts of the the execution after the prompt is rendered.
    When a handler changes the arguments in the context,
    the whole new arguments are used, they are not updated, but replaced,
    make sure to use the update_arguments function, since that also raises the flag that the arguments were updated.

    Args:
        function (KernelFunction): The function that is being executed.
        arguments (KernelArguments): The arguments that are being passed to the function.
        metadata (Dict[str, Any]): The metadata of the function that is being executed.
        kernel (Kernel): The kernel that is executing the function.
        rendered_prompt (str): The rendered prompt.

    Flags:
        updated_arguments (bool): Whether the arguments were updated, default False.

    Methods:
        update_arguments: Updates the arguments and raises the updated_arguments flag.

    """

    rendered_prompt: str
