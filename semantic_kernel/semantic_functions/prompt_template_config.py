# Copyright (c) Microsoft. All rights reserved.

from dataclasses import dataclass, field
from typing import List


@dataclass
class PromptTemplateConfig:
    @dataclass
    class CompletionConfig:
        temperature: float = 0.0
        top_p: float = 1.0
        presence_penalty: float = 0.0
        frequency_penalty: float = 0.0
        max_tokens: int = 256
        stop_sequences: List[str] = field(default_factory=list)

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
    default_backends: List[str] = field(default_factory=list)
    input: "PromptTemplateConfig.InputConfig" = field(default_factory=InputConfig)

    @staticmethod
    def from_dict(data: dict) -> "PromptTemplateConfig":
        config = PromptTemplateConfig()
        config.schema = data.get("schema")
        config.type = data.get("type)")
        config.description = data.get("description")

        # Some skills may not have all completion parameters defined
        config.completion = PromptTemplateConfig.CompletionConfig()
        completition_dict = data["completion"]
        config.completion.temperature = completition_dict.get("temperature")
        config.completion.top_p = completition_dict.get("top_p")
        config.completion.presence_penalty = completition_dict.get("presence_penalty")
        config.completion.frequency_penalty = completition_dict.get("frequency_penalty")
        config.completion.max_tokens = completition_dict.get("max_tokens")
        config.completion.stop_sequences = completition_dict.get("stop_sequences")
        config.default_backends = data.get("default_backends")

        # Some skills may not have input parameters defined
        config.input = PromptTemplateConfig.InputConfig()
        config.input.parameters = []
        if data.get("input") is not None:
            for parameter in data["input"]["parameters"]:
                config.input.parameters.append(
                    PromptTemplateConfig.InputParameter(
                        parameter["name"],
                        parameter["description"],
                        parameter["default_value"],
                    )
                )
        return config

    @staticmethod
    def from_json(json_str: str) -> "PromptTemplateConfig":
        import json

        return PromptTemplateConfig.from_dict(json.loads(json_str))

    @staticmethod
    def from_completion_parameters(
        temperature: float = 0.0,
        top_p: float = 1.0,
        presence_penalty: float = 0.0,
        frequency_penalty: float = 0.0,
        max_tokens: int = 256,
        stop_sequences: List[str] = [],
    ) -> "PromptTemplateConfig":
        config = PromptTemplateConfig()
        config.completion.temperature = temperature
        config.completion.top_p = top_p
        config.completion.presence_penalty = presence_penalty
        config.completion.frequency_penalty = frequency_penalty
        config.completion.max_tokens = max_tokens
        config.completion.stop_sequences = stop_sequences
        return config
