# Copyright (c) Microsoft. All rights reserved.

import pytest

import semantic_kernel as sk
from semantic_kernel.core_plugins.math_plugin import MathPlugin
from semantic_kernel.core_plugins.text_plugin import TextPlugin
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.planners import Plan


@pytest.mark.asyncio
async def test_invoke_empty_plan():
    kernel = sk.Kernel()
    plan = Plan()
    result = await plan.invoke(kernel)
    assert str(result) == ""


@pytest.mark.asyncio
async def test_invoke_plan_constructed_with_function():
    # create a kernel
    kernel = sk.Kernel()

    # import test (text) plugin
    plugin = TextPlugin()
    plugin = kernel.import_plugin_from_object(plugin, "text")
    test_function = plugin["uppercase"]

    plan = Plan(name="test", function=test_function)
    result = await plan.invoke(kernel, KernelArguments(input="hello world "))
    assert str(result) == "HELLO WORLD "


@pytest.mark.asyncio
async def test_invoke_empty_plan_with_added_function_step():
    # create a kernel
    kernel = sk.Kernel()

    # import test (text) plugin
    plugin = TextPlugin()
    plugin = kernel.import_plugin_from_object(plugin, "text")
    test_function = plugin["uppercase"]

    plan = Plan(name="test")
    plan.add_steps([test_function])
    result = await plan.invoke(kernel, KernelArguments(input="hello world "))
    print(result)
    assert str(result) == "HELLO WORLD "


@pytest.mark.asyncio
async def test_invoke_empty_plan_with_added_plan_step():
    # create a kernel
    kernel = sk.Kernel()

    # import test (text) plugin
    plugin = TextPlugin()
    plugin = kernel.import_plugin_from_object(plugin, "text")
    test_function = plugin["uppercase"]

    plan = Plan(name="test")
    new_step = Plan(name="test", function=test_function)
    plan.add_steps([new_step])
    result = await plan.invoke(kernel, KernelArguments(input="hello world "))
    assert str(result) == "HELLO WORLD "


@pytest.mark.asyncio
async def test_invoke_multi_step_plan():
    # create a kernel
    kernel = sk.Kernel()

    # import test (text) plugin
    plugin = TextPlugin()
    plugin = kernel.import_plugin_from_object(plugin, "text")
    test_function = plugin["uppercase"]
    test_function2 = plugin["trim_end"]

    plan = Plan(name="test")
    new_step = Plan(name="test", function=test_function)
    new_step2 = Plan(name="test", function=test_function2)
    plan.add_steps([new_step, new_step2])
    result = await plan.invoke(kernel, KernelArguments(input="hello world "))
    assert str(result) == "HELLO WORLD"


@pytest.mark.asyncio
async def test_invoke_multi_step_plan_with_arguments():
    # create a kernel
    kernel = sk.Kernel()

    # import test (text) plugin
    plugin = MathPlugin()
    plugin = kernel.import_plugin_from_object(plugin, "math")
    test_function = plugin["Add"]
    test_function2 = plugin["Subtract"]

    plan = Plan(name="test")

    new_step = Plan(name="test", function=test_function, parameters=KernelArguments(amount=10))
    new_step2 = Plan(name="test", function=test_function2, parameters=KernelArguments(amount=5))

    plan.add_steps([new_step, new_step2])
    result = await plan.invoke(kernel, KernelArguments(input=2))
    assert str(result) == "7"
