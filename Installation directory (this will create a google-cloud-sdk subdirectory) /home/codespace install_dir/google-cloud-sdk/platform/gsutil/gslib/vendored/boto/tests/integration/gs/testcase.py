# -*- coding: utf-8 -*-
# Copyright (c) 2013, Google, Inc.
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

"""Base TestCase class for gs integration tests."""

import shutil
import tempfile
import time

from boto.exception import GSResponseError
from boto.gs.connection import GSConnection
from tests.integration.gs import util
from tests.integration.gs.util import retry
from tests.unit import unittest

@unittest.skipUnless(util.has_google_credentials(),
                     "Google credentials are required to run the Google "
                     "Cloud Storage tests.  Update your boto.cfg to run "
                     "these tests.")
class GSTestCase(unittest.TestCase):
    gs = True

    def setUp(self):
        self._conn = GSConnection()
        self._buckets = []
        self._tempdirs = []

    # Retry with an exponential backoff if a server error is received. This
    # ensures that we try *really* hard to clean up after ourselves.
    @retry(GSResponseError)
    def tearDown(self):
        while len(self._tempdirs):
            tmpdir = self._tempdirs.pop()
            shutil.rmtree(tmpdir, ignore_errors=True)

        while(len(self._buckets)):
            b = self._buckets[-1]
            try:
                bucket = self._conn.get_bucket(b)
                while len(list(bucket.list_versions())) > 0:
                    for k in bucket.list_versions():
                        try:
                            bucket.delete_key(k.name, generation=k.generation)
                        except GSResponseError as e:
                            if e.status != 404:
                                raise
                bucket.delete()
            except GSResponseError as e:
                if e.status != 404:
                    raise
            self._buckets.pop()

    def _GetConnection(self):
        """Returns the GSConnection object used to connect to GCS."""
        return self._conn

    def _MakeTempName(self):
        """Creates and returns a temporary name for testing that is likely to be
        unique."""
        return "boto-gs-test-%s" % repr(time.time()).replace(".", "-")

    def _MakeBucketName(self):
        """Creates and returns a temporary bucket name for testing that is
        likely to be unique."""
        b = self._MakeTempName()
        self._buckets.append(b)
        return b

    def _MakeBucket(self):
        """Creates and returns temporary bucket for testing. After the test, the
        contents of the bucket and the bucket itself will be deleted."""
        b = self._conn.create_bucket(self._MakeBucketName())
        return b

    def _MakeKey(self, data='', bucket=None, set_contents=True):
        """Creates and returns a Key with provided data. If no bucket is given,
        a temporary bucket is created."""
        if data and not set_contents:
            # The data and set_contents parameters are mutually exclusive. 
            raise ValueError('MakeKey called with a non-empty data parameter '
                             'but set_contents was set to False.')
        if not bucket:
            bucket = self._MakeBucket()
        key_name = self._MakeTempName()
        k = bucket.new_key(key_name)
        if set_contents:
            k.set_contents_from_string(data)
        return k

    def _MakeVersionedBucket(self):
        """Creates and returns temporary versioned bucket for testing. After the
        test, the contents of the bucket and the bucket itself will be
        deleted."""
        b = self._MakeBucket()
        b.configure_versioning(True)
        time.sleep(30)  # Ensure versioning config propagates.
        return b

    def _MakeTempDir(self):
        """Creates and returns a temporary directory on disk. After the test,
        the contents of the directory and the directory itself will be
        deleted."""
        tmpdir = tempfile.mkdtemp(prefix=self._MakeTempName())
        self._tempdirs.append(tmpdir)
        return tmpdir
