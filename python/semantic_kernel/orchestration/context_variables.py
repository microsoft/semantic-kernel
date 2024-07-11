# Copyright (c) Microsoft. All rights reserved.
from typing import Dict, Optional, Tuple

import pydantic as pdt

from semantic_kernel.sk_pydantic import SKBaseModel


class ContextVariables(SKBaseModel):
    variables: Dict[str, str] = pdt.Field(default_factory=dict)
    _main_key: str = pdt.PrivateAttr()

    def __init__(
        self, content: Optional[str] = None, variables: Dict[str, str] = None
    ) -> None:
        """
        Initialize the ContextVariables instance with an optional content string.

        :param content: The content string to be stored as the main variable,
            defaults to an empty string.
        """
        main_key: str = "input"
        variables: Dict[str, str] = variables or {}
        if content is not None:
            variables[main_key] = content
        elif main_key not in variables:
            variables[main_key] = ""
        super().__init__(variables=variables)
        self._main_key = main_key

    @property
    def input(self) -> str:
        return self.variables[self._main_key]

    def update(self, content: str) -> "ContextVariables":
        self.variables[self._main_key] = content
        return self

    def merge_or_overwrite(
        self, new_vars: "ContextVariables", overwrite: bool = False
    ) -> "ContextVariables":
        if overwrite:
            self.variables = new_vars.variables
        else:
            self.variables.update(new_vars.variables)
        return self

    def set(self, name: str, value: str) -> "ContextVariables":
        if not name:
            raise ValueError("The variable name cannot be `None` or empty")
        name = name.lower()

        if value is not None:
            self.variables[name] = value
        else:
            self.variables.pop(name, None)

        return self

    def get(self, name: str) -> Tuple[bool, str]:
        name = name.lower()
        if name in self.variables:
            return True, self.variables[name]

        return False, ""

    def __getitem__(self, name: str) -> str:
        name = name.lower()
        return self.variables[name]

    def __setitem__(self, name: str, value: str) -> None:
        if not name:
            raise ValueError("The variable name cannot be `None` or empty")
        name = name.lower()
        self.variables[name] = value

    def contains_key(self, name: str) -> bool:
        name = name.lower()
        return name in self.variables

    def __str__(self) -> str:
        return self.variables[self._main_key]

    def clone(self) -> "ContextVariables":
        main_content = self.variables.get(self._main_key, "")
        new_vars = ContextVariables(main_content)
        new_vars.variables = self.variables.copy()
        return new_vars
