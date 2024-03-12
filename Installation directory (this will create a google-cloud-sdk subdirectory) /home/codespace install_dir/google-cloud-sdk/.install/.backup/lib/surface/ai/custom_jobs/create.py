# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""Command to create a custom job in Vertex AI."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.ai.custom_jobs import client
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.ai import constants
from googlecloudsdk.command_lib.ai import endpoint_util
from googlecloudsdk.command_lib.ai import validation as common_validation
from googlecloudsdk.command_lib.ai.custom_jobs import custom_jobs_util
from googlecloudsdk.command_lib.ai.custom_jobs import flags
from googlecloudsdk.command_lib.ai.custom_jobs import validation
from googlecloudsdk.command_lib.util.args import labels_util
from googlecloudsdk.core import log
from googlecloudsdk.core import properties

_JOB_CREATION_DISPLAY_MESSAGE_TEMPLATE = """\
CustomJob [{job_name}] is submitted successfully.

Your job is still active. You may view the status of your job with the command

  $ {command_prefix} ai custom-jobs describe {job_name}

or continue streaming the logs with the command

  $ {command_prefix} ai custom-jobs stream-logs {job_name}\
"""


@base.ReleaseTracks(base.ReleaseTrack.GA)
class CreateGA(base.CreateCommand):
  """Create a new custom job.

  This command will attempt to run the custom job immediately upon creation.

  ## EXAMPLES

  To create a job under project ``example'' in region
  ``us-central1'', run:

    $ {command} --region=us-central1 --project=example
    --worker-pool-spec=replica-count=1,machine-type='n1-highmem-2',container-image-uri='gcr.io/ucaip-test/ucaip-training-test'
    --display-name=test
  """

  _version = constants.GA_VERSION

  @staticmethod
  def Args(parser):
    flags.AddCreateCustomJobFlags(parser, constants.GA_VERSION)

  def _DisplayResult(self, response):
    cmd_prefix = 'gcloud'
    if self.ReleaseTrack().prefix:
      cmd_prefix += ' ' + self.ReleaseTrack().prefix

    log.status.Print(
        _JOB_CREATION_DISPLAY_MESSAGE_TEMPLATE.format(
            job_name=response.name, command_prefix=cmd_prefix))

  def _PrepareJobSpec(self, args, api_client, project):
    job_config = api_client.ImportResourceMessage(
        args.config, 'CustomJobSpec') if args.config else api_client.GetMessage(
            'CustomJobSpec')()

    validation.ValidateCreateArgs(args, job_config, self._version)
    worker_pool_specs = list(
        custom_jobs_util.UpdateWorkerPoolSpecsIfLocalPackageRequired(
            args.worker_pool_spec or [], args.display_name, project))

    job_spec = custom_jobs_util.ConstructCustomJobSpec(
        api_client,
        base_config=job_config,
        worker_pool_specs=worker_pool_specs,
        network=args.network,
        service_account=args.service_account,
        enable_web_access=args.enable_web_access,
        enable_dashboard_access=args.enable_dashboard_access,
        args=args.args,
        command=args.command,
        python_package_uri=args.python_package_uris,
        persistent_resource_id=(args.persistent_resource_id
                                if self._version == constants.BETA_VERSION
                                else None))

    return job_spec

  def Run(self, args):
    project = properties.VALUES.core.project.GetOrFail()
    region_ref = args.CONCEPTS.region.Parse()
    region = region_ref.AsDict()['locationsId']
    validation.ValidateRegion(region)

    with endpoint_util.AiplatformEndpointOverrides(
        version=self._version, region=region):
      api_client = client.CustomJobsClient(version=self._version)
      job_spec = self._PrepareJobSpec(args, api_client, project)
      labels = labels_util.ParseCreateArgs(
          args,
          api_client.CustomJobMessage().LabelsValue)

      response = api_client.Create(
          parent=region_ref.RelativeName(),
          display_name=args.display_name,
          job_spec=job_spec,
          kms_key_name=common_validation.GetAndValidateKmsKey(args),
          labels=labels)
      self._DisplayResult(response)
      return response


@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.ALPHA)
class CreatePreGA(CreateGA):
  """Create a new custom job.

  This command will attempt to run the custom job immediately upon creation.

  ## EXAMPLES

  To create a job under project ``example'' in region
  ``us-central1'', run:

    $ {command} --region=us-central1 --project=example
    --worker-pool-spec=replica-count=1,machine-type='n1-highmem-2',container-image-uri='gcr.io/ucaip-test/ucaip-training-test'
    --display-name=test
  """
  _version = constants.BETA_VERSION

  @staticmethod
  def Args(parser):
    flags.AddCreateCustomJobFlags(parser, constants.BETA_VERSION)
