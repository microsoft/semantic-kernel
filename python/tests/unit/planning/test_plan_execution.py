# Copyright (c) Microsoft. All rights reserved.

import pytest

import semantic_kernel as sk
from semantic_kernel.core_plugins.math_plugin import MathPlugin
from semantic_kernel.core_plugins.text_plugin import TextPlugin
from semantic_kernel.planning import Plan


def test_invoke_empty_plan():
    plan = Plan()
    result = plan.invoke()
    assert result.result == ""


@pytest.mark.asyncio
async def test_invoke_empty_plan_async():
    plan = Plan()
    result = await plan.invoke_async()
    assert result.result == ""


def test_invoke_plan_constructed_with_function():
    # create a kernel
    kernel = sk.Kernel()

    # import test (text) plugin
    plugin = TextPlugin()
    plugin_config_dict = kernel.import_plugin(plugin, "text")
    test_function = plugin_config_dict["uppercase"]

    # setup context
    context = kernel.create_new_context()
    context["input"] = "hello world "

    plan = Plan(name="test", function=test_function)
    result = plan.invoke(context=context)
    assert result.result == "HELLO WORLD "


@pytest.mark.asyncio
async def test_invoke_plan_constructed_with_function_async():
    # create a kernel
    kernel = sk.Kernel()

    # import test (text) plugin
    plugin = TextPlugin()
    plugin_config_dict = kernel.import_plugin(plugin, "text")
    test_function = plugin_config_dict["uppercase"]

    # setup context
    context = kernel.create_new_context()
    context["input"] = "hello world "

    plan = Plan(name="test", function=test_function)
    result = await plan.invoke_async(context=context)
    assert result.result == "HELLO WORLD "


def test_invoke_empty_plan_with_added_function_step():
    # create a kernel
    kernel = sk.Kernel()

    # import test (text) plugin
    plugin = TextPlugin()
    plugin_config_dict = kernel.import_plugin(plugin, "text")
    test_function = plugin_config_dict["uppercase"]

    # setup context
    context = kernel.create_new_context()
    context["input"] = "hello world "

    plan = Plan(name="test")
    plan.add_steps([test_function])
    result = plan.invoke(context=context)
    assert result.result == "HELLO WORLD "


@pytest.mark.asyncio
async def test_invoke_empty_plan_with_added_function_step_async():
    # create a kernel
    kernel = sk.Kernel()

    # import test (text) plugin
    plugin = TextPlugin()
    plugin_config_dict = kernel.import_plugin(plugin, "text")
    test_function = plugin_config_dict["uppercase"]

    # setup context
    context = kernel.create_new_context()
    context["input"] = "hello world "

    plan = Plan(name="test")
    plan.add_steps([test_function])
    result = await plan.invoke_async(context=context)
    assert result.result == "HELLO WORLD "


def test_invoke_empty_plan_with_added_plan_step():
    # create a kernel
    kernel = sk.Kernel()

    # import test (text) plugin
    plugin = TextPlugin()
    plugin_config_dict = kernel.import_plugin(plugin, "text")
    test_function = plugin_config_dict["uppercase"]

    # setup context
    context = kernel.create_new_context()
    context["input"] = "hello world "

    plan = Plan(name="test")
    new_step = Plan(name="test", function=test_function)
    plan.add_steps([new_step])
    result = plan.invoke(context=context)
    assert result.result == "HELLO WORLD "


@pytest.mark.asyncio
async def test_invoke_empty_plan_with_added_plan_step_async():
    # create a kernel
    kernel = sk.Kernel()

    # import test (text) plugin
    plugin = TextPlugin()
    plugin_config_dict = kernel.import_plugin(plugin, "text")
    test_function = plugin_config_dict["uppercase"]

    # setup context
    context = kernel.create_new_context()
    context["input"] = "hello world "

    plan = Plan(name="test")
    new_step = Plan(name="test", function=test_function)
    plan.add_steps([new_step])
    result = await plan.invoke_async(context=context)
    assert result.result == "HELLO WORLD "


def test_invoke_multi_step_plan():
    # create a kernel
    kernel = sk.Kernel()

    # import test (text) plugin
    plugin = TextPlugin()
    plugin_config_dict = kernel.import_plugin(plugin, "text")
    test_function = plugin_config_dict["uppercase"]
    test_function2 = plugin_config_dict["trim_end"]

    # setup context
    context = kernel.create_new_context()
    context["input"] = "hello world "

    plan = Plan(name="test")
    new_step = Plan(name="test", function=test_function)
    new_step2 = Plan(name="test", function=test_function2)
    plan.add_steps([new_step, new_step2])
    result = plan.invoke(context=context)
    assert result.result == "HELLO WORLD"


@pytest.mark.asyncio
async def test_invoke_multi_step_plan_async():
    # create a kernel
    kernel = sk.Kernel()

    # import test (text) plugin
    plugin = TextPlugin()
    plugin_config_dict = kernel.import_plugin(plugin, "text")
    test_function = plugin_config_dict["uppercase"]
    test_function2 = plugin_config_dict["trim_end"]

    # setup context
    context = kernel.create_new_context()
    context["input"] = "hello world "

    plan = Plan(name="test")
    new_step = Plan(name="test", function=test_function)
    new_step2 = Plan(name="test", function=test_function2)
    plan.add_steps([new_step, new_step2])
    result = await plan.invoke_async(context=context)
    assert result.result == "HELLO WORLD"


@pytest.mark.asyncio
async def test_invoke_multi_step_plan_async_with_variables():
    # create a kernel
    kernel = sk.Kernel()

    # import test (text) plugin
    plugin = MathPlugin()
    plugin_config_dict = kernel.import_plugin(plugin, "math")
    test_function = plugin_config_dict["Add"]
    test_function2 = plugin_config_dict["Subtract"]

    plan = Plan(name="test")

    # setup context for step 1
    context1 = kernel.create_new_context()
    context1["amount"] = "10"
    new_step = Plan(name="test", function=test_function, parameters=context1.variables)

    # setup context for step 2
    context2 = kernel.create_new_context()
    context2["amount"] = "5"
    new_step2 = Plan(name="test", function=test_function2, parameters=context2.variables)

    plan.add_steps([new_step, new_step2])
    result = await plan.invoke_async(input="2")
    assert result.result == "7"
