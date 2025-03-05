# Copyright (c) Microsoft. All rights reserved.

from typing import Any

from semantic_kernel.exceptions.function_exceptions import FunctionExecutionException
from semantic_kernel.utils.experimental_decorator import experimental_class


@experimental_class
class RestApiPayloadProperty:
    """RestApiPayloadProperty."""

    def __init__(
        self,
        name: str,
        type: str,
        properties: list["RestApiPayloadProperty"] | None = None,
        description: str | None = None,
        is_required: bool = False,
        default_value: Any | None = None,
        schema: str | None = None,
    ):
        """Initialize the RestApiPayloadProperty."""
        self._name = name
        self._type = type
        self._properties = properties or []
        self._description = description
        self._is_required = is_required
        self._default_value = default_value
        self._schema = schema
        self._is_frozen = False

    def freeze(self):
        """Make the instance immutable, and freeze nested properties."""
        self._is_frozen = True
        for prop in self._properties:
            prop.freeze()

    def _throw_if_frozen(self):
        """Raise an exception if the object is frozen."""
        if self._is_frozen:
            raise FunctionExecutionException("This instance is frozen and cannot be modified.")

    @property
    def name(self):
        """Get the name of the property."""
        return self._name

    @name.setter
    def name(self, value: str):
        self._throw_if_frozen()
        self._name = value

    @property
    def type(self):
        """Get the type of the property."""
        return self._type

    @type.setter
    def type(self, value: str):
        self._throw_if_frozen()
        self._type = value

    @property
    def properties(self):
        """Get the properties of the property."""
        return self._properties

    @properties.setter
    def properties(self, value: list["RestApiPayloadProperty"]):
        self._throw_if_frozen()
        self._properties = value

    @property
    def description(self):
        """Get the description of the property."""
        return self._description

    @description.setter
    def description(self, value: str | None):
        self._throw_if_frozen()
        self._description = value

    @property
    def is_required(self):
        """Get whether the property is required."""
        return self._is_required

    @is_required.setter
    def is_required(self, value: bool):
        self._throw_if_frozen()
        self._is_required = value

    @property
    def default_value(self):
        """Get the default value of the property."""
        return self._default_value

    @default_value.setter
    def default_value(self, value: Any | None):
        self._throw_if_frozen()
        self._default_value = value

    @property
    def schema(self):
        """Get the schema of the property."""
        return self._schema

    @schema.setter
    def schema(self, value: str | None):
        self._throw_if_frozen()
        self._schema = value
