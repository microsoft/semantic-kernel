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
from tests.unit import unittest
from tests.unit import AWSMockServiceTestCase

from boto.jsonresponse import ListElement
from boto.ses.connection import SESConnection


class TestSESIdentity(AWSMockServiceTestCase):
    connection_class = SESConnection

    def setUp(self):
        super(TestSESIdentity, self).setUp()

    def default_body(self):
        return b"""<GetIdentityDkimAttributesResponse \
xmlns="http://ses.amazonaws.com/doc/2010-12-01/">
  <GetIdentityDkimAttributesResult>
    <DkimAttributes>
      <entry>
        <key>test@amazon.com</key>
      <value>
        <DkimEnabled>true</DkimEnabled>
        <DkimVerificationStatus>Success</DkimVerificationStatus>
        <DkimTokens>
          <member>vvjuipp74whm76gqoni7qmwwn4w4qusjiainivf6f</member>
          <member>3frqe7jn4obpuxjpwpolz6ipb3k5nvt2nhjpik2oy</member>
          <member>wrqplteh7oodxnad7hsl4mixg2uavzneazxv5sxi2</member>
        </DkimTokens>
      </value>
    </entry>
    <entry>
      <key>secondtest@amazon.com</key>
        <value>
          <DkimEnabled>false</DkimEnabled>
          <DkimVerificationStatus>NotStarted</DkimVerificationStatus>
        </value>
      </entry>
    </DkimAttributes>
  </GetIdentityDkimAttributesResult>
  <ResponseMetadata>
    <RequestId>bb5a105d-c468-11e1-82eb-dff885ccc06a</RequestId>
  </ResponseMetadata>
</GetIdentityDkimAttributesResponse>"""

    def test_ses_get_identity_dkim_list(self):
        self.set_http_response(status_code=200)

        response = self.service_connection\
                       .get_identity_dkim_attributes(['test@amazon.com', 'secondtest@amazon.com'])

        response = response['GetIdentityDkimAttributesResponse']
        result = response['GetIdentityDkimAttributesResult']

        first_entry = result['DkimAttributes'][0]
        entry_key = first_entry['key']
        attributes = first_entry['value']
        tokens = attributes['DkimTokens']

        self.assertEqual(entry_key, 'test@amazon.com')
        self.assertEqual(ListElement, type(tokens))
        self.assertEqual(3, len(tokens))
        self.assertEqual('vvjuipp74whm76gqoni7qmwwn4w4qusjiainivf6f',
                         tokens[0])
        self.assertEqual('3frqe7jn4obpuxjpwpolz6ipb3k5nvt2nhjpik2oy',
                         tokens[1])
        self.assertEqual('wrqplteh7oodxnad7hsl4mixg2uavzneazxv5sxi2',
                         tokens[2])

        second_entry = result['DkimAttributes'][1]
        entry_key = second_entry['key']
        attributes = second_entry['value']
        dkim_enabled = attributes['DkimEnabled']
        dkim_verification_status = attributes['DkimVerificationStatus']

        self.assertEqual(entry_key, 'secondtest@amazon.com')
        self.assertEqual(dkim_enabled, 'false')
        self.assertEqual(dkim_verification_status, 'NotStarted')


class TestSESSetIdentityNotificationTopic(AWSMockServiceTestCase):
    connection_class = SESConnection

    def setUp(self):
        super(TestSESSetIdentityNotificationTopic, self).setUp()

    def default_body(self):
        return b"""<SetIdentityNotificationTopicResponse \
        xmlns="http://ses.amazonaws.com/doc/2010-12-01/">
           <SetIdentityNotificationTopicResult/>
           <ResponseMetadata>
             <RequestId>299f4af4-b72a-11e1-901f-1fbd90e8104f</RequestId>
           </ResponseMetadata>
         </SetIdentityNotificationTopicResponse>"""

    def test_ses_set_identity_notification_topic_bounce(self):
        self.set_http_response(status_code=200)

        response = self.service_connection\
                       .set_identity_notification_topic(
                        identity='user@example.com',
                        notification_type='Bounce',
                        sns_topic='arn:aws:sns:us-east-1:123456789012:example')

        response = response['SetIdentityNotificationTopicResponse']
        result = response['SetIdentityNotificationTopicResult']

        self.assertEqual(2, len(response))
        self.assertEqual(0, len(result))

    def test_ses_set_identity_notification_topic_complaint(self):
        self.set_http_response(status_code=200)

        response = self.service_connection\
                       .set_identity_notification_topic(
                        identity='user@example.com',
                        notification_type='Complaint',
                        sns_topic='arn:aws:sns:us-east-1:123456789012:example')

        response = response['SetIdentityNotificationTopicResponse']
        result = response['SetIdentityNotificationTopicResult']

        self.assertEqual(2, len(response))
        self.assertEqual(0, len(result))


class TestSESSetIdentityFeedbackForwardingEnabled(AWSMockServiceTestCase):
    connection_class = SESConnection

    def setUp(self):
        super(TestSESSetIdentityFeedbackForwardingEnabled, self).setUp()

    def default_body(self):
        return b"""<SetIdentityFeedbackForwardingEnabledResponse \
        xmlns="http://ses.amazonaws.com/doc/2010-12-01/">
          <SetIdentityFeedbackForwardingEnabledResult/>
          <ResponseMetadata>
            <RequestId>299f4af4-b72a-11e1-901f-1fbd90e8104f</RequestId>
          </ResponseMetadata>
        </SetIdentityFeedbackForwardingEnabledResponse>"""

    def test_ses_set_identity_feedback_forwarding_enabled_true(self):
        self.set_http_response(status_code=200)

        response = self.service_connection\
                       .set_identity_feedback_forwarding_enabled(
                            identity='user@example.com',
                            forwarding_enabled=True)

        response = response['SetIdentityFeedbackForwardingEnabledResponse']
        result = response['SetIdentityFeedbackForwardingEnabledResult']

        self.assertEqual(2, len(response))
        self.assertEqual(0, len(result))

    def test_ses_set_identity_notification_topic_enabled_false(self):
        self.set_http_response(status_code=200)

        response = self.service_connection\
                       .set_identity_feedback_forwarding_enabled(
                            identity='user@example.com',
                            forwarding_enabled=False)

        response = response['SetIdentityFeedbackForwardingEnabledResponse']
        result = response['SetIdentityFeedbackForwardingEnabledResult']

        self.assertEqual(2, len(response))
        self.assertEqual(0, len(result))


if __name__ == '__main__':
    unittest.main()
