# -*- coding: utf-8 -*- #
# Copyright 2021 Google Inc. All Rights Reserved.
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
"""`gcloud dataplex environments create` command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.dataplex import environment
from googlecloudsdk.api_lib.dataplex import util as dataplex_util
from googlecloudsdk.api_lib.util import exceptions as gcloud_exception
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.dataplex import resource_args
from googlecloudsdk.command_lib.util.args import labels_util
from googlecloudsdk.core import log


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.GA)
class Create(base.Command):
  """Create a Dataplex Environment."""

  detailed_help = {
      'EXAMPLES':
          """\

          To create a Dataplex Environment `test-environment`  within lake `test-lake` in
          location `us-central1` inside project `test-project` , run:

            $ {command} test-environment  --project=test-project --location=us-central1 --lake=test-lake  --os-image-version=1.0

          To know about the other required arguments to create an environment run:

            $ gcloud dataplex environment create --help

          """,
  }

  @staticmethod
  def Args(parser):
    resource_args.AddEnvironmentResourceArg(parser,
                                            'to create a Environment to.')
    parser.add_argument(
        '--description', required=False, help='Description of the Environment')
    parser.add_argument(
        '--display-name',
        required=False,
        help='Display Name of the Environment')
    infrastructure_spec = parser.add_group(
        required=True,
        help='Configuration for the underlying infrastructure used to run workloads.'
    )
    compute_resources = infrastructure_spec.add_group(
        help='Compute resources associated with the analyze interactive workloads.'
    )
    compute_resources.add_argument(
        '--compute-disk-size-gb',
        type=int,
        default=100,
        required=False,
        help='Size in GB of the disk. Default is 100 GB.')
    compute_resources.add_argument(
        '--compute-node-count',
        type=int,
        default=0,
        required=False,
        help='Total number of worker nodes in the cluster.')
    compute_resources.add_argument(
        '--compute-max-node-count',
        type=int,
        default=0,
        required=False,
        help='Maximum number of configurable nodes.')
    os_image_runtime = infrastructure_spec.add_group(
        required=True, help='Software Runtime Configuration to run Analyze.')
    os_image_runtime.add_argument(
        '--os-image-version', required=True, help='Dataplex Image version.')
    os_image_runtime.add_argument(
        '--os-image-java-libraries',
        default=[],
        metavar='OS_IMAGE_JAVA_LIBRARIES',
        type=arg_parsers.ArgList(),
        required=False,
        help='List of Java jars to be included in the runtime environment. Valid input includes Cloud Storage URIs to Jar binaries. For example, gs://bucket-name/my/path/to/file.jar'
    )
    os_image_runtime.add_argument(
        '--os-image-python-packages',
        default=[],
        metavar='OS_IMAGE_PYTHON_PACKAGES',
        type=arg_parsers.ArgList(),
        required=False,
        help='A list of python packages to be installed. Valid formats include Cloud Storage URI to a PIP installable library. For example, gs://bucket-name/my/path/to/lib.tar.gz'
    )
    os_image_runtime.add_argument(
        '--os-image-properties',
        metavar='OS_IMAGE_PROPERTIES',
        type=arg_parsers.ArgDict(),
        required=False,
        help='Override to common configuration of open source components installed on the Dataproc cluster. The properties to set on daemon config files. Property keys are specified in `prefix:property` format.'
    )
    session_spec = parser.add_group(
        help='Configuration for sessions created for the environment to be created.'
    )
    session_spec.add_argument(
        '--session-max-idle-duration',
        required=False,
        help='The idle time configuration of the session. The session will be auto-terminated at the end of this period.'
    )
    session_spec.add_argument(
        '--session-enable-fast-startup',
        action='store_true',
        required=False,
        default=False,
        help='Enables fast startup. This causes sessions to be pre-created and available for faster startup to enable interactive exploration use-cases.'
    )
    async_group = parser.add_group(
        mutex=True,
        required=False,
        help='At most one of --async | --validate-only can be specified.')
    async_group.add_argument(
        '--validate-only',
        action='store_true',
        default=False,
        help='Validate the create action, but don\'t actually perform it.')
    base.ASYNC_FLAG.AddToParser(async_group)
    labels_util.AddCreateLabelsFlags(parser)

  @gcloud_exception.CatchHTTPErrorRaiseHTTPException(
      'Status code: {status_code}. {status_message}.')
  def Run(self, args):
    environment_ref = args.CONCEPTS.environment.Parse()
    dataplex_client = dataplex_util.GetClientInstance()
    create_req_op = dataplex_client.projects_locations_lakes_environments.Create(
        dataplex_util.GetMessageModule(
        ).DataplexProjectsLocationsLakesEnvironmentsCreateRequest(
            environmentId=environment_ref.Name(),
            parent=environment_ref.Parent().RelativeName(),
            validateOnly=args.validate_only,
            googleCloudDataplexV1Environment=environment
            .GenerateEnvironmentForCreateRequest(args)))

    validate_only = getattr(args, 'validate_only', False)
    if validate_only:
      log.status.Print('Validation complete.')
      return

    async_ = getattr(args, 'async_', False)
    if not async_:
      response = environment.WaitForOperation(create_req_op)
      log.CreatedResource(
          response.name,
          details='Environment created in lake [{0}] in project [{1}] with location [{2}]'
          .format(environment_ref.lakesId, environment_ref.projectsId,
                  environment_ref.locationsId))
      return response

    log.status.Print(
        'Creating environment with path [{0}] and operation [{1}].'.format(
            environment_ref, create_req_op.name))
    return create_req_op
