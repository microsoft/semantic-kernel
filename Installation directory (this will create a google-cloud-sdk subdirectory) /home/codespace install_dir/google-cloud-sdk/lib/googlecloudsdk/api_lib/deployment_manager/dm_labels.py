# -*- coding: utf-8 -*- #
# Copyright 2016 Google LLC. All Rights Reserved.
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
"""Utility for DM labels."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import six


def UpdateLabels(labels, labels_proto, update_labels=None, remove_labels=None):
  """Returns a list of label protos based on the current state plus edits.

  Args:
    labels: The current label values.
    labels_proto: The LabelEntry proto message class.
    update_labels: A dict of label key=value edits.
    remove_labels: A list of labels keys to remove.

  Returns:
    A list of label protos representing the update and remove edits.
  """
  if not update_labels and not remove_labels:
    return labels

  new_labels = {}

  # Add pre-existing labels.
  if labels:
    for label in labels:
      new_labels[label.key] = label.value

  # Add label updates and/or addtions.
  if update_labels:
    new_labels.update(update_labels)

  # Remove labels if requested.
  if remove_labels:
    for key in remove_labels:
      new_labels.pop(key, None)

  # Return the label protos with all edits applied, sorted for reproducability
  return [
      labels_proto(key=key, value=value)
      for key, value in sorted(six.iteritems(new_labels))
  ]
