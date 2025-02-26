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


@experimental
def my_function_no_doc_string() -> None:
    pass


def test_function_experimental_decorator() -> None:
    assert (
        my_function.__doc__
        == "This is a sample function docstring.\n\nNote: This function is 'experimental' and may change in the future."
    )
    assert hasattr(my_function, "is_experimental")
    assert my_function.is_experimental is True


def test_function_experimental_decorator_with_no_doc_string() -> None:
    assert my_function_no_doc_string.__doc__ == "Note: This function is 'experimental' and may change in the future."
    assert hasattr(my_function_no_doc_string, "is_experimental")
    assert my_function_no_doc_string.is_experimental is True


def test_function_release_candidate_decorator() -> None:
    assert (
        my_function_release_candidate.__doc__
        == "This is a sample function docstring.\n\nNote: This function is a release candidate and may change in the future."
    )
    assert hasattr(my_function_release_candidate, "is_release_candidate")
    assert my_function_release_candidate.is_release_candidate is True


def test_function_release_candidate_decorator_with_no_doc_string() -> None:
    assert (
        my_function_release_candidate_no_doc_string.__doc__
        == "Note: This function is a release candidate and may change in the future."
    )
    assert hasattr(my_function_release_candidate_no_doc_string, "is_release_candidate")
    assert my_function_release_candidate_no_doc_string.is_release_candidate is True
