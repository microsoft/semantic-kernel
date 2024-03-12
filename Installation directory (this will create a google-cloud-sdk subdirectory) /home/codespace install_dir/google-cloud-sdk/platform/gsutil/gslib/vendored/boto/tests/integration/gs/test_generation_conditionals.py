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

"""Integration tests for GS versioning support."""

import os
import tempfile
from xml import sax

from six import StringIO

from boto import handler
from boto.exception import GSResponseError
from boto.gs.acl import ACL
from tests.integration.gs.testcase import GSTestCase


# HTTP Error returned when a generation precondition fails.
VERSION_MISMATCH = "412"


class GSGenerationConditionalsTest(GSTestCase):

    def testConditionalSetContentsFromFile(self):
        b = self._MakeBucket()
        k = b.new_key("foo")
        s1 = "test1"
        fp = StringIO.StringIO(s1)
        with self.assertRaisesRegexp(GSResponseError, VERSION_MISMATCH):
            k.set_contents_from_file(fp, if_generation=999)

        fp = StringIO.StringIO(s1)
        k.set_contents_from_file(fp, if_generation=0)
        g1 = k.generation

        s2 = "test2"
        fp = StringIO.StringIO(s2)
        with self.assertRaisesRegexp(GSResponseError, VERSION_MISMATCH):
            k.set_contents_from_file(fp, if_generation=int(g1)+1)

        fp = StringIO.StringIO(s2)
        k.set_contents_from_file(fp, if_generation=g1)
        self.assertEqual(k.get_contents_as_string(), s2)

    def testConditionalSetContentsFromString(self):
        b = self._MakeBucket()
        k = b.new_key("foo")
        s1 = "test1"
        with self.assertRaisesRegexp(GSResponseError, VERSION_MISMATCH):
            k.set_contents_from_string(s1, if_generation=999)

        k.set_contents_from_string(s1, if_generation=0)
        g1 = k.generation

        s2 = "test2"
        with self.assertRaisesRegexp(GSResponseError, VERSION_MISMATCH):
            k.set_contents_from_string(s2, if_generation=int(g1)+1)

        k.set_contents_from_string(s2, if_generation=g1)
        self.assertEqual(k.get_contents_as_string(), s2)

    def testConditionalSetContentsFromFilename(self):
        s1 = "test1"
        s2 = "test2"
        f1 = tempfile.NamedTemporaryFile(prefix="boto-gs-test", delete=False)
        f2 = tempfile.NamedTemporaryFile(prefix="boto-gs-test", delete=False)
        fname1 = f1.name
        fname2 = f2.name
        f1.write(s1)
        f1.close()
        f2.write(s2)
        f2.close()

        try:
            b = self._MakeBucket()
            k = b.new_key("foo")

            with self.assertRaisesRegexp(GSResponseError, VERSION_MISMATCH):
                k.set_contents_from_filename(fname1, if_generation=999)

            k.set_contents_from_filename(fname1, if_generation=0)
            g1 = k.generation

            with self.assertRaisesRegexp(GSResponseError, VERSION_MISMATCH):
                k.set_contents_from_filename(fname2, if_generation=int(g1)+1)

            k.set_contents_from_filename(fname2, if_generation=g1)
            self.assertEqual(k.get_contents_as_string(), s2)
        finally:
            os.remove(fname1)
            os.remove(fname2)

    def testBucketConditionalSetAcl(self):
        b = self._MakeVersionedBucket()
        k = b.new_key("foo")
        s1 = "test1"
        k.set_contents_from_string(s1)

        g1 = k.generation
        mg1 = k.metageneration
        self.assertEqual(str(mg1), "1")
        b.set_acl("public-read", key_name="foo")

        k = b.get_key("foo")
        g2 = k.generation
        mg2 = k.metageneration

        self.assertEqual(g2, g1)
        self.assertGreater(mg2, mg1)

        with self.assertRaisesRegexp(ValueError, ("Received if_metageneration "
                                                  "argument with no "
                                                  "if_generation argument")):
            b.set_acl("bucket-owner-full-control", key_name="foo",
                      if_metageneration=123)

        with self.assertRaisesRegexp(GSResponseError, VERSION_MISMATCH):
            b.set_acl("bucket-owner-full-control", key_name="foo",
                      if_generation=int(g2) + 1)

        with self.assertRaisesRegexp(GSResponseError, VERSION_MISMATCH):
            b.set_acl("bucket-owner-full-control", key_name="foo",
                      if_generation=g2, if_metageneration=int(mg2) + 1)

        b.set_acl("bucket-owner-full-control", key_name="foo", if_generation=g2)

        k = b.get_key("foo")
        g3 = k.generation
        mg3 = k.metageneration
        self.assertEqual(g3, g2)
        self.assertGreater(mg3, mg2)

        b.set_acl("public-read", key_name="foo", if_generation=g3,
                  if_metageneration=mg3)

    def testConditionalSetContentsFromStream(self):
        b = self._MakeBucket()
        k = b.new_key("foo")
        s1 = "test1"
        fp = StringIO.StringIO(s1)
        with self.assertRaisesRegexp(GSResponseError, VERSION_MISMATCH):
            k.set_contents_from_stream(fp, if_generation=999)

        fp = StringIO.StringIO(s1)
        k.set_contents_from_stream(fp, if_generation=0)
        g1 = k.generation

        k = b.get_key("foo")
        s2 = "test2"
        fp = StringIO.StringIO(s2)
        with self.assertRaisesRegexp(GSResponseError, VERSION_MISMATCH):
            k.set_contents_from_stream(fp, if_generation=int(g1)+1)

        fp = StringIO.StringIO(s2)
        k.set_contents_from_stream(fp, if_generation=g1)
        self.assertEqual(k.get_contents_as_string(), s2)

    def testBucketConditionalSetCannedAcl(self):
        b = self._MakeVersionedBucket()
        k = b.new_key("foo")
        s1 = "test1"
        k.set_contents_from_string(s1)

        g1 = k.generation
        mg1 = k.metageneration
        self.assertEqual(str(mg1), "1")
        b.set_canned_acl("public-read", key_name="foo")

        k = b.get_key("foo")
        g2 = k.generation
        mg2 = k.metageneration

        self.assertEqual(g2, g1)
        self.assertGreater(mg2, mg1)

        with self.assertRaisesRegexp(ValueError, ("Received if_metageneration "
                                                  "argument with no "
                                                  "if_generation argument")):
            b.set_canned_acl("bucket-owner-full-control", key_name="foo",
                      if_metageneration=123)

        with self.assertRaisesRegexp(GSResponseError, VERSION_MISMATCH):
            b.set_canned_acl("bucket-owner-full-control", key_name="foo",
                      if_generation=int(g2) + 1)

        with self.assertRaisesRegexp(GSResponseError, VERSION_MISMATCH):
            b.set_canned_acl("bucket-owner-full-control", key_name="foo",
                      if_generation=g2, if_metageneration=int(mg2) + 1)

        b.set_canned_acl("bucket-owner-full-control", key_name="foo",
                         if_generation=g2)

        k = b.get_key("foo")
        g3 = k.generation
        mg3 = k.metageneration
        self.assertEqual(g3, g2)
        self.assertGreater(mg3, mg2)

        b.set_canned_acl("public-read", key_name="foo", if_generation=g3,
                  if_metageneration=mg3)

    def testBucketConditionalSetXmlAcl(self):
        b = self._MakeVersionedBucket()
        k = b.new_key("foo")
        s1 = "test1"
        k.set_contents_from_string(s1)

        g1 = k.generation
        mg1 = k.metageneration
        self.assertEqual(str(mg1), "1")

        acl_xml = (
            '<ACCESSControlList><EntrIes><Entry>'    +
            '<Scope type="AllUsers"></Scope><Permission>READ</Permission>' +
            '</Entry></EntrIes></ACCESSControlList>')
        acl = ACL()
        h = handler.XmlHandler(acl, b)
        sax.parseString(acl_xml, h)
        acl = acl.to_xml()

        b.set_xml_acl(acl, key_name="foo")

        k = b.get_key("foo")
        g2 = k.generation
        mg2 = k.metageneration

        self.assertEqual(g2, g1)
        self.assertGreater(mg2, mg1)

        with self.assertRaisesRegexp(ValueError, ("Received if_metageneration "
                                                  "argument with no "
                                                  "if_generation argument")):
            b.set_xml_acl(acl, key_name="foo", if_metageneration=123)

        with self.assertRaisesRegexp(GSResponseError, VERSION_MISMATCH):
            b.set_xml_acl(acl, key_name="foo", if_generation=int(g2) + 1)

        with self.assertRaisesRegexp(GSResponseError, VERSION_MISMATCH):
            b.set_xml_acl(acl, key_name="foo", if_generation=g2,
                          if_metageneration=int(mg2) + 1)

        b.set_xml_acl(acl, key_name="foo", if_generation=g2)

        k = b.get_key("foo")
        g3 = k.generation
        mg3 = k.metageneration
        self.assertEqual(g3, g2)
        self.assertGreater(mg3, mg2)

        b.set_xml_acl(acl, key_name="foo", if_generation=g3,
                      if_metageneration=mg3)

    def testObjectConditionalSetAcl(self):
        b = self._MakeVersionedBucket()
        k = b.new_key("foo")
        k.set_contents_from_string("test1")

        g1 = k.generation
        mg1 = k.metageneration
        self.assertEqual(str(mg1), "1")
        k.set_acl("public-read")

        k = b.get_key("foo")
        g2 = k.generation
        mg2 = k.metageneration

        self.assertEqual(g2, g1)
        self.assertGreater(mg2, mg1)

        with self.assertRaisesRegexp(ValueError, ("Received if_metageneration "
                                                  "argument with no "
                                                  "if_generation argument")):
            k.set_acl("bucket-owner-full-control", if_metageneration=123)

        with self.assertRaisesRegexp(GSResponseError, VERSION_MISMATCH):
            k.set_acl("bucket-owner-full-control", if_generation=int(g2) + 1)

        with self.assertRaisesRegexp(GSResponseError, VERSION_MISMATCH):
            k.set_acl("bucket-owner-full-control", if_generation=g2,
                      if_metageneration=int(mg2) + 1)

        k.set_acl("bucket-owner-full-control", if_generation=g2)

        k = b.get_key("foo")
        g3 = k.generation
        mg3 = k.metageneration
        self.assertEqual(g3, g2)
        self.assertGreater(mg3, mg2)

        k.set_acl("public-read", if_generation=g3, if_metageneration=mg3)

    def testObjectConditionalSetCannedAcl(self):
        b = self._MakeVersionedBucket()
        k = b.new_key("foo")
        k.set_contents_from_string("test1")

        g1 = k.generation
        mg1 = k.metageneration
        self.assertEqual(str(mg1), "1")
        k.set_canned_acl("public-read")

        k = b.get_key("foo")
        g2 = k.generation
        mg2 = k.metageneration

        self.assertEqual(g2, g1)
        self.assertGreater(mg2, mg1)

        with self.assertRaisesRegexp(ValueError, ("Received if_metageneration "
                                                  "argument with no "
                                                  "if_generation argument")):
            k.set_canned_acl("bucket-owner-full-control",
                             if_metageneration=123)

        with self.assertRaisesRegexp(GSResponseError, VERSION_MISMATCH):
            k.set_canned_acl("bucket-owner-full-control",
                             if_generation=int(g2) + 1)

        with self.assertRaisesRegexp(GSResponseError, VERSION_MISMATCH):
            k.set_canned_acl("bucket-owner-full-control", if_generation=g2,
                      if_metageneration=int(mg2) + 1)

        k.set_canned_acl("bucket-owner-full-control", if_generation=g2)

        k = b.get_key("foo")
        g3 = k.generation
        mg3 = k.metageneration
        self.assertEqual(g3, g2)
        self.assertGreater(mg3, mg2)

        k.set_canned_acl("public-read", if_generation=g3, if_metageneration=mg3)

    def testObjectConditionalSetXmlAcl(self):
        b = self._MakeVersionedBucket()
        k = b.new_key("foo")
        s1 = "test1"
        k.set_contents_from_string(s1)

        g1 = k.generation
        mg1 = k.metageneration
        self.assertEqual(str(mg1), "1")

        acl_xml = (
            '<ACCESSControlList><EntrIes><Entry>'    +
            '<Scope type="AllUsers"></Scope><Permission>READ</Permission>' +
            '</Entry></EntrIes></ACCESSControlList>')
        acl = ACL()
        h = handler.XmlHandler(acl, b)
        sax.parseString(acl_xml, h)
        acl = acl.to_xml()

        k.set_xml_acl(acl)

        k = b.get_key("foo")
        g2 = k.generation
        mg2 = k.metageneration

        self.assertEqual(g2, g1)
        self.assertGreater(mg2, mg1)

        with self.assertRaisesRegexp(ValueError, ("Received if_metageneration "
                                                  "argument with no "
                                                  "if_generation argument")):
            k.set_xml_acl(acl, if_metageneration=123)

        with self.assertRaisesRegexp(GSResponseError, VERSION_MISMATCH):
            k.set_xml_acl(acl, if_generation=int(g2) + 1)

        with self.assertRaisesRegexp(GSResponseError, VERSION_MISMATCH):
            k.set_xml_acl(acl, if_generation=g2, if_metageneration=int(mg2) + 1)

        k.set_xml_acl(acl, if_generation=g2)

        k = b.get_key("foo")
        g3 = k.generation
        mg3 = k.metageneration
        self.assertEqual(g3, g2)
        self.assertGreater(mg3, mg2)

        k.set_xml_acl(acl, if_generation=g3, if_metageneration=mg3)
