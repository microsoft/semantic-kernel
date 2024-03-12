# Copyright (c) 2011 Blue Pines Technologies LLC, Brad Carleton
# www.bluepines.org
# All rights reserved.
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


class Status(object):
    def __init__(self, route53connection, change_dict):
        self.route53connection = route53connection
        for key in change_dict:
            if key == 'Id':
                self.__setattr__(key.lower(),
                                 change_dict[key].replace('/change/', ''))
            else:
                self.__setattr__(key.lower(), change_dict[key])

    def update(self):
        """ Update the status of this request."""
        status = self.route53connection.get_change(self.id)['GetChangeResponse']['ChangeInfo']['Status']
        self.status = status
        return status

    def __repr__(self):
        return '<Status:%s>' % self.status
