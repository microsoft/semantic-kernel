from tests.unit import unittest

from boto.ses.connection import SESConnection
from boto.ses import exceptions


class SESConnectionTest(unittest.TestCase):
    ses = True

    def setUp(self):
        self.ses = SESConnection()

    def test_get_dkim_attributes(self):
        response = self.ses.get_identity_dkim_attributes(['example.com'])
        # Verify we get the structure we expect, we don't care about the
        # values.
        self.assertTrue('GetIdentityDkimAttributesResponse' in response)
        self.assertTrue('GetIdentityDkimAttributesResult' in
                        response['GetIdentityDkimAttributesResponse'])
        self.assertTrue(
            'DkimAttributes' in response['GetIdentityDkimAttributesResponse']
                                        ['GetIdentityDkimAttributesResult'])

    def test_set_identity_dkim_enabled(self):
        # This api call should fail because have not verified the domain,
        # so we can test that it at least fails we we expect.
        with self.assertRaises(exceptions.SESIdentityNotVerifiedError):
            self.ses.set_identity_dkim_enabled('example.com', True)

    def test_verify_domain_dkim(self):
        # This api call should fail because have not confirmed the domain,
        # so we can test that it at least fails we we expect.
        with self.assertRaises(exceptions.SESDomainNotConfirmedError):
            self.ses.verify_domain_dkim('example.com')


if __name__ == '__main__':
    unittest.main()
