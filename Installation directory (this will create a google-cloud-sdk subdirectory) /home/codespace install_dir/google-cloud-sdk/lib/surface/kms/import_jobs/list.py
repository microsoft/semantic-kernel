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
"""List the import jobs within a keyring."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import list_pager
from googlecloudsdk.api_lib.cloudkms import base as cloudkms_base
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.kms import flags


class List(base.ListCommand):
  """Lists import jobs within a keyring.

  Lists all import jobs within the given keyring.

  ## EXAMPLES

  The following command lists a maximum of five import jobs within the
  keyring 'fellowship' and location 'global':

    $ {command} --keyring=fellowship --location=global
  """

  @staticmethod
  def Args(parser):
    flags.AddKeyRingFlag(parser, 'import job')
    flags.AddLocationFlag(parser, 'import job')
    parser.display_info.AddFormat("""
        table(
          name,
          state,
          import_method,
          protection_level,
          labels.list())
    """)

  def Run(self, args):
    client = cloudkms_base.GetClientInstance()
    messages = cloudkms_base.GetMessagesModule()

    key_ring_ref = flags.ParseKeyRingName(args)

    request = messages.CloudkmsProjectsLocationsKeyRingsImportJobsListRequest(
        parent=key_ring_ref.RelativeName())

    return list_pager.YieldFromList(
        client.projects_locations_keyRings_importJobs,
        request,
        field='importJobs',
        limit=args.limit,
        batch_size_attribute='pageSize')
