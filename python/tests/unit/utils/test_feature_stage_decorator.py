# Copyright (c) Microsoft. All rights reserved.

from semantic_kernel.utils.feature_stage_decorator import experimental, release_candidate


@experimental
def my_function() -> None:
    """This is a sample function docstring."""
    pass


@release_candidate
def my_function_release_candidate() -> None:
    """This is a sample function docstring."""
    pass


@release_candidate
def my_function_release_candidate_no_doc_string() -> None:
    pass


@release_candidate(version="1.0.0-rc2")
def my_function_release_candidate_with_version() -> None:
    """This is a sample function docstring."""
    pass


@experimental
def my_function_no_doc_string() -> None:
    pass


@experimental
class MyExperimentalClass:
    """A class that is still evolving rapidly."""

    pass


@release_candidate
class MyRCClass:
    """A class that is nearly final, but still in release-candidate stage."""

    pass


@release_candidate(version="1.0.0-rc2")
class MyRCClassTwo:
    """A class that is nearly final, but still in release-candidate stage."""

    pass


def test_function_experimental_decorator():
    assert (
        my_function.__doc__
        == "This is a sample function docstring.\n\nNote: This function is marked as 'experimental' and may change in the future."  # noqa: E501
    )
    assert hasattr(my_function, "is_experimental")
    assert my_function.is_experimental is True


def test_function_experimental_decorator_with_no_doc_string():
    assert (
        my_function_no_doc_string.__doc__
        == "Note: This function is marked as 'experimental' and may change in the future."
    )
    assert hasattr(my_function_no_doc_string, "is_experimental")
    assert my_function_no_doc_string.is_experimental is True


def test_function_release_candidate_decorator():
    assert (
        "Features marked with this status are nearing completion and are considered"
        in my_function_release_candidate_no_doc_string.__doc__
    )
    assert hasattr(my_function_release_candidate, "is_release_candidate")
    assert my_function_release_candidate.is_release_candidate is True
    assert "Version:" in my_function_release_candidate_no_doc_string.__doc__


def test_function_release_candidate_decorator_and_version():
    assert (
        "Features marked with this status are nearing completion and are considered"
        in my_function_release_candidate_with_version.__doc__
    )
    assert hasattr(my_function_release_candidate, "is_release_candidate")
    assert my_function_release_candidate.is_release_candidate is True
    assert "Version:" in my_function_release_candidate_with_version.__doc__


def test_function_release_candidate_decorator_with_no_doc_string():
    assert (
        "Features marked with this status are nearing completion" in my_function_release_candidate_no_doc_string.__doc__
    )
    assert hasattr(my_function_release_candidate_no_doc_string, "is_release_candidate")
    assert my_function_release_candidate_no_doc_string.is_release_candidate is True
    assert "Version:" in my_function_release_candidate_no_doc_string.__doc__


def test_class_experimental_decorator():
    assert MyExperimentalClass.__doc__ == (
        "A class that is still evolving rapidly.\n\nNote: This class is marked as "
        "'experimental' and may change in the future."
    )
    assert hasattr(MyExperimentalClass, "is_experimental")
    assert MyExperimentalClass.is_experimental is True


def test_class_release_candidate_decorator():
    assert "Features marked with this status are nearing completion" in MyRCClass.__doc__
    assert hasattr(MyRCClass, "is_release_candidate")
    assert MyRCClass.is_release_candidate is True
    assert "Version:" in MyRCClass.__doc__


def test_class_release_candidate_decorator_with_version():
    assert "Features marked with this status are nearing completion" in MyRCClassTwo.__doc__
    expected_version = "1.0.0-rc2"
    assert expected_version in MyRCClassTwo.__doc__
    assert hasattr(MyRCClassTwo, "is_release_candidate")
    assert MyRCClassTwo.is_release_candidate is True
    assert "Version:" in MyRCClassTwo.__doc__
