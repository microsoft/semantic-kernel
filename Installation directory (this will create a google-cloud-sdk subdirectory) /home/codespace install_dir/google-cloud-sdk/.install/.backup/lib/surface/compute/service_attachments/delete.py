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
"""Command for deleting service attachments."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import utils
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import scope as compute_scope
from googlecloudsdk.command_lib.compute.service_attachments import flags


def _DetailedHelp():
  return {
      'EXAMPLES':
          """\
          To delete a service attachment, run:

              $ {command} SERVICE_ATTACHMENT_NAME --region=us-central1"""
  }


def _Run(holder, service_attachment_refs):
  """Issues requests necessary to delete service attachments.

  Args:
    holder: the class that holds lazy initialized API client and resources.
    service_attachment_refs: the list of references for service attachments that
      need to be deleted.

  Returns:
    A list of responses. One response for each deletion request.
  """
  client = holder.client
  utils.PromptForDeletion(service_attachment_refs)

  requests = []
  for service_attachment_ref in service_attachment_refs:
    requests.append((client.apitools_client.serviceAttachments, 'Delete',
                     client.messages.ComputeServiceAttachmentsDeleteRequest(
                         **service_attachment_ref.AsDict())))

  return client.MakeRequests(requests)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.GA)
class Delete(base.DeleteCommand):
  """Delete one or more Google Compute Engine service attachments."""

  SERVICE_ATTACHMENT_ARG = None
  detailed_help = _DetailedHelp()

  @classmethod
  def Args(cls, parser):
    cls.SERVICE_ATTACHMENT_ARG = flags.ServiceAttachmentArgument(plural=True)
    cls.SERVICE_ATTACHMENT_ARG.AddArgument(parser, operation_type='delete')
    parser.display_info.AddCacheUpdater(flags.ServiceAttachmentsCompleter)

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    service_attachment_refs = self.SERVICE_ATTACHMENT_ARG.ResolveAsResource(
        args, holder.resources, default_scope=compute_scope.ScopeEnum.REGION)
    return _Run(holder, service_attachment_refs)
