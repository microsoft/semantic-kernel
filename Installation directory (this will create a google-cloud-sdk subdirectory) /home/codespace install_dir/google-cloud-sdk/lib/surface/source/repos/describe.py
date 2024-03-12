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
"""Describe Google Cloud Platform git repository."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.source import sourcerepo
from googlecloudsdk.calliope import base


@base.ReleaseTracks(base.ReleaseTrack.GA, base.ReleaseTrack.ALPHA,
                    base.ReleaseTrack.BETA)
class Describe(base.DescribeCommand):
  """Describe a cloud source repository.

  This command describes a repository from the currently
  active Google Cloud Platform project.  The description includes the
  full repository name (projects/<projectid>/repos/<reponame>), the size
  (if non-zero), and the url.

  ## EXAMPLES

  To describe a repository named example-repo in the current project
  issue the following command:

    $ {command} REPOSITORY_NAME

  """

  @staticmethod
  def Args(parser):
    parser.add_argument('repository_name', help='Name of the repository.')

  def Run(self, args):
    """Describe a named GCP repository in the current project.

    Args:
      args: argparse.Namespace, the arguments this command is run with.

    Returns:
      (sourcerepo_v1_messages.Repo) The named repository.

    Raises:
      sourcerepo.RepoResourceError: on resource initialization errors.
      apitools.base.py.exceptions.HttpError: on request errors.
    """
    res = sourcerepo.ParseRepo(args.repository_name)
    sourcerepo_handler = sourcerepo.Source()
    return sourcerepo_handler.GetRepo(res)
