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
"""Utility functions for create command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import utils
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.core import properties
import six
from six.moves import range  # pylint: disable=redefined-builtin


def ParseRegionDisksResources(resources, disks, replica_zones, project,
                              region):
  """Parse disks arguments taking into account project, region and zones.

  Try to deduce --region from --replica-zones and parse disk references:
  0. parse --project
  1. parse --region falling back to 0 for project
  2. for each disk:
   2.1. parse disk falling back to 0 and 1 falling back to property if necessary
   2.2. extract disk project from 2.1
   2.3. parse --replica-zones falling back to 2.2
   2.4. check zones are in disk project
   2.5. check zones are from the same region
   2.6. if --region is present, check if equal to 2.5
   2.7. parse disk falling back to 2.2 and 2.5
   2.8. check if disk is in 2.5 region
   2.9. yield 2.7

  Function is greedy - checks/deduces/parses all data before returning. If any
  error occurs, exception is raised.

  Args:
    resources: resources.Registry: resource parser
    disks: str, parsed disks argument (args.DISK_NAME)
    replica_zones: str, parsed --replica-zones flag (args.replica_zones)
    project: str, parsed --project flag or None (args.project)
    region: str, parsed --region flag or None (args.region)

  Returns:
    List disk resources [compute.regionDisks]
  """
  result_disks = []
  project_to_region = {}  # cache
  sample = '$SAMPLE$'  # shouldn't escape from this function

  # --project may be provided or not, URI should be accepted
  project_res = resources.Parse(
      project, collection='compute.projects', params={'project': sample})
  project_name = project_res.project
  # --region may be provided or not, URI should be accepted
  # project embedded in URI takes precedence over project_res
  region_res = resources.Parse(
      region,
      collection='compute.regions',
      params={'project': project_name,
              'region': sample})
  if region_res.project != project_name:
    project_name = region_res.project
  region_name = region_res.region
  if project_name == sample:
    # no project in --project nor --region - fallback to property
    project_name = properties.VALUES.core.project.GetOrFail
  # parse each disk separately as meaning of other flags may depend on disk URI
  for disk in disks:
    result_disk = _ParseDisk(resources, disk, sample, project_name,
                             project_to_region, region, region_name,
                             replica_zones)
    result_disks.append(result_disk)

  return result_disks


def _ParseDisk(resources, disk, sample, project_name, project_to_region,
               region, region_name, replica_zones):
  """Parse single disk reference."""
  # I need project to parse zone URI - parse disk argument, stage 1
  disk_resource = resources.Parse(
      disk,
      params={
          'region': region_name,
          'project': project_name
      },
      collection='compute.regionDisks')
  current_project = disk_resource.project
  # maintain cache
  if current_project not in project_to_region:
    project_to_region[current_project] = _DeduceRegionInProject(
        resources, current_project, disk_resource, sample, region,
        region_name, replica_zones)
  # parse disk argument using real region, stage 2
  # doesn't support scope listing/prompting, because scope is already chosen.
  result_disk = resources.Parse(
      disk,
      collection='compute.regionDisks',
      params={
          'region': project_to_region[current_project],
          'project': current_project
      })
  if result_disk.region != project_to_region[current_project]:
    raise exceptions.InvalidArgumentException('--replica-zones', (
        'Region from [DISK_NAME] ({}) is different from [--replica-zones] '
        '({}).').format(result_disk.SelfLink(),
                        project_to_region[current_project]))
  return result_disk


def _DeduceRegionInProject(resources, current_project, disk_resource,
                           sample, region, region_name, replica_zones):
  """Deduce region from zones in given project."""
  # parse all --replica-zones, consuming project from above
  current_zones = [
      resources.Parse(
          zone, collection='compute.zones', params={'project': current_project})
      for zone in replica_zones
  ]
  # check if all zones live in disks' project
  for zone in current_zones:
    if zone.project != current_project:
      raise exceptions.InvalidArgumentException(
          '--zone',
          'Zone [{}] lives in different project than disk [{}].'.format(
              six.text_type(zone.SelfLink()),
              six.text_type(disk_resource.SelfLink())))
  # check if all zones live in the same region
  for i in range(len(current_zones) - 1):
    if (utils.ZoneNameToRegionName(current_zones[i].zone) !=
        utils.ZoneNameToRegionName(current_zones[i + 1].zone)):
      raise exceptions.InvalidArgumentException('--replica-zones', (
          'Zones [{}, {}] live in different regions [{}, {}], but should '
          'live in the same.').format(
              current_zones[i].zone, current_zones[i + 1].zone,
              utils.ZoneNameToRegionName(current_zones[i].zone),
              utils.ZoneNameToRegionName(current_zones[i + 1].zone)))
  # check if --replica-zones is consistent with --region
  result = utils.ZoneNameToRegionName(current_zones[0].zone)
  if region is not None and region_name != sample and region_name != result:
    raise exceptions.InvalidArgumentException('--replica-zones', (
        'Region from [--replica-zones] ({}) is different from [--region] '
        '({}).').format(result, region_name))
  return result
