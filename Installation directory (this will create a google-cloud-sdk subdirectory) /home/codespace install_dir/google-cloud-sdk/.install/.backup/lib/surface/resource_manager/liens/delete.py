# -*- coding: utf-8 -*- #
# Copyright 2016 Google LLC. All Rights Reserved.
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
"""Command to delete a lien."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.resource_manager import error
from googlecloudsdk.api_lib.resource_manager import liens
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.resource_manager import flags
from googlecloudsdk.core import log


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Delete(base.DeleteCommand):
  """Delete a lien.

  Delete a lien, given a valid lien ID.

  This command can fail for the following reasons:
      * There is no lien with the given ID.
      * The active account does not have permission to delete the given lien.
  ## EXAMPLES


  The following command deletes a lien with the ID `p8765-kjasdkkhsd`:

    $ {command} p8765-kjasdkkhsd
  """

  @staticmethod
  def Args(parser):
    flags.LienIdArg('you want to delete.').AddToParser(parser)

  @error.EmitErrorDetails
  def Run(self, args):
    service = liens.LiensService()
    messages = liens.LiensMessages()
    service.Delete(
        messages.CloudresourcemanagerLiensDeleteRequest(liensId=args.id))
    log.DeletedResource(liens.LienIdToName(args.id))
