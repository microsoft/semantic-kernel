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
"""Command for deleting access approval settings."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from googlecloudsdk.api_lib.access_approval import settings
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.access_approval import parent


class Update(base.Command):
  """Update Access Approval settings.

  Update the Access Approval settings associated with a project, a folder, or
  organization. Partial updates are supported (for example, you can update the
  notification emails without modifying the enrolled services).
  """

  detailed_help = {
      'EXAMPLES':
          textwrap.dedent("""\
    Update notification emails associated with project `p1`, run:

        $ {command} --project=p1 --notification_emails='foo@example.com, bar@example.com'

    Enable Access Approval enforcement for folder `f1`:

        $ {command} --folder=f1 --enrolled_services=all

    Enable Access Approval enforcement for organization `org1` for only Cloud Storage and Compute
    products and set the notification emails at the same time:

        $ {command} --organization=org1 --enrolled_services='storage.googleapis.com,compute.googleapis.com' --notification_emails='security_team@example.com'

    Update active key version for project `p1`:

        $ {command} --project=p1 --active_key_version='projects/p1/locations/global/keyRings/signing-keys/cryptoKeys/signing-key/cryptoKeyVersions/1'
        """),
  }

  @staticmethod
  def Args(parser):
    """Add command-specific args."""
    parent.Args(parser)
    parser.add_argument(
        '--notification_emails',
        help='Comma-separated list of email addresses to which notifications relating to approval requests should be sent or \'\' to clear all saved notification emails.'
    )
    parser.add_argument(
        '--enrolled_services',
        help='Comma-separated list of services to enroll for Access Approval or \'all\' for all supported services. Note for project and folder enrollments, only \'all\' is supported. Use \'\' to clear all enrolled services.'
    )
    parser.add_argument(
        '--active_key_version',
        help='The asymmetric crypto key version to use for signing approval requests. Use `\'\'` to remove the custom signing key.'
    )

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      Some value that we want to have printed later.
    """
    p = parent.GetParent(args)

    if (args.notification_emails is None and args.enrolled_services is None and
        args.active_key_version is None):
      raise exceptions.MinimumArgumentException([
          '--notification_emails', '--enrolled_services', '--active_key_version'
      ], 'must specify at least one of these flags')

    update_mask = []
    emails_list = []
    if args.notification_emails is not None:
      update_mask.append('notification_emails')
      if args.notification_emails:
        emails_list = args.notification_emails.split(',')
        emails_list = [i.strip() for i in emails_list]

    services_list = []
    if args.enrolled_services is not None:
      update_mask.append('enrolled_services')
      if args.enrolled_services:
        services_list = args.enrolled_services.split(',')
        services_list = [i.strip() for i in services_list]

    if args.active_key_version is not None:
      update_mask.append('active_key_version')

    return settings.Update(
        name=('%s/accessApprovalSettings' % p),
        notification_emails=emails_list,
        enrolled_services=services_list,
        active_key_version=args.active_key_version,
        update_mask=','.join(update_mask))
