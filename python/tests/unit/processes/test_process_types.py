# Copyright (c) Microsoft. All rights reserved.

from typing import TypeVar
from unittest.mock import patch

from semantic_kernel.processes.process_types import get_generic_state_type


# Test classes for various scenarios
class ConcreteState:
    pass


class ConcreteKernelProcessStep:
    state: ConcreteState


class OptionalStateKernelProcessStep:
    state: ConcreteState | None


class OptionalStateKernelProcessStepOldSyntax:
    state: ConcreteState | None


TState = TypeVar("TState")


class TypeVarStateKernelProcessStep:
    state: TState


class NoStateKernelProcessStep:
    pass


class InheritedKernelProcessStep(ConcreteKernelProcessStep):
    pass


def test_get_generic_state_type_concrete():
    result = get_generic_state_type(ConcreteKernelProcessStep)
    assert result is ConcreteState


def test_get_generic_state_type_optional():
    result = get_generic_state_type(OptionalStateKernelProcessStep)
    assert result is ConcreteState


def test_get_generic_state_type_optional_old_syntax():
    result = get_generic_state_type(OptionalStateKernelProcessStepOldSyntax)
    assert result is ConcreteState


def test_get_generic_state_type_typevar():
    result = get_generic_state_type(TypeVarStateKernelProcessStep)
    assert result is None


def test_get_generic_state_type_no_state():
    result = get_generic_state_type(NoStateKernelProcessStep)
    assert result is None


def test_get_generic_state_type_inherited():
    result = get_generic_state_type(InheritedKernelProcessStep)
    assert result is ConcreteState


def test_get_generic_state_type_exception():
    with patch("semantic_kernel.processes.process_types.get_type_hints", side_effect=Exception("Mocked exception")):
        result = get_generic_state_type(ConcreteKernelProcessStep)
        assert result is None
