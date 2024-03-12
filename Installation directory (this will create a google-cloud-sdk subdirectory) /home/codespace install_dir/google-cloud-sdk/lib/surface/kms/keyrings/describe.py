# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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
"""Describe a keyring."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.cloudkms import base as cloudkms_base
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.kms import resource_args


class Describe(base.DescribeCommand):
  """Get metadata for a keyring.

  Returns metadata for the given keyring.

  ## EXAMPLES

  The following command returns the metadata for the keyring `towers`
  in the location `us-east1`:

    $ {command} towers --location=us-east1
  """

  @staticmethod
  def Args(parser):
    resource_args.AddKmsKeyringResourceArgForKMS(parser, True, 'keyring')

  def Run(self, args):
    client = cloudkms_base.GetClientInstance()
    messages = cloudkms_base.GetMessagesModule()
    key_ring_ref = args.CONCEPTS.keyring.Parse()
    if not key_ring_ref.Name():
      raise exceptions.InvalidArgumentException('keyring',
                                                'keyring id must be non-empty.')
    return client.projects_locations_keyRings.Get(
        messages.CloudkmsProjectsLocationsKeyRingsGetRequest(
            name=key_ring_ref.RelativeName()))
