# Copyright (c) Microsoft. All rights reserved.

from typing import Annotated

from semantic_kernel.functions import kernel_function


class UserInputPlugin:
    """A plugin that requests user input."""

    @kernel_function(description="Request user feedback given the content.")
    def request_user_feedback(
        self, content: Annotated[str, "The content to request feedback on."]
    ) -> Annotated[str, "The feedback provided by the user."]:
        """Request user input."""
        return input(f"Please provide feedback on the content:\n\n{content}\n\n> ")
