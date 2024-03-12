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
"""Traffic-specific printer and functions for generating traffic formats."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from googlecloudsdk.api_lib.run import service
from googlecloudsdk.api_lib.run import traffic_pair
from googlecloudsdk.command_lib.run import platforms
from googlecloudsdk.core.console import console_attr
from googlecloudsdk.core.resource import custom_printer_base as cp


TRAFFIC_PRINTER_FORMAT = 'traffic'
_INGRESS_UNSPECIFIED = '-'


def _GetIngress(record):
  """Gets the ingress traffic allowed to call the service."""
  if platforms.GetPlatform() == platforms.PLATFORM_MANAGED:
    spec_ingress = record.annotations.get(service.INGRESS_ANNOTATION)
    status_ingress = record.annotations.get(service.INGRESS_STATUS_ANNOTATION)
    if spec_ingress == status_ingress:
      return spec_ingress
    else:
      spec_ingress = spec_ingress or _INGRESS_UNSPECIFIED
      status_ingress = status_ingress or _INGRESS_UNSPECIFIED
      return '{} (currently {})'.format(spec_ingress, status_ingress)
  elif (record.labels.get(
      service.ENDPOINT_VISIBILITY) == service.CLUSTER_LOCAL):
    return service.INGRESS_INTERNAL
  else:
    return service.INGRESS_ALL


def _GetTagAndStatus(tag):
  """Returns the tag with padding and an adding/removing indicator if needed."""
  if tag.inSpec and not tag.inStatus:
    return '  {} (Adding):'.format(tag.tag)
  elif not tag.inSpec and tag.inStatus:
    return '  {} (Deleting):'.format(tag.tag)
  else:
    return '  {}:'.format(tag.tag)


def _TransformTrafficPair(pair):
  """Transforms a single TrafficTargetPair into a marker class structure."""
  console = console_attr.GetConsoleAttr()
  return (pair.displayPercent, console.Emphasize(pair.displayRevisionId),
          cp.Table([('', _GetTagAndStatus(t), t.url) for t in pair.tags]))


def _TransformTrafficPairs(traffic_pairs, service_url, service_ingress=None):
  """Transforms a List[TrafficTargetPair] into a marker class structure."""
  traffic_section = cp.Section(
      [cp.Table(_TransformTrafficPair(p) for p in traffic_pairs)])
  route_section = [cp.Labeled([('URL', service_url)])]
  if service_ingress is not None:
    route_section.append(cp.Labeled([('Ingress', service_ingress)]))
  route_section.append(cp.Labeled([('Traffic', traffic_section)]))
  return cp.Section(route_section, max_column_width=60)


def TransformRouteFields(service_record):
  """Transforms a service's route fields into a marker class structure to print.

  Generates the custom printing format for a service's url, ingress, and traffic
  using the marker classes defined in custom_printer_base.

  Args:
    service_record: A Service object.

  Returns:
    A custom printer marker object describing the route fields print format.
  """
  no_status = service_record.status is None
  traffic_pairs = traffic_pair.GetTrafficTargetPairs(
      service_record.spec_traffic, service_record.status_traffic,
      service_record.is_managed,
      (_INGRESS_UNSPECIFIED
       if no_status else service_record.status.latestReadyRevisionName))
  return _TransformTrafficPairs(traffic_pairs,
                                '' if no_status else service_record.status.url,
                                _GetIngress(service_record))


class TrafficPrinter(cp.CustomPrinterBase):
  """Prints a service's traffic in a custom human-readable format."""

  def Print(self, resources, single=False, intermediate=False):
    """Overrides ResourcePrinter.Print to set single=True."""
    # The update-traffic command returns a List[TrafficTargetPair] as its
    # result. In order to print the custom human-readable format, this printer
    # needs to process all records in the result at once (to compute column
    # widths). By default, ResourcePrinter interprets a List[*] as a list of
    # separate records and passes the contents of the list to this printer
    # one-by-one. Setting single=True forces ResourcePrinter to treat the
    # result as one record and pass the entire list to this printer in one call.
    super(TrafficPrinter, self).Print(resources, True, intermediate)

  def Transform(self, record):
    """Transforms a List[TrafficTargetPair] into a marker class format."""
    if record:
      service_url = record[0].serviceUrl
    else:
      service_url = ''
    return _TransformTrafficPairs(record, service_url)
