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

from apitools.base.py import exceptions as apitools_exceptions
from googlecloudsdk.api_lib.resourcesettings import utils as api_utils
from googlecloudsdk.api_lib.util import exceptions
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.resource_settings import arguments
from googlecloudsdk.command_lib.resource_settings import utils


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.GA)
class Describe(base.DescribeCommand):
  r"""Show the value of a resource setting.

  Show the value of a resource setting.

  ## EXAMPLES

  To describe the resource settings ``net-preferredDnsServers'' with the
  project ``foo-project'', run:

    $ {command} net-preferredDnsServers --project=foo-project
  """

  @staticmethod
  def Args(parser):
    arguments.AddSettingsNameArgToParser(parser)
    arguments.AddResourceFlagsToParser(parser)
    parser.add_argument(
        '--effective',
        action='store_true',
        help='Describe the effective setting.')

  def Run(self, args):
    """Get the (effective) resource settings.

    If --effective is not specified, it is a regular resource setting and
    it is retrieved using GetValue.

    If --effective is specified, it is an effective setting and it is retrieved
    using LookupEffectiveValue.

    Args:
      args: argparse.Namespace, An object that contains the values for the
        arguments specified in the Args method.

    Returns:
       The retrieved settings.
    """

    settings_service = api_utils.GetServiceFromArgs(args)
    setting_name = utils.GetSettingNameFromArgs(args)
    setting_path = utils.GetSettingsPathFromArgs(args)

    if args.effective:
      get_request = api_utils.GetRequestFromArgs(args, setting_path, True)
    else:
      get_request = api_utils.GetRequestFromArgs(args, setting_path, False)

    try:
      setting_value = settings_service.Get(get_request)
    except apitools_exceptions.HttpNotFoundError as e:
      raise exceptions.HttpException(
          e,
          error_format='The setting `' + setting_name +
          '` has not been set for this resource. Please ' +
          'set the setting first or show the flag `--effective` to lookup the effective setting instead.'
      )

    return setting_value
