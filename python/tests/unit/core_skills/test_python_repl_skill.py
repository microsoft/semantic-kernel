# Copyright (c) Microsoft. All rights reserved.

import pytest
from semantic_kernel import Kernel
from semantic_kernel.core_skills import PythonREPLSkill


@pytest.mark.asyncio
async def test_it_can_be_instantiated():
    skill = PythonREPLSkill()
    assert skill is not None


@pytest.mark.asyncio
async def test_it_can_be_imported():
    kernel = Kernel()
    skill = PythonREPLSkill()
    assert kernel.import_skill(skill, "pyrepl")
    assert kernel.skills.has_native_function("pyrepl", "runPythonREPL")


@pytest.mark.asyncio
async def test_valid_code_execution():
    skill = PythonREPLSkill()
    response = await skill.run_python_repl(
        """
        ```python
        def fibonacci(n):
            if n <= 0:
                return 0
            elif n == 1:
                return 1
            else:
                return fibonacci(n-1) + fibonacci(n-2)
    
        fibonacci(10)
        ```
    """
    )
    assert response == "55"


@pytest.mark.asyncio
async def test_invalid_code():
    skill = PythonREPLSkill()
    with pytest.raises(ValueError):
        await skill.run_python_repl("x = 10\ny = 20\nx + y")


@pytest.mark.asyncio
async def test_syntax_error_code():
    skill = PythonREPLSkill()
    with pytest.raises(ValueError):
        await skill.run_python_repl(
            """
            ```python
            x = 10
            y = 20
            x + y z
            ```
        """
        )


@pytest.mark.asyncio
async def test_code_without_return():
    skill = PythonREPLSkill()
    response = await skill.run_python_repl(
        """
        ```python
        x = 10
        y = 20
        z = x + y
        ```
    """
    )
    assert response == ""


@pytest.mark.asyncio
async def test_code_with_stdout_in_function():
    kernel = Kernel()
    skill = PythonREPLSkill()
    context = kernel.create_new_context()
    context.variables.set("include_stdout", True)
    response = await skill.run_python_repl(
        """
        ```python
        def fibonacci(n):
            if n <= 0:
                return 0
            elif n == 1:
                return 1
            else:
                print(f"Run fibonacci({n}) => fibonacci({n-1}) + fibonacci({n-2})")
                return fibonacci(n-1) + fibonacci(n-2)
    
        fibonacci(3)
        ```
    """,
        context=context,
    )

    expected = "Run fibonacci(3) => fibonacci(2) + fibonacci(1)\nRun fibonacci(2) => fibonacci(1) + fibonacci(0)\n\n2"
    assert response == expected


if __name__ == "__main__":
    pytest.main(["-vv", "-s", __file__])
