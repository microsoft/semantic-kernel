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

"""Compute resource completers for the core.cache.completion_cache module."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os

from googlecloudsdk.command_lib.resource_manager import completers as resource_manager_completers
from googlecloudsdk.command_lib.util import completers
from googlecloudsdk.command_lib.util import parameter_info_lib
from googlecloudsdk.core import exceptions
from googlecloudsdk.core.util import encoding


class Error(exceptions.Error):
  """Exceptions for this module."""


class TestParametersRequired(Error):
  """Test parameters must be exported in _ARGCOMPLETE_TEST."""


# resource param project aggregators


class ResourceParamCompleter(completers.ResourceParamCompleter):

  def ParameterInfo(self, parsed_args, argument):
    return parameter_info_lib.ParameterInfoByConvention(
        parsed_args,
        argument,
        self.collection,
        updaters={
            'project': (resource_manager_completers.ProjectCompleter, True),
        },
    )


# common parameter completers


class RegionsCompleter(ResourceParamCompleter):
  """The region completer."""

  def __init__(self, **kwargs):
    super(RegionsCompleter, self).__init__(
        collection='compute.regions',
        list_command='compute regions list --uri',
        param='region',
        timeout=8*60*60,
        **kwargs)


class ZonesCompleter(ResourceParamCompleter):
  """The zone completer."""

  def __init__(self, **kwargs):
    super(ZonesCompleter, self).__init__(
        collection='compute.zones',
        list_command='compute zones list --uri',
        param='zone',
        timeout=8*60*60,
        **kwargs)


# completers by parameter name convention


COMPLETERS_BY_CONVENTION = {
    'project': (resource_manager_completers.ProjectCompleter, True),
    'region': (RegionsCompleter, False),
    'zone': (ZonesCompleter, False),
}


# list command project aggregators


class ListCommandParameterInfo(parameter_info_lib.ParameterInfoByConvention):

  def GetFlag(self, parameter_name, parameter_value=None,
              check_properties=True, for_update=False):
    if for_update and self.GetDest(parameter_name) in ('region', 'zone'):
      return None
    return super(ListCommandParameterInfo, self).GetFlag(
        parameter_name,
        parameter_value=parameter_value,
        check_properties=check_properties,
        for_update=for_update,
    )


class ListCommandCompleter(completers.ListCommandCompleter):

  def ParameterInfo(self, parsed_args, argument):
    return ListCommandParameterInfo(
        parsed_args,
        argument,
        self.collection,
        updaters=COMPLETERS_BY_CONVENTION,
    )


class GlobalListCommandCompleter(ListCommandCompleter):
  """A global resource list command completer."""

  def ParameterInfo(self, parsed_args, argument):
    return ListCommandParameterInfo(
        parsed_args,
        argument,
        self.collection,
        additional_params=['global'],
        updaters=COMPLETERS_BY_CONVENTION,
    )


# completers referenced by multiple command groups and/or flags modules
#
# Search*Completer ResourceSearchCompleters have ListCommandCompleter
# variants that are currently the default.  The Search completers are currently
# for testing only.


class DisksCompleter(ListCommandCompleter):

  def __init__(self, **kwargs):
    super(DisksCompleter, self).__init__(
        collection='compute.disks',
        list_command='compute disks list --uri',
        **kwargs)


class DiskTypesRegionalCompleter(ListCommandCompleter):

  def __init__(self, **kwargs):
    super(DiskTypesRegionalCompleter, self).__init__(
        collection='compute.regionDiskTypes',
        api_version='alpha',
        list_command='alpha compute disk-types list --uri --filter=-zone:*',
        **kwargs)


class DiskTypesZonalCompleter(ListCommandCompleter):

  def __init__(self, **kwargs):
    super(DiskTypesZonalCompleter, self).__init__(
        collection='compute.diskTypes',
        api_version='alpha',
        list_command='alpha compute disk-types list --uri --filter=zone:*',
        **kwargs)


class DiskTypesCompleter(completers.MultiResourceCompleter):

  def __init__(self, **kwargs):
    super(DiskTypesCompleter, self).__init__(
        completers=[DiskTypesRegionalCompleter, DiskTypesZonalCompleter],
        **kwargs)


class HealthChecksCompleter(ListCommandCompleter):

  def __init__(self, **kwargs):
    super(HealthChecksCompleter, self).__init__(
        collection='compute.healthChecks',
        list_command='compute health-checks list --uri',
        **kwargs)


class HealthChecksCompleterAlpha(completers.MultiResourceCompleter):

  def __init__(self, **kwargs):
    super(HealthChecksCompleterAlpha, self).__init__(
        completers=[GlobalHealthChecksCompleter, RegionHealthChecksCompleter],
        **kwargs)


class GlobalHealthChecksCompleter(ListCommandCompleter):

  def __init__(self, **kwargs):
    super(GlobalHealthChecksCompleter, self).__init__(
        collection='compute.healthChecks',
        api_version='alpha',
        list_command='alpha compute health-checks list --global --uri',
        **kwargs)


class RegionHealthChecksCompleter(ListCommandCompleter):

  def __init__(self, **kwargs):
    super(RegionHealthChecksCompleter, self).__init__(
        collection='compute.regionHealthChecks',
        api_version='alpha',
        list_command='alpha compute health-checks list --filter=region:* --uri',
        **kwargs)


class SearchHealthChecksCompleter(completers.ResourceSearchCompleter):

  def __init__(self, **kwargs):
    super(SearchHealthChecksCompleter, self).__init__(
        collection='compute.healthChecks',
        **kwargs)


class HttpHealthChecksCompleter(ListCommandCompleter):

  def __init__(self, **kwargs):
    super(HttpHealthChecksCompleter, self).__init__(
        collection='compute.httpHealthChecks',
        list_command='compute http-health-checks list --uri',
        **kwargs)


class SearchHttpHealthChecksCompleter(completers.ResourceSearchCompleter):

  def __init__(self, **kwargs):
    super(SearchHttpHealthChecksCompleter, self).__init__(
        collection='compute.httpHealthChecks',
        **kwargs)


class HttpsHealthChecksCompleter(ListCommandCompleter):

  def __init__(self, **kwargs):
    super(HttpsHealthChecksCompleter, self).__init__(
        collection='compute.httpsHealthChecks',
        list_command='compute https-health-checks list --uri',
        **kwargs)


class SearchHttpsHealthChecksCompleter(completers.ResourceSearchCompleter):

  def __init__(self, **kwargs):
    super(SearchHttpsHealthChecksCompleter, self).__init__(
        collection='compute.httpsHealthChecks',
        **kwargs)


class InstancesCompleter(ListCommandCompleter):

  def __init__(self, **kwargs):
    super(InstancesCompleter, self).__init__(
        collection='compute.instances',
        list_command='compute instances list --uri',
        **kwargs)


class SearchInstancesCompleter(completers.ResourceSearchCompleter):

  def __init__(self, **kwargs):
    super(SearchInstancesCompleter, self).__init__(
        collection='compute.instances',
        **kwargs)


class InstanceGroupsCompleter(ListCommandCompleter):

  def __init__(self, **kwargs):
    super(InstanceGroupsCompleter, self).__init__(
        collection='compute.instanceGroups',
        list_command='compute instance-groups unmanaged list --uri',
        **kwargs)


class InstanceTemplatesCompleter(ListCommandCompleter):

  def __init__(self, **kwargs):
    super(InstanceTemplatesCompleter, self).__init__(
        collection='compute.instanceTemplates',
        list_command='compute instance-templates list --uri',
        **kwargs)


class SearchInstanceTemplatesCompleter(completers.ResourceSearchCompleter):

  def __init__(self, **kwargs):
    super(SearchInstanceTemplatesCompleter, self).__init__(
        collection='compute.instanceTemplates',
        **kwargs)


class MachineImagesCompleter(ListCommandCompleter):

  def __init__(self, **kwargs):
    super(MachineImagesCompleter, self).__init__(
        collection='compute.machineImages',
        list_command='compute machine-images list --uri',
        **kwargs)


class SearchMachineImagesCompleter(completers.ResourceSearchCompleter):

  def __init__(self, **kwargs):
    super(SearchMachineImagesCompleter, self).__init__(
        collection='compute.machineImages',
        **kwargs)


class InstantSnapshotsCompleter(completers.MultiResourceCompleter):

  def __init__(self, **kwargs):
    super(InstantSnapshotsCompleter, self).__init__(
        completers=[
            RegionInstantSnapshotsCompleter, ZoneInstantSnapshotsCompleter
        ],
        **kwargs)


class ZoneInstantSnapshotsCompleter(ListCommandCompleter):

  def __init__(self, **kwargs):
    super(ZoneInstantSnapshotsCompleter, self).__init__(
        collection='compute.instantSnapshots',
        list_command='alpha compute instant-snapshots list --uri',
        api_version='alpha',
        **kwargs)


class RegionInstantSnapshotsCompleter(ListCommandCompleter):

  def __init__(self, **kwargs):
    super(RegionInstantSnapshotsCompleter, self).__init__(
        collection='compute.regionInstantSnapshots',
        list_command='alpha compute instant-snapshots list --uri',
        api_version='alpha',
        **kwargs)


class MachineTypesCompleter(ListCommandCompleter):

  def __init__(self, **kwargs):
    super(MachineTypesCompleter, self).__init__(
        collection='compute.machineTypes',
        list_command='compute machine-types list --uri',
        **kwargs)


class RoutesCompleter(ListCommandCompleter):

  def __init__(self, **kwargs):
    super(RoutesCompleter, self).__init__(
        collection='compute.routes',
        list_command='compute routes list --uri',
        **kwargs)


# completers for testing the completer framework


class TestCompleter(ListCommandCompleter):
  """A completer that checks env var _ARGCOMPLETE_TEST for completer info.

  For testing list command completers.

  The env var is a comma separated list of name=value items:
    collection=COLLECTION
      The collection name.
    list_command=COMMAND
      The gcloud list command string with gcloud omitted.
  """

  def __init__(self, **kwargs):
    test_parameters = encoding.GetEncodedValue(os.environ, '_ARGCOMPLETE_TEST',
                                               'parameters=bad')
    kwargs = dict(kwargs)
    for pair in test_parameters.split(','):
      name, value = pair.split('=')
      kwargs[name] = value
    if 'collection' not in kwargs or 'list_command' not in kwargs:
      raise TestParametersRequired(
          'Specify test completer parameters in the _ARGCOMPLETE_TEST '
          'environment variable. It is a comma-separated separated list of '
          'name=value test parameters and must contain at least '
          '"collection=COLLECTION,list_command=LIST COMMAND" parameters.')
    super(TestCompleter, self).__init__(**kwargs)
