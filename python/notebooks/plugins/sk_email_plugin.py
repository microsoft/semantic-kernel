# Copyright (c) Microsoft. All rights reserved.

from semantic_kernel.skill_definition import sk_function
from plugins.imap_connector import ImapConnector
from plugins.gmail_connector import GmailConnector
from bs4 import BeautifulSoup
import re


class EmailPlugin:
    """
    A plugin to process emails over IMAP protocol.
    """

    def __init__(
        self,
        email: str = "",
        password: str = "",
        server: str = "",
        port: int = 993,
        inbox: str = "inbox",
        gmail_api_credentials: str = None,
        gmail_api_token: str = None,
        connector=None,
    ):
        if connector is not None:
            self.connector = connector
        elif gmail_api_credentials is not None and gmail_api_token is not None:
            self.connector = GmailConnector(
                app_cred_file=gmail_api_credentials, user_token_file=gmail_api_token
            )
        else:
            self.connector = ImapConnector(
                email=email,
                password=password,
                server=server,
                port=port,
                inbox=inbox,
            )

    @sk_function(
        description="Fetch the Nth email from the inbox. Returns one email message with all details. Increase the number to fetch older emails.",
        name="fetch_inbox_one_email_at_a_time",
        input_description="The position of the email to fetch, starting from '1' to fetch the most recent email. Increase the number to fetch older messages.",
    )
    def fetch_inbox_one_email_at_a_time(self, email_number: str) -> str:
        email_source = self.connector.fetch_email_number(email_number)

        soup = BeautifulSoup(email_source["text"], features="html.parser")
        # remove some elements
        for el in soup(["script", "style", "iframe", "img", "video", "audio"]):
            el.extract()

        # get text and compact empty lines
        text = soup.get_text()
        # remove multiple empty lines
        text = re.sub(r"[\r\n][\r\n]{2,}", "\n\n", text)
        # remove leading and trailing empty spaces, leaving max 1 empty space at the beginning of each line
        text = re.sub(r"[\n] +", "\n ", text)

        return f"Email id: {email_source['id']}\nDate: {email_source['date']}\nFrom: {email_source['from']}\nSubject: {email_source['subject']}\nContent: {text}"
