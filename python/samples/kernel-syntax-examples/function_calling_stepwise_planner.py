# Copyright (c) Microsoft. All rights reserved.

import sys

if sys.version_info >= (3, 9):
    from typing import Annotated
else:
    from typing_extensions import Annotated

import asyncio

import semantic_kernel as sk
from semantic_kernel.connectors.ai.open_ai import (
    OpenAIChatCompletion,
)
from semantic_kernel.core_plugins.math_plugin import MathPlugin
from semantic_kernel.core_plugins.time_plugin import TimePlugin
from semantic_kernel.functions.kernel_function_decorator import kernel_function
from semantic_kernel.planners.function_calling_stepwise_planner.function_calling_stepwise_planner import (
    FunctionCallingStepwisePlanner,
)
from semantic_kernel.planners.function_calling_stepwise_planner.function_calling_stepwise_planner_options import (
    FunctionCallingStepwisePlannerOptions,
)


# Define an example EmailPlugin
class EmailPlugin:
    """
    Description: EmailPlugin provides a set of functions to send emails.

    Usage:
        kernel.import_plugin_from_object(EmailPlugin(), plugin_name="email")

    Examples:
        {{email.SendEmail}} => Sends an email with the provided subject and body.
    """

    @kernel_function(name="SendEmail", description="Given an e-mail and message body, send an e-email")
    def send_email(
        self,
        subject: Annotated[str, "the subject of the email"],
        body: Annotated[str, "the body of the email"],
    ) -> Annotated[str, "the output is a string"]:
        """Sends an email with the provided subject and body."""
        return f"Email sent with subject: {subject} and body: {body}"

    @kernel_function(name="GetEmailAddress", description="Given a name, find the email address")
    def get_email_address(
        self,
        input: Annotated[str, "the name of the person"],
    ):
        email = ""
        if input == "Jane":
            email = "janedoe4321@example.com"
        elif input == "Paul":
            email = "paulsmith5678@example.com"
        elif input == "Mary":
            email = "maryjones8765@example.com"
        else:
            input = "johndoe1234@example.com"
        return email


async def main():
    kernel = sk.Kernel()

    service_id = "planner"
    api_key, _ = sk.openai_settings_from_dot_env()
    kernel.add_service(
        OpenAIChatCompletion(
            service_id=service_id,
            ai_model_id="gpt-3.5-turbo-1106",
            api_key=api_key,
        ),
    )

    kernel.import_plugin_from_object(MathPlugin(), "MathPlugin")
    kernel.import_plugin_from_object(TimePlugin(), "TimePlugin")
    kernel.import_plugin_from_object(EmailPlugin(), "EmailPlugin")

    questions = [
        "What is the current hour number, plus 5?",
        "What is 387 minus 22? Email the solution to John and Mary.",
        "Write a limerick, translate it to Spanish, and send it to Jane",
    ]

    options = FunctionCallingStepwisePlannerOptions(
        max_iterations=10,
        max_tokens=4000,
    )

    planner = FunctionCallingStepwisePlanner(service_id=service_id, options=options)

    for question in questions:
        result = await planner.execute(kernel, question)
        print(f"Q: {question}\nA: {result.final_answer}\n")

        # Uncomment the following line to view the planner's process for completing the request
        # print(f"Chat history: {result.chat_history}\n")


if __name__ == "__main__":
    asyncio.run(main())
