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

"""Implement the U2F variant of ISO 7816 extended APDU.

This module implements a subset ISO 7816 APDU encoding.  In particular,
it only supports extended length encoding, it only supports commands
that expect a reply, and it does not support explicitly specifying
the length of the expected reply.

It also implements the U2F variant of ISO 7816 where the Lc field
is always specified, even if there is no data.
"""
import struct

from pyu2f import errors

CMD_REGISTER = 0x01
CMD_AUTH = 0x02
CMD_VERSION = 0x03


class CommandApdu(object):
  """Represents a Command APDU.

  Represents a Command APDU sent to the security key.  Encoding
  is specified in FIDO U2F standards.
  """
  cla = None
  ins = None
  p1 = None
  p2 = None
  data = None

  def __init__(self, cla, ins, p1, p2, data=None):
    self.cla = cla
    self.ins = ins
    self.p1 = p1
    self.p2 = p2
    if data and len(data) > 65535:
      raise errors.InvalidCommandError()
    if data:
      self.data = data

  def ToByteArray(self):
    """Serialize the command.

    Encodes the command as per the U2F specs, using the standard
    ISO 7816-4 extended encoding.  All Commands expect data, so
    Le is always present.

    Returns:
      Python bytearray of the encoded command.
    """
    lc = self.InternalEncodeLc()
    out = bytearray(4)  # will extend

    out[0] = self.cla
    out[1] = self.ins
    out[2] = self.p1
    out[3] = self.p2
    if self.data:
      out.extend(lc)
      out.extend(self.data)
      out.extend([0x00, 0x00])  # Le
    else:
      out.extend([0x00, 0x00, 0x00])  # Le
    return out

  def ToLegacyU2FByteArray(self):
    """Serialize the command in the legacy format.

    Encodes the command as per the U2F specs, using the legacy
    encoding in which LC is always present.

    Returns:
      Python bytearray of the encoded command.
    """

    lc = self.InternalEncodeLc()
    out = bytearray(4)  # will extend

    out[0] = self.cla
    out[1] = self.ins
    out[2] = self.p1
    out[3] = self.p2
    out.extend(lc)
    if self.data:
      out.extend(self.data)
    out.extend([0x00, 0x00])  # Le

    return out

  def InternalEncodeLc(self):
    dl = 0
    if self.data:
      dl = len(self.data)
    # The top two bytes are guaranteed to be 0 by the assertion
    # in the constructor.
    fourbyte = struct.pack('>I', dl)
    return bytearray(fourbyte[1:])


class ResponseApdu(object):
  """Represents a Response APDU.

  Represents a Response APU sent by the security key.  Encoding
  is specified in FIDO U2F standards.
  """
  body = None
  sw1 = None
  sw2 = None

  def __init__(self, data):
    self.dbg_full_packet = data
    if not data or len(data) < 2:
      raise errors.InvalidResponseError()

    if len(data) > 2:
      self.body = data[:-2]

    self.sw1 = data[-2]
    self.sw2 = data[-1]

  def IsSuccess(self):
    return self.sw1 == 0x90 and self.sw2 == 0x00

  def CheckSuccessOrRaise(self):
    if self.sw1 == 0x69 and self.sw2 == 0x85:  # SW_CONDITIONS_NOT_SATISFIED
      raise errors.TUPRequiredError()
    elif self.sw1 == 0x6a and self.sw2 == 0x80:  # SW_WRONG_DATA
      raise errors.InvalidKeyHandleError()
    elif self.sw1 == 0x67 and self.sw2 == 0x00:  # SW_WRONG_LENGTH
      raise errors.InvalidKeyHandleError()
    elif not self.IsSuccess():
      raise errors.ApduError(self.sw1, self.sw2)
