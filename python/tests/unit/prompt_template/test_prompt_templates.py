# Copyright (c) Microsoft. All rights reserved.


import json

import yaml
from pytest import raises

from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from semantic_kernel.functions.kernel_function_from_prompt import KernelFunctionFromPrompt
from semantic_kernel.functions.kernel_parameter_metadata import KernelParameterMetadata
from semantic_kernel.prompt_template.input_variable import InputVariable
from semantic_kernel.prompt_template.prompt_template_config import PromptTemplateConfig


def test_prompt_template_config_initialization_minimal():
    config = PromptTemplateConfig(template="Example template")
    assert config.template == "Example template"
    assert config.name == ""
    assert config.description == ""
    assert config.template_format == "semantic-kernel"
    assert config.input_variables == []
    assert config.execution_settings == {}


def test_prompt_template_config_initialization_full():
    input_variables = [
        InputVariable(
            name="var1", description="A variable", default="default_val", is_required=True, json_schema="string"
        )
    ]
    execution_settings = {"setting1": PromptExecutionSettings(setting_value="value1")}
    config = PromptTemplateConfig(
        name="Test Config",
        description="Test Description",
        template="Example template",
        template_format="semantic-kernel",
        input_variables=input_variables,
        execution_settings=execution_settings,
    )
    assert config.name == "Test Config"
    assert config.description == "Test Description"
    assert config.template_format == "semantic-kernel"
    assert len(config.input_variables) == 1
    assert config.execution_settings is not None


def test_add_execution_settings():
    config = PromptTemplateConfig(template="Example template")
    new_settings = PromptExecutionSettings(service_id="test", setting_value="new_value")
    config.add_execution_settings(new_settings)
    assert config.execution_settings["test"] == new_settings


def test_add_execution_settings_no_overwrite():
    config = PromptTemplateConfig(template="Example template")
    new_settings = PromptExecutionSettings(service_id="test", setting_value="new_value")
    config.add_execution_settings(new_settings)
    assert config.execution_settings["test"] == new_settings
    new_settings = PromptExecutionSettings(service_id="test", setting_value="new_value2")
    config.add_execution_settings(new_settings, overwrite=False)
    assert config.execution_settings["test"].extension_data["setting_value"] == "new_value"


def test_add_execution_settings_with_overwrite():
    config = PromptTemplateConfig(template="Example template")
    new_settings = PromptExecutionSettings(service_id="test", setting_value="new_value")
    config.add_execution_settings(new_settings)
    assert config.execution_settings["test"] == new_settings
    new_settings = PromptExecutionSettings(service_id="test", setting_value="new_value2")
    config.add_execution_settings(new_settings, overwrite=True)
    assert config.execution_settings["test"].extension_data["setting_value"] == "new_value2"


def test_get_kernel_parameter_metadata_empty():
    config = PromptTemplateConfig(template="Example template")
    metadata = config.get_kernel_parameter_metadata()
    assert metadata == []


def test_get_kernel_parameter_metadata_with_variables():
    input_variables = [
        InputVariable(
            name="var1", description="A variable", default="default_val", is_required=True, json_schema="string"
        )
    ]
    config = PromptTemplateConfig(template="Example template", input_variables=input_variables)
    metadata: list[KernelParameterMetadata] = config.get_kernel_parameter_metadata()
    assert len(metadata) == 1
    assert metadata[0].name == "var1"
    assert metadata[0].description == "A variable"
    assert metadata[0].default_value == "default_val"
    assert metadata[0].type_ == "string"
    assert metadata[0].is_required is True


def test_get_kernel_parameter_metadata_with_variables_bad_default():
    input_variables = [
        InputVariable(name="var1", description="A variable", default=120, is_required=True, json_schema="string")
    ]
    with raises(TypeError):
        PromptTemplateConfig(template="Example template", input_variables=input_variables)


def test_restore():
    name = "Test Template"
    description = "This is a test template."
    template = "Hello, {{$name}}!"
    input_variables = [InputVariable(name="name", description="Name of the person to greet", type="string")]
    execution_settings = PromptExecutionSettings(timeout=30, max_tokens=100)

    restored_template = PromptTemplateConfig.restore(
        name=name,
        description=description,
        template=template,
        input_variables=input_variables,
        execution_settings={"default": execution_settings},
    )

    assert restored_template.name == name, "The name attribute does not match the expected value."
    assert restored_template.description == description, "The description attribute does not match the expected value."
    assert restored_template.template == template, "The template attribute does not match the expected value."
    assert restored_template.input_variables == input_variables, (
        "The input_variables attribute does not match the expected value."
    )
    assert restored_template.execution_settings["default"] == execution_settings, (
        "The execution_settings attribute does not match the expected value."
    )


def test_prompt_template_config_initialization_full_handlebars():
    input_variables = [
        InputVariable(
            name="var1", description="A variable", default="default_val", is_required=True, json_schema="string"
        )
    ]
    execution_settings = {"setting1": PromptExecutionSettings(setting_value="value1")}
    config = PromptTemplateConfig(
        name="Test Config",
        description="Test Description",
        template="Example template",
        template_format="handlebars",
        input_variables=input_variables,
        execution_settings=execution_settings,
    )
    assert config.name == "Test Config"
    assert config.description == "Test Description"
    assert config.template_format == "handlebars"
    assert len(config.input_variables) == 1
    assert config.execution_settings is not None


