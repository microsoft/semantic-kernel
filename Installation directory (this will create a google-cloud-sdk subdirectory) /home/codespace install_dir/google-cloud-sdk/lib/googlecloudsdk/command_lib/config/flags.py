# -*- coding: utf-8 -*- #
# Copyright 2013 Google LLC. All Rights Reserved.
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

"""Flags and helpers for the config related commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
from googlecloudsdk.core import properties


INSTALLATION_FLAG = base.Argument(
    '--installation',
    required=False,
    action='store_true',
    help="""\
        If set, the property is updated for the entire Google Cloud CLI
        installation. Otherwise, by default, the property is updated only in the
        currently active configuration."""
    )


def RequestedScope(args):
  # This hackiness will go away when we rip out args.scope everywhere
  install = 'installation' if getattr(args, 'installation', False) else None
  scope_arg = getattr(args, 'scope', None)

  return properties.Scope.FromId(scope_arg or install)
