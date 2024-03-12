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
"""Command to update an Essential Contact."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.essential_contacts import contacts
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.essential_contacts import flags
from googlecloudsdk.command_lib.essential_contacts import util


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.GA)
class Update(base.UpdateCommand):
  r"""Update an essential contact.

  ## EXAMPLES

  To update the notification category subscriptions for the contact with id
  ``123'' in the current project, run:

        $ {command} 123 --notification-categories=legal,suspension

  To update the language preference for the contact with id ``123'' in the
  folder with id ``456'', run:

        $ {command} 123 --language=es --folder=456

  To update the notification category subscriptions and language preference for
  the contact with id ``123'' in the organization with id ``456'', run:

        $ {command} 123 --notification-categories=legal --language=en-US
        --organization=456
  """

  @staticmethod
  def Args(parser):
    """Adds command-specific args."""
    flags.AddContactIdArg(parser)
    flags.AddNotificationCategoriesArg(
        parser, contacts.GetContactNotificationCategoryEnum())
    flags.AddLanugageArg(parser)
    flags.AddParentArgs(parser)

  def Run(self, args):
    """Runs the update command."""
    contact_name = util.GetContactName(args)
    categories = util.GetNotificationCategories(
        args, contacts.GetContactNotificationCategoryEnum())
    language = args.language

    if not language and not categories:
      raise exceptions.MinimumArgumentException(
          ['notification-categories', 'language'])

    client = contacts.ContactsClient()
    return client.Update(contact_name, categories, language)
