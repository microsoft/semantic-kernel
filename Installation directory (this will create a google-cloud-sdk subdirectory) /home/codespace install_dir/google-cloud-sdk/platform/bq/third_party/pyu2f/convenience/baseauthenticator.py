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

"""Interface to handle end to end flow of U2F signing."""
import sys


class BaseAuthenticator(object):
  """Interface to handle end to end flow of U2F signing."""

  def Authenticate(self, app_id, challenge_data,
                   print_callback=sys.stderr.write):
    """Authenticates app_id with a security key.

    Executes the U2F authentication/signature flow with a security key.

    Args:
      app_id: The app_id to register the security key against.
      challenge_data: List of dictionaries containing a RegisteredKey ('key')
        and the raw challenge data ('challenge') for this key.
      print_callback: Callback to print a message to the user. The callback
        function takes one argument--the message to display.

    Returns:
      A dictionary with the following fields:
        'clientData': url-safe base64 encoded ClientData JSON signed by the key.
        'signatureData': url-safe base64 encoded signature.
        'applicationId': application id.
        'keyHandle': url-safe base64 encoded handle of the key used to sign.

    Raises:
      U2FError: There was some kind of problem with registration (e.g.
        the device was already registered or there was a timeout waiting
        for the test of user presence).
    """
    raise NotImplementedError

  def IsAvailable(self):
    """Indicates whether the authenticator implementation is available to sign.

    The caller should not call Authenticate() if IsAvailable() returns False

    Returns:
      True if the authenticator is available to sign and False otherwise.

    """
    raise NotImplementedError
