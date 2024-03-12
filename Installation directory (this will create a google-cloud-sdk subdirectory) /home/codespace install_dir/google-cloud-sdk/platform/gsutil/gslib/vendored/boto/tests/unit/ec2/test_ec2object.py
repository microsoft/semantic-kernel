#!/usr/bin/env python

from tests.unit import unittest
from tests.unit import AWSMockServiceTestCase

from boto.ec2.connection import EC2Connection
from boto.ec2.ec2object import TaggedEC2Object


CREATE_TAGS_RESPONSE = br"""<?xml version="1.0" encoding="UTF-8"?>
<CreateTagsResponse xmlns="http://ec2.amazonaws.com/doc/2014-05-01/">
  <requestId>7a62c49f-347e-4fc4-9331-6e8eEXAMPLE</requestId>
  <return>true</return>
</CreateTagsResponse>
"""


DELETE_TAGS_RESPONSE = br"""<?xml version="1.0" encoding="UTF-8"?>
<DeleteTagsResponse xmlns="http://ec2.amazonaws.com/doc/2014-05-01/">
   <requestId>7a62c49f-347e-4fc4-9331-6e8eEXAMPLE</requestId>
   <return>true</return>
</DeleteTagsResponse>
"""


class TestAddTags(AWSMockServiceTestCase):
    connection_class = EC2Connection

    def default_body(self):
        return CREATE_TAGS_RESPONSE

    def test_add_tag(self):
        self.set_http_response(status_code=200)
        taggedEC2Object = TaggedEC2Object(self.service_connection)
        taggedEC2Object.id = "i-abcd1234"
        taggedEC2Object.tags["already_present_key"] = "already_present_value"

        taggedEC2Object.add_tag("new_key", "new_value")

        self.assert_request_parameters({
            'ResourceId.1': 'i-abcd1234',
            'Action': 'CreateTags',
            'Tag.1.Key': 'new_key',
            'Tag.1.Value': 'new_value'},
            ignore_params_values=['AWSAccessKeyId', 'SignatureMethod',
                                  'SignatureVersion', 'Timestamp',
                                  'Version'])

        self.assertEqual(taggedEC2Object.tags, {
            "already_present_key": "already_present_value",
            "new_key": "new_value"})

    def test_add_tags(self):
        self.set_http_response(status_code=200)
        taggedEC2Object = TaggedEC2Object(self.service_connection)
        taggedEC2Object.id = "i-abcd1234"
        taggedEC2Object.tags["already_present_key"] = "already_present_value"

        taggedEC2Object.add_tags({"key1": "value1", "key2": "value2"})

        self.assert_request_parameters({
            'ResourceId.1': 'i-abcd1234',
            'Action': 'CreateTags',
            'Tag.1.Key': 'key1',
            'Tag.1.Value': 'value1',
            'Tag.2.Key': 'key2',
            'Tag.2.Value': 'value2'},
            ignore_params_values=['AWSAccessKeyId', 'SignatureMethod',
                                  'SignatureVersion', 'Timestamp',
                                  'Version'])

        self.assertEqual(taggedEC2Object.tags, {
            "already_present_key": "already_present_value",
            "key1": "value1",
            "key2": "value2"})


