# -*- coding: utf-8 -*- #
# Copyright 2023 Google LLC. All Rights Reserved.
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
"""Update the EkmConfig."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.cloudkms import base as cloudkms_base
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.kms import flags
from googlecloudsdk.command_lib.kms import resource_args


class Update(base.UpdateCommand):
  r"""Update the EkmConfig.

  {command} can be used to update the EkmConfig. Applies to all CryptoKeys and
  CryptoKeyVersions with a `protection level` of `external vpc`.

  ## EXAMPLES

  The following command sets the default ekm-connection to `laplace` for its
  project `foo` and location `us-east1`:

    $ {command} --location=us-east1
    --default-ekm-connection="projects/foo/locations/us-east1/ekmConnections/laplace"

  The following command removes the default-ekm-connection in `us-east1` for the
  current project:

  $ {command} --location=us-east1 --default-ekm-connection=""


  """

  @staticmethod
  def Args(parser):
    flags.AddDefaultEkmConnectionFlag(parser)
    resource_args.AddKmsLocationResourceArgForKMS(parser, True, '--location')

  def CreateRequest(self, messages, ec_name, ekm_config):
    ekm_config_to_update = ekm_config
    ekm_config_to_update.defaultEkmConnection = ec_name
    req = messages.CloudkmsProjectsLocationsUpdateEkmConfigRequest(
        name=ekm_config.name, ekmConfig=ekm_config_to_update)

    req.updateMask = 'defaultEkmConnection'

    return req

  def Run(self, args):
    client = cloudkms_base.GetClientInstance()
    messages = cloudkms_base.GetMessagesModule()
    loc_ref = args.CONCEPTS.location.Parse()
    # Currently default_ekm_connection is the only field so it must be specified
    # but it can be an empty string to remove the default ekm connection from
    # the config.
    if args.default_ekm_connection is None:
      raise exceptions.RequiredArgumentException('--default-ekm-connection',
                                                 'Must be specified.')

    # Try to get the ekmConfig and raise an exception if it doesn't exist.
    ekm_config_name = 'projects/{0}/locations/{1}/ekmConfig'.format(
        loc_ref.projectsId, loc_ref.locationsId)
    ekm_config = client.projects_locations.GetEkmConfig(
        messages.CloudkmsProjectsLocationsGetEkmConfigRequest(
            name=ekm_config_name))

    # Make update request
    update_req = self.CreateRequest(messages, args.default_ekm_connection,
                                    ekm_config)

    return client.projects_locations.UpdateEkmConfig(update_req)
