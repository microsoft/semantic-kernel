import unittest

from boto.sts.credentials import Credentials


class STSCredentialsTest(unittest.TestCase):
    sts = True

    def setUp(self):
        super(STSCredentialsTest, self).setUp()
        self.creds = Credentials()

    def test_to_dict(self):
        # This would fail miserably if ``Credentials.request_id`` hadn't been
        # explicitly set (no default).
        # Default.
        self.assertEqual(self.creds.to_dict(), {
            'access_key': None,
            'expiration': None,
            'request_id': None,
            'secret_key': None,
            'session_token': None
        })

        # Override.
        creds = Credentials()
        creds.access_key = 'something'
        creds.secret_key = 'crypto'
        creds.session_token = 'this'
        creds.expiration = 'way'
        creds.request_id = 'comes'
        self.assertEqual(creds.to_dict(), {
            'access_key': 'something',
            'expiration': 'way',
            'request_id': 'comes',
            'secret_key': 'crypto',
            'session_token': 'this'
        })
