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
#

from boto.ec2.cloudwatch.alarm import MetricAlarm
from boto.ec2.cloudwatch.dimension import Dimension


class Metric(object):

    Statistics = ['Minimum', 'Maximum', 'Sum', 'Average', 'SampleCount']
    Units = ['Seconds', 'Microseconds', 'Milliseconds', 'Bytes', 'Kilobytes',
             'Megabytes', 'Gigabytes', 'Terabytes', 'Bits', 'Kilobits',
             'Megabits', 'Gigabits', 'Terabits', 'Percent', 'Count',
             'Bytes/Second', 'Kilobytes/Second', 'Megabytes/Second',
             'Gigabytes/Second', 'Terabytes/Second', 'Bits/Second',
             'Kilobits/Second', 'Megabits/Second', 'Gigabits/Second',
             'Terabits/Second', 'Count/Second', None]

    def __init__(self, connection=None):
        self.connection = connection
        self.name = None
        self.namespace = None
        self.dimensions = None

    def __repr__(self):
        return 'Metric:%s' % self.name

    def startElement(self, name, attrs, connection):
        if name == 'Dimensions':
            self.dimensions = Dimension()
            return self.dimensions

    def endElement(self, name, value, connection):
        if name == 'MetricName':
            self.name = value
        elif name == 'Namespace':
            self.namespace = value
        else:
            setattr(self, name, value)

    def query(self, start_time, end_time, statistics, unit=None, period=60):
        """
        :type start_time: datetime
        :param start_time: The time stamp to use for determining the
            first datapoint to return. The value specified is
            inclusive; results include datapoints with the time stamp
            specified.

        :type end_time: datetime
        :param end_time: The time stamp to use for determining the
            last datapoint to return. The value specified is
            exclusive; results will include datapoints up to the time
            stamp specified.

        :type statistics: list
        :param statistics: A list of statistics names Valid values:
            Average | Sum | SampleCount | Maximum | Minimum

        :type unit: string
        :param unit: The unit for the metric.  Value values are:
            Seconds | Microseconds | Milliseconds | Bytes | Kilobytes |
            Megabytes | Gigabytes | Terabytes | Bits | Kilobits |
            Megabits | Gigabits | Terabits | Percent | Count |
            Bytes/Second | Kilobytes/Second | Megabytes/Second |
            Gigabytes/Second | Terabytes/Second | Bits/Second |
            Kilobits/Second | Megabits/Second | Gigabits/Second |
            Terabits/Second | Count/Second | None

        :type period: integer
        :param period: The granularity, in seconds, of the returned datapoints.
            Period must be at least 60 seconds and must be a multiple
            of 60. The default value is 60.

        """
        if not isinstance(statistics, list):
            statistics = [statistics]
        return self.connection.get_metric_statistics(period,
                                                     start_time,
                                                     end_time,
                                                     self.name,
                                                     self.namespace,
                                                     statistics,
                                                     self.dimensions,
                                                     unit)

    def create_alarm(self, name, comparison, threshold,
                     period, evaluation_periods,
                     statistic, enabled=True, description=None,
                     dimensions=None, alarm_actions=None, ok_actions=None,
                     insufficient_data_actions=None, unit=None):
        """
        Creates or updates an alarm and associates it with this metric.
        Optionally, this operation can associate one or more
        Amazon Simple Notification Service resources with the alarm.

        When this operation creates an alarm, the alarm state is immediately
        set to INSUFFICIENT_DATA. The alarm is evaluated and its StateValue is
        set appropriately. Any actions associated with the StateValue is then
        executed.

        When updating an existing alarm, its StateValue is left unchanged.

        :type alarm: boto.ec2.cloudwatch.alarm.MetricAlarm
        :param alarm: MetricAlarm object.
        """
        if not dimensions:
            dimensions = self.dimensions
        alarm = MetricAlarm(self.connection, name, self.name,
                            self.namespace, statistic, comparison,
                            threshold, period, evaluation_periods,
                            unit, description, dimensions,
                            alarm_actions, insufficient_data_actions,
                            ok_actions)
        if self.connection.put_metric_alarm(alarm):
            return alarm

    def describe_alarms(self, period=None, statistic=None,
                        dimensions=None, unit=None):
        """
        Retrieves all alarms for this metric. Specify a statistic, period,
        or unit to filter the set of alarms further.

        :type period: int
        :param period: The period in seconds over which the statistic
            is applied.

        :type statistic: string
        :param statistic: The statistic for the metric.

        :type dimensions: dict
        :param dimension: A dictionary containing name/value
            pairs that will be used to filter the results. The key in
            the dictionary is the name of a Dimension. The value in
            the dictionary is either a scalar value of that Dimension
            name that you want to filter on, a list of values to
            filter on or None if you want all metrics with that
            Dimension name.

        :type unit: string

        :rtype list
        """
        return self.connection.describe_alarms_for_metric(self.name,
                                                          self.namespace,
                                                          period,
                                                          statistic,
                                                          dimensions,
                                                          unit)
