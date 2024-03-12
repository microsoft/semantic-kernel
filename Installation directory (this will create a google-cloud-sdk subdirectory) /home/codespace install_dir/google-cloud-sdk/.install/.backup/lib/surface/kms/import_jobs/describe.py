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
"""Describe a version."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.cloudkms import base as cloudkms_base
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.kms import exceptions as kms_exceptions
from googlecloudsdk.command_lib.kms import flags
from googlecloudsdk.core import log
from googlecloudsdk.core.util import files


class Describe(base.DescribeCommand):
  r"""Get metadata for a given import job.

  Returns metadata for the given import job.

  The optional flag `--attestation-file` specifies file to write the attestation
  into. The attestation enables the user to verify the integrity and provenance
  of the key. See https://cloud.google.com/kms/docs/attest-key for more
  information about attestations.

  ## EXAMPLES

  The following command returns metadata for import job 'strider' within the
  keyring 'fellowship' in the location 'us-central1':

    $ {command} strider --keyring=fellowship --location=us-central1

  For import jobs with protection level `HSM`, use the `--attestation-file`
  flag to save the attestation to a local file.

    $ {command} strider --keyring=fellowship --location=us-central1 \
        --attestation-file=path/to/attestation.dat
  """

  @staticmethod
  def Args(parser):
    flags.AddKeyRingFlag(parser, 'import job')
    flags.AddLocationFlag(parser, 'import job')
    flags.AddPositionalImportJobArgument(parser, 'to describe')
    flags.AddAttestationFileFlag(parser)

  def Run(self, args):
    client = cloudkms_base.GetClientInstance()
    messages = cloudkms_base.GetMessagesModule()

    import_job_ref = flags.ParseImportJobName(args)
    if not import_job_ref.Name():
      raise exceptions.InvalidArgumentException(
          'import_job', 'import job id must be non-empty.')
    import_job = client.projects_locations_keyRings_importJobs.Get(  # pylint: disable=line-too-long
        messages.CloudkmsProjectsLocationsKeyRingsImportJobsGetRequest(
            name=import_job_ref.RelativeName()))

    # Raise exception if --attestation-file is provided for software
    # import jobs.
    if (args.attestation_file and import_job.protectionLevel !=
        messages.ImportJob.ProtectionLevelValueValuesEnum.HSM):
      raise kms_exceptions.ArgumentError(
          'Attestations are only available for HSM import jobs.')

    if (args.attestation_file and import_job.state == messages.ImportJob
        .StateValueValuesEnum.PENDING_GENERATION):
      raise kms_exceptions.ArgumentError(
          'The attestation is unavailable until the import job is generated.')

    if args.attestation_file and import_job.attestation is not None:
      try:
        log.WriteToFileOrStdout(
            args.attestation_file,
            import_job.attestation.content,
            overwrite=True,
            binary=True)
      except files.Error as e:
        raise exceptions.BadFileException(e)

    if import_job.attestation is not None:
      # Suppress the attestation content in the printed output. Users can use
      # --attestation-file to obtain it, instead.
      import_job.attestation.content = None

    return import_job
