# Copyright (c) Microsoft. All rights reserved.

import os.path
import base64
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build


class GmailConnector:
    """
    Gmail connector
    See https://developers.google.com/gmail/api/quickstart/python
    """

    APP_CREDENTIALS_FILE = "gmail_credentials.json"
    USER_TOKEN_FILE = "gmail_token.json"

    SCOPES = [
        "https://www.googleapis.com/auth/gmail.readonly",
        # "https://www.googleapis.com/auth/gmail.modify",
    ]

    def __init__(
        self,
        app_cred_file: str = APP_CREDENTIALS_FILE,
        user_token_file: str = USER_TOKEN_FILE,
    ):
        self.app_cred_file = app_cred_file
        self.user_token_file = user_token_file

    def fetch_email_number(self, email_number: int) -> str:
        """
        Fetches an email by its number.
        Use IMAP to connect and fetch the N email in inbox.
        """
        credentials = self._get_credentials()

        result = {
            "id": "",
            "from": "",
            "to": "",
            "date": "",
            "subject": "",
            "text": "",
        }

        # Call the Gmail API
        service = build("gmail", "v1", credentials=credentials)
        results = (
            service.users()
            .messages()
            .list(userId="me", labelIds=["INBOX"], maxResults=email_number)
            .execute()
        )

        messages = results.get("messages", [])
        if not messages:
            print("No new messages.")
            return None
        else:
            for message in messages:
                from_name = ""
                to_name = ""
                date = ""
                subject = ""
                msg_id = ""
                text = ""

                msg = (
                    service.users()
                    .messages()
                    .get(userId="me", id=message["id"])
                    .execute()
                )
                email_data = msg["payload"]["headers"]
                for values in email_data:
                    name = values["name"]

                    if name == "Subject":
                        subject = values["value"]

                    if name == "From":
                        from_name = values["value"]

                    if name == "To":
                        to_name = values["value"]

                    if name == "Date":
                        date = values["value"]

                    if name == "Message-ID":
                        msg_id = values["value"]

                        # check if msg has a payload key
                        if "payload" in msg and "parts" in msg["payload"]:
                            for part in msg["payload"]["parts"]:
                                try:
                                    data = part["body"]["data"]
                                    byte_code = base64.urlsafe_b64decode(data)
                                    text = byte_code.decode("utf-8")
                                except BaseException as error:
                                    pass

                if msg_id != "":
                    result = {
                        "id": msg_id,
                        "from": from_name,
                        "to": to_name,
                        "date": date,
                        "subject": subject,
                        "text": text,
                    }

        return result

    def _get_credentials(self):
        """
        Gets valid user credentials from storage.
        If nothing has been stored, or if the stored credentials are invalid,
        the OAuth2 flow is completed to obtain the new credentials.
        Returns:
            Credentials, the obtained credential.
        """
        creds = None

        # The file token.json stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        if os.path.exists(self.user_token_file):
            creds = Credentials.from_authorized_user_file(
                self.user_token_file, self.SCOPES
            )

        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists(self.app_cred_file):
                    raise Exception(f"Credentials file not found: {self.app_cred_file}")

                flow = InstalledAppFlow.from_client_secrets_file(
                    self.app_cred_file,
                    self.SCOPES,
                )
                creds = flow.run_local_server(port=0)

            # Save the credentials for the next run
            with open(self.user_token_file, "w") as token:
                token.write(creds.to_json())

        return creds
