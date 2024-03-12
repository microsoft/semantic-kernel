# Copyright (c) 2009-2010 Mitch Garnaat http://garnaat.org/
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
Represents a DHCP Options set
"""

from boto.ec2.ec2object import TaggedEC2Object

class DhcpValueSet(list):

    def startElement(self, name, attrs, connection):
        pass

    def endElement(self, name, value, connection):
        if name == 'value':
            self.append(value)

class DhcpConfigSet(dict):

    def startElement(self, name, attrs, connection):
        if name == 'valueSet':
            if self._name not in self:
                self[self._name] = DhcpValueSet()
            return self[self._name]

    def endElement(self, name, value, connection):
        if name == 'key':
            self._name = value

class DhcpOptions(TaggedEC2Object):

    def __init__(self, connection=None):
        super(DhcpOptions, self).__init__(connection)
        self.id = None
        self.options = None

    def __repr__(self):
        return 'DhcpOptions:%s' % self.id

    def startElement(self, name, attrs, connection):
        retval = super(DhcpOptions, self).startElement(name, attrs, connection)
        if retval is not None:
            return retval
        if name == 'dhcpConfigurationSet':
            self.options = DhcpConfigSet()
            return self.options

    def endElement(self, name, value, connection):
        if name == 'dhcpOptionsId':
            self.id = value
        else:
            setattr(self, name, value)

