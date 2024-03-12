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

"""Common helper methods for Genomics commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import abc
import re
from googlecloudsdk.api_lib.genomics import genomics_util
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.core import resources
import six


def CreateFromName(name):
  """Creates a client and resource reference for a name.

  Args:
    name: An operation name, optionally including projects/, operations/, and a
        project name.

  Returns:
    A tuple containing the genomics client and resource reference.
  """
  client = None

  if re.search('[a-zA-Z]', name.split('/')[-1]):
    client = GenomicsV1ApiClient()
  else:
    client = GenomicsV2ApiClient()

  return client, client.ResourceFromName(name)


class GenomicsApiClient(six.with_metaclass(abc.ABCMeta, object)):
  """Base class for clients for accessing the genomics API.
  """

  def __init__(self, version):
    self._messages = genomics_util.GetGenomicsMessages(version)
    self._client = genomics_util.GetGenomicsClient(version)
    self._registry = resources.REGISTRY.Clone()
    self._registry.RegisterApiByName('genomics', version)

  @abc.abstractmethod
  def ResourceFromName(self, name):
    raise NotImplementedError()

  @abc.abstractmethod
  def Poller(self):
    raise NotImplementedError()

  @abc.abstractmethod
  def GetOperation(self, resource):
    raise NotImplementedError()

  @abc.abstractmethod
  def CancelOperation(self, resource):
    raise NotImplementedError()


class GenomicsV1ApiClient(GenomicsApiClient):
  """Client for accessing the V1 genomics API.
  """

  def __init__(self):
    super(GenomicsV1ApiClient, self).__init__('v1')

  def ResourceFromName(self, name):
    return self._registry.Parse(name, collection='genomics.operations')

  def Poller(self):
    return waiter.CloudOperationPollerNoResources(self._client.operations)

  def GetOperation(self, resource):
    return self._client.operations.Get(
        self._messages.GenomicsOperationsGetRequest(
            name=resource.RelativeName()))

  def CancelOperation(self, resource):
    return self._client.operations.Cancel(
        self._messages.GenomicsOperationsCancelRequest(
            name=resource.RelativeName()))


class GenomicsV2ApiClient(GenomicsApiClient):
  """Client for accessing the V2 genomics API.
  """

  def __init__(self):
    super(GenomicsV2ApiClient, self).__init__('v2alpha1')

  def ResourceFromName(self, name):
    return self._registry.Parse(
        name, collection='genomics.projects.operations',
        params={'projectsId': genomics_util.GetProjectId()})

  def Poller(self):
    return waiter.CloudOperationPollerNoResources(
        self._client.projects_operations)

  def GetOperation(self, resource):
    return self._client.projects_operations.Get(
        self._messages.GenomicsProjectsOperationsGetRequest(
            name=resource.RelativeName()))

  def CancelOperation(self, resource):
    return self._client.projects_operations.Cancel(
        self._messages.GenomicsProjectsOperationsCancelRequest(
            name=resource.RelativeName()))
