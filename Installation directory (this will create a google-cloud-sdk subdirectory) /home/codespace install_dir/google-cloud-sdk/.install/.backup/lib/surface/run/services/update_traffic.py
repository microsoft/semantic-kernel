# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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
"""Command for updating env vars and other configuration info."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from googlecloudsdk.api_lib.run import k8s_object
from googlecloudsdk.api_lib.run import traffic_pair
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import display
from googlecloudsdk.command_lib.run import config_changes
from googlecloudsdk.command_lib.run import connection_context
from googlecloudsdk.command_lib.run import exceptions
from googlecloudsdk.command_lib.run import flags
from googlecloudsdk.command_lib.run import platforms
from googlecloudsdk.command_lib.run import pretty_print
from googlecloudsdk.command_lib.run import resource_args
from googlecloudsdk.command_lib.run import serverless_operations
from googlecloudsdk.command_lib.run import stages
from googlecloudsdk.command_lib.run.printers import traffic_printer
from googlecloudsdk.command_lib.util.concepts import concept_parsers
from googlecloudsdk.command_lib.util.concepts import presentation_specs
from googlecloudsdk.core.console import progress_tracker
from googlecloudsdk.core.resource import resource_printer


@base.ReleaseTracks(base.ReleaseTrack.GA)
class AdjustTraffic(base.Command):
  """Adjust the traffic assignments for a Cloud Run service."""

  detailed_help = {
      'DESCRIPTION':
          """\
          {description}
          """,
      'EXAMPLES':
          """\
          To assign 10% of traffic to revision myservice-s5sxn and
          90% of traffic to revision myservice-cp9kw run:

              $ {command} myservice --to-revisions=myservice-s5sxn=10,myservice-cp9kw=90

          To increase the traffic to revision myservice-s5sxn to 20% and
          by reducing the traffic to revision myservice-cp9kw to 80% run:

              $ {command} myservice --to-revisions=myservice-s5sxn=20

          To rollback to revision myservice-cp9kw run:

              $ {command} myservice --to-revisions=myservice-cp9kw=100

          To assign 100% of traffic to the current or future LATEST revision
          run:

              $ {command} myservice --to-latest

          You can also refer to the current or future LATEST revision in
          --to-revisions by the string "LATEST". For example, to set 10% of
          traffic to always float to the latest revision:

              $ {command} myservice --to-revisions=LATEST=10

         """,
  }

  @classmethod
  def CommonArgs(cls, parser):
    service_presentation = presentation_specs.ResourcePresentationSpec(
        'SERVICE',
        resource_args.GetServiceResourceSpec(prompt=True),
        'Service to update the configuration of.',
        required=True,
        prefixes=False)
    flags.AddAsyncFlag(parser)
    flags.AddUpdateTrafficFlags(parser)
    flags.AddTrafficTagsFlags(parser)
    concept_parsers.ConceptParser([service_presentation]).AddToParser(parser)

    resource_printer.RegisterFormatter(
        traffic_printer.TRAFFIC_PRINTER_FORMAT,
        traffic_printer.TrafficPrinter,
        hidden=True)
    parser.display_info.AddFormat(traffic_printer.TRAFFIC_PRINTER_FORMAT)

  @classmethod
  def Args(cls, parser):
    cls.CommonArgs(parser)

  def Run(self, args):
    """Update the traffic split for the service.

    Args:
      args: Args!

    Returns:
      List of traffic.TrafficTargetStatus instances reflecting the change.
    """
    conn_context = connection_context.GetConnectionContext(
        args, flags.Product.RUN, self.ReleaseTrack())
    service_ref = args.CONCEPTS.service.Parse()
    flags.ValidateResource(service_ref)

    changes = flags.GetServiceConfigurationChanges(args)
    if not changes:
      raise exceptions.NoConfigurationChangeError(
          'No traffic configuration change requested.')
    changes.insert(
        0,
        config_changes.DeleteAnnotationChange(
            k8s_object.BINAUTHZ_BREAKGLASS_ANNOTATION))
    changes.append(
        config_changes.SetLaunchStageAnnotationChange(self.ReleaseTrack()))

    is_managed = platforms.GetPlatform() == platforms.PLATFORM_MANAGED
    with serverless_operations.Connect(conn_context) as client:
      deployment_stages = stages.UpdateTrafficStages()
      try:
        with progress_tracker.StagedProgressTracker(
            'Updating traffic...',
            deployment_stages,
            failure_message='Updating traffic failed',
            suppress_output=args.async_) as tracker:
          serv = client.UpdateTraffic(
              service_ref,
              changes,
              tracker,
              args.async_,
          )
      except:
        serv = client.GetService(service_ref)
        if serv:
          resources = traffic_pair.GetTrafficTargetPairs(
              serv.spec_traffic,
              serv.status_traffic,
              is_managed,
              serv.status.latestReadyRevisionName,
              serv.status.url)
          display.Displayer(
              self, args, resources,
              display_info=args.GetDisplayInfo()).Display()
        raise

      if args.async_:
        pretty_print.Success('Updating traffic asynchronously.')
      else:
        resources = traffic_pair.GetTrafficTargetPairs(
            serv.spec_traffic,
            serv.status_traffic,
            is_managed,
            serv.status.latestReadyRevisionName,
            serv.status.url)
        return resources


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class BetaAdjustTraffic(AdjustTraffic):
  """Adjust the traffic assignments for a Cloud Run service."""

  @classmethod
  def Args(cls, parser):
    cls.CommonArgs(parser)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class AlphaAdjustTraffic(AdjustTraffic):
  """Adjust the traffic assignments for a Cloud Run service."""

  @classmethod
  def Args(cls, parser):
    cls.CommonArgs(parser)

    # Flags specific to managed CR
    managed_group = flags.GetManagedArgGroup(parser)
    flags.AddBinAuthzBreakglassFlag(managed_group)
