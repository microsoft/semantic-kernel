# Copyright (c) 2010 Hunter Blanks http://artifex.org/~hblanks/
# All rights reserved.
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
Initial, and very limited, unit tests for CloudWatchConnection.
"""

import datetime

from boto.ec2.cloudwatch import CloudWatchConnection
from tests.compat import unittest, OrderedDict

# HTTP response body for CloudWatchConnection.describe_alarms
DESCRIBE_ALARMS_BODY = """<DescribeAlarmsResponse xmlns="http://monitoring.amazonaws.com/doc/2010-08-01/">
  <DescribeAlarmsResult>
    <NextToken>mynexttoken</NextToken>
    <MetricAlarms>
      <member>
        <StateUpdatedTimestamp>2011-11-18T23:43:59.111Z</StateUpdatedTimestamp>
        <InsufficientDataActions/>
        <StateReasonData>{&quot;version&quot;:&quot;1.0&quot;,&quot;queryDate&quot;:&quot;2011-11-18T23:43:59.089+0000&quot;,&quot;startDate&quot;:&quot;2011-11-18T23:30:00.000+0000&quot;,&quot;statistic&quot;:&quot;Maximum&quot;,&quot;period&quot;:60,&quot;recentDatapoints&quot;:[1.0,null,null,null,null,null,null,null,null,null,1.0],&quot;threshold&quot;:1.0}</StateReasonData>
        <AlarmArn>arn:aws:cloudwatch:us-east-1:1234:alarm:FancyAlarm</AlarmArn>
        <AlarmConfigurationUpdatedTimestamp>2011-11-18T23:43:58.489Z</AlarmConfigurationUpdatedTimestamp>
        <AlarmName>FancyAlarm</AlarmName>
        <StateValue>OK</StateValue>
        <Period>60</Period>
        <OKActions/>
        <ActionsEnabled>true</ActionsEnabled>
        <Namespace>AcmeCo/Cronjobs</Namespace>
        <EvaluationPeriods>15</EvaluationPeriods>
        <Threshold>1.0</Threshold>
        <Statistic>Maximum</Statistic>
        <AlarmActions>
          <member>arn:aws:sns:us-east-1:1234:Alerts</member>
        </AlarmActions>
        <StateReason>Threshold Crossed: 2 datapoints were not less than the threshold (1.0). The most recent datapoints: [1.0, 1.0].</StateReason>
        <Dimensions>
          <member>
            <Name>Job</Name>
            <Value>ANiceCronJob</Value>
          </member>
        </Dimensions>
        <ComparisonOperator>LessThanThreshold</ComparisonOperator>
        <MetricName>Success</MetricName>
      </member>
      <member>
        <StateUpdatedTimestamp>2011-11-19T08:09:20.655Z</StateUpdatedTimestamp>
        <InsufficientDataActions/>
        <StateReasonData>{&quot;version&quot;:&quot;1.0&quot;,&quot;queryDate&quot;:&quot;2011-11-19T08:09:20.633+0000&quot;,&quot;startDate&quot;:&quot;2011-11-19T08:07:00.000+0000&quot;,&quot;statistic&quot;:&quot;Maximum&quot;,&quot;period&quot;:60,&quot;recentDatapoints&quot;:[1.0],&quot;threshold&quot;:1.0}</StateReasonData>
        <AlarmArn>arn:aws:cloudwatch:us-east-1:1234:alarm:SuprtFancyAlarm</AlarmArn>
        <AlarmConfigurationUpdatedTimestamp>2011-11-19T16:20:19.687Z</AlarmConfigurationUpdatedTimestamp>
        <AlarmName>SuperFancyAlarm</AlarmName>
        <StateValue>OK</StateValue>
        <Period>60</Period>
        <OKActions/>
        <ActionsEnabled>true</ActionsEnabled>
        <Namespace>AcmeCo/CronJobs</Namespace>
        <EvaluationPeriods>60</EvaluationPeriods>
        <Threshold>1.0</Threshold>
        <Statistic>Maximum</Statistic>
        <AlarmActions>
          <member>arn:aws:sns:us-east-1:1234:alerts</member>
        </AlarmActions>
        <StateReason>Threshold Crossed: 1 datapoint (1.0) was not less than the threshold (1.0).</StateReason>
        <Dimensions>
          <member>
            <Name>Job</Name>
            <Value>ABadCronJob</Value>
          </member>
        </Dimensions>
        <ComparisonOperator>GreaterThanThreshold</ComparisonOperator>
        <MetricName>Success</MetricName>
      </member>
    </MetricAlarms>
  </DescribeAlarmsResult>
  <ResponseMetadata>
    <RequestId>f621311-1463-11e1-95c3-312389123</RequestId>
  </ResponseMetadata>
