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

"""Register gcloud as a Docker credential helper."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import json

from googlecloudsdk.calliope import base
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core.console import console_io
from googlecloudsdk.core.docker import credential_utils as cred_utils
from googlecloudsdk.core.util import files as file_utils


class ConfigureDockerError(exceptions.Error):
  """General command error class."""


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.GA)
class ConfigureDocker(base.Command):
  # pylint: disable=line-too-long
  r"""Register `gcloud` as a Docker credential helper.

  {command} adds the Docker `credHelper` entry to Docker's configuration file,
  or creates the file if it doesn't exist. This will register `gcloud` as the
  credential helper for all Google-supported Docker registries. If the Docker
  configuration already contains a `credHelper` entry, it will be overwritten.

  Note: `docker` and `gcloud` need to be on the same system `PATH` to work
  correctly.

  Note: This command will not work for `docker` installed via Snap, as the
  `docker` snap package does not currently provide an interface for credential
  helpers.

  For more details on Docker registries, see
  [](https://docs.docker.com/registry/).

  For more details on how to authenticate to Google Container Registry using
  this command, see
  [](https://cloud.google.com/container-registry/docs/advanced-authentication#gcloud-helper).

  For more details on Google Container Registry's standalone credential helpers,
  see [](https://github.com/GoogleCloudPlatform/docker-credential-gcr).

  For more details on Docker credential helpers, see
  [](https://docs.docker.com/engine/reference/commandline/login/#credential-helpers).


  ## EXAMPLES

  To configure docker authentication after logging into gcloud, run:

    $ {command}

  To configure docker authentication with Container Registry, e.g., `gcr.io`,
  run:

    $ {command} gcr.io
  """
  # pylint: enable=line-too-long

  def DockerCredentialGcloudExists(self):
    return file_utils.SearchForExecutableOnPath(
        'docker-credential-gcloud') or file_utils.SearchForExecutableOnPath(
            'docker-credential-gcloud.cmd')

  def DockerExists(self):
    return file_utils.SearchForExecutableOnPath(
        'docker') or file_utils.SearchForExecutableOnPath('docker.exe')

  @staticmethod
  def Args(parser):
    """Set args for configure-docker."""
    parser.add_argument(
        'registries',
        nargs='?',
        help='The comma-separated list of registries to configure the credential'
        ' helper for. Container Registry is a service for storing private '
        'container images. For available registries, see '
        '[](https://cloud.google.com/container-registry/docs/pushing-and-pulling#add-registry).'
    )
    parser.add_argument(
        '--include-artifact-registry',
        action='store_true',
        help='Whether to include all Artifact Registry domains.',
        hidden=True)

  def Run(self, args):
    """Run the configure-docker command."""
    if not self.DockerCredentialGcloudExists():
      log.warning('`docker-credential-gcloud` not in system PATH.\n'
                  'gcloud\'s Docker credential helper can be configured but '
                  'it will not work until this is corrected.')

    current_config = cred_utils.Configuration.ReadFromDisk()

    if self.DockerExists():
      if not current_config.SupportsRegistryHelpers():
        raise ConfigureDockerError(
            'Invalid Docker version: The version of your Docker client is '
            '[{}]; version [{}] or higher is required to support Docker '
            'credential helpers.'.format(
                current_config.DockerVersion(),
                cred_utils.MIN_DOCKER_CONFIG_HELPER_VERSION))
    else:
      log.warning(
          '`docker` not in system PATH.\n'
          '`docker` and `docker-credential-gcloud` need to be in the same PATH '
          'in order to work correctly together.\n'
          'gcloud\'s Docker credential helper can be configured but '
          'it will not work until this is corrected.')

    current_helpers = current_config.GetRegisteredCredentialHelpers()
    current_helper_map = {}
    if current_helpers:
      log.warning('Your config file at [{0}] contains these credential helper '
                  'entries:\n\n{1}'.format(
                      current_config.path,
                      json.dumps(current_helpers, indent=2)))
      current_helper_map = current_helpers[cred_utils.CREDENTIAL_HELPER_KEY]

    # Use the value from the argument, otherwise the default list.
    if args.registries:
      log.status.Print('Adding credentials for: {0}'.format(args.registries))
      registries = filter(self.CheckValidRegistry, args.registries.split(','))
      new_helpers = cred_utils.GetGcloudCredentialHelperConfig(registries)
    else:
      # If include-artifact-registry is set, add all GCR and AR repos, otherwise
      # just GCR repos.
      if args.include_artifact_registry:
        log.status.Print('Adding credentials for all GCR and AR repositories.')
      else:
        log.status.Print('Adding credentials for all GCR repositories.')
      log.warning('A long list of credential helpers may cause delays running '
                  '\'docker build\'. We recommend passing the registry name to '
                  'configure only the registry you are using.')
      new_helpers = cred_utils.GetGcloudCredentialHelperConfig(
          None, args.include_artifact_registry)

    # Merge in the new settings so that existing configs are preserved.
    merged_helper_map = current_helper_map.copy()
    merged_helper_map.update(new_helpers[cred_utils.CREDENTIAL_HELPER_KEY])

    if current_helper_map == merged_helper_map:
      log.status.Print(
          'gcloud credential helpers already registered correctly.')
      return

    merged_helpers = {cred_utils.CREDENTIAL_HELPER_KEY: merged_helper_map}
    console_io.PromptContinue(
        message='After update, the following will be written to your Docker '
        'config file located at [{0}]:\n {1}'.format(
            current_config.path, json.dumps(merged_helpers, indent=2)),
        cancel_on_no=True)

    current_config.RegisterCredentialHelpers(merged_helper_map)
    log.status.Print('Docker configuration file updated.')

  def CheckValidRegistry(self, registry):
    if registry not in cred_utils.SupportedRegistries():
      log.warning('{0} is not a supported registry'.format(registry))
      return False
    return True
