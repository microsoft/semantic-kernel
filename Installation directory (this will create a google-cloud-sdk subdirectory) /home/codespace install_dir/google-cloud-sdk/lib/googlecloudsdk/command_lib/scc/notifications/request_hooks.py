# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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
"""Declarative Request Hooks for Cloud SCC's Notification Configs."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import re

from googlecloudsdk.command_lib.scc import util
from googlecloudsdk.core import exceptions as core_exceptions


class InvalidNotificationConfigError(core_exceptions.Error):
  """Exception raised for errors in the input."""


def UpdateNotificationReqHook(ref, args, req):
  """Generate a notification config using organization and config id."""
  del ref

  parent = util.GetParentFromNamedArguments(args)
  _ValidateMutexOnConfigIdAndParent(args, parent)
  req.name = _GetNotificationConfigName(args)

  # SCC's custom --filter is passing the streaming config filter as part of
  # the request body. However --filter is a global filter flag in gcloud. The
  # --filter flag in gcloud (outside of this command) is used as client side
  # filtering. This has led to a collision in logic as gcloud believes the
  # update is trying to perform client side filtering. Since changing the
  # argument flag would be considered a breaking change, setting args.filter to
  # None in the request hook will skip over the client side filter logic.
  args.filter = None

  return req


def _GetNotificationConfigName(args):
  """Returns relative resource name for a notification config."""
  resource_pattern = re.compile(
      "(organizations|projects|folders)/.+/notificationConfigs/[a-zA-Z0-9-_]{1,128}$"
  )
  id_pattern = re.compile("[a-zA-Z0-9-_]{1,128}$")

  if not resource_pattern.match(
      args.notificationConfigId) and not id_pattern.match(
          args.notificationConfigId):
    raise InvalidNotificationConfigError(
        "NotificationConfig must match either (organizations|projects|folders)/"
        ".+/notificationConfigs/[a-zA-Z0-9-_]{1,128})$ or "
        "[a-zA-Z0-9-_]{1,128}$.")

  if resource_pattern.match(args.notificationConfigId):
    # Handle config id as full resource name
    return args.notificationConfigId

  return util.GetParentFromNamedArguments(
      args) + "/notificationConfigs/" + args.notificationConfigId


def _GetNotificationConfigId(resource_name):
  params_as_list = resource_name.split("/")
  return params_as_list[3]


def _ValidateMutexOnConfigIdAndParent(args, parent):
  """Validates that only a full resource name or split arguments are provided.
  """
  if "/" in args.notificationConfigId:
    if parent is not None:
      raise InvalidNotificationConfigError(
          "Only provide a full resource name "
          "(organizations/123/notificationConfigs/test-config) "
          "or an --(organization|folder|project) flag, not both.")
  elif parent is None:
    raise InvalidNotificationConfigError(
        "A corresponding parent by a --(organization|folder|project) flag must "
        "be provided if it is not included in notification ID.")
