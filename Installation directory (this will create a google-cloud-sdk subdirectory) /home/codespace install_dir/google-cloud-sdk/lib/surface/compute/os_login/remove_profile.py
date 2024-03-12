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

"""Implements the command for removing an OS Login profile."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.oslogin import client
from googlecloudsdk.calliope import base
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources
from googlecloudsdk.core.console import console_io


@base.ReleaseTracks(base.ReleaseTrack.GA, base.ReleaseTrack.BETA)
class RemoveProfile(base.Command):
  """Remove the posix account information for the current user."""

  def Run(self, args):
    oslogin_client = client.OsloginClient(self.ReleaseTrack())
    account = (properties.VALUES.auth.impersonate_service_account.Get()
               or properties.VALUES.core.account.GetOrFail())
    project = properties.VALUES.core.project.Get(required=True)
    project_ref = resources.REGISTRY.Parse(project, params={'user': account},
                                           collection='oslogin.users.projects')
    current_profile = oslogin_client.GetLoginProfile(account)
    account_id = None
    for account in current_profile.posixAccounts:
      if account.accountId == project:
        account_id = account.accountId

    if account_id:
      console_io.PromptContinue(
          'Posix accounts associated with project ID [{0}] will be deleted.'
          .format(project),
          default=True,
          cancel_on_no=True)
      operating_system = getattr(args, 'operating_system', None)
      res = oslogin_client.DeletePosixAccounts(project_ref, operating_system)
      log.DeletedResource(account_id, details='posix account(s)')
      return res
    else:
      log.warning('No profile found with accountId [{0}]'.format(project))


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class RemoveProfileAlpha(RemoveProfile):
  """Remove the posix account information for the current user."""

  @staticmethod
  def Args(parser):
    os_arg = base.ChoiceArgument(
        '--operating-system',
        choices=('linux', 'windows'),
        required=False,
        default='linux',
        help_str='Specifies the profile type to remove.')
    os_arg.AddToParser(parser)

RemoveProfile.detailed_help = {
    'brief': 'Remove the posix account information for the current user.',
    'DESCRIPTION': """
      *{command}* removes the posix account information for the current
      user where the account ID field is set to the current project ID.
      Posix account entries for G Suite users do not set the account ID
      field and can only be modified by a domain administrator.
      """,
    'EXAMPLES': """
      To remove all POSIX accounts associated with the current user and
      project, run:

        $ {command}

      To remove all POSIX accounts associated with the current user in the
      project named `example-project`, run:

        $ {command} --project=example-project
      """
}