class TestRemoveTags(AWSMockServiceTestCase):
    connection_class = EC2Connection

    def default_body(self):
        return DELETE_TAGS_RESPONSE

    def test_remove_tag(self):
        self.set_http_response(status_code=200)
        taggedEC2Object = TaggedEC2Object(self.service_connection)
        taggedEC2Object.id = "i-abcd1234"
        taggedEC2Object.tags["key1"] = "value1"
        taggedEC2Object.tags["key2"] = "value2"

        taggedEC2Object.remove_tag("key1", "value1")

        self.assert_request_parameters({
            'ResourceId.1': 'i-abcd1234',
            'Action': 'DeleteTags',
            'Tag.1.Key': 'key1',
            'Tag.1.Value': 'value1'},
            ignore_params_values=['AWSAccessKeyId', 'SignatureMethod',
                                  'SignatureVersion', 'Timestamp',
                                  'Version'])

        self.assertEqual(taggedEC2Object.tags, {"key2": "value2"})

    def test_remove_tag_no_value(self):
        self.set_http_response(status_code=200)
        taggedEC2Object = TaggedEC2Object(self.service_connection)
        taggedEC2Object.id = "i-abcd1234"
        taggedEC2Object.tags["key1"] = "value1"
        taggedEC2Object.tags["key2"] = "value2"

        taggedEC2Object.remove_tag("key1")

        self.assert_request_parameters({
            'ResourceId.1': 'i-abcd1234',
            'Action': 'DeleteTags',
            'Tag.1.Key': 'key1'},
            ignore_params_values=['AWSAccessKeyId', 'SignatureMethod',
                                  'SignatureVersion', 'Timestamp',
                                  'Version'])

        self.assertEqual(taggedEC2Object.tags, {"key2": "value2"})

    def test_remove_tag_empty_value(self):
        self.set_http_response(status_code=200)
        taggedEC2Object = TaggedEC2Object(self.service_connection)
        taggedEC2Object.id = "i-abcd1234"
        taggedEC2Object.tags["key1"] = "value1"
        taggedEC2Object.tags["key2"] = "value2"

        taggedEC2Object.remove_tag("key1", "")

        self.assert_request_parameters({
            'ResourceId.1': 'i-abcd1234',
            'Action': 'DeleteTags',
            'Tag.1.Key': 'key1',
            'Tag.1.Value': ''},
            ignore_params_values=['AWSAccessKeyId', 'SignatureMethod',
                                  'SignatureVersion', 'Timestamp',
                                  'Version'])

        self.assertEqual(taggedEC2Object.tags,
                         {"key1": "value1", "key2": "value2"})

    def test_remove_tags(self):
        self.set_http_response(status_code=200)
        taggedEC2Object = TaggedEC2Object(self.service_connection)
        taggedEC2Object.id = "i-abcd1234"
        taggedEC2Object.tags["key1"] = "value1"
        taggedEC2Object.tags["key2"] = "value2"

        taggedEC2Object.remove_tags({"key1": "value1", "key2": "value2"})

        self.assert_request_parameters({
            'ResourceId.1': 'i-abcd1234',
            'Action': 'DeleteTags',
            'Tag.1.Key': 'key1',
            'Tag.1.Value': 'value1',
            'Tag.2.Key': 'key2',
            'Tag.2.Value': 'value2'},
            ignore_params_values=['AWSAccessKeyId', 'SignatureMethod',
                                  'SignatureVersion', 'Timestamp',
                                  'Version'])

        self.assertEqual(taggedEC2Object.tags, {})

    def test_remove_tags_wrong_values(self):
        self.set_http_response(status_code=200)
        taggedEC2Object = TaggedEC2Object(self.service_connection)
        taggedEC2Object.id = "i-abcd1234"
        taggedEC2Object.tags["key1"] = "value1"
        taggedEC2Object.tags["key2"] = "value2"

        taggedEC2Object.remove_tags({"key1": "value1", "key2": "value3"})

        self.assert_request_parameters({
            'ResourceId.1': 'i-abcd1234',
            'Action': 'DeleteTags',
            'Tag.1.Key': 'key1',
            'Tag.1.Value': 'value1',
            'Tag.2.Key': 'key2',
            'Tag.2.Value': 'value3'},
            ignore_params_values=['AWSAccessKeyId', 'SignatureMethod',
                                  'SignatureVersion', 'Timestamp',
                                  'Version'])

        self.assertEqual(taggedEC2Object.tags, {"key2": "value2"})

    def test_remove_tags_none_values(self):
        self.set_http_response(status_code=200)
        taggedEC2Object = TaggedEC2Object(self.service_connection)
        taggedEC2Object.id = "i-abcd1234"
        taggedEC2Object.tags["key1"] = "value1"
        taggedEC2Object.tags["key2"] = "value2"

        taggedEC2Object.remove_tags({"key1": "value1", "key2": None})

        self.assert_request_parameters({
            'ResourceId.1': 'i-abcd1234',
            'Action': 'DeleteTags',
            'Tag.1.Key': 'key1',
            'Tag.1.Value': 'value1',
            'Tag.2.Key': 'key2'},
            ignore_params_values=['AWSAccessKeyId', 'SignatureMethod',
                                  'SignatureVersion', 'Timestamp',
                                  'Version'])

        self.assertEqual(taggedEC2Object.tags, {})


if __name__ == '__main__':
    unittest.main()
