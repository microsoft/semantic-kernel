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

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import re

from googlecloudsdk.calliope import exceptions


def Args(parser):
  """Adds an arg for the approval request name to the parser."""
  parser.add_argument(
      'name', help='Name of the Access Approval request to invalidate')


def GetName(args):
  """Returns the approval request name from the args or raises an exception."""
  if not re.match('^(projects|folders|organizations)/.+/approvalRequests/.+$',
                  args.name):
    raise exceptions.InvalidArgumentException(
        'name', ('expected format is projects/*/approvalRequests/*, '
                 'folders/*/approvalRequests/*, or '
                 'organizations/*/approvalRequests/*'))
  return args.name
