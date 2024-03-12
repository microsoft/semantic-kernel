# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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
"""API helpers for interacting with attestations."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import encoding
from googlecloudsdk.api_lib.container.binauthz import apis


class Client(object):
  """A client for interacting with attestations."""

  def __init__(self, api_version=None):
    self.client = apis.GetClientInstance(api_version)
    self.messages = apis.GetMessagesModule(api_version)
    self.api_version = api_version

  def Test(self, occurrence, attestor_ref):
    """Validates a v1 Occurrence using the TestAttestationOccurrence RPC endpoint."""
    # The AttestationOccurrence being passed in is an instance of the message
    # type from the Container Analysis API but the
    # TestAttestationOccurrenceRequest method generated in the Binary
    # Authorization API requires the Binauthz generated version of the type.
    binauthz_attestation = encoding.JsonToMessage(
        self.messages.AttestationOccurrence,
        encoding.MessageToJson(occurrence.attestation))
    test_attestation_request = self.messages.ValidateAttestationOccurrenceRequest(
        attestation=binauthz_attestation,
        occurrenceNote=occurrence.noteName,
        occurrenceResourceUri=occurrence.resourceUri,
    )
    validation_request = self.messages.BinaryauthorizationProjectsAttestorsValidateAttestationOccurrenceRequest(
        attestor=attestor_ref.RelativeName(),
        validateAttestationOccurrenceRequest=test_attestation_request)
    validation_response = self.client.projects_attestors.ValidateAttestationOccurrence(
        validation_request)

    return validation_response
