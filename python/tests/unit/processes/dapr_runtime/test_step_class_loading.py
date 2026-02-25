# Copyright (c) Microsoft. All rights reserved.

import pytest

from semantic_kernel.exceptions.process_exceptions import ProcessInvalidConfigurationException
from semantic_kernel.processes.kernel_process.kernel_process_step import KernelProcessStep
from semantic_kernel.processes.step_utils import get_step_class_from_qualified_name


class MockValidStep(KernelProcessStep):
    """A valid KernelProcessStep subclass for testing."""

    pass


class NotAStep:
    """A class that is NOT a KernelProcessStep subclass."""

    pass


def test_valid_step_class_loads_successfully():
    """Test that a valid KernelProcessStep subclass loads correctly."""
    full_name = f"{MockValidStep.__module__}.{MockValidStep.__name__}"
    result = get_step_class_from_qualified_name(
        full_name,
        allowed_module_prefixes=[MockValidStep.__module__],
    )
    assert result is MockValidStep
    assert issubclass(result, KernelProcessStep)


def test_invalid_format_no_dots_raises_exception():
    """Test that a class name without dots raises ProcessInvalidConfigurationException."""
    with pytest.raises(ProcessInvalidConfigurationException, match="Invalid step class name format"):
        get_step_class_from_qualified_name("NoDots")


def test_empty_module_name_raises_exception():
    """Test that empty module name (e.g., '.ClassName') raises ProcessInvalidConfigurationException."""
    with pytest.raises(ProcessInvalidConfigurationException, match="Module name and class name cannot be empty"):
        get_step_class_from_qualified_name(".ClassName")


def test_empty_class_name_raises_exception():
    """Test that empty class name (e.g., 'module.') raises ProcessInvalidConfigurationException."""
    with pytest.raises(ProcessInvalidConfigurationException, match="Module name and class name cannot be empty"):
        get_step_class_from_qualified_name("module.")


def test_empty_string_raises_exception():
    """Test that an empty string raises ProcessInvalidConfigurationException."""
    with pytest.raises(ProcessInvalidConfigurationException, match="Invalid step class name format"):
        get_step_class_from_qualified_name("")


def test_none_like_empty_raises_exception():
    """Test that None-like values raise ProcessInvalidConfigurationException."""
    with pytest.raises(ProcessInvalidConfigurationException, match="Invalid step class name format"):
        get_step_class_from_qualified_name(None)  # type: ignore


def test_nonexistent_module_raises_exception():
    """Test that a non-existent module raises ProcessInvalidConfigurationException."""
    with pytest.raises(ProcessInvalidConfigurationException, match="Unable to import module"):
        get_step_class_from_qualified_name("nonexistent_module_xyz123.SomeClass", allowed_module_prefixes=None)


def test_nonexistent_class_in_valid_module_raises_exception():
    """Test that a non-existent class in a valid module raises ProcessInvalidConfigurationException."""
    with pytest.raises(ProcessInvalidConfigurationException, match="not found in module"):
        get_step_class_from_qualified_name("semantic_kernel.kernel.NonExistentClass12345")


def test_non_class_attribute_raises_exception():
    """Test that loading a non-class attribute (function) raises ProcessInvalidConfigurationException."""
    with pytest.raises(ProcessInvalidConfigurationException, match="is not a class type"):
        get_step_class_from_qualified_name("semantic_kernel.processes.step_utils.get_fully_qualified_name")


def test_non_step_class_raises_exception():
    """Test that a class not inheriting from KernelProcessStep raises exception."""
    full_name = f"{NotAStep.__module__}.{NotAStep.__name__}"
    with pytest.raises(ProcessInvalidConfigurationException, match="must be a subclass of KernelProcessStep"):
        get_step_class_from_qualified_name(full_name, allowed_module_prefixes=[NotAStep.__module__])


def test_builtin_class_raises_exception():
    """Test that built-in classes like str raise exception (bypassing prefix check to test subclass validation)."""
    with pytest.raises(ProcessInvalidConfigurationException, match="must be a subclass of KernelProcessStep"):
        get_step_class_from_qualified_name("builtins.str", allowed_module_prefixes=None)


