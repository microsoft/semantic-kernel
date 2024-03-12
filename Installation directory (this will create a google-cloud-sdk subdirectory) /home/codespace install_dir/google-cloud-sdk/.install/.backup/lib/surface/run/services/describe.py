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
"""Command for obtaining details about a given service."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.run import connection_context
from googlecloudsdk.command_lib.run import exceptions
from googlecloudsdk.command_lib.run import flags
from googlecloudsdk.command_lib.run import resource_args
from googlecloudsdk.command_lib.run import serverless_operations
from googlecloudsdk.command_lib.run.printers import export_printer
from googlecloudsdk.command_lib.run.printers import service_printer
from googlecloudsdk.command_lib.util.concepts import concept_parsers
from googlecloudsdk.command_lib.util.concepts import presentation_specs
from googlecloudsdk.core.resource import resource_printer


@base.ReleaseTracks(base.ReleaseTrack.ALPHA,
                    base.ReleaseTrack.BETA,
                    base.ReleaseTrack.GA)
class Describe(base.Command):
  """Obtain details about a given service."""

  detailed_help = {
      'DESCRIPTION': """\
          {description}
          """,
      'EXAMPLES': """\
          To obtain details about a given service:

              $ {command} <service-name>

          To get those details in the YAML format:

              $ {command} <service-name> --format=yaml

          To get them in YAML format suited to export (omitting metadata
          specific to this deployment and status info):

              $ {command} <service-name> --format=export
          """,
  }

  @staticmethod
  def CommonArgs(parser):
    service_presentation = presentation_specs.ResourcePresentationSpec(
        'SERVICE',
        resource_args.GetServiceResourceSpec(),
        'Service to describe.',
        required=True,
        prefixes=False)
    concept_parsers.ConceptParser([service_presentation]).AddToParser(parser)

    resource_printer.RegisterFormatter(
        service_printer.SERVICE_PRINTER_FORMAT,
        service_printer.ServicePrinter, hidden=True)
    parser.display_info.AddFormat(service_printer.SERVICE_PRINTER_FORMAT)
    resource_printer.RegisterFormatter(
        export_printer.EXPORT_PRINTER_FORMAT,
        export_printer.ExportPrinter, hidden=True)

  @staticmethod
  def Args(parser):
    Describe.CommonArgs(parser)

  def _ConnectionContext(self, args):
    return connection_context.GetConnectionContext(
        args, flags.Product.RUN, self.ReleaseTrack()
    )

  def Run(self, args):
    """Obtain details about a given service."""
    conn_context = self._ConnectionContext(args)
    service_ref = args.CONCEPTS.service.Parse()
    flags.ValidateResource(service_ref)
    with serverless_operations.Connect(conn_context) as client:
      serv = client.GetService(service_ref)
    if not serv:
      raise exceptions.ArgumentError('Cannot find service [{}]'.format(
          service_ref.servicesId))
    return serv
