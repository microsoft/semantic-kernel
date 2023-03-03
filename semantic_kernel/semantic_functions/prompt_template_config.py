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
    completion: "PromptTemplateConfig.CompletionConfig" = CompletionConfig()
    default_backends: List[str] = field(default_factory=list)
    input: "PromptTemplateConfig.InputConfig" = InputConfig()

    @staticmethod
    def from_dict(data: dict) -> "PromptTemplateConfig":
        config = PromptTemplateConfig()
        config.schema = data["schema"]
        config.type = data["type"]
        config.description = data["description"]
        config.completion = PromptTemplateConfig.CompletionConfig()
        config.completion.temperature = data["completion"]["temperature"]
        config.completion.top_p = data["completion"]["top_p"]
        config.completion.presence_penalty = data["completion"]["presence_penalty"]
        config.completion.frequency_penalty = data["completion"]["frequency_penalty"]
        config.completion.max_tokens = data["completion"]["max_tokens"]
        config.completion.stop_sequences = data["completion"]["stop_sequences"]
        config.default_backends = data["default_backends"]
        config.input = PromptTemplateConfig.InputConfig()
        config.input.parameters = []
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
    def from_json(json: str) -> "PromptTemplateConfig":
        import json

        return PromptTemplateConfig.from_dict(json.loads(json))

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
