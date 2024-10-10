# Copyright (c) Microsoft. All rights reserved.

import logging

from pytest import mark, raises

<<<<<<< Updated upstream
<<<<<<< head
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
=======
>>>>>>> Stashed changes
<<<<<<< main
=======
<<<<<<< main
>>>>>>> origin/main
<<<<<<< Updated upstream
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
=======
<<<<<<< main
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
from semantic_kernel.exceptions import VarBlockSyntaxError
from semantic_kernel.exceptions.template_engine_exceptions import VarBlockRenderError
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.kernel import Kernel
<<<<<<< Updated upstream
<<<<<<< head
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
<<<<<<< main
=======
=======
>>>>>>> origin/main
=======
=======
<<<<<<< main
=======
=======
>>>>>>> Stashed changes
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.kernel import Kernel
from semantic_kernel.template_engine.blocks.block_errors import VarBlockSyntaxError
>>>>>>> ms/small_fixes
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> origin/main
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
=======
=======
>>>>>>> Stashed changes
>>>>>>> origin/main
from semantic_kernel.template_engine.blocks.block_types import BlockTypes
from semantic_kernel.template_engine.blocks.var_block import VarBlock

logger = logging.getLogger(__name__)


def test_init():
    var_block = VarBlock(content="$test_var")
    assert var_block.content == "$test_var"
    assert var_block.name == "test_var"
    assert var_block.type == BlockTypes.VARIABLE


def test_it_trims_spaces():
    assert VarBlock(content="  $x  ").content == "$x"


@mark.parametrize(
    "name",
    [
        "0",
        "1",
        "a",
        "_",
        "01",
        "01a",
        "a01",
        "_0",
        "a01_e",
        "_a01e",
    ],
)
def test_valid_syntax(name):
    target = VarBlock(content=f" ${name} ")
    result = target.render(Kernel(), KernelArguments(**{name: "value"}))
    assert target.name == name
    assert result == "value"


@mark.parametrize(
    "content",
    ["$", "$test-var", "test_var", "$a>b", "$."],
<<<<<<< Updated upstream
<<<<<<< head
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
=======
>>>>>>> Stashed changes
<<<<<<< main
=======
<<<<<<< main
>>>>>>> origin/main
<<<<<<< Updated upstream
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
=======
<<<<<<< main
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
    ids=[
        "prefix_only",
        "invalid_characters",
        "no_prefix",
        "invalid_characters2",
        "invalid_characters3",
    ],
)
def test_syntax_errors(content):
    match = content.replace("$", "\\$") if "$" in content else content
<<<<<<< Updated upstream
<<<<<<< head
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
<<<<<<< main
=======
=======
>>>>>>> origin/main
=======
=======
<<<<<<< main
=======
=======
>>>>>>> Stashed changes
    ids=["prefix_only", "invalid_characters", "no_prefix", "invalid_characters2", "invalid_characters3"],
)
def test_syntax_errors(content):
    if "$" in content:
        match = content.replace("$", r"\$")
    else:
        match = content
>>>>>>> ms/small_fixes
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> origin/main
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
=======
=======
>>>>>>> Stashed changes
>>>>>>> origin/main
    with raises(VarBlockSyntaxError, match=rf".*{match}.*"):
        VarBlock(content=content)


def test_render():
    var_block = VarBlock(content="$test_var")
    rendered_value = var_block.render(Kernel(), KernelArguments(test_var="test_value"))
    assert rendered_value == "test_value"


def test_render_variable_not_found():
    var_block = VarBlock(content="$test_var")
    rendered_value = var_block.render(Kernel(), KernelArguments())
    assert rendered_value == ""


def test_render_no_args():
    target = VarBlock(content="$var")
    result = target.render(Kernel())
    assert result == ""
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> origin/main
=======
<<<<<<< main
>>>>>>> Stashed changes


class MockNonString(str):
    def __str__(self):
        raise ValueError("This is not a string")


def test_not_string():
    target = VarBlock(content="$var")
    with raises(VarBlockRenderError):
        target.render(Kernel(), KernelArguments(var=MockNonString("1")))
<<<<<<< Updated upstream
<<<<<<< head
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
=======
>>>>>>> Stashed changes
<<<<<<< main
=======
=======
>>>>>>> ms/small_fixes
>>>>>>> origin/main
<<<<<<< Updated upstream
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
=======
=======
>>>>>>> ms/small_fixes
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
