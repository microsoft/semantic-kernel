# Copyright (c) 2013 Amazon.com, Inc. or its affiliates.  All Rights Reserved
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
import unittest
import time

from boto.support.layer1 import SupportConnection
from boto.support import exceptions


class TestSupportLayer1Management(unittest.TestCase):
    support = True

    def setUp(self):
        self.api = SupportConnection()
        self.wait_time = 5

    def test_as_much_as_possible_before_teardown(self):
        cases = self.api.describe_cases()
        preexisting_count = len(cases.get('cases', []))

        services = self.api.describe_services()
        self.assertTrue('services' in services)
        service_codes = [serv['code'] for serv in services['services']]
        self.assertTrue('amazon-cloudsearch' in service_codes)

        severity = self.api.describe_severity_levels()
        self.assertTrue('severityLevels' in severity)
        severity_codes = [sev['code'] for sev in severity['severityLevels']]
        self.assertTrue('low' in severity_codes)

        case_1 = self.api.create_case(
            subject='TEST: I am a test case.',
            service_code='amazon-cloudsearch',
            category_code='other',
            communication_body="This is a test problem",
            severity_code='low',
            language='en'
        )
        time.sleep(self.wait_time)
        case_id = case_1['caseId']

        new_cases = self.api.describe_cases()
        self.assertTrue(len(new_cases['cases']) > preexisting_count)

        result = self.api.add_communication_to_case(
            communication_body="This is a test solution.",
            case_id=case_id
        )
        self.assertTrue(result.get('result', False))
        time.sleep(self.wait_time)

        final_cases = self.api.describe_cases(case_id_list=[case_id])
        comms = final_cases['cases'][0]['recentCommunications']\
                           ['communications']
        self.assertEqual(len(comms), 2)

        close_result = self.api.resolve_case(case_id=case_id)
