# Copyright (c) 2006-2009 Mitch Garnaat http://garnaat.org/
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


class InstanceState(object):
    """
    Represents the state of an EC2 Load Balancer Instance
    """

    def __init__(self, load_balancer=None, description=None,
                 state=None, instance_id=None, reason_code=None):
        """
        :ivar boto.ec2.elb.loadbalancer.LoadBalancer load_balancer: The
            load balancer this instance is registered to.
        :ivar str description: A description of the instance.
        :ivar str instance_id: The EC2 instance ID.
        :ivar str reason_code: Provides information about the cause of
            an OutOfService instance. Specifically, it indicates whether the
            cause is Elastic Load Balancing or the instance behind the
            LoadBalancer.
        :ivar str state: Specifies the current state of the instance.
        """
        self.load_balancer = load_balancer
        self.description = description
        self.state = state
        self.instance_id = instance_id
        self.reason_code = reason_code

    def __repr__(self):
        return 'InstanceState:(%s,%s)' % (self.instance_id, self.state)

    def startElement(self, name, attrs, connection):
        return None

    def endElement(self, name, value, connection):
        if name == 'Description':
            self.description = value
        elif name == 'State':
            self.state = value
        elif name == 'InstanceId':
            self.instance_id = value
        elif name == 'ReasonCode':
            self.reason_code = value
        else:
            setattr(self, name, value)
