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
"""Routes to/from Compute Engine VMs."""


from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import argparse
import io
import os
import re

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import lister
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.compute import ssh_utils
from googlecloudsdk.command_lib.compute.diagnose import external_helper
from googlecloudsdk.command_lib.compute.diagnose import internal_helpers
from googlecloudsdk.command_lib.util.ssh import ssh
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core.console import console_io
from googlecloudsdk.core.util import files
import six


DETAILED_HELP = {
    'EXAMPLES':
        """\
        To route to/from Compute Engine virtual machine instances, run:

          $ {command}
        """,
}


class Routes(base_classes.BaseCommand):
  """Routes to/from Compute Engine virtual machine instances.

  Routes to/from Compute Engine virtual machine instances.

  NOTE: The name filtering will cycle through all the VMs in the project.
  Depending on the size of the project, this could be a considerable amount
  of work.

  If that is the case, use the --regexp flag to filter down the amount
  of VMs considered in the filtering.
  """

  detailed_help = DETAILED_HELP

  @classmethod
  def Args(cls, parser):
    _RoutesArgs.Args(parser)

  def Run(self, args):
    """Default run method implementation."""
    super(Routes, self).Run(args)

    self._use_accounts_service = False

    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    resource_registry = holder.resources
    ssh_helper = ssh_utils.BaseSSHCLIHelper()
    ssh_helper.Run(args)

    # We store always needed commands non-changing fields
    self._args = args
    self._ssh_helper = ssh_helper

    # We obtain generic parameters of the call
    project = properties.VALUES.core.project.GetOrFail()
    filters = _RoutesArgs.GetFilters(args)
    instances = _RoutesQueries.ObtainInstances(
        args.names,
        service=self.compute.instances,
        project=project,
        zones=args.zones,
        filters=filters,
        http=self.http,
        batch_url=self.batch_url)

    user = args.user
    if not user:
      user = ssh.GetDefaultSshUsername()

    # We unpack the flags
    dry_run = args.dry_run
    reverse_traceroute = args.reverse_traceroute
    traceroute_args = args.traceroute_args
    external_route_ip = args.external_route_ip

    internal_helpers.PrintHeader(instances)
    prompt = 'The following VMs will be tracerouted.'
    if instances and not dry_run and not console_io.PromptContinue(prompt):
      return
    # Sometimes the prompt would appear after the instance data
    log.out.flush()

    for instance in instances:
      header = 'Checking instance %s' % instance.name
      log.out.Print(header)
      log.out.Print('-' * len(header))

      try:
        self.TracerouteInstance(instance, traceroute_args, dry_run,
                                resource_registry)
      except exceptions.ToolException as e:
        log.error('Error routing to instance')
        log.error(six.text_type(e))
        continue

      if reverse_traceroute:
        try:
          has_traceroute = self.CheckTraceroute(instance, user, dry_run,
                                                resource_registry)
          if has_traceroute:
            # We obtain the self ip
            if not external_route_ip:
              external_route_ip = self.ObtainSelfIp(instance, user, dry_run,
                                                    resource_registry)
            if external_route_ip:
              self.ReverseTracerouteInstance(instance, user, external_route_ip,
                                             traceroute_args, dry_run,
                                             resource_registry)
            else:
              log.out.Print('Unable to obtain self ip. Aborting.')
          else:
            log.out.Print(
                'Please make sure traceroute is installed in PATH to move on.')
        except ssh.CommandError as e:
          log.error(six.text_type(e))
      log.out.Print('')  # Separator

  ###########################################################
  # Traceroute Invocations
  ###########################################################

  def TracerouteInstance(self, instance, traceroute_args, dry_run,
                         resource_registry):
    """Runs a traceroute from localhost to a GCE VM.

    Args:
      instance: Compute Engine VM.
      traceroute_args: Additional traceroute args to be passed on.
      dry_run: Whether to only print commands instead of running them.
      resource_registry: gcloud class used for obtaining data from the
        resources.
    """
    instance_string = internal_helpers.GetInstanceNetworkTitleString(instance)
    log.out.Print('>>> Tracerouting to %s' % instance_string)

    external_ip = ssh_utils.GetExternalIPAddress(instance)
    cmd = ['traceroute', external_ip]
    if traceroute_args:
      cmd += traceroute_args
    if dry_run:
      external_helper.DryRunLog(' '.join(cmd))
    else:
      external_helper.RunSubprocess(proc_name='Traceroute', command_list=cmd)
      log.out.Print('>>>')

  def ReverseTracerouteInstance(self, instance, user, external_route_ip,
                                traceroute_args, dry_run, resource_registry):
    """Runs a traceroute from a GCE VM to localhost.

    Args:
      instance: Compute Engine VM.
      user: The user to use to SSH into the instance.
      external_route_ip: the ip to which traceroute from the VM
      traceroute_args: Additional traceroute args to be passed on.
      dry_run: Whether to only print commands instead of running them.
      resource_registry: gcloud class used for obtaining data from the
        resources.
    Raises:
      ssh.CommandError: there was an error running a SSH command
    """
    instance_string = internal_helpers.GetInstanceNetworkTitleString(instance)
    log.out.Print('<<< Reverse tracerouting from %s' % instance_string)
    # Necessary because the order of commands in the output
    # would be wrong otherwise (the ssh command will output by its own)
    log.out.flush()

    if dry_run:
      external_route_ip = '<SELF-IP>'
    cmd = ['traceroute', external_route_ip]
    if traceroute_args:
      cmd += traceroute_args
    external_helper.RunSSHCommandToInstance(
        command_list=cmd,
        instance=instance,
        user=user,
        args=self._args,
        ssh_helper=self._ssh_helper,
        dry_run=dry_run)
    # This identifier is a simple delimiter of each traceroute run
    if not dry_run:
      log.out.Print('<<<')

  def CheckTraceroute(self, instance, user, dry_run, resource_registry):
    """Checks whether the instance has traceroute in PATH.

    Args:
      instance: Compute Engine VM.
      user: The user to use to SSH into the instance.
      dry_run: Whether to only print commands instead of running them.
      resource_registry: gcloud class used for obtaining data from the
        resources.
    Returns:
      True if the instance has traceroute in PATH,
      False otherwise
    Raises:
      ssh.CommandError: there was an error running a SSH command
    """
    instance_string = internal_helpers.GetInstanceNetworkTitleString(instance)
    log.out.write('Checking traceroute for %s: ' % instance_string)
    if dry_run:
      log.out.Print('[DRY-RUN] No command executed.')
    log.out.flush()

    cmd = ['which', 'traceroute']
    try:
      # This command is silent
      with files.FileWriter(os.devnull) as dev_null:
        return_code = external_helper.RunSSHCommandToInstance(
            command_list=cmd,
            instance=instance,
            user=user,
            args=self._args,
            ssh_helper=self._ssh_helper,
            explicit_output_file=dev_null,
            dry_run=dry_run)
    except Exception as e:
      log.out.write(six.text_type(e))
      log.out.write('\n')  # Close the open print stmt
      log.out.flush()
      raise ssh.CommandError(' '.join(cmd), six.text_type(e))

    if return_code == 0:
      log.out.Print('Traceroute found in PATH')
    else:
      log.out.Print('Traceroute not found in PATH')
    log.out.flush()
    return return_code == 0

  def ObtainSelfIp(self, instance, user, dry_run, resource_registry):
    """Returns the localhost ip as seen from the VM.

    Args:
      instance: Compute Engine VM.
      user: The user to use to SSH into the instance.
      dry_run: Whether to only print commands instead of running them.
      resource_registry: gcloud class used for obtaining data from the
        resources.
    Returns:
      A string containing the local ip,
      None if the obtaining was unsuccessful
    Raises:
      ssh.CommandError: there was an error running a SSH command
    """
    instance_string = internal_helpers.GetInstanceNetworkTitleString(instance)
    log.out.write('Obtaining self ip from %s: ' % instance_string)
    # Sometimes this call will appear after the actual result
    log.out.flush()
    if dry_run:
      log.out.Print('<SELF-IP>')

    temp = io.BytesIO()
    cmd = ['echo', '$SSH_CLIENT']
    try:
      external_helper.RunSSHCommandToInstance(
          command_list=cmd,
          instance=instance,
          user=user,
          args=self._args,
          ssh_helper=self._ssh_helper,
          explicit_output_file=temp,
          dry_run=dry_run)
    except Exception as e:  # pylint: disable=broad-exception
      log.out.write('\n')  # Close the open print stmt
      log.out.flush()
      raise ssh.CommandError(' '.join(cmd), six.text_type(e))

    who_am_i_str = temp.getvalue().decode('utf-8')
    result = re.search(r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})', who_am_i_str)
    if result:
      res = result.group(1)
      log.out.Print(res)
      log.out.flush()
      return res

    return None

  @property
  def resource_type(self):
    return 'instances'


