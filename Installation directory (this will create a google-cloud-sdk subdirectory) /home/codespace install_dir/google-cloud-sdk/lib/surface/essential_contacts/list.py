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
"""Command to list essential contacts for a resource."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.essential_contacts import contacts
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.essential_contacts import flags
from googlecloudsdk.command_lib.essential_contacts import util


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.GA)
class List(base.ListCommand):
  """List essential contacts for a resource.

  ## EXAMPLES

  To list the contacts set on the current project:

        $ {command} [--page_size=10] [--limit=20]

  To list the contacts set on the folder with id ``456'', run:

      $ {command} --folder=456 [--page_size=10] [--limit=20]

  To list the contacts set on the organization with id ``456'', run:

        $ {command} --organization=456 [--page_size=10] [--limit=20]
  """

  @staticmethod
  def Args(parser):
    """Adds command-specific args."""
    flags.AddParentArgs(parser)
    base.URI_FLAG.RemoveFromParser(parser)

  def Run(self, args):
    """Runs the list command."""
    parent_name = util.GetParent(args)
    client = contacts.ContactsClient()
    return client.List(parent_name, limit=args.limit, page_size=args.page_size)
