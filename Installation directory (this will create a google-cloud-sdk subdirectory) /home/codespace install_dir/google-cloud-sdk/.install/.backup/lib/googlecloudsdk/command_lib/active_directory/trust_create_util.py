# -*- coding: utf-8 -*- #
# Copyright 2019 Google Inc. All Rights Reserved.
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
"""Utilities for creating trusts for domains."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.core.console import console_io


def GetHandshakeSecret():
  """Prompt for user input of handshake secret with target domain."""
  unused_cred = console_io.PromptPassword(
      "Please enter handshake secret with target domain. The secret will not be stored: "
  )
  return unused_cred


def AddExtraTrustCreateArgs(unused_ref, args, request):
  """Allows for the handshake secret to be read from stdin if not specified."""
  if args.IsSpecified("handshake_secret"):
    return request
  secret = GetHandshakeSecret()
  request.attachTrustRequest.trust.trustHandshakeSecret = secret
  return request
