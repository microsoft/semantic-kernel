from abc import abstractmethod

from semantic_kernel.sk_pydantic import SKBaseModel
from semantic_kernel.skill_definition.parameter_view import ParameterView as Parameter

from typing import List

class SKFunctionNew(SKBaseModel):
    name: str
    description: str
    input_variables: list[Parameter]
    output_variables: list[Parameter]
    plugin_name: str = ""

    @abstractmethod
    async def run_async(self, variables, *args, **kwargs) -> dict:
        pass

    @property
    def output_variable_name(self) -> str:
        if self.output_variables is None or len(self.output_variables) == 0:
            return "result"
        return self.output_variables[0].name

    @property
    def Parameters(self) -> dict:
        return self.input_variables

    @property
    def fully_qualified_name(self) -> str:
        return f"{self.plugin_name}_{self.name}"