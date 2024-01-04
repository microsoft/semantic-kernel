# Copyright (c) Microsoft. All rights reserved.
import json
from typing import Generic, List, TypeVar

from pydantic import Field

from semantic_kernel.connectors.ai.ai_request_settings import AIRequestSettings
from semantic_kernel.sk_pydantic import SKBaseModel
from semantic_kernel.skill_definition.parameter_view import ParameterView

AIRequestSettingsT = TypeVar("AIRequestSettingsT", bound=AIRequestSettings)


class PromptTemplateConfig(SKBaseModel, Generic[AIRequestSettingsT]):
    schema_: int = Field(default=1, alias="schema")
    type: str = "completion"
    description: str = ""
    completion: AIRequestSettingsT = Field(default_factory=AIRequestSettings)
    default_services: List[str] = Field(default_factory=list)
    parameters: List[ParameterView] = Field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict) -> "PromptTemplateConfig":
        config = {
            key: value
            for key, value in data.items()
            if key in ["schema", "type", "description"]
        }
        config["parameters"] = []

        completion_dict = data["completion"]
        service_id = completion_dict.pop("service_id", None)
        concrete_type = cls.model_fields["completion"].annotation
        if isinstance(concrete_type, TypeVar):
            concrete_type = AIRequestSettings
        config["completion"] = concrete_type(
            service_id=service_id, extension_data=completion_dict
        )

        # Some skills may not have input parameters defined
        if data.get("parameters") is not None:
            for parameter in data["parameters"]:
                if "name" in parameter:
                    name = parameter["name"]
                else:
                    raise Exception(
                        f"The input parameter doesn't have a name (function: {config['description']})"
                    )

                if "description" in parameter:
                    description = parameter["description"]
                else:
                    raise Exception(
                        f"Input parameter '{name}' doesn't have a description (function: {config['description']})"
                    )
                if "defaultValue" in parameter:
                    defaultValue = parameter["defaultValue"]
                else:
                    raise Exception(
                        f"Input parameter '{name}' doesn't have a default value (function: {config['description']})"
                    )
                type_ = parameter.get("type")
                required = parameter.get("required")

                config["parameters"].append(
                    ParameterView(
                        name,
                        description,
                        defaultValue,
                        type_,
                        required,
                    )
                )
        if "default_services" in data:
            config["default_services"] = data["default_services"]
        return cls(**config)

    @classmethod
    def from_json(cls, json_str: str) -> "PromptTemplateConfig":
        return cls.from_dict(json.loads(json_str))

    @classmethod
    def from_completion_parameters(cls, **kwargs) -> "PromptTemplateConfig":
        concrete_class = cls.model_fields["completion"].annotation
        if isinstance(concrete_class, TypeVar):
            concrete_class = AIRequestSettings
        return PromptTemplateConfig(completion=concrete_class(extension_data=kwargs))
