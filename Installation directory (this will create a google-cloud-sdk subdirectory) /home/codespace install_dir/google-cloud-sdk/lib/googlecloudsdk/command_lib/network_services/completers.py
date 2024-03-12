# -*- coding: utf-8 -*- #
# Copyright 2021 Google LLC. All Rights Reserved.
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
"""Networkservices resource completers for the completion_cache module."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.command_lib.util import completers
from googlecloudsdk.core import exceptions


class Error(exceptions.Error):
  """Exceptions for this module."""


class ServiceLoadBalancingPoliciesCompleter(completers.ListCommandCompleter):

  def __init__(self, **kwargs):
    super(ServiceLoadBalancingPoliciesCompleter, self).__init__(
        collection='networkservices.projects.locations.serviceLbPolicies',
        api_version='v1alpha1',
        list_command='network-services service-lb-policies list --location=global --uri',
        **kwargs)


class ServiceBindingsCompleter(completers.ListCommandCompleter):

  def __init__(self, **kwargs):
    super(ServiceBindingsCompleter, self).__init__(
        collection='networkservices.projects.locations.serviceBindings',
        list_command='network-services service-bindings list --location=global --uri',
        **kwargs)
