# Copyright (c) Microsoft. All rights reserved.
import json
from typing import Generic, List, TypeVar

from pydantic import Field

from semantic_kernel.connectors.ai.ai_request_settings import AIRequestSettings
from semantic_kernel.kernel_pydantic import KernelBaseModel
from semantic_kernel.plugin_definition.parameter_view import ParameterView

AIRequestSettingsT = TypeVar("AIRequestSettingsT", bound=AIRequestSettings)


class PromptTemplateConfig(KernelBaseModel, Generic[AIRequestSettingsT]):
    schema_: int = Field(default=1, alias="schema")
    type: str = "completion"
    description: str = ""
    execution_settings: AIRequestSettingsT = Field(default_factory=AIRequestSettings)  # todo: this should be a dict
    default_services: List[str] = Field(default_factory=list)
    parameters: List[ParameterView] = Field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict) -> "PromptTemplateConfig":
        config = {
            key: value for key, value in data.items() if key in ["schema", "type", "description", "default_services"]
        }
        config["parameters"] = []

        config = cls._process_execution_settings(config, data)

        if "input_variables" in data:
            for parameter in data["input_variables"]:
                name = parameter.get("name", "")
                description = parameter.get("description", "")
                defaultValue = parameter.get("default", "")
                type_ = parameter.get("type")
                required = parameter.get("required", False)

                config["parameters"].append(
                    ParameterView(
                        name=name,
                        description=description,
                        default_value=defaultValue,
                        type_=type_,
                        required=required,
                    )
                )

        return cls(**config)

    @classmethod
    def from_json(cls, json_str: str) -> "PromptTemplateConfig":
        return cls.from_dict(json.loads(json_str))

    @classmethod
    def from_execution_settings(cls, **kwargs) -> "PromptTemplateConfig":
        concrete_class = cls.model_fields["execution_settings"].annotation
        if isinstance(concrete_class, TypeVar):
            concrete_class = AIRequestSettings
        return PromptTemplateConfig(execution_settings=concrete_class(extension_data=kwargs))

    @classmethod
    def _process_execution_settings(cls, config: dict, data: dict) -> dict:
        exec_settings = data.get("execution_settings", {})

        for service_id, settings in exec_settings.items():
            # Copy settings to avoid modifying the original data
            settings = settings.copy()

            # Extract and remove 'service_id' if it exists
            # service_id = settings.pop("service_id", service_id)

            # Determine the concrete type
            concrete_type = cls.model_fields["execution_settings"].annotation
            if isinstance(concrete_type, TypeVar):
                concrete_type = AIRequestSettings

            # Initialize the concrete type with the service_id and remaining settings
            config["execution_settings"] = concrete_type(service_id=service_id, extension_data=settings)

        return config
