# Copyright (c) Microsoft. All rights reserved.

import pytest
import semantic_kernel.connectors.ai.open_ai as sk_oai
from semantic_kernel.kernel import Kernel
from semantic_kernel.planning.sequential_planner.sequential_planner_parser import (
    SequentialPlanParser,
)
from tests.integration.fakes.email_skill_fake import EmailSkillFake
from tests.integration.fakes.summarize_skill_fake import SummarizeSkillFake
from tests.integration.fakes.writer_skill_fake import WriterSkillFake


@pytest.mark.asyncio
async def test_can_call_to_plan_from_xml(get_aoai_config):
    deployment_name, api_key, endpoint = get_aoai_config

    kernel = Kernel()
    # Configure LLM service
    kernel.add_text_completion_service(
        "text_completion",
        sk_oai.AzureChatCompletion(deployment_name, endpoint, api_key),
    )
    kernel.import_skill(EmailSkillFake(), "email")
    kernel.import_skill(SummarizeSkillFake(), "SummarizeSkill")
    kernel.import_skill(WriterSkillFake(), "WriterSkill")

    plan_string = """
<plan>
    <function.SummarizeSkill.Summarize/>
    <function.WriterSkill.Translate language="French" setContextVariable="TRANSLATED_SUMMARY"/>
    <function.email.GetEmailAddress input="John Doe" setContextVariable="EMAIL_ADDRESS"/>
    <function.email.SendEmail input="$TRANSLATED_SUMMARY" email_address="$EMAIL_ADDRESS"/>
</plan>
"""
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
    step = plan._steps[0]
    assert step.skill_name == "SummarizeSkill"
    assert step.name == "Summarize"

    step = plan._steps[1]
    assert step.skill_name == "WriterSkill"
    assert step.name == "Translate"
    assert step.parameters["language"] == "French"
    assert "TRANSLATED_SUMMARY" in step._outputs

    step = plan._steps[2]
    assert step.skill_name == "email"
    assert step.name == "GetEmailAddress"
    assert step.parameters["input"] == "John Doe"
    assert "EMAIL_ADDRESS" in step._outputs

    step = plan._steps[3]
    assert step.skill_name == "email"
    assert step.name == "SendEmail"
    assert step.parameters["input"] == "$TRANSLATED_SUMMARY"
    assert step.parameters["email_address"] == "$EMAIL_ADDRESS"
