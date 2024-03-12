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
"""Command for deleting a service."""

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
  """Delete a service."""

  detailed_help = {
      'DESCRIPTION':
          """\
          {description}
          """,
      'EXAMPLES':
          """\
          To delete a service:

              $ {command} <service-name>
          """,
  }

  @staticmethod
  def CommonArgs(parser):
    service_presentation = presentation_specs.ResourcePresentationSpec(
        'SERVICE',
        resource_args.GetServiceResourceSpec(),
        'Service to delete.',
        required=True,
        prefixes=False)
    concept_parsers.ConceptParser([service_presentation]).AddToParser(parser)
    flags.AddAsyncFlag(parser, default_async_for_cluster=True)

  @staticmethod
  def Args(parser):
    Delete.CommonArgs(parser)

  def _ConnectionContext(self, args):
    return connection_context.GetConnectionContext(
        args, flags.Product.RUN, self.ReleaseTrack()
    )

  def Run(self, args):
    """Delete a service."""
    conn_context = self._ConnectionContext(args)
    service_ref = args.CONCEPTS.service.Parse()
    flags.ValidateResource(service_ref)
    console_io.PromptContinue(
        message='Service [{service}] will be deleted.'.format(
            service=service_ref.servicesId),
        throw_if_unattended=True,
        cancel_on_no=True)

    async_ = deletion.AsyncOrDefault(args.async_)
    with serverless_operations.Connect(conn_context) as client:
      deletion.Delete(
          service_ref, client.GetService, client.DeleteService, async_
      )
    if async_:
      pretty_print.Success(
          'Service [{}] is being deleted.'.format(service_ref.servicesId)
      )
    else:
      log.DeletedResource(service_ref.servicesId, 'service')


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class AlphaDelete(Delete):
  """Delete a service."""

  @staticmethod
  def Args(parser):
    Delete.CommonArgs(parser)


AlphaDelete.__doc__ = Delete.__doc__
