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

import xml.sax

from boto.compat import StringIO


class XmlHandler(xml.sax.ContentHandler):

    def __init__(self, root_node, connection):
        self.connection = connection
        self.nodes = [('root', root_node)]
        self.current_text = ''

    def startElement(self, name, attrs):
        self.current_text = ''
        new_node = self.nodes[-1][1].startElement(name, attrs, self.connection)
        if new_node is not None:
            self.nodes.append((name, new_node))

    def endElement(self, name):
        self.nodes[-1][1].endElement(name, self.current_text, self.connection)
        if self.nodes[-1][0] == name:
            if hasattr(self.nodes[-1][1], 'endNode'):
                self.nodes[-1][1].endNode(self.connection)
            self.nodes.pop()
        self.current_text = ''

    def characters(self, content):
        self.current_text += content


class XmlHandlerWrapper(object):
    def __init__(self, root_node, connection):
        self.handler = XmlHandler(root_node, connection)
        self.parser = xml.sax.make_parser()
        self.parser.setContentHandler(self.handler)
        self.parser.setFeature(xml.sax.handler.feature_external_ges, 0)

    def parseString(self, content):
        return self.parser.parse(StringIO(content))
