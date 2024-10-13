# Copyright (c) Microsoft. All rights reserved.

import logging

from pytest import mark, raises

<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
from semantic_kernel.exceptions import NamedArgBlockSyntaxError
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.kernel import Kernel
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
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
<<<<<<< HEAD
from semantic_kernel.exceptions import NamedArgBlockSyntaxError
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.kernel import Kernel
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> head
<<<<<<< HEAD
from semantic_kernel.exceptions import NamedArgBlockSyntaxError
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.kernel import Kernel
=======
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.kernel import Kernel
from semantic_kernel.template_engine.blocks.block_errors import NamedArgBlockSyntaxError
>>>>>>> f40c1f2075e2443c31c57c34f5f66c2711a8db75
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< HEAD
>>>>>>> main
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
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head
from semantic_kernel.template_engine.blocks.block_types import BlockTypes
from semantic_kernel.template_engine.blocks.named_arg_block import NamedArgBlock
from semantic_kernel.template_engine.blocks.val_block import ValBlock
from semantic_kernel.template_engine.blocks.var_block import VarBlock

logger = logging.getLogger(__name__)


def test_init_with_var():
    named_arg_block = NamedArgBlock(content="test=$test_var")
    assert named_arg_block.content == "test=$test_var"
    assert named_arg_block.name == "test"
    assert named_arg_block.variable.name == "test_var"
    assert isinstance(named_arg_block.variable, VarBlock)


def test_init_with_val():
    named_arg_block = NamedArgBlock(content="test='test_val'")
    assert named_arg_block.content == "test='test_val'"
    assert named_arg_block.name == "test"
    assert named_arg_block.value.value == "test_val"
    assert isinstance(named_arg_block.value, ValBlock)


def test_type_property():
    named_arg_block = NamedArgBlock(content="test=$test_var")
    assert named_arg_block.type == BlockTypes.NAMED_ARG


@mark.parametrize(
    "content",
    [
        "=$test_var",
        "test=$test-var",
        "test='test_val\"",
        "test=''",
        "test=$",
    ],
    ids=["no_name", "invalid_var", "invalid_val", "empty_val", "empty_var"],
)
def test_syntax_error(content):
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
    match = content.replace("$", "\\$") if "$" in content else content
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
<<<<<<< HEAD
    match = content.replace("$", "\\$") if "$" in content else content
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
    match = content.replace("$", "\\$") if "$" in content else content
=======
>>>>>>> Stashed changes
=======
    match = content.replace("$", "\\$") if "$" in content else content
=======
>>>>>>> Stashed changes
>>>>>>> head
<<<<<<< HEAD
    match = content.replace("$", "\\$") if "$" in content else content
=======
    if "$" in content:
        match = content.replace("$", r"\$")
    else:
        match = content
>>>>>>> f40c1f2075e2443c31c57c34f5f66c2711a8db75
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< HEAD
>>>>>>> main
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
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head
    with raises(NamedArgBlockSyntaxError, match=rf".*{match}.*"):
        NamedArgBlock(content=content)


def test_render():
    named_arg_block = NamedArgBlock(content="test=$test_var")
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
    rendered_value = named_arg_block.render(
        Kernel(), KernelArguments(test_var="test_value")
    )
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
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
<<<<<<< HEAD
    rendered_value = named_arg_block.render(
        Kernel(), KernelArguments(test_var="test_value")
    )
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> head
<<<<<<< HEAD
    rendered_value = named_arg_block.render(
        Kernel(), KernelArguments(test_var="test_value")
    )
=======
    rendered_value = named_arg_block.render(Kernel(), KernelArguments(test_var="test_value"))
>>>>>>> f40c1f2075e2443c31c57c34f5f66c2711a8db75
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< HEAD
>>>>>>> main
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
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head
    assert rendered_value == "test_value"


def test_render_variable_not_found():
    named_arg_block = NamedArgBlock(content="test=$test_var")
    rendered_value = named_arg_block.render(Kernel(), KernelArguments())
    assert rendered_value == ""


def test_init_minimal_var():
    block = NamedArgBlock(content="a=$a")
    assert block.name == "a"
    assert block.variable.name == "a"


def test_init_minimal_val():
    block = NamedArgBlock(content="a='a'")
    assert block.name == "a"
    assert block.value.value == "a"


def test_init_empty():
    with raises(NamedArgBlockSyntaxError, match=r".*"):
        NamedArgBlock(content="")


def test_it_trims_spaces():
    assert NamedArgBlock(content="  a=$x  ").content == "a=$x"


def test_it_ignores_spaces_around():
    target = NamedArgBlock(content="  a=$var \n ")
    assert target.content == "a=$var"


def test_it_renders_to_empty_string_without_variables():
    target = NamedArgBlock(content="  a=$var \n ")
    result = target.render(Kernel(), None)
    assert result == ""


def test_it_renders_to_empty_string_if_variable_is_missing():
    target = NamedArgBlock(content="  a=$var \n ")
    result = target.render(Kernel(), KernelArguments(foo="bar"))
    assert result == ""


def test_it_renders_to_variable_value_when_available():
    target = NamedArgBlock(content="  a=$var \n ")
    result = target.render(Kernel(), KernelArguments(foo="bar", var="able"))
    assert result == "able"


def test_it_renders_to_value():
    target = NamedArgBlock(content="  a='var' \n ")
    result = target.render(Kernel(), None)
    assert result == "var"
