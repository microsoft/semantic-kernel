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

class Price(object):

    def __init__(self, amount=0.0, currency_code='USD'):
        self.amount = amount
        self.currency_code = currency_code
        self.formatted_price = ''

    def __repr__(self):
        if self.formatted_price:
            return self.formatted_price
        else:
            return str(self.amount)

    def startElement(self, name, attrs, connection):
        return None

    def endElement(self, name, value, connection):
        if name == 'Amount':
            self.amount = float(value)
        elif name == 'CurrencyCode':
            self.currency_code = value
        elif name == 'FormattedPrice':
            self.formatted_price = value

    def get_as_params(self, label, ord=1):
        return {'%s.%d.Amount'%(label, ord) : str(self.amount),
                '%s.%d.CurrencyCode'%(label, ord) : self.currency_code}
