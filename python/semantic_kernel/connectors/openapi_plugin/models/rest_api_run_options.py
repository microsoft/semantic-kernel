# Copyright (c) Microsoft. All rights reserved.


class RestApiRunOptions:
    """The options for running the REST API operation."""

    def __init__(
        self, server_url_override: str | None = None, api_host_url: str | None = None, timeout: float | None = None
    ) -> None:
        """Initialize the REST API operation run options.

        Args:
            server_url_override: The server URL override, if any.
            api_host_url: The API host URL, if any.
            timeout: The timeout for the operation, if any.
        """
        self.server_url_override: str | None = server_url_override
        self.api_host_url: str | None = api_host_url
        self.timeout: float | None = timeout
