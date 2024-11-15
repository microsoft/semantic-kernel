# Copyright (c) Microsoft. All rights reserved.

from dataclasses import dataclass

from semantic_kernel.utils.experimental_decorator import experimental_class


@experimental_class
@dataclass
class RestApiOAuthFlow:
    """Represents the OAuth flow used by the REST API."""

    authorization_url: str
    token_url: str
    scopes: dict[str, str]
    refresh_url: str | None = None
