# Copyright (c) 2008 Chris Moyer http://coredumped.org/
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

class LayoutParameters(object):

    def __init__(self, layoutParameters=None):
        if layoutParameters is None:
            layoutParameters = []
        self.layoutParameters = layoutParameters

    def add(self, req):
        self.layoutParameters.append(req)

    def get_as_params(self):
        params = {}
        assert(len(self.layoutParameters) <= 25)
        for n, layoutParameter in enumerate(self.layoutParameters):
            kv = layoutParameter.get_as_params()
            for key in kv:
                params['HITLayoutParameter.%s.%s' % ((n+1), key) ] = kv[key]
        return params

class LayoutParameter(object):
    """
    Representation of a single HIT layout parameter
    """

    def __init__(self, name, value):
        self.name = name
        self.value = value

    def get_as_params(self):
        params =  {
            "Name": self.name,
            "Value": self.value,
        }
        return params
