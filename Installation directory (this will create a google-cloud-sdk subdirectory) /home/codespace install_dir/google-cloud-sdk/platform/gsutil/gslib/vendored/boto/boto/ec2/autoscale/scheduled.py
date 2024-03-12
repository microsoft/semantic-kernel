# Copyright (c) 2009-2010 Reza Lotun http://reza.lotun.name/
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


class ScheduledUpdateGroupAction(object):
    def __init__(self, connection=None):
        self.connection = connection
        self.name = None
        self.action_arn = None
        self.as_group = None
        self.time = None
        self.start_time = None
        self.end_time = None
        self.recurrence = None
        self.desired_capacity = None
        self.max_size = None
        self.min_size = None

    def __repr__(self):
        return 'ScheduledUpdateGroupAction:%s' % self.name

    def startElement(self, name, attrs, connection):
        return None

    def endElement(self, name, value, connection):
        if name == 'DesiredCapacity':
            self.desired_capacity = value
        elif name == 'ScheduledActionName':
            self.name = value
        elif name == 'AutoScalingGroupName':
            self.as_group = value
        elif name == 'MaxSize':
            self.max_size = int(value)
        elif name == 'MinSize':
            self.min_size = int(value)
        elif name == 'ScheduledActionARN':
            self.action_arn = value
        elif name == 'Recurrence':
            self.recurrence = value
        elif name == 'Time':
            try:
                self.time = datetime.strptime(value, '%Y-%m-%dT%H:%M:%S.%fZ')
            except ValueError:
                self.time = datetime.strptime(value, '%Y-%m-%dT%H:%M:%SZ')
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
        else:
            setattr(self, name, value)
