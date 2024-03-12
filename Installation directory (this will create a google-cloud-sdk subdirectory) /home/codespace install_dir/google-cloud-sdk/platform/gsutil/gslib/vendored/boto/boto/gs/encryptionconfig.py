# Copyright 2018 Google Inc.
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
from boto.exception import InvalidEncryptionConfigError
from xml.sax import handler

# Relevant tags for the EncryptionConfiguration XML document.
DEFAULT_KMS_KEY_NAME = 'DefaultKmsKeyName'
ENCRYPTION_CONFIG = 'EncryptionConfiguration'

class EncryptionConfig(handler.ContentHandler):
    """Encapsulates the EncryptionConfiguration XML document"""
    def __init__(self):
        # Valid items in an EncryptionConfiguration XML node.
        self.default_kms_key_name = None

        self.parse_level = 0

    def validateParseLevel(self, tag, level):
        """Verify parse level for a given tag."""
        if self.parse_level != level:
            raise InvalidEncryptionConfigError(
                'Invalid tag %s at parse level %d: ' % (tag, self.parse_level))

    def startElement(self, name, attrs, connection):
        """SAX XML logic for parsing new element found."""
        if name == ENCRYPTION_CONFIG:
            self.validateParseLevel(name, 0)
            self.parse_level += 1;
        elif name == DEFAULT_KMS_KEY_NAME:
            self.validateParseLevel(name, 1)
            self.parse_level += 1;
        else:
            raise InvalidEncryptionConfigError('Unsupported tag ' + name)

    def endElement(self, name, value, connection):
        """SAX XML logic for parsing new element found."""
        if name == ENCRYPTION_CONFIG:
            self.validateParseLevel(name, 1)
            self.parse_level -= 1;
        elif name == DEFAULT_KMS_KEY_NAME:
            self.validateParseLevel(name, 2)
            self.parse_level -= 1;
            self.default_kms_key_name = value.strip()
        else:
            raise InvalidEncryptionConfigError('Unsupported end tag ' + name)

    def to_xml(self):
        """Convert EncryptionConfig object into XML string representation."""
        s = ['<%s>' % ENCRYPTION_CONFIG]
        if self.default_kms_key_name:
            s.append('<%s>%s</%s>' % (DEFAULT_KMS_KEY_NAME,
                                      self.default_kms_key_name,
                                      DEFAULT_KMS_KEY_NAME))
        s.append('</%s>' % ENCRYPTION_CONFIG)
        return ''.join(s)
