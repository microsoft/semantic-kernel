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
"""Declarative Request Hooks for Event Threat Detection custom modules."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import re

from googlecloudsdk.command_lib.scc.errors import InvalidSCCInputError
from googlecloudsdk.command_lib.scc.hooks import CleanUpUserInput

_PARENT_SUFFIX = "/eventThreatDetectionSettings"
_ETD_CUSTOM_MODULE_ID_PATTERN = re.compile("([0-9]{1,20})$")
_ETD_CUSTOM_MODULE_PATTERN = re.compile(
    "(organizations|projects|folders)/.*/eventThreatDetectionSettings/"
    "customModules/%s"
    % _ETD_CUSTOM_MODULE_ID_PATTERN.pattern
)
_ETD_EFFECTIVE_CUSTOM_MODULE_PATTERN = re.compile(
    "(organizations|projects|folders)/.*/eventThreatDetectionSettings/"
    "effectiveCustomModules/%s"
    % _ETD_CUSTOM_MODULE_ID_PATTERN.pattern
)
_ORGANIZATION_ID_PATTERN = re.compile("[0-9]{1,19}")
_ORGANIZATION_NAME_PATTERN = re.compile("organizations/[0-9]{1,19}")
_FOLDER_NAME_PATTERN = re.compile("folders/.*")
_PROJECT_NAME_PATTERN = re.compile("projects/.*")


def CreateEventThreatDetectionCustomModuleReqHook(ref, args, req):
  """Creates an Event Threat Detection custom module."""
  del ref
  req.parent = _ValidateAndGetParent(args)
  if args.enablement_state not in ["enabled", "disabled"]:
    raise InvalidSCCInputError(
        "Invalid custom module enablement state: %s. Enablement state must be"
        " enabled or disabled." % args.enablement_state)
  return req


def DeleteEventThreatDetectionCustomModuleReqHook(ref, args, req):
  """Deletes an Event Threat Detection custom module."""
  del ref
  parent = _ValidateAndGetParent(args)
  if parent is None:
    custom_module = _ValidateAndGetCustomModuleFullResourceName(args)
    req.name = custom_module
  else:
    custom_module_id = _ValidateAndGetCustomModuleId(args)
    req.name = parent + "/customModules/" + custom_module_id

  return req


def GetEventThreatDetectionCustomModuleReqHook(ref, args, req):
  """Gets an Event Threat Detection custom module."""
  del ref
  parent = _ValidateAndGetParent(args)
  if parent is None:
    custom_module = _ValidateAndGetCustomModuleFullResourceName(args)
    req.name = custom_module
  else:
    custom_module_id = _ValidateAndGetCustomModuleId(args)
    req.name = parent + "/customModules/" + custom_module_id
  return req


def GetEffectiveEventThreatDetectionCustomModuleReqHook(ref, args, req):
  """Gets an effective Event Threat Detection custom module."""
  del ref
  parent = _ValidateAndGetParent(args)
  if parent is None:
    custom_module = _ValidateAndGetEffectiveCustomModuleFullResourceName(args)
    req.name = custom_module
  else:
    custom_module_id = _ValidateAndGetCustomModuleId(args)
    req.name = parent + "/effectiveCustomModules/" + custom_module_id
  return req


def ListEventThreatDetectionCustomModulesReqHook(ref, args, req):
  """Lists Event Threat Detection custom modules."""
  del ref
  req.parent = _ValidateAndGetParent(args)
  return req


def ListDescendantEventThreatDetectionCustomModulesReqHook(ref, args, req):
  """Lists descendant Event Threat Detection custom modules."""
  del ref
  req.parent = _ValidateAndGetParent(args)
  return req


def ListEffectiveEventThreatDetectionCustomModulesReqHook(ref, args, req):
  """Lists effective Event Threat Detection custom modules."""
  del ref
  req.parent = _ValidateAndGetParent(args)
  return req


def ValidateEventThreatDetectionCustomModulesReqHook(ref, args, req):
  """Validates an Event Threat Detection custom module."""
  del ref
  parent = _ValidateAndGetParent(args)
  custom_module_name = ""
  if parent is None:
    custom_module_name = _ValidateAndGetCustomModuleFullResourceName(args)
  else:
    custom_module_id = _ValidateAndGetCustomModuleId(args)
    custom_module_name = parent + "/customModules/" + custom_module_id

  test_req = req.validateEventThreatDetectionCustomModuleRequest
  req.name = custom_module_name
  if test_req.eventThreatDetectionCustomModule is not None:
    test_req.eventThreatDetectionCustomModule.name = custom_module_name
  return req


def UpdateEventThreatDetectionCustomModuleReqHook(ref, args, req):
  """Updates an Event Threat Detection custom module."""
  del ref
  parent = _ValidateAndGetParent(args)
  if parent is None:
    custom_module = _ValidateAndGetCustomModuleFullResourceName(args)
    req.name = custom_module
  else:
    custom_module_id = _ValidateAndGetCustomModuleId(args)
    req.name = parent + "/customModules/" + custom_module_id
  req.updateMask = CleanUpUserInput(req.updateMask)
  if args.enablement_state not in ["enabled", "disabled", "inherited"]:
    raise InvalidSCCInputError(
        "Invalid custom module enablement state: %s. Enablement state must be"
        " enabled, disabled or inherited." % args.enablement_state)
  return req


def _ValidateAndGetCustomModuleId(args):
  """Validates customModuleId."""
  custom_module_id = args.custom_module

  if _ETD_CUSTOM_MODULE_ID_PATTERN.match(custom_module_id):
    return custom_module_id
  raise InvalidSCCInputError(
      "Custom module ID does not match the pattern '%s'."
      % _ETD_CUSTOM_MODULE_ID_PATTERN.pattern
  )


def _ValidateAndGetCustomModuleFullResourceName(args):
  """Validates a custom module's full resource name."""
  custom_module = args.custom_module
  if _ETD_CUSTOM_MODULE_PATTERN.match(custom_module):
    return custom_module
  raise _InvalidResourceName()


