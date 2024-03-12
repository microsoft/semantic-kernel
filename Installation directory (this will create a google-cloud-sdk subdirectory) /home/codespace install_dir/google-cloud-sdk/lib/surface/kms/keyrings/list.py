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
"""List keyrings within a location."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import list_pager
from googlecloudsdk.api_lib.cloudkms import base as cloudkms_base
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.kms import resource_args


class List(base.ListCommand):
  """List keyrings within a location.

  Lists all keyrings within the given location.

  ## EXAMPLES

  The following command lists a maximum of five keyrings in the location
  `global`:

    $ {command} --location=global --limit=5
  """

  @staticmethod
  def Args(parser):
    resource_args.AddKmsLocationResourceArgForKMS(parser, True, '--location')

    parser.display_info.AddFormat('table(name)')

  def Run(self, args):
    client = cloudkms_base.GetClientInstance()
    messages = cloudkms_base.GetMessagesModule()
    location_ref = args.CONCEPTS.location.Parse()

    request = messages.CloudkmsProjectsLocationsKeyRingsListRequest(
        parent=location_ref.RelativeName())

    return list_pager.YieldFromList(
        client.projects_locations_keyRings,
        request,
        field='keyRings',
        limit=args.limit,
        batch_size_attribute='pageSize')
