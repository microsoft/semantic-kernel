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

"""Wrapper around Snapshot to provide file-order determinism."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os

from googlecloudsdk.api_lib.storage import storage_util


class DeterministicSnapshot(storage_util.Snapshot):
  """DeterministicSnapshot is a thin wrapper around Snapshot."""

  def GetSortedFiles(self):
    """Gets the values of `self.files` in a deterministic order.

    Internally, `self.files` is a dictionary. Prior to Python 3.6, dictionaries
    were ordered nondeterministically, but our tests require determinism. As
    such, we have to convert the underlying dictionary to a list and sort that
    list. The specific order itself (e.g. alphabetical vs. reverse-alphabetical)
    doesn't matter.

    Returns:
      A list of files in a deterministic order.
    """
    return sorted(
        self.files.values(), key=lambda m: os.path.join(m.root, m.path)
    )
