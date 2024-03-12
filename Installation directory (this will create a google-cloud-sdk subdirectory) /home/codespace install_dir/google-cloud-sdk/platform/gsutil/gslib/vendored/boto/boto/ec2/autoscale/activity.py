# Copyright (c) 2009-2011 Reza Lotun http://reza.lotun.name/
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

from datetime import datetime


class Activity(object):
    def __init__(self, connection=None):
        self.connection = connection
        self.start_time = None
        self.end_time = None
        self.activity_id = None
        self.progress = None
        self.status_code = None
        self.cause = None
        self.description = None
        self.status_message = None
        self.group_name = None

    def __repr__(self):
        return 'Activity<%s>: For group:%s, progress:%s, cause:%s' % (self.activity_id,
                                                                      self.group_name,
                                                                      self.status_message,
                                                                      self.cause)

    def startElement(self, name, attrs, connection):
        return None

    def endElement(self, name, value, connection):
        if name == 'ActivityId':
            self.activity_id = value
        elif name == 'AutoScalingGroupName':
            self.group_name = value
        elif name == 'StartTime':
            try:
                self.start_time = datetime.strptime(value, '%Y-%m-%dT%H:%M:%S.%fZ')
            except ValueError:
                self.start_time = datetime.strptime(value, '%Y-%m-%dT%H:%M:%SZ')
        elif name == 'EndTime':
            try:
                self.end_time = datetime.strptime(value, '%Y-%m-%dT%H:%M:%S.%fZ')
            except ValueError:
                self.end_time = datetime.strptime(value, '%Y-%m-%dT%H:%M:%SZ')
        elif name == 'Progress':
            self.progress = value
        elif name == 'Cause':
            self.cause = value
        elif name == 'Description':
            self.description = value
        elif name == 'StatusMessage':
            self.status_message = value
        elif name == 'StatusCode':
            self.status_code = value
        else:
            setattr(self, name, value)
