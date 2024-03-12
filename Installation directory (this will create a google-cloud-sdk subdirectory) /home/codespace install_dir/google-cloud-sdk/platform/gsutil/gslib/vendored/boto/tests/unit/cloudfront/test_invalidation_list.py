#!/usr/bin/env python
import random
import string
from tests.compat import unittest, mock

import boto


RESPONSE_TEMPLATE = r"""
<InvalidationList>
   <Marker/>
   <NextMarker>%(next_marker)s</NextMarker>
   <MaxItems>%(max_items)s</MaxItems>
   <IsTruncated>%(is_truncated)s</IsTruncated>
   %(inval_summaries)s
</InvalidationList>
"""

INVAL_SUMMARY_TEMPLATE = r"""
   <InvalidationSummary>
      <Id>%(cfid)s</Id>
      <Status>%(status)s</Status>
   </InvalidationSummary>
"""


class CFInvalidationListTest(unittest.TestCase):

    cloudfront = True

    def setUp(self):
        self.cf = boto.connect_cloudfront('aws.aws_access_key_id',
                                          'aws.aws_secret_access_key')

    def _get_random_id(self, length=14):
        return ''.join([random.choice(string.ascii_letters) for i in
                        range(length)])

    def _group_iter(self, iterator, n):
        accumulator = []
        for item in iterator:
            accumulator.append(item)
            if len(accumulator) == n:
                yield accumulator
                accumulator = []
        if len(accumulator) != 0:
            yield accumulator

    def _get_mock_responses(self, num, max_items):
        max_items = min(max_items, 100)
        cfid_groups = list(self._group_iter([self._get_random_id() for i in
                                             range(num)], max_items))
        cfg = dict(status='Completed', max_items=max_items, next_marker='')
        responses = []
        is_truncated = 'true'
        for i, group in enumerate(cfid_groups):
            next_marker = group[-1]
            if (i + 1) == len(cfid_groups):
                is_truncated = 'false'
                next_marker = ''
            invals = ''
            cfg.update(dict(next_marker=next_marker,
                            is_truncated=is_truncated))
            for cfid in group:
                cfg.update(dict(cfid=cfid))
                invals += INVAL_SUMMARY_TEMPLATE % cfg
            cfg.update(dict(inval_summaries=invals))
            mock_response = mock.Mock()
            mock_response.read.return_value = (RESPONSE_TEMPLATE % cfg).encode('utf-8')
            mock_response.status = 200
            responses.append(mock_response)
        return responses

    def test_manual_pagination(self, num_invals=30, max_items=4):
        """
        Test that paginating manually works properly
        """
        self.assertGreater(num_invals, max_items)
        responses = self._get_mock_responses(num=num_invals,
                                             max_items=max_items)
        self.cf.make_request = mock.Mock(side_effect=responses)
        ir = self.cf.get_invalidation_requests('dist-id-here',
                                               max_items=max_items)
        all_invals = list(ir)
        self.assertEqual(len(all_invals), max_items)
        while ir.is_truncated:
            ir = self.cf.get_invalidation_requests('dist-id-here',
                                                   marker=ir.next_marker,
                                                   max_items=max_items)
            invals = list(ir)
            self.assertLessEqual(len(invals), max_items)
            all_invals.extend(invals)
        remainder = num_invals % max_items
        if remainder != 0:
            self.assertEqual(len(invals), remainder)
        self.assertEqual(len(all_invals), num_invals)

    def test_auto_pagination(self, num_invals=1024):
        """
        Test that auto-pagination works properly
        """
        max_items = 100
        self.assertGreaterEqual(num_invals, max_items)
        responses = self._get_mock_responses(num=num_invals,
                                             max_items=max_items)
        self.cf.make_request = mock.Mock(side_effect=responses)
        ir = self.cf.get_invalidation_requests('dist-id-here')
        self.assertEqual(len(ir._inval_cache), max_items)
        self.assertEqual(len(list(ir)), num_invals)

if __name__ == '__main__':
    unittest.main()
