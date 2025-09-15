# Copyright (c) Microsoft. All rights reserved.

from typing import Annotated

from semantic_kernel.functions import kernel_function


class UserPlugin:
    """A plugin that interacts with the user."""

    @kernel_function(description="Present the content to user and request feedback.")
    def request_user_feedback(
        self, content: Annotated[str, "The content to present and request feedback on."]
    ) -> Annotated[str, "The feedback provided by the user."]:
        """Request user feedback on the content."""
        return input(f"Please provide feedback on the content:\n\n{content}\n\n> ")
