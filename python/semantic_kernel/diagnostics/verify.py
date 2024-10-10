# Copyright (c) Microsoft. All rights reserved.

import os
import re
from typing import Any, Optional

from semantic_kernel.diagnostics.validation_exception import ValidationException
from semantic_kernel.kernel_exception import KernelException


class Verify:
    @staticmethod
    def not_null(value: Optional[Any], message: str) -> None:
        if value is not None:
            return

        raise ValidationException(ValidationException.ErrorCodes.NullValue, message)

    @staticmethod
    def not_empty(value: Optional[str], message: str) -> None:
        Verify.not_null(value, message)
        if value.strip() != "":  # type: ignore
            return

        raise ValidationException(ValidationException.ErrorCodes.EmptyValue, message)

    @staticmethod
    def valid_skill_name(value: Optional[str]) -> None:
        Verify.not_empty(value, "The skill name cannot be empty")

        SKILL_NAME_REGEX = r"^[0-9A-Za-z_]*$"
        if re.match(SKILL_NAME_REGEX, value):  # type: ignore
            return

        raise KernelException(
            KernelException.ErrorCodes.InvalidFunctionDescription,
            "A skill name can contain only latin letters, digits 0-9, "
            f"and underscores: '{value}' is not a valid skill name.",
        )

    @staticmethod
    def valid_function_name(value: Optional[str]) -> None:
        Verify.not_empty(value, "The function name cannot be empty")

        FUNCTION_NAME_REGEX = r"^[0-9A-Za-z_]*$"
        if re.match(FUNCTION_NAME_REGEX, value):  # type: ignore
            return

        raise KernelException(
            KernelException.ErrorCodes.InvalidFunctionDescription,
            "A function name can contain only latin letters, digits 0-9, "
            f"and underscores: '{value}' is not a valid function name.",
        )

    @staticmethod
    def valid_function_param_name(value: Optional[str]) -> None:
        Verify.not_empty(value, "The function parameter name cannot be empty")

        FUNCTION_PARAM_NAME_REGEX = r"^[0-9A-Za-z_]*$"
        if re.match(FUNCTION_PARAM_NAME_REGEX, value):  # type: ignore
            return

        raise KernelException(
            KernelException.ErrorCodes.InvalidFunctionDescription,
            "A function parameter name can contain only latin letters, "
            f"digits 0-9, and underscores: '{value}' is not a valid "
            f"function parameter name.",
        )

    @staticmethod
    def starts_with(text: str, prefix: Optional[str], message: str) -> None:
        Verify.not_empty(text, "The text to verify cannot be empty")
        Verify.not_null(prefix, "The prefix to verify cannot be null")

        if text.startswith(prefix):  # type: ignore
            return

        raise ValidationException(ValidationException.ErrorCodes.MissingPrefix, message)

    @staticmethod
    def directory_exists(path: str):
        Verify.not_empty(path, "The path to verify cannot be empty")

        if os.path.isdir(path):
            return

        raise ValidationException(
            ValidationException.ErrorCodes.DirectoryNotFound,
            f"Directory not found: '{path}'",
        )

    @staticmethod
    def parameters_unique(parameters: list):  # TODO: ParameterView
        name_set = set()

        for parameter in parameters:
            if parameter.name in name_set:
                raise KernelException(
                    KernelException.ErrorCodes.InvalidFunctionDescription,
                    "The function has two or more parameters "
                    f"with the same name '{parameter.name}'",
                )

            Verify.not_empty(parameter.name, "The function parameter name is empty")
            name_set.add(parameter.name.lower())
