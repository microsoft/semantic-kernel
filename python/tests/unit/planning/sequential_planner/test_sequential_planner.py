# Copyright (c) Microsoft. All rights reserved.

from unittest.mock import Mock

import pytest

from semantic_kernel.kernel import Kernel
from semantic_kernel.memory.semantic_text_memory import SemanticTextMemoryBase
from semantic_kernel.orchestration.context_variables import ContextVariables
from semantic_kernel.orchestration.sk_context import SKContext
from semantic_kernel.orchestration.sk_function_base import SKFunctionBase
from semantic_kernel.planning.planning_exception import PlanningException
from semantic_kernel.planning.sequential_planner.sequential_planner import (
    SequentialPlanner,
)
from semantic_kernel.skill_definition.function_view import FunctionView
from semantic_kernel.skill_definition.functions_view import FunctionsView
from semantic_kernel.skill_definition.skill_collection_base import SkillCollectionBase


def create_mock_function(function_view: FunctionView):
    mock_function = Mock(spec=SKFunctionBase)
    mock_function.describe.return_value = function_view
    mock_function.name = function_view.name
    mock_function.skill_name = function_view.skill_name
    return mock_function


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "goal", ["Write a poem or joke and send it in an e-mail to Kai."]
)
async def test_it_can_create_plan_async(goal):
    # Arrange
    kernel = Mock(spec=Kernel)

    memory = Mock(spec=SemanticTextMemoryBase)

    input = [
        ("SendEmail", "email", "Send an e-mail", False),
        ("GetEmailAddress", "email", "Get an e-mail address", False),
        ("Translate", "WriterSkill", "Translate something", True),
        ("Summarize", "SummarizeSkill", "Summarize something", True),
    ]

    functionsView = FunctionsView()
    skills = Mock(spec=SkillCollectionBase)
    mock_functions = []
    for name, skillName, description, isSemantic in input:
        function_view = FunctionView(name, skillName, description, [], isSemantic, True)
        mock_function = create_mock_function(function_view)
        functionsView.add_function(function_view)

        context = SKContext.construct(
            variables=ContextVariables(), memory=memory, skill_collection=skills
        )
        context.variables.update("MOCK FUNCTION CALLED")
        mock_function.invoke_async.return_value = context
        mock_functions.append(mock_function)

    skills.get_function.side_effect = lambda skill_name, function_name: next(
        (
            func
            for func in mock_functions
            if func.skill_name == skill_name and func.name == function_name
        ),
        None,
    )
    skills.get_functions_view.return_value = functionsView

    expected_functions = [x[0] for x in input]
    expected_skills = [x[1] for x in input]

    context = SKContext.construct(
        variables=ContextVariables(), memory=memory, skill_collection=skills
    )
    return_context = SKContext.construct(
        variables=ContextVariables(), memory=memory, skill_collection=skills
    )
    plan_string = """
<plan>
    <function.SummarizeSkill.Summarize/>
    <function.WriterSkill.Translate language="French" setContextVariable="TRANSLATED_SUMMARY"/>
    <function.email.GetEmailAddress input="John Doe" setContextVariable="EMAIL_ADDRESS"/>
    <function.email.SendEmail input="$TRANSLATED_SUMMARY" email_address="$EMAIL_ADDRESS"/>
</plan>"""

    return_context.variables.update(plan_string)

    mock_function_flow_function = Mock(spec=SKFunctionBase)
    mock_function_flow_function.invoke_async.return_value = return_context

    kernel.skills = skills
    kernel.create_new_context.return_value = context
    kernel.register_semantic_function.return_value = mock_function_flow_function

    planner = SequentialPlanner(kernel)

    # Act
    plan = await planner.create_plan_async(goal)

    # Assert
    assert plan.description == goal
    assert any(
        step.name in expected_functions and step.skill_name in expected_skills
        for step in plan._steps
    )
    for expected_function in expected_functions:
        assert any(step.name == expected_function for step in plan._steps)
    for expectedSkill in expected_skills:
        assert any(step.skill_name == expectedSkill for step in plan._steps)


@pytest.mark.asyncio
async def test_empty_goal_throws_async():
    # Arrange
    kernel = Mock(spec=Kernel)
    planner = SequentialPlanner(kernel)

    # Act & Assert
    with pytest.raises(PlanningException):
        await planner.create_plan_async("")


@pytest.mark.asyncio
async def test_invalid_xml_throws_async():
    # Arrange
    kernel = Mock(spec=Kernel)
    memory = Mock(spec=SemanticTextMemoryBase)
    skills = Mock(spec=SkillCollectionBase)

    functionsView = FunctionsView()
    skills.get_functions_view.return_value = functionsView

    plan_string = "<plan>notvalid<</plan>"
    return_context = SKContext.construct(
        variables=ContextVariables(plan_string), memory=memory, skill_collection=skills
    )

    context = SKContext.construct(
        variables=ContextVariables(), memory=memory, skill_collection=skills
    )

    mock_function_flow_function = Mock(spec=SKFunctionBase)
    mock_function_flow_function.invoke_async.return_value = return_context

    kernel.skills = skills
    kernel.create_new_context.return_value = context
    kernel.register_semantic_function.return_value = mock_function_flow_function

    planner = SequentialPlanner(kernel)

    # Act & Assert
    with pytest.raises(PlanningException):
        await planner.create_plan_async("goal")
