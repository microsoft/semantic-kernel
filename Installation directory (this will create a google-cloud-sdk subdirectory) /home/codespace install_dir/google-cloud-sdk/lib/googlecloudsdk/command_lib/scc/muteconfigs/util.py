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
"""Shared utility functions for Cloud SCC muteconfigs commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import re

from googlecloudsdk.command_lib.scc import errors
from googlecloudsdk.command_lib.scc import util as scc_util


def ValidateAndGetParent(args):
  """Validates parent."""
  if args.organization is not None:
    name_pattern = re.compile("^organizations/[0-9]{1,19}$")
    id_pattern = re.compile("^[0-9]{1,19}$")

    if name_pattern.match(args.organization):
      return args.organization
    if id_pattern.match(args.organization):
      return f"organizations/{args.organization}"

    if "/" in args.organization:
      raise errors.InvalidSCCInputError(
          "When providing a full resource path, it must include the pattern "
          "'^organizations/[0-9]{1,19}$'."
      )

    raise errors.InvalidSCCInputError(
        "Organization does not match the pattern '^[0-9]{1,19}$'."
    )

  if args.folder is not None:
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

  if args.project is not None:
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


def ValidateAndGetMuteConfigId(args):
  """Validate muteConfigId."""
  mute_config_id = args.mute_config
  pattern = re.compile("^[a-z]([a-z0-9-]{0,61}[a-z0-9])?$")
  if not pattern.match(mute_config_id):
    raise errors.InvalidSCCInputError(
        "Mute config id does not match the pattern"
        " '^[a-z]([a-z0-9-]{0,61}[a-z0-9])?$'."
    )
  else:
    return mute_config_id


def ValidateAndGetMuteConfigFullResourceName(args, version):
  """Validates muteConfig full resource name."""
  mute_config = args.mute_config
  resource_pattern = re.compile(
      "(organizations|projects|folders)/.*/muteConfigs/[a-z]([a-z0-9-]{0,61}[a-z0-9])?$"
  )
  regionalized_resource_pattern = re.compile(
      "(organizations|projects|folders)/.*/locations/.*/muteConfigs/[a-z]([a-z0-9-]{0,61}[a-z0-9])?$"
  )

  if regionalized_resource_pattern.match(mute_config):
    return mute_config

  # Add location to parent if user didn't specify location in the mute_config
  # but wants to use v2.
  if resource_pattern.match(mute_config):
    if version == "v2":
      mute_config_components = mute_config.split("/")
      return f"{mute_config_components[0]}/{mute_config_components[1]}/locations/{args.location}/{mute_config_components[2]}/{mute_config_components[3]}"
    else:
      return mute_config

  # TODO: b/282774006 - Update message to include information about location.
  raise errors.InvalidSCCInputError(
      "Mute config must match the full resource name, or `--organization=`,"
      " `--folder=` or `--project=` must be provided."
  )


def GetMuteConfigIdFromFullResourceName(mute_config):
  """Gets muteConfig id from the full resource name."""
  mute_config_components = mute_config.split("/")
  return mute_config_components[len(mute_config_components) - 1]


def GetParentFromFullResourceName(mute_config, version):
  """Gets parent from the full resource name."""
  mute_config_components = mute_config.split("/")
  if version == "v1":
    # Return parent as "organizations/{organizationsID}"
    # or "folders/{foldersID}"
    # or "projects/{projectsID}"
    return f"{mute_config_components[0]}/{mute_config_components[1]}"
  if version == "v2":
    # Return parent as "organizations/{organizationsID}/locations/{locationsID}"
    # or "folders/{foldersID}/locations/{locationsID}"
    # or "projects/{projectsID}/locations/{locationsID}"
    return f"{mute_config_components[0]}/{mute_config_components[1]}/{mute_config_components[2]}/{mute_config_components[3]}"


def GenerateMuteConfigName(args, req, version):
  """Generates the name of the mute config."""
  parent = ValidateAndGetParent(args)
  if parent is not None:
    if version == "v2":
      parent = ValidateAndGetRegionalizedParent(args, parent)
    mute_config_id = ValidateAndGetMuteConfigId(args)
    req.name = f"{parent}/muteConfigs/{mute_config_id}"
  else:
    args.location = scc_util.ValidateAndGetLocation(args, version)
    mute_config = ValidateAndGetMuteConfigFullResourceName(args, version)
    req.name = mute_config
  return req


def ValidateAndGetRegionalizedParent(args, parent):
  """Appends location to parent."""
  if args.location is not None:
    if "/" in args.location:
      pattern = re.compile("^locations/.*$")
      if not pattern.match(args.location):
        raise errors.InvalidSCCInputError(
            "When providing a full resource path, it must include the pattern "
            "'^locations/.*$'."
        )
      else:
        return f"{parent}/{args.location}"
    else:
      return f"{parent}/locations/{args.location}"
