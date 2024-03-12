# -*- coding: utf-8 -*- #
# Copyright 2020 Google Inc. All Rights Reserved.
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
"""services api-keys list command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.services import apikeys
from googlecloudsdk.calliope import base
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources


def _GetUriFunction(api_version):
  """Returns a Uri function for list."""
  collection = 'apikeys.projects.locations.keys'

  def UriFunc(resource):
    return resources.REGISTRY.ParseRelativeName(
        resource.name, collection=collection,
        api_version=api_version).SelfLink()

  return UriFunc


def _ListArgs(parser):
  parser.add_argument(
      '--show-deleted',
      action='store_true',
      help=('Show soft-deleted keys by specifying this flag.'))


@base.ReleaseTracks(base.ReleaseTrack.ALPHA,
                    base.ReleaseTrack.BETA, base.ReleaseTrack.GA)
class List(base.ListCommand):
  """Lists API keys.

  Lists the API keys of a given project.

  ## EXAMPLES

   List keys of a given project:

    $ {command}

   List keys of a given project, including keys that were soft-deleted in the
   past 30 days.:

    $ {command} --show-deleted --project=my_project
  """

  @staticmethod
  def Args(parser):
    _ListArgs(parser)
    parser.display_info.AddUriFunc(_GetUriFunction(api_version='v2'))

  def Run(self, args):
    """Run command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      The list of api keys.
    """

    project_id = properties.VALUES.core.project.GetOrFail()
    return apikeys.ListKeys(project_id, args.show_deleted, args.page_size,
                            args.limit)
