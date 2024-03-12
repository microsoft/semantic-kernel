# -*- coding: utf-8 -*- #
# Copyright 2015 Google LLC. All Rights Reserved.
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

"""Utilities for dealing with service resources."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.app import operations_util
from googlecloudsdk.core import exceptions
from googlecloudsdk.core.util import text
import six


class ServiceValidationError(exceptions.Error):
  pass


class ServicesDeleteError(exceptions.Error):
  pass


class ServicesNotFoundError(exceptions.Error):

  @classmethod
  def FromServiceLists(cls, requested_services, all_services):
    """Format a ServiceNotFoundError.

    Args:
      requested_services: list of str, IDs of services that were not found.
      all_services: list of str, IDs of all available services

    Returns:
      ServicesNotFoundError, error with properly formatted message
    """
    return cls(
        'The following {0} not found: [{1}]\n\n'
        'All services: [{2}]'.format(
            text.Pluralize(len(requested_services), 'service was',
                           plural='services were'),
            ', '.join(requested_services),
            ', '.join(all_services)))


class ServicesSplitTrafficError(exceptions.Error):
  pass


class Service(object):
  """Value class representing a service resource."""

  def __init__(self, project, id_, split=None):
    self.project = project
    self.id = id_
    self.split = split or {}

  def __eq__(self, other):
    return (type(other) is Service and
            self.project == other.project and self.id == other.id)

  def __ne__(self, other):
    return not self == other

  @classmethod
  def FromResourcePath(cls, path):
    parts = path.split('/')
    if len(parts) != 2:
      raise ServiceValidationError('[{0}] is not a valid resource path. '
                                   'Expected <project>/<service>.')
    return cls(*parts)

  def __lt__(self, other):
    return (self.project, self.id) < (other.project, other.id)

  def __le__(self, other):
    return (self.project, self.id) <= (other.project, other.id)

  def __gt__(self, other):
    return (self.project, self.id) > (other.project, other.id)

  def __ge__(self, other):
    return (self.project, self.id) >= (other.project, other.id)

  def __repr__(self):
    return '{0}/{1}'.format(self.project, self.id)


def _ValidateServicesAreSubset(filtered_services, all_services):
  not_found_services = set(filtered_services) - set(all_services)
  if not_found_services:
    raise ServicesNotFoundError.FromServiceLists(not_found_services,
                                                 all_services)


def GetMatchingServices(all_services, args_services):
  """Return a list of services to act on based on user arguments.

  Args:
    all_services: list of Services representing all services in the project.
    args_services: list of string, service IDs to filter for, from arguments
      given by the user to the command line. If empty, match all services.

  Returns:
    list of matching Services sorted by the order they were given to the
      command line.

  Raises:
    ServiceValidationError: If an improper combination of arguments is given
  """
  if not args_services:
    args_services = sorted(s.id for s in all_services)
  else:
    _ValidateServicesAreSubset(args_services, [s.id for s in all_services])
  matching_services = []
  # Match the order to the order of arguments.
  for service_id in args_services:
    matching_services += [s for s in all_services if s.id == service_id]
  return matching_services


def ParseTrafficAllocations(args_allocations, split_method):
  """Parses the user-supplied allocations into a format acceptable by the API.

  Args:
    args_allocations: The raw allocations passed on the command line. A dict
      mapping version_id (str) to the allocation (float).
    split_method: Whether the traffic will be split by ip or cookie. This
      affects the format we specify the splits in.

  Returns:
    A dict mapping version id (str) to traffic split (float).

  Raises:
    ServicesSplitTrafficError: if the sum of traffic allocations is zero.
  """
  # Splitting by IP allows 2 decimal places, splitting by cookie allows 3.
  max_decimal_places = 2 if split_method == 'ip' else 3
  sum_of_splits = sum([float(s) for s in args_allocations.values()])

  err = ServicesSplitTrafficError(
      'Cannot set traffic split to zero. If you would like a version to '
      'receive no traffic, send 100% of traffic to other versions or delete '
      'the service.')

  # Prevent division by zero
  if sum_of_splits == 0.0:
    raise err

  allocations = {}
  for version, split in six.iteritems(args_allocations):
    allocation = float(split) / sum_of_splits
    allocation = round(allocation, max_decimal_places)
    if allocation == 0.0:
      raise err
    allocations[version] = allocation

  # The API requires that these sum to 1.0. This is hard to get exactly correct,
  # (think .33, .33, .33) so we take our difference and subtract it from the
  # first maximum element of our sorted allocations dictionary
  total_splits = round(sum(allocations.values()), max_decimal_places)
  difference = total_splits - 1.0

  max_split = max(allocations.values())
  for version, split in sorted(allocations.items()):
    if max_split == split:
      allocations[version] -= difference
      break
  return allocations


def DeleteServices(api_client, services):
  """Delete the given services."""
  errors = {}
  for service in services:
    try:
      operations_util.CallAndCollectOpErrors(
          api_client.DeleteService, service.id)
    except operations_util.MiscOperationError as err:
      errors[service.id] = six.text_type(err)

  if errors:
    printable_errors = {}
    for service_id, error_msg in errors.items():
      printable_errors[service_id] = '[{0}]: {1}'.format(service_id,
                                                         error_msg)
    raise ServicesDeleteError(
        'Issue deleting {0}: [{1}]\n\n'.format(
            text.Pluralize(len(printable_errors), 'service'),
            ', '.join(list(printable_errors.keys()))) +
        '\n\n'.join(list(printable_errors.values())))