def test_restore_handlebars():
    name = "Test Template"
    description = "This is a test template."
    template = "Hello, {{name}}!"
    template_format = "handlebars"
    input_variables = [InputVariable(name="name", description="Name of the person to greet", type="string")]
    execution_settings = PromptExecutionSettings(timeout=30, max_tokens=100)

    restored_template = PromptTemplateConfig.restore(
        name=name,
        description=description,
        template=template,
        input_variables=input_variables,
        template_format=template_format,
        execution_settings={"default": execution_settings},
    )

    assert restored_template.name == name, "The name attribute does not match the expected value."
    assert restored_template.description == description, "The description attribute does not match the expected value."
    assert restored_template.template == template, "The template attribute does not match the expected value."
    assert restored_template.input_variables == input_variables, (
        "The input_variables attribute does not match the expected value."
    )
    assert restored_template.execution_settings["default"] == execution_settings, (
        "The execution_settings attribute does not match the expected value."
    )
    assert restored_template.template_format == template_format, (
        "The template_format attribute does not match the expected value."
    )


def test_rewrite_execution_settings():
    config = PromptTemplateConfig.rewrite_execution_settings(settings=None)
    assert config == {}

    settings = {"default": PromptExecutionSettings()}
    config = PromptTemplateConfig.rewrite_execution_settings(settings=settings)
    assert config == settings

    settings = [PromptExecutionSettings()]
    config = PromptTemplateConfig.rewrite_execution_settings(settings=settings)
    assert config == {"default": settings[0]}

    settings = PromptExecutionSettings()
    config = PromptTemplateConfig.rewrite_execution_settings(settings=settings)
    assert config == {"default": settings}

    settings = PromptExecutionSettings(service_id="test")
    config = PromptTemplateConfig.rewrite_execution_settings(settings=settings)
    assert config == {"test": settings}


def test_from_json():
    config = PromptTemplateConfig.from_json(
        json.dumps({
            "name": "Test Config",
            "description": "Test Description",
            "template": "Example template",
            "template_format": "semantic-kernel",
            "input_variables": [
                {
                    "name": "var1",
                    "description": "A variable",
                    "default": "default_val",
                    "is_required": True,
                    "json_schema": "string",
                }
            ],
            "execution_settings": {},
        })
    )
    assert config.name == "Test Config"
    assert config.description == "Test Description"
    assert config.template == "Example template"
    assert config.template_format == "semantic-kernel"
    assert len(config.input_variables) == 1
    assert config.execution_settings == {}


def test_from_json_fail():
    with raises(ValueError):
        PromptTemplateConfig.from_json("")


def test_from_json_validate_fail():
    with raises(ValueError):
        PromptTemplateConfig.from_json(
            json.dumps({
                "name": "Test Config",
                "description": "Test Description",
                "template": "Example template",
                "template_format": "semantic-kernel",
                "input_variables": [
                    {
                        "name": "var1",
                        "description": "A variable",
                        "default": 1,
                        "is_required": True,
                        "json_schema": "string",
                    }
                ],
                "execution_settings": {},
            })
        )


def test_from_json_with_function_choice_behavior():
    config_string = json.dumps({
        "name": "Test Config",
        "description": "Test Description",
        "template": "Example template",
        "template_format": "semantic-kernel",
        "input_variables": [
            {
                "name": "var1",
                "description": "A variable",
                "default": "default_val",
                "is_required": True,
                "json_schema": "string",
            }
        ],
        "execution_settings": {
            "settings1": {"function_choice_behavior": {"type": "auto", "functions": ["p1.f1"]}},
        },
    })
    config = PromptTemplateConfig.from_json(config_string)

    expected_execution_settings = PromptExecutionSettings(
        function_choice_behavior={"type": "auto", "functions": ["p1.f1"]}
    )

    assert config.name == "Test Config"
    assert config.description == "Test Description"
    assert config.template == "Example template"
    assert config.template_format == "semantic-kernel"
    assert len(config.input_variables) == 1
    assert config.execution_settings["settings1"] == expected_execution_settings


def test_from_yaml_with_function_choice_behavior():
    yaml_payload = """
    name: Test Config
    description: Test Description
    template: Example template
    template_format: semantic-kernel
    input_variables:
      - name: var1
        description: A variable
        default: default_val
        is_required: true
        json_schema: string
    execution_settings:
      settings1:
        function_choice_behavior:
          type: auto
          functions:
            - p1.f1
    """
    yaml_data = yaml.safe_load(yaml_payload)
    config = PromptTemplateConfig(**yaml_data)

    expected_execution_settings = PromptExecutionSettings(
        function_choice_behavior={"type": "auto", "functions": ["p1.f1"]}
    )

    assert config.name == "Test Config"
    assert config.description == "Test Description"
    assert config.template == "Example template"
    assert config.template_format == "semantic-kernel"
    assert len(config.input_variables) == 1
    assert config.execution_settings["settings1"] == expected_execution_settings


def test_multiple_param_in_prompt():
    func = KernelFunctionFromPrompt("test", prompt="{{$param}}{{$param}}")
    assert len(func.parameters) == 1
    assert func.metadata.parameters[0].schema_data == {"type": "object"}
