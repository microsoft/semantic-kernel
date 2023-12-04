# Copyright (c) Microsoft. All rights reserved.

from typing import Generic, List, TypeVar

from pydantic import Field

from semantic_kernel.connectors.ai.ai_request_settings import AIRequestSettings
from semantic_kernel.sk_pydantic import SKBaseModel
from semantic_kernel.skill_definition.parameter_view import ParameterView

AIRequestSettingsT = TypeVar("AIRequestSettingsT", bound=AIRequestSettings)


# class InputConfig(SKBaseModel):
#     parameters: List[ParameterView] = Field(
#         default_factory=list
#     )


class PromptConfig(SKBaseModel, Generic[AIRequestSettingsT]):
    schema_: int = Field(default=1, alias="schema")
    type: str = "completion"
    description: str = ""
    completion: AIRequestSettingsT = Field(default_factory=AIRequestSettings)
    default_services: List[str] = Field(default_factory=list)
    parameters: List[ParameterView] = Field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict) -> "PromptConfig":
        config = cls()
        keys = ["schema", "type", "description"]
        for key in keys:
            if key in data:
                setattr(config, key, data[key])

        # Some skills may not have all completion parameters defined
        completion_dict = data["completion"]
        if "service_id" in completion_dict:
            service_id = completion_dict.pop("service_id")
            config.completion = AIRequestSettings(
                service_id=service_id, extension_data=completion_dict
            )

        # Some skills may not have input parameters defined
        if data.get("parameters") is not None:
            for parameter in data["parameters"]:
                if "name" in parameter:
                    name = parameter["name"]
                else:
                    raise Exception(
                        f"The input parameter doesn't have a name (function: {config.description})"
                    )

                if "description" in parameter:
                    description = parameter["description"]
                else:
                    raise Exception(
                        f"Input parameter '{name}' doesn't have a description (function: {config.description})"
                    )
                if "defaultValue" in parameter:
                    defaultValue = parameter["defaultValue"]
                else:
                    raise Exception(
                        f"Input parameter '{name}' doesn't have a default value (function: {config.description})"
                    )
                type_ = parameter.get("type")
                required = parameter.get("required")

                config.parameters.append(
                    ParameterView(
                        name,
                        description,
                        defaultValue,
                        type_,
                        required,
                    )
                )
        return config

    @staticmethod
    def from_json(json_str: str) -> "PromptConfig":
        import json

        def keystoint(d):
            return {int(k) if k.isdigit() else k: v for k, v in d.items()}

        return PromptConfig.from_dict(json.loads(json_str, object_hook=keystoint))

    # @staticmethod
    # def from_completion_parameters(
    #     temperature: float = 0.0,
    #     top_p: float = 1.0,
    #     presence_penalty: float = 0.0,
    #     frequency_penalty: float = 0.0,
    #     max_tokens: int = 256,
    #     number_of_responses: int = 1,
    #     stop_sequences: List[str] = [],
    #     token_selection_biases: Dict[int, int] = {},
    #     chat_system_prompt: str = None,
    #     function_call: Optional[str] = None,
    # ) -> "PromptTemplateConfig":
    #     config = PromptTemplateConfig()
    #     config.completion.temperature = temperature
    #     config.completion.top_p = top_p
    #     config.completion.presence_penalty = presence_penalty
    #     config.completion.frequency_penalty = frequency_penalty
    #     config.completion.max_tokens = max_tokens
    #     config.completion.number_of_responses = number_of_responses
    #     config.completion.stop_sequences = stop_sequences
    #     config.completion.token_selection_biases = token_selection_biases
    #     config.completion.chat_system_prompt = chat_system_prompt
    #     config.completion.function_call = function_call
    #     return config
