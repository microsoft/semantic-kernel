# Copyright (c) Microsoft. All rights reserved.

from semantic_kernel.connectors.openapi_plugin.models.rest_api_operation_payload_property import (
    RestApiOperationPayloadProperty,
)
from semantic_kernel.utils.experimental_decorator import experimental_class


@experimental_class
class RestApiOperationPayload:
    """RestApiOperationPayload."""

    def __init__(
        self,
        media_type: str,
        properties: list["RestApiOperationPayloadProperty"],
        description: str | None = None,
        schema: str | None = None,
    ):
        """Initialize the RestApiOperationPayload."""
        self.media_type = media_type
        self.properties = properties
        self.description = description
        self.schema = schema
