# Copyright (c) Microsoft. All rights reserved.

from semantic_kernel.connectors.openapi_plugin.models.rest_api_oauth_flow import RestApiOAuthFlow
from semantic_kernel.utils.experimental_decorator import experimental_class


@experimental_class
class RestApiOAuthFlows:
    """Represents the OAuth flows used by the REST API."""

    def __init__(
        self,
        implicit: RestApiOAuthFlow | None = None,
        password: RestApiOAuthFlow | None = None,
        client_credentials: RestApiOAuthFlow | None = None,
        authorization_code: RestApiOAuthFlow | None = None,
    ):
        """Initializes a new instance of the RestApiOAuthFlows class."""
        self.implicit = implicit
        self.password = password
        self.client_credentials = client_credentials
        self.authorization_code = authorization_code
