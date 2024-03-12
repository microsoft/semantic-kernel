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
# Created by Chris Huegle for TellApart, Inc.

class ConnectionSettingAttribute(object):
    """
    Represents the ConnectionSetting segment of ELB Attributes.
    """
    def __init__(self, connection=None):
        self.idle_timeout = None

    def __repr__(self):
        return 'ConnectionSettingAttribute(%s)' % (
            self.idle_timeout)

    def startElement(self, name, attrs, connection):
        pass

    def endElement(self, name, value, connection):
        if name == 'IdleTimeout':
            self.idle_timeout = int(value)

class CrossZoneLoadBalancingAttribute(object):
    """
    Represents the CrossZoneLoadBalancing segement of ELB Attributes.
    """
    def __init__(self, connection=None):
        self.enabled = None

    def __repr__(self):
        return 'CrossZoneLoadBalancingAttribute(%s)' % (
            self.enabled)

    def startElement(self, name, attrs, connection):
        pass

    def endElement(self, name, value, connection):
        if name == 'Enabled':
            if value.lower() == 'true':
                self.enabled = True
            else:
                self.enabled = False


class AccessLogAttribute(object):
    """
    Represents the AccessLog segment of ELB attributes.
    """
    def __init__(self, connection=None):
        self.enabled = None
        self.s3_bucket_name = None
        self.s3_bucket_prefix = None
        self.emit_interval = None

    def __repr__(self):
        return 'AccessLog(%s, %s, %s, %s)' % (
            self.enabled,
            self.s3_bucket_name,
            self.s3_bucket_prefix,
            self.emit_interval
        )

    def startElement(self, name, attrs, connection):
        pass

    def endElement(self, name, value, connection):
        if name == 'Enabled':
            if value.lower() == 'true':
                self.enabled = True
            else:
                self.enabled = False
        elif name == 'S3BucketName':
            self.s3_bucket_name = value
        elif name == 'S3BucketPrefix':
            self.s3_bucket_prefix = value
        elif name == 'EmitInterval':
            self.emit_interval = int(value)


class ConnectionDrainingAttribute(object):
    """
    Represents the ConnectionDraining segment of ELB attributes.
    """
    def __init__(self, connection=None):
        self.enabled = None
        self.timeout = None

    def __repr__(self):
        return 'ConnectionDraining(%s, %s)' % (
            self.enabled,
            self.timeout
        )

    def startElement(self, name, attrs, connection):
        pass

    def endElement(self, name, value, connection):
        if name == 'Enabled':
            if value.lower() == 'true':
                self.enabled = True
            else:
                self.enabled = False
        elif name == 'Timeout':
            self.timeout = int(value)


class LbAttributes(object):
    """
    Represents the Attributes of an Elastic Load Balancer.
    """
    def __init__(self, connection=None):
        self.connection = connection
        self.cross_zone_load_balancing = CrossZoneLoadBalancingAttribute(
            self.connection)
        self.access_log = AccessLogAttribute(self.connection)
        self.connection_draining = ConnectionDrainingAttribute(self.connection)
        self.connecting_settings = ConnectionSettingAttribute(self.connection)

    def __repr__(self):
        return 'LbAttributes(%s, %s, %s, %s)' % (
            repr(self.cross_zone_load_balancing),
            repr(self.access_log),
            repr(self.connection_draining),
            repr(self.connecting_settings))

    def startElement(self, name, attrs, connection):
        if name == 'CrossZoneLoadBalancing':
            return self.cross_zone_load_balancing
        if name == 'AccessLog':
            return self.access_log
        if name == 'ConnectionDraining':
            return self.connection_draining
        if name == 'ConnectionSettings':
            return self.connecting_settings

    def endElement(self, name, value, connection):
        pass
