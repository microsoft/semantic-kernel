# Copyright (c) Microsoft. All rights reserved.

from semantic_kernel.utils.feature_stage_decorator import experimental


@experimental
class RestApiExpectedResponse:
    """RestApiExpectedResponse."""

    def __init__(self, description: str, media_type: str, schema: dict[str, str] | None = None):
        """Initialize the RestApiExpectedResponse."""
        self.description = description
        self.media_type = media_type
        self.schema = schema
