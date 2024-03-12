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
"""Command for deleting revisions."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.run import connection_context
from googlecloudsdk.command_lib.run import deletion
from googlecloudsdk.command_lib.run import flags
from googlecloudsdk.command_lib.run import pretty_print
from googlecloudsdk.command_lib.run import resource_args
from googlecloudsdk.command_lib.run import serverless_operations
from googlecloudsdk.command_lib.util.concepts import concept_parsers
from googlecloudsdk.command_lib.util.concepts import presentation_specs
from googlecloudsdk.core import log
from googlecloudsdk.core.console import console_io


@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.GA)
class Delete(base.Command):
  """Delete a revision."""

  detailed_help = {
      'DESCRIPTION':
          """\
          {description}
          """,
      'EXAMPLES':
          """\
          To delete a revision:

              $ {command} <revision-name>
          """,
  }

  @staticmethod
  def CommonArgs(parser):
    revision_presentation = presentation_specs.ResourcePresentationSpec(
        'REVISION',
        resource_args.GetRevisionResourceSpec(),
        'Revision to delete.',
        required=True,
        prefixes=False)
    concept_parsers.ConceptParser([revision_presentation]).AddToParser(parser)
    flags.AddAsyncFlag(parser, default_async_for_cluster=True)

  @staticmethod
  def Args(parser):
    Delete.CommonArgs(parser)

  def Run(self, args):
    """Delete a revision."""
    conn_context = connection_context.GetConnectionContext(
        args, flags.Product.RUN, self.ReleaseTrack())
    revision_ref = args.CONCEPTS.revision.Parse()

    console_io.PromptContinue(
        message='Revision [{}] will be deleted.'.format(
            revision_ref.revisionsId),
        throw_if_unattended=True,
        cancel_on_no=True)

    async_ = deletion.AsyncOrDefault(args.async_)
    with serverless_operations.Connect(conn_context) as client:
      deletion.Delete(
          revision_ref, client.GetRevision, client.DeleteRevision, async_
      )
    if async_:
      pretty_print.Success(
          'Revision [{}] is being deleted.'.format(revision_ref.revisionsId)
      )
    else:
      log.DeletedResource(revision_ref.revisionsId, 'revision')


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class AlphaDelete(Delete):
  """Delete a revision."""

  @staticmethod
  def Args(parser):
    Delete.CommonArgs(parser)


AlphaDelete.__doc__ = Delete.__doc__
