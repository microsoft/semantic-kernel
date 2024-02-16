# Copyright (c) Microsoft. All rights reserved.
import json
import logging
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
    execution_settings: Optional[Dict[str, PromptExecutionSettings]] = Field(
        default_factory=dict, alias="execution_settings"
    )

    def __init__(self, **data) -> None:
        """Create a new PromptTemplateConfig instance.
        
        Args:
            **data: The data to initialize the instance with.
        """
        super().__init__(**data)

    def add_execution_settings(self, settings: PromptExecutionSettings) -> None:
        """Add execution settings to the prompt template."""
        self.execution_settings = settings

    def get_kernel_parameter_metadata(self) -> List[KernelParameterMetadata]:
        """Get the kernel parameter metadata for the input variables."""
        return [
            KernelParameterMetadata(
                name=variable.name,
                description=variable.description,
                default_value=variable.default,
                type_=variable.json_schema,  # TODO: update to handle complex JSON schemas
                required=variable.is_required,
                expose=True,
            )
            for variable in self.input_variables
        ]

    @classmethod
    def from_json(cls, json_str: str) -> "PromptTemplateConfig":
        """Create a PromptTemplateConfig instance from a JSON string."""
        if not json_str:
            raise ValueError("json_str is empty")

        try:
            parsed_json = json.loads(json_str)
            config = PromptTemplateConfig(**parsed_json)
        except:
            raise ValueError(f"Unable to deserialize PromptTemplateConfig from the specified JSON string: {json_str}")

        # Verify that input variable default values are string only
        for variable in config.input_variables:
            if variable.default and not isinstance(variable.default, str):
                raise ValueError(f"Default value for input variable {variable.name} must be a string for {config.name}")
            
        return config
