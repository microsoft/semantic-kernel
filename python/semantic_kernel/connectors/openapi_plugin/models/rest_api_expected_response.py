# Copyright (c) Microsoft. All rights reserved.


from semantic_kernel.utils.experimental_decorator import experimental_class


@experimental_class
class RestApiExpectedResponse:
    """RestApiExpectedResponse."""

    def __init__(self, description: str, media_type: str, schema: dict[str, str] | None = None):
        """Initialize the RestApiExpectedResponse."""
        self.description = description
        self.media_type = media_type
        self.schema = schema
