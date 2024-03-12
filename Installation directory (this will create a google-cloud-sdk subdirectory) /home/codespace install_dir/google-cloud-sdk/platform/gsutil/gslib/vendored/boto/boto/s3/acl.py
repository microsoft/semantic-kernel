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

from boto.s3.user import User


CannedACLStrings = ['private', 'public-read',
                    'public-read-write', 'authenticated-read',
                    'bucket-owner-read', 'bucket-owner-full-control',
                    'log-delivery-write']


class Policy(object):

    def __init__(self, parent=None):
        self.parent = parent
        self.namespace = None
        self.acl = None

    def __repr__(self):
        grants = []
        for g in self.acl.grants:
            if g.id == self.owner.id:
                grants.append("%s (owner) = %s" % (g.display_name, g.permission))
            else:
                if g.type == 'CanonicalUser':
                    u = g.display_name
                elif g.type == 'Group':
                    u = g.uri
                else:
                    u = g.email_address
                grants.append("%s = %s" % (u, g.permission))
        return "<Policy: %s>" % ", ".join(grants)

    def startElement(self, name, attrs, connection):
        if name == 'AccessControlPolicy':
            self.namespace = attrs.get('xmlns', None)
            return None
        if name == 'Owner':
            self.owner = User(self)
            return self.owner
        elif name == 'AccessControlList':
            self.acl = ACL(self)
            return self.acl
        else:
            return None

    def endElement(self, name, value, connection):
        if name == 'Owner':
            pass
        elif name == 'AccessControlList':
            pass
        else:
            setattr(self, name, value)

    def to_xml(self):
        if self.namespace is not None:
            s = '<AccessControlPolicy xmlns="{0}">'.format(self.namespace)
        else:
            s = '<AccessControlPolicy>'
        s += self.owner.to_xml()
        s += self.acl.to_xml()
        s += '</AccessControlPolicy>'
        return s


class ACL(object):

    def __init__(self, policy=None):
        self.policy = policy
        self.grants = []

    def add_grant(self, grant):
        self.grants.append(grant)

    def add_email_grant(self, permission, email_address):
        grant = Grant(permission=permission, type='AmazonCustomerByEmail',
                      email_address=email_address)
        self.grants.append(grant)

    def add_user_grant(self, permission, user_id, display_name=None):
        grant = Grant(permission=permission, type='CanonicalUser', id=user_id, display_name=display_name)
        self.grants.append(grant)

    def startElement(self, name, attrs, connection):
        if name == 'Grant':
            self.grants.append(Grant(self))
            return self.grants[-1]
        else:
            return None

    def endElement(self, name, value, connection):
        if name == 'Grant':
            pass
        else:
            setattr(self, name, value)

    def to_xml(self):
        s = '<AccessControlList>'
        for grant in self.grants:
            s += grant.to_xml()
        s += '</AccessControlList>'
        return s


class Grant(object):

    NameSpace = 'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"'

    def __init__(self, permission=None, type=None, id=None,
                 display_name=None, uri=None, email_address=None):
        self.permission = permission
        self.id = id
        self.display_name = display_name
        self.uri = uri
        self.email_address = email_address
        self.type = type

    def startElement(self, name, attrs, connection):
        if name == 'Grantee':
            self.type = attrs['xsi:type']
        return None

    def endElement(self, name, value, connection):
        if name == 'ID':
            self.id = value
        elif name == 'DisplayName':
            self.display_name = value
        elif name == 'URI':
            self.uri = value
        elif name == 'EmailAddress':
            self.email_address = value
        elif name == 'Grantee':
            pass
        elif name == 'Permission':
            self.permission = value
        else:
            setattr(self, name, value)

    def to_xml(self):
        s = '<Grant>'
        s += '<Grantee %s xsi:type="%s">' % (self.NameSpace, self.type)
        if self.type == 'CanonicalUser':
            s += '<ID>%s</ID>' % self.id
            s += '<DisplayName>%s</DisplayName>' % self.display_name
        elif self.type == 'Group':
            s += '<URI>%s</URI>' % self.uri
        else:
            s += '<EmailAddress>%s</EmailAddress>' % self.email_address
        s += '</Grantee>'
        s += '<Permission>%s</Permission>' % self.permission
        s += '</Grant>'
        return s
