# Copyright (c) 2010 Mitch Garnaat http://garnaat.org/
# Copyright (c) 2010, Eucalyptus Systems, Inc.
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

import os

class Converter(object):

    @classmethod
    def convert_string(cls, param, value):
        # TODO: could do length validation, etc. here
        if not isinstance(value, basestring):
            raise ValueError
        return value

    @classmethod
    def convert_integer(cls, param, value):
        # TODO: could do range checking here
        return int(value)

    @classmethod
    def convert_boolean(cls, param, value):
        """
        For command line arguments, just the presence
        of the option means True so just return True
        """
        return True

    @classmethod
    def convert_file(cls, param, value):
        if os.path.exists(value) and not os.path.isdir(value):
            return value
        raise ValueError

    @classmethod
    def convert_dir(cls, param, value):
        if os.path.isdir(value):
            return value
        raise ValueError

    @classmethod
    def convert(cls, param, value):
        try:
            if hasattr(cls, 'convert_'+param.ptype):
                mthd = getattr(cls, 'convert_'+param.ptype)
            else:
                mthd = cls.convert_string
            return mthd(param, value)
        except:
            raise ValidationException(param, '')

class Param(Converter):

    def __init__(self, name=None, ptype='string', optional=True,
                 short_name=None, long_name=None, doc='',
                 metavar=None, cardinality=1, default=None,
                 choices=None, encoder=None, request_param=True):
        self.name = name
        self.ptype = ptype
        self.optional = optional
        self.short_name = short_name
        self.long_name = long_name
        self.doc = doc
        self.metavar = metavar
        self.cardinality = cardinality
        self.default = default
        self.choices = choices
        self.encoder = encoder
        self.request_param = request_param

    @property
    def optparse_long_name(self):
        ln = None
        if self.long_name:
            ln = '--%s' % self.long_name
        return ln

    @property
    def synopsis_long_name(self):
        ln = None
        if self.long_name:
            ln = '--%s' % self.long_name
        return ln

    @property
    def getopt_long_name(self):
        ln = None
        if self.long_name:
            ln = '%s' % self.long_name
            if self.ptype != 'boolean':
                ln += '='
        return ln

    @property
    def optparse_short_name(self):
        sn = None
        if self.short_name:
            sn = '-%s' % self.short_name
        return sn

    @property
    def synopsis_short_name(self):
        sn = None
        if self.short_name:
            sn = '-%s' % self.short_name
        return sn

    @property
    def getopt_short_name(self):
        sn = None
        if self.short_name:
            sn = '%s' % self.short_name
            if self.ptype != 'boolean':
                sn += ':'
        return sn

    def convert(self, value):
        """
        Convert a string value as received in the command line
        tools and convert to the appropriate type of value.
        Raise a ValidationError if the value can't be converted.

        :type value: str
        :param value: The value to convert.  This should always
                      be a string.
        """
        return super(Param, self).convert(self,value)


