# Copyright (c) Microsoft. All rights reserved.

import pytest

<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
from semantic_kernel.core_plugins.math_plugin import MathPlugin
from semantic_kernel.core_plugins.text_plugin import TextPlugin
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.kernel import Kernel
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
=======
import semantic_kernel as sk
from semantic_kernel.core_plugins.math_plugin import MathPlugin
from semantic_kernel.core_plugins.text_plugin import TextPlugin
from semantic_kernel.functions.kernel_arguments import KernelArguments
>>>>>>> f40c1f2075e2443c31c57c34f5f66c2711a8db75
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
from semantic_kernel.planners import Plan


@pytest.mark.asyncio
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
async def test_invoke_empty_plan(kernel: Kernel):
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
async def test_invoke_empty_plan(kernel: Kernel):
=======
<<<<<<< HEAD
async def test_invoke_empty_plan(kernel: Kernel):
=======
async def test_invoke_empty_plan():
    kernel = sk.Kernel()
>>>>>>> f40c1f2075e2443c31c57c34f5f66c2711a8db75
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
    plan = Plan()
    result = await plan.invoke(kernel)
    assert str(result) == ""


@pytest.mark.asyncio
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
async def test_invoke_plan_constructed_with_function(kernel: Kernel):
    # import test (text) plugin
    kernel.add_plugin(TextPlugin(), "text")
    test_function = kernel.get_function("text", "uppercase")
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
=======
async def test_invoke_plan_constructed_with_function():
    # create a kernel
    kernel = sk.Kernel()

    # import test (text) plugin
    plugin = TextPlugin()
    plugin = kernel.import_plugin(plugin, "text")
    test_function = plugin["uppercase"]
>>>>>>> f40c1f2075e2443c31c57c34f5f66c2711a8db75
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes

    plan = Plan(name="test", function=test_function)
    result = await plan.invoke(kernel, KernelArguments(input="hello world "))
    assert str(result) == "HELLO WORLD "


@pytest.mark.asyncio
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
async def test_invoke_empty_plan_with_added_function_step(kernel: Kernel):
    # import test (text) plugin
    kernel.add_plugin(TextPlugin(), "text")
    test_function = kernel.get_function("text", "uppercase")
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
=======
async def test_invoke_empty_plan_with_added_function_step():
    # create a kernel
    kernel = sk.Kernel()

    # import test (text) plugin
    plugin = TextPlugin()
    plugin = kernel.import_plugin(plugin, "text")
    test_function = plugin["uppercase"]
>>>>>>> f40c1f2075e2443c31c57c34f5f66c2711a8db75
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes

    plan = Plan(name="test")
    plan.add_steps([test_function])
    result = await plan.invoke(kernel, KernelArguments(input="hello world "))
    print(result)
    assert str(result) == "HELLO WORLD "


@pytest.mark.asyncio
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
async def test_invoke_empty_plan_with_added_plan_step(kernel: Kernel):
    # import test (text) plugin
    kernel.add_plugin(TextPlugin(), "text")
    test_function = kernel.get_function("text", "uppercase")
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
=======
async def test_invoke_empty_plan_with_added_plan_step():
    # create a kernel
    kernel = sk.Kernel()

    # import test (text) plugin
    plugin = TextPlugin()
    plugin = kernel.import_plugin(plugin, "text")
    test_function = plugin["uppercase"]
>>>>>>> f40c1f2075e2443c31c57c34f5f66c2711a8db75
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes

    plan = Plan(name="test")
    new_step = Plan(name="test", function=test_function)
    plan.add_steps([new_step])
    result = await plan.invoke(kernel, KernelArguments(input="hello world "))
    assert str(result) == "HELLO WORLD "


@pytest.mark.asyncio
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
async def test_invoke_multi_step_plan(kernel: Kernel):
    # import test (text) plugin
    kernel.add_plugin(TextPlugin(), "text")
    test_function = kernel.get_function("text", "uppercase")
    test_function2 = kernel.get_function("text", "trim_end")
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
=======
async def test_invoke_multi_step_plan():
    # create a kernel
    kernel = sk.Kernel()

    # import test (text) plugin
    plugin = TextPlugin()
    plugin = kernel.import_plugin(plugin, "text")
    test_function = plugin["uppercase"]
    test_function2 = plugin["trim_end"]
>>>>>>> f40c1f2075e2443c31c57c34f5f66c2711a8db75
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes

    plan = Plan(name="test")
    new_step = Plan(name="test", function=test_function)
    new_step2 = Plan(name="test", function=test_function2)
    plan.add_steps([new_step, new_step2])
    result = await plan.invoke(kernel, KernelArguments(input="hello world "))
    assert str(result) == "HELLO WORLD"


@pytest.mark.asyncio
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
async def test_invoke_multi_step_plan_with_arguments(kernel: Kernel):
    # import test (text) plugin
    kernel.add_plugin(MathPlugin(), "math")
    test_function = kernel.get_function("math", "Add")
    test_function2 = kernel.get_function("math", "Subtract")

    plan = Plan(name="test")

    new_step = Plan(
        name="test", function=test_function, parameters=KernelArguments(amount=10)
    )
    new_step2 = Plan(
        name="test", function=test_function2, parameters=KernelArguments(amount=5)
    )
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
=======
async def test_invoke_multi_step_plan_with_arguments():
    # create a kernel
    kernel = sk.Kernel()

    # import test (text) plugin
    plugin = MathPlugin()
    plugin = kernel.import_plugin(plugin, "math")
    test_function = plugin["Add"]
    test_function2 = plugin["Subtract"]

    plan = Plan(name="test")

    new_step = Plan(name="test", function=test_function, parameters=KernelArguments(amount=10))
    new_step2 = Plan(name="test", function=test_function2, parameters=KernelArguments(amount=5))
>>>>>>> f40c1f2075e2443c31c57c34f5f66c2711a8db75
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes

    plan.add_steps([new_step, new_step2])
    result = await plan.invoke(kernel, KernelArguments(input=2))
    assert str(result) == "7"
