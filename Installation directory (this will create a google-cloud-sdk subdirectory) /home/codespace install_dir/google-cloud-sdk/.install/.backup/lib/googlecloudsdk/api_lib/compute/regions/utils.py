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
"""Common classes and functions for regions."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import request_helper
from googlecloudsdk.api_lib.compute import utils
from googlecloudsdk.command_lib.compute import exceptions
from googlecloudsdk.core.console import console_io


class RegionResourceFetcher(object):
  """Helper class for working with regions."""

  def __init__(self, client):
    self.compute = client.apitools_client
    self.messages = client.messages
    self.http = self.compute.http
    self.batch_url = client.batch_url

  def GetRegions(self, resource_refs):
    """Fetches region resources."""
    # TODO(b/34445512)
    errors = []
    requests = []
    region_names = set()
    for resource_ref in resource_refs:
      if (resource_ref.project, resource_ref.region) not in region_names:
        region_names.add((resource_ref.project, resource_ref.region))
        requests.append((
            self.compute.regions,
            'Get',
            self.messages.ComputeRegionsGetRequest(
                project=resource_ref.project,
                region=resource_ref.region)))
    if requests:
      res = list(request_helper.MakeRequests(
          requests=requests,
          http=self.http,
          batch_url=self.batch_url,
          errors=errors))
    else:
      return None

    if errors:
      return None
    else:
      return res

  def WarnForRegionalCreation(self, resource_refs):
    """Warns the user if a region has upcoming deprecation."""
    regions = self.GetRegions(resource_refs)
    if not regions:
      return

    prompts = []
    regions_with_deprecated = []
    for region in regions:
      if region.deprecated:
        regions_with_deprecated.append(region)

    if not regions_with_deprecated:
      return

    if regions_with_deprecated:
      phrases = []
      if len(regions_with_deprecated) == 1:
        phrases = ('region is', 'this region', 'the')
      else:
        phrases = ('regions are', 'these regions', 'their')
      title = ('\n'
               'WARNING: The following selected {0} deprecated.'
               ' All resources in {1} will be deleted after'
               ' {2} turndown date.'.format(phrases[0], phrases[1], phrases[2]))
      printable_deprecated_regions = []
      for region in regions_with_deprecated:
        if region.deprecated.deleted:
          printable_deprecated_regions.append(('[{0}] {1}').format(
              region.name, region.deprecated.deleted))
        else:
          printable_deprecated_regions.append('[{0}]'.format(region.name))
      prompts.append(utils.ConstructList(title, printable_deprecated_regions))

    final_message = ' '.join(prompts)
    if not console_io.PromptContinue(message=final_message):
      raise exceptions.AbortedError('Creation aborted by user.')
