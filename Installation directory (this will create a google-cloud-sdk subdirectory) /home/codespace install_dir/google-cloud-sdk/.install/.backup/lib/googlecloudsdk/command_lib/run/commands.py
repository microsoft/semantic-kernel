# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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
"""Base classes for shared code between Cloud Run commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.run import connection_context


SUPPORTS_PZS_ALIAS = (
    "labels.'run.googleapis.com/supportsPzs':alias='supportsPzs'"
)
SATISFIES_PZS_ALIAS = (
    "metadata.labels.'run.googleapis.com/satisfiesPzs':alias='satisfiesPzs'"
)


class List(base.ListCommand):
  """Base class for `run [resources] list` commands."""

  # Fully specified client endpoint for a resource, including region.
  # Examples:
  #   https://us-central1-run.googleapis.com/
  #   https://kubernetes.default/
  complete_api_endpoint = None

  # Patially specified client endpoint for a resource, missing region.
  # Examples:
  #   https://run.googleapis.com/
  partial_api_endpoint = None

  @classmethod
  def _GetResourceUri(cls, resource):
    """Get uri for resource.

    This is a @classmethod because this method is called by
    googlecloudsdk.calliope.display_info.DisplayInfo outside of a List instance.

    Args:
      resource: a googlecloudsdk.command_lib.run.k8s_object.KubernetesObject
        object

    Returns:
      uri: str of the resource's uri
    """
    complete_endpoint = cls.complete_api_endpoint
    if not complete_endpoint:
      try:
        region = resource.locationId
      except AttributeError:
        region = resource.region
      complete_endpoint = connection_context.DeriveRegionalEndpoint(
          cls.partial_api_endpoint, region)
    return '{}/{}'.format(
        complete_endpoint.rstrip('/'), getattr(resource, 'self_link', ''))

  @classmethod
  def SetCompleteApiEndpoint(cls, complete_api_endpoint):
    cls.complete_api_endpoint = complete_api_endpoint

  @classmethod
  def SetPartialApiEndpoint(cls, partial_api_endpoint):
    cls.partial_api_endpoint = partial_api_endpoint


def SortByName(list_response):
  """Return the list_response sorted by name."""
  return sorted(list_response, key=lambda x: x.name)
