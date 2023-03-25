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
