# -*- coding: utf-8 -*- #
# Copyright 2023 Google LLC. All Rights Reserved.
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
"""Hooks for Simulation declarative style commands implementation."""

from googlecloudsdk.command_lib.network_management.simulation import util
from googlecloudsdk.core import properties


def SetProjectAsParent(unused_ref, unused_args, request):
  """Add parent path to request, since it isn't automatically populated by apitools."""
  project = properties.VALUES.core.project.Get()
  if project is None:
    raise ValueError("Required field project not provided")
  request.parent = "projects/" + project + "/locations/global"
  return request


def SetLocationGlobal():
  """Set location ID to global."""
  return "global"


def ProcessSimulationConfigChangesFile(unused_ref, args, request):
  """Reads the firewall-service, route-service exported resources configs and transform them into the API accepted format and update the request proto."""
  if args.proposed_config_file:
    api_version = util.GetSimulationApiVersionFromArgs(args)
    request.simulation = util.PrepareSimulationChanges(
        args.proposed_config_file,
        api_version,
        file_format=args.file_format,
        simulation_type=args.simulation_type,
        original_config_file=args.original_config_file,
    )
  return request
