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

from tests.unit import unittest
from boto.ecs import ECSConnection
from tests.unit import AWSMockServiceTestCase


class TestECSConnection(AWSMockServiceTestCase):
    connection_class = ECSConnection

    def default_body(self):
        return b"""
            <Items>
              <Request>
              <IsValid>True</IsValid>
              <ItemLookupRequest>
                <ItemId>B00008OE6I</ItemId>
              </ItemLookupRequest>
              </Request>
              <Item>
                <ASIN>B00008OE6I</ASIN>
                <ItemAttributes>
                <Manufacturer>Canon</Manufacturer>
                <ProductGroup>Photography</ProductGroup>
                <Title>Canon PowerShot S400 4MP Digital Camera w/ 3x Optical Zoom</Title>
               </ItemAttributes>
              </Item>
            </Items>
        """

    def test_item_lookup(self):
        self.set_http_response(status_code=200)
        item_set = self.service_connection.item_lookup(
            ItemId='0316067938',
            ResponseGroup='Reviews'
        )

        self.assert_request_parameters(
            {'ItemId': '0316067938',
             'Operation': 'ItemLookup',
             'ResponseGroup': 'Reviews',
             'Service': 'AWSECommerceService'},
            ignore_params_values=['Version', 'AWSAccessKeyId',
                                  'SignatureMethod', 'SignatureVersion',
                                  'Timestamp'])

        items = list(item_set)
        self.assertEqual(len(items), 1)
        self.assertTrue(item_set.is_valid)
        self.assertEqual(items[0].ASIN, 'B00008OE6I')
