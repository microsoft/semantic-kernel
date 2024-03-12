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
"""Helpers for running commands external to gcloud."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import subprocess
from googlecloudsdk.command_lib.compute import ssh_utils
from googlecloudsdk.command_lib.util.ssh import containers
from googlecloudsdk.command_lib.util.ssh import ssh
from googlecloudsdk.core import log
import six


def RunSubprocess(proc_name, command_list):
  """Runs a subprocess and prints out the output.

  Args:
    proc_name: The name of the subprocess to call.
      Used for error logging.
    command_list: A list with all the arguments for a subprocess call.
      Must be able to be passed to a subprocess.Popen call.
  """

  try:
    proc = subprocess.Popen(
        command_list, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    for l in iter(proc.stdout.readline, ''):
      log.out.write(l)
      log.out.flush()
    proc.wait()
    if proc.returncode != 0:
      # Recycling exception type
      raise OSError(proc.stderr.read().strip())
  except OSError as e:
    log.err.Print('Error running %s: %s' % (proc_name, six.text_type(e)))
    command_list_str = ' '.join(command_list)
    log.err.Print('INVOCATION: %s' % command_list_str)


def RunSSHCommandToInstance(command_list,
                            instance,
                            user,
                            args,
                            ssh_helper,
                            explicit_output_file=None,
                            explicit_error_file=None,
                            dry_run=False):
  """Runs a SSH command to a Google Compute Engine VM.

  Args:
    command_list: List with the ssh command to run.
    instance: The GCE VM object.
    user: The user to be used for the SSH command.
    args: The args used to call the gcloud instance.
    ssh_helper: ssh_utils.BaseSSHCLIHelper instance initialized
      for the command.
    explicit_output_file: Use this file for piping stdout of the SSH command,
                          instead of using stdout. This is useful for
                          capturing the command and analyzing it.
    explicit_error_file: Use this file for piping stdout of the SSH command,
                         instead of using stdout. This is useful for
                         capturing the command and analyzing it.
    dry_run: Whether or not this is a dry-run (only print, not run).
  Returns:
    The exit code of the SSH command
  Raises:
    ssh.CommandError: there was an error running a SSH command
  """
  external_address = ssh_utils.GetExternalIPAddress(instance)
  internal_address = ssh_utils.GetInternalIPAddress(instance)
  remote = ssh.Remote(external_address, user)

  identity_file = None
  options = None
  if not args.plain:
    identity_file = ssh_helper.keys.key_file
    options = ssh_helper.GetConfig(ssh_utils.HostKeyAlias(instance),
                                   args.strict_host_key_checking)
  extra_flags = ssh.ParseAndSubstituteSSHFlags(args, remote, external_address,
                                               internal_address)
  remainder = []

  remote_command = containers.GetRemoteCommand(None, command_list)

  cmd = ssh.SSHCommand(
      remote,
      identity_file=identity_file,
      options=options,
      extra_flags=extra_flags,
      remote_command=remote_command,
      remainder=remainder)
  if dry_run:
    DryRunLog(' '.join(cmd.Build(ssh_helper.env)))
    return 0

  return_code = cmd.Run(
      ssh_helper.env,
      explicit_output_file=explicit_output_file,
      explicit_error_file=explicit_error_file)
  log.out.flush()
  return return_code


def DryRunLog(msg):
  log.out.Print('[COMMAND TO RUN]: %s\n' % msg)
