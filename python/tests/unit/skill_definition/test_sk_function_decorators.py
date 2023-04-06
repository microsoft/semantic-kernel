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


def test_description():
    decorator_test = MiscClass()
    my_func = getattr(decorator_test, "func_with_description")
    assert my_func.__sk_function_description__ == "description"


def test_sk_function_name_not_specified():
    decorator_test = MiscClass()
    my_func = getattr(decorator_test, "func_no_name")
    assert my_func.__sk_function_name__ == "func_no_name"


def test_sk_function_with_name_specified():
    decorator_test = MiscClass()
    my_func = getattr(decorator_test, "func_with_name")
    assert my_func.__sk_function_name__ == "my-name"


def test_doc_string_test_1():
    decorator_test = MiscClass()
    my_func = getattr(decorator_test, "doc_string_test_1")
    assert my_func.__sk_function_description__ == "A multi-line docstring."


def test_doc_string_test_2():
    decorator_test = MiscClass()
    my_func = getattr(decorator_test, "doc_string_test_2")
    assert my_func.__sk_function_description__ == "This is a multi-line docstring too"


def test_doc_string_test_3():
    decorator_test = MiscClass()
    my_func = getattr(decorator_test, "doc_string_test_3")
    assert my_func.__sk_function_description__ == "This is a single-line docstring."


def test_doc_string_test_4():
    decorator_test = MiscClass()
    my_func = getattr(decorator_test, "doc_string_test_4")
    assert my_func.__sk_function_description__ == "This is a single-line docstring."


def test_doc_string_test_5():
    decorator_test = MiscClass()
    my_func = getattr(decorator_test, "doc_string_test_5")
    assert my_func.__sk_function_description__ == "Forms a complex number"


def test_doc_string_test_6():
    decorator_test = MiscClass()
    my_func = getattr(decorator_test, "doc_string_test_6")
    assert my_func.__sk_function_description__ == "Forms a complex number"


def test_doc_string_test_7():
    decorator_test = MiscClass()
    my_func = getattr(decorator_test, "doc_string_test_7")
    assert my_func.__sk_function_description__ == ""


def test_doc_string_test_8():
    decorator_test = MiscClass()
    my_func = getattr(decorator_test, "doc_string_test_8")
    assert my_func.__sk_function_description__ == ""


def test_doc_string_test_9():
    decorator_test = MiscClass()
    my_func = getattr(decorator_test, "doc_string_test_9")
    assert my_func.__sk_function_description__ == ""


def test_doc_string_test_10():
    decorator_test = MiscClass()
    my_func = getattr(decorator_test, "doc_string_test_10")
    assert my_func.__sk_function_description__ == "What if I have a leading empty line?"


def test_doc_string_test_11():
    decorator_test = MiscClass()
    my_func = getattr(decorator_test, "doc_string_test_11")
    assert (
        my_func.__sk_function_description__
        == "What about this sort of construct it's like"
    )
