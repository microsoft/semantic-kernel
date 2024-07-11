from semantic_kernel.orchestration.context_variables import ContextVariables


def test_context_vars_contain_single_var_by_default():
    context_vars = ContextVariables()
    assert context_vars.variables is not None
    assert len(context_vars.variables) == 1
    assert context_vars.variables["input"] == ""


def test_context_vars_can_be_constructed_with_string():
    content = "Hello, world!"
    context_vars = ContextVariables(content)
    assert context_vars.variables is not None
    assert len(context_vars.variables) == 1
    assert context_vars.variables["input"] == content


def test_context_vars_can_be_constructed_with_dict():
    variables = {"test_string": "Hello, world!"}
    context_vars = ContextVariables(variables=variables)
    assert context_vars.variables is not None
    assert len(context_vars.variables) == 2
    assert context_vars.variables["input"] == ""
    assert context_vars.variables["test_string"] == variables["test_string"]


def test_context_vars_can_be_constructed_with_string_and_dict():
    content = "I love muffins"
    variables = {"test_string": "Hello, world!"}
    context_vars = ContextVariables(content=content, variables=variables)
    assert context_vars.variables is not None
    assert len(context_vars.variables) == 2
    assert context_vars.variables["input"] == content
    assert context_vars.variables["test_string"] == variables["test_string"]


def test_merged_context_vars_with_empty_input_results_in_empty_input():
    content = "I love muffins"
    variables = {"test_string": "Hello, world!"}
    context_vars1 = ContextVariables(content=content)
    context_vars2 = ContextVariables(variables=variables)
    context_vars_combined_1with2 = context_vars1.merge_or_overwrite(context_vars2)
    context_vars_combined_2with1 = context_vars2.merge_or_overwrite(context_vars1)

    assert context_vars_combined_1with2.variables is not None
    assert len(context_vars_combined_1with2.variables) == 2
    assert context_vars_combined_1with2.variables["input"] == ""
    assert (
        context_vars_combined_1with2.variables["test_string"]
        == variables["test_string"]
    )

    assert context_vars_combined_2with1.variables is not None
    assert len(context_vars_combined_2with1.variables) == 2
    assert context_vars_combined_2with1.variables["input"] == ""
    assert (
        context_vars_combined_2with1.variables["test_string"]
        == variables["test_string"]
    )


def test_merged_context_vars_with_same_input_results_in_unchanged_input():
    content = "I love muffins"
    variables = {"test_string": "Hello, world!"}
    context_vars1 = ContextVariables(content=content)
    context_vars2 = ContextVariables(content=content, variables=variables)
    context_vars_combined_1with2 = context_vars1.merge_or_overwrite(context_vars2)
    context_vars_combined_2with1 = context_vars2.merge_or_overwrite(context_vars1)

    assert context_vars_combined_1with2.variables is not None
    assert len(context_vars_combined_1with2.variables) == 2
    assert context_vars_combined_1with2.variables["input"] == content
    assert (
        context_vars_combined_1with2.variables["test_string"]
        == variables["test_string"]
    )

    assert context_vars_combined_2with1.variables is not None
    assert len(context_vars_combined_2with1.variables) == 2
    assert context_vars_combined_2with1.variables["input"] == content
    assert (
        context_vars_combined_2with1.variables["test_string"]
        == variables["test_string"]
    )


def test_merged_context_vars_with_different_input_results_in_input_overwrite1():
    content = "I love muffins"
    content2 = "I love cupcakes"
    variables = {"test_string": "Hello, world!"}
    context_vars1 = ContextVariables(content=content)
    context_vars2 = ContextVariables(content=content2, variables=variables)
    context_vars_combined_1with2 = context_vars1.merge_or_overwrite(
        context_vars2, overwrite=False
    )

    assert context_vars_combined_1with2.variables is not None
    assert len(context_vars_combined_1with2.variables) == 2
    assert (
        context_vars_combined_1with2.variables["input"]
        == context_vars2.variables["input"]
    )
    assert (
        context_vars_combined_1with2.variables["test_string"]
        == context_vars2.variables["test_string"]
    )


def test_merged_context_vars_with_different_input_results_in_input_overwrite2():
    content = "I love muffins"
    content2 = "I love cupcakes"
    variables = {"test_string": "Hello, world!"}
    context_vars1 = ContextVariables(content=content)
    context_vars2 = ContextVariables(content=content2, variables=variables)
    context_vars_combined_2with1 = context_vars2.merge_or_overwrite(
        context_vars1, overwrite=False
    )

    assert context_vars_combined_2with1.variables is not None
    assert len(context_vars_combined_2with1.variables) == 2
    assert context_vars_combined_2with1.variables["input"] == context_vars1["input"]
    assert (
        context_vars_combined_2with1.variables["test_string"]
        == context_vars2.variables["test_string"]
    )


def test_can_overwrite_context_variables1():
    content = "I love muffins"
    content2 = "I love cupcakes"
    variables = {"test_string": "Hello, world!"}
    context_vars1 = ContextVariables(content=content)
    context_vars2 = ContextVariables(content=content2, variables=variables)
    context_vars_overwrite_1with2 = context_vars1.merge_or_overwrite(
        context_vars2, overwrite=True
    )

    assert context_vars_overwrite_1with2.variables is not None
    assert len(context_vars_overwrite_1with2.variables) == len(context_vars2.variables)
    assert (
        context_vars_overwrite_1with2.variables["input"]
        == context_vars2.variables["input"]
    )
    assert (
        context_vars_overwrite_1with2.variables["test_string"]
        == context_vars2["test_string"]
    )


def test_can_overwrite_context_variables2():
    content = "I love muffins"
    content2 = "I love cupcakes"
    variables = {"test_string": "Hello, world!"}
    context_vars1 = ContextVariables(content=content)
    context_vars2 = ContextVariables(content=content2, variables=variables)
    context_vars_overwrite_2with1 = context_vars2.merge_or_overwrite(
        context_vars1, overwrite=True
    )

    assert context_vars_overwrite_2with1.variables is not None
    assert len(context_vars_overwrite_2with1.variables) == len(context_vars1.variables)
    assert (
        context_vars_overwrite_2with1.variables["input"]
        == context_vars1.variables["input"]
    )
