# Copyright (c) Microsoft. All rights reserved.

from typing import Any

from semantic_kernel.connectors.openapi_plugin.models.rest_api_operation_expected_response import (
    RestApiOperationExpectedResponse,
)
from semantic_kernel.connectors.openapi_plugin.models.rest_api_operation_parameter_location import (
    RestApiOperationParameterLocation,
)
from semantic_kernel.connectors.openapi_plugin.models.rest_api_operation_parameter_style import (
    RestApiOperationParameterStyle,
)
from semantic_kernel.utils.experimental_decorator import experimental_class


@experimental_class
class RestApiOperationParameter:
    def __init__(
        self,
        name: str,
        type: str,
        location: RestApiOperationParameterLocation,
        style: RestApiOperationParameterStyle | None = None,
        alternative_name: str | None = None,
        description: str | None = None,
        is_required: bool = False,
        default_value: Any | None = None,
        schema: str | None = None,
        response: RestApiOperationExpectedResponse | None = None,
    ):
        """Initialize the RestApiOperationParameter."""
        self.name = name
        self.type = type
        self.location = location
        self.style = style
        self.alternative_name = alternative_name
        self.description = description
        self.is_required = is_required
        self.default_value = default_value
        self.schema = schema
        self.response = response
