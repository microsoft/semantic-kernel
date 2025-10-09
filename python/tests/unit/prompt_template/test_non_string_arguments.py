# Copyright (c) Microsoft. All rights reserved.

"""Tests for non-string kernel arguments passed to functions in prompt templates."""

import pytest

from semantic_kernel import Kernel
from semantic_kernel.functions import kernel_function
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.prompt_template.kernel_prompt_template import KernelPromptTemplate
from semantic_kernel.prompt_template.prompt_template_config import PromptTemplateConfig


class NonStringArgumentsPlugin:
    """Plugin to test non-string argument types."""

    @kernel_function
    def process_int(self, value: int) -> str:
        """Process an integer argument."""
        assert isinstance(value, int), f"Expected int, got {type(value)}"
        return f"int:{value * 2}"

    @kernel_function
    def process_float(self, value: float) -> str:
        """Process a float argument."""
        assert isinstance(value, (float, int)), f"Expected float, got {type(value)}"
        return f"float:{value * 2.0}"

    @kernel_function
    def process_bool(self, value: bool) -> str:
        """Process a boolean argument."""
        assert isinstance(value, bool), f"Expected bool, got {type(value)}"
        return f"bool:{not value}"

    @kernel_function
    def process_list(self, items: list) -> str:
        """Process a list argument."""
        assert isinstance(items, list), f"Expected list, got {type(items)}"
        return f"list:{len(items)}"

    @kernel_function
    def process_dict(self, data: dict) -> str:
        """Process a dict argument."""
        assert isinstance(data, dict), f"Expected dict, got {type(data)}"
        return f"dict:{len(data)}"

    @kernel_function
    def process_none(self, value: None) -> str:
        """Process a None argument."""
        assert value is None, f"Expected None, got {value}"
        return "none:received"

    @kernel_function
    def process_multiple(self, a: int, b: str, c: list) -> str:
        """Process multiple arguments of different types."""
        assert isinstance(a, int), f"Expected int for a, got {type(a)}"
        assert isinstance(b, str), f"Expected str for b, got {type(b)}"
        assert isinstance(c, list), f"Expected list for c, got {type(c)}"
        return f"multi:{a},{b},{len(c)}"


@pytest.mark.asyncio
async def test_int_argument(kernel: Kernel):
    """Test passing integer argument to function."""
    kernel.add_plugin(NonStringArgumentsPlugin(), "test")
    template = "Result: {{ test.process_int value=$num }}"
    arguments = KernelArguments(num=42)

    result = await KernelPromptTemplate(
        prompt_template_config=PromptTemplateConfig(
            name="test", description="test", template=template, allow_dangerously_set_content=True
        )
    ).render(kernel, arguments)

    assert result == "Result: int:84"


@pytest.mark.asyncio
async def test_float_argument(kernel: Kernel):
    """Test passing float argument to function."""
    kernel.add_plugin(NonStringArgumentsPlugin(), "test")
    template = "Result: {{ test.process_float value=$num }}"
    arguments = KernelArguments(num=3.14)

    result = await KernelPromptTemplate(
        prompt_template_config=PromptTemplateConfig(
            name="test", description="test", template=template, allow_dangerously_set_content=True
        )
    ).render(kernel, arguments)

    assert result == "Result: float:6.28"


@pytest.mark.asyncio
async def test_bool_argument(kernel: Kernel):
    """Test passing boolean argument to function."""
    kernel.add_plugin(NonStringArgumentsPlugin(), "test")
    template = "Result: {{ test.process_bool value=$flag }}"
    arguments = KernelArguments(flag=True)

    result = await KernelPromptTemplate(
        prompt_template_config=PromptTemplateConfig(
            name="test", description="test", template=template, allow_dangerously_set_content=True
        )
    ).render(kernel, arguments)

    assert result == "Result: bool:False"


