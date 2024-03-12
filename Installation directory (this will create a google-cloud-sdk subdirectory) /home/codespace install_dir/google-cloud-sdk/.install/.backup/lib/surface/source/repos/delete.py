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
"""Delete Google Cloud Platform git repository."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.source import sourcerepo
from googlecloudsdk.calliope import actions
from googlecloudsdk.calliope import base
from googlecloudsdk.core import log
from googlecloudsdk.core.console import console_io


@base.ReleaseTracks(base.ReleaseTrack.GA, base.ReleaseTrack.ALPHA,
                    base.ReleaseTrack.BETA)
class Delete(base.DeleteCommand):
  """Delete a cloud source repository.

  This command deletes a named git repository from the currently
  active Google Cloud Platform project.

  ## EXAMPLES

  To delete a named repository in the current project issue the
  following commands:

    $ gcloud init

    $ {command} REPOSITORY_NAME

  """

  @staticmethod
  def Args(parser):
    parser.add_argument('repository_name', help='Name of the repository.')
    parser.add_argument(
        '--force',
        action=actions.DeprecationAction(
            '--force',
            error=('The {flag_name} option has been removed; use --quiet '
                   'to suppress prompting.'),
            removed=True,
            action='store_true'),
        help='If provided, skip the delete confirmation prompt.')

  def Run(self, args):
    """Delete a named GCP repository in the current project.

    Args:
      args: argparse.Namespace, the arguments this command is run with.

    Returns:
      The path to the deleted git repository.

    Raises:
      sourcerepo.RepoResourceError: on resource initialization errors.
      apitools.base.py.exceptions.HttpError: on request errors.
    """
    res = sourcerepo.ParseRepo(args.repository_name)
    delete_warning = ('If {repo} is deleted, the name cannot be reused for up '
                      'to seven days.'.format(repo=res.Name()))
    prompt_string = ('Delete "{repo}" in project "{prj}"'.format(
        repo=res.Name(), prj=res.projectsId))
    if console_io.PromptContinue(
        message=delete_warning, prompt_string=prompt_string, default=True):
      sourcerepo_handler = sourcerepo.Source()
      # This returns an empty proto buffer as a response, so there's
      # nothing to return.
      sourcerepo_handler.DeleteRepo(res)
      log.DeletedResource(res.Name())
      return res.Name()