def _ValidateAndGetEffectiveCustomModuleFullResourceName(args):
  """Validates an effective custom module's full resource name."""
  custom_module = args.custom_module
  if _ETD_EFFECTIVE_CUSTOM_MODULE_PATTERN.match(custom_module):
    return custom_module
  raise _InvalidResourceName()


def _NormalizeOrganization(organization):
  """Validates an organization name or id."""
  if "/" in organization:
    if _ORGANIZATION_NAME_PATTERN.fullmatch(organization):
      return organization + _PARENT_SUFFIX
    raise _InvalidFullResourcePathForPattern(_ORGANIZATION_NAME_PATTERN)

  if _ORGANIZATION_ID_PATTERN.fullmatch(organization):
    return "organizations/" + organization + _PARENT_SUFFIX
  raise InvalidSCCInputError(
      "Organization does not match the pattern '%s'."
      % _ORGANIZATION_ID_PATTERN.pattern
  )


def _NormalizeFolder(folder):
  """Validates and normalizes a folder name."""
  if "/" in folder:
    if _FOLDER_NAME_PATTERN.fullmatch(folder):
      return folder + _PARENT_SUFFIX
    raise _InvalidFullResourcePathForPattern(_FOLDER_NAME_PATTERN)

  return "folders/" + folder + _PARENT_SUFFIX


def _NormalizeProject(project):
  """Validates and normalizes a project name."""
  if "/" in project:
    if _PROJECT_NAME_PATTERN.fullmatch(project):
      return project + _PARENT_SUFFIX
    raise _InvalidFullResourcePathForPattern(_PROJECT_NAME_PATTERN)

  return "projects/" + project + _PARENT_SUFFIX


def _ValidateAndGetParent(args):
  """Validates parent."""
  if args.organization is not None:
    return _NormalizeOrganization(args.organization)

  if args.folder is not None:
    return _NormalizeFolder(args.folder)

  if args.project is not None:
    return _NormalizeProject(args.project)

  return None


def _InvalidResourceName():
  """Returns an error indicating that a module lacks a valid resource name."""
  return InvalidSCCInputError(
      "Custom module must match the full resource name, or `--organization=`,"
      " `--folder=`, or `--project=` must be provided."
  )


def _InvalidFullResourcePathForPattern(pattern):
  """Returns an error indicating that provided resource path is invalid."""
  return InvalidSCCInputError(
      "When providing a full resource path, it must match the pattern '%s'."
      % pattern.pattern
  )
