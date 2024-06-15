# Copyright (c) Microsoft. All rights reserved.

from typing import Annotated

from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.functions.kernel_function_decorator import kernel_function
from semantic_kernel.kernel_pydantic import KernelBaseModel


class FunctionCallingStepwisePlannerResult(KernelBaseModel):
    """The result of the function calling stepwise planner."""

    final_answer: str = ""
    chat_history: ChatHistory | None = None
    iterations: int = 0


class UserInteraction:
    """The Kernel Function used to interact with the user."""

    @kernel_function(description="The final answer to return to the user", name="SendFinalAnswer")
    def send_final_answer(self, answer: Annotated[str, "The final answer"]) -> str:
        """Send the final answer to the user."""
        return "Thanks"
