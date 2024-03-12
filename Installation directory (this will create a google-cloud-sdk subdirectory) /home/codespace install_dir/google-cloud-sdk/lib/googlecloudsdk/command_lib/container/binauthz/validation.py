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
"""Functions related to resource validation for Binary Authorization's CLI."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.container.binauthz import attestations
from googlecloudsdk.core import log
from googlecloudsdk.core.console import console_io


def validate_attestation(occurrence,
                         attestor_ref,
                         api_version,
                         action='create'):
  """Returns the passed `image_url` with the scheme replaced.

  Args:
    occurrence: The AttestationOccurrence-kind Occurrence to be validated.
      (grafeas.v1.Occurrence)
    attestor_ref: The Attestor to validate the Attestation against. (Resource)
    api_version: The version of the Binary Authorization API to use. (string)
    action: The name of the action included in the confirmation prompt if the
      Attestation can't be validated. (string)
  """
  client = attestations.Client(api_version)
  validation_response = client.Test(occurrence, attestor_ref)
  if validation_response.result == client.messages.ValidateAttestationOccurrenceResponse.ResultValueValuesEnum.VERIFIED:
    log.info('Attestation was successfully validated')
    return
  elif validation_response.result == client.messages.ValidateAttestationOccurrenceResponse.ResultValueValuesEnum.ATTESTATION_NOT_VERIFIABLE:
    log.warning('Attestation could not be validated! ({})'.format(
        validation_response.denialReason))
  else:
    log.error('Attestation could not be validated! (Reason not provided)')

  console_io.PromptContinue(
      prompt_string='{} Attestation anyway?'.format(action.capitalize()),
      cancel_on_no=True)
