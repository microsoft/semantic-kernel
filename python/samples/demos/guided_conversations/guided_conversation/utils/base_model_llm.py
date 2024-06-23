# Copyright (c) Microsoft. All rights reserved.

import ast
from types import NoneType
from typing import get_args

from pydantic import BaseModel, ValidationInfo, field_validator


class BaseModelLLM(BaseModel):
    """A Pydantic base class for use when an LLM is completing fields. Provides a custom field validator and Pydantic Config."""

    @field_validator("*", mode="before")
    def parse_literal_eval(cls, value: str, info: ValidationInfo):  # noqa: N805
        """An LLM will always result in a string (e.g. '["x", "y"]'), so we need to parse it to the correct type"""
        # Get the type hints for the field
        annotation = cls.model_fields[info.field_name].annotation
        typehints = get_args(annotation)
        if len(typehints) == 0:
            typehints = [annotation]

        # Usually fields that are NoneType have another type hint as well, e.g. str | None
        # if the LLM returns "None" and the field allows NoneType, we should return None
        # without this code, the next if-block would leave the string "None" as the value
        if (NoneType in typehints) and (value == "None"):
            return None

        # If the field allows strings, we don't parse it - otherwise a validation error might be raised
        # e.g. phone_number = "1234567890" should not be converted to an int if the type hint is str
        if str in typehints:
            return value
        try:
            evaluated_value = ast.literal_eval(value)
            return evaluated_value
        except Exception:
            return value

    class Config:
        # Ensure that validation happens every time a field is updated, not just when the artifact is created
        validate_assignment = True
        # Do not allow extra fields to be added to the artifact
        extra = "forbid"
