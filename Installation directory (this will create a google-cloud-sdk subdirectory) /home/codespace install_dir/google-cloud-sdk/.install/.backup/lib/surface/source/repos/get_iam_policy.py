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
"""Gets the IAM policy for the repository."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.source import sourcerepo
from googlecloudsdk.calliope import base


@base.ReleaseTracks(base.ReleaseTrack.GA, base.ReleaseTrack.ALPHA,
                    base.ReleaseTrack.BETA)
class GetIamPolicy(base.ListCommand):
  """Get the IAM policy for the named cloud source repository.

  This command gets the IAM policy for the given repository.

  ## EXAMPLES

  To get the IAM policy, issue the following command:

    $ {command} REPOSITORY_NAME

  """

  @staticmethod
  def Args(parser):
    parser.add_argument('repository_name', help='Name of the repository.')
    base.URI_FLAG.RemoveFromParser(parser)

  def Run(self, args):
    """Gets the IAM policy for the repository.

    Args:
      args: argparse.Namespace, the arguments this command is run with.

    Returns:
      (sourcerepo_v1_messages.Policy) The IAM policy.

    Raises:
      sourcerepo.RepoResourceError: on resource initialization errors.
      apitools.base.py.exceptions.HttpError: on request errors.
    """
    res = sourcerepo.ParseRepo(args.repository_name)
    source = sourcerepo.Source()
    return source.GetIamPolicy(res)
