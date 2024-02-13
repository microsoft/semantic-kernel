# Copyright (c) Microsoft. All rights reserved.

import json

import pytest
from typing import List

from semantic_kernel.prompt_template.prompt_template_config import (
    PromptTemplateConfig,
)
from semantic_kernel.prompt_template.input_variable import InputVariable
from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from semantic_kernel.functions.kernel_parameter_metadata import KernelParameterMetadata


def test_prompt_template_config_initialization_minimal():
    config = PromptTemplateConfig(template="Example template")
    assert config.template == "Example template"
    assert config.name == ""
    assert config.description == ""
    assert config.template_format == "semantic-kernel"
    assert config.input_variables == []
    assert config.execution_settings == {}

def test_prompt_template_config_initialization_full():
    input_variables = [InputVariable(name="var1", description="A variable", default="default_val", is_required=True, json_schema="string")]
    execution_settings = {"setting1": PromptExecutionSettings(setting_value="value1")}
    config = PromptTemplateConfig(
        name="Test Config",
        description="Test Description",
        template="Example template",
        template_format="custom-format",
        input_variables=input_variables,
        execution_settings=execution_settings
    )
    assert config.name == "Test Config"
    assert config.description == "Test Description"
    assert config.template_format == "custom-format"
    assert len(config.input_variables) == 1
    assert len(config.execution_settings) == 1

def test_add_execution_settings():
    config = PromptTemplateConfig(template="Example template")
    new_settings = {"new_setting": PromptExecutionSettings(setting_value="new_value")}
    config.add_execution_settings(new_settings)
    assert config.execution_settings == new_settings

def test_get_kernel_parameter_metadata_empty():
    config = PromptTemplateConfig(template="Example template")
    metadata = config.get_kernel_parameter_metadata()
    assert metadata == []

def test_get_kernel_parameter_metadata_with_variables():
    input_variables = [InputVariable(name="var1", description="A variable", default="default_val", is_required=True, json_schema="string")]
    config = PromptTemplateConfig(template="Example template", input_variables=input_variables)
    metadata: List[KernelParameterMetadata] = config.get_kernel_parameter_metadata()
    assert len(metadata) == 1
    assert metadata[0].name == "var1"
    assert metadata[0].description == "A variable"
    assert metadata[0].default_value == "default_val"
    assert metadata[0].type_ == "string"
    assert metadata[0].required is True
