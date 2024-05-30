# Copyright (c) Microsoft. All rights reserved.

from urllib.parse import urlparse

from semantic_kernel.utils.experimental_decorator import experimental_class


@experimental_class
class Uri:
    """The Uri class that represents the URI."""

    def __init__(self, uri):
        """Initialize the Uri."""
        self.uri = uri

    def get_left_part(self):
        """Get the left part of the URI."""
        parsed_uri = urlparse(self.uri)
        return f"{parsed_uri.scheme}://{parsed_uri.netloc}"
