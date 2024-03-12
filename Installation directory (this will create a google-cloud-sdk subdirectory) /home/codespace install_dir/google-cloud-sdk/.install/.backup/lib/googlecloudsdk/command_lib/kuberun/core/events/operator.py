# -*- coding: utf-8 -*- #
# Copyright 2021 Google LLC. All Rights Reserved.
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
"""Provides functions for installing Eventing with the CloudRun operator."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from googlecloudsdk.api_lib.kuberun.core import events_constants

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.events import exceptions
from googlecloudsdk.command_lib.events import stages
from googlecloudsdk.command_lib.events import util
from googlecloudsdk.command_lib.kuberun.core.events import init_shared
from googlecloudsdk.core import log
from googlecloudsdk.core.console import progress_tracker


def install_eventing_via_operator(client, track):
  """Install eventing cluster by enabling it via the KubeRun operator.

  Attempt to determine whether KubeRun or CloudRun operator is installed by
    presence of the corresponding operator resource or namespace.

  Args:
    client: An api_tools client.
    track: base.ReleaseTrack, the release (ga, beta, alpha) the command is in.
  """
  namespaces_list = client.ListNamespaces()

  # If not found, then None.
  operator_obj = client.GetKubeRun()

  if operator_obj is not None and track == base.ReleaseTrack.ALPHA:
    # KubeRun operator resource is cluster-scoped so must directly fetch.
    operator_type = events_constants.Operator.KUBERUN
  elif 'cloud-run-system' in namespaces_list:
    # CloudRun operator installed inferred by presence of CR operator namespace.
    operator_obj = client.GetCloudRun()
    operator_type = events_constants.Operator.CLOUDRUN
  else:
    # Neither operator installed.
    operator_type = None
    init_shared.prompt_if_can_prompt(
        'Unable to find the CloudRun resource to install Eventing. '
        'Eventing will not be installed. '
        'Would you like to continue anyway?')
    if ('cloud-run-events' in namespaces_list or
        'events-system' in namespaces_list):
      # Neither operator installed, but knative eventing found.
      log.status.Print('Eventing already installed.')
    else:
      # Neither operator installed, nor is OSS knative eventing installed.
      raise exceptions.EventingInstallError('Eventing not installed.')

  if operator_obj is None:
    return

  tracker_stages = stages.EventingStages()

  operator_max_wait_secs = util.OPERATOR_MAX_WAIT_MS / 1000

  # Enable eventing or wait for operator to finish installing eventing.
  with progress_tracker.StagedProgressTracker(
      'Waiting on eventing installation...'
      if operator_obj.eventing_enabled else 'Enabling eventing...',
      tracker_stages,
      failure_message='Eventing failed to install within {} seconds, '
      'please try rerunning the command.'.format(
          operator_max_wait_secs)) as tracker:

    if not operator_obj.eventing_enabled:
      _update_operator_with_eventing_enabled(client, operator_type)

    # Wait for Operator to enable eventing
    _poll_operator_resource(client, operator_type, tracker)

    if operator_obj.eventing_enabled:
      log.status.Print('Eventing already enabled.')
    else:
      log.status.Print('Enabled eventing successfully.')


def _update_operator_with_eventing_enabled(client, operator_type):
  if operator_type == events_constants.Operator.KUBERUN:
    client.UpdateKubeRunWithEventingEnabled()
  else:
    client.UpdateCloudRunWithEventingEnabled()


def _poll_operator_resource(client, operator_type, tracker):
  if operator_type == events_constants.Operator.KUBERUN:
    client.PollKubeRunResource(tracker)
  else:
    client.PollCloudRunResource(tracker)
