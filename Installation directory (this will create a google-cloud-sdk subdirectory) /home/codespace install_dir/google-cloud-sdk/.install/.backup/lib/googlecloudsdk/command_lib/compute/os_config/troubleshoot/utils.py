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
"""Extra utility functions for OS Config Troubleshooter."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import logging
import traceback

from googlecloudsdk.calliope import base
from googlecloudsdk.core import log
from googlecloudsdk.core import properties


def GetCommandString(args, release_track):
  """Gets the command string for the user to invoke.

  Args:
    args: the command args. These should be arguments put after 'gcloud'.
    release_track: The release track.

  Returns:
    The command string, formatted as '$ gcloud [args]'.
  """
  if release_track != base.ReleaseTrack.GA:
    args.insert(0, release_track.prefix)
  return ' '.join(['$', 'gcloud'] + args)


def UnknownMessage(exception):
  debug_verbosity = log.GetVerbosity() == logging.DEBUG
  message = (
      'Unknown\n'
      'The troubleshooter encountered ' + type(exception).__name__ + ' while '
      'checking your instance.'
  )
  if debug_verbosity:
    message += '\n{}\n'.format(traceback.format_exc(limit=0))
  return message


def GetProject(client, project):
  return client.MakeRequests(
      [(client.apitools_client.projects, 'Get',
        client.messages.ComputeProjectsGetRequest(
            project=project or
            properties.VALUES.core.project.Get(required=True),))])[0]


def GetInstance(client, instance_ref):
  request = client.messages.ComputeInstancesGetRequest(
      **instance_ref.AsDict())
  return client.MakeRequests([
      (client.apitools_client.instances, 'Get', request)])[0]


class Response:
  """Represents a response returned by each of the prerequisite checks."""

  def __init__(self, continue_flag, response_message):
    self.continue_flag = continue_flag
    self.response_message = response_message