</DescribeAlarmsResponse>"""


class CloudWatchConnectionTest(unittest.TestCase):
    ec2 = True

    def test_build_list_params(self):
        c = CloudWatchConnection()
        params = {}
        c.build_list_params(
            params, ['thing1', 'thing2', 'thing3'], 'ThingName%d')
        expected_params = {
            'ThingName1': 'thing1',
            'ThingName2': 'thing2',
            'ThingName3': 'thing3'
        }
        self.assertEqual(params, expected_params)

    def test_build_put_params_one(self):
        c = CloudWatchConnection()
        params = {}
        c.build_put_params(params, name="N", value=1, dimensions={"D": "V"})
        expected_params = {
            'MetricData.member.1.MetricName': 'N',
            'MetricData.member.1.Value': 1,
            'MetricData.member.1.Dimensions.member.1.Name': 'D',
            'MetricData.member.1.Dimensions.member.1.Value': 'V',
        }
        self.assertEqual(params, expected_params)

    def test_build_put_params_multiple_metrics(self):
        c = CloudWatchConnection()
        params = {}
        c.build_put_params(params, name=["N", "M"], value=[1, 2], dimensions={"D": "V"})
        expected_params = {
            'MetricData.member.1.MetricName': 'N',
            'MetricData.member.1.Value': 1,
            'MetricData.member.1.Dimensions.member.1.Name': 'D',
            'MetricData.member.1.Dimensions.member.1.Value': 'V',
            'MetricData.member.2.MetricName': 'M',
            'MetricData.member.2.Value': 2,
            'MetricData.member.2.Dimensions.member.1.Name': 'D',
            'MetricData.member.2.Dimensions.member.1.Value': 'V',
        }
        self.assertEqual(params, expected_params)

    def test_build_put_params_multiple_dimensions(self):
        c = CloudWatchConnection()
        params = {}
        c.build_put_params(params, name="N", value=[1, 2], dimensions=[{"D": "V"}, {"D": "W"}])
        expected_params = {
            'MetricData.member.1.MetricName': 'N',
            'MetricData.member.1.Value': 1,
            'MetricData.member.1.Dimensions.member.1.Name': 'D',
            'MetricData.member.1.Dimensions.member.1.Value': 'V',
            'MetricData.member.2.MetricName': 'N',
            'MetricData.member.2.Value': 2,
            'MetricData.member.2.Dimensions.member.1.Name': 'D',
            'MetricData.member.2.Dimensions.member.1.Value': 'W',
        }
        self.assertEqual(params, expected_params)

    def test_build_put_params_multiple_parameter_dimension(self):
        self.maxDiff = None
        c = CloudWatchConnection()
        params = {}
        dimensions = [OrderedDict((("D1", "V"), ("D2", "W")))]
        c.build_put_params(params,
                           name="N",
                           value=[1],
                           dimensions=dimensions)
        expected_params = {
            'MetricData.member.1.MetricName': 'N',
            'MetricData.member.1.Value': 1,
            'MetricData.member.1.Dimensions.member.1.Name': 'D1',
            'MetricData.member.1.Dimensions.member.1.Value': 'V',
            'MetricData.member.1.Dimensions.member.2.Name': 'D2',
            'MetricData.member.1.Dimensions.member.2.Value': 'W',
        }
        self.assertEqual(params, expected_params)

    def test_build_get_params_multiple_parameter_dimension1(self):
        self.maxDiff = None
        c = CloudWatchConnection()
        params = {}
        dimensions = OrderedDict((("D1", "V"), ("D2", "W")))
        c.build_dimension_param(dimensions, params)
        expected_params = {
            'Dimensions.member.1.Name': 'D1',
            'Dimensions.member.1.Value': 'V',
            'Dimensions.member.2.Name': 'D2',
            'Dimensions.member.2.Value': 'W',
        }
        self.assertEqual(params, expected_params)

    def test_build_get_params_multiple_parameter_dimension2(self):
        self.maxDiff = None
        c = CloudWatchConnection()
        params = {}
        dimensions = OrderedDict((("D1", ["V1", "V2"]), ("D2", "W"), ("D3", None)))
        c.build_dimension_param(dimensions, params)
        expected_params = {
            'Dimensions.member.1.Name': 'D1',
            'Dimensions.member.1.Value': 'V1',
            'Dimensions.member.2.Name': 'D1',
            'Dimensions.member.2.Value': 'V2',
            'Dimensions.member.3.Name': 'D2',
            'Dimensions.member.3.Value': 'W',
            'Dimensions.member.4.Name': 'D3',
        }
        self.assertEqual(params, expected_params)

    def test_build_put_params_invalid(self):
        c = CloudWatchConnection()
        params = {}
        try:
            c.build_put_params(params, name=["N", "M"], value=[1, 2, 3])
        except:
            pass
        else:
            self.fail("Should not accept lists of different lengths.")

    def test_get_metric_statistics(self):
        c = CloudWatchConnection()
        m = c.list_metrics()[0]
        end = datetime.datetime.utcnow()
        start = end - datetime.timedelta(hours=24 * 14)
        c.get_metric_statistics(
            3600 * 24, start, end, m.name, m.namespace, ['Average', 'Sum'])

    def test_put_metric_data(self):
        c = CloudWatchConnection()
        now = datetime.datetime.utcnow()
        name, namespace = 'unit-test-metric', 'boto-unit-test'
        c.put_metric_data(namespace, name, 5, now, 'Bytes')

        # Uncomment the following lines for a slower but more thorough
        # test. (Hurrah for eventual consistency...)
        #
        # metric = Metric(connection=c)
        # metric.name = name
        # metric.namespace = namespace
        # time.sleep(60)
        # l = metric.query(
        #     now - datetime.timedelta(seconds=60),
        #     datetime.datetime.utcnow(),
        #     'Average')
        # assert l
        # for row in l:
        #     self.assertEqual(row['Unit'], 'Bytes')
        #     self.assertEqual(row['Average'], 5.0)

    def test_describe_alarms(self):
        c = CloudWatchConnection()

        def make_request(*args, **kwargs):
            class Body(object):
                def __init__(self):
                    self.status = 200

                def read(self):
                    return DESCRIBE_ALARMS_BODY
            return Body()

        c.make_request = make_request
        alarms = c.describe_alarms()
        self.assertEquals(alarms.next_token, 'mynexttoken')
        self.assertEquals(alarms[0].name, 'FancyAlarm')
        self.assertEquals(alarms[0].comparison, '<')
        self.assertEquals(alarms[0].dimensions, {u'Job': [u'ANiceCronJob']})
        self.assertEquals(alarms[1].name, 'SuperFancyAlarm')
        self.assertEquals(alarms[1].comparison, '>')
        self.assertEquals(alarms[1].dimensions, {u'Job': [u'ABadCronJob']})

if __name__ == '__main__':
    unittest.main()
