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

"""Exceptions that can be raised by the pyu2f library.

All exceptions that can be raised by the pyu2f library.  Most of these
are internal coditions, but U2FError and NoDeviceFoundError are public
errors that clients should expect to handle.
"""


class NoDeviceFoundError(Exception):
  pass


class U2FError(Exception):
  OK = 0
  OTHER_ERROR = 1
  BAD_REQUEST = 2
  CONFIGURATION_UNSUPPORTED = 3
  DEVICE_INELIGIBLE = 4
  TIMEOUT = 5

  def __init__(self, code, cause=None):
    self.code = code
    if cause:
      self.cause = cause
    super(U2FError, self).__init__("U2F Error code: %d (cause: %s)" %
                                   (code, str(cause)))


class HidError(Exception):
  """Errors in the hid usb transport protocol."""
  pass


class InvalidPacketError(HidError):
  pass


class HardwareError(Exception):
  """Errors in the security key hardware that are transport independent."""
  pass


class InvalidRequestError(HardwareError):
  pass


class ApduError(HardwareError):

  def __init__(self, sw1, sw2):
    self.sw1 = sw1
    self.sw2 = sw2
    super(ApduError, self).__init__("Device returned status: %d %d" %
                                    (sw1, sw2))


class TUPRequiredError(HardwareError):
  pass


class InvalidKeyHandleError(HardwareError):
  pass


class UnsupportedVersionException(Exception):
  pass


class InvalidCommandError(Exception):
  pass


class InvalidResponseError(Exception):
  pass


class InvalidModelError(Exception):
  pass


class OsHidError(Exception):
  pass


class PluginError(Exception):
  pass
