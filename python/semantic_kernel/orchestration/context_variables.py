# Copyright (c) Microsoft. All rights reserved.
from typing import Dict, Optional

import pydantic as pdt

from semantic_kernel.sk_pydantic import SKBaseModel


class ContextVariables(SKBaseModel):
    """Class for the context variables, maintains a dict with keys and values for the variables.
    The keys are all converted to lower case, both in setting and in getting.

    Uses `input` as the main key for the content string, that value can be extracted by using:
    - the `input` property
    - context_variables_instance['input']
    - context_variables_instance.get('input')
    - str(context_variables_instance)

    The value for that is always a string, and is set to "" if not provided and can be updated by using:
    - the `update` method
    - context_variables_instance['input'] = "new value"
    - context_variables_instance.set("input", "new value")
    """

    variables: Dict[str, str] = pdt.Field(default_factory=dict)
    _main_key: str = pdt.PrivateAttr(default="input")

    def __init__(
        self, content: Optional[str] = None, variables: Optional[Dict[str, str]] = {}
    ) -> None:
        """
        Initialize the ContextVariables instance with an optional content string.

        The value of the content variable has precedence over the value of the 'input' key in the variables dictionary.
        If the 'input' key is not in the variables dictionary.

        :param content: The content string to be stored as the main variable,
            defaults to an empty string.
        :param variables: The variables dictionary, defaults to an empty dictionary.
        """
        super().__init__(variables=variables)
        if self._main_key not in self.variables or content is not None:
            self.variables[self._main_key] = content if content else ""

    @property
    def input(self) -> str:
        """Returns the 'input' field."""
        return self.variables[self._main_key]

    def update(self, content: str) -> "ContextVariables":
        """Updates the 'input' field with the given content."""
        self.variables[self._main_key] = content
        return self

    def merge_or_overwrite(
        self, new_vars: "ContextVariables", overwrite: bool = False
    ) -> "ContextVariables":
        """Merge or overwrite the current variables with the new variables.

        Arguments:
            new_vars {ContextVariables} -- The new variables.
            overwrite {bool} -- If True, overwrite the current variables with the new variables,
                otherwise merge the new variables with the current variables.
                Defaults to False.

        Returns:
            ContextVariables -- The current instance with updated variables.
        """
        if overwrite:
            self.variables = new_vars.variables
            return self
        self.variables.update(new_vars.variables)
        return self

    def set(self, name: str, value: Optional[str]) -> "ContextVariables":
        """Set a variable value by name.

        If the value is None, the variable is removed.

        Returns:
            ContextVariables -- The current instance with updated variables.
        """
        if not name:
            raise ValueError("The variable name cannot be `None` or empty")
        if value is not None:
            self.variables[name.lower()] = value
            return self
        self.variables.pop(name.lower(), None)
        return self

    def get(self, name: str, value: Optional[str] = None) -> Optional[str]:
        """Get a variable value by name, or return a default value if not found.

        Arguments:
            name {str} -- The variable name.
            value {Optional[str]} -- The value to return if the variable is not found.
                Defaults to None.

        Returns:
            Optional[str] -- The variable value, or the default value if not found.
        """
        name = name.lower()
        if name in self.variables:
            return self.variables[name]
        return value

    def __getitem__(self, name: str) -> str:
        return self.variables[name.lower()]

    def __setitem__(self, name: str, value: str) -> None:
        if not name:
            raise ValueError("The variable name cannot be `None` or empty")
        self.variables[name.lower()] = value

    def __delitem__(self, name: str) -> None:
        del self.variables[name.lower()]

    def __contains__(self, name: str) -> bool:
        return name.lower() in self.variables

    def __str__(self) -> str:
        return self.variables[self._main_key]

    def clone(self) -> "ContextVariables":
        """Create a clone of this instance.

        If the `input` key is empty, the value is set to "".
        """
        return ContextVariables(variables=self.variables.copy())
