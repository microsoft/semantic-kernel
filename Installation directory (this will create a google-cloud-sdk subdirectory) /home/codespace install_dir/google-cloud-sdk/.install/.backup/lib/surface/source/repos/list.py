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
"""List project repositories."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.source import sourcerepo
from googlecloudsdk.calliope import base


@base.ReleaseTracks(base.ReleaseTrack.GA, base.ReleaseTrack.ALPHA,
                    base.ReleaseTrack.BETA)
class List(base.ListCommand):
  """List the repositories the currently active project.

  By default, repos in the current project are listed; this can be overridden
  with the gcloud --project flag.  The repository size is not returned, but
  can be retrieved for a particular repository with the describe command.

  ## EXAMPLES

  To list all repositories in the current project, run:

    $ {command}
  """

  @staticmethod
  def Args(parser):
    base.URI_FLAG.RemoveFromParser(parser)
    # Here's some sample output (with the URL cut short)
    # REPO_NAME                     PROJECT_ID     URL
    # ANewRepo                      kris-csr-test  https://...
    #
    # The resource name looks like projects/<projectid>/repos/reponame
    # We extract the project name as segment 1 and the repo name as segment 3
    # and up.
    parser.display_info.AddFormat("""
          table(
            name.split(/).slice(3:).join(/):label=REPO_NAME,
            name.segment(1):label=PROJECT_ID,
            firstof(mirror_config.url, url):label=URL
          )
        """)

  def Run(self, args):
    """Run the list command."""
    res = sourcerepo.GetDefaultProject()
    source_handler = sourcerepo.Source()
    return source_handler.ListRepos(
        res, limit=args.limit, page_size=args.page_size)
