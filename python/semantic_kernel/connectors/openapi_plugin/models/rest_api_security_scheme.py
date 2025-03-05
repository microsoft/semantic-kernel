# Copyright (c) Microsoft. All rights reserved.

from semantic_kernel.connectors.openapi_plugin.models.rest_api_oauth_flows import RestApiOAuthFlows
from semantic_kernel.connectors.openapi_plugin.models.rest_api_parameter_location import (
    RestApiParameterLocation,
)
from semantic_kernel.utils.experimental_decorator import experimental_class


@experimental_class
class RestApiSecurityScheme:
    """Represents the security scheme used by the REST API."""

    def __init__(
        self,
        security_scheme_type: str,
        name: str,
        in_: RestApiParameterLocation,
        scheme: str,
        open_id_connect_url: str,
        description: str | None = None,
        bearer_format: str | None = None,
        flows: RestApiOAuthFlows | None = None,
    ):
        """Initializes a new instance of the RestApiSecurityScheme class."""
        self.security_scheme_type = security_scheme_type
        self.description = description
        self.name = name
        self.in_ = in_
        self.scheme = scheme
        self.bearer_format = bearer_format
        self.flows = flows
        self.open_id_connect_url = open_id_connect_url
