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
"""CRM API Liens utilities."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.core import resources

LIENS_API_VERSION = 'v1'


def LiensClient():
  return apis.GetClientInstance('cloudresourcemanager', LIENS_API_VERSION)


def LiensRegistry():
  registry = resources.REGISTRY.Clone()
  registry.RegisterApiByName('cloudresourcemanager', LIENS_API_VERSION)
  return registry


def LiensService():
  return LiensClient().liens


def LiensMessages():
  return apis.GetMessagesModule('cloudresourcemanager', LIENS_API_VERSION)


def LienNameToId(lien_name):
  return lien_name[len('liens/'):]


def LienIdToName(lien_id):
  return 'liens/{0}'.format(lien_id)


def GetLien(lien_id):
  return LiensService().Get(
      LiensMessages().CloudresourcemanagerLiensGetRequest(LiensId=lien_id))


def GetUri(resource):
  """Returns the uri for resource."""
  lien_id = LienNameToId(resource.name)
  lien_ref = LiensRegistry().Parse(
      None, params={'liensId': lien_id},
      collection='cloudresourcemanager.liens')
  return lien_ref.SelfLink()
