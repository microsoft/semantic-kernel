#!/usr/bin/env python
# Copyright (c) 2013 Amazon.com, Inc. or its affiliates.  All Rights Reserved
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
import datetime

from tests.unit import unittest
from tests.unit import AWSMockServiceTestCase

from boto.ec2.cloudwatch import CloudWatchConnection


class TestCloudWatchConnection(AWSMockServiceTestCase):

    connection_class = CloudWatchConnection

    def test_build_put_params_multiple_everything(self):
        # This dictionary gets modified by the method call.
        # Check to make sure all updates happen appropriately.
        params = {}
        # Again, these are rubbish parameters. Pay them no mind, we care more
        # about the functionality of the method
        name = ['whatever', 'goeshere']
        value = None
        timestamp = [
            datetime.datetime(2013, 5, 13, 9, 2, 35),
            datetime.datetime(2013, 5, 12, 9, 2, 35),
        ]
        unit = ['lbs', 'ft']
        dimensions = None
        statistics = [
            {
                'maximum': 5,
                'minimum': 1,
                'samplecount': 3,
                'sum': 7,
            },
            {
                'maximum': 6,
                'minimum': 2,
                'samplecount': 4,
                'sum': 5,
            },
        ]

        # The important part is that this shouldn't generate a warning (due
        # to overwriting a variable) & should have the correct number of
        # Metrics (2).
        self.service_connection.build_put_params(
            params,
            name=name,
            value=value,
            timestamp=timestamp,
            unit=unit,
            dimensions=dimensions,
            statistics=statistics
        )

        self.assertEqual(params, {
            'MetricData.member.1.MetricName': 'whatever',
            'MetricData.member.1.StatisticValues.Maximum': 5,
            'MetricData.member.1.StatisticValues.Minimum': 1,
            'MetricData.member.1.StatisticValues.SampleCount': 3,
            'MetricData.member.1.StatisticValues.Sum': 7,
            'MetricData.member.1.Timestamp': '2013-05-13T09:02:35',
            'MetricData.member.1.Unit': 'lbs',
            'MetricData.member.2.MetricName': 'goeshere',
            'MetricData.member.2.StatisticValues.Maximum': 6,
            'MetricData.member.2.StatisticValues.Minimum': 2,
            'MetricData.member.2.StatisticValues.SampleCount': 4,
            'MetricData.member.2.StatisticValues.Sum': 5,
            'MetricData.member.2.Timestamp': '2013-05-12T09:02:35',
            # If needed, comment this next line to cause a test failure & see
            # the logging warning.
            'MetricData.member.2.Unit': 'ft',
        })


if __name__ == '__main__':
    unittest.main()
