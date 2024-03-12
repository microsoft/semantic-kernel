# -*- coding: utf-8 -*- #
# Copyright 2015 Google LLC. All Rights Reserved.
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
"""Clone Google Cloud Platform git repository."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.source import git
from googlecloudsdk.api_lib.source import sourcerepo
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions as c_exc
from googlecloudsdk.core import log
from googlecloudsdk.core.credentials import store as c_store


@base.ReleaseTracks(base.ReleaseTrack.GA)
class CloneGA(base.Command):
  """Clone a cloud source repository."""

  detailed_help = {
      'DESCRIPTION': """\
        This command clones a git repository from the currently active
        Google Cloud project into the specified directory or into the current
        directory if no target directory is specified.

        Each Google Cloud project can have zero or more git repositories
        associated with it. To see the available repositories, run:

          $ {parent_command} list

        The clone operation configures the local clone to use your gcloud
        credentials to authenticate future git operations. This command emits a
        warning if the cloud source repository is a mirror.
      """,
      'EXAMPLES': """\
      The example commands below show a sample workflow.

        $ gcloud init

        $ {command} REPOSITORY_NAME DIRECTORY_NAME

        $ cd DIRECTORY_NAME
          ... create/edit files and create one or more commits ...

        $ git push origin main
      """,
  }

  @staticmethod
  def Args(parser):
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help=('If provided, prints the command that would be run to standard '
              'out instead of executing it.'))
    parser.add_argument(
        'src', metavar='REPOSITORY_NAME', help='Name of the repository.')
    parser.add_argument(
        'dst',
        metavar='DIRECTORY_NAME',
        nargs='?',
        help=('Directory name for the cloned repo. Defaults to the repository '
              'name.'))

  def UseFullGcloudPath(self, args):
    """Always false because --use-full-gcloud-path argument is not in GA."""
    return False

  def ActionIfMirror(self, project, repo, mirror_url):
    """Prints a warning if the repository is a mirror."""
    message = ('Repository "{repo}" in project "{prj}" is a mirror. Pushing to '
               'this clone will have no effect.  Instead, clone the '
               'mirrored repository directly with \n$ git clone '
               '{url}'.format(repo=repo, prj=project, url=mirror_url))
    log.warning(message)

  def Run(self, args):
    """Clone a GCP repository to the current directory.

    Args:
      args: argparse.Namespace, the arguments this command is run with.

    Returns:
      The path to the new git repository.
    """
    # Ensure that we're logged in.
    c_store.Load(use_google_auth=True)

    res = sourcerepo.ParseRepo(args.src)
    source_handler = sourcerepo.Source()

    repo = source_handler.GetRepo(res)
    if hasattr(repo, 'mirrorConfig') and repo.mirrorConfig:
      mirror_url = repo.mirrorConfig.url
      self.ActionIfMirror(
          project=res.projectsId, repo=args.src, mirror_url=mirror_url)
    # do the actual clone
    git_helper = git.Git(res.projectsId, args.src, uri=repo.url)
    path = git_helper.Clone(
        destination_path=args.dst or args.src,
        dry_run=args.dry_run,
        full_path=self.UseFullGcloudPath(args))
    if path and not args.dry_run:
      log.status.write('Project [{prj}] repository [{repo}] was cloned '
                       'to [{path}].\n'.format(
                           prj=res.projectsId, path=path, repo=args.src))


@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.ALPHA)
class CloneAlpha(CloneGA):
  """Clone a cloud source repository.

  This command clones a git repository for the currently active
  Google Cloud Platform project into the specified directory or into
  the current directory if no target directory is specified.  This command
  gives an error if the cloud source repository is a mirror.

  The clone operation configures the local clone to use your gcloud
  credentials to authenticate future git operations.

  ## EXAMPLES

  The example commands below show a sample workflow.

    $ gcloud init
    $ {command} REPOSITORY_NAME DIRECTORY_NAME
    $ cd DIRECTORY_NAME
    ... create/edit files and create one or more commits ...
    $ git push origin main
  """

  @staticmethod
  def Args(parser):
    CloneGA.Args(parser)
    parser.add_argument(
        '--use-full-gcloud-path',
        action='store_true',
        help=
        ('If provided, use the full gcloud path for the git credential.helper. '
         'Using the full path means that gcloud does not need to be in '
         'the path for future git operations on the repository.'))

  def UseFullGcloudPath(self, args):
    """Use value of --use-full-gcloud-path argument in beta and alpha."""
    return args.use_full_gcloud_path

  def ActionIfMirror(self, project, repo, mirror_url):
    """Raises an exception if the repository is a mirror."""
    message = ('Repository "{repo}" in project "{prj}" is a mirror. Clone the '
               'mirrored repository directly with \n$ git clone '
               '{url}'.format(repo=repo, prj=project, url=mirror_url))
    raise c_exc.InvalidArgumentException('REPOSITORY_NAME', message)
