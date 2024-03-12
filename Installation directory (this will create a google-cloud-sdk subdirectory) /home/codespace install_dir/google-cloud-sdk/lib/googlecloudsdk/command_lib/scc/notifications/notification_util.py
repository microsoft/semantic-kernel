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

"""Shared util methods common to Notification commands."""
import re
from googlecloudsdk.command_lib.scc import errors
from googlecloudsdk.command_lib.scc import util


def GetParentFromNotificationConfigName(notification_config_name):
  resource_pattern = re.compile("(organizations|projects|folders)/.*")
  if not resource_pattern.match(notification_config_name):
    raise errors.InvalidSCCInputError(
        "When providing a full resource path, it must also include the pattern "
        "the organization, project, or folder prefix."
    )
  return notification_config_name.split("/notificationConfigs/")[0]


def GetParentFromResourceName(resource_name):
  list_organization_components = resource_name.split("/")
  return list_organization_components[0] + "/" + list_organization_components[1]


def ValidateAndGetNotificationConfigV1Name(args):
  """Returns relative resource name for a v1 notification config.

  Validates on regexes for args containing full names or short names with
  resources. Localization is supported by the
  ValidateAndGetNotificationConfigV2Name method.

  Args:
    args: an argparse object that should contain .NOTIFICATIONCONFIGID,
      optionally 1 of .organization, .folder, .project

  Examples:

  args with NOTIFICATIONCONFIGID="organizations/123/notificationConfigs/config1"
  returns the NOTIFICATIONCONFIGID

  args with NOTIFICATIONCONFIGID="config1" and projects="projects/123" returns
  projects/123/notificationConfigs/config1
  """
  resource_pattern = re.compile(
      "(organizations|projects|folders)/.+/notificationConfigs/[a-zA-Z0-9-_]{1,128}$"
  )
  id_pattern = re.compile("[a-zA-Z0-9-_]{1,128}$")
  notification_config_id = args.NOTIFICATIONCONFIGID
  if not resource_pattern.match(
      notification_config_id
  ) and not id_pattern.match(notification_config_id):
    raise errors.InvalidNotificationConfigError(
        "NotificationConfig must match either (organizations|projects|folders)/"
        ".+/notificationConfigs/[a-zA-Z0-9-_]{1,128})$ or "
        "[a-zA-Z0-9-_]{1,128}$."
    )

  if resource_pattern.match(notification_config_id):
    # Handle config id as full resource name
    return notification_config_id

  return (
      util.GetParentFromNamedArguments(args)
      + "/notificationConfigs/"
      + notification_config_id
  )


def ValidateAndGetLocationFromV2Arg(args):
  """Returns the location from the location arg, or throws an error."""
  if args.IsKnownAndSpecified("location"):
    # arg format: locations/<location>
    if "/" in args.location:
      long_pattern = re.compile("^locations/.*$")
      if long_pattern.match(args.location):
        return args.location.split("/")[-1]
      else:
        raise errors.InvalidSCCInputError(
            "When providing a full resource path, it must include the pattern "
            "'^locations/.*$'."
        )
    # arg format: <location>
    else:
      return args.location
  else:
    return "global"


def ValidateAndGetNotificationConfigV2Name(args):
  """Returns relative resource name for a v2 notification config.

  Validates on regexes for args containing full names with locations or short
  names with resources.

  Args:
    args: an argparse object that should contain .NOTIFICATIONCONFIGID,
      optionally 1 of .organization, .folder, .project; and optionally .location

  Examples:

  args with NOTIFICATIONCONFIGID="organizations/123/notificationConfigs/config1"
  and location="locations/us" returns
  organizations/123/locations/us/notificationConfigs/config1

  args with
  NOTIFICATIONCONFIGID="folders/123/locations/us/notificationConfigs/config1"
  and returns folders/123/locations/us/notificationConfigs/config1

  args with NOTIFICATIONCONFIGID="config1", projects="projects/123", and
  locations="us" returns projects/123/notificationConfigs/config1
  """
  id_pattern = re.compile("[a-zA-Z0-9-_]{1,128}$")
  nonregionalized_resource_pattern = re.compile(
      "(organizations|projects|folders)/.+/notificationConfigs/[a-zA-Z0-9-_]{1,128}$"
  )
  regionalized_resource_pattern = re.compile(
      "(organizations|projects|folders)/.+/locations/.+/notificationConfigs/[a-zA-Z0-9-_]{1,128}$"
  )
  notification_config_id = args.NOTIFICATIONCONFIGID
  location = util.ValidateAndGetLocation(args, "v2")

  # id-only pattern (short name): compose the full name
  if id_pattern.match(notification_config_id):
    return f"{util.GetParentFromNamedArguments(args)}/locations/{location}/notificationConfigs/{notification_config_id}"

  # v2=style regionalized patterns
  if regionalized_resource_pattern.match(notification_config_id):
    return notification_config_id

  # v1-style nonregionalized patterns are acceptable
  if nonregionalized_resource_pattern.match(notification_config_id):
    # Handle config id as full resource name
    [parent_segment, id_segment] = notification_config_id.split(
        "/notificationConfigs/"
    )
    return f"{parent_segment}/locations/{location}/notificationConfigs/{id_segment}"

  raise errors.InvalidNotificationConfigError(
      "NotificationConfig must match"
      " (organizations|projects|folders)/.+/notificationConfigs/[a-zA-Z0-9-_]{1,128})$,"
      " (organizations|projects|folders)/.+/locations/.+/notificationConfigs/[a-zA-Z0-9-_]{1,128})$,"
      " or [a-zA-Z0-9-_]{1,128}$."
  )


def ValidateMutexOnConfigIdAndParent(args, parent):
  """Validates that only a full resource or resouce args are provided."""
  notification_config_id = args.NOTIFICATIONCONFIGID
  if "/" in notification_config_id:
    if parent is not None:
      raise errors.InvalidNotificationConfigError(
          "Only provide a full resource name "
          "(organizations/123/notificationConfigs/test-config) "
          "or an --(organization|folder|project) flag, not both."
      )
  elif parent is None:
    raise errors.InvalidNotificationConfigError(
        "A corresponding parent by a --(organization|folder|project) flag must "
        "be provided if it is not included in notification ID."
    )
