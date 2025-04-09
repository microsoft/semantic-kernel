# Copyright (c) Microsoft. All rights reserved.

from dataclasses import dataclass

from semantic_kernel.connectors.openapi_plugin.models.rest_api_oauth_flow import RestApiOAuthFlow
from semantic_kernel.utils.feature_stage_decorator import experimental


@experimental
@dataclass
class RestApiOAuthFlows:
    """Represents the OAuth flows used by the REST API."""

    implicit: RestApiOAuthFlow | None = None
    password: RestApiOAuthFlow | None = None
    client_credentials: RestApiOAuthFlow | None = None
    authorization_code: RestApiOAuthFlow | None = None
