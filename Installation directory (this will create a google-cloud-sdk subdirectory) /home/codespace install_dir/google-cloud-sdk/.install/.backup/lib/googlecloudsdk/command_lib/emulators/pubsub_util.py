# -*- coding: utf-8 -*- #
# Copyright 2015 Google LLC. All Rights Reserved.
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
"""Utility functions for gcloud pubsub emulator."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os
from googlecloudsdk.command_lib.emulators import util
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import execution_utils
from googlecloudsdk.core import log
from googlecloudsdk.core.util import platforms

PUBSUB = 'pubsub'
PUBSUB_TITLE = 'Google Cloud Pub/Sub emulator'


class InvalidArgumentError(exceptions.Error):

  pass


def GetDataDir():
  return util.GetDataDir(PUBSUB)


def BuildStartArgs(args, current_os):
  """Builds the command for starting the pubsub emulator.

  Args:
    args: (list of str) The arguments for the pubsub emulator, excluding the
      program binary.
    current_os: (platforms.OperatingSystem)

  Returns:
    A list of command arguments.
  """
  pubsub_dir = util.GetEmulatorRoot(PUBSUB)
  if current_os is platforms.OperatingSystem.WINDOWS:
    pubsub_executable = os.path.join(
        pubsub_dir, r'bin\cloud-pubsub-emulator.bat')
    return execution_utils.ArgsForCMDTool(pubsub_executable, *args)

  pubsub_executable = os.path.join(pubsub_dir, 'bin/cloud-pubsub-emulator')
  return execution_utils.ArgsForExecutableTool(pubsub_executable, *args)


def GetEnv(args):
  """Returns an environment variable mapping from an argparse.Namespace."""
  return {'PUBSUB_EMULATOR_HOST': '%s:%s' %
                                  (args.host_port.host, args.host_port.port)}


def Start(args, log_file=None):
  pubsub_args = BuildStartArgs(
      util.BuildArgsList(args), platforms.OperatingSystem.Current())
  log.status.Print('Executing: {0}'.format(' '.join(pubsub_args)))
  return util.Exec(pubsub_args, log_file=log_file)


class PubsubEmulator(util.Emulator):
  """Represents the ability to start and route pubsub emulator."""

  def Start(self, port):
    args = util.AttrDict({'host_port': {'host': '::1', 'port': port}})
    return Start(args, self._GetLogNo())

  @property
  def prefixes(self):
    # Taken Jan 1, 2017 from:
    # https://cloud.google.com/pubsub/docs/reference/rpc/google.pubsub.v1
    # Note that this should probably be updated to just be based off of the
    # prefix, without enumerating all of the types.
    return [
        'google.pubsub.v1.Publisher',
        'google.pubsub.v1.Subscriber',
        'google.pubsub.v1.AcknowledgeRequest',
        'google.pubsub.v1.DeleteSubscriptionRequest',
        'google.pubsub.v1.DeleteTopicRequest',
        'google.pubsub.v1.GetSubscriptionRequest',
        'google.pubsub.v1.GetTopicRequest',
        'google.pubsub.v1.ListSubscriptionsRequest',
        'google.pubsub.v1.ListSubscriptionsResponse',
        'google.pubsub.v1.ListTopicSubscriptionsRequest',
        'google.pubsub.v1.ListTopicSubscriptionsResponse',
        'google.pubsub.v1.ListTopicsRequest',
        'google.pubsub.v1.ListTopicsResponse',
        'google.pubsub.v1.ModifyAckDeadlineRequest',
        'google.pubsub.v1.ModifyPushConfigRequest',
        'google.pubsub.v1.PublishRequest',
        'google.pubsub.v1.PublishResponse',
        'google.pubsub.v1.PubsubMessage',
        'google.pubsub.v1.PullRequest',
        'google.pubsub.v1.PullResponse',
        'google.pubsub.v1.PushConfig',
        'google.pubsub.v1.ReceivedMessage',
        'google.pubsub.v1.Subscription',
        'google.pubsub.v1.Topic',
    ]

  @property
  def service_name(self):
    return PUBSUB

  @property
  def emulator_title(self):
    return PUBSUB_TITLE

  @property
  def emulator_component(self):
    return 'pubsub-emulator'
