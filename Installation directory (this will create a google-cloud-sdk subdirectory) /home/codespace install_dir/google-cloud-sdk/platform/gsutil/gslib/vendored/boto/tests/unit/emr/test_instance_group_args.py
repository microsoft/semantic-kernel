#!/usr/bin/env python
# Author: Charlie Schluting <charlie@schluting.com>
#
# Test to ensure initalization of InstanceGroup object emits appropriate errors
# if bidprice is not specified, but allows float, int, Decimal.

from decimal import Decimal

from tests.compat import unittest
from boto.emr.instance_group import InstanceGroup


class TestInstanceGroupArgs(unittest.TestCase):

    def test_bidprice_missing_spot(self):
        """
        Test InstanceGroup init raises ValueError when market==spot and
        bidprice is not specified.
        """
        with self.assertRaisesRegexp(ValueError, 'bidprice must be specified'):
            InstanceGroup(1, 'MASTER', 'm1.small',
                          'SPOT', 'master')

    def test_bidprice_missing_ondemand(self):
        """
        Test InstanceGroup init accepts a missing bidprice arg, when market is
        ON_DEMAND.
        """
        instance_group = InstanceGroup(1, 'MASTER', 'm1.small',
                                       'ON_DEMAND', 'master')

    def test_bidprice_Decimal(self):
        """
        Test InstanceGroup init works with bidprice type = Decimal.
        """
        instance_group = InstanceGroup(1, 'MASTER', 'm1.small',
                                       'SPOT', 'master', bidprice=Decimal(1.10))
        self.assertEquals('1.10', instance_group.bidprice[:4])

    def test_bidprice_float(self):
        """
        Test InstanceGroup init works with bidprice type = float.
        """
        instance_group = InstanceGroup(1, 'MASTER', 'm1.small',
                                       'SPOT', 'master', bidprice=1.1)
        self.assertEquals('1.1', instance_group.bidprice)

    def test_bidprice_string(self):
        """
        Test InstanceGroup init works with bidprice type = string.
        """
        instance_group = InstanceGroup(1, 'MASTER', 'm1.small',
                                       'SPOT', 'master', bidprice='1.1')
        self.assertEquals('1.1', instance_group.bidprice)

if __name__ == "__main__":
    unittest.main()
