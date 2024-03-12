# Copyright (c) 2010 Mitch Garnaat http://garnaat.org/
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
Represents an EC2 Bundle Task
"""

from boto.ec2.ec2object import EC2Object


class BundleInstanceTask(EC2Object):

    def __init__(self, connection=None):
        super(BundleInstanceTask, self).__init__(connection)
        self.id = None
        self.instance_id = None
        self.progress = None
        self.start_time = None
        self.state = None
        self.bucket = None
        self.prefix = None
        self.upload_policy = None
        self.upload_policy_signature = None
        self.update_time = None
        self.code = None
        self.message = None

    def __repr__(self):
        return 'BundleInstanceTask:%s' % self.id

    def startElement(self, name, attrs, connection):
        return None

    def endElement(self, name, value, connection):
        if name == 'bundleId':
            self.id = value
        elif name == 'instanceId':
            self.instance_id = value
        elif name == 'progress':
            self.progress = value
        elif name == 'startTime':
            self.start_time = value
        elif name == 'state':
            self.state = value
        elif name == 'bucket':
            self.bucket = value
        elif name == 'prefix':
            self.prefix = value
        elif name == 'uploadPolicy':
            self.upload_policy = value
        elif name == 'uploadPolicySignature':
            self.upload_policy_signature = value
        elif name == 'updateTime':
            self.update_time = value
        elif name == 'code':
            self.code = value
        elif name == 'message':
            self.message = value
        else:
            setattr(self, name, value)
