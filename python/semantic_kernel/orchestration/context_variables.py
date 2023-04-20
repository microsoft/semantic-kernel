# Copyright (c) Microsoft. All rights reserved.


from typing import Dict, Tuple


class ContextVariables:
    def __init__(self, content: str = "", variables: Dict[str, str] = None) -> None:
        """
        Initialize the ContextVariables instance with an optional content string.

        :param content: The content string to be stored as the main variable,
            defaults to an empty string.
        """
        self._variables: Dict[str, str] = variables or {}
        self._main_key: str = "input"
        self._variables[self._main_key] = content

    @property
    def input(self) -> str:
        return self._variables[self._main_key]

    def update(self, content: str) -> "ContextVariables":
        self._variables[self._main_key] = content
        return self

    def merge_or_overwrite(
        self, new_vars: "ContextVariables", overwrite: bool = False
    ) -> "ContextVariables":
        if overwrite:
            self._variables = new_vars._variables
        else:
            self._variables.update(new_vars._variables)
        return self

    def set(self, name: str, value: str) -> "ContextVariables":
        if not name:
            raise ValueError("The variable name cannot be `None` or empty")
        name = name.lower()

        if value is not None:
            self._variables[name] = value
        else:
            self._variables.pop(name, None)

        return self

    def get(self, name: str) -> Tuple[bool, str]:
        name = name.lower()
        if name in self._variables:
            return True, self._variables[name]

        return False, ""

    def __getitem__(self, name: str) -> str:
        name = name.lower()
        return self._variables[name]

    def __setitem__(self, name: str, value: str) -> None:
        if not name:
            raise ValueError("The variable name cannot be `None` or empty")
        name = name.lower()
        self._variables[name] = value

    def contains_key(self, name: str) -> bool:
        name = name.lower()
        return name in self._variables

    def __str__(self) -> str:
        return self._variables[self._main_key]

    def clone(self) -> "ContextVariables":
        main_content = self._variables.get(self._main_key, "")
        new_vars = ContextVariables(main_content)
        new_vars._variables = self._variables.copy()
        return new_vars
