# -*- coding: utf-8 -*- #
# Copyright 2022 Google LLC. All Rights Reserved.
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
"""Create a new import job."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.cloudkms import base as cloudkms_base
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.kms import flags
from googlecloudsdk.command_lib.kms import maps


class Create(base.CreateCommand):
  r"""Create a new import job.

  Creates a new import job within the given keyring.

  ## EXAMPLES

  The following command creates a new import job named 'strider' within the
  'fellowship' keyring, and 'us-central1' location:

    $ {command} strider --location=us-central1 \
        --keyring=fellowship --import-method=rsa-oaep-3072-sha256-aes-256 \
        --protection-level=hsm
  """

  @staticmethod
  def Args(parser):
    flags.AddKeyRingFlag(parser, 'import job')
    flags.AddLocationFlag(parser, 'import job')
    flags.AddRequiredProtectionLevelFlag(parser)
    flags.AddRequiredImportMethodFlag(parser)
    flags.AddPositionalImportJobArgument(parser, 'to create')

    parser.display_info.AddCacheUpdater(flags.KeyRingCompleter)

  def _CreateRequest(self, args):
    messages = cloudkms_base.GetMessagesModule()

    if not args.protection_level:
      raise exceptions.ArgumentError(
          '--protection-level needs to be specified when creating an import job'
      )

    if not args.import_method:
      raise exceptions.ArgumentError(
          '--import-method needs to be specified when creating an import job')

    import_job_ref = flags.ParseImportJobName(args)
    parent_ref = flags.ParseParentFromResource(import_job_ref)

    return messages.CloudkmsProjectsLocationsKeyRingsImportJobsCreateRequest(
        parent=parent_ref.RelativeName(),
        importJobId=import_job_ref.Name(),
        importJob=messages.ImportJob(
            protectionLevel=maps.IMPORT_PROTECTION_LEVEL_MAPPER
            .GetEnumForChoice(args.protection_level),
            importMethod=maps.IMPORT_METHOD_MAPPER.GetEnumForChoice(
                args.import_method)))

  def Run(self, args):
    client = cloudkms_base.GetClientInstance()
    return client.projects_locations_keyRings_importJobs.Create(
        self._CreateRequest(args))
