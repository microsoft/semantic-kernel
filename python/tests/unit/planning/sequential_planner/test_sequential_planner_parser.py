# Copyright (c) Microsoft. All rights reserved.

from unittest.mock import Mock

import pytest
from semantic_kernel.kernel import Kernel
from semantic_kernel.orchestration.sk_function_base import SKFunctionBase
from semantic_kernel.planning.planning_exception import PlanningException
from semantic_kernel.planning.sequential_planner.sequential_planner_parser import (
    SequentialPlanParser,
)
from semantic_kernel.skill_definition.function_view import FunctionView
from semantic_kernel.skill_definition.functions_view import FunctionsView


def create_mock_function(function_view: FunctionView) -> SKFunctionBase:
    mock_function = Mock(spec=SKFunctionBase)
    mock_function.describe.return_value = function_view
    mock_function.name = function_view.name
    mock_function.skill_name = function_view.skill_name
    mock_function.description = function_view.description
    return mock_function


def create_kernel_and_functions_mock(functions) -> Kernel:
    kernel = Kernel()
    functions_view = FunctionsView()
    for name, skill_name, description, is_semantic, result_string in functions:
        function_view = FunctionView(
            name, skill_name, description, [], is_semantic, True
        )
        functions_view.add_function(function_view)
        mock_function = create_mock_function(function_view)

        result = kernel.create_new_context()
        result.variables.update(result_string)
        mock_function.invoke_async.return_value = result
        kernel._skill_collection.add_semantic_function(mock_function)

    return kernel


def test_can_call_to_plan_from_xml():
    functions = [
        (
            "Summarize",
            "SummarizeSkill",
            "Summarize an input",
            True,
            "This is the summary.",
        ),
        ("Translate", "WriterSkill", "Translate to french", True, "Bonjour!"),
        (
            "GetEmailAddressAsync",
            "email",
            "Get email address",
            False,
            "johndoe@email.com",
        ),
        ("SendEmailAsync", "email", "Send email", False, "Email sent."),
    ]
    kernel = create_kernel_and_functions_mock(functions)

    plan_string = """<plan>
    <function.SummarizeSkill.Summarize/>
    <function.WriterSkill.Translate language="French" setContextVariable="TRANSLATED_SUMMARY"/>
    <function.email.GetEmailAddressAsync input="John Doe" setContextVariable="EMAIL_ADDRESS" appendToResult="PLAN_RESULT"/>
    <function.email.SendEmailAsync input="$TRANSLATED_SUMMARY" email_address="$EMAIL_ADDRESS"/>
</plan>"""
    goal = "Summarize an input, translate to french, and e-mail to John Doe"

    plan = SequentialPlanParser.to_plan_from_xml(
        plan_string,
        goal,
        SequentialPlanParser.get_skill_function(kernel.create_new_context()),
    )

    assert plan is not None
    assert (
        plan.description
        == "Summarize an input, translate to french, and e-mail to John Doe"
    )

    assert len(plan._steps) == 4
    assert plan._steps[0].skill_name == "SummarizeSkill"
    assert plan._steps[0].name == "Summarize"
    assert plan._steps[1].skill_name == "WriterSkill"
    assert plan._steps[1].name == "Translate"
    assert plan._steps[1].parameters["language"] == "French"
    assert "TRANSLATED_SUMMARY" in plan._steps[1]._outputs

    assert plan._steps[2].skill_name == "email"
    assert plan._steps[2].name == "GetEmailAddressAsync"
    assert plan._steps[2].parameters["input"] == "John Doe"
    assert "EMAIL_ADDRESS" in plan._steps[2]._outputs

    assert plan._steps[3].skill_name == "email"
    assert plan._steps[3].name == "SendEmailAsync"
    assert "$TRANSLATED_SUMMARY" in plan._steps[3].parameters["input"]
    assert "$EMAIL_ADDRESS" in plan._steps[3].parameters["email_address"]


