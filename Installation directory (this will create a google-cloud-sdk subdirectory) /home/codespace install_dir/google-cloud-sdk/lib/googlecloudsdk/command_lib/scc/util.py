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
"""Shared utility functions for Cloud SCC commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import re

from googlecloudsdk.command_lib.scc import errors
from googlecloudsdk.core import properties


def GetParentFromPositionalArguments(args):
  """Converts user input to one of: organization, project, or folder."""
  id_pattern = re.compile("[0-9]+")
  parent = None
  if hasattr(args, "parent"):
    if not args.parent:
      parent = properties.VALUES.scc.parent.Get()
    else:
      parent = args.parent

  if parent is None:
    # Use organization property as backup for legacy behavior.
    parent = properties.VALUES.scc.organization.Get()

  if parent is None and hasattr(args, "organization"):
    parent = args.organization

  if parent is None:
    raise errors.InvalidSCCInputError(
        "Could not find Parent argument. Please provide the parent argument."
    )

  if id_pattern.match(parent):
    # Prepend organizations/ if only number value is provided.
    parent = "organizations/" + parent

  if not (
      parent.startswith("organizations/")
      or parent.startswith("projects/")
      or parent.startswith("folders/")
  ):
    error_message = (
        "Parent must match either [0-9]+, organizations/[0-9]+, "
        "projects/.* "
        "or folders/.*."
        ""
    )
    raise errors.InvalidSCCInputError(error_message)

  return parent


def GetParentFromNamedArguments(args):
  """Gets and validates parent from named arguments."""
  if args.organization is not None:
    if "/" in args.organization:
      pattern = re.compile("^organizations/[0-9]{1,19}$")
      if not pattern.match(args.organization):
        raise errors.InvalidSCCInputError(
            "When providing a full resource path, it must include the pattern "
            "'^organizations/[0-9]{1,19}$'."
        )
      else:
        return args.organization
    else:
      pattern = re.compile("^[0-9]{1,19}$")
      if not pattern.match(args.organization):
        raise errors.InvalidSCCInputError(
            "Organization does not match the pattern '^[0-9]{1,19}$'."
        )
      else:
        return "organizations/" + args.organization

  if hasattr(args, "folder") and args.folder is not None:
    if "/" in args.folder:
      pattern = re.compile("^folders/.*$")
      if not pattern.match(args.folder):
        raise errors.InvalidSCCInputError(
            "When providing a full resource path, it must include the pattern "
            "'^folders/.*$'."
        )
      else:
        return args.folder
    else:
      return "folders/" + args.folder

  if hasattr(args, "project") and args.project is not None:
    if "/" in args.project:
      pattern = re.compile("^projects/.*$")
      if not pattern.match(args.project):
        raise errors.InvalidSCCInputError(
            "When providing a full resource path, it must include the pattern "
            "'^projects/.*$'."
        )
      else:
        return args.project
    else:
      return "projects/" + args.project


def CleanUpUserMaskInput(mask):
  """Removes spaces from a field mask provided by user."""
  return mask.replace(" ", "")


def IsLocationSpecified(args, resource_name):
  """Returns true if location is specified."""
  location_in_resource_name = "/locations/" in resource_name
  # Validate mutex on location.
  if args.IsKnownAndSpecified("location") and location_in_resource_name:
    raise errors.InvalidSCCInputError(
        "Only provide location in a full resource name "
        "or in a --location flag, not both."
    )

  return args.IsKnownAndSpecified("location") or location_in_resource_name


def GetVersionFromArguments(
    args,
    resource_name="",
    deprecated_args=None,
    version_specific_existing_resource: bool = False,
):
  """Returns the correct version to call based on the user supplied arguments.

  Args:
    args: arguments
    resource_name: (optional) resource name e.g. finding, mute_config
    deprecated_args: (optional) list of deprecated arguments for a command
    version_specific_existing_resource: (optional) command is invoked on a
      resource which is not interoperable between versions.

  Returns:
    Version of securitycenter api to handle command, either "v1" or "v2"
  """
  location_specified = IsLocationSpecified(args, resource_name)

  # Non-interoperable resources such as BigQuery Export and NotificationConfigs
  # may only be accessed through the version in which they were instantiated.
  # This may be determined by the presence of a location.
  if version_specific_existing_resource:
    if location_specified:
      return "v2"
    else:
      return "v1"

  # Args that have been deprecated in v2 may necessitate a v1 call.
  if deprecated_args:
    for argument in deprecated_args:
      if args.IsKnownAndSpecified(argument) and location_specified:
        raise errors.InvalidSCCInputError(
            "Location is not available when deprecated arguments are used"
        )
      if args.IsKnownAndSpecified(argument) and not location_specified:
        return "v1"

  if args.api_version == "v1":
    if location_specified:
      return "v2"
    return "v1"

  return "v2"


def ValidateAndGetLocation(args, version):
  """Validates --location flag input and returns location."""
  if version == "v2":
    if args.location is not None:
      # Validate location if a user wants to use v2 and specifes a location.
      name_pattern = re.compile("^locations/[A-Za-z0-9-]{0,61}$")
      id_pattern = re.compile("^[A-Za-z0-9-]{0,61}$")
      if name_pattern.match(args.location):
        return args.location.split("/")[1]
      if id_pattern.match(args.location):
        return args.location
      raise errors.InvalidSCCInputError(
          "location does not match the pattern"
          " '^locations/[A-Za-z0-9-]{0,61}$'. or [A-Za-z0-9-]{0,61}"
      )
  # Return the default location (global) if version is equal to v1.
  return args.location
