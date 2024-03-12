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
"""Completers for workbench."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.command_lib.util import completers
from googlecloudsdk.core import properties

LOCATION_COLLECTION = 'notebooks.projects.locations'
INSTANCE_COLLECTION = 'notebooks.projects.locations.instances'
REGION_COLLECTION = 'compute.regions'


class LocationCompleter(completers.ListCommandCompleter):

  def __init__(self, **kwargs):
    super(LocationCompleter, self).__init__(
        collection=LOCATION_COLLECTION,
        list_command='workbench locations list --uri',
        **kwargs)


class InstanceCompleter(completers.ListCommandCompleter):

  def __init__(self, **kwargs):
    location_property = properties.VALUES.notebooks.location.Get(required=True)
    super(InstanceCompleter, self).__init__(
        collection=INSTANCE_COLLECTION,
        list_command='workbench instances list --location={} --uri'.format(
            location_property),
        **kwargs)


class RegionCompleter(completers.ListCommandCompleter):

  def __init__(self, **kwargs):
    super(RegionCompleter, self).__init__(
        collection=REGION_COLLECTION,
        list_command='compute regions list --uri',
        **kwargs)
