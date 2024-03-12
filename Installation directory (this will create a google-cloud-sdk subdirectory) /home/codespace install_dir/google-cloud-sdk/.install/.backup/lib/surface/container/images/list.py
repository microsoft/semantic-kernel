# -*- coding: utf-8 -*- #
# Copyright 2016 Google LLC. All Rights Reserved.
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
"""List images command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from containerregistry.client.v2_2 import docker_image
from googlecloudsdk.api_lib.container.images import util
from googlecloudsdk.calliope import base
from googlecloudsdk.core import log
from googlecloudsdk.core import properties


class List(base.ListCommand):
  """List existing images."""

  detailed_help = {
      'DESCRIPTION':
          """\
          The container images list command of gcloud lists metadata about
          existing container images in a specified repository. Repositories
          must be hosted by the Google Container Registry.
      """,
      'EXAMPLES':
          """\
          List the images in a specified repository:

            $ {command} --repository=gcr.io/myproject

          List the images in the default repository:

            $ {command}

          List images with names prefixed with 'test-project':

            $ {command} --filter="name:test-project"

      """,
  }

  @staticmethod
  def Args(parser):
    """Register flags for this command.

    Args:
      parser: An argparse.ArgumentParser-like object. It is mocked out in order
        to capture some information, but behaves like an ArgumentParser.
    """
    parser.add_argument(
        '--repository',
        required=False,
        help=('The name of the repository. Format: *.gcr.io/repository. '
              'Defaults to gcr.io/<project>, for the active project.'))
    parser.display_info.AddFormat('table(name)')

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      Some value that we want to have printed later.

    Raises:
      exceptions.Error: If the repository could not be found, or access was
      denied.
      docker_http.V2DiagnosticException: Any other error occurred while
      accessing GCR.
    """
    repository_arg = args.repository
    self._epilog = None
    if not repository_arg:
      project_id = properties.VALUES.core.project.Get(required=True)
      # Handle domain-scoped projects...
      project_id = project_id.replace(':', '/', 1)
      repository_arg = 'gcr.io/{0}'.format(project_id)
      self._epilog = 'Only listing images in {0}. '.format(repository_arg)
      self._epilog += 'Use --repository to list images in other repositories.'

    # Throws if invalid.
    repository = util.ValidateRepositoryPath(repository_arg)

    def _DisplayName(c):
      """Display the fully-qualified name."""
      return '{0}/{1}'.format(repository, c)

    http_obj = util.Http()
    with util.WrapExpectedDockerlessErrors(repository):
      with docker_image.FromRegistry(
          basic_creds=util.CredentialProvider(),
          name=repository,
          transport=http_obj) as r:
        images = [{'name': _DisplayName(c)} for c in r.children()]
        return images

  def Epilog(self, resources_were_displayed=True):
    super(List, self).Epilog(resources_were_displayed)

    if self._epilog:
      log.status.Print(self._epilog)
