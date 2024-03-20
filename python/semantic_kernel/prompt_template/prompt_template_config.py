# Copyright (c) Microsoft. All rights reserved.
import json
import logging
from typing import Dict, List, Optional, TypeVar, Union

from pydantic import Field, field_validator

from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from semantic_kernel.functions.kernel_parameter_metadata import KernelParameterMetadata
from semantic_kernel.kernel_pydantic import KernelBaseModel
from semantic_kernel.prompt_template.const import KERNEL_TEMPLATE_FORMAT_NAME, TEMPLATE_FORMAT_TYPES
from semantic_kernel.prompt_template.input_variable import InputVariable

PromptExecutionSettingsT = TypeVar("PromptExecutionSettingsT", bound=PromptExecutionSettings)

logger: logging.Logger = logging.getLogger(__name__)


class PromptTemplateConfig(KernelBaseModel):
    name: Optional[str] = ""
    description: Optional[str] = ""
    template: Optional[str] = None
    template_format: TEMPLATE_FORMAT_TYPES = KERNEL_TEMPLATE_FORMAT_NAME
    input_variables: List[InputVariable] = Field(default_factory=list)
    execution_settings: Dict[str, PromptExecutionSettings] = Field(default_factory=dict)

    @field_validator("execution_settings", mode="before")
    @classmethod
    def rewrite_execution_settings(
        cls,
        settings: Optional[
            Union[PromptExecutionSettings, List[PromptExecutionSettings], Dict[str, PromptExecutionSettings]]
        ],
    ) -> Dict[str, PromptExecutionSettings]:
        """Rewrite execution settings to a dictionary."""
        if not settings:
            return {}
        if isinstance(settings, PromptExecutionSettings):
            return {settings.service_id or "default": settings}
        if isinstance(settings, list):
            return {s.service_id or "default": s for s in settings}
        return settings

    def add_execution_settings(self, settings: PromptExecutionSettings, overwrite: bool = True) -> None:
        """Add execution settings to the prompt template."""
        if settings.service_id in self.execution_settings and not overwrite:
            return
        self.execution_settings[settings.service_id or "default"] = settings
        logger.warning("Execution settings already exist and overwrite is set to False")

    def get_kernel_parameter_metadata(self) -> List[KernelParameterMetadata]:
        """Get the kernel parameter metadata for the input variables."""
        return [
            KernelParameterMetadata(
                name=variable.name,
                description=variable.description,
                default_value=variable.default,
                type_=variable.json_schema,  # TODO: update to handle complex JSON schemas
                is_required=variable.is_required,
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
        except Exception as e:
            raise ValueError(
                "Unable to deserialize PromptTemplateConfig from the "
                f"specified JSON string: {json_str} with exception: {e}"
            )

        # Verify that input variable default values are string only
        for variable in config.input_variables:
            if variable.default and not isinstance(variable.default, str):
                raise ValueError(f"Default value for input variable {variable.name} must be a string for {config.name}")

        return config

    @classmethod
    def restore(
        cls,
        name: str,
        description: str,
        template: str,
        template_format: TEMPLATE_FORMAT_TYPES = KERNEL_TEMPLATE_FORMAT_NAME,
        input_variables: List[InputVariable] = [],
        execution_settings: Dict[str, PromptExecutionSettings] = {},
    ) -> "PromptTemplateConfig":
        """Restore a PromptTemplateConfig instance from the specified parameters.

        Args:
            name: The name of the prompt template.
            description: The description of the prompt template.
            template: The template for the prompt.
            input_variables: The input variables for the prompt.
            execution_settings: The execution settings for the prompt.

        Returns:
            A new PromptTemplateConfig instance.
        """
        return cls(
            name=name,
            description=description,
            template=template,
            template_format=template_format,
            input_variables=input_variables,
            execution_settings=execution_settings,
        )
