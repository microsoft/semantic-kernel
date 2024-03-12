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
"""Shared utility functions for Cloud SCC findings commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import re

from apitools.base.py import encoding
from googlecloudsdk.api_lib.scc import securitycenter_client
from googlecloudsdk.command_lib.scc import errors
from googlecloudsdk.command_lib.scc import util as scc_util


def ValidateMutexOnFindingAndSourceAndOrganization(args):
  """Validates that only a full resource name or split arguments are provided."""
  if "/" in args.finding and (
      args.IsKnownAndSpecified("organization")
      or args.IsKnownAndSpecified("source")
  ):
    raise errors.InvalidSCCInputError(
        "Only provide a full resource name "
        "(organizations/123/sources/456/findings/789) or an --organization flag"
        " and --sources flag, not both."
    )


def GetFullFindingName(args, version):
  """Returns relative resource name for a finding name.

  Args:
    args: Argument namespace.
    version: Api version.

  Returns:
    Relative resource name
    if no location is specified the result will be one of the following forms
      `organizations/{organization_id}/sources/{source_id}/finding/{finding_id}`
      `folders/{folders_id}/sources/{source_id}/finding/{finding_id}`
      `projects/{projects_id}/sources/{source_id}/finding/{finding_id}`
    if a location is specified the result will be one of the following forms
      `organizations/{organization_id}/sources/{source_id}/locations/{location_id}/finding/{finding_id}`
      `folders/{folders_id}/sources/{source_id}/locations/{location_id}/finding/{finding_id}`
      `projects/{projects_id}/sources/{source_id}/locations/{location_id}/finding/{finding_id}`
  """
  resource_pattern = re.compile(
      "(organizations|projects|folders)/.*/sources/[0-9-]+/findings/[a-zA-Z0-9]+$"
  )
  region_resource_pattern = re.compile(
      "(organizations|projects|folders)/.*/sources/[0-9-]+/locations/.*/findings/[a-zA-Z0-9]+$"
  )
  id_pattern = re.compile("^[a-zA-Z0-9]+$")
  if region_resource_pattern.match(args.finding):
    # Handle finding id as full resource name.
    return args.finding
  if resource_pattern.match(args.finding):
    if version == "v2":
      return GetRegionalizedResourceName(args, version)
    return args.finding
  if id_pattern.match(args.finding):
    return f"{GetFullSourceName(args, version)}/findings/{args.finding}"

  raise errors.InvalidSCCInputError(
      "Finding must match either the full resource name or only the finding id."
  )


def GetFullSourceName(args, version):
  """Returns relative resource name for a source from --source argument.

  Args:
    args: Argument namespace.
    version: Api version.

  Returns:
    Relative resource name
    if args.source is not provided an exception will be raised
    if no location is specified in argument: sources/{source_id}
    if a location is specified: sources/{source_id}/locations/{location_id}
  """
  resource_pattern = re.compile(
      "(organizations|projects|folders)/.*/sources/[0-9-]+"
  )
  region_resource_pattern = re.compile(
      "(organizations|projects|folders)/.*/sources/[0-9-]+/locations/[a-zA-Z0-9-]+$"
  )
  id_pattern = re.compile("[0-9-]+")

  if not args.source:
    raise errors.InvalidSCCInputError(
        "Finding source must be provided in --source flag or full resource"
        " name."
    )

  if region_resource_pattern.match(args.source):
    return args.source

  location = scc_util.ValidateAndGetLocation(args, version)
  if resource_pattern.match(args.source):
    source = args.source
    if version == "v2":
      return f"{source}/locations/{location}"
    return source

  if id_pattern.match(args.source):
    source = f"{scc_util.GetParentFromPositionalArguments(args)}/sources/{args.source}"
    if version == "v2":
      return f"{source}/locations/{location}"
    return source

  raise errors.InvalidSCCInputError(
      "The source must either be the full resource "
      "name or the numeric source ID."
  )


def GetSourceParentFromFindingName(resource_name, version):
  """Get parent (with source) from Finding name i.e remove 'findings/{finding_name}'.

  Args:
    resource_name: finding name {parent with source}/findings/{findingID}
    version: API version.

  Returns:
    The parent with source or parent with source and location
    examples:
    if no location is specified the result will be one of the following forms
      `organizations/{organization_id}/sources/{source_id}`
      `folders/{folders_id}/sources/{source_id}`
      `projects/{projects_id}/sources/{source_id}`
    if a location is specified the result will be one of the following forms
      `organizations/{organization_id}/sources/{source_id}/locations/{location_id}`
      `folders/{folders_id}/sources/{source_id}/locations/{location_id}`
      `projects/{projects_id}/sources/{source_id}/locations/{location_id}`
  """
  resource_pattern = re.compile(
      "(organizations|projects|folders)/.*/sources/[0-9]+"
  )
  if not resource_pattern.match(resource_name):
    raise errors.InvalidSCCInputError(
        "When providing a full resource path, it must also include "
        "the organization, project, or folder prefix."
    )
  list_source_components = resource_name.split("/")
  if version == "v1":
    return f"{GetParentFromResourceName(resource_name)}/{list_source_components[2]}/{list_source_components[3]}"
  if version == "v2":
    # Include location.
    return f"{GetParentFromResourceName(resource_name)}/{list_source_components[2]}/{list_source_components[3]}/{list_source_components[4]}/{list_source_components[5]}"


def GetFindingIdFromName(finding_name):
  """Gets a finding id from the full resource name."""
  resource_pattern = re.compile(
      "(organizations|projects|folders)/.*/sources/[0-9-]+/findings/[a-zA-Z0-9]+$"
  )
  region_resource_pattern = re.compile(
      "(organizations|projects|folders)/.*/sources/[0-9-]+/locations/.*/findings/[a-zA-Z0-9]+$"
  )
  if not resource_pattern.match(
      finding_name
  ) and not region_resource_pattern.match(finding_name):
    raise errors.InvalidSCCInputError(
        "When providing a full resource path, it must include the pattern "
        "organizations/[0-9]+/sources/[0-9-]+/findings/[a-zA-Z0-9]+."
    )
  list_finding_components = finding_name.split("/")
  return list_finding_components[len(list_finding_components) - 1]


def GetParentFromResourceName(resource_name):
  list_organization_components = resource_name.split("/")
  return f"{list_organization_components[0]}/{list_organization_components[1]}"


def ConvertStateInput(state, version):
  """Convert state input to messages.Finding.StateValueValuesEnum object."""
  messages = securitycenter_client.GetMessages(version)
  if state:
    state = state.upper()

  state_dict = {}
  if version == "v1":
    unspecified_state = messages.Finding.StateValueValuesEnum.STATE_UNSPECIFIED
    state_dict["v1"] = {
        "ACTIVE": messages.Finding.StateValueValuesEnum.ACTIVE,
        "INACTIVE": messages.Finding.StateValueValuesEnum.INACTIVE,
        "STATE_UNSPECIFIED": unspecified_state,
    }
  else:
    v2_unspecified_state = (
        messages.GoogleCloudSecuritycenterV2Finding.StateValueValuesEnum.STATE_UNSPECIFIED
    )
    state_dict["v2"] = {
        "ACTIVE": (
            messages.GoogleCloudSecuritycenterV2Finding.StateValueValuesEnum.ACTIVE
        ),
        "INACTIVE": (
            messages.GoogleCloudSecuritycenterV2Finding.StateValueValuesEnum.INACTIVE
        ),
        "STATE_UNSPECIFIED": v2_unspecified_state,
    }
  return state_dict[version].get(
      state, state_dict[version]["STATE_UNSPECIFIED"]
  )


def ValidateAndGetParent(args):
  """Validates parent."""
  if args.organization is not None:  # Validates organization.
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
        return f"organizations/{args.organization}"

  if args.folder is not None:  # Validates folder.
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
      return f"folders/{args.folder}"

  if args.project is not None:  # Validates project.
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
      return f"projects/{args.project}"


def ValidateMutexOnSourceAndParent(args):
  """Validates that only a full resource name or split arguments are provided."""
  if "/" in args.source and args.parent is not None:
    raise errors.InvalidSCCInputError(
        "Only provide a full resource name "
        "(organizations/123/sources/456) or a --parent flag, not both."
    )


def ExtractSecurityMarksFromResponse(response, args):
  """Returns security marks from finding response."""
  del args
  list_finding_response = list(response)
  if len(list_finding_response) > 1:
    raise errors.InvalidSCCInputError(
        "ListFindingResponse must only return one finding since it is "
        "filtered by Finding Name."
    )
  for finding_result in list_finding_response:
    return finding_result.finding.securityMarks


def ValidateSourceAndFindingIdIfParentProvided(args):
  """Validates that source and finding id are provided if parent is provided."""
  if args.source is None:
    raise errors.InvalidSCCInputError("--source flag must be provided.")
  if "/" in args.finding:
    raise errors.InvalidSCCInputError(
        "Finding id must be provided, instead of the full resource name."
    )


def ValidateLocationAndGetRegionalizedParent(args, parent):
  """Appends location to parent."""
  if args.location:
    if "/" in args.location:
      pattern = re.compile("^locations/[A-Za-z0-9-]{0,61}$")
      if not pattern.match(args.location):
        raise errors.InvalidSCCInputError(
            "When providing a full resource path, it must include the pattern "
            "'^locations/.*$'."
        )
      else:
        return f"{parent}/{args.location}"
    else:
      return f"{parent}/locations/{args.location}"


def GetRegionalizedResourceName(args, version):
  """Returns regionalized resource name."""
  location = scc_util.ValidateAndGetLocation(args, version)
  name_components = args.finding.split("/")
  return f"{name_components[0]}/{name_components[1]}/{name_components[2]}/{name_components[3]}/locations/{location}/{name_components[4]}/{name_components[5]}"


def ConvertSourceProperties(source_properties_dict, version):
  """Hook to capture "key1=val1,key2=val2" as SourceProperties object."""
  messages = securitycenter_client.GetMessages(version)
  if version == "v1":
    return encoding.DictToMessage(
        source_properties_dict, messages.Finding.SourcePropertiesValue
    )
  elif version == "v2":
    return encoding.DictToMessage(
        source_properties_dict,
        messages.GoogleCloudSecuritycenterV2Finding.SourcePropertiesValue,
    )
  raise errors.InvalidAPIVersion("Invalid API version")


def GetApiVersionUsingDeprecatedArgs(args, deprecated_args):
  """Determine what version to call from --location and --api-version."""
  if not args.parent:
    # If the parent argument is not provided in the command, it can be derived
    # from properties set by gcloud config.
    parent = scc_util.GetParentFromPositionalArguments(args)
  else:
    parent = args.parent
  return scc_util.GetVersionFromArguments(args, parent, deprecated_args)