class _RoutesArgs(object):
  """Helper to setting and getting values for the args."""

  @classmethod
  def Args(cls, parser):
    """Creates the flags stmts for the command."""
    # Gives us the basic SSH flags
    ssh_utils.BaseSSHCLIHelper.Args(parser)

    base_classes.ZonalLister.Args(parser)

    # SSH flag
    parser.add_argument(
        '--container',
        help="""\
            The name or ID of a container inside of the virtual machine instance
            to connect to. This only applies to virtual machines that are using
            a Container-Optimized OS virtual machine image.
            For more information, see
            [](https://cloud.google.com/compute/docs/containers)
            """)

    parser.add_argument(
        '--external-route-ip',
        default=None,
        help=
        ('For reverse traceroute, this will be the ip given to the VM instance '
         'to traceroute to. This will override all obtained ips.'))

    parser.add_argument(
        '--reverse-traceroute',
        action='store_true',
        help='If enabled, will also run traceroute from the VM to the host')

    # SSH flag
    parser.add_argument(
        '--ssh-flag',
        action='append',
        help="""\
        Additional flags to be passed to *ssh(1)*. It is recommended that flags
        be passed using an assignment operator and quotes. This flag will
        replace occurences of ``%USER%'' and ``%INSTANCE%'' with their
        dereferenced values. Example:

          $ {command} example-instance --zone us-central1-a \
          --ssh-flag="-vvv" --ssh-flag="-L 80:%INSTANCE%:80"

        is equivalent to passing the flags ``--vvv'' and ``-L
        80:162.222.181.197:80'' to *ssh(1)* if the external IP address of
        'example-instance' is 162.222.181.197.
        """)

    parser.add_argument(
        '--user',
        help="""\
        User for login to the selected VMs.
        If not specified, the default user will be used.
        """)

    parser.add_argument(
        'traceroute_args',
        nargs=argparse.REMAINDER,
        help="""\
            Flags and positionals passed to the underlying traceroute call.
            """,
        example="""\
            $ {command} example-instance -- -w 0.5 -q 5 42
        """)

  @classmethod
  def GetFilters(cls, args):
    filters = []
    if args.regexp:
      filters.append('name eq %s' % args.regexp)

    if not filters:
      return None
    filters = ' AND '.join(filters)
    return filters


class _RoutesQueries(object):
  """Helper for getting instance queries using the gcloud SDK."""

  @classmethod
  def ObtainInstances(cls, names, **kwargs):
    """Returns a list of instances according to the flags."""
    errors = []
    result = lister.GetZonalResources(
        service=kwargs['service'],
        project=kwargs['project'],
        requested_zones=kwargs['zones'],
        filter_expr=kwargs['filters'],
        http=kwargs['http'],
        batch_url=kwargs['batch_url'],
        errors=errors)
    instances = list(result)

    # We filter them according to the names
    filtered_instances = []
    if not names:
      filtered_instances = instances
    else:
      for name in names:
        # First compare by name
        name_match = None
        in_name = None
        in_self_link = None

        for instance in instances:
          if name == instance.name:
            # Exact name match has a priority
            # over loose match on instance name or selfLink
            name_match = instance
            break
          elif name in instance.name:
            in_name = instance
          elif name in instance.selfLink:
            in_self_link = instance

        if name_match:
          filtered_instances.append(name_match)
        elif in_name:
          filtered_instances.append(in_name)
        elif in_self_link:
          filtered_instances.append(in_self_link)

    return filtered_instances
