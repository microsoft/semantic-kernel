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

"""Common flag setup and parsing for Cloud API Gateway surface."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.command_lib.iam import completers as iam_completers
from googlecloudsdk.command_lib.util.args import labels_util


def AddDisplayNameArg(parser):
  """Adds the display name arg to the parser."""
  parser.add_argument(
      '--display-name',
      help="""\
      Human readable name which can optionally be supplied.
      """)


def AddManagedServiceFlag(parser):
  """Adds the managed service flag."""
  parser.add_argument(
      '--managed-service',
      help="""\
      The name of a pre-existing Google Managed Service.
      """)


def AddBackendAuthServiceAccountFlag(parser):
  """Adds the backend auth service account flag."""
  parser.add_argument(
      '--backend-auth-service-account',
      help="""\
      Service account which will be used to sign tokens for backends with \
      authentication configured.
      """)


def ProcessLabelsFlag(labels, message):
  """Parses labels into a specific message format."""

  class Object(object):
    pass

  if labels:
    labels_obj = Object()
    labels_obj.labels = labels
    labels = labels_util.ParseCreateArgs(
        labels_obj,
        message)

  return labels


class GatewayIamRolesCompleter(iam_completers.IamRolesCompleter):

  def __init__(self, **kwargs):
    super(GatewayIamRolesCompleter, self).__init__(
        resource_collection='apigateway.projects.locations.gateways',
        resource_dest='gateway',
        **kwargs)
