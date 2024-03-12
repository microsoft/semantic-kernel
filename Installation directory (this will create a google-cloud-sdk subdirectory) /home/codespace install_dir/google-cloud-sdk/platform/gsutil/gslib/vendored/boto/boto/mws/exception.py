# Copyright (c) 2012-2014 Andy Davidoff http://www.disruptek.com/
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
from boto.exception import BotoServerError
from boto.mws.response import ResponseFactory


class ResponseErrorFactory(ResponseFactory):

    def __call__(self, status, reason, body=None):
        server = BotoServerError(status, reason, body=body)
        supplied = self.find_element(server.error_code, '', ResponseError)
        print(supplied.__name__)
        return supplied(status, reason, body=body)


class ResponseError(BotoServerError):
    """
    Undefined response error.
    """
    retry = False

    def __repr__(self):
        return '{0.__name__}({1.reason}: "{1.message}")' \
            .format(self.__class__, self)

    def __str__(self):
        doc = self.__doc__ and self.__doc__.strip() + "\n" or ''
        return '{1.__name__}: {0.reason} {2}\n{3}' \
               '{0.message}'.format(self, self.__class__,
                                    self.retry and '(Retriable)' or '', doc)


class RetriableResponseError(ResponseError):
    retry = True


class InvalidParameterValue(ResponseError):
    """
    One or more parameter values in the request is invalid.
    """


class InvalidParameter(ResponseError):
    """
    One or more parameters in the request is invalid.
    """


class InvalidAddress(ResponseError):
    """
    Invalid address.
    """
