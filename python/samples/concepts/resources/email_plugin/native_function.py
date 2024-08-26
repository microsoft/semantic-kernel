# Copyright (c) Microsoft. All rights reserved.


from typing import Annotated

from semantic_kernel.functions.kernel_function_decorator import kernel_function


class EmailPlugin:
    """Description: EmailPlugin provides a set of functions to send emails.

    Usage:
        kernel.add_plugin(EmailPlugin(), plugin_name="email")

    Examples:
        {{email.SendEmail}} => Sends an email with the provided subject and body.
    """

    @kernel_function(
        name="SendEmail",
        description="Given an e-mail and message body, send an e-email",
    )
    def send_email(
        self,
        subject: Annotated[str, "the subject of the email"],
        body: Annotated[str, "the body of the email"],
    ) -> Annotated[str, "the output is a string"]:
        """Sends an email with the provided subject and body."""
        return f"Email sent with subject: {subject} and body: {body}"

    @kernel_function(
        name="GetEmailAddress", description="Given a name, find the email address"
    )
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
