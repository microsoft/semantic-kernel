# -*- coding: utf-8 -*-
# Copyright (c) 2012 Thomas Parslow http://almostobsolete.net/
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
#
from boto.compat import json


class GlacierResponse(dict):
    """
    Represents a response from Glacier layer1. It acts as a dictionary
    containing the combined keys received via JSON in the body (if
    supplied) and headers.
    """
    def __init__(self, http_response, response_headers):
        self.http_response = http_response
        self.status = http_response.status
        self[u'RequestId'] = http_response.getheader('x-amzn-requestid')
        if response_headers:
            for header_name, item_name in response_headers:
                self[item_name] = http_response.getheader(header_name)
        if http_response.status != 204: 
            if http_response.getheader('Content-Type') == 'application/json':
                body = json.loads(http_response.read().decode('utf-8'))
                self.update(body)
        size = http_response.getheader('Content-Length', None)
        if size is not None:
            self.size = size

    def read(self, amt=None):
        "Reads and returns the response body, or up to the next amt bytes."
        return self.http_response.read(amt)
