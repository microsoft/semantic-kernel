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
"""Utilities for manipulating GCE instances running an App Engine project."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import re

from googlecloudsdk.core import exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core.console import console_io
from six.moves import filter  # pylint: disable=redefined-builtin
from six.moves import map  # pylint: disable=redefined-builtin


class InvalidInstanceSpecificationError(exceptions.Error):
  pass


class SelectInstanceError(exceptions.Error):
  pass


class Instance(object):
  """Value class for instances running the current App Engine project."""

  # TODO(b/27900246): Once API supports "Get" verb, convert to use resource
  # parser.
  _INSTANCE_NAME_PATTERN = ('apps/(?P<project>.*)/'
                            'services/(?P<service>.*)/'
                            'versions/(?P<version>.*)/'
                            'instances/(?P<instance>.*)')

  def __init__(self, service, version, id_, instance=None):
    self.service = service
    self.version = version
    self.id = id_
    self.instance = instance  # The Client API instance object

  @classmethod
  def FromInstanceResource(cls, instance):
    match = re.match(cls._INSTANCE_NAME_PATTERN, instance.name)
    service = match.group('service')
    version = match.group('version')
    return cls(service, version, instance.id, instance)

  @classmethod
  def FromResourcePath(cls, path, service=None, version=None):
    """Convert a resource path into an AppEngineInstance.

    A resource path is of the form '<service>/<version>/<instance>'.
    '<service>' and '<version>' can be omitted, in which case they are None in
    the resulting instance.

    >>> (AppEngineInstance.FromResourcePath('a/b/c') ==
         ...  AppEngineInstance('a', 'b', 'c'))
    True
    >>> (AppEngineInstance.FromResourcePath('b/c', service='a') ==
    ...  AppEngineInstance('a', 'b', 'c'))
    True
    >>> (AppEngineInstance.FromResourcePath('c', service='a', version='b') ==
    ...  AppEngineInstance('a', 'b', 'c'))
    True

    Args:
      path: str, the resource path
      service: the service of the instance (replaces the service from the
        resource path)
      version: the version of the instance (replaces the version from the
        resource path)

    Returns:
      AppEngineInstance, an AppEngineInstance representing the path

    Raises:
      InvalidInstanceSpecificationError: if the instance is over- or
        under-specified
    """
    parts = path.split('/')
    if len(parts) == 1:
      path_service, path_version, instance = None, None, parts[0]
    elif len(parts) == 2:
      path_service, path_version, instance = None, parts[0], parts[1]
    elif len(parts) == 3:
      path_service, path_version, instance = parts
    else:
      raise InvalidInstanceSpecificationError(
          'Instance resource path is incorrectly specified. '
          'Please provide at most one service, version, and instance id, '
          '.\n\n'
          'You provided:\n' + path)

    if path_service and service and path_service != service:
      raise InvalidInstanceSpecificationError(
          'Service [{0}] is inconsistent with specified instance [{1}].'.format(
              service, path))
    service = service or path_service

    if path_version and version and path_version != version:
      raise InvalidInstanceSpecificationError(
          'Version [{0}] is inconsistent with specified instance [{1}].'.format(
              version, path))
    version = version or path_version

    return cls(service, version, instance)

  def __eq__(self, other):
    return (type(self) is type(other) and
            self.service == other.service and
            self.version == other.version and
            self.id == other.id)

  def __ne__(self, other):
    return not self == other

  # needed for set comparisons in tests
  def __hash__(self):
    return hash((self.service, self.version, self.id))

  def __str__(self):
    return '/'.join(filter(bool, [self.service, self.version, self.id]))

  def __cmp__(self, other):
    return cmp((self.service, self.version, self.id),
               (other.service, other.version, other.id))


def FilterInstances(instances, service=None, version=None, instance=None):
  """Filter a list of App Engine instances.

  Args:
    instances: list of AppEngineInstance, all App Engine instances
    service: str, the name of the service to filter by or None to match all
      services
    version: str, the name of the version to filter by or None to match all
      versions
    instance: str, the instance id to filter by or None to match all versions.

  Returns:
    list of instances matching the given filters
  """
  matching_instances = []
  for provided_instance in instances:
    if ((not service or provided_instance.service == service) and
        (not version or provided_instance.version == version) and
        (not instance or provided_instance.id == instance)):
      matching_instances.append(provided_instance)
  return matching_instances


def GetMatchingInstance(instances, service=None, version=None, instance=None):
  """Return exactly one matching instance.

  If instance is given, filter down based on the given criteria (service,
  version, instance) and return the matching instance (it is an error unless
  exactly one instance matches).

  Otherwise, prompt the user to select the instance interactively.

  Args:
    instances: list of AppEngineInstance, all instances to select from
    service: str, a service to filter by or None to include all services
    version: str, a version to filter by or None to include all versions
    instance: str, an instance ID to filter by. If not given, the instance will
      be selected interactively.

  Returns:
    AppEngineInstance, an instance from the given list.

  Raises:
    InvalidInstanceSpecificationError: if no matching instances or more than one
      matching instance were found.
  """
  if not instance:
    return SelectInstanceInteractive(instances, service=service,
                                     version=version)

  matching = FilterInstances(instances, service, version, instance)
  if len(matching) > 1:
    raise InvalidInstanceSpecificationError(
        'More than one instance matches the given specification.\n\n'
        'Matching instances: {0}'.format(list(sorted(map(str, matching)))))
  elif not matching:
    raise InvalidInstanceSpecificationError(
        'No instances match the given specification.\n\n'
        'All instances: {0}'.format(list(sorted(map(str, instances)))))
  return matching[0]


def SelectInstanceInteractive(all_instances, service=None, version=None):
  """Interactively choose an instance from a provided list.

  Example interaction:

      Which service?
       [1] default
       [2] service1
      Please enter your numeric choice:  1

      Which version?
       [1] v1
       [2] v2
      Please enter your numeric choice:  1

      Which instance?
       [1] i1
       [2] i2
      Please enter your numeric choice:  1

  Skips any prompts with only one option.

  Args:
    all_instances: list of AppEngineInstance, the list of instances to drill
      down on.
    service: str. If provided, skip the service prompt.
    version: str. If provided, skip the version prompt.

  Returns:
    AppEngineInstance, the selected instance from the list.

  Raises:
    SelectInstanceError: if no versions matching the criteria can be found or
      prompts are disabled.
  """
  if properties.VALUES.core.disable_prompts.GetBool():
    raise SelectInstanceError(
        'Cannot interactively select instances with prompts disabled.')

  # Defined here to close over all_instances for the error message
  def _PromptOptions(options, type_):
    """Given an iterable options of type type_, prompt and return one."""
    options = sorted(set(options), key=str)
    if len(options) > 1:
      idx = console_io.PromptChoice(options, message='Which {0}?'.format(type_))
    elif len(options) == 1:
      idx = 0
      log.status.Print('Choosing [{0}] for {1}.\n'.format(options[0], type_))
    else:
      if all_instances:
        msg = ('No instances could be found matching the given criteria.\n\n'
               'All instances:\n' +
               '\n'.join(
                   map('* [{0}]'.format, sorted(all_instances, key=str))))
      else:
        msg = 'No instances were found for the current project [{0}].'.format(
            properties.VALUES.core.project.Get(required=True))
      raise SelectInstanceError(msg)
    return options[idx]

  matching_instances = FilterInstances(all_instances, service, version)

  service = _PromptOptions((i.service for i in matching_instances), 'service')
  matching_instances = FilterInstances(matching_instances, service=service)

  version = _PromptOptions((i.version for i in matching_instances), 'version')
  matching_instances = FilterInstances(matching_instances, version=version)

  return _PromptOptions(matching_instances, 'instance')
