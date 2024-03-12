# Copyright (c) 2006,2007 Mitch Garnaat http://garnaat.org/
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

class User(object):
    def __init__(self, parent=None, id='', display_name=''):
        if parent:
            parent.owner = self
        self.type = None
        self.id = id
        self.display_name = display_name

    def startElement(self, name, attrs, connection):
        return None

    def endElement(self, name, value, connection):
        if name == 'DisplayName':
            self.display_name = value
        elif name == 'ID':
            self.id = value
        else:
            setattr(self, name, value)

    def to_xml(self, element_name='Owner'):
        if self.type:
            s = '<%s xsi:type="%s">' % (element_name, self.type)
        else:
            s = '<%s>' % element_name
        s += '<ID>%s</ID>' % self.id
        s += '<DisplayName>%s</DisplayName>' % self.display_name
        s += '</%s>' % element_name
        return s
