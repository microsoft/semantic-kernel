from tests.unit import unittest

from boto.exception import BotoServerError, S3CreateError, JSONResponseError

from httpretty import HTTPretty, httprettified


class TestBotoServerError(unittest.TestCase):

    def test_botoservererror_basics(self):
        bse = BotoServerError('400', 'Bad Request')
        self.assertEqual(bse.status, '400')
        self.assertEqual(bse.reason, 'Bad Request')

    def test_message_elb_xml(self):
        # This test XML response comes from #509
        xml = """
<ErrorResponse xmlns="http://elasticloadbalancing.amazonaws.com/doc/2011-11-15/">
  <Error>
    <Type>Sender</Type>
    <Code>LoadBalancerNotFound</Code>
    <Message>Cannot find Load Balancer webapp-balancer2</Message>
  </Error>
  <RequestId>093f80d0-4473-11e1-9234-edce8ec08e2d</RequestId>
</ErrorResponse>"""
        bse = BotoServerError('400', 'Bad Request', body=xml)

        self.assertEqual(bse.error_message, 'Cannot find Load Balancer webapp-balancer2')
        self.assertEqual(bse.error_message, bse.message)
        self.assertEqual(bse.request_id, '093f80d0-4473-11e1-9234-edce8ec08e2d')
        self.assertEqual(bse.error_code, 'LoadBalancerNotFound')
        self.assertEqual(bse.status, '400')
        self.assertEqual(bse.reason, 'Bad Request')

    def test_message_sd_xml(self):
        # Sample XML response from: https://forums.aws.amazon.com/thread.jspa?threadID=87393
        xml = """
<Response>
  <Errors>
    <Error>
      <Code>AuthorizationFailure</Code>
      <Message>Session does not have permission to perform (sdb:CreateDomain) on resource (arn:aws:sdb:us-east-1:xxxxxxx:domain/test_domain). Contact account owner.</Message>
      <BoxUsage>0.0055590278</BoxUsage>
    </Error>
  </Errors>
  <RequestID>e73bb2bb-63e3-9cdc-f220-6332de66dbbe</RequestID>
</Response>"""
        bse = BotoServerError('403', 'Forbidden', body=xml)
        self.assertEqual(
            bse.error_message,
            'Session does not have permission to perform (sdb:CreateDomain) on '
            'resource (arn:aws:sdb:us-east-1:xxxxxxx:domain/test_domain). '
            'Contact account owner.')
        self.assertEqual(bse.error_message, bse.message)
        self.assertEqual(bse.box_usage, '0.0055590278')
        self.assertEqual(bse.error_code, 'AuthorizationFailure')
        self.assertEqual(bse.status, '403')
        self.assertEqual(bse.reason, 'Forbidden')

    @httprettified
    def test_xmlns_not_loaded(self):
        xml = '<ErrorResponse xmlns="http://elasticloadbalancing.amazonaws.com/doc/2011-11-15/">'
        bse = BotoServerError('403', 'Forbidden', body=xml)
        self.assertEqual([], HTTPretty.latest_requests)

    @httprettified
    def test_xml_entity_not_loaded(self):
        xml = '<!DOCTYPE Message [<!ENTITY xxe SYSTEM "http://aws.amazon.com/">]><Message>error:&xxe;</Message>'
        bse = BotoServerError('403', 'Forbidden', body=xml)
        self.assertEqual([], HTTPretty.latest_requests)

    def test_message_storage_create_error(self):
        # This test value comes from https://answers.launchpad.net/duplicity/+question/150801
        xml = """<?xml version="1.0" encoding="UTF-8"?>
<Error>
  <Code>BucketAlreadyOwnedByYou</Code>
  <Message>Your previous request to create the named bucket succeeded and you already own it.</Message>
  <BucketName>cmsbk</BucketName>
  <RequestId>FF8B86A32CC3FE4F</RequestId>
  <HostId>6ENGL3DT9f0n7Tkv4qdKIs/uBNCMMA6QUFapw265WmodFDluP57esOOkecp55qhh</HostId>
</Error>
"""
        s3ce = S3CreateError('409', 'Conflict', body=xml)

        self.assertEqual(s3ce.bucket, 'cmsbk')
        self.assertEqual(s3ce.error_code, 'BucketAlreadyOwnedByYou')
        self.assertEqual(s3ce.status, '409')
        self.assertEqual(s3ce.reason, 'Conflict')
        self.assertEqual(
            s3ce.error_message,
            'Your previous request to create the named bucket succeeded '
            'and you already own it.')
        self.assertEqual(s3ce.error_message, s3ce.message)
        self.assertEqual(s3ce.request_id, 'FF8B86A32CC3FE4F')

    def test_message_json_response_error(self):
        # This test comes from https://forums.aws.amazon.com/thread.jspa?messageID=374936
        body = {
            '__type': 'com.amazon.coral.validate#ValidationException',
            'message': 'The attempted filter operation is not supported '
                       'for the provided filter argument count'}

        jre = JSONResponseError('400', 'Bad Request', body=body)

        self.assertEqual(jre.status, '400')
        self.assertEqual(jre.reason, 'Bad Request')
        self.assertEqual(jre.error_message, body['message'])
        self.assertEqual(jre.error_message, jre.message)
        self.assertEqual(jre.code, 'ValidationException')
        self.assertEqual(jre.code, jre.error_code)

    def test_message_not_xml(self):
        body = 'This is not XML'

        bse = BotoServerError('400', 'Bad Request', body=body)
        self.assertEqual(bse.error_message, 'This is not XML')

    def test_getters(self):
        body = "This is the body"

        bse = BotoServerError('400', 'Bad Request', body=body)
        self.assertEqual(bse.code, bse.error_code)
        self.assertEqual(bse.message, bse.error_message)
