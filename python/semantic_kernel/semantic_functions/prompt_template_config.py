# Copyright (c) Microsoft. All rights reserved.

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class PromptTemplateConfig:
    @dataclass
    class CompletionConfig:
        temperature: float = 0.0
        top_p: float = 1.0
        presence_penalty: float = 0.0
        frequency_penalty: float = 0.0
        max_tokens: int = 256
        number_of_responses: int = 1
        stop_sequences: List[str] = field(default_factory=list)
        token_selection_biases: Dict[int, int] = field(default_factory=dict)
        chat_system_prompt: str = None

    @dataclass
    class InputParameter:
        name: str = ""
        description: str = ""
        default_value: str = ""

    @dataclass
    class InputConfig:
        parameters: List["PromptTemplateConfig.InputParameter"] = field(
            default_factory=list
        )

    schema: int = 1
    type: str = "completion"
    description: str = ""
    completion: "PromptTemplateConfig.CompletionConfig" = field(
        default_factory=CompletionConfig
    )
    default_services: List[str] = field(default_factory=list)
    input: "PromptTemplateConfig.InputConfig" = field(default_factory=InputConfig)

    @staticmethod
    def from_dict(data: dict) -> "PromptTemplateConfig":
        config = PromptTemplateConfig()
        config.schema = data.get("schema")
        config.type = data.get("type")
        config.description = data.get("description")

        # Some skills may not have all completion parameters defined
        config.completion = PromptTemplateConfig.CompletionConfig()
        completion_dict = data["completion"]
        config.completion.temperature = completion_dict.get("temperature")
        config.completion.top_p = completion_dict.get("top_p")
        config.completion.presence_penalty = completion_dict.get("presence_penalty")
        config.completion.frequency_penalty = completion_dict.get("frequency_penalty")
        config.completion.max_tokens = completion_dict.get("max_tokens")
        config.completion.number_of_responses = completion_dict.get(
            "number_of_responses"
        )
        config.completion.stop_sequences = completion_dict.get("stop_sequences", [])
        config.completion.token_selection_biases = completion_dict.get(
            "token_selection_biases", {}
        )
        config.completion.chat_system_prompt = completion_dict.get("chat_system_prompt")

        config.default_services = data.get("default_services", [])

        # Some skills may not have input parameters defined
        config.input = PromptTemplateConfig.InputConfig()
        config.input.parameters = []
        if data.get("input") is not None:
            for parameter in data["input"]["parameters"]:
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

                config.input.parameters.append(
                    PromptTemplateConfig.InputParameter(
                        name,
                        description,
                        defaultValue,
                    )
                )
        return config

    @staticmethod
    def from_json(json_str: str) -> "PromptTemplateConfig":
        import json

        def keystoint(d):
            return {int(k) if k.isdigit() else k: v for k, v in d.items()}

        return PromptTemplateConfig.from_dict(
            json.loads(json_str, object_hook=keystoint)
        )

    @staticmethod
    def from_completion_parameters(
        temperature: float = 0.0,
        top_p: float = 1.0,
        presence_penalty: float = 0.0,
        frequency_penalty: float = 0.0,
        max_tokens: int = 256,
        number_of_responses: int = 1,
        stop_sequences: List[str] = [],
        token_selection_biases: Dict[int, int] = {},
        chat_system_prompt: str = None,
    ) -> "PromptTemplateConfig":
        config = PromptTemplateConfig()
        config.completion.temperature = temperature
        config.completion.top_p = top_p
        config.completion.presence_penalty = presence_penalty
        config.completion.frequency_penalty = frequency_penalty
        config.completion.max_tokens = max_tokens
        config.completion.number_of_responses = number_of_responses
        config.completion.stop_sequences = stop_sequences
        config.completion.token_selection_biases = token_selection_biases
        config.completion.chat_system_prompt = chat_system_prompt
        return config
