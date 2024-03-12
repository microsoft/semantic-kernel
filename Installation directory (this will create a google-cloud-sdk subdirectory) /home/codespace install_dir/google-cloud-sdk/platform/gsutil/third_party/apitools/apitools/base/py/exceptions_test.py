# Copyright 2017 Google Inc.
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

import unittest

from apitools.base.py import exceptions
from apitools.base.py import http_wrapper


def _MakeResponse(status_code):
    return http_wrapper.Response(
        info={'status': status_code}, content='{"field": "abc"}',
        request_url='http://www.google.com')


class HttpErrorFromResponseTest(unittest.TestCase):

    """Tests for exceptions.HttpError.FromResponse."""

    def testBadRequest(self):
        err = exceptions.HttpError.FromResponse(_MakeResponse(400))
        self.assertIsInstance(err, exceptions.HttpError)
        self.assertIsInstance(err, exceptions.HttpBadRequestError)
        self.assertEquals(err.status_code, 400)

    def testUnauthorized(self):
        err = exceptions.HttpError.FromResponse(_MakeResponse(401))
        self.assertIsInstance(err, exceptions.HttpError)
        self.assertIsInstance(err, exceptions.HttpUnauthorizedError)
        self.assertEquals(err.status_code, 401)

    def testForbidden(self):
        err = exceptions.HttpError.FromResponse(_MakeResponse(403))
        self.assertIsInstance(err, exceptions.HttpError)
        self.assertIsInstance(err, exceptions.HttpForbiddenError)
        self.assertEquals(err.status_code, 403)

    def testExceptionMessageIncludesErrorDetails(self):
        err = exceptions.HttpError.FromResponse(_MakeResponse(403))
        self.assertIn('403', repr(err))
        self.assertIn('http://www.google.com', repr(err))
        self.assertIn('{"field": "abc"}', repr(err))

    def testNotFound(self):
        err = exceptions.HttpError.FromResponse(_MakeResponse(404))
        self.assertIsInstance(err, exceptions.HttpError)
        self.assertIsInstance(err, exceptions.HttpNotFoundError)
        self.assertEquals(err.status_code, 404)

    def testConflict(self):
        err = exceptions.HttpError.FromResponse(_MakeResponse(409))
        self.assertIsInstance(err, exceptions.HttpError)
        self.assertIsInstance(err, exceptions.HttpConflictError)
        self.assertEquals(err.status_code, 409)

    def testUnknownStatus(self):
        err = exceptions.HttpError.FromResponse(_MakeResponse(499))
        self.assertIsInstance(err, exceptions.HttpError)
        self.assertEquals(err.status_code, 499)

    def testMalformedStatus(self):
        err = exceptions.HttpError.FromResponse(_MakeResponse('BAD'))
        self.assertIsInstance(err, exceptions.HttpError)
