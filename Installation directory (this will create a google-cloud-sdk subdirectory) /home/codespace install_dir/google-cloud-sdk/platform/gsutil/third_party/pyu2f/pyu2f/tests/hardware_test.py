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

"""Tests for pyu2f.hardware."""

import sys

import mock

from pyu2f import errors
from pyu2f import hardware

if sys.version_info[:2] < (2, 7):
  import unittest2 as unittest  # pylint: disable=g-import-not-at-top
else:
  import unittest  # pylint: disable=g-import-not-at-top


class HardwareTest(unittest.TestCase):

  def testSimpleCommands(self):
    mock_transport = mock.MagicMock()
    sk = hardware.SecurityKey(mock_transport)

    sk.CmdBlink(5)
    mock_transport.SendBlink.assert_called_once_with(5)

    sk.CmdWink()
    mock_transport.SendWink.assert_called_once_with()

    sk.CmdPing(bytearray(b'foo'))
    mock_transport.SendPing.assert_called_once_with(bytearray(b'foo'))

  def testRegisterInvalidParams(self):
    mock_transport = mock.MagicMock()
    sk = hardware.SecurityKey(mock_transport)

    self.assertRaises(errors.InvalidRequestError, sk.CmdRegister, '1234',
                      '1234')

  def testRegisterSuccess(self):
    mock_transport = mock.MagicMock()
    sk = hardware.SecurityKey(mock_transport)

    challenge_param = b'01234567890123456789012345678901'
    app_param = b'01234567890123456789012345678901'

    mock_transport.SendMsgBytes.return_value = bytearray(
        [0x01, 0x02, 0x90, 0x00])

    reply = sk.CmdRegister(challenge_param, app_param)
    self.assertEquals(reply, bytearray([0x01, 0x02]))
    self.assertEquals(mock_transport.SendMsgBytes.call_count, 1)
    (sent_msg,), _ = mock_transport.SendMsgBytes.call_args
    self.assertEquals(sent_msg[0:4], bytearray([0x00, 0x01, 0x03, 0x00]))
    self.assertEquals(sent_msg[7:-2], bytearray(challenge_param + app_param))

  def testRegisterTUPRequired(self):
    mock_transport = mock.MagicMock()
    sk = hardware.SecurityKey(mock_transport)

    challenge_param = b'01234567890123456789012345678901'
    app_param = b'01234567890123456789012345678901'

    mock_transport.SendMsgBytes.return_value = bytearray([0x69, 0x85])

    self.assertRaises(errors.TUPRequiredError, sk.CmdRegister, challenge_param,
                      app_param)
    self.assertEquals(mock_transport.SendMsgBytes.call_count, 1)

  def testVersion(self):
    mock_transport = mock.MagicMock()
    sk = hardware.SecurityKey(mock_transport)

    mock_transport.SendMsgBytes.return_value = bytearray(b'U2F_V2\x90\x00')

    reply = sk.CmdVersion()
    self.assertEquals(reply, bytearray(b'U2F_V2'))
    self.assertEquals(mock_transport.SendMsgBytes.call_count, 1)
    (sent_msg,), _ = mock_transport.SendMsgBytes.call_args
    self.assertEquals(sent_msg, bytearray(
        [0x00, 0x03, 0x00, 0x00, 0x00, 0x00, 0x00]))

  def testVersionFallback(self):
    mock_transport = mock.MagicMock()
    sk = hardware.SecurityKey(mock_transport)

    mock_transport.SendMsgBytes.side_effect = [
        bytearray([0x67, 0x00]),
        bytearray(b'U2F_V2\x90\x00')]

    reply = sk.CmdVersion()
    self.assertEquals(reply, bytearray(b'U2F_V2'))
    self.assertEquals(mock_transport.SendMsgBytes.call_count, 2)
    (sent_msg,), _ = mock_transport.SendMsgBytes.call_args_list[0]
    self.assertEquals(len(sent_msg), 7)
    self.assertEquals(sent_msg[0:4], bytearray([0x00, 0x03, 0x00, 0x00]))
    self.assertEquals(sent_msg[4:7], bytearray([0x00, 0x00, 0x00]))  # Le
    (sent_msg,), _ = mock_transport.SendMsgBytes.call_args_list[1]
    self.assertEquals(len(sent_msg), 9)
    self.assertEquals(sent_msg[0:4], bytearray([0x00, 0x03, 0x00, 0x00]))
    self.assertEquals(sent_msg[4:7], bytearray([0x00, 0x00, 0x00]))  # Lc
    self.assertEquals(sent_msg[7:9], bytearray([0x00, 0x00]))  # Le

  def testVersionErrors(self):
    mock_transport = mock.MagicMock()
    sk = hardware.SecurityKey(mock_transport)

    mock_transport.SendMsgBytes.return_value = bytearray([0xfa, 0x05])

    self.assertRaises(errors.ApduError, sk.CmdVersion)
    self.assertEquals(mock_transport.SendMsgBytes.call_count, 1)

  def testAuthenticateSuccess(self):
    mock_transport = mock.MagicMock()
    sk = hardware.SecurityKey(mock_transport)

    challenge_param = b'01234567890123456789012345678901'
    app_param = b'01234567890123456789012345678901'
    key_handle = b'\x01\x02\x03\x04'

    mock_transport.SendMsgBytes.return_value = bytearray(
        [0x01, 0x02, 0x90, 0x00])

    reply = sk.CmdAuthenticate(challenge_param, app_param, key_handle)
    self.assertEquals(reply, bytearray([0x01, 0x02]))
    self.assertEquals(mock_transport.SendMsgBytes.call_count, 1)
    (sent_msg,), _ = mock_transport.SendMsgBytes.call_args
    self.assertEquals(sent_msg[0:4], bytearray([0x00, 0x02, 0x03, 0x00]))
    self.assertEquals(
        sent_msg[7:-2],
        bytearray(challenge_param + app_param + bytearray([4, 1, 2, 3, 4])))

  def testAuthenticateCheckOnly(self):
    mock_transport = mock.MagicMock()
    sk = hardware.SecurityKey(mock_transport)

    challenge_param = b'01234567890123456789012345678901'
    app_param = b'01234567890123456789012345678901'
    key_handle = b'\x01\x02\x03\x04'

    mock_transport.SendMsgBytes.return_value = bytearray(
        [0x01, 0x02, 0x90, 0x00])

    reply = sk.CmdAuthenticate(challenge_param,
                               app_param,
                               key_handle,
                               check_only=True)
    self.assertEquals(reply, bytearray([0x01, 0x02]))
    self.assertEquals(mock_transport.SendMsgBytes.call_count, 1)
    (sent_msg,), _ = mock_transport.SendMsgBytes.call_args
    self.assertEquals(sent_msg[0:4], bytearray([0x00, 0x02, 0x07, 0x00]))
    self.assertEquals(
        sent_msg[7:-2],
        bytearray(challenge_param + app_param + bytearray([4, 1, 2, 3, 4])))

  def testAuthenticateTUPRequired(self):
    mock_transport = mock.MagicMock()
    sk = hardware.SecurityKey(mock_transport)

    challenge_param = b'01234567890123456789012345678901'
    app_param = b'01234567890123456789012345678901'
    key_handle = b'\x01\x02\x03\x04'

    mock_transport.SendMsgBytes.return_value = bytearray([0x69, 0x85])

    self.assertRaises(errors.TUPRequiredError, sk.CmdAuthenticate,
                      challenge_param, app_param, key_handle)
    self.assertEquals(mock_transport.SendMsgBytes.call_count, 1)

  def testAuthenticateInvalidKeyHandle(self):
    mock_transport = mock.MagicMock()
    sk = hardware.SecurityKey(mock_transport)

    challenge_param = b'01234567890123456789012345678901'
    app_param = b'01234567890123456789012345678901'
    key_handle = b'\x01\x02\x03\x04'

    mock_transport.SendMsgBytes.return_value = bytearray([0x6a, 0x80])

    self.assertRaises(errors.InvalidKeyHandleError, sk.CmdAuthenticate,
                      challenge_param, app_param, key_handle)
    self.assertEquals(mock_transport.SendMsgBytes.call_count, 1)


if __name__ == '__main__':
  unittest.main()
