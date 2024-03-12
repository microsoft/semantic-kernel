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

"""Implement a high level U2F API analogous to the javascript API spec.

This modules implements a high level U2F API that is analogous in spirit
to the high level U2F javascript API.  It supports both registration and
authetication.  For the purposes of this API, the "origin" is the hostname
of the machine this library is running on.
"""

import hashlib
import socket
import time

from pyu2f import errors
from pyu2f import hardware
from pyu2f import hidtransport
from pyu2f import model


def GetLocalU2FInterface(origin=socket.gethostname()):
  """Obtains a U2FInterface for the first valid local U2FHID device found."""
  hid_transports = hidtransport.DiscoverLocalHIDU2FDevices()
  for t in hid_transports:
    try:
      return U2FInterface(security_key=hardware.SecurityKey(transport=t),
                          origin=origin)
    except errors.UnsupportedVersionException:
      # Skip over devices that don't speak the proper version of the protocol.
      pass

  # Unable to find a device
  raise errors.NoDeviceFoundError()


class U2FInterface(object):
  """High level U2F interface.

  Implements a high level interface in the spirit of the FIDO U2F
  javascript API high level interface.  It supports registration
  and authentication (signing).

  IMPORTANT NOTE: This class does NOT validate the app id against the
  origin.  In particular, any user can assert any app id all the way to
  the device.  The security model of a python library is such that doing
  so would not provide significant benfit as it could be bypassed by the
  caller talking to a lower level of the API.  In fact, so could the origin
  itself.  The origin is still set to a plausible value (the hostname) by
  this library.

  TODO(user): Figure out a plan on how to address this gap/document the
  consequences of this more clearly.
  """

  def __init__(self, security_key, origin=socket.gethostname()):
    self.origin = origin
    self.security_key = security_key

    if self.security_key.CmdVersion() != b'U2F_V2':
      raise errors.UnsupportedVersionException()

  def Register(self, app_id, challenge, registered_keys):
    """Registers app_id with the security key.

    Executes the U2F registration flow with the security key.

    Args:
      app_id: The app_id to register the security key against.
      challenge: Server challenge passed to the security key.
      registered_keys: List of keys already registered for this app_id+user.

    Returns:
      RegisterResponse with key_handle and attestation information in it (
        encoded in FIDO U2F binary format within registration_data field).

    Raises:
      U2FError: There was some kind of problem with registration (e.g.
        the device was already registered or there was a timeout waiting
        for the test of user presence).
    """
    client_data = model.ClientData(model.ClientData.TYP_REGISTRATION, challenge,
                                   self.origin)
    challenge_param = self.InternalSHA256(client_data.GetJson())
    app_param = self.InternalSHA256(app_id)

    for key in registered_keys:
      try:
        # skip non U2F_V2 keys
        if key.version != u'U2F_V2':
          continue
        resp = self.security_key.CmdAuthenticate(challenge_param, app_param,
                                                 key.key_handle, True)
        # check_only mode CmdAuthenticate should always raise some
        # exception
        raise errors.HardwareError('Should Never Happen')

      except errors.TUPRequiredError:
        # This indicates key was valid.  Thus, no need to register
        raise errors.U2FError(errors.U2FError.DEVICE_INELIGIBLE)
      except errors.InvalidKeyHandleError as e:
        # This is the case of a key for a different token, so we just ignore it.
        pass
      except errors.HardwareError as e:
        raise errors.U2FError(errors.U2FError.BAD_REQUEST, e)

    # Now register the new key
    for _ in range(30):
      try:
        resp = self.security_key.CmdRegister(challenge_param, app_param)
        return model.RegisterResponse(resp, client_data)
      except errors.TUPRequiredError as e:
        self.security_key.CmdWink()
        time.sleep(0.5)
      except errors.HardwareError as e:
        raise errors.U2FError(errors.U2FError.BAD_REQUEST, e)

    raise errors.U2FError(errors.U2FError.TIMEOUT)

  def Authenticate(self, app_id, challenge, registered_keys):
    """Authenticates app_id with the security key.

    Executes the U2F authentication/signature flow with the security key.

    Args:
      app_id: The app_id to register the security key against.
      challenge: Server challenge passed to the security key as a bytes object.
      registered_keys: List of keys already registered for this app_id+user.

    Returns:
      SignResponse with client_data, key_handle, and signature_data.  The client
      data is an object, while the signature_data is encoded in FIDO U2F binary
      format.

    Raises:
      U2FError: There was some kind of problem with authentication (e.g.
        there was a timeout while waiting for the test of user presence.)
    """
    client_data = model.ClientData(model.ClientData.TYP_AUTHENTICATION,
                                   challenge, self.origin)
    app_param = self.InternalSHA256(app_id)
    challenge_param = self.InternalSHA256(client_data.GetJson())
    num_invalid_keys = 0
    for key in registered_keys:
      try:
        if key.version != u'U2F_V2':
          continue
        for _ in range(30):
          try:
            resp = self.security_key.CmdAuthenticate(challenge_param, app_param,
                                                     key.key_handle)
            return model.SignResponse(key.key_handle, resp, client_data)
          except errors.TUPRequiredError:
            self.security_key.CmdWink()
            time.sleep(0.5)
      except errors.InvalidKeyHandleError:
        num_invalid_keys += 1
        continue
      except errors.HardwareError as e:
        raise errors.U2FError(errors.U2FError.BAD_REQUEST, e)

    if num_invalid_keys == len(registered_keys):
      # In this case, all provided keys were invalid.
      raise errors.U2FError(errors.U2FError.DEVICE_INELIGIBLE)

    # In this case, the TUP was not pressed.
    raise errors.U2FError(errors.U2FError.TIMEOUT)

  def InternalSHA256(self, string):
    md = hashlib.sha256()
    md.update(string.encode())
    return md.digest()
