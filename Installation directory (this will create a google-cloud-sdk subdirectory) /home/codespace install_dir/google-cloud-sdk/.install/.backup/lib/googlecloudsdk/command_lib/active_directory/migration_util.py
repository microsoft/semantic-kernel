# -*- coding: utf-8 -*- #
# Copyright 2022 Google Inc. All Rights Reserved.
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
"""Utilities for `gcloud active-directory`."""
from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.command_lib.active_directory import util


def UpdateOnPremSIDDetails(domain_ref, args, request):
  """Generate Migrating Domain Details."""
  onprem_arg = args.onprem_domains
  disable_sid_domains = args.disable_sid_filtering_domains or []

  messages = util.GetMessagesForResource(domain_ref)
  on_prem_dets = []
  for name in onprem_arg or []:
    disable_sid_filter = False
    if name in disable_sid_domains:
      disable_sid_filter = True
    onprem_req = messages.OnPremDomainDetails(
        domainName=name,
        disableSidFiltering=disable_sid_filter)
    on_prem_dets.append(onprem_req)
  request.enableMigrationRequest = messages.EnableMigrationRequest(
      migratingDomains=on_prem_dets)
  return request
