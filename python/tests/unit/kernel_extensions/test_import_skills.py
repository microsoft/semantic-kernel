# Copyright (c) Microsoft. All rights reserved.

import os

import semantic_kernel as sk
import semantic_kernel.connectors.ai.open_ai as sk_oai


def test_skill_can_be_imported():
    # create a kernel
    kernel = sk.Kernel()
    api_key = "test-api-key"
    org_id = "test-org-id"
    kernel.add_text_completion_service(
        "test-completion-service",
        sk_oai.OpenAITextCompletion("text-davinci-003", api_key, org_id),
    )

    # import skills
    skills_directory = os.path.join(os.path.dirname(__file__), "../..", "test_skills")
    # path to skills directory
    skill_config_dict = kernel.import_semantic_skill_from_directory(
        skills_directory, "TestSkill"
    )

    assert skill_config_dict is not None
    assert len(skill_config_dict) == 1
    assert "TestFunction" in skill_config_dict
    skill_config = skill_config_dict["TestFunction"]
    assert skill_config.name == "TestFunction"
    assert skill_config.description == "Test Description"


def test_native_skill_can_be_imported():
    # create a kernel
    kernel = sk.Kernel()

    # import skills
    skills_directory = os.path.join(
        os.path.dirname(__file__), "../..", "test_native_skills"
    )
    # path to skills directory
    skill_config_dict = kernel.import_native_skill_from_directory(
        skills_directory, "TestNativeSkill"
    )

    assert skill_config_dict is not None
    assert len(skill_config_dict) == 1
    assert "echoAsync" in skill_config_dict
    skill_config = skill_config_dict["echoAsync"]
    assert skill_config.name == "echoAsync"
    assert skill_config.description == "Echo for input text"
