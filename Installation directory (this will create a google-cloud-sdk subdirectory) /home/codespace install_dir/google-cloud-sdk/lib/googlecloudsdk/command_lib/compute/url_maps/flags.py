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
"""Flags and helpers for the compute url-maps commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.command_lib.compute import completers as compute_completers
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.util import completers

DEFAULT_LIST_FORMAT = """\
    table(
      name,
      defaultService.type_suffix()
    )"""


class GlobalUrlMapsCompleter(compute_completers.ListCommandCompleter):

  def __init__(self, **kwargs):
    super(GlobalUrlMapsCompleter, self).__init__(
        collection='compute.urlMaps',
        list_command=('compute url-maps list --global --uri'),
        **kwargs)


class RegionalUrlMapsCompleter(compute_completers.ListCommandCompleter):

  def __init__(self, **kwargs):
    super(RegionalUrlMapsCompleter, self).__init__(
        collection='compute.regionUrlMaps',
        list_command='compute url-maps list --filter=region:* --uri',
        **kwargs)


class UrlMapsCompleter(completers.MultiResourceCompleter):

  def __init__(self, **kwargs):
    super(UrlMapsCompleter, self).__init__(
        completers=[GlobalUrlMapsCompleter, RegionalUrlMapsCompleter], **kwargs)


def UrlMapArgument(required=True, plural=False):
  return compute_flags.ResourceArgument(
      name='url_map',
      resource_name='URL map',
      completer=UrlMapsCompleter,
      plural=plural,
      required=required,
      global_collection='compute.urlMaps',
      regional_collection='compute.regionUrlMaps',
      region_explanation=compute_flags.REGION_PROPERTY_EXPLANATION)


def UrlMapArgumentForTargetProxy(required=True, proxy_type='HTTP'):
  return compute_flags.ResourceArgument(
      name='--url-map',
      resource_name='URL map',
      completer=UrlMapsCompleter,
      plural=False,
      required=required,
      global_collection='compute.urlMaps',
      regional_collection='compute.regionUrlMaps',
      short_help=(
          'A reference to a URL map resource that defines the mapping of '
          'URLs to backend services.'),
      detailed_help="""\
        A reference to a URL map resource. A URL map defines the mapping of URLs
        to backend services. Before you can refer to a URL map, you must
        create the URL map. To delete a URL map that a target proxy is referring
        to, you must first delete the target {0} proxy.
        """.format(proxy_type))
