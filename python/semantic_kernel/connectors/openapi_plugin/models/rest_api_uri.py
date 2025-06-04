# Copyright (c) Microsoft. All rights reserved.

from urllib.parse import urlparse

from semantic_kernel.utils.feature_stage_decorator import experimental


@experimental
class Uri:
    """The Uri class that represents the URI."""

    def __init__(self, uri):
        """Initialize the Uri."""
        self.uri = uri

    def get_left_part(self):
        """Get the left part of the URI."""
        parsed_uri = urlparse(self.uri)
        return f"{parsed_uri.scheme}://{parsed_uri.netloc}"
