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

"""
Represents an EC2 Spot Instance Datafeed Subscription
"""
from boto.ec2.ec2object import EC2Object
from boto.ec2.spotinstancerequest import SpotInstanceStateFault


class SpotDatafeedSubscription(EC2Object):

    def __init__(self, connection=None, owner_id=None,
                 bucket=None, prefix=None, state=None, fault=None):
        super(SpotDatafeedSubscription, self).__init__(connection)
        self.owner_id = owner_id
        self.bucket = bucket
        self.prefix = prefix
        self.state = state
        self.fault = fault

    def __repr__(self):
        return 'SpotDatafeedSubscription:%s' % self.bucket

    def startElement(self, name, attrs, connection):
        if name == 'fault':
            self.fault = SpotInstanceStateFault()
            return self.fault
        else:
            return None

    def endElement(self, name, value, connection):
        if name == 'ownerId':
            self.owner_id = value
        elif name == 'bucket':
            self.bucket = value
        elif name == 'prefix':
            self.prefix = value
        elif name == 'state':
            self.state = value
        else:
            setattr(self, name, value)

    def delete(self, dry_run=False):
        return self.connection.delete_spot_datafeed_subscription(
            dry_run=dry_run
        )
