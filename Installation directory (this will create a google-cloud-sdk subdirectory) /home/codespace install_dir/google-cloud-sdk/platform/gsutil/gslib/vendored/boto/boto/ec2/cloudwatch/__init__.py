# Copyright (c) 2006-2011 Mitch Garnaat http://garnaat.org/
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
"""
This module provides an interface to the Elastic Compute Cloud (EC2)
CloudWatch service from AWS.
"""
from boto.compat import json, map, six, zip
from boto.connection import AWSQueryConnection
from boto.ec2.cloudwatch.metric import Metric
from boto.ec2.cloudwatch.alarm import MetricAlarm, MetricAlarms, AlarmHistoryItem
from boto.ec2.cloudwatch.datapoint import Datapoint
from boto.regioninfo import RegionInfo, get_regions, load_regions
from boto.regioninfo import connect
import boto

RegionData = load_regions().get('cloudwatch', {})


def regions():
    """
    Get all available regions for the CloudWatch service.

    :rtype: list
    :return: A list of :class:`boto.RegionInfo` instances
    """
    return get_regions('cloudwatch', connection_cls=CloudWatchConnection)


def connect_to_region(region_name, **kw_params):
    """
    Given a valid region name, return a
    :class:`boto.ec2.cloudwatch.CloudWatchConnection`.

    :param str region_name: The name of the region to connect to.

    :rtype: :class:`boto.ec2.CloudWatchConnection` or ``None``
    :return: A connection to the given region, or None if an invalid region
        name is given
    """
    return connect('cloudwatch', region_name,
                   connection_cls=CloudWatchConnection, **kw_params)


