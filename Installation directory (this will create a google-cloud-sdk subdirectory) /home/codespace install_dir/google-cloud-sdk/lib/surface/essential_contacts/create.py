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
"""Command to create an Essential Contact."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.essential_contacts import contacts
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.essential_contacts import flags
from googlecloudsdk.command_lib.essential_contacts import util


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.GA)
class Create(base.CreateCommand):
  r"""Create an essential contact.

  ## EXAMPLES

  To create a contact in the current project, run:

        $ {command} --email=contact-email@example.com
        --notification-categories=technical,product-updates --language=en-US

  To create a contact in the folder with id ``456'', run:

        $ {command} --email=contact-email@example.com
        --notification-categories=technical,product-updates --language=en-US
        --folder=456

  To create a contact in the organization with id ``456'', run:

        $ {command} --email=contact-email@example.com
        --notification-categories=technical,product-updates --language=en-US
        --organization=456
  """

  @staticmethod
  def Args(parser):
    """Adds command-specific args."""
    flags.AddEmailArg(parser, required=True)
    flags.AddNotificationCategoriesArg(
        parser, contacts.GetContactNotificationCategoryEnum(), required=True)
    flags.AddLanugageArg(parser, required=True)
    flags.AddParentArgs(parser)

  def Run(self, args):
    """Runs the create command."""
    parent_name = util.GetParent(args)
    categories = util.GetNotificationCategories(
        args, contacts.GetContactNotificationCategoryEnum())
    client = contacts.ContactsClient()
    return client.Create(parent_name, args.email, categories, args.language)
