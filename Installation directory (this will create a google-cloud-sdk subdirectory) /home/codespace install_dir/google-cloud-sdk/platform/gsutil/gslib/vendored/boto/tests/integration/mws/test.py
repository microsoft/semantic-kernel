#!/usr/bin/env python
from __future__ import print_function
import sys
import os
import os.path
from datetime import datetime, timedelta


simple = os.environ.get('MWS_MERCHANT', None)
if not simple:
    print("""
        Please set the MWS_MERCHANT environmental variable
        to your Merchant or SellerId to enable MWS tests.
    """)


advanced = False
isolator = True
if __name__ == "__main__":
    devpath = os.path.relpath(os.path.join('..', '..', '..'),
                              start=os.path.dirname(__file__))
    sys.path = [devpath] + sys.path
    advanced = simple and True or False
    if advanced:
        print('>>> advanced MWS tests; using local boto sources')

from boto.mws.connection import MWSConnection
from tests.compat import unittest


class MWSTestCase(unittest.TestCase):

    def setUp(self):
        self.mws = MWSConnection(Merchant=simple, debug=0)

    @unittest.skipUnless(simple and isolator, "skipping simple test")
    def test_feedlist(self):
        self.mws.get_feed_submission_list()

    @unittest.skipUnless(simple and isolator, "skipping simple test")
    def test_inbound_status(self):
        response = self.mws.get_inbound_service_status()
        status = response.GetServiceStatusResult.Status
        self.assertIn(status, ('GREEN', 'GREEN_I', 'YELLOW', 'RED'))

    @property
    def marketplace(self):
        try:
            return self._marketplace
        except AttributeError:
            response = self.mws.list_marketplace_participations()
            result = response.ListMarketplaceParticipationsResult
            self._marketplace = result.ListMarketplaces.Marketplace[0]
            return self.marketplace

    @property
    def marketplace_id(self):
        return self.marketplace.MarketplaceId

    @unittest.skipUnless(simple and isolator, "skipping simple test")
    def test_marketplace_participations(self):
        response = self.mws.list_marketplace_participations()
        result = response.ListMarketplaceParticipationsResult
        self.assertTrue(result.ListMarketplaces.Marketplace[0].MarketplaceId)

    @unittest.skipUnless(simple and isolator, "skipping simple test")
    def test_get_product_categories_for_asin(self):
        asin = '144930544X'
        response = self.mws.get_product_categories_for_asin(
            MarketplaceId=self.marketplace_id,
            ASIN=asin)
        self.assertEqual(len(response._result.Self), 3)
        categoryids = [x.ProductCategoryId for x in response._result.Self]
        self.assertSequenceEqual(categoryids, ['285856', '21', '491314'])

    @unittest.skipUnless(simple and isolator, "skipping simple test")
    def test_list_matching_products(self):
        response = self.mws.list_matching_products(
            MarketplaceId=self.marketplace_id,
            Query='boto')
        products = response._result.Products
        self.assertTrue(len(products))

    @unittest.skipUnless(simple and isolator, "skipping simple test")
    def test_get_matching_product(self):
        asin = 'B001UDRNHO'
        response = self.mws.get_matching_product(
            MarketplaceId=self.marketplace_id,
            ASINList=[asin])
        attributes = response._result[0].Product.AttributeSets.ItemAttributes
        self.assertEqual(attributes[0].Label, 'Serengeti')

    @unittest.skipUnless(simple and isolator, "skipping simple test")
    def test_get_matching_product_for_id(self):
        asins = ['B001UDRNHO', '144930544X']
        response = self.mws.get_matching_product_for_id(
            MarketplaceId=self.marketplace_id,
            IdType='ASIN',
            IdList=asins)
        self.assertEqual(len(response._result), 2)
        for result in response._result:
            self.assertEqual(len(result.Products.Product), 1)

    @unittest.skipUnless(simple and isolator, "skipping simple test")
    def test_get_lowest_offer_listings_for_asin(self):
        asin = '144930544X'
        response = self.mws.get_lowest_offer_listings_for_asin(
            MarketplaceId=self.marketplace_id,
            ItemCondition='New',
            ASINList=[asin])
        listings = response._result[0].Product.LowestOfferListings
        self.assertTrue(len(listings.LowestOfferListing))

    @unittest.skipUnless(simple and isolator, "skipping simple test")
    def test_list_inventory_supply(self):
        asof = (datetime.today() - timedelta(days=30)).isoformat()
        response = self.mws.list_inventory_supply(QueryStartDateTime=asof,
                                                  ResponseGroup='Basic')
        self.assertTrue(hasattr(response._result, 'InventorySupplyList'))

if __name__ == "__main__":
    unittest.main()
