# Copyright (c) Microsoft. All rights reserved.


import pytest
from semantic_kernel import Kernel
from semantic_kernel.kernel_exception import KernelException
from semantic_kernel.orchestration.sk_function_base import SKFunctionBase
from semantic_kernel.skill_definition.sk_function_decorator import sk_function
from semantic_kernel.skill_definition.skill_collection import SkillCollection


def not_decorated_native_function(arg1: str) -> str:
    return "test"


@sk_function(name="getLightStatus")
def decorated_native_function(arg1: str) -> str:
    return "test"


def test_register_valid_native_function():
    kernel = Kernel()

    registered_func = kernel.register_native_function(
        "TestSkill", decorated_native_function
    )

    assert isinstance(registered_func, SKFunctionBase)
    assert (
        kernel.skills.get_native_function("TestSkill", "getLightStatus")
        == registered_func
    )
    assert registered_func.invoke("testtest").result == "test"


def test_register_undecorated_native_function():
    kernel = Kernel()

    with pytest.raises(KernelException):
        kernel.register_native_function("TestSkill", not_decorated_native_function)


def test_register_with_none_skill_name():
    kernel = Kernel()

    registered_func = kernel.register_native_function(None, decorated_native_function)
    # Assumption here is that the GLOBAL_SKILL constant is set to "global" or similar.
    assert registered_func.skill_name == SkillCollection.GLOBAL_SKILL


def test_register_overloaded_native_function():
    kernel = Kernel()

    kernel.register_native_function("TestSkill", decorated_native_function)

    with pytest.raises(KernelException):
        kernel.register_native_function("TestSkill", decorated_native_function)


if __name__ == "__main__":
    pytest.main([__file__])
