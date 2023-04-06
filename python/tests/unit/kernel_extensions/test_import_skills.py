# Copyright (c) Microsoft. All rights reserved.

import os

import semantic_kernel as sk
import semantic_kernel.ai.open_ai as sk_oai


def test_skill_can_be_imported():
    # create a kernel
    kernel = sk.create_kernel()
    api_key = "test-api-key"
    org_id = "test-org-id"
    kernel.config.add_text_backend(
        "test-completion-backend",
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