def test_os_system_prevented():
    """Test that os.system is prevented (bypassing prefix check to test type validation)."""
    with pytest.raises(ProcessInvalidConfigurationException, match="is not a class type"):
        get_step_class_from_qualified_name("os.system", allowed_module_prefixes=None)


def test_arbitrary_class_prevented():
    """Test that arbitrary classes like subprocess.Popen are prevented (bypassing prefix check)."""
    with pytest.raises(ProcessInvalidConfigurationException, match="must be a subclass of KernelProcessStep"):
        get_step_class_from_qualified_name("subprocess.Popen", allowed_module_prefixes=None)


def test_kernel_class_prevented():
    """Test that even internal SK classes that aren't steps are prevented."""
    with pytest.raises(ProcessInvalidConfigurationException, match="must be a subclass of KernelProcessStep"):
        get_step_class_from_qualified_name("semantic_kernel.kernel.Kernel")


# Module allowlist tests


def test_allowlist_permits_valid_module():
    """Test that a valid step class from an allowed module loads successfully."""
    full_name = f"{MockValidStep.__module__}.{MockValidStep.__name__}"
    # Allow the test module (use actual module name from __module__)
    module_prefix = MockValidStep.__module__
    result = get_step_class_from_qualified_name(
        full_name,
        allowed_module_prefixes=[module_prefix],
    )
    assert result is MockValidStep


def test_allowlist_blocks_disallowed_module():
    """Test that a module not in the allowlist is blocked BEFORE import."""
    with pytest.raises(ProcessInvalidConfigurationException, match="is not in the allowed module prefixes"):
        get_step_class_from_qualified_name(
            "os.path",
            allowed_module_prefixes=["semantic_kernel.", "myapp."],
        )


def test_allowlist_blocks_dangerous_module():
    """Test that dangerous modules are blocked when allowlist is provided."""
    with pytest.raises(ProcessInvalidConfigurationException, match="is not in the allowed module prefixes"):
        get_step_class_from_qualified_name(
            "subprocess.Popen",
            allowed_module_prefixes=["semantic_kernel."],
        )


def test_empty_allowlist_allows_all():
    """Test that an empty allowlist allows any module."""
    full_name = f"{MockValidStep.__module__}.{MockValidStep.__name__}"
    result = get_step_class_from_qualified_name(full_name, allowed_module_prefixes=[])
    assert result is MockValidStep


def test_none_allowlist_allows_all():
    """Test that None allowlist allows any module (explicit opt-out)."""
    full_name = f"{MockValidStep.__module__}.{MockValidStep.__name__}"
    result = get_step_class_from_qualified_name(full_name, allowed_module_prefixes=None)
    assert result is MockValidStep


def test_default_allowlist_blocks_non_sk_modules():
    """Test that the default allowlist only permits semantic_kernel modules."""
    with pytest.raises(ProcessInvalidConfigurationException, match="is not in the allowed module prefixes"):
        get_step_class_from_qualified_name("subprocess.Popen")


def test_default_allowlist_permits_sk_modules():
    """Test that the default allowlist permits semantic_kernel modules."""
    full_name = "semantic_kernel.processes.kernel_process.kernel_process_step.KernelProcessStep"
    result = get_step_class_from_qualified_name(full_name)
    assert result is KernelProcessStep


def test_allowlist_prefix_matching():
    """Test that allowlist uses prefix matching correctly."""
    full_name = f"{MockValidStep.__module__}.{MockValidStep.__name__}"
    # Use a prefix of the actual module name
    module_prefix = MockValidStep.__module__[:4]  # First 4 chars as prefix
    result = get_step_class_from_qualified_name(
        full_name,
        allowed_module_prefixes=[module_prefix],
    )
    assert result is MockValidStep


def test_allowlist_multiple_prefixes():
    """Test that multiple allowed prefixes work correctly."""
    full_name = f"{MockValidStep.__module__}.{MockValidStep.__name__}"
    module_prefix = MockValidStep.__module__
    result = get_step_class_from_qualified_name(
        full_name,
        allowed_module_prefixes=["semantic_kernel.", "myapp.", module_prefix],
    )
    assert result is MockValidStep
