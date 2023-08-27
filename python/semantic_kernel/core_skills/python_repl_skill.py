# Copyright (c) Microsoft. All rights reserved.

import ast
import re
from contextlib import redirect_stdout
from io import StringIO
from typing import TYPE_CHECKING

from semantic_kernel.sk_pydantic import PydanticField
from semantic_kernel.skill_definition import sk_function, sk_function_context_parameter

if TYPE_CHECKING:
    from semantic_kernel.orchestration.sk_context import SKContext


def reindent_code_block(code_block: str) -> str:
    """Reindents a code block."""
    lines = code_block.split("\n")
    # Remove leading and trailing empty lines
    lines = [line for line in lines if line.strip()]
    # Get the minimum leading whitespace for non-empty lines
    min_indent = min(
        len(re.match(r"^(\s*)", line).group(1)) for line in lines if line.strip()
    )
    # Dedent each line
    dedented = [line[min_indent:] for line in lines]
    return "\n".join(dedented)


def sanitize_input(query: str) -> str:
    pattern = r"```python\n(.*?)\n\s*```"
    code_block = re.search(pattern, query, re.DOTALL).group(1)
    code_block = reindent_code_block(code_block)
    return code_block


class PythonREPLSkill(PydanticField):
    """
    A skill that provides Python code execution functionality within a restricted environment.

    Usage:
        kernel.import_skill(PythonREPLSkill(), "pyrepl")
    """

    @sk_function(
        description="Run python code encapsulated in a specific pattern (```python ... ```).",
        name="runPythonREPL",
    )
    @sk_function_context_parameter(
        name="include_stdout",
        description="Include the standard output of the Python code execution as final REPL output.",
        default_value=False,
    )
    async def run_python_repl(self, query: str, context: "SKContext" = None) -> str:
        """
        Parses and executes the Python code provided within a given string query.
        The code must be encapsulated within a specific pattern (```python ... ```).

        params:
            query: A string that encapsulates the Python code to be executed.

        returns:
            The output of the Python code execution as a string.

        Exceptions:
            Raises ValueError if no valid Python code block is found or if the provided code has syntax errors.
        """
        if context is not None:
            _, include_stdout = context.variables.get("include_stdout")
            assert isinstance(include_stdout, bool)
        else:
            include_stdout = False

        __globals = {}

        try:
            query = sanitize_input(query)
        except AttributeError:
            raise ValueError("Couldn't find python code block.")

        try:
            tree = ast.parse(query)
        except SyntaxError:
            raise ValueError("Invalid python code.")

        module = ast.Module(tree.body[:-1], type_ignores=[])
        exec(ast.unparse(module), __globals)

        # execute last line of the code
        module_end = ast.Module(tree.body[-1:], type_ignores=[])
        module_end_str = ast.unparse(module_end)

        io_buffer = StringIO()

        # TODO(joowon-dm-snu): Execution of the code should be done in a separate thread/process
        #      1) to avoid blocking the main thread.
        #      2) to avoid the possibility of malicious code execution. -> separate process is better but complicated.
        #      3) to avoid the possibility of code execution that takes too long. -> Add timeout.
        try:
            with redirect_stdout(io_buffer):
                ret = eval(module_end_str, __globals)
                if ret is None:
                    return io_buffer.getvalue()
                else:
                    ret = str(ret)
                    if include_stdout:
                        ret = io_buffer.getvalue() + "\n" + ret
                    return ret

        except Exception:
            with redirect_stdout(io_buffer):
                exec(module_end_str, __globals)
            return io_buffer.getvalue()
