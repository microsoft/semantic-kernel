# Copyright (c) Microsoft. All rights reserved.
import json
from typing import Generic, List, TypeVar

from pydantic import Field

from semantic_kernel.connectors.ai.ai_request_settings import AIRequestSettings
from semantic_kernel.sk_pydantic import SKBaseModel
from semantic_kernel.plugin_definition.parameter_view import ParameterView

AIRequestSettingsT = TypeVar("AIRequestSettingsT", bound=AIRequestSettings)

class PromptTemplateConfig(SKBaseModel, Generic[AIRequestSettingsT]):
    schema_: int = Field(default=1, alias="schema")
    type: str = "completion"
    description: str = ""
    execution_settings: AIRequestSettingsT = Field(default_factory=AIRequestSettings)
    default_services: List[str] = Field(default_factory=list)
    parameters: List[ParameterView] = Field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict) -> "PromptTemplateConfig":
        config = {key: value for key, value in data.items() if key in ["schema", "type", "description", "default_services"]}
        config["parameters"] = []

        execution_settings_dict = data.get("execution_settings", {}).get("default", {})
        concrete_type = cls.model_fields["execution_settings"].annotation
        if isinstance(concrete_type, TypeVar):
            concrete_type = AIRequestSettings
        config["execution_settings"] = concrete_type(**execution_settings_dict)

        if "input_variables" in data:
            for parameter in data["input_variables"]:
                name = parameter.get("name", "")
                description = parameter.get("description", "")
                defaultValue = parameter.get("default", "")
                type_ = parameter.get("type")
                required = parameter.get("required", False)

                config["parameters"].append(
                    ParameterView(
                        name,
                        description,
                        defaultValue,
                        type_,
                        required,
                    )
                )

        return cls(**config)

    @classmethod
    def from_json(cls, json_str: str) -> "PromptTemplateConfig":
        return cls.from_dict(json.loads(json_str))

    @classmethod
    def from_completion_parameters(cls, **kwargs) -> "PromptTemplateConfig":
        concrete_class = cls.model_fields["execution_settings"].annotation
        if isinstance(concrete_class, TypeVar):
            concrete_class = AIRequestSettings
        return PromptTemplateConfig(execution_settings=concrete_class(**kwargs))