@pytest.mark.asyncio
async def test_list_argument(kernel: Kernel):
    """Test passing list argument to function."""
    kernel.add_plugin(NonStringArgumentsPlugin(), "test")
    template = "Result: {{ test.process_list items=$my_list }}"
    arguments = KernelArguments(my_list=[1, 2, 3, 4, 5])

    result = await KernelPromptTemplate(
        prompt_template_config=PromptTemplateConfig(
            name="test", description="test", template=template, allow_dangerously_set_content=True
        )
    ).render(kernel, arguments)

    assert result == "Result: list:5"


@pytest.mark.asyncio
async def test_dict_argument(kernel: Kernel):
    """Test passing dict argument to function."""
    kernel.add_plugin(NonStringArgumentsPlugin(), "test")
    template = "Result: {{ test.process_dict data=$my_dict }}"
    arguments = KernelArguments(my_dict={"a": 1, "b": 2, "c": 3})

    result = await KernelPromptTemplate(
        prompt_template_config=PromptTemplateConfig(
            name="test", description="test", template=template, allow_dangerously_set_content=True
        )
    ).render(kernel, arguments)

    assert result == "Result: dict:3"


@pytest.mark.asyncio
async def test_none_argument(kernel: Kernel):
    """Test passing None argument to function."""
    kernel.add_plugin(NonStringArgumentsPlugin(), "test")
    template = "Result: {{ test.process_none value=$none_val }}"
    arguments = KernelArguments(none_val=None)

    result = await KernelPromptTemplate(
        prompt_template_config=PromptTemplateConfig(
            name="test", description="test", template=template, allow_dangerously_set_content=True
        )
    ).render(kernel, arguments)

    assert result == "Result: none:received"


@pytest.mark.asyncio
async def test_multiple_typed_arguments(kernel: Kernel):
    """Test passing multiple arguments of different types to function."""
    kernel.add_plugin(NonStringArgumentsPlugin(), "test")
    template = "Result: {{ test.process_multiple a=$num b=$text c=$items }}"
    arguments = KernelArguments(num=10, text="hello", items=[1, 2, 3])

    result = await KernelPromptTemplate(
        prompt_template_config=PromptTemplateConfig(
            name="test", description="test", template=template, allow_dangerously_set_content=True
        )
    ).render(kernel, arguments)

    assert result == "Result: multi:10,hello,3"


@pytest.mark.asyncio
async def test_string_argument_still_works(kernel: Kernel):
    """Test that string arguments still work correctly."""
    kernel.add_plugin(NonStringArgumentsPlugin(), "test")
    template = "Result: {{ test.process_multiple a=$num b=$text c=$items }}"
    arguments = KernelArguments(num=5, text="world", items=[])

    result = await KernelPromptTemplate(
        prompt_template_config=PromptTemplateConfig(
            name="test", description="test", template=template, allow_dangerously_set_content=True
        )
    ).render(kernel, arguments)

    assert result == "Result: multi:5,world,0"


@pytest.mark.asyncio
async def test_positional_list_argument(kernel: Kernel):
    """Test passing list as positional (first) argument to function."""
    kernel.add_plugin(NonStringArgumentsPlugin(), "test")
    template = "Result: {{ test.process_list $my_list }}"
    arguments = KernelArguments(my_list=[1, 2, 3, 4, 5])

    result = await KernelPromptTemplate(
        prompt_template_config=PromptTemplateConfig(
            name="test", description="test", template=template, allow_dangerously_set_content=True
        )
    ).render(kernel, arguments)

    assert result == "Result: list:5"


@pytest.mark.asyncio
async def test_positional_int_argument(kernel: Kernel):
    """Test passing int as positional (first) argument to function."""
    kernel.add_plugin(NonStringArgumentsPlugin(), "test")
    template = "Result: {{ test.process_int $num }}"
    arguments = KernelArguments(num=42)

    result = await KernelPromptTemplate(
        prompt_template_config=PromptTemplateConfig(
            name="test", description="test", template=template, allow_dangerously_set_content=True
        )
    ).render(kernel, arguments)

    assert result == "Result: int:84"
