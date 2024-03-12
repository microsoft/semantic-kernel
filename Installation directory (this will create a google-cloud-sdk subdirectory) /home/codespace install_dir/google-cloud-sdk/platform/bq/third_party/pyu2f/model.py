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

"""Implements data model for the library.

This module implements basic data model objects that are necessary
for interacting with the Security Key as well as for implementing
the higher level components of the U2F protocol.
"""

import base64
import json

from pyu2f import errors


class ClientData(object):
  """FIDO U2F ClientData.

  Implements the ClientData object of the FIDO U2F protocol.
  """
  TYP_AUTHENTICATION = 'navigator.id.getAssertion'
  TYP_REGISTRATION = 'navigator.id.finishEnrollment'

  def __init__(self, typ, raw_server_challenge, origin):
    if typ not in [ClientData.TYP_REGISTRATION, ClientData.TYP_AUTHENTICATION]:
      raise errors.InvalidModelError()
    self.typ = typ
    self.raw_server_challenge = raw_server_challenge
    self.origin = origin

  def GetJson(self):
    """Returns JSON version of ClientData compatible with FIDO spec."""

    # The U2F Raw Messages specification specifies that the challenge is encoded
    # with URL safe Base64 without padding encoding specified in RFC 4648.
    # Python does not natively support a paddingless encoding, so we simply
    # remove the padding from the end of the string.
    server_challenge_b64 = base64.urlsafe_b64encode(
        self.raw_server_challenge).decode()
    server_challenge_b64 = server_challenge_b64.rstrip('=')
    return json.dumps({'typ': self.typ,
                       'challenge': server_challenge_b64,
                       'origin': self.origin}, sort_keys=True)

  def __repr__(self):
    return self.GetJson()


class RegisteredKey(object):

  def __init__(self, key_handle, version=u'U2F_V2'):
    self.key_handle = key_handle
    self.version = version


class RegisterResponse(object):

  def __init__(self, registration_data, client_data):
    self.registration_data = registration_data
    self.client_data = client_data


class SignResponse(object):

  def __init__(self, key_handle, signature_data, client_data):
    self.key_handle = key_handle
    self.signature_data = signature_data
    self.client_data = client_data
