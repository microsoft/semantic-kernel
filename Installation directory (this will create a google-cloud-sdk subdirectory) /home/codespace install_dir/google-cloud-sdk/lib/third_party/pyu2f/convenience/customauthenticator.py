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

"""Class to offload the end to end flow of U2F signing."""

import base64
import hashlib
import json
import os
import struct
import subprocess
import sys

from pyu2f import errors
from pyu2f import model
from pyu2f.convenience import baseauthenticator

SK_SIGNING_PLUGIN_ENV_VAR = 'SK_SIGNING_PLUGIN'
U2F_SIGNATURE_TIMEOUT_SECONDS = 5

SK_SIGNING_PLUGIN_NO_ERROR = 0
SK_SIGNING_PLUGIN_TOUCH_REQUIRED = 0x6985
SK_SIGNING_PLUGIN_WRONG_DATA = 0x6A80


class CustomAuthenticator(baseauthenticator.BaseAuthenticator):
  """Offloads U2F signing to a pluggable command-line tool.

  Offloads U2F signing to a signing plugin which takes the form of a
  command-line tool. The command-line tool is configurable via the
  SK_SIGNING_PLUGIN environment variable.

  The signing plugin should implement the following interface:

  Communication occurs over stdin/stdout, and messages are both sent and
  received in the form:

  [4 bytes - payload size (little-endian)][variable bytes - json payload]

  Signing Request JSON
  {
    "type": "sign_helper_request",
    "signData": [{
        "keyHandle": <url-safe base64-encoded key handle>,
        "appIdHash": <url-safe base64-encoded SHA-256 hash of application ID>,
        "challengeHash": <url-safe base64-encoded SHA-256 hash of ClientData>,
        "version": U2F protocol version (usually "U2F_V2")
        },...],
    "timeoutSeconds": <security key touch timeout>
  }

  Signing Response JSON
  {
    "type": "sign_helper_reply",
    "code": <result code>.
    "errorDetail": <text description of error>,
    "responseData": {
      "appIdHash": <url-safe base64-encoded SHA-256 hash of application ID>,
      "challengeHash": <url-safe base64-encoded SHA-256 hash of ClientData>,
      "keyHandle": <url-safe base64-encoded key handle>,
      "version": <U2F protocol version>,
      "signatureData": <url-safe base64-encoded signature>
    }
  }

  Possible response error codes are:

    NoError            = 0
    UnknownError       = -127
    TouchRequired      = 0x6985
    WrongData          = 0x6a80
  """

  def __init__(self, origin):
    self.origin = origin

  def Authenticate(self, app_id, challenge_data,
                   print_callback=sys.stderr.write):
    """See base class."""

    # Ensure environment variable is present
    plugin_cmd = os.environ.get(SK_SIGNING_PLUGIN_ENV_VAR)
    if plugin_cmd is None:
      raise errors.PluginError('{} env var is not set'
                               .format(SK_SIGNING_PLUGIN_ENV_VAR))

    # Prepare input to signer
    client_data_map, signing_input = self._BuildPluginRequest(
        app_id, challenge_data, self.origin)

    # Call plugin
    print_callback('Please insert and touch your security key\n')
    response = self._CallPlugin([plugin_cmd], signing_input)

    # Handle response
    key_challenge_pair = (response['keyHandle'], response['challengeHash'])
    client_data_json = client_data_map[key_challenge_pair]
    client_data = client_data_json.encode()
    return self._BuildAuthenticatorResponse(app_id, client_data, response)

  def IsAvailable(self):
    """See base class."""
    return os.environ.get(SK_SIGNING_PLUGIN_ENV_VAR) is not None

  def _BuildPluginRequest(self, app_id, challenge_data, origin):
    """Builds a JSON request in the form that the plugin expects."""
    client_data_map = {}
    encoded_challenges = []
    app_id_hash_encoded = self._Base64Encode(self._SHA256(app_id))
    for challenge_item in challenge_data:
      key = challenge_item['key']
      key_handle_encoded = self._Base64Encode(key.key_handle)

      raw_challenge = challenge_item['challenge']

      client_data_json = model.ClientData(
          model.ClientData.TYP_AUTHENTICATION,
          raw_challenge,
          origin).GetJson()

      challenge_hash_encoded = self._Base64Encode(
          self._SHA256(client_data_json))

      # Populate challenges list
      encoded_challenges.append({
          'appIdHash': app_id_hash_encoded,
          'challengeHash': challenge_hash_encoded,
          'keyHandle': key_handle_encoded,
          'version': key.version,
      })

      # Populate ClientData map
      key_challenge_pair = (key_handle_encoded, challenge_hash_encoded)
      client_data_map[key_challenge_pair] = client_data_json

    signing_request = {
        'type': 'sign_helper_request',
        'signData': encoded_challenges,
        'timeoutSeconds': U2F_SIGNATURE_TIMEOUT_SECONDS,
        'localAlways': True
    }

    return client_data_map, json.dumps(signing_request)

  def _BuildAuthenticatorResponse(self, app_id, client_data, plugin_response):
    """Builds the response to return to the caller."""
    encoded_client_data = self._Base64Encode(client_data)
    signature_data = str(plugin_response['signatureData'])
    key_handle = str(plugin_response['keyHandle'])

    response = {
        'clientData': encoded_client_data,
        'signatureData': signature_data,
        'applicationId': app_id,
        'keyHandle': key_handle,
    }
    return response

  def _CallPlugin(self, cmd, input_json):
    """Calls the plugin and validates the response."""
    # Calculate length of input
    input_length = len(input_json)
    length_bytes_le = struct.pack('<I', input_length)
    request = length_bytes_le + input_json.encode()

    # Call plugin
    sign_process = subprocess.Popen(cmd,
                                    stdin=subprocess.PIPE,
                                    stdout=subprocess.PIPE)

    stdout = sign_process.communicate(request)[0]
    exit_status = sign_process.wait()

    # Parse and validate response size
    response_len_le = stdout[:4]
    response_len = struct.unpack('<I', response_len_le)[0]
    response = stdout[4:]
    if response_len != len(response):
      raise errors.PluginError(
          'Plugin response length {} does not match data {} (exit_status={})'
          .format(response_len, len(response), exit_status))

    # Ensure valid json
    try:
      json_response = json.loads(response.decode())
    except ValueError:
      raise errors.PluginError('Plugin returned invalid output (exit_status={})'
                               .format(exit_status))

    # Ensure response type
    if json_response.get('type') != 'sign_helper_reply':
      error_string = 'Plugin returned invalid response type (exit_status={})'.format(exit_status)
      error_detail = json_response.get('errorDetail')
      if (error_detail):
        error_string += '. Additional information:\n' + error_detail
      raise errors.PluginError(error_string)

    # Parse response codes
    result_code = json_response.get('code')
    if result_code is None:
      raise errors.PluginError('Plugin missing result code (exit_status={})'
                               .format(exit_status))

    # Handle errors
    if result_code == SK_SIGNING_PLUGIN_TOUCH_REQUIRED:
      raise errors.U2FError(errors.U2FError.TIMEOUT)
    elif result_code == SK_SIGNING_PLUGIN_WRONG_DATA:
      raise errors.U2FError(errors.U2FError.DEVICE_INELIGIBLE)
    elif result_code != SK_SIGNING_PLUGIN_NO_ERROR:
      raise errors.PluginError(
          'Plugin failed with error {} - {} (exit_status={})'
          .format(result_code,
                  json_response.get('errorDetail'),
                  exit_status))

    # Ensure response data is present
    response_data = json_response.get('responseData')
    if response_data is None:
      raise errors.PluginErrors(
          'Plugin returned output with missing responseData (exit_status={})'
          .format(exit_status))

    return response_data

  def _SHA256(self, string):
    """Helper method to perform SHA256."""
    md = hashlib.sha256()
    md.update(string.encode())
    return md.digest()

  def _Base64Encode(self, bytes_data):
      """Helper method to base64 encode, strip padding, and return str
      result."""
      return base64.urlsafe_b64encode(bytes_data).decode().rstrip('=')