def test_invalid_plan_execute_plan_returns_invalid_result():
    # Arrange
    kernel = create_kernel_and_functions_mock([])

    # Act and Assert
    with pytest.raises(PlanningException):
        SequentialPlanParser.to_plan_from_xml(
            "<someTag>",
            "Solve the equation x^2 = 2.",
            SequentialPlanParser.get_skill_function(kernel.create_new_context()),
        )


def test_can_create_plan_with_text_nodes():
    # Arrange
    goal_text = "Test the functionFlowRunner"
    plan_text = """
        <goal>Test the functionFlowRunner</goal>
        <plan>
        <function.MockSkill.Echo input="Hello World" />
        This is some text
        </plan>"""
    functions = [
        ("Echo", "MockSkill", "Echo an input", True, "Mock Echo Result"),
    ]
    kernel = create_kernel_and_functions_mock(functions)

    # Act
    plan = SequentialPlanParser.to_plan_from_xml(
        plan_text,
        goal_text,
        SequentialPlanParser.get_skill_function(kernel.create_new_context()),
    )

    # Assert
    assert plan is not None
    assert plan.description == goal_text
    assert len(plan._steps) == 1
    assert plan._steps[0].skill_name == "MockSkill"
    assert plan._steps[0].name == "Echo"


@pytest.mark.parametrize(
    "plan_text, allow_missing_functions",
    [
        (
            """
        <plan>
        <function.MockSkill.Echo input="Hello World" />
        <function.MockSkill.DoesNotExist input="Hello World" />
        </plan>""",
            True,
        ),
        (
            """
        <plan>
        <function.MockSkill.Echo input="Hello World" />
        <function.MockSkill.DoesNotExist input="Hello World" />
        </plan>""",
            False,
        ),
    ],
)
def test_can_create_plan_with_invalid_function_nodes(
    plan_text, allow_missing_functions
):
    # Arrange
    functions = [
        ("Echo", "MockSkill", "Echo an input", True, "Mock Echo Result"),
    ]
    kernel = create_kernel_and_functions_mock(functions)
    # Act and Assert
    if allow_missing_functions:
        plan = SequentialPlanParser.to_plan_from_xml(
            plan_text,
            "",
            SequentialPlanParser.get_skill_function(kernel.create_new_context()),
            allow_missing_functions,
        )

        # Assert
        assert plan is not None
        assert len(plan._steps) == 2

        assert plan._steps[0].skill_name == "MockSkill"
        assert plan._steps[0].name == "Echo"
        assert plan._steps[0].description == "Echo an input"

        assert plan._steps[1].skill_name == plan.__class__.__name__
        assert plan._steps[1].name == ""
        assert plan._steps[1].description == "MockSkill.DoesNotExist"
    else:
        with pytest.raises(PlanningException):
            SequentialPlanParser.to_plan_from_xml(
                plan_text,
                "",
                SequentialPlanParser.get_skill_function(kernel.create_new_context()),
                allow_missing_functions,
            )


def test_can_create_plan_with_other_text():
    # Arrange
    goal_text = "Test the functionFlowRunner"
    plan_text1 = """Possible result: <goal>Test the functionFlowRunner</goal>
        <plan>
        <function.MockSkill.Echo input="Hello World" />
        This is some text
        </plan>"""
    plan_text2 = """
        <plan>
        <function.MockSkill.Echo input="Hello World" />
        This is some text
        </plan>

        plan end"""
    plan_text3 = """
        <plan>
        <function.MockSkill.Echo input="Hello World" />
        This is some text
        </plan>

        plan <xml> end"""
    functions = [
        ("Echo", "MockSkill", "Echo an input", True, "Mock Echo Result"),
    ]
    kernel = create_kernel_and_functions_mock(functions)

    # Act
    plan1 = SequentialPlanParser.to_plan_from_xml(
        plan_text1,
        goal_text,
        SequentialPlanParser.get_skill_function(kernel.create_new_context()),
    )
    plan2 = SequentialPlanParser.to_plan_from_xml(
        plan_text2,
        goal_text,
        SequentialPlanParser.get_skill_function(kernel.create_new_context()),
    )
    plan3 = SequentialPlanParser.to_plan_from_xml(
        plan_text3,
        goal_text,
        SequentialPlanParser.get_skill_function(kernel.create_new_context()),
    )

    # Assert
    assert plan1 is not None
    assert plan1.description == goal_text
    assert len(plan1._steps) == 1
    assert plan1._steps[0].skill_name == "MockSkill"
    assert plan1._steps[0].name == "Echo"

    assert plan2 is not None
    assert plan2.description == goal_text
    assert len(plan2._steps) == 1
    assert plan2._steps[0].skill_name == "MockSkill"
    assert plan2._steps[0].name == "Echo"

    assert plan3 is not None
    assert plan3.description == goal_text
    assert len(plan3._steps) == 1
    assert plan3._steps[0].skill_name == "MockSkill"
    assert plan3._steps[0].name == "Echo"


