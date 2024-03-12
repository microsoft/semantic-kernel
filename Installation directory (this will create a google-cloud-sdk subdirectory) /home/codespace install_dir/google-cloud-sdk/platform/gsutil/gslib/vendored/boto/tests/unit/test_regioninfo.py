# Copyright (c) 2014 Amazon.com, Inc. or its affiliates.  All Rights Reserved
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
import os
import mock

import boto
from boto.pyami.config import Config
from boto.regioninfo import RegionInfo, load_endpoint_json, merge_endpoints
from boto.regioninfo import load_regions, get_regions, connect

from tests.unit import unittest


class TestRegionInfo(object):
    def __init__(self, connection=None, name=None, endpoint=None,
                 connection_cls=None):
        self.connection = connection
        self.name = name
        self.endpoint = endpoint
        self.connection_cls = connection_cls

    def connect(self, **kwargs):
        return self.connection_cls(region=self)


class FakeConn(object):
    def __init__(self, region, **kwargs):
        self.region = region
        self.kwargs = kwargs


class TestEndpointLoading(unittest.TestCase):
    def setUp(self):
        super(TestEndpointLoading, self).setUp()

    def test_load_endpoint_json(self):
        endpoints = load_endpoint_json(boto.ENDPOINTS_PATH)
        self.assertTrue('partitions' in endpoints)

    def test_merge_endpoints(self):
        defaults = {
            'ec2': {
                'us-east-1': 'ec2.us-east-1.amazonaws.com',
                'us-west-1': 'ec2.us-west-1.amazonaws.com',
            }
        }
        additions = {
            # Top-level addition.
            's3': {
                'us-east-1': 's3.amazonaws.com'
            },
            'ec2': {
                # Overwrite. This doesn't exist, just test data.
                'us-east-1': 'ec2.auto-resolve.amazonaws.com',
                # Deep addition.
                'us-west-2': 'ec2.us-west-2.amazonaws.com',
            }
        }

        endpoints = merge_endpoints(defaults, additions)
        self.assertEqual(endpoints, {
            'ec2': {
                'us-east-1': 'ec2.auto-resolve.amazonaws.com',
                'us-west-1': 'ec2.us-west-1.amazonaws.com',
                'us-west-2': 'ec2.us-west-2.amazonaws.com',
            },
            's3': {
                'us-east-1': 's3.amazonaws.com'
            }
        })

    def test_load_regions(self):
        # Just the defaults.
        endpoints = load_regions()
        self.assertTrue('us-east-1' in endpoints['ec2'])
        self.assertFalse('test-1' in endpoints['ec2'])

        # With ENV overrides.
        os.environ['BOTO_ENDPOINTS'] = os.path.join(
            os.path.dirname(__file__),
            'test_endpoints.json'
        )
        self.addCleanup(os.environ.pop, 'BOTO_ENDPOINTS')
        endpoints = load_regions()
        self.assertTrue('us-east-1' in endpoints['ec2'])
        self.assertTrue('test-1' in endpoints['ec2'])
        self.assertEqual(endpoints['ec2']['test-1'], 'ec2.test-1.amazonaws.com')

    def test_get_regions(self):
        # With defaults.
        ec2_regions = get_regions('ec2')
        self.assertTrue(len(ec2_regions) >= 10)
        west_2 = None

        for region_info in ec2_regions:
            if region_info.name == 'us-west-2':
                west_2 = region_info
                break

        self.assertNotEqual(west_2, None, "Couldn't find the us-west-2 region!")
        self.assertTrue(isinstance(west_2, RegionInfo))
        self.assertEqual(west_2.name, 'us-west-2')
        self.assertEqual(west_2.endpoint, 'ec2.us-west-2.amazonaws.com')
        self.assertEqual(west_2.connection_cls, None)

    def test_get_regions_overrides(self):
        ec2_regions = get_regions(
            'ec2',
            region_cls=TestRegionInfo,
            connection_cls=FakeConn
        )
        self.assertTrue(len(ec2_regions) >= 10)
        west_2 = None

        for region_info in ec2_regions:
            if region_info.name == 'us-west-2':
                west_2 = region_info
                break

        self.assertNotEqual(west_2, None, "Couldn't find the us-west-2 region!")
        self.assertFalse(isinstance(west_2, RegionInfo))
        self.assertTrue(isinstance(west_2, TestRegionInfo))
        self.assertEqual(west_2.name, 'us-west-2')
        self.assertEqual(west_2.endpoint, 'ec2.us-west-2.amazonaws.com')
        self.assertEqual(west_2.connection_cls, FakeConn)


class TestConnectToRegion(unittest.TestCase):
    def test_connect(self):
        connection = connect(
            'ec2', 'us-west-2', connection_cls=FakeConn)
        self.assertEqual(connection.region.name, 'us-west-2')
        expected_endpoint = 'ec2.us-west-2.amazonaws.com'
        self.assertEqual(connection.region.endpoint, expected_endpoint)

    def test_does_not_use_heuristics_by_default(self):
        connection = connect(
            'ec2', 'us-southeast-43', connection_cls=FakeConn)
        self.assertIsNone(connection)

    def test_uses_region_override(self):
        connection = connect(
            'ec2', 'us-west-2', connection_cls=FakeConn,
            region_cls=TestRegionInfo
        )
        self.assertIsInstance(connection.region, TestRegionInfo)
        self.assertEqual(connection.region.name, 'us-west-2')
        expected_endpoint = 'ec2.us-west-2.amazonaws.com'
        self.assertEqual(connection.region.endpoint, expected_endpoint)

    def test_use_heuristics_via_env_var(self):
        # With ENV overrides.
        os.environ['BOTO_USE_ENDPOINT_HEURISTICS'] = 'True'
        self.addCleanup(os.environ.pop, 'BOTO_USE_ENDPOINT_HEURISTICS')
        connection = connect(
            'ec2', 'us-southeast-43', connection_cls=FakeConn,
            region_cls=TestRegionInfo)
        self.assertIsNotNone(connection)
        self.assertEqual(connection.region.name, 'us-southeast-43')
        expected_endpoint = 'ec2.us-southeast-43.amazonaws.com'
        self.assertEqual(connection.region.endpoint, expected_endpoint)

    def test_use_heuristics_via_config(self):
        config = mock.Mock(spec=Config)

        def _getbool(section, name, default=False):
            if section == 'Boto' and name == 'use_endpoint_heuristics':
                return True
            return default

        config.getbool = _getbool
        config.get.return_value = None

        with mock.patch('boto.config', config):
            connection = connect(
                'ec2', 'us-southeast-43', connection_cls=FakeConn,
                region_cls=TestRegionInfo)

        self.assertIsNotNone(connection)
        self.assertEqual(connection.region.name, 'us-southeast-43')
        expected_endpoint = 'ec2.us-southeast-43.amazonaws.com'
        self.assertEqual(connection.region.endpoint, expected_endpoint)

    def test_connect_with_hueristics_without_explicit_regioninfo(self):
        os.environ['BOTO_USE_ENDPOINT_HEURISTICS'] = 'True'
        self.addCleanup(os.environ.pop, 'BOTO_USE_ENDPOINT_HEURISTICS')
        connection = connect(
            'ec2', 'us-southeast-43', connection_cls=FakeConn)
        self.assertIsNotNone(connection)
        self.assertIsInstance(connection.region, RegionInfo)
        self.assertEqual(connection.region.name, 'us-southeast-43')
        expected_endpoint = 'ec2.us-southeast-43.amazonaws.com'
        self.assertEqual(connection.region.endpoint, expected_endpoint)


if __name__ == '__main__':
    unittest.main()
