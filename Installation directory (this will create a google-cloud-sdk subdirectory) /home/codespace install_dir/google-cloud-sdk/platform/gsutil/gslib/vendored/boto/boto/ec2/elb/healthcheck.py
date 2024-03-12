# Copyright (c) 2006-2012 Mitch Garnaat http://garnaat.org/
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


class HealthCheck(object):
    """
    Represents an EC2 Access Point Health Check. See
    :ref:`elb-configuring-a-health-check` for a walkthrough on configuring
    load balancer health checks.
    """
    def __init__(self, access_point=None, interval=30, target=None,
                 healthy_threshold=3, timeout=5, unhealthy_threshold=5):
        """
        :ivar str access_point: The name of the load balancer this
            health check is associated with.
        :ivar int interval: Specifies how many seconds there are between
            health checks.
        :ivar str target: Determines what to check on an instance. See the
            Amazon HealthCheck_ documentation for possible Target values.

        .. _HealthCheck: http://docs.amazonwebservices.com/ElasticLoadBalancing/latest/APIReference/API_HealthCheck.html
        """
        self.access_point = access_point
        self.interval = interval
        self.target = target
        self.healthy_threshold = healthy_threshold
        self.timeout = timeout
        self.unhealthy_threshold = unhealthy_threshold

    def __repr__(self):
        return 'HealthCheck:%s' % self.target

    def startElement(self, name, attrs, connection):
        return None

    def endElement(self, name, value, connection):
        if name == 'Interval':
            self.interval = int(value)
        elif name == 'Target':
            self.target = value
        elif name == 'HealthyThreshold':
            self.healthy_threshold = int(value)
        elif name == 'Timeout':
            self.timeout = int(value)
        elif name == 'UnhealthyThreshold':
            self.unhealthy_threshold = int(value)
        else:
            setattr(self, name, value)

    def update(self):
        """
        In the case where you have accessed an existing health check on a
        load balancer, this method applies this instance's health check
        values to the load balancer it is attached to.

        .. note:: This method will not do anything if the :py:attr:`access_point`
            attribute isn't set, as is the case with a newly instantiated
            HealthCheck instance.
        """
        if not self.access_point:
            return

        new_hc = self.connection.configure_health_check(self.access_point,
                                                        self)
        self.interval = new_hc.interval
        self.target = new_hc.target
        self.healthy_threshold = new_hc.healthy_threshold
        self.unhealthy_threshold = new_hc.unhealthy_threshold
        self.timeout = new_hc.timeout
