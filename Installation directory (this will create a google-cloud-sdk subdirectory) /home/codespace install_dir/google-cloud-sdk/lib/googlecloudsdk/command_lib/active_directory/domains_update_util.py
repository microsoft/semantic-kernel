# -*- coding: utf-8 -*- #
# Copyright 2019 Google Inc. All Rights Reserved.
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
"""Utility for updating Managed Microsoft AD domains."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.active_directory import exceptions
from googlecloudsdk.command_lib.active_directory import util
from googlecloudsdk.command_lib.util.args import labels_util
from googlecloudsdk.core.console import console_io


def CheckFieldsSpecified(unused_domain_ref, args, patch_request):
  """Check that update command has one of these flags specified."""
  update_args = [
      'clear_labels',
      'remove_labels',
      'update_labels',
      'add_region',
      'remove_region',
      'add_authorized_networks',
      'remove_authorized_networks',
      'enable_audit_logs',
  ]
  if any(args.IsSpecified(update_arg) for update_arg in update_args):
    return patch_request
  raise exceptions.ActiveDirectoryError(
      'Must specify at least one field to update. Try --help.')


def GetExistingDomain(domain_ref):
  """Fetch existing AD domain."""
  client = util.GetClientForResource(domain_ref)
  messages = util.GetMessagesForResource(domain_ref)
  get_req = messages.ManagedidentitiesProjectsLocationsGlobalDomainsGetRequest(
      name=domain_ref.RelativeName())
  return client.projects_locations_global_domains.Get(get_req)


def UpdatePatchRequest(domain_ref, unused_args, patch_request):
  """Fetch existing AD domain to update and add it to Patch request."""
  patch_request.domain = GetExistingDomain(domain_ref)
  return patch_request


def AddFieldToUpdateMask(field, patch_request):
  """Adds name of field to update mask."""
  update_mask = patch_request.updateMask
  if update_mask:
    if update_mask.count(field) == 0:
      patch_request.updateMask = update_mask + ',' + field
  else:
    patch_request.updateMask = field
  return patch_request


def UpdateLabels(domain_ref, args, patch_request):
  """Updates labels of domain."""
  labels_diff = labels_util.Diff.FromUpdateArgs(args)
  if labels_diff.MayHaveUpdates():
    patch_request = AddFieldToUpdateMask('labels', patch_request)
    messages = util.GetMessagesForResource(domain_ref)
    new_labels = labels_diff.Apply(messages.Domain.LabelsValue,
                                   patch_request.domain.labels).GetOrNone()
    if new_labels:
      patch_request.domain.labels = new_labels
  return patch_request


def ProcessPfxFile(domain_ref, args, request):
  """Reads the pfx file into the LDAPSSettings proto and updates the request."""
  if args.certificate_pfx_file:
    if not request.lDAPSSettings:
      messages = util.GetMessagesForResource(domain_ref)
      settings = messages.LDAPSSettings()
      request.lDAPSSettings = settings
    request.lDAPSSettings.certificatePfx = args.certificate_pfx_file
    request = AddFieldToUpdateMask('certificatePfx', request)
    request = AddFieldToUpdateMask('certificatePassword', request)
  return request


def GetPfxPasssword():
  """Prompt for user input of pfx password."""
  cred = console_io.PromptPassword(
      'Please enter the password used the encrypt the pfx certificate: ')
  return cred


def ReadPfxPasswordIfNeeded(unused_ref, args, request):
  """Allows for the pfx password to be read from stdin if not specified."""
  del unused_ref
  if args.certificate_password:
    request.lDAPSSettings.certificatePassword = args.certificate_password
    return request
  if args.clear_certificates:
    return request
  secret = GetPfxPasssword()
  request.lDAPSSettings.certificatePassword = secret
  return request


def ClearCertificates(unused_ref, args, request):
  del unused_ref
  if args.clear_certificates:
    request = AddFieldToUpdateMask('certificatePfx', request)
    request = AddFieldToUpdateMask('certificatePassword', request)
  return request
