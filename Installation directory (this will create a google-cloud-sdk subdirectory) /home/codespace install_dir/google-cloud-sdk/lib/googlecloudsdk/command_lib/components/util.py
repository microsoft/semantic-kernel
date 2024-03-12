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

"""Utilities for components commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import exceptions
from googlecloudsdk.core.updater import update_manager
from googlecloudsdk.core.util import files
from googlecloudsdk.core.util import platforms


def GetUpdateManager(group_args):
  """Construct the UpdateManager to use based on the common args for the group.

  Args:
    group_args: An argparse namespace.

  Returns:
    update_manager.UpdateManager, The UpdateManager to use for the commands.
  """
  try:
    os_override = platforms.OperatingSystem.FromId(
        group_args.operating_system_override)
  except platforms.InvalidEnumValue as e:
    raise exceptions.InvalidArgumentException('operating-system-override', e)
  try:
    arch_override = platforms.Architecture.FromId(
        group_args.architecture_override)
  except platforms.InvalidEnumValue as e:
    raise exceptions.InvalidArgumentException('architecture-override', e)

  platform = platforms.Platform.Current(os_override, arch_override)

  # darwin-arm machines thats are running a darwin_x86_64 python binary will
  # report arch as darwin_x86_64 because Architecture.Current() uses
  # platform.machine() as the source of truth. Here in the UpdateManager we want
  # to know the "real" truth so we call IsActuallyM1ArmArchitecture as the
  # source of truth which breaks out of the python env to see the underlying
  # arch.
  if not os_override and not arch_override:
    if (platform.operating_system == platforms.OperatingSystem.MACOSX and
        platform.architecture == platforms.Architecture.x86_64):
      if platforms.Platform.IsActuallyM1ArmArchitecture():
        platform.architecture = platforms.Architecture.arm

  root = (files.ExpandHomeDir(group_args.sdk_root_override)
          if group_args.sdk_root_override else None)
  url = (files.ExpandHomeDir(group_args.snapshot_url_override)
         if group_args.snapshot_url_override else None)
  compile_python = True
  if hasattr(group_args, 'compile_python'):
    compile_python = group_args.compile_python
  if hasattr(group_args, 'no_compile_python'):
    compile_python = group_args.no_compile_python
  return update_manager.UpdateManager(
      sdk_root=root, url=url, platform_filter=platform,
      skip_compile_python=(not compile_python))
