# Copyright (c) 2015 Amazon.com, Inc. or its affiliates.  All Rights Reserved
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

import boto
from boto.compat import json
from boto.connection import AWSQueryConnection
from boto.regioninfo import RegionInfo
from boto.exception import JSONResponseError
from boto.configservice import exceptions


class ConfigServiceConnection(AWSQueryConnection):
    """
    AWS Config
    AWS Config provides a way to keep track of the configurations of
    all the AWS resources associated with your AWS account. You can
    use AWS Config to get the current and historical configurations of
    each AWS resource and also to get information about the
    relationship between the resources. An AWS resource can be an
    Amazon Compute Cloud (Amazon EC2) instance, an Elastic Block Store
    (EBS) volume, an Elastic network Interface (ENI), or a security
    group. For a complete list of resources currently supported by AWS
    Config, see `Supported AWS Resources`_.

    You can access and manage AWS Config through the AWS Management
    Console, the AWS Command Line Interface (AWS CLI), the AWS Config
    API, or the AWS SDKs for AWS Config

    This reference guide contains documentation for the AWS Config API
    and the AWS CLI commands that you can use to manage AWS Config.

    The AWS Config API uses the Signature Version 4 protocol for
    signing requests. For more information about how to sign a request
    with this protocol, see `Signature Version 4 Signing Process`_.

    For detailed information about AWS Config features and their
    associated actions or commands, as well as how to work with AWS
    Management Console, see `What Is AWS Config?`_ in the AWS Config
    Developer Guide .
    """
    APIVersion = "2014-11-12"
    DefaultRegionName = "us-east-1"
    DefaultRegionEndpoint = "config.us-east-1.amazonaws.com"
    ServiceName = "ConfigService"
    TargetPrefix = "StarlingDoveService"
    ResponseError = JSONResponseError

    _faults = {
        "InvalidLimitException": exceptions.InvalidLimitException,
        "NoSuchBucketException": exceptions.NoSuchBucketException,
        "InvalidSNSTopicARNException": exceptions.InvalidSNSTopicARNException,
        "ResourceNotDiscoveredException": exceptions.ResourceNotDiscoveredException,
        "MaxNumberOfDeliveryChannelsExceededException": exceptions.MaxNumberOfDeliveryChannelsExceededException,
        "LastDeliveryChannelDeleteFailedException": exceptions.LastDeliveryChannelDeleteFailedException,
        "InsufficientDeliveryPolicyException": exceptions.InsufficientDeliveryPolicyException,
        "InvalidRoleException": exceptions.InvalidRoleException,
        "InvalidTimeRangeException": exceptions.InvalidTimeRangeException,
        "NoSuchDeliveryChannelException": exceptions.NoSuchDeliveryChannelException,
        "NoSuchConfigurationRecorderException": exceptions.NoSuchConfigurationRecorderException,
        "InvalidS3KeyPrefixException": exceptions.InvalidS3KeyPrefixException,
        "InvalidDeliveryChannelNameException": exceptions.InvalidDeliveryChannelNameException,
        "NoRunningConfigurationRecorderException": exceptions.NoRunningConfigurationRecorderException,
        "ValidationException": exceptions.ValidationException,
        "NoAvailableConfigurationRecorderException": exceptions.NoAvailableConfigurationRecorderException,
        "InvalidNextTokenException": exceptions.InvalidNextTokenException,
        "InvalidConfigurationRecorderNameException": exceptions.InvalidConfigurationRecorderNameException,
        "NoAvailableDeliveryChannelException": exceptions.NoAvailableDeliveryChannelException,
        "MaxNumberOfConfigurationRecordersExceededException": exceptions.MaxNumberOfConfigurationRecordersExceededException,
    }


    def __init__(self, **kwargs):
        region = kwargs.pop('region', None)
        if not region:
            region = RegionInfo(self, self.DefaultRegionName,
                                self.DefaultRegionEndpoint)

        if 'host' not in kwargs or kwargs['host'] is None:
            kwargs['host'] = region.endpoint

        super(ConfigServiceConnection, self).__init__(**kwargs)
        self.region = region

    def _required_auth_capability(self):
        return ['hmac-v4']

    def delete_delivery_channel(self, delivery_channel_name):
        """
        Deletes the specified delivery channel.

        The delivery channel cannot be deleted if it is the only
        delivery channel and the configuration recorder is still
        running. To delete the delivery channel, stop the running
        configuration recorder using the StopConfigurationRecorder
        action.

        :type delivery_channel_name: string
        :param delivery_channel_name: The name of the delivery channel to
            delete.

        """
        params = {'DeliveryChannelName': delivery_channel_name, }
        return self.make_request(action='DeleteDeliveryChannel',
                                 body=json.dumps(params))

    def deliver_config_snapshot(self, delivery_channel_name):
        """
        Schedules delivery of a configuration snapshot to the Amazon
        S3 bucket in the specified delivery channel. After the
        delivery has started, AWS Config sends following notifications
        using an Amazon SNS topic that you have specified.


        + Notification of starting the delivery.
        + Notification of delivery completed, if the delivery was
          successfully completed.
        + Notification of delivery failure, if the delivery failed to
          complete.

        :type delivery_channel_name: string
        :param delivery_channel_name: The name of the delivery channel through
            which the snapshot is delivered.

        """
        params = {'deliveryChannelName': delivery_channel_name, }
        return self.make_request(action='DeliverConfigSnapshot',
                                 body=json.dumps(params))

    def describe_configuration_recorder_status(self,
                                               configuration_recorder_names=None):
        """
        Returns the current status of the specified configuration
        recorder. If a configuration recorder is not specified, this
        action returns the status of all configuration recorder
        associated with the account.

        :type configuration_recorder_names: list
        :param configuration_recorder_names: The name(s) of the configuration
            recorder. If the name is not specified, the action returns the
            current status of all the configuration recorders associated with
            the account.

        """
        params = {}
        if configuration_recorder_names is not None:
            params['ConfigurationRecorderNames'] = configuration_recorder_names
        return self.make_request(action='DescribeConfigurationRecorderStatus',
                                 body=json.dumps(params))

    def describe_configuration_recorders(self,
                                         configuration_recorder_names=None):
        """
        Returns the name of one or more specified configuration
        recorders. If the recorder name is not specified, this action
        returns the names of all the configuration recorders
        associated with the account.

        :type configuration_recorder_names: list
        :param configuration_recorder_names: A list of configuration recorder
            names.

        """
        params = {}
        if configuration_recorder_names is not None:
            params['ConfigurationRecorderNames'] = configuration_recorder_names
        return self.make_request(action='DescribeConfigurationRecorders',
                                 body=json.dumps(params))

    def describe_delivery_channel_status(self, delivery_channel_names=None):
        """
        Returns the current status of the specified delivery channel.
        If a delivery channel is not specified, this action returns
        the current status of all delivery channels associated with
        the account.

        :type delivery_channel_names: list
        :param delivery_channel_names: A list of delivery channel names.

        """
        params = {}
        if delivery_channel_names is not None:
            params['DeliveryChannelNames'] = delivery_channel_names
        return self.make_request(action='DescribeDeliveryChannelStatus',
                                 body=json.dumps(params))

    def describe_delivery_channels(self, delivery_channel_names=None):
        """
        Returns details about the specified delivery channel. If a
        delivery channel is not specified, this action returns the
        details of all delivery channels associated with the account.

        :type delivery_channel_names: list
        :param delivery_channel_names: A list of delivery channel names.

        """
        params = {}
        if delivery_channel_names is not None:
            params['DeliveryChannelNames'] = delivery_channel_names
        return self.make_request(action='DescribeDeliveryChannels',
                                 body=json.dumps(params))

    def get_resource_config_history(self, resource_type, resource_id,
                                    later_time=None, earlier_time=None,
                                    chronological_order=None, limit=None,
                                    next_token=None):
        """
        Returns a list of configuration items for the specified
        resource. The list contains details about each state of the
        resource during the specified time interval. You can specify a
        `limit` on the number of results returned on the page. If a
        limit is specified, a `nextToken` is returned as part of the
        result that you can use to continue this request.

        :type resource_type: string
        :param resource_type: The resource type.

        :type resource_id: string
        :param resource_id: The ID of the resource (for example., `sg-xxxxxx`).

        :type later_time: timestamp
        :param later_time: The time stamp that indicates a later time. If not
            specified, current time is taken.

        :type earlier_time: timestamp
        :param earlier_time: The time stamp that indicates an earlier time. If
            not specified, the action returns paginated results that contain
            configuration items that start from when the first configuration
            item was recorded.

        :type chronological_order: string
        :param chronological_order: The chronological order for configuration
            items listed. By default the results are listed in reverse
            chronological order.

        :type limit: integer
        :param limit: The maximum number of configuration items returned in
            each page. The default is 10. You cannot specify a limit greater
            than 100.

        :type next_token: string
        :param next_token: An optional parameter used for pagination of the
            results.

        """
        params = {
            'resourceType': resource_type,
            'resourceId': resource_id,
        }
        if later_time is not None:
            params['laterTime'] = later_time
        if earlier_time is not None:
            params['earlierTime'] = earlier_time
        if chronological_order is not None:
            params['chronologicalOrder'] = chronological_order
        if limit is not None:
            params['limit'] = limit
        if next_token is not None:
            params['nextToken'] = next_token
        return self.make_request(action='GetResourceConfigHistory',
                                 body=json.dumps(params))

    def put_configuration_recorder(self, configuration_recorder):
        """
        Creates a new configuration recorder to record the resource
        configurations.

        You can use this action to change the role ( `roleARN`) of an
        existing recorder. To change the role, call the action on the
        existing configuration recorder and specify a role.

        :type configuration_recorder: dict
        :param configuration_recorder: The configuration recorder object that
            records each configuration change made to the resources. The
            format should follow:

            {'name': 'myrecorder',
             'roleARN': 'arn:aws:iam::123456789012:role/trusted-aws-config'}

        """
        params = {'ConfigurationRecorder': configuration_recorder, }
        return self.make_request(action='PutConfigurationRecorder',
                                 body=json.dumps(params))

    def put_delivery_channel(self, delivery_channel):
        """
        Creates a new delivery channel object to deliver the
        configuration information to an Amazon S3 bucket, and to an
        Amazon SNS topic.

        You can use this action to change the Amazon S3 bucket or an
        Amazon SNS topic of the existing delivery channel. To change
        the Amazon S3 bucket or an Amazon SNS topic, call this action
        and specify the changed values for the S3 bucket and the SNS
        topic. If you specify a different value for either the S3
        bucket or the SNS topic, this action will keep the existing
        value for the parameter that is not changed.

        :type delivery_channel: dict
        :param delivery_channel: The configuration delivery channel object that
            delivers the configuration information to an Amazon S3 bucket, and
            to an Amazon SNS topic.

        """
        params = {'DeliveryChannel': delivery_channel, }
        return self.make_request(action='PutDeliveryChannel',
                                 body=json.dumps(params))

    def start_configuration_recorder(self, configuration_recorder_name):
        """
        Starts recording configurations of all the resources
        associated with the account.

        You must have created at least one delivery channel to
        successfully start the configuration recorder.

        :type configuration_recorder_name: string
        :param configuration_recorder_name: The name of the recorder object
            that records each configuration change made to the resources.

        """
        params = {
            'ConfigurationRecorderName': configuration_recorder_name,
        }
        return self.make_request(action='StartConfigurationRecorder',
                                 body=json.dumps(params))

    def stop_configuration_recorder(self, configuration_recorder_name):
        """
        Stops recording configurations of all the resources associated
        with the account.

        :type configuration_recorder_name: string
        :param configuration_recorder_name: The name of the recorder object
            that records each configuration change made to the resources.

        """
        params = {
            'ConfigurationRecorderName': configuration_recorder_name,
        }
        return self.make_request(action='StopConfigurationRecorder',
                                 body=json.dumps(params))

    def make_request(self, action, body):
        headers = {
            'X-Amz-Target': '%s.%s' % (self.TargetPrefix, action),
            'Host': self.region.endpoint,
            'Content-Type': 'application/x-amz-json-1.1',
            'Content-Length': str(len(body)),
        }
        http_request = self.build_base_http_request(
            method='POST', path='/', auth_path='/', params={},
            headers=headers, data=body)
        response = self._mexe(http_request, sender=None,
                              override_num_retries=10)
        response_body = response.read().decode('utf-8')
        boto.log.debug(response_body)
        if response.status == 200:
            if response_body:
                return json.loads(response_body)
        else:
            json_body = json.loads(response_body)
            fault_name = json_body.get('__type', None)
            exception_class = self._faults.get(fault_name, self.ResponseError)
            raise exception_class(response.status, response.reason,
                                  body=json_body)

