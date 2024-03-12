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
"""Describe the EkmConfig."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.cloudkms import base as cloudkms_base
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.kms import resource_args


class Describe(base.DescribeCommand):
  r"""Describe the EkmConfig.

  {command} can be used to retrieve the EkmConfig.

  ## EXAMPLES

  The following command retrieves the EkmConfig in `us-east1` for the current
  project:

  $ {command} --location=us-east1

  The following command retrieves the EkmConfig for its project `foo` and
  location `us-east1`:

    $ {command} --location="projects/foo/locations/us-east1"

  """

  @staticmethod
  def Args(parser):
    resource_args.AddKmsLocationResourceArgForKMS(parser, True, '--location')

  def Run(self, args):
    client = cloudkms_base.GetClientInstance()
    messages = cloudkms_base.GetMessagesModule()
    location_ref = args.CONCEPTS.location.Parse()
    ekm_config_name = 'projects/{0}/locations/{1}/ekmConfig'.format(
        location_ref.projectsId, location_ref.locationsId)

    return client.projects_locations.GetEkmConfig(
        messages.CloudkmsProjectsLocationsGetEkmConfigRequest(
            name=ekm_config_name))
