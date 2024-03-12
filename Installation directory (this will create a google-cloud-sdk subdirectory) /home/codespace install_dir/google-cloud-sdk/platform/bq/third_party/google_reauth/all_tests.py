#!/usr/bin/env python
"""Run all the test for google_reauth."""

import unittest

from google_reauth.tests.test_challenges import ChallengesTest
from google_reauth.tests.test_reauth import ReauthTest
from google_reauth.tests.test_reauth_creds import ReauthCredsTest

if __name__ == '__main__':
  unittest.main(verbosity=2)
