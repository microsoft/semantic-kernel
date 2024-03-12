# Copyright (c) 2013 Amazon.com, Inc. or its affiliates.  All Rights Reserved
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

def tag(key, value):
    start = '<%s>' % key
    end = '</%s>' % key
    return '%s%s%s' % (start, value, end)


class WebsiteConfiguration(object):
    """
    Website configuration for a bucket.

    :ivar suffix: Suffix that is appended to a request that is for a
        "directory" on the website endpoint (e.g. if the suffix is
        index.html and you make a request to samplebucket/images/
        the data that is returned will be for the object with the
        key name images/index.html).  The suffix must not be empty
        and must not include a slash character.

    :ivar error_key: The object key name to use when a 4xx class error
        occurs.  This key identifies the page that is returned when
        such an error occurs.

    :ivar redirect_all_requests_to: Describes the redirect behavior for every
        request to this bucket's website endpoint. If this value is non None,
        no other values are considered when configuring the website
        configuration for the bucket. This is an instance of
        ``RedirectLocation``.

    :ivar routing_rules: ``RoutingRules`` object which specifies conditions
        and redirects that apply when the conditions are met.

    """

    def __init__(self, suffix=None, error_key=None,
                 redirect_all_requests_to=None, routing_rules=None):
        self.suffix = suffix
        self.error_key = error_key
        self.redirect_all_requests_to = redirect_all_requests_to
        if routing_rules is not None:
            self.routing_rules = routing_rules
        else:
            self.routing_rules = RoutingRules()

    def startElement(self, name, attrs, connection):
        if name == 'RoutingRules':
            self.routing_rules = RoutingRules()
            return self.routing_rules
        elif name == 'IndexDocument':
            return _XMLKeyValue([('Suffix', 'suffix')], container=self)
        elif name == 'ErrorDocument':
            return _XMLKeyValue([('Key', 'error_key')], container=self)

    def endElement(self, name, value, connection):
        pass

    def to_xml(self):
        parts = ['<?xml version="1.0" encoding="UTF-8"?>',
          '<WebsiteConfiguration xmlns="http://s3.amazonaws.com/doc/2006-03-01/">']
        if self.suffix is not None:
            parts.append(tag('IndexDocument', tag('Suffix', self.suffix)))
        if self.error_key is not None:
            parts.append(tag('ErrorDocument', tag('Key', self.error_key)))
        if self.redirect_all_requests_to is not None:
            parts.append(self.redirect_all_requests_to.to_xml())
        if self.routing_rules:
            parts.append(self.routing_rules.to_xml())
        parts.append('</WebsiteConfiguration>')
        return ''.join(parts)


class _XMLKeyValue(object):
    def __init__(self, translator, container=None):
        self.translator = translator
        if container:
            self.container = container
        else:
            self.container = self

    def startElement(self, name, attrs, connection):
        pass

    def endElement(self, name, value, connection):
        for xml_key, attr_name in self.translator:
            if name == xml_key:
                setattr(self.container, attr_name, value)

    def to_xml(self):
        parts = []
        for xml_key, attr_name in self.translator:
            content = getattr(self.container, attr_name)
            if content is not None:
                parts.append(tag(xml_key, content))
        return ''.join(parts)


class RedirectLocation(_XMLKeyValue):
    """Specify redirect behavior for every request to a bucket's endpoint.

    :ivar hostname: Name of the host where requests will be redirected.

    :ivar protocol: Protocol to use (http, https) when redirecting requests.
        The default is the protocol that is used in the original request.

    """
    TRANSLATOR = [('HostName', 'hostname'),
                  ('Protocol', 'protocol'),
                 ]

    def __init__(self, hostname=None, protocol=None):
        self.hostname = hostname
        self.protocol = protocol
        super(RedirectLocation, self).__init__(self.TRANSLATOR)

    def to_xml(self):
        return tag('RedirectAllRequestsTo',
            super(RedirectLocation, self).to_xml())


class RoutingRules(list):

    def add_rule(self, rule):
        """

        :type rule: :class:`boto.s3.website.RoutingRule`
        :param rule: A routing rule.

        :return: This ``RoutingRules`` object is returned,
            so that it can chain subsequent calls.

        """
        self.append(rule)
        return self

    def startElement(self, name, attrs, connection):
        if name == 'RoutingRule':
            rule = RoutingRule(Condition(), Redirect())
            self.add_rule(rule)
            return rule

    def endElement(self, name, value, connection):
        pass

    def __repr__(self):
        return "RoutingRules(%s)" % super(RoutingRules, self).__repr__()

    def to_xml(self):
        inner_text = []
        for rule in self:
            inner_text.append(rule.to_xml())
        return tag('RoutingRules', '\n'.join(inner_text))


