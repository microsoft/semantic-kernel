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
"""Core labels_util extended with GCF specific behavior."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.command_lib.util.args import labels_util


class Diff(labels_util.Diff):
  """Computes changes to labels.

  Similar to the core class, but it allows specifying labels that will be
  added if not present or removed either via --remove-labels or
  --clear-labels.
  """

  @classmethod
  def FromUpdateArgs(cls, args, enable_clear=True, required_labels=None):
    """Initializes a Diff based on the arguments in AddUpdateLabelsFlags.

    Args:
      args: The parsed args
      enable_clear: whether --clear-labels flag is enabled
      required_labels: dict of labels that will be added unless they're removed
        explicitly or via clear

    Returns:
      The label updates Diff that needs to be applied to the exisiting labels.
    """
    if enable_clear:
      clear = args.clear_labels
      if clear:
        # don't add labels on clear
        required_labels = {}
    else:
      clear = None
    addition = required_labels if required_labels else {}
    if args.update_labels:
      addition.update(args.update_labels)
    return cls(addition, args.remove_labels, clear)
