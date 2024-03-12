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

"""Tests for pyu2f.apdu."""

from six.moves import range
import sys

from pyu2f import apdu
from pyu2f import errors

if sys.version_info[:2] < (2, 7):
  import unittest2 as unittest  # pylint: disable=g-import-not-at-top
else:
  import unittest  # pylint: disable=g-import-not-at-top


class ApduTest(unittest.TestCase):

  def testSerializeCommandApdu(self):
    cmd = apdu.CommandApdu(0, 0x01, 0x03, 0x04, bytearray([0x10, 0x20, 0x30]))
    self.assertEqual(
        cmd.ToByteArray(),
        bytearray([0x00, 0x01, 0x03, 0x04, 0x00, 0x00, 0x03, 0x10, 0x20, 0x30,
                   0x00, 0x00]))
    self.assertEqual(
        cmd.ToLegacyU2FByteArray(),
        bytearray([0x00, 0x01, 0x03, 0x04, 0x00, 0x00, 0x03, 0x10, 0x20, 0x30,
                   0x00, 0x00]))

  def testSerializeCommandApduNoData(self):
    cmd = apdu.CommandApdu(0, 0x01, 0x03, 0x04)
    self.assertEqual(cmd.ToByteArray(),
                     bytearray([0x00, 0x01, 0x03, 0x04, 0x00, 0x00, 0x00]))
    self.assertEqual(cmd.ToLegacyU2FByteArray(),
                     bytearray([0x00, 0x01, 0x03, 0x04,
                                0x00, 0x00, 0x00, 0x00, 0x00]))

  def testSerializeCommandApduTooLong(self):
    self.assertRaises(errors.InvalidCommandError, apdu.CommandApdu, 0, 0x01,
                      0x03, 0x04, bytearray(0 for x in range(0, 65536)))

  def testResponseApduParse(self):
    resp = apdu.ResponseApdu(bytearray([0x05, 0x04, 0x90, 0x00]))
    self.assertEqual(resp.body, bytearray([0x05, 0x04]))
    self.assertEqual(resp.sw1, 0x90)
    self.assertEqual(resp.sw2, 0x00)
    self.assertTrue(resp.IsSuccess())

  def testResponseApduParseNoBody(self):
    resp = apdu.ResponseApdu(bytearray([0x69, 0x85]))
    self.assertEqual(resp.sw1, 0x69)
    self.assertEqual(resp.sw2, 0x85)
    self.assertFalse(resp.IsSuccess())

  def testResponseApduParseInvalid(self):
    self.assertRaises(errors.InvalidResponseError, apdu.ResponseApdu,
                      bytearray([0x05]))

  def testResponseApduCheckSuccessTUPRequired(self):
    resp = apdu.ResponseApdu(bytearray([0x69, 0x85]))
    self.assertRaises(errors.TUPRequiredError, resp.CheckSuccessOrRaise)

  def testResponseApduCheckSuccessInvalidKeyHandle(self):
    resp = apdu.ResponseApdu(bytearray([0x6a, 0x80]))
    self.assertRaises(errors.InvalidKeyHandleError, resp.CheckSuccessOrRaise)

  def testResponseApduCheckSuccessOtherError(self):
    resp = apdu.ResponseApdu(bytearray([0xfa, 0x05]))
    self.assertRaises(errors.ApduError, resp.CheckSuccessOrRaise)


if __name__ == '__main__':
  unittest.main()
