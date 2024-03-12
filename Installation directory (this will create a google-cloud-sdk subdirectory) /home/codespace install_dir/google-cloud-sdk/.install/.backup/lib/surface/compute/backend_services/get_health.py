# -*- coding: utf-8 -*- #
# Copyright 2014 Google LLC. All Rights Reserved.
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

"""Command for getting health status of backend(s) in a backend service."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute.backend_services import client
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute.backend_services import backend_services_utils
from googlecloudsdk.command_lib.compute.backend_services import flags


class GetHealth(base.ListCommand):
  """Gets health status."""

  _BACKEND_SERVICE_ARG = flags.GLOBAL_REGIONAL_BACKEND_SERVICE_ARG

  @classmethod
  def Args(cls, parser):
    cls._BACKEND_SERVICE_ARG.AddArgument(parser)

  def GetReference(self, holder, args):
    """Override. Don't assume a default scope."""
    return self._BACKEND_SERVICE_ARG.ResolveAsResource(
        args,
        holder.resources,
        default_scope=backend_services_utils.GetDefaultScope(),
        scope_lister=compute_flags.GetDefaultScopeLister(holder.client))

  def Run(self, args):
    """Returns a list of backendServiceGroupHealth objects."""
    if args.uri:
      args.uri = False
      args.format = 'value[delimiter="\n"](status.healthStatus[].instance)'

    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    ref = self.GetReference(holder, args)

    backend_service = client.BackendService(
        ref, compute_client=holder.client)

    return backend_service.GetHealth()


GetHealth.detailed_help = {
    'brief': 'Get backend health statuses from a backend service.',
    'DESCRIPTION': """
        *{command}* is used to request the current health status of
        instances in a backend service. Every group in the service
        is checked and the health status of each configured instance
        is printed.

        If a group contains names of instances that don't exist or
        instances that haven't yet been pushed to the load-balancing
        system, they will not show up. Those that are listed as
        ``HEALTHY'' are able to receive load-balanced traffic. Those that
        are marked as ``UNHEALTHY'' are either failing the configured
        health-check or not responding to it.

        Since the health checks are performed continuously and in
        a distributed manner, the state returned by this command is
        the most recent result of a vote of several redundant health
        checks. Backend services that do not have a valid global
        forwarding rule referencing it will not be health checked and
        so will have no health status.
    """
}
