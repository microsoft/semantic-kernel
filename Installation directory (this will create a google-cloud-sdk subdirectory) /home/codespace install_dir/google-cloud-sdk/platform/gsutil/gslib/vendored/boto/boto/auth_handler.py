# Copyright 2010 Google Inc.
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish, dis-
# tribute, sublicense, and/or sell copies of the Software, and to permit
# persons to whom the Software is furnished to do so, subject to the fol-
# lowing conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
# OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABIL-
# ITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT
# SHALL THE AUTHOR BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
# IN THE SOFTWARE.

"""
Defines an interface which all Auth handlers need to implement.
"""

from boto.plugin import Plugin


class NotReadyToAuthenticate(Exception):
    pass


class AuthHandler(Plugin):

    capability = []

    def __init__(self, host, config, provider):
        """Constructs the handlers.
        :type host: string
        :param host: The host to which the request is being sent.

        :type config: boto.pyami.Config
        :param config: Boto configuration.

        :type provider: boto.provider.Provider
        :param provider: Provider details.

        Raises:
            NotReadyToAuthenticate: if this handler is not willing to
                authenticate for the given provider and config.
        """
        pass

    def add_auth(self, http_request):
        """Invoked to add authentication details to request.

        :type http_request: boto.connection.HTTPRequest
        :param http_request: HTTP request that needs to be authenticated.
        """
        pass
