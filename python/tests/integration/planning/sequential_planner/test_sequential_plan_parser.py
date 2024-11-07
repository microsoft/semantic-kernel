# Copyright (c) Microsoft. All rights reserved.

import pytest

import semantic_kernel.connectors.ai.open_ai as sk_oai
from semantic_kernel.kernel import Kernel
from semantic_kernel.planners.sequential_planner.sequential_planner_parser import SequentialPlanParser
from tests.integration.fakes.email_plugin_fake import EmailPluginFake
from tests.integration.fakes.summarize_plugin_fake import SummarizePluginFake
from tests.integration.fakes.writer_plugin_fake import WriterPluginFake


@pytest.mark.asyncio
async def test_can_call_to_plan_from_xml():
    kernel = Kernel()
    # Configure LLM service
    kernel.add_service(
        sk_oai.AzureChatCompletion(
            service_id="text_completion",
        ),
    )
    kernel.add_plugin(EmailPluginFake(), "email")
    kernel.add_plugin(SummarizePluginFake(), "SummarizePlugin")
    kernel.add_plugin(WriterPluginFake(), "WriterPlugin")

    plan_string = """
<plan>
    <function.SummarizePlugin-Summarize/>
    <function.WriterPlugin-Translate language="French" setContextVariable="TRANSLATED_SUMMARY"/>
    <function.email-GetEmailAddress input="John Doe" setContextVariable="EMAIL_ADDRESS"/>
    <function.email-SendEmail input="$TRANSLATED_SUMMARY" email_address="$EMAIL_ADDRESS"/>
</plan>
"""
    goal = "Summarize an input, translate to french, and e-mail to John Doe"

    plan = SequentialPlanParser.to_plan_from_xml(plan_string, goal, kernel)

    assert plan is not None
    assert plan.description == "Summarize an input, translate to french, and e-mail to John Doe"

    assert len(plan._steps) == 4
    step = plan._steps[0]
    assert step.plugin_name == "SummarizePlugin"
    assert step.name == "Summarize"

    step = plan._steps[1]
    assert step.plugin_name == "WriterPlugin"
    assert step.name == "Translate"
    assert step.parameters["language"] == "French"
    assert "TRANSLATED_SUMMARY" in step._outputs

    step = plan._steps[2]
    assert step.plugin_name == "email"
    assert step.name == "GetEmailAddress"
    assert step.parameters["input"] == "John Doe"
    assert "EMAIL_ADDRESS" in step._outputs

    step = plan._steps[3]
    assert step.plugin_name == "email"
    assert step.name == "SendEmail"
    assert step.parameters["input"] == "$TRANSLATED_SUMMARY"
    assert step.parameters["email_address"] == "$EMAIL_ADDRESS"
