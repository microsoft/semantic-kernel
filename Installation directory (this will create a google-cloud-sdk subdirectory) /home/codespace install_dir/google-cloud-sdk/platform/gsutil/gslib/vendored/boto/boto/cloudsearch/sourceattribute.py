# Copyright (c) 202 Mitch Garnaat http://garnaat.org/
# Copyright (c) 2012 Amazon.com, Inc. or its affiliates.
# All Rights Reserved
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

class SourceAttribute(object):
    """
    Provide information about attributes for an index field.
    A maximum of 20 source attributes can be configured for
    each index field.

    :ivar default: Optional default value if the source attribute
        is not specified in a document.
        
    :ivar name: The name of the document source field to add
        to this ``IndexField``.

    :ivar data_function: Identifies the transformation to apply
        when copying data from a source attribute.
        
    :ivar data_map: The value is a dict with the following keys:
        * cases - A dict that translates source field values
            to custom values.
        * default - An optional default value to use if the
            source attribute is not specified in a document.
        * name - the name of the document source field to add
            to this ``IndexField``
    :ivar data_trim_title: Trims common title words from a source
        document attribute when populating an ``IndexField``.
        This can be used to create an ``IndexField`` you can
        use for sorting.  The value is a dict with the following
        fields:
        * default - An optional default value.
        * language - an IETF RFC 4646 language code.
        * separator - The separator that follows the text to trim.
        * name - The name of the document source field to add.
    """

    ValidDataFunctions = ('Copy', 'TrimTitle', 'Map')

    def __init__(self):
        self.data_copy = {}
        self._data_function = self.ValidDataFunctions[0]
        self.data_map = {}
        self.data_trim_title = {}

    @property
    def data_function(self):
        return self._data_function

    @data_function.setter
    def data_function(self, value):
        if value not in self.ValidDataFunctions:
            valid = '|'.join(self.ValidDataFunctions)
            raise ValueError('data_function must be one of: %s' % valid)
        self._data_function = value
