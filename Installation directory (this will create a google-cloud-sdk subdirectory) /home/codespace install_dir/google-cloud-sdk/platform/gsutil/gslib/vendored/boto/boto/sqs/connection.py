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

import boto
from boto.connection import AWSQueryConnection
from boto.sqs.regioninfo import SQSRegionInfo
from boto.sqs.queue import Queue
from boto.sqs.message import Message
from boto.sqs.attributes import Attributes
from boto.sqs.batchresults import BatchResults
from boto.exception import SQSError, BotoServerError


class SQSConnection(AWSQueryConnection):
    """
    A Connection to the SQS Service.
    """
    DefaultRegionName = boto.config.get('Boto', 'sqs_region_name', 'us-east-1')
    DefaultRegionEndpoint = boto.config.get('Boto', 'sqs_region_endpoint',
                                            'queue.amazonaws.com')
    APIVersion = boto.config.get('Boto', 'sqs_version', '2012-11-05')
    DefaultContentType = 'text/plain'
    ResponseError = SQSError
    AuthServiceName = 'sqs'

    def __init__(self, aws_access_key_id=None, aws_secret_access_key=None,
                 is_secure=True, port=None, proxy=None, proxy_port=None,
                 proxy_user=None, proxy_pass=None, debug=0,
                 https_connection_factory=None, region=None, path='/',
                 security_token=None, validate_certs=True, profile_name=None):
        if not region:
            region = SQSRegionInfo(self, self.DefaultRegionName,
                                   self.DefaultRegionEndpoint)
        self.region = region
        super(SQSConnection, self).__init__(aws_access_key_id,
                                    aws_secret_access_key,
                                    is_secure, port,
                                    proxy, proxy_port,
                                    proxy_user, proxy_pass,
                                    self.region.endpoint, debug,
                                    https_connection_factory, path,
                                    security_token=security_token,
                                    validate_certs=validate_certs,
                                    profile_name=profile_name)
        self.auth_region_name = self.region.name

    def _required_auth_capability(self):
        return ['hmac-v4']

    def create_queue(self, queue_name, visibility_timeout=None):
        """
        Create an SQS Queue.

        :type queue_name: str or unicode
        :param queue_name: The name of the new queue.  Names are
            scoped to an account and need to be unique within that
            account.  Calling this method on an existing queue name
            will not return an error from SQS unless the value for
            visibility_timeout is different than the value of the
            existing queue of that name.  This is still an expensive
            operation, though, and not the preferred way to check for
            the existence of a queue.  See the
            :func:`boto.sqs.connection.SQSConnection.lookup` method.

        :type visibility_timeout: int
        :param visibility_timeout: The default visibility timeout for
            all messages written in the queue.  This can be overridden
            on a per-message.

        :rtype: :class:`boto.sqs.queue.Queue`
        :return: The newly created queue.

        """
        params = {'QueueName': queue_name}
        if visibility_timeout:
            params['Attribute.1.Name'] = 'VisibilityTimeout'
            params['Attribute.1.Value'] = int(visibility_timeout)
        return self.get_object('CreateQueue', params, Queue)

    def delete_queue(self, queue, force_deletion=False):
        """
        Delete an SQS Queue.

        :type queue: A Queue object
        :param queue: The SQS queue to be deleted

        :type force_deletion: Boolean
        :param force_deletion: A deprecated parameter that is no longer used by
            SQS's API.

        :rtype: bool
        :return: True if the command succeeded, False otherwise
        """
        return self.get_status('DeleteQueue', None, queue.id)

    def purge_queue(self, queue):
        """
        Purge all messages in an SQS Queue.

        :type queue: A Queue object
        :param queue: The SQS queue to be purged

        :rtype: bool
        :return: True if the command succeeded, False otherwise
        """
        return self.get_status('PurgeQueue', None, queue.id)

    def get_queue_attributes(self, queue, attribute='All'):
        """
        Gets one or all attributes of a Queue

        :type queue: A Queue object
        :param queue: The SQS queue to get attributes for

        :type attribute: str
        :param attribute: The specific attribute requested.  If not
            supplied, the default is to return all attributes.  Valid
            attributes are:

            * All
            * ApproximateNumberOfMessages
            * ApproximateNumberOfMessagesNotVisible
            * VisibilityTimeout
            * CreatedTimestamp
            * LastModifiedTimestamp
            * Policy
            * MaximumMessageSize
            * MessageRetentionPeriod
            * QueueArn
            * ApproximateNumberOfMessagesDelayed
            * DelaySeconds
            * ReceiveMessageWaitTimeSeconds
            * RedrivePolicy

        :rtype: :class:`boto.sqs.attributes.Attributes`
        :return: An Attributes object containing request value(s).
        """
        params = {'AttributeName' : attribute}
        return self.get_object('GetQueueAttributes', params,
                               Attributes, queue.id)

    def set_queue_attribute(self, queue, attribute, value):
        """
        Set a new value for an attribute of a Queue.

        :type queue: A Queue object
        :param queue: The SQS queue to get attributes for

        :type attribute: String
        :param attribute: The name of the attribute you want to set.

        :param value: The new value for the attribute must be:

            * For `DelaySeconds` the value must be an integer number of
            seconds from 0 to 900 (15 minutes).
                >>> connection.set_queue_attribute(queue, 'DelaySeconds', 900)

            * For `MaximumMessageSize` the value must be an integer number of
            bytes from 1024 (1 KiB) to 262144 (256 KiB).
                >>> connection.set_queue_attribute(queue, 'MaximumMessageSize', 262144)

            * For `MessageRetentionPeriod` the value must be an integer number of
            seconds from 60 (1 minute) to 1209600 (14 days).
                >>> connection.set_queue_attribute(queue, 'MessageRetentionPeriod', 1209600)

            * For `Policy` the value must be an string that contains JSON formatted
            parameters and values.
                >>> connection.set_queue_attribute(queue, 'Policy', json.dumps({
                ...     'Version': '2008-10-17',
                ...     'Id': '/123456789012/testQueue/SQSDefaultPolicy',
                ...     'Statement': [
                ...        {
                ...            'Sid': 'Queue1ReceiveMessage',
                ...            'Effect': 'Allow',
                ...            'Principal': {
                ...                'AWS': '*'
                ...            },
                ...            'Action': 'SQS:ReceiveMessage',
                ...            'Resource': 'arn:aws:aws:sqs:us-east-1:123456789012:testQueue'
                ...        }
                ...    ]
                ... }))

            * For `ReceiveMessageWaitTimeSeconds` the value must be an integer number of
            seconds from 0 to 20.
                >>> connection.set_queue_attribute(queue, 'ReceiveMessageWaitTimeSeconds', 20)

            * For `VisibilityTimeout` the value must be an integer number of
            seconds from 0 to 43200 (12 hours).
                >>> connection.set_queue_attribute(queue, 'VisibilityTimeout', 43200)

            * For `RedrivePolicy` the value must be an string that contains JSON formatted
            parameters and values. You can set maxReceiveCount to a value between 1 and 1000.
            The deadLetterTargetArn value is the Amazon Resource Name (ARN) of the queue that
            will receive the dead letter messages.
                >>> connection.set_queue_attribute(queue, 'RedrivePolicy', json.dumps({
                ...    'maxReceiveCount': 5,
                ...    'deadLetterTargetArn': "arn:aws:aws:sqs:us-east-1:123456789012:testDeadLetterQueue"
                ... }))
        """

        params = {'Attribute.Name' : attribute, 'Attribute.Value' : value}
        return self.get_status('SetQueueAttributes', params, queue.id)

    def receive_message(self, queue, number_messages=1,
                        visibility_timeout=None, attributes=None,
                        wait_time_seconds=None, message_attributes=None):
        """
        Read messages from an SQS Queue.

        :type queue: A Queue object
        :param queue: The Queue from which messages are read.

        :type number_messages: int
        :param number_messages: The maximum number of messages to read
                                (default=1)

        :type visibility_timeout: int
        :param visibility_timeout: The number of seconds the message should
            remain invisible to other queue readers
            (default=None which uses the Queues default)

        :type attributes: str
        :param attributes: The name of additional attribute to return
            with response or All if you want all attributes.  The
            default is to return no additional attributes.  Valid
            values:
            * All
            * SenderId
            * SentTimestamp
            * ApproximateReceiveCount
            * ApproximateFirstReceiveTimestamp

        :type wait_time_seconds: int
        :param wait_time_seconds: The duration (in seconds) for which the call
            will wait for a message to arrive in the queue before returning.
            If a message is available, the call will return sooner than
            wait_time_seconds.

        :type message_attributes: list
        :param message_attributes: The name(s) of additional message
            attributes to return. The default is to return no additional
            message attributes. Use ``['All']`` or ``['.*']`` to return all.

        :rtype: list
        :return: A list of :class:`boto.sqs.message.Message` objects.

        """
        params = {'MaxNumberOfMessages' : number_messages}
        if visibility_timeout is not None:
            params['VisibilityTimeout'] = visibility_timeout
        if attributes is not None:
            self.build_list_params(params, attributes, 'AttributeName')
        if wait_time_seconds is not None:
            params['WaitTimeSeconds'] = wait_time_seconds
        if message_attributes is not None:
            self.build_list_params(params, message_attributes,
                                   'MessageAttributeName')
        return self.get_list('ReceiveMessage', params,
                             [('Message', queue.message_class)],
                             queue.id, queue)

    def delete_message(self, queue, message):
        """
        Delete a message from a queue.

        :type queue: A :class:`boto.sqs.queue.Queue` object
        :param queue: The Queue from which messages are read.

        :type message: A :class:`boto.sqs.message.Message` object
        :param message: The Message to be deleted

        :rtype: bool
        :return: True if successful, False otherwise.
        """
        params = {'ReceiptHandle' : message.receipt_handle}
        return self.get_status('DeleteMessage', params, queue.id)

    def delete_message_batch(self, queue, messages):
        """
        Deletes a list of messages from a queue in a single request.

        :type queue: A :class:`boto.sqs.queue.Queue` object.
        :param queue: The Queue to which the messages will be written.

        :type messages: List of :class:`boto.sqs.message.Message` objects.
        :param messages: A list of message objects.
        """
        params = {}
        for i, msg in enumerate(messages):
            prefix = 'DeleteMessageBatchRequestEntry'
            p_name = '%s.%i.Id' % (prefix, (i+1))
            params[p_name] = msg.id
            p_name = '%s.%i.ReceiptHandle' % (prefix, (i+1))
            params[p_name] = msg.receipt_handle
        return self.get_object('DeleteMessageBatch', params, BatchResults,
                               queue.id, verb='POST')

    def delete_message_from_handle(self, queue, receipt_handle):
        """
        Delete a message from a queue, given a receipt handle.

        :type queue: A :class:`boto.sqs.queue.Queue` object
        :param queue: The Queue from which messages are read.

        :type receipt_handle: str
        :param receipt_handle: The receipt handle for the message

        :rtype: bool
        :return: True if successful, False otherwise.
        """
        params = {'ReceiptHandle' : receipt_handle}
        return self.get_status('DeleteMessage', params, queue.id)

    def send_message(self, queue, message_content, delay_seconds=None,
                     message_attributes=None):
        """
        Send a new message to the queue.

        :type queue: A :class:`boto.sqs.queue.Queue` object.
        :param queue: The Queue to which the messages will be written.

        :type message_content: string
        :param message_content: The body of the message

        :type delay_seconds: int
        :param delay_seconds: Number of seconds (0 - 900) to delay this
            message from being processed.

        :type message_attributes: dict
        :param message_attributes: Message attributes to set. Should be
            of the form:

            {
                "name1": {
                    "data_type": "Number",
                    "string_value": "1"
                },
                "name2": {
                    "data_type": "String",
                    "string_value": "Bob"
                }
            }

        """
        params = {'MessageBody' : message_content}
        if delay_seconds:
            params['DelaySeconds'] = int(delay_seconds)

        if message_attributes is not None:
            keys = sorted(message_attributes.keys())
            for i, name in enumerate(keys, start=1):
                attribute = message_attributes[name]
                params['MessageAttribute.%s.Name' % i] = name
                if 'data_type' in attribute:
                    params['MessageAttribute.%s.Value.DataType' % i] = \
                        attribute['data_type']
                if 'string_value' in attribute:
                    params['MessageAttribute.%s.Value.StringValue' % i] = \
                        attribute['string_value']
                if 'binary_value' in attribute:
                    params['MessageAttribute.%s.Value.BinaryValue' % i] = \
                        attribute['binary_value']
                if 'string_list_value' in attribute:
                    params['MessageAttribute.%s.Value.StringListValue' % i] = \
                        attribute['string_list_value']
                if 'binary_list_value' in attribute:
                    params['MessageAttribute.%s.Value.BinaryListValue' % i] = \
                        attribute['binary_list_value']

        return self.get_object('SendMessage', params, Message,
                               queue.id, verb='POST')

    def send_message_batch(self, queue, messages):
        """
        Delivers up to 10 messages to a queue in a single request.

        :type queue: A :class:`boto.sqs.queue.Queue` object.
        :param queue: The Queue to which the messages will be written.

        :type messages: List of lists.
        :param messages: A list of lists or tuples.  Each inner
            tuple represents a single message to be written
            and consists of and ID (string) that must be unique
            within the list of messages, the message body itself
            which can be a maximum of 64K in length, an
            integer which represents the delay time (in seconds)
            for the message (0-900) before the message will
            be delivered to the queue, and an optional dict of
            message attributes like those passed to ``send_message``
            above.

        """
        params = {}
        for i, msg in enumerate(messages):
            base = 'SendMessageBatchRequestEntry.%i' % (i + 1)
            params['%s.Id' % base] = msg[0]
            params['%s.MessageBody' % base] = msg[1]
            params['%s.DelaySeconds' % base] = msg[2]
            if len(msg) > 3:
                base += '.MessageAttribute'
                keys = sorted(msg[3].keys())
                for j, name in enumerate(keys):
                    attribute = msg[3][name]

                    p_name = '%s.%i.Name' % (base, j + 1)
                    params[p_name] = name

                    if 'data_type' in attribute:
                        p_name = '%s.%i.Value.DataType' % (base, j + 1)
                        params[p_name] = attribute['data_type']
                    if 'string_value' in attribute:
                        p_name = '%s.%i.Value.StringValue' % (base, j + 1)
                        params[p_name] = attribute['string_value']
                    if 'binary_value' in attribute:
                        p_name = '%s.%i.Value.BinaryValue' % (base, j + 1)
                        params[p_name] = attribute['binary_value']
                    if 'string_list_value' in attribute:
                        p_name = '%s.%i.Value.StringListValue' % (base, j + 1)
                        params[p_name] = attribute['string_list_value']
                    if 'binary_list_value' in attribute:
                        p_name = '%s.%i.Value.BinaryListValue' % (base, j + 1)
                        params[p_name] = attribute['binary_list_value']

        return self.get_object('SendMessageBatch', params, BatchResults,
                               queue.id, verb='POST')

    def change_message_visibility(self, queue, receipt_handle,
                                  visibility_timeout):
        """
        Extends the read lock timeout for the specified message from
        the specified queue to the specified value.

        :type queue: A :class:`boto.sqs.queue.Queue` object
        :param queue: The Queue from which messages are read.

        :type receipt_handle: str
        :param receipt_handle: The receipt handle associated with the message
                               whose visibility timeout will be changed.

        :type visibility_timeout: int
        :param visibility_timeout: The new value of the message's visibility
                                   timeout in seconds.
        """
        params = {'ReceiptHandle' : receipt_handle,
                  'VisibilityTimeout' : visibility_timeout}
        return self.get_status('ChangeMessageVisibility', params, queue.id)

    def change_message_visibility_batch(self, queue, messages):
        """
        A batch version of change_message_visibility that can act
        on up to 10 messages at a time.

        :type queue: A :class:`boto.sqs.queue.Queue` object.
        :param queue: The Queue to which the messages will be written.

        :type messages: List of tuples.
        :param messages: A list of tuples where each tuple consists
            of a :class:`boto.sqs.message.Message` object and an integer
            that represents the new visibility timeout for that message.
        """
        params = {}
        for i, t in enumerate(messages):
            prefix = 'ChangeMessageVisibilityBatchRequestEntry'
            p_name = '%s.%i.Id' % (prefix, (i+1))
            params[p_name] = t[0].id
            p_name = '%s.%i.ReceiptHandle' % (prefix, (i+1))
            params[p_name] = t[0].receipt_handle
            p_name = '%s.%i.VisibilityTimeout' % (prefix, (i+1))
            params[p_name] = t[1]
        return self.get_object('ChangeMessageVisibilityBatch',
                               params, BatchResults,
                               queue.id, verb='POST')

    def get_all_queues(self, prefix=''):
        """
        Retrieves all queues.

        :keyword str prefix: Optionally, only return queues that start with
            this value.
        :rtype: list
        :returns: A list of :py:class:`boto.sqs.queue.Queue` instances.
        """
        params = {}
        if prefix:
            params['QueueNamePrefix'] = prefix
        return self.get_list('ListQueues', params, [('QueueUrl', Queue)])

    def get_queue(self, queue_name, owner_acct_id=None):
        """
        Retrieves the queue with the given name, or ``None`` if no match
        was found.

        :param str queue_name: The name of the queue to retrieve.
        :param str owner_acct_id: Optionally, the AWS account ID of the account that created the queue.
        :rtype: :py:class:`boto.sqs.queue.Queue` or ``None``
        :returns: The requested queue, or ``None`` if no match was found.
        """
        params = {'QueueName': queue_name}
        if owner_acct_id:
            params['QueueOwnerAWSAccountId']=owner_acct_id
        try:
            return self.get_object('GetQueueUrl', params, Queue)
        except SQSError:
            return None

    lookup = get_queue

    def get_dead_letter_source_queues(self, queue):
        """
        Retrieves the dead letter source queues for a given queue.

        :type queue: A :class:`boto.sqs.queue.Queue` object.
        :param queue: The queue for which to get DL source queues
        :rtype: list
        :returns: A list of :py:class:`boto.sqs.queue.Queue` instances.
        """
        params = {'QueueUrl': queue.url}
        return self.get_list('ListDeadLetterSourceQueues', params,
                             [('QueueUrl', Queue)])

    #
    # Permissions methods
    #

    def add_permission(self, queue, label, aws_account_id, action_name):
        """
        Add a permission to a queue.

        :type queue: :class:`boto.sqs.queue.Queue`
        :param queue: The queue object

        :type label: str or unicode
        :param label: A unique identification of the permission you are setting.
            Maximum of 80 characters ``[0-9a-zA-Z_-]``
            Example, AliceSendMessage

        :type aws_account_id: str or unicode
        :param principal_id: The AWS account number of the principal
            who will be given permission.  The principal must have an
            AWS account, but does not need to be signed up for Amazon
            SQS. For information about locating the AWS account
            identification.

        :type action_name: str or unicode
        :param action_name: The action.  Valid choices are:
            * *
            * SendMessage
            * ReceiveMessage
            * DeleteMessage
            * ChangeMessageVisibility
            * GetQueueAttributes

        :rtype: bool
        :return: True if successful, False otherwise.

        """
        params = {'Label': label,
                  'AWSAccountId' : aws_account_id,
                  'ActionName' : action_name}
        return self.get_status('AddPermission', params, queue.id)

    def remove_permission(self, queue, label):
        """
        Remove a permission from a queue.

        :type queue: :class:`boto.sqs.queue.Queue`
        :param queue: The queue object

        :type label: str or unicode
        :param label: The unique label associated with the permission
                      being removed.

        :rtype: bool
        :return: True if successful, False otherwise.
        """
        params = {'Label': label}
        return self.get_status('RemovePermission', params, queue.id)
