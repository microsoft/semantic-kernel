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


class AccountAttribute(object):
    def __init__(self, connection=None):
        self.connection = connection
        self.attribute_name = None
        self.attribute_values = None

    def startElement(self, name, attrs, connection):
        if name == 'attributeValueSet':
            self.attribute_values = AttributeValues()
            return self.attribute_values

    def endElement(self, name, value, connection):
        if name == 'attributeName':
            self.attribute_name = value


class AttributeValues(list):
    def startElement(self, name, attrs, connection):
        pass

    def endElement(self, name, value, connection):
        if name == 'attributeValue':
            self.append(value)


class VPCAttribute(object):
    def __init__(self, connection=None):
        self.connection = connection
        self.vpc_id = None
        self.enable_dns_hostnames = None
        self.enable_dns_support = None
        self._current_attr = None

    def startElement(self, name, attrs, connection):
        if name in ('enableDnsHostnames', 'enableDnsSupport'):
            self._current_attr = name

    def endElement(self, name, value, connection):
        if name == 'vpcId':
            self.vpc_id = value
        elif name == 'value':
            if value == 'true':
                value = True
            else:
                value = False
            if self._current_attr == 'enableDnsHostnames':
                self.enable_dns_hostnames = value
            elif self._current_attr == 'enableDnsSupport':
                self.enable_dns_support = value
