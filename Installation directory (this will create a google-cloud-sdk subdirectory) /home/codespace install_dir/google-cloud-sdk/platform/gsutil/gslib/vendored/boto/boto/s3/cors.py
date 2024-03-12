# Copyright (c) 2012 Mitch Garnaat http://garnaat.org/
# Copyright (c) 2012 Amazon.com, Inc. or its affiliates.  All Rights Reserved
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


class CORSRule(object):
    """
    CORS rule for a bucket.

    :ivar id: A unique identifier for the rule.  The ID value can be
        up to 255 characters long.  The IDs help you find a rule in
        the configuration.

    :ivar allowed_methods: An HTTP method that you want to allow the
        origin to execute.  Each CORSRule must identify at least one
        origin and one method. Valid values are:
        GET|PUT|HEAD|POST|DELETE

    :ivar allowed_origin: An origin that you want to allow cross-domain
        requests from. This can contain at most one * wild character.
        Each CORSRule must identify at least one origin and one method.
        The origin value can include at most one '*' wild character.
        For example, "http://*.example.com". You can also specify
        only * as the origin value allowing all origins cross-domain access.

    :ivar allowed_header: Specifies which headers are allowed in a
        pre-flight OPTIONS request via the
        Access-Control-Request-Headers header. Each header name
        specified in the Access-Control-Request-Headers header must
        have a corresponding entry in the rule. Amazon S3 will send
        only the allowed headers in a response that were requested.
        This can contain at most one * wild character.

    :ivar max_age_seconds: The time in seconds that your browser is to
        cache the preflight response for the specified resource.

    :ivar expose_header: One or more headers in the response that you
        want customers to be able to access from their applications
        (for example, from a JavaScript XMLHttpRequest object).  You
        add one ExposeHeader element in the rule for each header.
        """

    def __init__(self, allowed_method=None, allowed_origin=None,
                 id=None, allowed_header=None, max_age_seconds=None,
                 expose_header=None):
        if allowed_method is None:
            allowed_method = []
        self.allowed_method = allowed_method
        if allowed_origin is None:
            allowed_origin = []
        self.allowed_origin = allowed_origin
        self.id = id
        if allowed_header is None:
            allowed_header = []
        self.allowed_header = allowed_header
        self.max_age_seconds = max_age_seconds
        if expose_header is None:
            expose_header = []
        self.expose_header = expose_header

    def __repr__(self):
        return '<Rule: %s>' % self.id

    def startElement(self, name, attrs, connection):
        return None

    def endElement(self, name, value, connection):
        if name == 'ID':
            self.id = value
        elif name == 'AllowedMethod':
            self.allowed_method.append(value)
        elif name == 'AllowedOrigin':
            self.allowed_origin.append(value)
        elif name == 'AllowedHeader':
            self.allowed_header.append(value)
        elif name == 'MaxAgeSeconds':
            self.max_age_seconds = int(value)
        elif name == 'ExposeHeader':
            self.expose_header.append(value)
        else:
            setattr(self, name, value)

    def to_xml(self):
        s = '<CORSRule>'
        for allowed_method in self.allowed_method:
            s += '<AllowedMethod>%s</AllowedMethod>' % allowed_method
        for allowed_origin in self.allowed_origin:
            s += '<AllowedOrigin>%s</AllowedOrigin>' % allowed_origin
        for allowed_header in self.allowed_header:
            s += '<AllowedHeader>%s</AllowedHeader>' % allowed_header
        for expose_header in self.expose_header:
            s += '<ExposeHeader>%s</ExposeHeader>' % expose_header
        if self.max_age_seconds:
            s += '<MaxAgeSeconds>%d</MaxAgeSeconds>' % self.max_age_seconds
        if self.id:
            s += '<ID>%s</ID>' % self.id
        s += '</CORSRule>'
        return s


class CORSConfiguration(list):
    """
    A container for the rules associated with a CORS configuration.
    """

    def startElement(self, name, attrs, connection):
        if name == 'CORSRule':
            rule = CORSRule()
            self.append(rule)
            return rule
        return None

    def endElement(self, name, value, connection):
        setattr(self, name, value)

    def to_xml(self):
        """
        Returns a string containing the XML version of the Lifecycle
        configuration as defined by S3.
        """
        s = '<CORSConfiguration>'
        for rule in self:
            s += rule.to_xml()
        s += '</CORSConfiguration>'
        return s

    def add_rule(self, allowed_method, allowed_origin,
                 id=None, allowed_header=None, max_age_seconds=None,
                 expose_header=None):
        """
        Add a rule to this CORS configuration.  This only adds
        the rule to the local copy.  To install the new rule(s) on
        the bucket, you need to pass this CORS config object
        to the set_cors method of the Bucket object.

        :type allowed_methods: list of str
        :param allowed_methods: An HTTP method that you want to allow the
            origin to execute.  Each CORSRule must identify at least one
            origin and one method. Valid values are:
            GET|PUT|HEAD|POST|DELETE

        :type allowed_origin: list of str
        :param allowed_origin: An origin that you want to allow cross-domain
            requests from. This can contain at most one * wild character.
            Each CORSRule must identify at least one origin and one method.
            The origin value can include at most one '*' wild character.
            For example, "http://*.example.com". You can also specify
            only * as the origin value allowing all origins
            cross-domain access.

        :type id: str
        :param id: A unique identifier for the rule.  The ID value can be
            up to 255 characters long.  The IDs help you find a rule in
            the configuration.

        :type allowed_header: list of str
        :param allowed_header: Specifies which headers are allowed in a
            pre-flight OPTIONS request via the
            Access-Control-Request-Headers header. Each header name
            specified in the Access-Control-Request-Headers header must
            have a corresponding entry in the rule. Amazon S3 will send
            only the allowed headers in a response that were requested.
            This can contain at most one * wild character.

        :type max_age_seconds: int
        :param max_age_seconds: The time in seconds that your browser is to
            cache the preflight response for the specified resource.

        :type expose_header: list of str
        :param expose_header: One or more headers in the response that you
            want customers to be able to access from their applications
            (for example, from a JavaScript XMLHttpRequest object).  You
            add one ExposeHeader element in the rule for each header.
        """
        if not isinstance(allowed_method, (list, tuple)):
            allowed_method = [allowed_method]
        if not isinstance(allowed_origin, (list, tuple)):
            allowed_origin = [allowed_origin]
        if not isinstance(allowed_origin, (list, tuple)):
            if allowed_origin is None:
                allowed_origin = []
            else:
                allowed_origin = [allowed_origin]
        if not isinstance(expose_header, (list, tuple)):
            if expose_header is None:
                expose_header = []
            else:
                expose_header = [expose_header]
        rule = CORSRule(allowed_method, allowed_origin, id, allowed_header,
                        max_age_seconds, expose_header)
        self.append(rule)
