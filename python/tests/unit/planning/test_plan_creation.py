# Copyright (c) Microsoft. All rights reserved.

import semantic_kernel as sk
from semantic_kernel.core_skills.math_skill import MathSkill
from semantic_kernel.orchestration.context_variables import ContextVariables
from semantic_kernel.planning import Plan


def test_create_empty_plan():
    plan = Plan()
    assert plan is not None
    assert plan.name == ""
    assert type(plan.state) is ContextVariables
    assert plan.skill_name == ""
    assert plan.description == ""
    assert plan.function is None
    assert type(plan.parameters) is ContextVariables
    assert plan.is_semantic is None
    assert plan.is_native is None
    assert plan.request_settings is None
    assert plan.has_next_step is False
    assert plan.next_step_index == 0
    assert plan._steps == []


def test_create_plan_with_name():
    plan = Plan(name="test")
    assert plan is not None
    assert plan.name == "test"
    assert type(plan.state) is ContextVariables
    assert plan.skill_name == ""
    assert plan.description == ""
    assert plan.function is None
    assert type(plan.parameters) is ContextVariables
    assert plan.is_semantic is None
    assert plan.is_native is None
    assert plan.request_settings is None
    assert plan.has_next_step is False
    assert plan.next_step_index == 0
    assert plan._steps == []


def test_create_plan_with_name_and_description():
    plan = Plan(name="test", description="test description")
    assert plan is not None
    assert plan.name == "test"
    assert type(plan.state) is ContextVariables
    assert plan.skill_name == ""
    assert plan.description == "test description"
    assert plan.function is None
    assert type(plan.parameters) is ContextVariables
    assert plan.is_semantic is None
    assert plan.is_native is None
    assert plan.request_settings is None
    assert plan.has_next_step is False
    assert plan.next_step_index == 0
    assert plan._steps == []


def test_create_plan_with_state_and_parameters():
    plan = Plan(
        name="test",
        state=ContextVariables(),
        parameters={"test_param": "test_param_val"},
    )
    assert plan is not None
    assert plan.name == "test"
    assert plan.state["input"] == ""
    assert plan.skill_name == ""
    assert plan.description == ""
    assert plan.function is None
    assert plan.parameters["test_param"] == "test_param_val"
    assert plan.is_semantic is None
    assert plan.is_native is None
    assert plan.request_settings is None
    assert plan.has_next_step is False
    assert plan.next_step_index == 0
    assert plan._steps == []


def test_create_plan_with_name_and_function():
    # create a kernel
    kernel = sk.Kernel()

    # import test (math) skill
    skill = MathSkill()
    skill_config_dict = kernel.import_skill(skill, "math")

    test_function = skill_config_dict["Add"]

    plan = Plan(name="test", function=test_function)
    assert plan is not None
    assert plan.name == "Add"
    assert type(plan.state) is ContextVariables
    assert plan.skill_name == "math"
    assert plan.description == test_function.description
    assert plan.function is test_function
    assert type(plan.parameters) is ContextVariables
    assert plan.is_semantic is test_function.is_semantic
    assert plan.is_native is test_function.is_native
    assert plan.request_settings == test_function.request_settings
    assert plan.has_next_step is False
    assert plan.next_step_index == 0
    assert plan._steps == []


def test_create_multistep_plan_with_functions():
    # create a kernel
    kernel = sk.Kernel()

    # import test (math) skill
    skill = MathSkill()
    skill_config_dict = kernel.import_skill(skill, "math")

    test_function1 = skill_config_dict["Add"]
    test_function2 = skill_config_dict["Subtract"]

    plan = Plan(name="multistep_test")
    plan.add_steps([test_function1, test_function2])

    assert plan is not None
    assert plan.name == "multistep_test"
    assert type(plan.state) is ContextVariables
    assert plan.skill_name == ""
    assert plan.description == ""
    assert plan.function is None
    assert type(plan.parameters) is ContextVariables
    assert plan.is_semantic is None
    assert plan.is_native is None
    assert plan.request_settings is None
    assert plan.has_next_step is True
    assert plan.next_step_index == 0
    assert len(plan._steps) == 2


def test_create_multistep_plan_with_plans():
    # create a kernel
    kernel = sk.Kernel()

    # import test (math) skill
    skill = MathSkill()
    skill_config_dict = kernel.import_skill(skill, "math")

    test_function1 = skill_config_dict["Add"]
    test_function2 = skill_config_dict["Subtract"]

    plan = Plan(name="multistep_test")
    plan_step1 = Plan(name="step1", function=test_function1)
    plan_step2 = Plan(name="step2", function=test_function2)
    plan.add_steps([plan_step1, plan_step2])

    assert plan is not None
    assert plan.name == "multistep_test"
    assert type(plan.state) is ContextVariables
    assert plan.skill_name == ""
    assert plan.description == ""
    assert plan.function is None
    assert type(plan.parameters) is ContextVariables
    assert plan.is_semantic is None
    assert plan.is_native is None
    assert plan.request_settings is None
    assert plan.has_next_step is True
    assert plan.next_step_index == 0
    assert len(plan._steps) == 2


def test_add_step_to_plan():
    # create a kernel
    kernel = sk.Kernel()

    # import test (math) skill
    skill = MathSkill()
    skill_config_dict = kernel.import_skill(skill, "math")

    test_function1 = skill_config_dict["Add"]
    test_function2 = skill_config_dict["Subtract"]

    plan = Plan(name="multistep_test", function=test_function1)
    plan.add_steps([test_function2])
    assert plan is not None
    assert plan.name == "Add"
    assert type(plan.state) is ContextVariables
    assert plan.skill_name == "math"
    assert plan.description == test_function1.description
    assert plan.function is test_function1
    assert type(plan.parameters) is ContextVariables
    assert plan.is_semantic is test_function1.is_semantic
    assert plan.is_native is test_function1.is_native
    assert plan.request_settings == test_function1.request_settings
    assert plan.has_next_step is True
    assert plan.next_step_index == 0
    assert len(plan._steps) == 1
