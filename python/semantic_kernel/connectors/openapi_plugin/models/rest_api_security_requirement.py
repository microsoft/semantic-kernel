# Copyright (c) Microsoft. All rights reserved.

from semantic_kernel.connectors.openapi_plugin.models.rest_api_security_scheme import RestApiSecurityScheme
from semantic_kernel.utils.experimental_decorator import experimental_class


@experimental_class
class RestApiSecurityRequirement(dict[RestApiSecurityScheme, list[str]]):
    """Represents the security requirements used by the REST API."""

    def __init__(self, dictionary: dict[RestApiSecurityScheme, list[str]]):
        """Initializes a new instance of the RestApiSecurityRequirement class."""
        super().__init__(dictionary)