class RoutingRule(object):
    """Represents a single routing rule.

    There are convenience methods to making creating rules
    more concise::

        rule = RoutingRule.when(key_prefix='foo/').then_redirect('example.com')

    :ivar condition: Describes condition that must be met for the
        specified redirect to apply.

    :ivar redirect: Specifies redirect behavior.  You can redirect requests to
        another host, to another page, or with another protocol. In the event
        of an error, you can can specify a different error code to return.

    """
    def __init__(self, condition=None, redirect=None):
        self.condition = condition
        self.redirect = redirect

    def startElement(self, name, attrs, connection):
        if name == 'Condition':
            return self.condition
        elif name == 'Redirect':
            return self.redirect

    def endElement(self, name, value, connection):
        pass

    def to_xml(self):
        parts = []
        if self.condition:
            parts.append(self.condition.to_xml())
        if self.redirect:
            parts.append(self.redirect.to_xml())
        return tag('RoutingRule', '\n'.join(parts))

    @classmethod
    def when(cls, key_prefix=None, http_error_code=None):
        return cls(Condition(key_prefix=key_prefix,
                             http_error_code=http_error_code), None)

    def then_redirect(self, hostname=None, protocol=None, replace_key=None,
                      replace_key_prefix=None, http_redirect_code=None):
        self.redirect = Redirect(
                hostname=hostname, protocol=protocol,
                replace_key=replace_key,
                replace_key_prefix=replace_key_prefix,
                http_redirect_code=http_redirect_code)
        return self


class Condition(_XMLKeyValue):
    """
    :ivar key_prefix: The object key name prefix when the redirect is applied.
        For example, to redirect requests for ExamplePage.html, the key prefix
        will be ExamplePage.html. To redirect request for all pages with the
        prefix docs/, the key prefix will be /docs, which identifies all
        objects in the docs/ folder.

    :ivar http_error_code: The HTTP error code when the redirect is applied. In
        the event of an error, if the error code equals this value, then the
        specified redirect is applied.

    """
    TRANSLATOR = [
        ('KeyPrefixEquals', 'key_prefix'),
        ('HttpErrorCodeReturnedEquals', 'http_error_code'),
        ]

    def __init__(self, key_prefix=None, http_error_code=None):
        self.key_prefix = key_prefix
        self.http_error_code = http_error_code
        super(Condition, self).__init__(self.TRANSLATOR)

    def to_xml(self):
        return tag('Condition', super(Condition, self).to_xml())


class Redirect(_XMLKeyValue):
    """
    :ivar hostname: The host name to use in the redirect request.

    :ivar protocol: The protocol to use in the redirect request.  Can be either
    'http' or 'https'.

    :ivar replace_key: The specific object key to use in the redirect request.
        For example, redirect request to error.html.

    :ivar replace_key_prefix: The object key prefix to use in the redirect
        request. For example, to redirect requests for all pages with prefix
        docs/ (objects in the docs/ folder) to documents/, you can set a
        condition block with KeyPrefixEquals set to docs/ and in the Redirect
        set ReplaceKeyPrefixWith to /documents.

    :ivar http_redirect_code: The HTTP redirect code to use on the response.

    """

    TRANSLATOR = [
        ('Protocol', 'protocol'),
        ('HostName', 'hostname'),
        ('ReplaceKeyWith', 'replace_key'),
        ('ReplaceKeyPrefixWith', 'replace_key_prefix'),
        ('HttpRedirectCode', 'http_redirect_code'),
        ]

    def __init__(self, hostname=None, protocol=None, replace_key=None,
                 replace_key_prefix=None, http_redirect_code=None):
        self.hostname = hostname
        self.protocol = protocol
        self.replace_key = replace_key
        self.replace_key_prefix = replace_key_prefix
        self.http_redirect_code = http_redirect_code
        super(Redirect, self).__init__(self.TRANSLATOR)

    def to_xml(self):
        return tag('Redirect', super(Redirect, self).to_xml())


