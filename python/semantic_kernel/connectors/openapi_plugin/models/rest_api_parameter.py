# Copyright (c) Microsoft. All rights reserved.

from typing import Any

from semantic_kernel.connectors.openapi_plugin.models.rest_api_expected_response import (
    RestApiExpectedResponse,
)
from semantic_kernel.connectors.openapi_plugin.models.rest_api_parameter_location import (
    RestApiParameterLocation,
)
from semantic_kernel.connectors.openapi_plugin.models.rest_api_parameter_style import (
    RestApiParameterStyle,
)
from semantic_kernel.exceptions.function_exceptions import FunctionExecutionException
from semantic_kernel.utils.feature_stage_decorator import experimental


@experimental
class RestApiParameter:
    """RestApiParameter."""

    def __init__(
        self,
        name: str,
        type: str,
        location: RestApiParameterLocation,
        style: RestApiParameterStyle | None = None,
        alternative_name: str | None = None,
        description: str | None = None,
        is_required: bool = False,
        default_value: Any | None = None,
        schema: str | dict | None = None,
        response: RestApiExpectedResponse | None = None,
    ):
        """Initialize the RestApiParameter."""
        self._name = name
        self._type = type
        self._location = location
        self._style = style
        self._alternative_name = alternative_name
        self._description = description
        self._is_required = is_required
        self._default_value = default_value
        self._schema = schema
        self._response = response
        self._is_frozen = False

    def freeze(self):
        """Make the instance immutable."""
        self._is_frozen = True

    def _throw_if_frozen(self):
        """Raise an exception if the object is frozen."""
        if self._is_frozen:
            raise FunctionExecutionException("This `RestApiParameter` instance is frozen and cannot be modified.")

    @property
    def name(self):
        """Get the name of the parameter."""
        return self._name

    @name.setter
    def name(self, value: str):
        self._throw_if_frozen()
        self._name = value

    @property
    def type(self):
        """Get the type of the parameter."""
        return self._type

    @type.setter
    def type(self, value: str):
        self._throw_if_frozen()
        self._type = value

    @property
    def location(self):
        """Get the location of the parameter."""
        return self._location

    @location.setter
    def location(self, value: RestApiParameterLocation):
        self._throw_if_frozen()
        self._location = value

    @property
    def style(self):
        """Get the style of the parameter."""
        return self._style

    @style.setter
    def style(self, value: RestApiParameterStyle | None):
        self._throw_if_frozen()
        self._style = value

    @property
    def alternative_name(self):
        """Get the alternative name of the parameter."""
        return self._alternative_name

    @alternative_name.setter
    def alternative_name(self, value: str | None):
        self._throw_if_frozen()
        self._alternative_name = value

    @property
    def description(self):
        """Get the description of the parameter."""
        return self._description

    @description.setter
    def description(self, value: str | None):
        self._throw_if_frozen()
        self._description = value

    @property
    def is_required(self):
        """Get whether the parameter is required."""
        return self._is_required

    @is_required.setter
    def is_required(self, value: bool):
        self._throw_if_frozen()
        self._is_required = value

    @property
    def default_value(self):
        """Get the default value of the parameter."""
        return self._default_value

    @default_value.setter
    def default_value(self, value: Any | None):
        self._throw_if_frozen()
        self._default_value = value

    @property
    def schema(self):
        """Get the schema of the parameter."""
        return self._schema

    @schema.setter
    def schema(self, value: str | dict | None):
        self._throw_if_frozen()
        self._schema = value

    @property
    def response(self):
        """Get the response of the parameter."""
        return self._response

    @response.setter
    def response(self, value: Any | None):
        self._throw_if_frozen()
        self._response = value
