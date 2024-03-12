# -*- coding: utf-8 -*- #
# Copyright 2022 Google LLC. All Rights Reserved.
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
"""Declarative Request Hooks for Security Health Analytics custom modules."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import re

from googlecloudsdk.command_lib.scc.errors import InvalidSCCInputError
from googlecloudsdk.command_lib.scc.hooks import CleanUpUserInput

_PARENT_SUFFIX = "/securityHealthAnalyticsSettings"
_SHA_CUSTOM_MODULE_ID_PATTERN = re.compile("([0-9]{1,20})$")
_ORGANIZATION_ID_PATTERN = re.compile("^[0-9]{1,19}$")
_ORGANIZATION_NAME_PATTERN = re.compile("^organizations/[0-9]{1,19}$")


def CreateSecurityHealthAnalyticsCustomModuleReqHook(ref, args, req):
  """Creates a Security Health Analytics custom module."""
  del ref
  req.parent = _ValidateAndGetParent(args)
  if args.enablement_state not in ["enabled", "disabled"]:
    raise InvalidSCCInputError(
        "Invalid custom module enablement state: %s. Enablement state must be"
        " enabled or disabled." % args.enablement_state)
  return req


def DeleteSecurityHealthAnalyticsCustomModuleReqHook(ref, args, req):
  """Deletes a Security Health Analytics custom module."""
  del ref
  parent = _ValidateAndGetParent(args)
  if parent is not None:
    custom_module_id = _ValidateAndGetCustomModuleId(args)
    req.name = parent + "/customModules/" + custom_module_id
  else:
    custom_module = _ValidateAndGetCustomModuleFullResourceName(args)
    req.name = custom_module
  return req


def GetSecurityHealthAnalyticsCustomModuleReqHook(ref, args, req):
  """Gets a Security Health Analytics custom module."""
  del ref
  parent = _ValidateAndGetParent(args)
  if parent is not None:
    custom_module_id = _ValidateAndGetCustomModuleId(args)
    req.name = parent + "/customModules/" + custom_module_id
  else:
    custom_module = _ValidateAndGetCustomModuleFullResourceName(args)
    req.name = custom_module
  return req


def GetEffectiveSecurityHealthAnalyticsCustomModuleReqHook(ref, args, req):
  """Gets an effective Security Health Analytics custom module."""
  del ref
  parent = _ValidateAndGetParent(args)
  if parent is not None:
    custom_module_id = _ValidateAndGetCustomModuleId(args)
    req.name = parent + "/effectiveCustomModules/" + custom_module_id
  else:
    custom_module = _ValidateAndGetEffectiveCustomModuleFullResourceName(args)
    req.name = custom_module
  return req


def ListSecurityHealthAnalyticsCustomModulesReqHook(ref, args, req):
  """Lists Security Health Analytics custom modules."""
  del ref
  req.parent = _ValidateAndGetParent(args)
  return req


def ListDescendantSecurityHealthAnalyticsCustomModulesReqHook(ref, args, req):
  """Lists descendant Security Health Analytics custom modules."""
  del ref
  req.parent = _ValidateAndGetParent(args)
  return req


def ListEffectiveSecurityHealthAnalyticsCustomModulesReqHook(ref, args, req):
  """Lists effective Security Health Analytics custom modules."""
  del ref
  req.parent = _ValidateAndGetParent(args)
  return req


def TestSecurityHealthAnalyticsCustomModulesReqHook(ref, args, req):
  """Test a Security Health Analytics custom module."""
  del ref
  parent = _ValidateAndGetParent(args)
  custom_module_name = ""
  test_req = req.testSecurityHealthAnalyticsCustomModuleRequest
  if parent is not None:
    custom_module_id = _ValidateAndGetCustomModuleId(args)
    custom_module_name = parent + "/customModules/" + custom_module_id
  else:
    custom_module_name = _ValidateAndGetCustomModuleFullResourceName(args)
  req.name = custom_module_name
  if  test_req.securityHealthAnalyticsCustomModule is not None:
    test_req.securityHealthAnalyticsCustomModule.name = custom_module_name
  return req


def SimulateSecurityHealthAnalyticsCustomModulesReqHook(ref, args, req):
  """Simulates a Security Health Analytics custom module."""
  del ref
  req.parent = _ValidateAndGetParent(args)
  return req


def UpdateSecurityHealthAnalyticsCustomModuleReqHook(ref, args, req):
  """Updates a Security Health Analytics custom module."""
  del ref
  parent = _ValidateAndGetParent(args)
  if parent is not None:
    custom_module_id = _ValidateAndGetCustomModuleId(args)
    req.name = parent + "/customModules/" + custom_module_id
  else:
    custom_module = _ValidateAndGetCustomModuleFullResourceName(args)
    req.name = custom_module
  req.updateMask = CleanUpUserInput(req.updateMask)
  if args.enablement_state not in ["enabled", "disabled", "inherited"]:
    raise InvalidSCCInputError(
        "Invalid custom module enablement state: %s. Enablement state must be"
        " enabled, disabled or inherited." % args.enablement_state)
  return req


def _ValidateAndGetCustomModuleId(args):
  """Validates customModuleId."""
  custom_module_id = args.custom_module

  if not _SHA_CUSTOM_MODULE_ID_PATTERN.match(custom_module_id):
    raise InvalidSCCInputError(
        "Custom module id does not match the pattern '%s'." %
        _SHA_CUSTOM_MODULE_ID_PATTERN.pattern)
  else:
    return custom_module_id


def _ValidateAndGetCustomModuleFullResourceName(args):
  """Validates custom module full resource name."""
  custom_module = args.custom_module
  resource_pattern = re.compile(
      "(organizations|projects|folders)/.*/securityHealthAnalyticsSettings/"
      "customModules/%s"%_SHA_CUSTOM_MODULE_ID_PATTERN.pattern)
  if not resource_pattern.match(custom_module):
    raise InvalidSCCInputError(
        "Custom module must match the full resource name, or `--organization=`,"
        " `--folder=` or `--project=` must be provided.")
  return custom_module


def _ValidateAndGetEffectiveCustomModuleFullResourceName(args):
  """Validates effective custom module full resource name."""
  custom_module = args.custom_module
  resource_pattern = re.compile(
      "(organizations|projects|folders)/.*/securityHealthAnalyticsSettings/effectiveCustomModules/%s"
      % _SHA_CUSTOM_MODULE_ID_PATTERN.pattern
  )
  if not resource_pattern.match(custom_module):
    raise InvalidSCCInputError(
        "Custom module must match the full resource name, or `--organization=`, `--folder=` or `--project=` must be provided."
    )
  return custom_module


def _ValidateAndGetParent(args):
  """Validates parent."""
  if args.organization is not None:
    if "/" in args.organization:
      if not _ORGANIZATION_NAME_PATTERN.match(args.organization):
        raise InvalidSCCInputError(
            "When providing a full resource path, it must include the pattern "
            "'%s'." % _ORGANIZATION_NAME_PATTERN.pattern)
      else:
        return args.organization + _PARENT_SUFFIX
    else:
      if not _ORGANIZATION_ID_PATTERN.match(args.organization):
        raise InvalidSCCInputError(
            "Organization does not match the pattern '%s'." %
            _ORGANIZATION_ID_PATTERN.pattern)
      else:
        return "organizations/" + args.organization + _PARENT_SUFFIX

  if args.folder is not None:
    if "/" in args.folder:
      pattern = re.compile("^folders/.*$")
      if not pattern.match(args.folder):
        raise InvalidSCCInputError(
            "When providing a full resource path, it must include the pattern "
            "'^folders/.*$'.")
      else:
        return args.folder + _PARENT_SUFFIX
    else:
      return "folders/" + args.folder + _PARENT_SUFFIX

  if args.project is not None:
    if "/" in args.project:
      pattern = re.compile("^projects/.*$")
      if not pattern.match(args.project):
        raise InvalidSCCInputError(
            "When providing a full resource path, it must include the pattern "
            "'^projects/.*$'.")
      else:
        return args.project + _PARENT_SUFFIX
    else:
      return "projects/" + args.project + _PARENT_SUFFIX
