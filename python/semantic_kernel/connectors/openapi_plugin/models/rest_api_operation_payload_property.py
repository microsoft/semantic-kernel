# Copyright (c) Microsoft. All rights reserved.

from typing import Any

from semantic_kernel.utils.experimental_decorator import experimental_class


@experimental_class
class RestApiOperationPayloadProperty:
    def __init__(
        self,
        name: str,
        type: str,
        properties: "RestApiOperationPayloadProperty",
        description: str | None = None,
        is_required: bool = False,
        default_value: Any | None = None,
        schema: str | None = None,
    ):
        """Initialize the RestApiOperationPayloadProperty."""
        self.name = name
        self.type = type
        self.properties = properties
        self.description = description
        self.is_required = is_required
        self.default_value = default_value
        self.schema = schema
