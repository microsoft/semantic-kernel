#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2015 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Tests for util."""
import codecs
import gzip
import os
import six.moves.urllib.request as urllib_request
import tempfile
import unittest

from apitools.gen import util
from mock import patch


class NormalizeVersionTest(unittest.TestCase):

    def testVersions(self):
        already_valid = 'v1'
        self.assertEqual(already_valid, util.NormalizeVersion(already_valid))
        to_clean = 'v0.1'
        self.assertEqual('v0_1', util.NormalizeVersion(to_clean))


class NamesTest(unittest.TestCase):

    def testKeywords(self):
        names = util.Names([''])
        self.assertEqual('in_', names.CleanName('in'))

    def testNormalizeEnumName(self):
        names = util.Names([''])
        self.assertEqual('_0', names.NormalizeEnumName('0'))


class MockRequestResponse():
    """Mocks the behavior of urllib.response."""

    class MockRequestEncoding():
        def __init__(self, encoding):
            self.encoding = encoding

        def get(self, _):
            return self.encoding

    def __init__(self, content, encoding):
        self.content = content
        self.encoding = MockRequestResponse.MockRequestEncoding(encoding)

    def info(self):
        return self.encoding

    def read(self):
        return self.content


def _Gzip(raw_content):
    """Returns gzipped content from any content."""
    f = tempfile.NamedTemporaryFile(suffix='gz', mode='wb', delete=False)
    f.close()
    try:
        with gzip.open(f.name, 'wb') as h:
            h.write(raw_content)
        with open(f.name, 'rb') as h:
            return h.read()
    finally:
        os.unlink(f.name)


class GetURLContentTest(unittest.TestCase):

    def testUnspecifiedContentEncoding(self):
        data = 'regular non-gzipped content'
        with patch.object(urllib_request, 'urlopen',
                          return_value=MockRequestResponse(data, '')):
            self.assertEqual(data, util._GetURLContent('unused_url_parameter'))

    def testGZippedContent(self):
        data = u'¿Hola qué tal?'
        compressed_data = _Gzip(data.encode('utf-8'))
        with patch.object(urllib_request, 'urlopen',
                          return_value=MockRequestResponse(
                              compressed_data, 'gzip')):
            self.assertEqual(data, util._GetURLContent(
                'unused_url_parameter').decode('utf-8'))
