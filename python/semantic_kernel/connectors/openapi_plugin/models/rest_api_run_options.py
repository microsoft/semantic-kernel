# Copyright (c) Microsoft. All rights reserved.

from semantic_kernel.utils.feature_stage_decorator import experimental


@experimental
class RestApiRunOptions:
    """The options for running the REST API operation."""

    def __init__(self, server_url_override=None, api_host_url=None) -> None:
        """Initialize the REST API operation run options."""
        self.server_url_override: str = server_url_override
        self.api_host_url: str = api_host_url
