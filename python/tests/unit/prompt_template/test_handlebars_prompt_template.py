from unittest.mock import Mock

from pytest import fixture, mark

from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.functions.kernel_function import KernelFunction
from semantic_kernel.functions.kernel_function_decorator import kernel_function
from semantic_kernel.functions.kernel_plugin_collection import KernelPluginCollection
from semantic_kernel.kernel import Kernel
from semantic_kernel.prompt_template.handlebars_prompt_template import HandlebarsPromptTemplate
from semantic_kernel.prompt_template.input_variable import InputVariable
from semantic_kernel.prompt_template.prompt_template_config import PromptTemplateConfig


def create_handlebars_prompt_template(template: str) -> HandlebarsPromptTemplate:
    return HandlebarsPromptTemplate(
        prompt_template_config=PromptTemplateConfig(
            name="test", description="test", template=template, template_format="handlebars"
        )
    )


@fixture
def plugins():
    return Mock(spec=KernelPluginCollection)


def test_init():
    template = HandlebarsPromptTemplate(
        prompt_template_config=PromptTemplateConfig(
            name="test", description="test", template="{{input}}", template_format="handlebars"
        )
    )
    assert template.prompt_template_config.template == "{{input}}"


def test_input_variables():
    config = PromptTemplateConfig(name="test", description="test", template="{{plug.func input=$input}}")
    assert config.input_variables == []
    HandlebarsPromptTemplate(prompt_template_config=config)
    assert config.input_variables[0] == InputVariable(name="input")


def test_config_without_prompt():
    config = PromptTemplateConfig(name="test", description="test")
    template = HandlebarsPromptTemplate(prompt_template_config=config)


@mark.asyncio
async def test_it_renders_variables(kernel: Kernel):
    template = "Foo {{#if bar}}{{bar}}{{else}}No Bar{{/if}}"
    target = create_handlebars_prompt_template(template)

    rendered = await target.render(kernel, KernelArguments(bar="Bar"))
    assert rendered == "Foo Bar"

    rendered = await target.render(kernel, KernelArguments())
    assert rendered == "Foo No Bar"


@mark.asyncio
async def test_it_renders_code():
    kernel = Kernel()
    arguments = KernelArguments()

    @kernel_function(name="function")
    def my_function(arguments: KernelArguments) -> str:
        return f"F({arguments.get('_a')}-{arguments.get('arg1')})"

    func = KernelFunction.from_method(my_function, "test")
    assert func is not None
    kernel.plugins.add_plugin_from_functions("test", [func])

    arguments["_a"] = "foo"
    arguments["arg"] = "bar"
    template = "template {{'val'}}{{test.function $_a arg1=$arg}}"

    target = create_handlebars_prompt_template(template)

    result = await target.render(kernel, arguments)
    assert result == "template valF(foo-bar)"


@mark.asyncio
async def test_it_renders_code_using_input():
    kernel = Kernel()
    arguments = KernelArguments()

    @kernel_function(name="function")
    def my_function(arguments: KernelArguments) -> str:
        return f"F({arguments.get('input')})"

    func = KernelFunction.from_method(my_function, "test")
    assert func is not None
    kernel.plugins.add_plugin_from_functions("test", [func])

    arguments["input"] = "INPUT-BAR"
    template = "foo-{{test.function}}-baz"
    target = create_kernel_prompt_template(template)
    result = await target.render(kernel, arguments)

    assert result == "foo-F(INPUT-BAR)-baz"


@mark.asyncio
async def test_it_renders_code_using_variables():
    kernel = Kernel()
    arguments = KernelArguments()

    @kernel_function(name="function")
    def my_function(myVar: str) -> str:
        return f"F({myVar})"

    func = KernelFunction.from_method(my_function, "test")
    assert func is not None
    kernel.plugins.add_plugin_from_functions("test", [func])

    arguments["myVar"] = "BAR"
    template = "foo-{{test.function $myVar}}-baz"
    target = create_kernel_prompt_template(template)
    result = await target.render(kernel, arguments)

    assert result == "foo-F(BAR)-baz"


@mark.asyncio
async def test_it_renders_code_using_variables_async():
    kernel = Kernel()
    arguments = KernelArguments()

    @kernel_function(name="function")
    async def my_function(myVar: str) -> str:
        return myVar

    func = KernelFunction.from_method(my_function, "test")
    assert func is not None
    kernel.plugins.add_plugin_from_functions("test", [func])

    arguments["myVar"] = "BAR"

    template = "foo-{{test.function $myVar}}-baz"

    target = create_kernel_prompt_template(template)
    result = await target.render(kernel, arguments)

    assert result == "foo-BAR-baz"
