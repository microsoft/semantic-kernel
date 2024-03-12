# Copyright (c) 2010-2012 Mitch Garnaat http://garnaat.org/
# Copyright (c) 2012 Amazon.com, Inc. or its affiliates.  All Rights Reserved
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

import uuid
import hashlib

from boto.connection import AWSQueryConnection
from boto.regioninfo import RegionInfo
from boto.compat import json
import boto


class SNSConnection(AWSQueryConnection):
    """
    Amazon Simple Notification Service
    Amazon Simple Notification Service (Amazon SNS) is a web service
    that enables you to build distributed web-enabled applications.
    Applications can use Amazon SNS to easily push real-time
    notification messages to interested subscribers over multiple
    delivery protocols. For more information about this product see
    `http://aws.amazon.com/sns`_. For detailed information about
    Amazon SNS features and their associated API calls, see the
    `Amazon SNS Developer Guide`_.

    We also provide SDKs that enable you to access Amazon SNS from
    your preferred programming language. The SDKs contain
    functionality that automatically takes care of tasks such as:
    cryptographically signing your service requests, retrying
    requests, and handling error responses. For a list of available
    SDKs, go to `Tools for Amazon Web Services`_.
    """
    DefaultRegionName = boto.config.get('Boto', 'sns_region_name', 'us-east-1')
    DefaultRegionEndpoint = boto.config.get('Boto', 'sns_region_endpoint', 
                                            'sns.us-east-1.amazonaws.com')
    APIVersion = boto.config.get('Boto', 'sns_version', '2010-03-31')


    def __init__(self, aws_access_key_id=None, aws_secret_access_key=None,
                 is_secure=True, port=None, proxy=None, proxy_port=None,
                 proxy_user=None, proxy_pass=None, debug=0,
                 https_connection_factory=None, region=None, path='/',
                 security_token=None, validate_certs=True,
                 profile_name=None):
        if not region:
            region = RegionInfo(self, self.DefaultRegionName,
                                self.DefaultRegionEndpoint,
                                connection_cls=SNSConnection)
        self.region = region
        super(SNSConnection, self).__init__(aws_access_key_id,
                                    aws_secret_access_key,
                                    is_secure, port, proxy, proxy_port,
                                    proxy_user, proxy_pass,
                                    self.region.endpoint, debug,
                                    https_connection_factory, path,
                                    security_token=security_token,
                                    validate_certs=validate_certs,
                                    profile_name=profile_name)

    def _build_dict_as_list_params(self, params, dictionary, name):
      """
            Serialize a parameter 'name' which value is a 'dictionary' into a list of parameters.

            See: http://docs.aws.amazon.com/sns/latest/api/API_SetPlatformApplicationAttributes.html
            For example::

                dictionary = {'PlatformPrincipal': 'foo', 'PlatformCredential': 'bar'}
                name = 'Attributes'

            would result in params dict being populated with:
                Attributes.entry.1.key    = PlatformPrincipal
                Attributes.entry.1.value  = foo
                Attributes.entry.2.key    = PlatformCredential
                Attributes.entry.2.value  = bar

      :param params: the resulting parameters will be added to this dict
      :param dictionary: dict - value of the serialized parameter
      :param name: name of the serialized parameter
      """
      items = sorted(dictionary.items(), key=lambda x:x[0])
      for kv, index in zip(items, list(range(1, len(items)+1))):
        key, value = kv
        prefix = '%s.entry.%s' % (name, index)
        params['%s.key' % prefix] = key
        params['%s.value' % prefix] = value

    def _required_auth_capability(self):
        return ['hmac-v4']

    def get_all_topics(self, next_token=None):
        """
        :type next_token: string
        :param next_token: Token returned by the previous call to
                           this method.

        """
        params = {}
        if next_token:
            params['NextToken'] = next_token
        return self._make_request('ListTopics', params)

    def get_topic_attributes(self, topic):
        """
        Get attributes of a Topic

        :type topic: string
        :param topic: The ARN of the topic.

        """
        params = {'TopicArn': topic}
        return self._make_request('GetTopicAttributes', params)

    def set_topic_attributes(self, topic, attr_name, attr_value):
        """
        Get attributes of a Topic

        :type topic: string
        :param topic: The ARN of the topic.

        :type attr_name: string
        :param attr_name: The name of the attribute you want to set.
                          Only a subset of the topic's attributes are mutable.
                          Valid values: Policy | DisplayName

        :type attr_value: string
        :param attr_value: The new value for the attribute.

        """
        params = {'TopicArn': topic,
                  'AttributeName': attr_name,
                  'AttributeValue': attr_value}
        return self._make_request('SetTopicAttributes', params)

    def add_permission(self, topic, label, account_ids, actions):
        """
        Adds a statement to a topic's access control policy, granting
        access for the specified AWS accounts to the specified actions.

        :type topic: string
        :param topic: The ARN of the topic.

        :type label: string
        :param label: A unique identifier for the new policy statement.

        :type account_ids: list of strings
        :param account_ids: The AWS account ids of the users who will be
                            give access to the specified actions.

        :type actions: list of strings
        :param actions: The actions you want to allow for each of the
                        specified principal(s).

        """
        params = {'TopicArn': topic,
                  'Label': label}
        self.build_list_params(params, account_ids, 'AWSAccountId.member')
        self.build_list_params(params, actions, 'ActionName.member')
        return self._make_request('AddPermission', params)

    def remove_permission(self, topic, label):
        """
        Removes a statement from a topic's access control policy.

        :type topic: string
        :param topic: The ARN of the topic.

        :type label: string
        :param label: A unique identifier for the policy statement
                      to be removed.

        """
        params = {'TopicArn': topic,
                  'Label': label}
        return self._make_request('RemovePermission', params)

    def create_topic(self, topic):
        """
        Create a new Topic.

        :type topic: string
        :param topic: The name of the new topic.

        """
        params = {'Name': topic}
        return self._make_request('CreateTopic', params)

    def delete_topic(self, topic):
        """
        Delete an existing topic

        :type topic: string
        :param topic: The ARN of the topic

        """
        params = {'TopicArn': topic}
        return self._make_request('DeleteTopic', params, '/', 'GET')

    def publish(self, topic=None, message=None, subject=None, target_arn=None,
                message_structure=None, message_attributes=None):
        """
        Sends a message to all of a topic's subscribed endpoints

        :type topic: string
        :param topic: The topic you want to publish to.

        :type message: string
        :param message: The message you want to send to the topic.
                        Messages must be UTF-8 encoded strings and
                        be at most 4KB in size.

        :type message_structure: string
        :param message_structure: Optional parameter. If left as ``None``,
                                  plain text will be sent. If set to ``json``,
                                  your message should be a JSON string that
                                  matches the structure described at
                                  http://docs.aws.amazon.com/sns/latest/dg/PublishTopic.html#sns-message-formatting-by-protocol

        :type message_attributes: dict
        :param message_attributes: Message attributes to set. Should be
            of the form:

            .. code-block:: python

                {
                    "name1": {
                        "data_type": "Number",
                        "string_value": "42"
                    },
                    "name2": {
                        "data_type": "String",
                        "string_value": "Bob"
                    }
                }

        :type subject: string
        :param subject: Optional parameter to be used as the "Subject"
                        line of the email notifications.

        :type target_arn: string
        :param target_arn: Optional parameter for either TopicArn or
                           EndpointArn, but not both.

        """
        if message is None:
            # To be backwards compatible when message did not have
            # a default value and topic and message were required
            # args.
            raise TypeError("'message' is a required parameter")
        params = {'Message': message}
        if subject is not None:
            params['Subject'] = subject
        if topic is not None:
            params['TopicArn'] = topic
        if target_arn is not None:
            params['TargetArn'] = target_arn
        if message_structure is not None:
            params['MessageStructure'] = message_structure
        if message_attributes is not None:
            keys = sorted(message_attributes.keys())
            for i, name in enumerate(keys, start=1):
                attribute = message_attributes[name]
                params['MessageAttributes.entry.{0}.Name'.format(i)] = name
                if 'data_type' in attribute:
                    params['MessageAttributes.entry.{0}.Value.DataType'.format(i)] = \
                        attribute['data_type']
                if 'string_value' in attribute:
                    params['MessageAttributes.entry.{0}.Value.StringValue'.format(i)] = \
                        attribute['string_value']
                if 'binary_value' in attribute:
                    params['MessageAttributes.entry.{0}.Value.BinaryValue'.format(i)] = \
                        attribute['binary_value']
        return self._make_request('Publish', params, '/', 'POST')

    def subscribe(self, topic, protocol, endpoint):
        """
        Subscribe to a Topic.

        :type topic: string
        :param topic: The ARN of the new topic.

        :type protocol: string
        :param protocol: The protocol used to communicate with
                         the subscriber.  Current choices are:
                         email|email-json|http|https|sqs|sms|application

        :type endpoint: string
        :param endpoint: The location of the endpoint for
                         the subscriber.
                         * For email, this would be a valid email address
                         * For email-json, this would be a valid email address
                         * For http, this would be a URL beginning with http
                         * For https, this would be a URL beginning with https
                         * For sqs, this would be the ARN of an SQS Queue
                         * For sms, this would be a phone number of an
                           SMS-enabled device
                         * For application, the endpoint is the EndpointArn
                           of a mobile app and device.
        """
        params = {'TopicArn': topic,
                  'Protocol': protocol,
                  'Endpoint': endpoint}
        return self._make_request('Subscribe', params)

    def subscribe_sqs_queue(self, topic, queue):
        """
        Subscribe an SQS queue to a topic.

        This is convenience method that handles most of the complexity involved
        in using an SQS queue as an endpoint for an SNS topic.  To achieve this
        the following operations are performed:

        * The correct ARN is constructed for the SQS queue and that ARN is
          then subscribed to the topic.
        * A JSON policy document is contructed that grants permission to
          the SNS topic to send messages to the SQS queue.
        * This JSON policy is then associated with the SQS queue using
          the queue's set_attribute method.  If the queue already has
          a policy associated with it, this process will add a Statement to
          that policy.  If no policy exists, a new policy will be created.

        :type topic: string
        :param topic: The ARN of the new topic.

        :type queue: A boto Queue object
        :param queue: The queue you wish to subscribe to the SNS Topic.
        """
        t = queue.id.split('/')
        q_arn = queue.arn
        sid = hashlib.md5((topic + q_arn).encode('utf-8')).hexdigest()
        sid_exists = False
        resp = self.subscribe(topic, 'sqs', q_arn)
        attr = queue.get_attributes('Policy')
        if 'Policy' in attr:
            policy = json.loads(attr['Policy'])
        else:
            policy = {}
        if 'Version' not in policy:
            policy['Version'] = '2008-10-17'
        if 'Statement' not in policy:
            policy['Statement'] = []
        # See if a Statement with the Sid exists already.
        for s in policy['Statement']:
            if s['Sid'] == sid:
                sid_exists = True
        if not sid_exists:
            statement = {'Action': 'SQS:SendMessage',
                         'Effect': 'Allow',
                         'Principal': {'AWS': '*'},
                         'Resource': q_arn,
                         'Sid': sid,
                         'Condition': {'StringLike': {'aws:SourceArn': topic}}}
            policy['Statement'].append(statement)
        queue.set_attribute('Policy', json.dumps(policy))
        return resp

    def confirm_subscription(self, topic, token,
                             authenticate_on_unsubscribe=False):
        """
        Get properties of a Topic

        :type topic: string
        :param topic: The ARN of the new topic.

        :type token: string
        :param token: Short-lived token sent to and endpoint during
                      the Subscribe operation.

        :type authenticate_on_unsubscribe: bool
        :param authenticate_on_unsubscribe: Optional parameter indicating
                                            that you wish to disable
                                            unauthenticated unsubscription
                                            of the subscription.

        """
        params = {'TopicArn': topic, 'Token': token}
        if authenticate_on_unsubscribe:
            params['AuthenticateOnUnsubscribe'] = 'true'
        return self._make_request('ConfirmSubscription', params)

    def unsubscribe(self, subscription):
        """
        Allows endpoint owner to delete subscription.
        Confirmation message will be delivered.

        :type subscription: string
        :param subscription: The ARN of the subscription to be deleted.

        """
        params = {'SubscriptionArn': subscription}
        return self._make_request('Unsubscribe', params)

    def get_all_subscriptions(self, next_token=None):
        """
        Get list of all subscriptions.

        :type next_token: string
        :param next_token: Token returned by the previous call to
                           this method.

        """
        params = {}
        if next_token:
            params['NextToken'] = next_token
        return self._make_request('ListSubscriptions', params)

    def get_all_subscriptions_by_topic(self, topic, next_token=None):
        """
        Get list of all subscriptions to a specific topic.

        :type topic: string
        :param topic: The ARN of the topic for which you wish to
                      find subscriptions.

        :type next_token: string
        :param next_token: Token returned by the previous call to
                           this method.

        """
        params = {'TopicArn': topic}
        if next_token:
            params['NextToken'] = next_token
        return self._make_request('ListSubscriptionsByTopic', params)

    def create_platform_application(self, name=None, platform=None,
                                    attributes=None):
        """
        The `CreatePlatformApplication` action creates a platform
        application object for one of the supported push notification
        services, such as APNS and GCM, to which devices and mobile
        apps may register. You must specify PlatformPrincipal and
        PlatformCredential attributes when using the
        `CreatePlatformApplication` action. The PlatformPrincipal is
        received from the notification service. For APNS/APNS_SANDBOX,
        PlatformPrincipal is "SSL certificate". For GCM,
        PlatformPrincipal is not applicable. For ADM,
        PlatformPrincipal is "client id". The PlatformCredential is
        also received from the notification service. For
        APNS/APNS_SANDBOX, PlatformCredential is "private key". For
        GCM, PlatformCredential is "API key". For ADM,
        PlatformCredential is "client secret". The
        PlatformApplicationArn that is returned when using
        `CreatePlatformApplication` is then used as an attribute for
        the `CreatePlatformEndpoint` action. For more information, see
        `Using Amazon SNS Mobile Push Notifications`_.

        :type name: string
        :param name: Application names must be made up of only uppercase and
            lowercase ASCII letters, numbers, underscores, hyphens, and
            periods, and must be between 1 and 256 characters long.

        :type platform: string
        :param platform: The following platforms are supported: ADM (Amazon
            Device Messaging), APNS (Apple Push Notification Service),
            APNS_SANDBOX, and GCM (Google Cloud Messaging).

        :type attributes: map
        :param attributes: For a list of attributes, see
            `SetPlatformApplicationAttributes`_

        """
        params = {}
        if name is not None:
            params['Name'] = name
        if platform is not None:
            params['Platform'] = platform
        if attributes is not None:
            self._build_dict_as_list_params(params, attributes, 'Attributes')
        return self._make_request(action='CreatePlatformApplication',
                                  params=params)

    def set_platform_application_attributes(self,
                                            platform_application_arn=None,
                                            attributes=None):
        """
        The `SetPlatformApplicationAttributes` action sets the
        attributes of the platform application object for the
        supported push notification services, such as APNS and GCM.
        For more information, see `Using Amazon SNS Mobile Push
        Notifications`_.

        :type platform_application_arn: string
        :param platform_application_arn: PlatformApplicationArn for
            SetPlatformApplicationAttributes action.

        :type attributes: map
        :param attributes:
        A map of the platform application attributes. Attributes in this map
            include the following:


        + `PlatformCredential` -- The credential received from the notification
              service. For APNS/APNS_SANDBOX, PlatformCredential is "private
              key". For GCM, PlatformCredential is "API key". For ADM,
              PlatformCredential is "client secret".
        + `PlatformPrincipal` -- The principal received from the notification
              service. For APNS/APNS_SANDBOX, PlatformPrincipal is "SSL
              certificate". For GCM, PlatformPrincipal is not applicable. For
              ADM, PlatformPrincipal is "client id".
        + `EventEndpointCreated` -- Topic ARN to which EndpointCreated event
              notifications should be sent.
        + `EventEndpointDeleted` -- Topic ARN to which EndpointDeleted event
              notifications should be sent.
        + `EventEndpointUpdated` -- Topic ARN to which EndpointUpdate event
              notifications should be sent.
        + `EventDeliveryFailure` -- Topic ARN to which DeliveryFailure event
              notifications should be sent upon Direct Publish delivery failure
              (permanent) to one of the application's endpoints.

        """
        params = {}
        if platform_application_arn is not None:
            params['PlatformApplicationArn'] = platform_application_arn
        if attributes is not None:
            self._build_dict_as_list_params(params, attributes, 'Attributes')
        return self._make_request(action='SetPlatformApplicationAttributes',
                                  params=params)

    def get_platform_application_attributes(self,
                                            platform_application_arn=None):
        """
        The `GetPlatformApplicationAttributes` action retrieves the
        attributes of the platform application object for the
        supported push notification services, such as APNS and GCM.
        For more information, see `Using Amazon SNS Mobile Push
        Notifications`_.

        :type platform_application_arn: string
        :param platform_application_arn: PlatformApplicationArn for
            GetPlatformApplicationAttributesInput.

        """
        params = {}
        if platform_application_arn is not None:
            params['PlatformApplicationArn'] = platform_application_arn
        return self._make_request(action='GetPlatformApplicationAttributes',
                                  params=params)

    def list_platform_applications(self, next_token=None):
        """
        The `ListPlatformApplications` action lists the platform
        application objects for the supported push notification
        services, such as APNS and GCM. The results for
        `ListPlatformApplications` are paginated and return a limited
        list of applications, up to 100. If additional records are
        available after the first page results, then a NextToken
        string will be returned. To receive the next page, you call
        `ListPlatformApplications` using the NextToken string received
        from the previous call. When there are no more records to
        return, NextToken will be null. For more information, see
        `Using Amazon SNS Mobile Push Notifications`_.

        :type next_token: string
        :param next_token: NextToken string is used when calling
            ListPlatformApplications action to retrieve additional records that
            are available after the first page results.

        """
        params = {}
        if next_token is not None:
            params['NextToken'] = next_token
        return self._make_request(action='ListPlatformApplications',
                                  params=params)

    def list_endpoints_by_platform_application(self,
                                               platform_application_arn=None,
                                               next_token=None):
        """
        The `ListEndpointsByPlatformApplication` action lists the
        endpoints and endpoint attributes for devices in a supported
        push notification service, such as GCM and APNS. The results
        for `ListEndpointsByPlatformApplication` are paginated and
        return a limited list of endpoints, up to 100. If additional
        records are available after the first page results, then a
        NextToken string will be returned. To receive the next page,
        you call `ListEndpointsByPlatformApplication` again using the
        NextToken string received from the previous call. When there
        are no more records to return, NextToken will be null. For
        more information, see `Using Amazon SNS Mobile Push
        Notifications`_.

        :type platform_application_arn: string
        :param platform_application_arn: PlatformApplicationArn for
            ListEndpointsByPlatformApplicationInput action.

        :type next_token: string
        :param next_token: NextToken string is used when calling
            ListEndpointsByPlatformApplication action to retrieve additional
            records that are available after the first page results.

        """
        params = {}
        if platform_application_arn is not None:
            params['PlatformApplicationArn'] = platform_application_arn
        if next_token is not None:
            params['NextToken'] = next_token
        return self._make_request(action='ListEndpointsByPlatformApplication',
                                  params=params)

    def delete_platform_application(self, platform_application_arn=None):
        """
        The `DeletePlatformApplication` action deletes a platform
        application object for one of the supported push notification
        services, such as APNS and GCM. For more information, see
        `Using Amazon SNS Mobile Push Notifications`_.

        :type platform_application_arn: string
        :param platform_application_arn: PlatformApplicationArn of platform
            application object to delete.

        """
        params = {}
        if platform_application_arn is not None:
            params['PlatformApplicationArn'] = platform_application_arn
        return self._make_request(action='DeletePlatformApplication',
                                  params=params)

    def create_platform_endpoint(self, platform_application_arn=None,
                                 token=None, custom_user_data=None,
                                 attributes=None):
        """
        The `CreatePlatformEndpoint` creates an endpoint for a device
        and mobile app on one of the supported push notification
        services, such as GCM and APNS. `CreatePlatformEndpoint`
        requires the PlatformApplicationArn that is returned from
        `CreatePlatformApplication`. The EndpointArn that is returned
        when using `CreatePlatformEndpoint` can then be used by the
        `Publish` action to send a message to a mobile app or by the
        `Subscribe` action for subscription to a topic. For more
        information, see `Using Amazon SNS Mobile Push
        Notifications`_.

        :type platform_application_arn: string
        :param platform_application_arn: PlatformApplicationArn returned from
            CreatePlatformApplication is used to create a an endpoint.

        :type token: string
        :param token: Unique identifier created by the notification service for
            an app on a device. The specific name for Token will vary,
            depending on which notification service is being used. For example,
            when using APNS as the notification service, you need the device
            token. Alternatively, when using GCM or ADM, the device token
            equivalent is called the registration ID.

        :type custom_user_data: string
        :param custom_user_data: Arbitrary user data to associate with the
            endpoint. SNS does not use this data. The data must be in UTF-8
            format and less than 2KB.

        :type attributes: map
        :param attributes: For a list of attributes, see
            `SetEndpointAttributes`_.

        """
        params = {}
        if platform_application_arn is not None:
            params['PlatformApplicationArn'] = platform_application_arn
        if token is not None:
            params['Token'] = token
        if custom_user_data is not None:
            params['CustomUserData'] = custom_user_data
        if attributes is not None:
            self._build_dict_as_list_params(params, attributes, 'Attributes')
        return self._make_request(action='CreatePlatformEndpoint',
                                  params=params)

    def delete_endpoint(self, endpoint_arn=None):
        """
        The `DeleteEndpoint` action, which is idempotent, deletes the
        endpoint from SNS. For more information, see `Using Amazon SNS
        Mobile Push Notifications`_.

        :type endpoint_arn: string
        :param endpoint_arn: EndpointArn of endpoint to delete.

        """
        params = {}
        if endpoint_arn is not None:
            params['EndpointArn'] = endpoint_arn
        return self._make_request(action='DeleteEndpoint', params=params)

    def set_endpoint_attributes(self, endpoint_arn=None, attributes=None):
        """
        The `SetEndpointAttributes` action sets the attributes for an
        endpoint for a device on one of the supported push
        notification services, such as GCM and APNS. For more
        information, see `Using Amazon SNS Mobile Push
        Notifications`_.

        :type endpoint_arn: string
        :param endpoint_arn: EndpointArn used for SetEndpointAttributes action.

        :type attributes: map
        :param attributes:
        A map of the endpoint attributes. Attributes in this map include the
            following:


        + `CustomUserData` -- arbitrary user data to associate with the
              endpoint. SNS does not use this data. The data must be in UTF-8
              format and less than 2KB.
        + `Enabled` -- flag that enables/disables delivery to the endpoint.
              Message Processor will set this to false when a notification
              service indicates to SNS that the endpoint is invalid. Users can
              set it back to true, typically after updating Token.
        + `Token` -- device token, also referred to as a registration id, for
              an app and mobile device. This is returned from the notification
              service when an app and mobile device are registered with the
              notification service.

        """
        params = {}
        if endpoint_arn is not None:
            params['EndpointArn'] = endpoint_arn
        if attributes is not None:
            self._build_dict_as_list_params(params, attributes, 'Attributes')
        return self._make_request(action='SetEndpointAttributes',
                                  params=params)

    def get_endpoint_attributes(self, endpoint_arn=None):
        """
        The `GetEndpointAttributes` retrieves the endpoint attributes
        for a device on one of the supported push notification
        services, such as GCM and APNS. For more information, see
        `Using Amazon SNS Mobile Push Notifications`_.

        :type endpoint_arn: string
        :param endpoint_arn: EndpointArn for GetEndpointAttributes input.

        """
        params = {}
        if endpoint_arn is not None:
            params['EndpointArn'] = endpoint_arn
        return self._make_request(action='GetEndpointAttributes',
                                  params=params)

    def _make_request(self, action, params, path='/', verb='GET'):
        params['ContentType'] = 'JSON'
        response = self.make_request(action=action, verb=verb,
                                     path=path, params=params)
        body = response.read().decode('utf-8')
        boto.log.debug(body)
        if response.status == 200:
            return json.loads(body)
        else:
            boto.log.error('%s %s' % (response.status, response.reason))
            boto.log.error('%s' % body)
            raise self.ResponseError(response.status, response.reason, body)
