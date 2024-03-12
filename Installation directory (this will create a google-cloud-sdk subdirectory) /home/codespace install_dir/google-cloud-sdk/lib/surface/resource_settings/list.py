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
"""Describe command for the Resource Settings CLI."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.resourcesettings import utils as api_utils
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.resource_settings import arguments
from googlecloudsdk.command_lib.resource_settings import utils


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.GA)
class List(base.ListCommand):
  r"""List all available resource settings.

  List all available resource settings.

  ## EXAMPLES

  To list all available resource settings with the project ``foo-project'', run:

    $ {command} --project=foo-project
  """

  @staticmethod
  def Args(parser):
    arguments.AddResourceFlagsToParser(parser)

  def Run(self, args):
    """Get the resource settings.

    Args:
      args: argparse.Namespace, An object that contains the values for the
        arguments specified in the Args method.

    Returns:
       The retrieved settings.
    """

    settings_service = api_utils.GetServiceFromArgs(args)
    parent_resource = utils.GetParentResourceFromArgs(args)

    get_request = api_utils.GetListRequestFromArgs(args, parent_resource, False)
    setting_value = settings_service.List(get_request)

    return setting_value
