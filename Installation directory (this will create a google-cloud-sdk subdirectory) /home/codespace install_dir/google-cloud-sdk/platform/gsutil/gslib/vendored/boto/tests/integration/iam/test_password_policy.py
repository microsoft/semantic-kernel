# Copyright (c) 2014 Rocket Internet AG.
# Luca Bruno <luca.bruno@rocket-internet.de>
# All rights reserved.
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

import boto
import time

from tests.compat import unittest

class IAMAccountPasswordPolicy(unittest.TestCase):
    iam = True

    def test_password_policy(self):
        # A series of tests to check the password policy API
        iam = boto.connect_iam()

        # First preserve what is the current password policy
        try:
            initial_policy_result = iam.get_account_password_policy()
        except boto.exception.BotoServerError as srv_error:
            initial_policy = None
            if srv_error.status != 404:
                raise srv_error

        # Update the policy and check it back
        test_min_length = 88
        iam.update_account_password_policy(minimum_password_length=test_min_length)
        new_policy = iam.get_account_password_policy()
        new_min_length = new_policy['get_account_password_policy_response']\
                                        ['get_account_password_policy_result']['password_policy']\
                                        ['minimum_password_length']

        if test_min_length != int(new_min_length):
            raise Exception("Failed to update account password policy")

        # Delete the policy and check the correct deletion
        test_policy = ''
        iam.delete_account_password_policy()
        try:
            test_policy = iam.get_account_password_policy()
        except boto.exception.BotoServerError as srv_error:
            test_policy = None
            if srv_error.status != 404:
                raise srv_error

        if test_policy is not None:
            raise Exception("Failed to delete account password policy")

        # Restore initial account password policy
        if initial_policy:
            p = initial_policy['get_account_password_policy_response']\
                    ['get_account_password_policy_result']['password_policy']
            iam.update_account_password_policy(minimum_password_length=int(p['minimum_password_length']),
                                                allow_users_to_change_password=bool(p['allow_users_to_change_password']),
                                                hard_expiry=bool(p['hard_expiry']),
                                                max_password_age=int(p['max_password_age']),
                                                password_reuse_prevention=int(p['password_reuse_prevention']),
                                                require_lowercase_characters=bool(p['require_lowercase_characters']),
                                                require_numbers=bool(p['require_numbers']),
                                                require_symbols=bool(p['require_symbols']),
                                                require_uppercase_characters=bool(p['require_uppercase_characters']))
