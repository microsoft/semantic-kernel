# -*- coding: utf-8 -*- #
# Copyright 2016 Google LLC. All Rights Reserved.
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
"""Flags and helpers for the compute operations commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.command_lib.compute import completers as compute_completers
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.util import completers


class GlobalOperationsCompleter(compute_completers.ListCommandCompleter):

  def __init__(self, **kwargs):
    super(GlobalOperationsCompleter, self).__init__(
        collection='compute.globalOperations',
        list_command=('compute operations list --uri '
                      '--filter="-region:* -zone:*"'),
        **kwargs)


class RegionalOperationsCompleter(compute_completers.ListCommandCompleter):

  def __init__(self, **kwargs):
    super(RegionalOperationsCompleter, self).__init__(
        collection='compute.regionOperations',
        list_command='compute operations list --uri --filter=region:*',
        **kwargs)


class ZonalOperationsCompleter(
    compute_completers.ListCommandCompleter):

  def __init__(self, **kwargs):
    super(ZonalOperationsCompleter, self).__init__(
        collection='compute.zoneOperations',
        list_command='compute operations list --uri --filter=zone:*',
        **kwargs)


class OperationsCompleter(completers.MultiResourceCompleter):

  def __init__(self, **kwargs):
    super(OperationsCompleter, self).__init__(
        completers=[GlobalOperationsCompleter,
                    RegionalOperationsCompleter,
                    ZonalOperationsCompleter],
        **kwargs)


COMPUTE_OPERATION_ARG = compute_flags.ResourceArgument(
    resource_name='operation',
    completer=OperationsCompleter,
    global_collection='compute.globalOperations',
    regional_collection='compute.regionOperations',
    zonal_collection='compute.zoneOperations',
    required=True,
    plural=False,
    short_help='Name of the operation returned by an asynchronous command. '
               'Use `gcloud compute operations list` to display recent '
               'operations.'
)
