# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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

"""Utilities for using containers in conjunction with ssh."""


from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals


def GetRemoteCommand(container, command):
  """Assemble the remote command list given user-supplied args.

  If a container argument is supplied, run
  `sudo docker exec -i[t] CONTAINER_ID COMMAND [ARGS...]` on the remote.

  Args:
    container: str or None, name of container to enter during connection.
    command: [str] or None, the remote command to execute. If no command is
      given, allocate a TTY.

  Returns:
    [str] or None, Remote command to run or None if no command.
  """
  if container:
    # The `/bin/sh` is for listening to commands.
    args = command or ['/bin/sh']
    flags = '-i' if command else '-it'
    return ['sudo', 'docker', 'exec', flags, container] + args
  if command:
    return command
  return None


def GetTty(container, command):
  """Determine the ssh command should be run in a TTY or not.

  Args:
    container: str or None, name of container to enter during connection.
    command: [str] or None, the remote command to execute. If no command is
      given, allocate a TTY.

  Returns:
    Bool or None, whether to enforce TTY or not, or None if "auto".
  """
  return True if container and not command else None

