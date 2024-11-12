# Copyright (c) Microsoft. All rights reserved.

from semantic_kernel.utils.experimental_decorator import experimental_class


@experimental_class
class RestApiOAuthFlow:
    """Represents the OAuth flow used by the REST API."""

    def __init__(self, authorization_url: str, token_url: str, scopes: dict[str, str], refresh_url: str | None = None):
        """Initializes a new instance of the RestApiOAuthFlow class."""
        self.authorization_url = authorization_url
        self.token_url = token_url
        self.refresh_url = refresh_url
        self.scopes = scopes
