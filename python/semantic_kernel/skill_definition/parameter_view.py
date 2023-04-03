# Copyright (c) Microsoft. All rights reserved.

from re import match as re_match

from semantic_kernel.orchestration.sk_function_base import SKFunctionBase


class ParameterView:
    _name: str
    _description: str
    _default_value: str

    def __init__(self, name: str, description: str, default_value: str) -> None:
        if not re_match(SKFunctionBase.FUNCTION_PARAM_NAME_REGEX, name):
            raise ValueError(
                f"Invalid function parameter name: {name}. Function parameter names "
                f"must match the regex: {SKFunctionBase.FUNCTION_PARAM_NAME_REGEX}"
            )

        self._name = name
        self._description = description
        self._default_value = default_value

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str:
        return self._description

    @property
    def default_value(self) -> str:
        return self._default_value

    @name.setter
    def name(self, value: str) -> None:
        if not re_match(SKFunctionBase.FUNCTION_PARAM_NAME_REGEX, value):
            raise ValueError(
                f"Invalid function parameter name: {value}. Function parameter names "
                f"must match the regex: {SKFunctionBase.FUNCTION_PARAM_NAME_REGEX}"
            )
        self._name = value

    @description.setter
    def description(self, value: str) -> None:
        self._description = value

    @default_value.setter
    def default_value(self, value: str) -> None:
        self._default_value = value