@pytest.mark.parametrize(
    "plan_text",
    [
        """<plan> <function.CodeSearch.codesearchresults_post organization="MyOrg" project="Proj" api_version="7.1-preview.1" server_url="https://faketestorg.dev.azure.com/" payload="{&quot;searchText&quot;:&quot;test&quot;,&quot;$top&quot;:3,&quot;filters&quot;:{&quot;Repository/Project&quot;:[&quot;Proj&quot;],&quot;Repository/Repository&quot;:[&quot;Repo&quot;]}}" content_type="application/json" appendToResult="RESULT__TOP_THREE_RESULTS" /> </plan>""",
        """<plan>
  <function.CodeSearch.codesearchresults_post organization="MyOrg" project="MyProject" api_version="7.1-preview.1" payload="{&quot;searchText&quot;: &quot;MySearchText&quot;, &quot;filters&quot;: {&quot;pathFilters&quot;: [&quot;MyRepo&quot;]} }" setContextVariable="SEARCH_RESULTS"/>
</plan><!-- END -->""",
        """<plan>
  <function.CodeSearch.codesearchresults_post organization="MyOrg" project="MyProject" api_version="7.1-preview.1" server_url="https://faketestorg.dev.azure.com/" payload="{ 'searchText': 'MySearchText', 'filters': { 'Project': ['MyProject'], 'Repository': ['MyRepo'] }, 'top': 3, 'skip': 0 }" content_type="application/json" appendToResult="RESULT__TOP_THREE_RESULTS" />
</plan><!-- END -->""",
    ],
)
def test_can_create_plan_with_open_api_plugin(plan_text):
    # Arrange
    functions = [
        (
            "codesearchresults_post",
            "CodeSearch",
            "Echo an input",
            True,
            "Mock Echo Result",
        ),
    ]
    kernel = create_kernel_and_functions_mock(functions)

    # Act
    plan = SequentialPlanParser.to_plan_from_xml(
        plan_text,
        "",
        SequentialPlanParser.get_skill_function(kernel.create_new_context()),
    )

    # Assert
    assert plan is not None
    assert len(plan._steps) == 1
    assert plan._steps[0].skill_name == "CodeSearch"
    assert plan._steps[0].name == "codesearchresults_post"


def test_can_create_plan_with_ignored_nodes():
    # Arrange
    goal_text = "Test the functionFlowRunner"
    plan_text = """<plan>
        <function.MockSkill.Echo input="Hello World" />
        <tag>Some other tag</tag>
        <function.MockSkill.Echo />
        </plan>"""
    functions = [
        ("Echo", "MockSkill", "Echo an input", True, "Mock Echo Result"),
    ]
    kernel = create_kernel_and_functions_mock(functions)

    # Act
    plan = SequentialPlanParser.to_plan_from_xml(
        plan_text,
        goal_text,
        SequentialPlanParser.get_skill_function(kernel.create_new_context()),
    )

    # Assert
    assert plan is not None
    assert plan.description == goal_text
    assert len(plan._steps) == 2
    assert plan._steps[0].skill_name == "MockSkill"
    assert plan._steps[0].name == "Echo"
    assert len(plan._steps[1]._steps) == 0
    assert plan._steps[1].skill_name == "MockSkill"
    assert plan._steps[1].name == "Echo"
