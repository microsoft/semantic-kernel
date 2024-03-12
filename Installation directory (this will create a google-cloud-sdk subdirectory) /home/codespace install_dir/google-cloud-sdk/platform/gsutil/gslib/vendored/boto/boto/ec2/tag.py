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


class TagSet(dict):
    """
    A TagSet is used to collect the tags associated with a particular
    EC2 resource.  Not all resources can be tagged but for those that
    can, this dict object will be used to collect those values.  See
    :class:`boto.ec2.ec2object.TaggedEC2Object` for more details.
    """

    def __init__(self, connection=None):
        self.connection = connection
        self._current_key = None
        self._current_value = None

    def startElement(self, name, attrs, connection):
        if name == 'item':
            self._current_key = None
            self._current_value = None
        return None

    def endElement(self, name, value, connection):
        if name == 'key':
            self._current_key = value
        elif name == 'value':
            self._current_value = value
        elif name == 'item':
            self[self._current_key] = self._current_value


class Tag(object):
    """
    A Tag is used when creating or listing all tags related to
    an AWS account.  It records not only the key and value but
    also the ID of the resource to which the tag is attached
    as well as the type of the resource.
    """

    def __init__(self, connection=None, res_id=None, res_type=None,
                 name=None, value=None):
        self.connection = connection
        self.res_id = res_id
        self.res_type = res_type
        self.name = name
        self.value = value

    def __repr__(self):
        return 'Tag:%s' % self.name

    def startElement(self, name, attrs, connection):
        return None

    def endElement(self, name, value, connection):
        if name == 'resourceId':
            self.res_id = value
        elif name == 'resourceType':
            self.res_type = value
        elif name == 'key':
            self.name = value
        elif name == 'value':
            self.value = value
        else:
            setattr(self, name, value)
