# Copyright (c) 2006-2009 Mitch Garnaat http://garnaat.org/
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

import uuid

class OriginAccessIdentity(object):
    def __init__(self, connection=None, config=None, id='',
                 s3_user_id='', comment=''):
        self.connection = connection
        self.config = config
        self.id = id
        self.s3_user_id = s3_user_id
        self.comment = comment
        self.etag = None

    def startElement(self, name, attrs, connection):
        if name == 'CloudFrontOriginAccessIdentityConfig':
            self.config = OriginAccessIdentityConfig()
            return self.config
        else:
            return None

    def endElement(self, name, value, connection):
        if name == 'Id':
            self.id = value
        elif name == 'S3CanonicalUserId':
            self.s3_user_id = value
        elif name == 'Comment':
            self.comment = value
        else:
            setattr(self, name, value)

    def update(self, comment=None):
        new_config = OriginAccessIdentityConfig(self.connection,
                                                self.config.caller_reference,
                                                self.config.comment)
        if comment is not None:
            new_config.comment = comment
        self.etag = self.connection.set_origin_identity_config(self.id, self.etag, new_config)
        self.config = new_config

    def delete(self):
        return self.connection.delete_origin_access_identity(self.id, self.etag)

    def uri(self):
        return 'origin-access-identity/cloudfront/%s' % self.id


class OriginAccessIdentityConfig(object):
    def __init__(self, connection=None, caller_reference='', comment=''):
        self.connection = connection
        if caller_reference:
            self.caller_reference = caller_reference
        else:
            self.caller_reference = str(uuid.uuid4())
        self.comment = comment

    def to_xml(self):
        s = '<?xml version="1.0" encoding="UTF-8"?>\n'
        s += '<CloudFrontOriginAccessIdentityConfig xmlns="http://cloudfront.amazonaws.com/doc/2009-09-09/">\n'
        s += '  <CallerReference>%s</CallerReference>\n' % self.caller_reference
        if self.comment:
            s += '  <Comment>%s</Comment>\n' % self.comment
        s += '</CloudFrontOriginAccessIdentityConfig>\n'
        return s

    def startElement(self, name, attrs, connection):
        return None

    def endElement(self, name, value, connection):
        if name == 'Comment':
            self.comment = value
        elif name == 'CallerReference':
            self.caller_reference = value
        else:
            setattr(self, name, value)


class OriginAccessIdentitySummary(object):
    def __init__(self, connection=None, id='',
                 s3_user_id='', comment=''):
        self.connection = connection
        self.id = id
        self.s3_user_id = s3_user_id
        self.comment = comment
        self.etag = None

    def startElement(self, name, attrs, connection):
        return None

    def endElement(self, name, value, connection):
        if name == 'Id':
            self.id = value
        elif name == 'S3CanonicalUserId':
            self.s3_user_id = value
        elif name == 'Comment':
            self.comment = value
        else:
            setattr(self, name, value)

    def get_origin_access_identity(self):
        return self.connection.get_origin_access_identity_info(self.id)

