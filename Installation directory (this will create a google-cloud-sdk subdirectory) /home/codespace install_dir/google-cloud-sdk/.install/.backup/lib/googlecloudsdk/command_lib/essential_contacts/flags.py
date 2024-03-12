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
"""Flags module for Essential Contacts commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.command_lib.util.apis import arg_utils


def AddContactIdArg(parser, help_text='id of contact'):
  """Adds an arg for the contact id to the parser."""
  parser.add_argument('CONTACT_ID', type=str, help=help_text)


def AddParentArgs(parser):
  """Adds args for the parent resource of a contact to the parser."""
  parent_group = parser.add_mutually_exclusive_group(required=False)
  parent_group.add_argument(
      '--project',
      help='project number or id where contacts are set. If neither --project, --folder, nor --organization are provided then the config property [core/project] will be used as the resource.'
  )
  parent_group.add_argument(
      '--folder',
      help='folder number where contacts are set. If neither --project, --folder, nor --organization are provided then the config property [core/project] will be used as the resource.'
  )
  parent_group.add_argument(
      '--organization',
      help='organization number where contacts are set. If neither --project, --folder, nor --organization are provided then the config property [core/project] will be used as the resource.'
  )


def _NotificationCategoryEnumMapper(notification_category_enum_message):
  return arg_utils.ChoiceEnumMapper('--notification-categories',
                                    notification_category_enum_message)


def AddNotificationCategoriesArg(
    parser,
    notification_category_enum_message,
    required=False,
    help_text='list of notification categories contact is subscribed to.'):
  """Adds the arg for specifying a list of notification categories to the parser."""
  parser.add_argument(
      '--notification-categories',
      metavar='NOTIFICATION_CATEGORIES',
      type=arg_parsers.ArgList(
          choices=_NotificationCategoryEnumMapper(
              notification_category_enum_message).choices),
      help=help_text,
      required=required)


def AddEmailArg(parser, required=False, help_text='email address of contact.'):
  """Adds an arg for the contact's email to the parser."""
  parser.add_argument('--email', help=help_text, required=required)


def AddLanugageArg(
    parser,
    required=False,
    help_text='preferred language of contact. Must be a valid ISO 639-1 '
    'language code.'):
  """Adds an arg for the contact's preferred language to the parser."""
  parser.add_argument('--language', help=help_text, required=required)
