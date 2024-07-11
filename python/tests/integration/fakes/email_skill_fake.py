# Copyright (c) Microsoft. All rights reserved.

from semantic_kernel.skill_definition.sk_function_decorator import sk_function


class EmailSkillFake:
    @sk_function(
        description="Given an email address and message body, send an email",
        name="SendEmail",
    )
    def send_email(self, input: str) -> str:
        return f"Sent email to: . Body: {input}"

    @sk_function(
        description="Lookup an email address for a person given a name",
        name="GetEmailAddress",
    )
    def get_email_address(self, input: str) -> str:
        if input == "":
            return "johndoe1234@example.com"
        return f"{input}@example.com"

    @sk_function(description="Write a short poem for an e-mail", name="WritePoem")
    def write_poem(self, input: str) -> str:
        return f"Roses are red, violets are blue, {input} is hard, so is this test."
