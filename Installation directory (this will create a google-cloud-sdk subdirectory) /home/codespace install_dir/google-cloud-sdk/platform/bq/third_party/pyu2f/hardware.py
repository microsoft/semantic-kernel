#!/usr/bin/env python
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

"""This module implements the low level device API.

This module exposes a low level SecurityKey class,
representing the physical security key device.
"""
import logging

from pyu2f import apdu
from pyu2f import errors


class SecurityKey(object):
  """Low level api for talking to a security key.

  This class implements the low level api specified in FIDO
  U2F for talking to a security key.
  """

  def __init__(self, transport):
    self.transport = transport
    self.use_legacy_format = False
    self.logger = logging.getLogger('pyu2f.hardware')

  def CmdRegister(self, challenge_param, app_param):
    """Register security key.

    Ask the security key to register with a particular origin & client.

    Args:
      challenge_param: Arbitrary 32 byte challenge string.
      app_param: Arbitrary 32 byte applciation parameter.

    Returns:
      A binary structure containing the key handle, attestation, and a
      signature over that by the attestation key.  The precise format
      is dictated by the FIDO U2F specs.

    Raises:
      TUPRequiredError: A Test of User Precense is required to proceed.
      ApduError: Something went wrong on the device.
    """
    self.logger.debug('CmdRegister')
    if len(challenge_param) != 32 or len(app_param) != 32:
      raise errors.InvalidRequestError()

    body = bytearray(challenge_param + app_param)
    response = self.InternalSendApdu(apdu.CommandApdu(
        0,
        apdu.CMD_REGISTER,
        0x03,  # Per the U2F reference code tests
        0x00,
        body))
    response.CheckSuccessOrRaise()

    return response.body

  def CmdAuthenticate(self,
                      challenge_param,
                      app_param,
                      key_handle,
                      check_only=False):
    """Attempt to obtain an authentication signature.

    Ask the security key to sign a challenge for a particular key handle
    in order to authenticate the user.

    Args:
      challenge_param: SHA-256 hash of client_data object as a bytes
          object.
      app_param: SHA-256 hash of the app id as a bytes object.
      key_handle: The key handle to use to issue the signature as a bytes
          object.
      check_only: If true, only check if key_handle is valid.

    Returns:
      A binary structure containing the key handle, attestation, and a
      signature over that by the attestation key.  The precise format
      is dictated by the FIDO U2F specs.

    Raises:
      TUPRequiredError: If check_only is False, a Test of User Precense
          is required to proceed.  If check_only is True, this means
          the key_handle is valid.
      InvalidKeyHandleError: The key_handle is not valid for this device.
      ApduError: Something else went wrong on the device.
    """
    self.logger.debug('CmdAuthenticate')
    if len(challenge_param) != 32 or len(app_param) != 32:
      raise errors.InvalidRequestError()
    control = 0x07 if check_only else 0x03

    body = bytearray(challenge_param + app_param +
                     bytearray([len(key_handle)]) + key_handle)
    response = self.InternalSendApdu(apdu.CommandApdu(
        0, apdu.CMD_AUTH, control, 0x00, body))
    response.CheckSuccessOrRaise()

    return response.body

  def CmdVersion(self):
    """Obtain the version of the device and test transport format.

    Obtains the version of the device and determines whether to use ISO
    7816-4 or the U2f variant.  This function should be called at least once
    before CmdAuthenticate or CmdRegister to make sure the object is using the
    proper transport for the device.

    Returns:
      The version of the U2F protocol in use.
    """
    self.logger.debug('CmdVersion')
    response = self.InternalSendApdu(apdu.CommandApdu(
        0, apdu.CMD_VERSION, 0x00, 0x00))

    if not response.IsSuccess():
      raise errors.ApduError(response.sw1, response.sw2)

    return response.body

  def CmdBlink(self, time):
    self.logger.debug('CmdBlink')
    self.transport.SendBlink(time)

  def CmdWink(self):
    self.logger.debug('CmdWink')
    self.transport.SendWink()

  def CmdPing(self, data):
    self.logger.debug('CmdPing')
    return self.transport.SendPing(data)

  def InternalSendApdu(self, apdu_to_send):
    """Send an APDU to the device.

    Sends an APDU to the device, possibly falling back to the legacy
    encoding format that is not ISO7816-4 compatible.

    Args:
      apdu_to_send: The CommandApdu object to send

    Returns:
      The ResponseApdu object constructed out of the devices reply.
    """
    response = None
    if not self.use_legacy_format:
      response = apdu.ResponseApdu(self.transport.SendMsgBytes(
          apdu_to_send.ToByteArray()))
      if response.sw1 == 0x67 and response.sw2 == 0x00:
        # If we failed using the standard format, retry with the
        # legacy format.
        self.use_legacy_format = True
        return self.InternalSendApdu(apdu_to_send)
    else:
      response = apdu.ResponseApdu(self.transport.SendMsgBytes(
          apdu_to_send.ToLegacyU2FByteArray()))
    return response
