# Copyright (c) Microsoft. All rights reserved.

import pytest

from semantic_kernel.exceptions.template_engine_exceptions import TemplateRenderException
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.functions.kernel_function import KernelFunction
from semantic_kernel.functions.kernel_function_decorator import kernel_function
from semantic_kernel.kernel import Kernel
from semantic_kernel.prompt_template.input_variable import InputVariable
from semantic_kernel.prompt_template.kernel_prompt_template import KernelPromptTemplate
from semantic_kernel.prompt_template.prompt_template_config import PromptTemplateConfig
from semantic_kernel.template_engine.blocks.var_block import VarBlock


def create_kernel_prompt_template(template: str, allow_dangerously_set_content: bool = False) -> KernelPromptTemplate:
    return KernelPromptTemplate(
        prompt_template_config=PromptTemplateConfig(
            name="test",
            description="test",
            template=template,
            allow_dangerously_set_content=allow_dangerously_set_content,
        )
    )


def test_init():
    template = KernelPromptTemplate(
        prompt_template_config=PromptTemplateConfig(name="test", description="test", template="{{$input}}")
    )
    assert template._blocks == [VarBlock(content="$input", name="input")]
    assert len(template._blocks) == 1


def test_init_validate_template_format_fail():
    with pytest.raises(ValueError):
        KernelPromptTemplate(
            prompt_template_config=PromptTemplateConfig(
                name="test", description="test", template="{{$input}}", template_format="handlebars"
            )
        )


def test_input_variables():
    config = PromptTemplateConfig(name="test", description="test", template="{{plug.func input=$input}}")
    assert config.input_variables == []
    KernelPromptTemplate(prompt_template_config=config)
    assert config.input_variables[0] == InputVariable(name="input")


def test_config_without_prompt():
    config = PromptTemplateConfig(name="test", description="test")
    template = KernelPromptTemplate(prompt_template_config=config)
    assert template._blocks == []


def test_extract_from_empty():
    blocks = create_kernel_prompt_template(None)._blocks
    assert len(blocks) == 0

    blocks = create_kernel_prompt_template("")._blocks
    assert len(blocks) == 0


async def test_it_renders_code_using_input(kernel: Kernel):
    arguments = KernelArguments()

    @kernel_function(name="function")
    def my_function(arguments: KernelArguments) -> str:
        return f"F({arguments.get('input')})"

    func = KernelFunction.from_method(my_function, "test")
    assert func is not None
    kernel.add_function("test", func)

    arguments["input"] = "INPUT-BAR"
    template = "foo-{{test.function}}-baz"
    target = create_kernel_prompt_template(template, allow_dangerously_set_content=True)
    result = await target.render(kernel, arguments)

    assert result == "foo-F(INPUT-BAR)-baz"


async def test_it_renders_code_using_variables(kernel: Kernel):
    arguments = KernelArguments()

    @kernel_function(name="function")
    def my_function(myVar: str) -> str:
        return f"F({myVar})"

    func = KernelFunction.from_method(my_function, "test")
    assert func is not None
    kernel.add_function("test", func)

    arguments["myVar"] = "BAR"
    template = "foo-{{test.function $myVar}}-baz"
    target = create_kernel_prompt_template(template, allow_dangerously_set_content=True)
    result = await target.render(kernel, arguments)

    assert result == "foo-F(BAR)-baz"


async def test_it_renders_code_using_variables_async(kernel: Kernel):
    arguments = KernelArguments()

    @kernel_function(name="function")
    async def my_function(myVar: str) -> str:
        return myVar

    func = KernelFunction.from_method(my_function, "test")
    assert func is not None
    kernel.add_function("test", func)

    arguments["myVar"] = "BAR"

    template = "foo-{{test.function $myVar}}-baz"

    target = create_kernel_prompt_template(template, allow_dangerously_set_content=True)
    result = await target.render(kernel, arguments)

    assert result == "foo-BAR-baz"


async def test_it_renders_code_error(kernel: Kernel):
    arguments = KernelArguments()

    @kernel_function(name="function")
    def my_function(arguments: KernelArguments) -> str:
        raise ValueError("Error")

    func = KernelFunction.from_method(my_function, "test")
    assert func is not None
    kernel.add_function("test", func)

    arguments["input"] = "INPUT-BAR"
    template = "foo-{{test.function}}-baz"
    target = create_kernel_prompt_template(template, allow_dangerously_set_content=True)
    with pytest.raises(TemplateRenderException):
        await target.render(kernel, arguments)
