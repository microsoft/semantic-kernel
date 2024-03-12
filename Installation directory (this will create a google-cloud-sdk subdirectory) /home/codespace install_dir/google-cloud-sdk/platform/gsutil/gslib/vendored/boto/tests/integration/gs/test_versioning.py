# -*- coding: utf-8 -*-
# Copyright (c) 2012, Google, Inc.
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

from xml import sax

from boto import handler
from boto.gs import acl
from tests.integration.gs.testcase import GSTestCase


class GSVersioningTest(GSTestCase):

    def testVersioningToggle(self):
        b = self._MakeBucket()
        self.assertFalse(b.get_versioning_status())
        b.configure_versioning(True)
        self.assertTrue(b.get_versioning_status())
        b.configure_versioning(False)
        self.assertFalse(b.get_versioning_status())

    def testDeleteVersionedKey(self):
        b = self._MakeVersionedBucket()
        k = b.new_key("foo")
        s1 = "test1"
        k.set_contents_from_string(s1)

        k = b.get_key("foo")
        g1 = k.generation

        s2 = "test2"
        k.set_contents_from_string(s2)
        k = b.get_key("foo")
        g2 = k.generation

        versions = list(b.list_versions())
        self.assertEqual(len(versions), 2)
        self.assertEqual(versions[0].name, "foo")
        self.assertEqual(versions[1].name, "foo")
        generations = [k.generation for k in versions]
        self.assertIn(g1, generations)
        self.assertIn(g2, generations)

        # Delete "current" version and make sure that version is no longer
        # visible from a basic GET call.
        b.delete_key("foo", generation=None)
        self.assertIsNone(b.get_key("foo"))

        # Both old versions should still be there when listed using the versions
        # query parameter.
        versions = list(b.list_versions())
        self.assertEqual(len(versions), 2)
        self.assertEqual(versions[0].name, "foo")
        self.assertEqual(versions[1].name, "foo")
        generations = [k.generation for k in versions]
        self.assertIn(g1, generations)
        self.assertIn(g2, generations)

        # Delete generation 2 and make sure it's gone.
        b.delete_key("foo", generation=g2)
        versions = list(b.list_versions())
        self.assertEqual(len(versions), 1)
        self.assertEqual(versions[0].name, "foo")
        self.assertEqual(versions[0].generation, g1)

        # Delete generation 1 and make sure it's gone.
        b.delete_key("foo", generation=g1)
        versions = list(b.list_versions())
        self.assertEqual(len(versions), 0)

    def testGetVersionedKey(self):
        b = self._MakeVersionedBucket()
        k = b.new_key("foo")
        s1 = "test1"
        k.set_contents_from_string(s1)

        k = b.get_key("foo")
        g1 = k.generation
        o1 = k.get_contents_as_string()
        self.assertEqual(o1, s1)

        s2 = "test2"
        k.set_contents_from_string(s2)
        k = b.get_key("foo")
        g2 = k.generation
        self.assertNotEqual(g2, g1)
        o2 = k.get_contents_as_string()
        self.assertEqual(o2, s2)

        k = b.get_key("foo", generation=g1)
        self.assertEqual(k.get_contents_as_string(), s1)
        k = b.get_key("foo", generation=g2)
        self.assertEqual(k.get_contents_as_string(), s2)

    def testVersionedBucketCannedAcl(self):
        b = self._MakeVersionedBucket()
        k = b.new_key("foo")
        s1 = "test1"
        k.set_contents_from_string(s1)

        k = b.get_key("foo")
        g1 = k.generation

        s2 = "test2"
        k.set_contents_from_string(s2)
        k = b.get_key("foo")
        g2 = k.generation

        acl1g1 = b.get_acl("foo", generation=g1)
        acl1g2 = b.get_acl("foo", generation=g2)
        owner1g1 = acl1g1.owner.id
        owner1g2 = acl1g2.owner.id
        self.assertEqual(owner1g1, owner1g2)
        entries1g1 = acl1g1.entries.entry_list
        entries1g2 = acl1g2.entries.entry_list
        self.assertEqual(len(entries1g1), len(entries1g2))

        b.set_acl("public-read", key_name="foo", generation=g1)

        acl2g1 = b.get_acl("foo", generation=g1)
        acl2g2 = b.get_acl("foo", generation=g2)
        entries2g1 = acl2g1.entries.entry_list
        entries2g2 = acl2g2.entries.entry_list
        self.assertEqual(len(entries2g2), len(entries1g2))
        public_read_entries1 = [e for e in entries2g1 if e.permission == "READ"
                                and e.scope.type == acl.ALL_USERS]
        public_read_entries2 = [e for e in entries2g2 if e.permission == "READ"
                                and e.scope.type == acl.ALL_USERS]
        self.assertEqual(len(public_read_entries1), 1)
        self.assertEqual(len(public_read_entries2), 0)

    def testVersionedBucketXmlAcl(self):
        b = self._MakeVersionedBucket()
        k = b.new_key("foo")
        s1 = "test1"
        k.set_contents_from_string(s1)

        k = b.get_key("foo")
        g1 = k.generation

        s2 = "test2"
        k.set_contents_from_string(s2)
        k = b.get_key("foo")
        g2 = k.generation

        acl1g1 = b.get_acl("foo", generation=g1)
        acl1g2 = b.get_acl("foo", generation=g2)
        owner1g1 = acl1g1.owner.id
        owner1g2 = acl1g2.owner.id
        self.assertEqual(owner1g1, owner1g2)
        entries1g1 = acl1g1.entries.entry_list
        entries1g2 = acl1g2.entries.entry_list
        self.assertEqual(len(entries1g1), len(entries1g2))

        acl_xml = (
            '<ACCESSControlList><EntrIes><Entry>'    +
            '<Scope type="AllUsers"></Scope><Permission>READ</Permission>' +
            '</Entry></EntrIes></ACCESSControlList>')
        aclo = acl.ACL()
        h = handler.XmlHandler(aclo, b)
        sax.parseString(acl_xml, h)

        b.set_acl(aclo, key_name="foo", generation=g1)

        acl2g1 = b.get_acl("foo", generation=g1)
        acl2g2 = b.get_acl("foo", generation=g2)
        entries2g1 = acl2g1.entries.entry_list
        entries2g2 = acl2g2.entries.entry_list
        self.assertEqual(len(entries2g2), len(entries1g2))
        public_read_entries1 = [e for e in entries2g1 if e.permission == "READ"
                                and e.scope.type == acl.ALL_USERS]
        public_read_entries2 = [e for e in entries2g2 if e.permission == "READ"
                                and e.scope.type == acl.ALL_USERS]
        self.assertEqual(len(public_read_entries1), 1)
        self.assertEqual(len(public_read_entries2), 0)

    def testVersionedObjectCannedAcl(self):
        b = self._MakeVersionedBucket()
        k = b.new_key("foo")
        s1 = "test1"
        k.set_contents_from_string(s1)

        k = b.get_key("foo")
        g1 = k.generation

        s2 = "test2"
        k.set_contents_from_string(s2)
        k = b.get_key("foo")
        g2 = k.generation

        acl1g1 = b.get_acl("foo", generation=g1)
        acl1g2 = b.get_acl("foo", generation=g2)
        owner1g1 = acl1g1.owner.id
        owner1g2 = acl1g2.owner.id
        self.assertEqual(owner1g1, owner1g2)
        entries1g1 = acl1g1.entries.entry_list
        entries1g2 = acl1g2.entries.entry_list
        self.assertEqual(len(entries1g1), len(entries1g2))

        b.set_acl("public-read", key_name="foo", generation=g1)

        acl2g1 = b.get_acl("foo", generation=g1)
        acl2g2 = b.get_acl("foo", generation=g2)
        entries2g1 = acl2g1.entries.entry_list
        entries2g2 = acl2g2.entries.entry_list
        self.assertEqual(len(entries2g2), len(entries1g2))
        public_read_entries1 = [e for e in entries2g1 if e.permission == "READ"
                                and e.scope.type == acl.ALL_USERS]
        public_read_entries2 = [e for e in entries2g2 if e.permission == "READ"
                                and e.scope.type == acl.ALL_USERS]
        self.assertEqual(len(public_read_entries1), 1)
        self.assertEqual(len(public_read_entries2), 0)

    def testCopyVersionedKey(self):
        b = self._MakeVersionedBucket()
        k = b.new_key("foo")
        s1 = "test1"
        k.set_contents_from_string(s1)

        k = b.get_key("foo")
        g1 = k.generation

        s2 = "test2"
        k.set_contents_from_string(s2)

        b2 = self._MakeVersionedBucket()
        b2.copy_key("foo2", b.name, "foo", src_generation=g1)

        k2 = b2.get_key("foo2")
        s3 = k2.get_contents_as_string()
        self.assertEqual(s3, s1)

    def testKeyGenerationUpdatesOnSet(self):
        b = self._MakeVersionedBucket()
        k = b.new_key("foo")
        self.assertIsNone(k.generation)
        k.set_contents_from_string("test1")
        g1 = k.generation
        self.assertRegexpMatches(g1, r'[0-9]+')
        self.assertEqual(k.metageneration, '1')
        k.set_contents_from_string("test2")
        g2 = k.generation
        self.assertNotEqual(g1, g2)
        self.assertRegexpMatches(g2, r'[0-9]+')
        self.assertGreater(int(g2), int(g1))
        self.assertEqual(k.metageneration, '1')
