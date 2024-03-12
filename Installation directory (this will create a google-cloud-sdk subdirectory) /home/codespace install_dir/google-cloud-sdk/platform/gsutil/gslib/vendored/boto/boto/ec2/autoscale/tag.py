# Copyright (c) 2012 Mitch Garnaat http://garnaat.org/
# Copyright (c) 2012 Amazon.com, Inc. or its affiliates.  All Rights Reserved
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


class Tag(object):
    """
    A name/value tag on an AutoScalingGroup resource.

    :ivar key: The key of the tag.
    :ivar value: The value of the tag.
    :ivar propagate_at_launch: Boolean value which specifies whether the
        new tag will be applied to instances launched after the tag is created.
    :ivar resource_id: The name of the autoscaling group.
    :ivar resource_type: The only supported resource type at this time
        is "auto-scaling-group".
    """

    def __init__(self, connection=None, key=None, value=None,
                 propagate_at_launch=False, resource_id=None,
                 resource_type='auto-scaling-group'):
        self.connection = connection
        self.key = key
        self.value = value
        self.propagate_at_launch = propagate_at_launch
        self.resource_id = resource_id
        self.resource_type = resource_type

    def __repr__(self):
        return 'Tag(%s=%s)' % (self.key, self.value)

    def startElement(self, name, attrs, connection):
        pass

    def endElement(self, name, value, connection):
        if name == 'Key':
            self.key = value
        elif name == 'Value':
            self.value = value
        elif name == 'PropagateAtLaunch':
            if value.lower() == 'true':
                self.propagate_at_launch = True
            else:
                self.propagate_at_launch = False
        elif name == 'ResourceId':
            self.resource_id = value
        elif name == 'ResourceType':
            self.resource_type = value

    def build_params(self, params, i):
        """
        Populates a dictionary with the name/value pairs necessary
        to identify this Tag in a request.
        """
        prefix = 'Tags.member.%d.' % i
        params[prefix + 'ResourceId'] = self.resource_id
        params[prefix + 'ResourceType'] = self.resource_type
        params[prefix + 'Key'] = self.key
        params[prefix + 'Value'] = self.value
        if self.propagate_at_launch:
            params[prefix + 'PropagateAtLaunch'] = 'true'
        else:
            params[prefix + 'PropagateAtLaunch'] = 'false'

    def delete(self):
        return self.connection.delete_tags([self])
