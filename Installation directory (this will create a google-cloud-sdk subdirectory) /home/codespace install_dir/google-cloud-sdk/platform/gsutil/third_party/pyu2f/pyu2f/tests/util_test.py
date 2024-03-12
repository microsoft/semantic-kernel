# Copyright 2016 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Tests for pyu2f.tests.lib.util."""

from six.moves import range
import sys

from pyu2f.tests.lib import util

if sys.version_info[:2] < (2, 7):
  import unittest2 as unittest  # pylint: disable=g-import-not-at-top
else:
  import unittest  # pylint: disable=g-import-not-at-top


class UtilTest(unittest.TestCase):

  def testSimplePing(self):
    dev = util.FakeHidDevice(cid_to_allocate=None)
    dev.Write([0, 0, 0, 1, 0x81, 0, 3, 1, 2, 3])
    self.assertEquals(
        dev.Read(), [0, 0, 0, 1, 0x81, 0, 3, 1, 2, 3] + [0
                                                         for _ in range(54)])

  def testErrorBusy(self):
    dev = util.FakeHidDevice(cid_to_allocate=None)
    dev.SetChannelBusyCount(2)
    dev.Write([0, 0, 0, 1, 0x81, 0, 3, 1, 2, 3])
    self.assertEquals(
        dev.Read(), [0, 0, 0, 1, 0xbf, 0, 1, 6] + [0 for _ in range(56)])
    dev.Write([0, 0, 0, 1, 0x81, 0, 3, 1, 2, 3])
    self.assertEquals(
        dev.Read(), [0, 0, 0, 1, 0xbf, 0, 1, 6] + [0 for _ in range(56)])
    dev.Write([0, 0, 0, 1, 0x81, 0, 3, 1, 2, 3])
    self.assertEquals(
        dev.Read(), [0, 0, 0, 1, 0x81, 0, 3, 1, 2, 3] + [0
                                                         for _ in range(54)])

  def testFragmentedApdu(self):
    dev = util.FakeHidDevice(cid_to_allocate=None,
                             msg_reply=list(range(85, 0, -1)))
    dev.Write([0, 0, 0, 1, 0x83, 0, 100] + [x for x in range(57)])
    dev.Write([0, 0, 0, 1, 0] + [x for x in range(57, 100)])
    self.assertEquals(
        dev.Read(), [0, 0, 0, 1, 0x83, 0, 85] + [x for x in range(85, 28, -1)])
    self.assertEquals(
        dev.Read(),
        [0, 0, 0, 1, 0] + [x for x in range(28, 0, -1)] + [0
                                                           for _ in range(31)])


if __name__ == '__main__':
  unittest.main()
