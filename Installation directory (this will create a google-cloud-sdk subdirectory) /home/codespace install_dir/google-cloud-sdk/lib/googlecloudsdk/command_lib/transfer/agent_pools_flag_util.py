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
"""Utils for managng common agent pool flags.

Tested more through command surface tests.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import sys

from googlecloudsdk.calliope import arg_parsers


def setup_parser(parser):
  """Adds flags to agent-pools create and agent-pools update commands."""
  parser.add_argument(
      'name', help='A unique, permanent identifier for this pool.')
  parser.add_argument(
      '--display-name',
      help='A modifiable name to help you identify this pool. You can include'
      " details that might not fit in the pool's unique full resource name.")
  parser.add_argument(
      '--bandwidth-limit',
      type=arg_parsers.BoundedInt(1, sys.maxsize, unlimited=True),
      help="Set how much of your bandwidth to make available to this pool's"
      ' agents. A bandwidth limit applies to all agents in a pool and can'
      " help prevent the pool's transfer workload from disrupting other"
      " operations that share your bandwidth. For example, enter '50' to set"
      ' a bandwidth limit of 50 MB/s. By leaving this flag unspecified, this'
      " flag unspecified, this pool's agents will use all bandwidth available"
      ' to them.')
