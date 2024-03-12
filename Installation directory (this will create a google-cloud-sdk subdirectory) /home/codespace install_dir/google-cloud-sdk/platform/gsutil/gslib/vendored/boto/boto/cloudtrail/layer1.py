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
from boto.connection import AWSQueryConnection
from boto.regioninfo import RegionInfo
from boto.exception import JSONResponseError
from boto.cloudtrail import exceptions
from boto.compat import json


class CloudTrailConnection(AWSQueryConnection):
    """
    AWS CloudTrail
    This is the CloudTrail API Reference. It provides descriptions of
    actions, data types, common parameters, and common errors for
    CloudTrail.

    CloudTrail is a web service that records AWS API calls for your
    AWS account and delivers log files to an Amazon S3 bucket. The
    recorded information includes the identity of the user, the start
    time of the AWS API call, the source IP address, the request
    parameters, and the response elements returned by the service.

    As an alternative to using the API, you can use one of the AWS
    SDKs, which consist of libraries and sample code for various
    programming languages and platforms (Java, Ruby, .NET, iOS,
    Android, etc.). The SDKs provide a convenient way to create
    programmatic access to AWSCloudTrail. For example, the SDKs take
    care of cryptographically signing requests, managing errors, and
    retrying requests automatically. For information about the AWS
    SDKs, including how to download and install them, see the `Tools
    for Amazon Web Services page`_.

    See the CloudTrail User Guide for information about the data that
    is included with each AWS API call listed in the log files.
    """
    APIVersion = "2013-11-01"
    DefaultRegionName = "us-east-1"
    DefaultRegionEndpoint = "cloudtrail.us-east-1.amazonaws.com"
    ServiceName = "CloudTrail"
    TargetPrefix = "com.amazonaws.cloudtrail.v20131101.CloudTrail_20131101"
    ResponseError = JSONResponseError

    _faults = {
        "InvalidMaxResultsException": exceptions.InvalidMaxResultsException,
        "InvalidSnsTopicNameException": exceptions.InvalidSnsTopicNameException,
        "InvalidS3BucketNameException": exceptions.InvalidS3BucketNameException,
        "TrailAlreadyExistsException": exceptions.TrailAlreadyExistsException,
        "InvalidTimeRangeException": exceptions.InvalidTimeRangeException,
        "InvalidLookupAttributesException": exceptions.InvalidLookupAttributesException,
        "InsufficientSnsTopicPolicyException": exceptions.InsufficientSnsTopicPolicyException,
        "InvalidCloudWatchLogsLogGroupArnException": exceptions.InvalidCloudWatchLogsLogGroupArnException,
        "InvalidCloudWatchLogsRoleArnException": exceptions.InvalidCloudWatchLogsRoleArnException,
        "InvalidTrailNameException": exceptions.InvalidTrailNameException,
        "CloudWatchLogsDeliveryUnavailableException": exceptions.CloudWatchLogsDeliveryUnavailableException,
        "TrailNotFoundException": exceptions.TrailNotFoundException,
        "S3BucketDoesNotExistException": exceptions.S3BucketDoesNotExistException,
        "InvalidNextTokenException": exceptions.InvalidNextTokenException,
        "InvalidS3PrefixException": exceptions.InvalidS3PrefixException,
        "MaximumNumberOfTrailsExceededException": exceptions.MaximumNumberOfTrailsExceededException,
        "InsufficientS3BucketPolicyException": exceptions.InsufficientS3BucketPolicyException,
    }


    def __init__(self, **kwargs):
        region = kwargs.pop('region', None)
        if not region:
            region = RegionInfo(self, self.DefaultRegionName,
                                self.DefaultRegionEndpoint)

        if 'host' not in kwargs or kwargs['host'] is None:
            kwargs['host'] = region.endpoint

        super(CloudTrailConnection, self).__init__(**kwargs)
        self.region = region

    def _required_auth_capability(self):
        return ['hmac-v4']

    def create_trail(self, name, s3_bucket_name, s3_key_prefix=None,
                     sns_topic_name=None, include_global_service_events=None,
                     cloud_watch_logs_log_group_arn=None,
                     cloud_watch_logs_role_arn=None):
        """
        From the command line, use `create-subscription`.

        Creates a trail that specifies the settings for delivery of
        log data to an Amazon S3 bucket.

        :type name: string
        :param name: Specifies the name of the trail.

        :type s3_bucket_name: string
        :param s3_bucket_name: Specifies the name of the Amazon S3 bucket
            designated for publishing log files.

        :type s3_key_prefix: string
        :param s3_key_prefix: Specifies the Amazon S3 key prefix that precedes
            the name of the bucket you have designated for log file delivery.

        :type sns_topic_name: string
        :param sns_topic_name: Specifies the name of the Amazon SNS topic
            defined for notification of log file delivery.

        :type include_global_service_events: boolean
        :param include_global_service_events: Specifies whether the trail is
            publishing events from global services such as IAM to the log
            files.

        :type cloud_watch_logs_log_group_arn: string
        :param cloud_watch_logs_log_group_arn: Specifies a log group name using
            an Amazon Resource Name (ARN), a unique identifier that represents
            the log group to which CloudTrail logs will be delivered. Not
            required unless you specify CloudWatchLogsRoleArn.

        :type cloud_watch_logs_role_arn: string
        :param cloud_watch_logs_role_arn: Specifies the role for the CloudWatch
            Logs endpoint to assume to write to a users log group.

        """
        params = {'Name': name, 'S3BucketName': s3_bucket_name, }
        if s3_key_prefix is not None:
            params['S3KeyPrefix'] = s3_key_prefix
        if sns_topic_name is not None:
            params['SnsTopicName'] = sns_topic_name
        if include_global_service_events is not None:
            params['IncludeGlobalServiceEvents'] = include_global_service_events
        if cloud_watch_logs_log_group_arn is not None:
            params['CloudWatchLogsLogGroupArn'] = cloud_watch_logs_log_group_arn
        if cloud_watch_logs_role_arn is not None:
            params['CloudWatchLogsRoleArn'] = cloud_watch_logs_role_arn
        return self.make_request(action='CreateTrail',
                                 body=json.dumps(params))

    def delete_trail(self, name):
        """
        Deletes a trail.

        :type name: string
        :param name: The name of a trail to be deleted.

        """
        params = {'Name': name, }
        return self.make_request(action='DeleteTrail',
                                 body=json.dumps(params))

    def describe_trails(self, trail_name_list=None):
        """
        Retrieves settings for the trail associated with the current
        region for your account.

        :type trail_name_list: list
        :param trail_name_list: The trail returned.

        """
        params = {}
        if trail_name_list is not None:
            params['trailNameList'] = trail_name_list
        return self.make_request(action='DescribeTrails',
                                 body=json.dumps(params))

    def get_trail_status(self, name):
        """
        Returns a JSON-formatted list of information about the
        specified trail. Fields include information on delivery
        errors, Amazon SNS and Amazon S3 errors, and start and stop
        logging times for each trail.

        :type name: string
        :param name: The name of the trail for which you are requesting the
            current status.

        """
        params = {'Name': name, }
        return self.make_request(action='GetTrailStatus',
                                 body=json.dumps(params))

    def lookup_events(self, lookup_attributes=None, start_time=None,
                      end_time=None, max_results=None, next_token=None):
        """
        Looks up API activity events captured by CloudTrail that
        create, update, or delete resources in your account. Events
        for a region can be looked up for the times in which you had
        CloudTrail turned on in that region during the last seven
        days. Lookup supports five different attributes: time range
        (defined by a start time and end time), user name, event name,
        resource type, and resource name. All attributes are optional.
        The maximum number of attributes that can be specified in any
        one lookup request are time range and one other attribute. The
        default number of results returned is 10, with a maximum of 50
        possible. The response includes a token that you can use to
        get the next page of results.
        The rate of lookup requests is limited to one per second per
        account. If this limit is exceeded, a throttling error occurs.
        Events that occurred during the selected time range will not
        be available for lookup if CloudTrail logging was not enabled
        when the events occurred.

        :type lookup_attributes: list
        :param lookup_attributes: Contains a list of lookup attributes.
            Currently the list can contain only one item.

        :type start_time: timestamp
        :param start_time: Specifies that only events that occur after or at
            the specified time are returned. If the specified start time is
            after the specified end time, an error is returned.

        :type end_time: timestamp
        :param end_time: Specifies that only events that occur before or at the
            specified time are returned. If the specified end time is before
            the specified start time, an error is returned.

        :type max_results: integer
        :param max_results: The number of events to return. Possible values are
            1 through 50. The default is 10.

        :type next_token: string
        :param next_token: The token to use to get the next page of results
            after a previous API call. This token must be passed in with the
            same parameters that were specified in the the original call. For
            example, if the original call specified an AttributeKey of
            'Username' with a value of 'root', the call with NextToken should
            include those same parameters.

        """
        params = {}
        if lookup_attributes is not None:
            params['LookupAttributes'] = lookup_attributes
        if start_time is not None:
            params['StartTime'] = start_time
        if end_time is not None:
            params['EndTime'] = end_time
        if max_results is not None:
            params['MaxResults'] = max_results
        if next_token is not None:
            params['NextToken'] = next_token
        return self.make_request(action='LookupEvents',
                                 body=json.dumps(params))

    def start_logging(self, name):
        """
        Starts the recording of AWS API calls and log file delivery
        for a trail.

        :type name: string
        :param name: The name of the trail for which CloudTrail logs AWS API
            calls.

        """
        params = {'Name': name, }
        return self.make_request(action='StartLogging',
                                 body=json.dumps(params))

    def stop_logging(self, name):
        """
        Suspends the recording of AWS API calls and log file delivery
        for the specified trail. Under most circumstances, there is no
        need to use this action. You can update a trail without
        stopping it first. This action is the only way to stop
        recording.

        :type name: string
        :param name: Communicates to CloudTrail the name of the trail for which
            to stop logging AWS API calls.

        """
        params = {'Name': name, }
        return self.make_request(action='StopLogging',
                                 body=json.dumps(params))

    def update_trail(self, name, s3_bucket_name=None, s3_key_prefix=None,
                     sns_topic_name=None, include_global_service_events=None,
                     cloud_watch_logs_log_group_arn=None,
                     cloud_watch_logs_role_arn=None):
        """
        From the command line, use `update-subscription`.

        Updates the settings that specify delivery of log files.
        Changes to a trail do not require stopping the CloudTrail
        service. Use this action to designate an existing bucket for
        log delivery. If the existing bucket has previously been a
        target for CloudTrail log files, an IAM policy exists for the
        bucket.

        :type name: string
        :param name: Specifies the name of the trail.

        :type s3_bucket_name: string
        :param s3_bucket_name: Specifies the name of the Amazon S3 bucket
            designated for publishing log files.

        :type s3_key_prefix: string
        :param s3_key_prefix: Specifies the Amazon S3 key prefix that precedes
            the name of the bucket you have designated for log file delivery.

        :type sns_topic_name: string
        :param sns_topic_name: Specifies the name of the Amazon SNS topic
            defined for notification of log file delivery.

        :type include_global_service_events: boolean
        :param include_global_service_events: Specifies whether the trail is
            publishing events from global services such as IAM to the log
            files.

        :type cloud_watch_logs_log_group_arn: string
        :param cloud_watch_logs_log_group_arn: Specifies a log group name using
            an Amazon Resource Name (ARN), a unique identifier that represents
            the log group to which CloudTrail logs will be delivered. Not
            required unless you specify CloudWatchLogsRoleArn.

        :type cloud_watch_logs_role_arn: string
        :param cloud_watch_logs_role_arn: Specifies the role for the CloudWatch
            Logs endpoint to assume to write to a users log group.

        """
        params = {'Name': name, }
        if s3_bucket_name is not None:
            params['S3BucketName'] = s3_bucket_name
        if s3_key_prefix is not None:
            params['S3KeyPrefix'] = s3_key_prefix
        if sns_topic_name is not None:
            params['SnsTopicName'] = sns_topic_name
        if include_global_service_events is not None:
            params['IncludeGlobalServiceEvents'] = include_global_service_events
        if cloud_watch_logs_log_group_arn is not None:
            params['CloudWatchLogsLogGroupArn'] = cloud_watch_logs_log_group_arn
        if cloud_watch_logs_role_arn is not None:
            params['CloudWatchLogsRoleArn'] = cloud_watch_logs_role_arn
        return self.make_request(action='UpdateTrail',
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
