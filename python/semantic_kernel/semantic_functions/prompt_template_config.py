# Copyright (c) Microsoft. All rights reserved.
import json
from typing import Generic, List, TypeVar

from pydantic import Field

from semantic_kernel.connectors.ai.ai_request_settings import AIRequestSettings
from semantic_kernel.sk_pydantic import SKBaseModel
from semantic_kernel.skill_definition.parameter_view import ParameterView

AIRequestSettingsT = TypeVar("AIRequestSettingsT", bound=AIRequestSettings)


<<<<<<< HEAD
class PromptTemplateConfig(SKBaseModel, Generic[AIRequestSettingsT]):
    schema_: int = Field(default=1, alias="schema")
    type: str = "completion"
    description: str = ""
    completion: AIRequestSettingsT = Field(default_factory=AIRequestSettings)
    default_services: List[str] = Field(default_factory=list)
    parameters: List[ParameterView] = Field(default_factory=list)
=======
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
        # the function_call should be 'auto' or the name of a specific function in order to leverage function calling
        # when not using auto, the format is 'SkillName-FunctionName', e.g. 'Weather-GetWeather'
        function_call: Optional[str] = None

    @dataclass
    class InputParameter:
        name: str = ""
        description: str = ""
        default_value: str = ""
        type_: str = "string"
        required: bool = True

    @dataclass
    class InputConfig:
        parameters: List["PromptTemplateConfig.InputParameter"] = field(default_factory=list)

    schema: int = 1
    type: str = "completion"
    description: str = ""
    completion: "PromptTemplateConfig.CompletionConfig" = field(default_factory=CompletionConfig)
    default_services: List[str] = field(default_factory=list)
    input: "PromptTemplateConfig.InputConfig" = field(default_factory=InputConfig)
>>>>>>> 9c8afa87 (set line-length for black in sync with Ruff, run black.)

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
<<<<<<< HEAD
                    raise Exception(
                        f"The input parameter doesn't have a name (function: {config['description']})"
                    )
=======
                    raise Exception(f"The input parameter doesn't have a name (function: {config.description})")
>>>>>>> 9c8afa87 (set line-length for black in sync with Ruff, run black.)

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

<<<<<<< HEAD
    @classmethod
    def from_completion_parameters(cls, **kwargs) -> "PromptTemplateConfig":
        concrete_class = cls.model_fields["completion"].annotation
        if isinstance(concrete_class, TypeVar):
            concrete_class = AIRequestSettings
        return PromptTemplateConfig(completion=concrete_class(extension_data=kwargs))
=======
        def keystoint(d):
            return {int(k) if k.isdigit() else k: v for k, v in d.items()}

        return PromptTemplateConfig.from_dict(json.loads(json_str, object_hook=keystoint))

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
        function_call: Optional[str] = None,
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
        config.completion.function_call = function_call
        return config
>>>>>>> 9c8afa87 (set line-length for black in sync with Ruff, run black.)
