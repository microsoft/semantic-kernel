# Copyright 2012 Google Inc.
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

import types
from boto.gs.user import User
from boto.exception import InvalidCorsError
from xml.sax import handler

# Relevant tags for the CORS XML document.
CORS_CONFIG = 'CorsConfig'
CORS        = 'Cors'
ORIGINS     = 'Origins'
ORIGIN      = 'Origin'
METHODS     = 'Methods'
METHOD      = 'Method'
HEADERS     = 'ResponseHeaders'
HEADER      = 'ResponseHeader'
MAXAGESEC   = 'MaxAgeSec'

class Cors(handler.ContentHandler):
    """Encapsulates the CORS configuration XML document"""
    def __init__(self):
        # List of CORS elements found within a CorsConfig element.
        self.cors = []
        # List of collections (e.g. Methods, ResponseHeaders, Origins)
        # found within a CORS element. We use a list of lists here
        # instead of a dictionary because the collections need to be
        # preserved in the order in which they appear in the input XML
        # document (and Python dictionary keys are inherently unordered).
        # The elements on this list are two element tuples of the form
        # (collection name, [list of collection contents]).
        self.collections = []
        # Lists of elements within a collection. Again a list is needed to
        # preserve ordering but also because the same element may appear
        # multiple times within a collection.
        self.elements = []
        # Dictionary mapping supported collection names to element types
        # which may be contained within each.
        self.legal_collections = {
            ORIGINS : [ORIGIN],
            METHODS : [METHOD],
            HEADERS : [HEADER],
            MAXAGESEC: []
        }
        # List of supported element types within any collection, used for
        # checking validadity of a parsed element name.
        self.legal_elements = [ORIGIN, METHOD, HEADER]

        self.parse_level = 0
        self.collection = None
        self.element = None

    def validateParseLevel(self, tag, level):
        """Verify parse level for a given tag."""
        if self.parse_level != level:
            raise InvalidCorsError('Invalid tag %s at parse level %d: ' %
                                   (tag, self.parse_level))

    def startElement(self, name, attrs, connection):
        """SAX XML logic for parsing new element found."""
        if name == CORS_CONFIG:
            self.validateParseLevel(name, 0)
            self.parse_level += 1;
        elif name == CORS:
            self.validateParseLevel(name, 1)
            self.parse_level += 1;
        elif name in self.legal_collections:
            self.validateParseLevel(name, 2)
            self.parse_level += 1;
            self.collection = name
        elif name in self.legal_elements:
            self.validateParseLevel(name, 3)
            # Make sure this tag is found inside a collection tag.
            if self.collection is None:
                raise InvalidCorsError('Tag %s found outside collection' % name)
            # Make sure this tag is allowed for the current collection tag.
            if name not in self.legal_collections[self.collection]:
                raise InvalidCorsError('Tag %s not allowed in %s collection' %
                                       (name, self.collection))
            self.element = name
        else:
            raise InvalidCorsError('Unsupported tag ' + name)

    def endElement(self, name, value, connection):
        """SAX XML logic for parsing new element found."""
        if name == CORS_CONFIG:
            self.validateParseLevel(name, 1)
            self.parse_level -= 1;
        elif name == CORS:
            self.validateParseLevel(name, 2)
            self.parse_level -= 1;
            # Terminating a CORS element, save any collections we found
            # and re-initialize collections list.
            self.cors.append(self.collections)
            self.collections = []
        elif name in self.legal_collections:
            self.validateParseLevel(name, 3)
            if name != self.collection:
              raise InvalidCorsError('Mismatched start and end tags (%s/%s)' %
                                     (self.collection, name))
            self.parse_level -= 1;
            if not self.legal_collections[name]:
              # If this collection doesn't contain any sub-elements, store
              # a tuple of name and this tag's element value.
              self.collections.append((name, value.strip()))
            else:
              # Otherwise, we're terminating a collection of sub-elements,
              # so store a tuple of name and list of contained elements.
              self.collections.append((name, self.elements))
            self.elements = []
            self.collection = None
        elif name in self.legal_elements:
            self.validateParseLevel(name, 3)
            # Make sure this tag is found inside a collection tag.
            if self.collection is None:
                raise InvalidCorsError('Tag %s found outside collection' % name)
            # Make sure this end tag is allowed for the current collection tag.
            if name not in self.legal_collections[self.collection]:
                raise InvalidCorsError('Tag %s not allowed in %s collection' %
                                       (name, self.collection))
            if name != self.element:
              raise InvalidCorsError('Mismatched start and end tags (%s/%s)' %
                                     (self.element, name))
            # Terminating an element tag, add it to the list of elements
            # for the current collection.
            self.elements.append((name, value.strip()))
            self.element = None
        else:
            raise InvalidCorsError('Unsupported end tag ' + name)

    def to_xml(self):
        """Convert CORS object into XML string representation."""
        s = '<' + CORS_CONFIG + '>'
        for collections in self.cors:
          s += '<' + CORS + '>'
          for (collection, elements_or_value) in collections:
            assert collection is not None
            s += '<' + collection + '>'
            # If collection elements has type string, append atomic value,
            # otherwise, append sequence of values in named tags.
            if isinstance(elements_or_value, str):
              s += elements_or_value
            else:
              for (name, value) in elements_or_value:
                assert name is not None
                assert value is not None
                s += '<' + name + '>' + value + '</' + name + '>'
            s += '</' + collection + '>'
          s += '</' + CORS + '>'
        s += '</' + CORS_CONFIG + '>'
        return s
