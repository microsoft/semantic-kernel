# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""'functions deploy' utilities for labels."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.functions.v1 import util as api_util
from googlecloudsdk.calliope import exceptions as calliope_exceptions
from googlecloudsdk.command_lib.util.args import labels_util as args_labels_util


NO_LABELS_STARTING_WITH_DEPLOY_MESSAGE = (
    'Label keys starting with `deployment` are reserved for use by deployment '
    'tools and cannot be specified manually.'
)


def CheckNoDeploymentLabels(flag_name, label_names):
  """Check for labels that start with `deployment`, which is not allowed.

  Args:
    flag_name: The name of the flag to include in case of an exception
    label_names: A list of label names to check

  Raises:
    calliope_exceptions.InvalidArgumentException
  """
  if not label_names:
    return
  for label_name in label_names:
    if label_name.startswith('deployment'):
      raise calliope_exceptions.InvalidArgumentException(
          flag_name, NO_LABELS_STARTING_WITH_DEPLOY_MESSAGE
      )


def SetFunctionLabels(function, update_labels, remove_labels, clear_labels):
  """Set the labels on a function based on args.

  Args:
    function: the function to set the labels on
    update_labels: a dict of <label-name>-<label-value> pairs for the labels to
      be updated, from --update-labels
    remove_labels: a list of the labels to be removed, from --remove-labels
    clear_labels: a bool representing whether or not to clear all labels, from
      --clear-labels

  Returns:
    A bool indicating whether or not any labels were updated on the function.
  """
  labels_to_update = update_labels or {}
  labels_to_update['deployment-tool'] = 'cli-gcloud'
  labels_diff = args_labels_util.Diff(
      additions=labels_to_update, subtractions=remove_labels, clear=clear_labels
  )
  messages = api_util.GetApiMessagesModule()
  labels_update = labels_diff.Apply(
      messages.CloudFunction.LabelsValue, function.labels
  )
  if labels_update.needs_update:
    function.labels = labels_update.labels
    return True
  return False
