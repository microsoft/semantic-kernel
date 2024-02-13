# Copyright (c) Microsoft. All rights reserved.
import logging
import json
from typing import Dict, Generic, List, Optional, TypeVar

from pydantic import Field

from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from semantic_kernel.functions.kernel_parameter_metadata import KernelParameterMetadata
from semantic_kernel.kernel_pydantic import KernelBaseModel
from semantic_kernel.prompt_template.input_variable import InputVariable

PromptExecutionSettingsT = TypeVar("PromptExecutionSettingsT", bound=PromptExecutionSettings)

logger: logging.Logger = logging.getLogger(__name__)


class PromptTemplateConfig(KernelBaseModel, Generic[PromptExecutionSettingsT]):
    name: Optional[str] = Field(default="", alias="name")
    description: Optional[str] = Field(default="", alias="description")
    template: Optional[str] = Field(None, alias="template")
    template_format: Optional[str] = Field(default="semantic-kernel", alias="template_format")
    input_variables: Optional[List[InputVariable]] = Field(default_factory=list, alias="input_variables")
    execution_settings: Optional[Dict[str, PromptExecutionSettings]] = Field(default_factory=dict, alias="execution_settings")

    def __init__(self, **data) -> None:
        super().__init__(**data)

    def add_execution_settings(self, settings: PromptExecutionSettings) -> None:
        self.execution_settings = settings

    def get_kernel_parameter_metadata(self) -> List[KernelParameterMetadata]:
        return [
            KernelParameterMetadata(
                name=variable.name,
                description=variable.description,
                default_value=variable.default,
                type_=variable.json_schema,  # TODO: update to handle complex JSON schemas
                required=variable.is_required,
            )
            for variable in self.input_variables
        ]

    @classmethod
    def from_json(cls, json_str: str) -> "PromptTemplateConfig":
        if not json_str:
            raise ValueError("json_str is empty")
        
        parsed_json = json.loads(json_str)

        return PromptTemplateConfig(**parsed_json)