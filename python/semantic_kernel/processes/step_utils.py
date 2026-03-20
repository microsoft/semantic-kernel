# Copyright (c) Microsoft. All rights reserved.

import importlib
import inspect
from collections.abc import Sequence
from typing import Any

from semantic_kernel.exceptions.process_exceptions import ProcessInvalidConfigurationException
from semantic_kernel.functions.kernel_function import KernelFunction
from semantic_kernel.processes.kernel_process.kernel_process_message_channel import KernelProcessMessageChannel
from semantic_kernel.processes.kernel_process.kernel_process_step import KernelProcessStep
from semantic_kernel.processes.kernel_process.kernel_process_step_context import KernelProcessStepContext
from semantic_kernel.utils.feature_stage_decorator import experimental


@experimental
def find_input_channels(
    channel: KernelProcessMessageChannel, functions: dict[str, KernelFunction]
) -> dict[str, dict[str, Any | None]]:
    """Finds and creates input channels."""
    if not functions:
        raise ValueError("The step has not been initialized.")

    inputs: dict[str, Any] = {}
    for name, function in functions.items():
        inputs[name] = {}
        for param in function.metadata.parameters:
            # Check for Kernel, and skip if necessary, since it is populated later on
            if param.type_ == "Kernel":
                continue
            if not param.is_required:
                continue
            if param.type_ == "KernelProcessStepContext":
                inputs[name][param.name] = KernelProcessStepContext(channel)
            else:
                inputs[name][param.name] = None

    return inputs


@experimental
def get_fully_qualified_name(cls) -> str:
    """Gets the fully qualified name of a class."""
    return f"{cls.__module__}.{cls.__name__}"


@experimental
def get_step_class_from_qualified_name(
    full_class_name: str,
    allowed_module_prefixes: Sequence[str] | None = None,
) -> type[KernelProcessStep]:
    """Loads and validates a KernelProcessStep class from a fully qualified name.

    This function validates that the loaded class is a proper subclass of
    KernelProcessStep, preventing instantiation of arbitrary classes.

    Args:
        full_class_name: The fully qualified class name in Python import notation
            (e.g., 'mypackage.mymodule.MyStep'). The module must be importable
            from the current Python environment.
        allowed_module_prefixes: Optional list of module prefixes that are allowed
            to be imported. If provided, the module must start with one of these
            prefixes. This check is performed BEFORE import to prevent execution
            of module-level code in unauthorized modules. If None or empty, any
            module is allowed.

    Returns:
        The validated class type that is a subclass of KernelProcessStep

    Raises:
        ProcessInvalidConfigurationException: Raised when:
            - The class name format is invalid (missing module separator)
            - The module is not in the allowed prefixes list (if provided)
            - The module cannot be imported
            - The class attribute doesn't exist in the module
            - The attribute is not a class type
            - The class is not a subclass of KernelProcessStep
    """
    if not full_class_name or "." not in full_class_name:
        raise ProcessInvalidConfigurationException(
            f"Invalid step class name format: '{full_class_name}'. "
            "Expected a fully qualified name like 'module.ClassName'."
        )

    module_name, class_name = full_class_name.rsplit(".", 1)

    if not module_name or not class_name:
        raise ProcessInvalidConfigurationException(
            f"Invalid step class name format: '{full_class_name}'. Module name and class name cannot be empty."
        )

    # Check module allowlist BEFORE import to prevent module-level code execution
    if allowed_module_prefixes and not any(module_name.startswith(prefix) for prefix in allowed_module_prefixes):
        raise ProcessInvalidConfigurationException(
            f"Module '{module_name}' is not in the allowed module prefixes: {allowed_module_prefixes}. "
            f"Step class '{full_class_name}' cannot be loaded."
        )

    try:
        module = importlib.import_module(module_name)
    except ImportError as e:
        raise ProcessInvalidConfigurationException(
            f"Unable to import module '{module_name}' for step class '{full_class_name}': {e}"
        ) from e

    try:
        cls = getattr(module, class_name)
    except AttributeError as e:
        raise ProcessInvalidConfigurationException(
            f"Class '{class_name}' not found in module '{module_name}': {e}"
        ) from e

    if not inspect.isclass(cls):
        raise ProcessInvalidConfigurationException(f"'{full_class_name}' is not a class type, got {type(cls).__name__}")

    if not issubclass(cls, KernelProcessStep):
        raise ProcessInvalidConfigurationException(
            f"Step class '{full_class_name}' must be a subclass of KernelProcessStep. Got: {cls.__bases__}"
        )

    return cls