class CloudWatchConnection(AWSQueryConnection):

    APIVersion = boto.config.get('Boto', 'cloudwatch_version', '2010-08-01')
    DefaultRegionName = boto.config.get('Boto', 'cloudwatch_region_name',
                                        'us-east-1')
    DefaultRegionEndpoint = boto.config.get('Boto',
                                            'cloudwatch_region_endpoint',
                                            'monitoring.us-east-1.amazonaws.com')

    def __init__(self, aws_access_key_id=None, aws_secret_access_key=None,
                 is_secure=True, port=None, proxy=None, proxy_port=None,
                 proxy_user=None, proxy_pass=None, debug=0,
                 https_connection_factory=None, region=None, path='/',
                 security_token=None, validate_certs=True, profile_name=None):
        """
        Init method to create a new connection to EC2 Monitoring Service.

        B{Note:} The host argument is overridden by the host specified in the
        boto configuration file.
        """
        if not region:
            region = RegionInfo(self, self.DefaultRegionName,
                                self.DefaultRegionEndpoint)
        self.region = region

        # Ugly hack to get around both a bug in Python and a
        # misconfigured SSL cert for the eu-west-1 endpoint
        if self.region.name == 'eu-west-1':
            validate_certs = False

        super(CloudWatchConnection, self).__init__(aws_access_key_id,
                                                   aws_secret_access_key,
                                                   is_secure, port, proxy, proxy_port,
                                                   proxy_user, proxy_pass,
                                                   self.region.endpoint, debug,
                                                   https_connection_factory, path,
                                                   security_token,
                                                   validate_certs=validate_certs,
                                                   profile_name=profile_name)

    def _required_auth_capability(self):
        return ['hmac-v4']

    def build_dimension_param(self, dimension, params):
        prefix = 'Dimensions.member'
        i = 0
        for dim_name in dimension:
            dim_value = dimension[dim_name]
            if dim_value:
                if isinstance(dim_value, six.string_types):
                    dim_value = [dim_value]
                for value in dim_value:
                    params['%s.%d.Name' % (prefix, i + 1)] = dim_name
                    params['%s.%d.Value' % (prefix, i + 1)] = value
                    i += 1
            else:
                params['%s.%d.Name' % (prefix, i + 1)] = dim_name
                i += 1

    def build_list_params(self, params, items, label):
        if isinstance(items, six.string_types):
            items = [items]
        for index, item in enumerate(items):
            i = index + 1
            if isinstance(item, dict):
                for k, v in six.iteritems(item):
                    params[label % (i, 'Name')] = k
                    if v is not None:
                        params[label % (i, 'Value')] = v
            else:
                params[label % i] = item

    def build_put_params(self, params, name, value=None, timestamp=None,
                         unit=None, dimensions=None, statistics=None):
        args = (name, value, unit, dimensions, statistics, timestamp)
        length = max(map(lambda a: len(a) if isinstance(a, list) else 1, args))

        def aslist(a):
            if isinstance(a, list):
                if len(a) != length:
                    raise Exception('Must specify equal number of elements; expected %d.' % length)
                return a
            return [a] * length

        for index, (n, v, u, d, s, t) in enumerate(zip(*map(aslist, args))):
            metric_data = {'MetricName': n}

            if timestamp:
                metric_data['Timestamp'] = t.isoformat()

            if unit:
                metric_data['Unit'] = u

            if dimensions:
                self.build_dimension_param(d, metric_data)

            if statistics:
                metric_data['StatisticValues.Maximum'] = s['maximum']
                metric_data['StatisticValues.Minimum'] = s['minimum']
                metric_data['StatisticValues.SampleCount'] = s['samplecount']
                metric_data['StatisticValues.Sum'] = s['sum']
                if value is not None:
                    msg = 'You supplied a value and statistics for a ' + \
                          'metric.Posting statistics and not value.'
                    boto.log.warn(msg)
            elif value is not None:
                metric_data['Value'] = v
            else:
                raise Exception('Must specify a value or statistics to put.')

            for key, val in six.iteritems(metric_data):
                params['MetricData.member.%d.%s' % (index + 1, key)] = val

    def get_metric_statistics(self, period, start_time, end_time, metric_name,
                              namespace, statistics, dimensions=None,
                              unit=None):
        """
        Get time-series data for one or more statistics of a given metric.

        :type period: integer
        :param period: The granularity, in seconds, of the returned datapoints.
            Period must be at least 60 seconds and must be a multiple
            of 60. The default value is 60.

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

        :type metric_name: string
        :param metric_name: The metric name.

        :type namespace: string
        :param namespace: The metric's namespace.

        :type statistics: list
        :param statistics: A list of statistics names Valid values:
            Average | Sum | SampleCount | Maximum | Minimum

        :type dimensions: dict
        :param dimensions: A dictionary of dimension key/values where
                           the key is the dimension name and the value
                           is either a scalar value or an iterator
                           of values to be associated with that
                           dimension.

        :type unit: string
        :param unit: The unit for the metric.  Value values are:
            Seconds | Microseconds | Milliseconds | Bytes | Kilobytes |
            Megabytes | Gigabytes | Terabytes | Bits | Kilobits |
            Megabits | Gigabits | Terabits | Percent | Count |
            Bytes/Second | Kilobytes/Second | Megabytes/Second |
            Gigabytes/Second | Terabytes/Second | Bits/Second |
            Kilobits/Second | Megabits/Second | Gigabits/Second |
            Terabits/Second | Count/Second | None

        :rtype: list
        """
        params = {'Period': period,
                  'MetricName': metric_name,
                  'Namespace': namespace,
                  'StartTime': start_time.isoformat(),
                  'EndTime': end_time.isoformat()}
        self.build_list_params(params, statistics, 'Statistics.member.%d')
        if dimensions:
            self.build_dimension_param(dimensions, params)
        if unit:
            params['Unit'] = unit
        return self.get_list('GetMetricStatistics', params,
                             [('member', Datapoint)])

    def list_metrics(self, next_token=None, dimensions=None,
                     metric_name=None, namespace=None):
        """
        Returns a list of the valid metrics for which there is recorded
        data available.

        :type next_token: str
        :param next_token: A maximum of 500 metrics will be returned
            at one time.  If more results are available, the ResultSet
            returned will contain a non-Null next_token attribute.
            Passing that token as a parameter to list_metrics will
            retrieve the next page of metrics.

        :type dimensions: dict
        :param dimensions: A dictionary containing name/value
            pairs that will be used to filter the results.  The key in
            the dictionary is the name of a Dimension.  The value in
            the dictionary is either a scalar value of that Dimension
            name that you want to filter on or None if you want all
            metrics with that Dimension name.  To be included in the
            result a metric must contain all specified dimensions,
            although the metric may contain additional dimensions beyond
            the requested metrics.  The Dimension names, and values must
            be strings between 1 and 250 characters long. A maximum of
            10 dimensions are allowed.

        :type metric_name: str
        :param metric_name: The name of the Metric to filter against.  If None,
            all Metric names will be returned.

        :type namespace: str
        :param namespace: A Metric namespace to filter against (e.g. AWS/EC2).
            If None, Metrics from all namespaces will be returned.
        """
        params = {}
        if next_token:
            params['NextToken'] = next_token
        if dimensions:
            self.build_dimension_param(dimensions, params)
        if metric_name:
            params['MetricName'] = metric_name
        if namespace:
            params['Namespace'] = namespace

        return self.get_list('ListMetrics', params, [('member', Metric)])

    def put_metric_data(self, namespace, name, value=None, timestamp=None,
                        unit=None, dimensions=None, statistics=None):
        """
        Publishes metric data points to Amazon CloudWatch. Amazon Cloudwatch
        associates the data points with the specified metric. If the specified
        metric does not exist, Amazon CloudWatch creates the metric. If a list
        is specified for some, but not all, of the arguments, the remaining
        arguments are repeated a corresponding number of times.

        :type namespace: str
        :param namespace: The namespace of the metric.

        :type name: str or list
        :param name: The name of the metric.

        :type value: float or list
        :param value: The value for the metric.

        :type timestamp: datetime or list
        :param timestamp: The time stamp used for the metric. If not specified,
            the default value is set to the time the metric data was received.

        :type unit: string or list
        :param unit: The unit of the metric.  Valid Values: Seconds |
            Microseconds | Milliseconds | Bytes | Kilobytes |
            Megabytes | Gigabytes | Terabytes | Bits | Kilobits |
            Megabits | Gigabits | Terabits | Percent | Count |
            Bytes/Second | Kilobytes/Second | Megabytes/Second |
            Gigabytes/Second | Terabytes/Second | Bits/Second |
            Kilobits/Second | Megabits/Second | Gigabits/Second |
            Terabits/Second | Count/Second | None

        :type dimensions: dict
        :param dimensions: Add extra name value pairs to associate
            with the metric, i.e.:
            {'name1': value1, 'name2': (value2, value3)}

        :type statistics: dict or list
        :param statistics: Use a statistic set instead of a value, for example::

            {'maximum': 30, 'minimum': 1, 'samplecount': 100, 'sum': 10000}
        """
        params = {'Namespace': namespace}
        self.build_put_params(params, name, value=value, timestamp=timestamp,
                              unit=unit, dimensions=dimensions, statistics=statistics)

        return self.get_status('PutMetricData', params, verb="POST")

    def describe_alarms(self, action_prefix=None, alarm_name_prefix=None,
                        alarm_names=None, max_records=None, state_value=None,
                        next_token=None):
        """
        Retrieves alarms with the specified names. If no name is specified, all
        alarms for the user are returned. Alarms can be retrieved by using only
        a prefix for the alarm name, the alarm state, or a prefix for any
        action.

        :type action_prefix: string
        :param action_prefix: The action name prefix.

        :type alarm_name_prefix: string
        :param alarm_name_prefix: The alarm name prefix. AlarmNames cannot
            be specified if this parameter is specified.

        :type alarm_names: list
        :param alarm_names: A list of alarm names to retrieve information for.

        :type max_records: int
        :param max_records: The maximum number of alarm descriptions
            to retrieve.

        :type state_value: string
        :param state_value: The state value to be used in matching alarms.

        :type next_token: string
        :param next_token: The token returned by a previous call to
            indicate that there is more data.

        :rtype list
        """
        params = {}
        if action_prefix:
            params['ActionPrefix'] = action_prefix
        if alarm_name_prefix:
            params['AlarmNamePrefix'] = alarm_name_prefix
        elif alarm_names:
            self.build_list_params(params, alarm_names, 'AlarmNames.member.%s')
        if max_records:
            params['MaxRecords'] = max_records
        if next_token:
            params['NextToken'] = next_token
        if state_value:
            params['StateValue'] = state_value

        result = self.get_list('DescribeAlarms', params,
                               [('MetricAlarms', MetricAlarms)])
        ret = result[0]
        ret.next_token = result.next_token
        return ret

    def describe_alarm_history(self, alarm_name=None,
                               start_date=None, end_date=None,
                               max_records=None, history_item_type=None,
                               next_token=None):
        """
        Retrieves history for the specified alarm. Filter alarms by date range
        or item type. If an alarm name is not specified, Amazon CloudWatch
        returns histories for all of the owner's alarms.

        Amazon CloudWatch retains the history of deleted alarms for a period of
        six weeks. If an alarm has been deleted, its history can still be
        queried.

        :type alarm_name: string
        :param alarm_name: The name of the alarm.

        :type start_date: datetime
        :param start_date: The starting date to retrieve alarm history.

        :type end_date: datetime
        :param end_date: The starting date to retrieve alarm history.

        :type history_item_type: string
        :param history_item_type: The type of alarm histories to retreive
            (ConfigurationUpdate | StateUpdate | Action)

        :type max_records: int
        :param max_records: The maximum number of alarm descriptions
            to retrieve.

        :type next_token: string
        :param next_token: The token returned by a previous call to indicate
            that there is more data.

        :rtype list
        """
        params = {}
        if alarm_name:
            params['AlarmName'] = alarm_name
        if start_date:
            params['StartDate'] = start_date.isoformat()
        if end_date:
            params['EndDate'] = end_date.isoformat()
        if history_item_type:
            params['HistoryItemType'] = history_item_type
        if max_records:
            params['MaxRecords'] = max_records
        if next_token:
            params['NextToken'] = next_token
        return self.get_list('DescribeAlarmHistory', params,
                             [('member', AlarmHistoryItem)])

    def describe_alarms_for_metric(self, metric_name, namespace, period=None,
                                   statistic=None, dimensions=None, unit=None):
        """
        Retrieves all alarms for a single metric. Specify a statistic, period,
        or unit to filter the set of alarms further.

        :type metric_name: string
        :param metric_name: The name of the metric.

        :type namespace: string
        :param namespace: The namespace of the metric.

        :type period: int
        :param period: The period in seconds over which the statistic
            is applied.

        :type statistic: string
        :param statistic: The statistic for the metric.

        :type dimensions: dict
        :param dimensions: A dictionary containing name/value
            pairs that will be used to filter the results. The key in
            the dictionary is the name of a Dimension. The value in
            the dictionary is either a scalar value of that Dimension
            name that you want to filter on, a list of values to
            filter on or None if you want all metrics with that
            Dimension name.

        :type unit: string

        :rtype list
        """
        params = {'MetricName': metric_name,
                  'Namespace': namespace}
        if period:
            params['Period'] = period
        if statistic:
            params['Statistic'] = statistic
        if dimensions:
            self.build_dimension_param(dimensions, params)
        if unit:
            params['Unit'] = unit
        return self.get_list('DescribeAlarmsForMetric', params,
                             [('member', MetricAlarm)])

    def put_metric_alarm(self, alarm):
        """
        Creates or updates an alarm and associates it with the specified Amazon
        CloudWatch metric. Optionally, this operation can associate one or more
        Amazon Simple Notification Service resources with the alarm.

        When this operation creates an alarm, the alarm state is immediately
        set to INSUFFICIENT_DATA. The alarm is evaluated and its StateValue is
        set appropriately. Any actions associated with the StateValue is then
        executed.

        When updating an existing alarm, its StateValue is left unchanged.

        :type alarm: boto.ec2.cloudwatch.alarm.MetricAlarm
        :param alarm: MetricAlarm object.
        """
        params = {
            'AlarmName': alarm.name,
            'MetricName': alarm.metric,
            'Namespace': alarm.namespace,
            'Statistic': alarm.statistic,
            'ComparisonOperator': alarm.comparison,
            'Threshold': alarm.threshold,
            'EvaluationPeriods': alarm.evaluation_periods,
            'Period': alarm.period,
        }
        if alarm.actions_enabled is not None:
            params['ActionsEnabled'] = alarm.actions_enabled
        if alarm.alarm_actions:
            self.build_list_params(params, alarm.alarm_actions,
                                   'AlarmActions.member.%s')
        if alarm.description:
            params['AlarmDescription'] = alarm.description
        if alarm.dimensions:
            self.build_dimension_param(alarm.dimensions, params)
        if alarm.insufficient_data_actions:
            self.build_list_params(params, alarm.insufficient_data_actions,
                                   'InsufficientDataActions.member.%s')
        if alarm.ok_actions:
            self.build_list_params(params, alarm.ok_actions,
                                   'OKActions.member.%s')
        if alarm.unit:
            params['Unit'] = alarm.unit
        alarm.connection = self
        return self.get_status('PutMetricAlarm', params)
    create_alarm = put_metric_alarm
    update_alarm = put_metric_alarm

    def delete_alarms(self, alarms):
        """
        Deletes all specified alarms. In the event of an error, no
        alarms are deleted.

        :type alarms: list
        :param alarms: List of alarm names.
        """
        params = {}
        self.build_list_params(params, alarms, 'AlarmNames.member.%s')
        return self.get_status('DeleteAlarms', params)

    def set_alarm_state(self, alarm_name, state_reason, state_value,
                        state_reason_data=None):
        """
        Temporarily sets the state of an alarm. When the updated StateValue
        differs from the previous value, the action configured for the
        appropriate state is invoked. This is not a permanent change. The next
        periodic alarm check (in about a minute) will set the alarm to its
        actual state.

        :type alarm_name: string
        :param alarm_name: Descriptive name for alarm.

        :type state_reason: string
        :param state_reason: Human readable reason.

        :type state_value: string
        :param state_value: OK | ALARM | INSUFFICIENT_DATA

        :type state_reason_data: string
        :param state_reason_data: Reason string (will be jsonified).
        """
        params = {'AlarmName': alarm_name,
                  'StateReason': state_reason,
                  'StateValue': state_value}
        if state_reason_data:
            params['StateReasonData'] = json.dumps(state_reason_data)

        return self.get_status('SetAlarmState', params)

    def enable_alarm_actions(self, alarm_names):
        """
        Enables actions for the specified alarms.

        :type alarms: list
        :param alarms: List of alarm names.
        """
        params = {}
        self.build_list_params(params, alarm_names, 'AlarmNames.member.%s')
        return self.get_status('EnableAlarmActions', params)

    def disable_alarm_actions(self, alarm_names):
        """
        Disables actions for the specified alarms.

        :type alarms: list
        :param alarms: List of alarm names.
        """
        params = {}
        self.build_list_params(params, alarm_names, 'AlarmNames.member.%s')
        return self.get_status('DisableAlarmActions', params)
