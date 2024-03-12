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

"""Convenience class for U2F signing with local security keys."""
import six
import base64
import sys

from pyu2f import errors
from pyu2f import u2f
from pyu2f.convenience import baseauthenticator


class LocalAuthenticator(baseauthenticator.BaseAuthenticator):
  """Authenticator wrapper around the native python u2f implementation."""

  def __init__(self, origin):
    self.origin = origin

  def Authenticate(self, app_id, challenge_data,
                   print_callback=sys.stderr.write):
    """See base class."""
    # If authenticator is not plugged in, prompt
    try:
      device = u2f.GetLocalU2FInterface(origin=self.origin)
    except errors.NoDeviceFoundError:
      print_callback('Please insert your security key and press enter...')
      six.moves.input()
      device = u2f.GetLocalU2FInterface(origin=self.origin)

    print_callback('Please touch your security key.\n')

    for challenge_item in challenge_data:
      raw_challenge = challenge_item['challenge']
      key = challenge_item['key']

      try:
        result = device.Authenticate(app_id, raw_challenge, [key])
      except errors.U2FError as e:
        if e.code == errors.U2FError.DEVICE_INELIGIBLE:
          continue
        else:
          raise

      client_data = self._base64encode(result.client_data.GetJson().encode())
      signature_data = self._base64encode(result.signature_data)
      key_handle = self._base64encode(result.key_handle)

      return {
          'clientData': client_data,
          'signatureData': signature_data,
          'applicationId': app_id,
          'keyHandle': key_handle,
      }

    raise errors.U2FError(errors.U2FError.DEVICE_INELIGIBLE)

  def IsAvailable(self):
    """See base class."""
    return True

  def _base64encode(self, bytes_data):
      """Helper method to base64 encode and return str result."""
      return base64.urlsafe_b64encode(bytes_data).decode()
