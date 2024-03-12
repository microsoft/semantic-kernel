# -*- coding: utf-8 -*- #
# Copyright 2021 Google LLC. All Rights Reserved.
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

"""'logging settings describe' command."""


from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.logging import util
from googlecloudsdk.calliope import base


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.GA)
class Describe(base.DescribeCommand):
  # pylint: disable=line-too-long
  """Display the settings for the Cloud Logging Logs Router.

  If *kmsKeyName* is present in the output, then CMEK is enabled for your
  project, folder, organization or billing-account. You can also find the Logs
  Router service account using this command.

  ## EXAMPLES

  To describe the Logs Router settings for a project, run:

    $ {command} --project=[PROJECT_ID]

  To describe the Logs Router settings for an organization, run:

    $ {command} --organization=[ORGANIZATION_ID]

    kmsKeyName:
    'projects/my-project/locations/my-location/keyRings/my-keyring/cryptoKeys/key'
    name: 'organizations/[ORGANIZATION_ID]/settings'
    serviceAccountId:
    '[SERVICE_ACCOUNT_ID]@gcp-sa-logging.iam.gserviceaccount.com'
  """

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    util.AddParentArgs(parser, 'settings to describe')

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      The settings for the specified project, folder, organizations or
      billing-account.
    """
    parent_name = util.GetParentFromArgs(args)
    return util.GetClient().projects.GetSettings(
        util.GetMessages().LoggingProjectsGetSettingsRequest(name=parent_name))
