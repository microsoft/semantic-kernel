# Copyright (c) Microsoft. All rights reserved.

from imap_tools import MailBox


class ImapConnector:
    """
    A standard IMAP provider.
    """

    def __init__(
        self,
        email: str,
        password: str,
        server: str,
        port: int = 993,
        inbox: str = "inbox",
    ):
        self.server = server
        self.port = port
        self.email = email
        self.password = password
        self.inbox = inbox

    def fetch_email_number(self, email_number: int) -> str:
        """
        Fetches an email by its number.
        Use IMAP to connect and fetch the N email in inbox.
        """

        result = {
            "id": "",
            "from": "",
            "to": "",
            "date": "",
            "subject": "",
            "text": "",
        }
        with MailBox(host=self.server, port=self.port).login(
                self.email, self.password
            ) as mailbox:
            for msg in mailbox.fetch(limit=email_number, reverse=True):
                result = {
                    "id": msg.uid,
                    "from": msg.from_,
                    "to": msg.to,
                    "date": msg.date,
                    "subject": msg.subject,
                    "text": msg.text or msg.html,
                }

        return result
