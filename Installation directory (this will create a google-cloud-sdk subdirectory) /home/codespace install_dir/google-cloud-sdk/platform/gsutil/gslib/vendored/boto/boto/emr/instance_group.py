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


class InstanceGroup(object):
    def __init__(self, num_instances, role, type, market, name, bidprice=None):
        self.num_instances = num_instances
        self.role = role
        self.type = type
        self.market = market
        self.name = name
        if market == 'SPOT':
            if not bidprice:
                raise ValueError('bidprice must be specified if market == SPOT')
            self.bidprice = str(bidprice)

    def __repr__(self):
        if self.market == 'SPOT':
            return '%s.%s(name=%r, num_instances=%r, role=%r, type=%r, market = %r, bidprice = %r)' % (
                self.__class__.__module__, self.__class__.__name__,
                self.name, self.num_instances, self.role, self.type, self.market,
                self.bidprice)
        else:
            return '%s.%s(name=%r, num_instances=%r, role=%r, type=%r, market = %r)' % (
                self.__class__.__module__, self.__class__.__name__,
                self.name, self.num_instances, self.role, self.type, self.market)
