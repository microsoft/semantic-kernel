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
Represents an EC2 Spot Instance Request
"""

from boto.ec2.ec2object import EC2Object


class SpotPriceHistory(EC2Object):

    def __init__(self, connection=None):
        super(SpotPriceHistory, self).__init__(connection)
        self.price = 0.0
        self.instance_type = None
        self.product_description = None
        self.timestamp = None
        self.availability_zone = None

    def __repr__(self):
        return 'SpotPriceHistory(%s):%2f' % (self.instance_type, self.price)

    def endElement(self, name, value, connection):
        if name == 'instanceType':
            self.instance_type = value
        elif name == 'spotPrice':
            self.price = float(value)
        elif name == 'productDescription':
            self.product_description = value
        elif name == 'timestamp':
            self.timestamp = value
        elif name == 'availabilityZone':
            self.availability_zone = value
        else:
            setattr(self, name, value)
