# Copyright (c) Microsoft. All rights reserved.

from semantic_kernel.functions.kernel_function_decorator import kernel_function


class EmailPluginFake:
    @kernel_function(
        description="Given an email address and message body, send an email",
        name="SendEmail",
    )
    def send_email(self, input: str) -> str:
        return f"Sent email to: . Body: {input}"

    @kernel_function(
        description="Lookup an email address for a person given a name",
        name="GetEmailAddress",
    )
    def get_email_address(self, input: str) -> str:
        if input == "":
            return "johndoe1234@example.com"
        return f"{input}@example.com"

    @kernel_function(description="Write a short poem for an e-mail", name="WritePoem")
    def write_poem(self, input: str) -> str:
        return f"Roses are red, violets are blue, {input} is hard, so is this test."
