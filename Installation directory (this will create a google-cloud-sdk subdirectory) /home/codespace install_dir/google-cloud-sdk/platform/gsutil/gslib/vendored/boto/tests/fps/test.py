#!/usr/bin/env python

from tests.unit import unittest
import sys
import os
import os.path

simple = True
advanced = False
if __name__ == "__main__":
    devpath = os.path.relpath(os.path.join('..', '..'),
                              start=os.path.dirname(__file__))
    sys.path = [devpath] + sys.path
    print '>>> advanced FPS tests; using local boto sources'
    advanced = True

from boto.fps.connection import FPSConnection
from boto.fps.response import ComplexAmount


class FPSTestCase(unittest.TestCase):

    def setUp(self):
        self.fps = FPSConnection(host='fps.sandbox.amazonaws.com')
        if advanced:
            self.activity = self.fps.get_account_activity(\
                                StartDate='2012-01-01')
            result = self.activity.GetAccountActivityResult
            self.transactions = result.Transaction

    @unittest.skipUnless(simple, "skipping simple test")
    def test_get_account_balance(self):
        response = self.fps.get_account_balance()
        self.assertTrue(hasattr(response, 'GetAccountBalanceResult'))
        self.assertTrue(hasattr(response.GetAccountBalanceResult,
                                                'AccountBalance'))
        accountbalance = response.GetAccountBalanceResult.AccountBalance
        self.assertTrue(hasattr(accountbalance, 'TotalBalance'))
        self.assertIsInstance(accountbalance.TotalBalance, ComplexAmount)
        self.assertTrue(hasattr(accountbalance, 'AvailableBalances'))
        availablebalances = accountbalance.AvailableBalances
        self.assertTrue(hasattr(availablebalances, 'RefundBalance'))

    @unittest.skipUnless(simple, "skipping simple test")
    def test_complex_amount(self):
        response = self.fps.get_account_balance()
        accountbalance = response.GetAccountBalanceResult.AccountBalance
        asfloat = float(accountbalance.TotalBalance.Value)
        self.assertIn('.', str(asfloat))

    @unittest.skipUnless(simple, "skipping simple test")
    def test_required_arguments(self):
        with self.assertRaises(KeyError):
            self.fps.write_off_debt(AdjustmentAmount=123.45)

    @unittest.skipUnless(simple, "skipping simple test")
    def test_cbui_url(self):
        inputs = {
            'transactionAmount':    123.45,
            'pipelineName':         'SingleUse',
            'returnURL':            'https://localhost/',
            'paymentReason':        'a reason for payment',
            'callerReference':      'foo',
        }
        result = self.fps.cbui_url(**inputs)
        print "cbui_url() yields {0}".format(result)

    @unittest.skipUnless(simple, "skipping simple test")
    def test_get_account_activity(self):
        response = self.fps.get_account_activity(StartDate='2012-01-01')
        self.assertTrue(hasattr(response, 'GetAccountActivityResult'))
        result = response.GetAccountActivityResult
        self.assertTrue(hasattr(result, 'BatchSize'))
        try:
            int(result.BatchSize)
        except:
            self.assertTrue(False)

    @unittest.skipUnless(advanced, "skipping advanced test")
    def test_get_transaction(self):
        assert len(self.transactions)
        transactionid = self.transactions[0].TransactionId
        result = self.fps.get_transaction(TransactionId=transactionid)
        self.assertTrue(hasattr(result.GetTransactionResult, 'Transaction'))

    @unittest.skip('cosmetic')
    def test_bad_request(self):
        try:
            self.fps.write_off_debt(CreditInstrumentId='foo',
                                    AdjustmentAmount=123.45)
        except Exception as e:
            print e

    @unittest.skip('cosmetic')
    def test_repr(self):
        print self.fps.get_account_balance()


if __name__ == "__main__":
    unittest.main()
