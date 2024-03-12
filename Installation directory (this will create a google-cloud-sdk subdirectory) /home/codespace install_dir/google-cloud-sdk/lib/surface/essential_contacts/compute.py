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
"""Command to compute Essential Contacts for a resource."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.essential_contacts import contacts
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.essential_contacts import flags
from googlecloudsdk.command_lib.essential_contacts import util


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.GA)
class Compute(base.ListCommand):
  r"""Compute the essential contacts that are subscribed to the specified notification categories for a resource.

  This command will return the contacts subscribed to any of the notification
  categories that have been set on the requested resource or any of its
  ancestors.

  ## EXAMPLES

  To compute contacts subscribed to the technical category for the current
  project, run:

        $ {command} --notification-categories=technical

  To compute contacts subscribed to the product-updates or billing categories
  for the folder with id ``123'', run:

        $ {command} --notification-categories=product-updates,billing
        --folder=123

  To compute contacts subscribed to the legal category for the organization with
  id ``456'', run:

        $ {command} --notification-categories=legal --organization=456
  """

  @staticmethod
  def _GetNotificationCategoryEnumByParentType(parent_name):
    """Gets the NotificationCategory enum to cast the args as based on the type of parent resource arg."""
    if parent_name.startswith('folders'):
      return contacts.GetMessages(
      ).EssentialcontactsFoldersContactsComputeRequest.NotificationCategoriesValueValuesEnum

    if parent_name.startswith('organizations'):
      return contacts.GetMessages(
      ).EssentialcontactsOrganizationsContactsComputeRequest.NotificationCategoriesValueValuesEnum

    return contacts.GetMessages(
    ).EssentialcontactsProjectsContactsComputeRequest.NotificationCategoriesValueValuesEnum

  @staticmethod
  def Args(parser):
    """Adds command-specific args."""
    flags.AddNotificationCategoriesArg(
        parser, contacts.GetContactNotificationCategoryEnum(), required=True)
    flags.AddParentArgs(parser)
    base.URI_FLAG.RemoveFromParser(parser)

  def Run(self, args):
    """Runs the compute contacts command."""
    parent_name = util.GetParent(args)
    notification_category_enum = self._GetNotificationCategoryEnumByParentType(
        parent_name)
    categories = util.GetNotificationCategories(args,
                                                notification_category_enum)

    client = contacts.ContactsClient()
    return client.Compute(
        parent_name, categories, limit=args.limit, page_size=args.page_size)
