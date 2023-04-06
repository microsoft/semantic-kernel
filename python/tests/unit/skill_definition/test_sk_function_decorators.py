# Copyright (c) Microsoft. All rights reserved.

from pytest import fixture, mark

from semantic_kernel.skill_definition import sk_function


class MiscClass:
    __test__ = False

    @sk_function(description="description")
    def func_with_description(self, input):
        return input

    @sk_function(description="description")
    def func_no_name(self, input):
        return input

    @sk_function(description="description", name="my-name")
    def func_with_name(self, input):
        return input

    @sk_function()
    def doc_string_test_1(self):
        """
        A multi-line
        docstring.
        """

    @sk_function()
    def doc_string_test_2(self):
        """This is a
        multi-line docstring
        too"""

    @sk_function()
    def doc_string_test_3(self):
        """This is a single-line docstring."""

    @sk_function()
    def doc_string_test_4(self):
        """
        This is a single-line docstring.
        """

    @sk_function()
    def doc_string_test_5(self):
        """Forms a complex number

        Keyword arguments:
        real -- the real part (default 0.0)
        imag -- the imaginary part (default 0.0)
        """

    @sk_function()
    def doc_string_test_6(self):
        """
        Forms a complex number

        Here's an example:
        >>> complex(2, 3)
        (2+3j)

        Keyword arguments:
        real -- the real part (default 0.0)
        imag -- the imaginary part (default 0.0)
        """

    @sk_function()
    def doc_string_test_7(self):
        pass

    @sk_function()
    def doc_string_test_8(self):
        """"""

    @sk_function()
    def doc_string_test_9(self):
        """ """

    @sk_function()
    def doc_string_test_10(self):
        """

        What if I have a leading empty line?
        """

    @sk_function()
    def doc_string_test_11(self):
        """

        What about this
        sort of
          construct
            it's like

        a poem (but shouldn't include this)

        """


@fixture
def decorator_test():
    return MiscClass()


@mark.parametrize(
    "func_name, expected",
    [
        ("func_with_description", "description"),
        ("doc_string_test_1", "A multi-line docstring."),
        ("doc_string_test_2", "This is a multi-line docstring too"),
        ("doc_string_test_3", "This is a single-line docstring."),
        ("doc_string_test_4", "This is a single-line docstring."),
        ("doc_string_test_5", "Forms a complex number"),
        ("doc_string_test_6", "Forms a complex number"),
        ("doc_string_test_7", ""),
        ("doc_string_test_8", ""),
        ("doc_string_test_9", ""),
        ("doc_string_test_10", "What if I have a leading empty line?"),
        ("doc_string_test_11", "What about this sort of construct it's like"),
    ],
)
def test_description(decorator_test, func_name, expected):
    my_func = getattr(decorator_test, func_name)
    assert my_func.__sk_function_description__ == expected


@mark.parametrize(
    "func_name, expected",
    [
        ("func_no_name", "func_no_name"),
        ("func_with_name", "my-name"),
    ],
)
def test_sk_function_name(decorator_test, func_name, expected):
    my_func = getattr(decorator_test, func_name)
    assert my_func.__sk_function_name__ == expected
