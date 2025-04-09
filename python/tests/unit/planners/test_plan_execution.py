# Copyright (c) Microsoft. All rights reserved.


from semantic_kernel.core_plugins.math_plugin import MathPlugin
from semantic_kernel.core_plugins.text_plugin import TextPlugin
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.kernel import Kernel
from semantic_kernel.planners import Plan


async def test_invoke_empty_plan(kernel: Kernel):
    plan = Plan()
    result = await plan.invoke(kernel)
    assert str(result) == ""


async def test_invoke_plan_constructed_with_function(kernel: Kernel):
    # import test (text) plugin
    kernel.add_plugin(TextPlugin(), "text")
    test_function = kernel.get_function("text", "uppercase")

    plan = Plan(name="test", function=test_function)
    result = await plan.invoke(kernel, KernelArguments(input="hello world "))
    assert str(result) == "HELLO WORLD "


async def test_invoke_empty_plan_with_added_function_step(kernel: Kernel):
    # import test (text) plugin
    kernel.add_plugin(TextPlugin(), "text")
    test_function = kernel.get_function("text", "uppercase")

    plan = Plan(name="test")
    plan.add_steps([test_function])
    result = await plan.invoke(kernel, KernelArguments(input="hello world "))
    print(result)
    assert str(result) == "HELLO WORLD "


async def test_invoke_empty_plan_with_added_plan_step(kernel: Kernel):
    # import test (text) plugin
    kernel.add_plugin(TextPlugin(), "text")
    test_function = kernel.get_function("text", "uppercase")

    plan = Plan(name="test")
    new_step = Plan(name="test", function=test_function)
    plan.add_steps([new_step])
    result = await plan.invoke(kernel, KernelArguments(input="hello world "))
    assert str(result) == "HELLO WORLD "


async def test_invoke_multi_step_plan(kernel: Kernel):
    # import test (text) plugin
    kernel.add_plugin(TextPlugin(), "text")
    test_function = kernel.get_function("text", "uppercase")
    test_function2 = kernel.get_function("text", "trim_end")

    plan = Plan(name="test")
    new_step = Plan(name="test", function=test_function)
    new_step2 = Plan(name="test", function=test_function2)
    plan.add_steps([new_step, new_step2])
    result = await plan.invoke(kernel, KernelArguments(input="hello world "))
    assert str(result) == "HELLO WORLD"


async def test_invoke_multi_step_plan_with_arguments(kernel: Kernel):
    # import test (text) plugin
    kernel.add_plugin(MathPlugin(), "math")
    test_function = kernel.get_function("math", "Add")
    test_function2 = kernel.get_function("math", "Subtract")

    plan = Plan(name="test")

    new_step = Plan(name="test", function=test_function, parameters=KernelArguments(amount=10))
    new_step2 = Plan(name="test", function=test_function2, parameters=KernelArguments(amount=5))

    plan.add_steps([new_step, new_step2])
    result = await plan.invoke(kernel, KernelArguments(input=2))
    assert str(result) == "7"
