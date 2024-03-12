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
"""SSH/SCP utilities for Cloud TPU VM commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import copy
import io
import sys
import threading
import time

from apitools.base.py import encoding_helper
from apitools.base.py.exceptions import HttpConflictError
from apitools.base.py.exceptions import HttpError
from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.compute import iap_tunnel
from googlecloudsdk.command_lib.compute import ssh_utils
from googlecloudsdk.command_lib.compute.tpus.tpu_vm import exceptions as tpu_exceptions
from googlecloudsdk.command_lib.compute.tpus.tpu_vm import util as tpu_utils
from googlecloudsdk.command_lib.util.ssh import ssh
from googlecloudsdk.core import execution_utils
from googlecloudsdk.core import log
from googlecloudsdk.core.util.files import FileWriter
import six

SSH_KEYS_METADATA_KEY = 'ssh-keys'

IAP_TROUBLESHOOTING_HELP = """
Please check the following:
- Verify that the 'compute.disableGuestAttributesAccess'
  Organization Policy Constraint is not enforced in your project.
- Verify that this TPU was created after March 24, 2022.
- Check that you have allowed IAP to connect to instances in your
  firewall (https://cloud.google.com/iap/docs/using-tcp-forwarding#create-firewall-rule),
  and that the TPU is in READY state with HEALTHY health.
"""


def AddTPUSSHArgs(
    parser, enable_iap, enable_batching=False, enable_batching_default='all'
):
  """Arguments that are common and specific to both TPU VM/QR SSH and SCP."""
  parser.add_argument(
      '--worker',
      default='0',
      help="""\
          TPU worker to connect to. The supported value is a single 0-based
          index of the worker in the case of a TPU Pod. When also using the
          `--command` flag, it additionally supports a comma-separated list
          (e.g. '1,4,6'), range (e.g. '1-3'), or special keyword ``all" to
          run the command concurrently on each of the specified workers.

          Note that when targeting multiple workers, you should run 'ssh-add'
          with your private key prior to executing the gcloud command. Default:
          'ssh-add ~/.ssh/google_compute_engine'.
          """)
  if enable_batching:
    parser.add_argument(
        '--batch-size',
        default=enable_batching_default,
        help="""\
            Batch size for simultaneous command execution on the client's side.
            When using a comma-separated list (e.g. '1,4,6') or a range (e.g. '1-3') or
            ``all`` keyword in `--worker` flag, it executes the command
            concurrently in groups of the batch size. This flag takes a
            value greater than 0 to specify the batch size to control the
            concurrent connections that can be established with the TPU
            workers, or the special keyword ``all`` to allow the concurrent
            command executions on all the specified workers in `--worker` flag.
            Maximum value of this flag should not be more than the number of
            specified workers, otherwise the value will be treated as
            ``--batch-size=all``.
            """,
    )
  if enable_iap:
    routing_group = parser.add_mutually_exclusive_group()
    routing_group.add_argument(
        '--internal-ip',
        action='store_true',
        help="""\
            Connect to TPU VMs using their internal IP addresses rather than their
            external IP addresses. Use this to connect from a Google Compute
            Engine VM to a TPU VM on the same VPC network, or between two peered
            VPC networks.
            """)
    routing_group.add_argument(
        '--tunnel-through-iap',
        action='store_true',
        help="""\
        Tunnel the SSH connection through Cloud Identity-Aware Proxy for TCP
        forwarding.

        This flag must be specified to attempt to connect via IAP tunneling. If it
        is not set, and connection to a Cloud TPU VM without external IP address
        is attempted from outside the network, then the command will fail.

        To use IAP tunneling, there must be firewall access to the SSH port for
        the IAP TCP IP address range for the network the TPU is created in. See
        the [user guide](https://cloud.google.com/iap/docs/using-tcp-forwarding)
        for more details.

        To learn more, see the
        [IAP for TCP forwarding documentation](https://cloud.google.com/iap/docs/tcp-forwarding-overview).
        """)
  else:
    parser.add_argument(
        '--internal-ip',
        action='store_true',
        help="""\
            Connect to TPU VMs using their internal IP addresses rather than their
            external IP addresses. Use this to connect from a Google Compute
            Engine VM to a TPU VM on the same VPC network, or between two peered
            VPC networks.
            """)


def ValidateTPUState(state, state_enum, tpu_name):
  """Validates the TPU's state.

  Prints warnings or throws exceptions when appropriate.

  Args:
    state: the state of the TPU.
    state_enum: the enum for all TPU states.
    tpu_name: the name of the TPU VM.
  """
  if state is state_enum.READY:
    # This is the base case.
    pass
  elif state is state_enum.STATE_UNSPECIFIED:
    log.warning(
        'The TPU VM "{}" is in state "{}", therefore the TPU may not be'
        ' available or reachable.'.format(tpu_name, state)
    )
  elif state in [
      state_enum.CREATING, state_enum.STARTING, state_enum.REPAIRING,
      state_enum.HIDING, state_enum.UNHIDING
  ]:
    log.warning(
        'The TPU VM "{}" is in state "{}", therefore the TPU may not be'
        ' available or reachable. If the connection fails, please try again'
        ' later.'.format(tpu_name, state)
    )
  elif state in [
      state_enum.STOPPED, state_enum.STOPPING, state_enum.DELETING,
      state_enum.HIDDEN
  ]:
    raise tpu_exceptions.TPUInUnusableState(state)
  elif state in [state_enum.PREEMPTED, state_enum.TERMINATED]:
    raise tpu_exceptions.TPUInUnusableTerminalState(state)


class IPAddresses():
  """Worker is a holder for the worker IP addresses."""

  def __init__(self, ip_address, internal_address):
    self.ip_address = ip_address
    self.internal_address = internal_address


def ParseWorkerFlag(worker_flag, network_endpoints, use_internal_ips):
  """Parses the --worker flag into a dict of worker indexes to IP addresses."""
  n_vms = len(network_endpoints)
  if six.text_type(worker_flag).upper() == 'ALL':
    indexes = list(range(n_vms))
  else:
    indexes = set()
    ranges = worker_flag.split(',')
    for r in ranges:
      if not r:
        continue
      if '-' in r:
        bounds = r.split('-')
        if len(bounds) != 2 or not bounds[0] or not bounds[1]:
          raise exceptions.InvalidArgumentException(
              '--worker', 'found malformed range "{}".'.format(r))
        start, end = int(bounds[0]), int(bounds[1])
        if start >= end:
          raise exceptions.InvalidArgumentException(
              '--worker', 'found malformed range "{}".'.format(r))
        indexes.update(range(start, end + 1))
      else:
        try:
          indexes.add(int(r))
        except ValueError:
          raise exceptions.InvalidArgumentException(
              '--worker', 'unable to parse worker ID {}. Please only use'
              'numbers.'.format(r))

  if not indexes:
    raise exceptions.InvalidArgumentException(
        '--worker', 'no worker specified, or none were parsed from the '
        'argument value.')

  mx = max(indexes)
  if mx >= n_vms:
    raise exceptions.InvalidArgumentException(
        '--worker', 'worker index {} is larger than the valid worker indexes '
        'on this TPU VM. Please only use indexes in the range [0, {}], '
        'inclusive.'.format(mx, n_vms - 1))

  # Get the VMs' IP addresses.
  worker_ips = {}
  for worker in indexes:
    internal_address = network_endpoints[worker].ipAddress
    if (not use_internal_ips and network_endpoints[worker].accessConfig and
        network_endpoints[worker].accessConfig.externalIp):
      ip_address = network_endpoints[worker].accessConfig.externalIp
    else:
      ip_address = internal_address
    worker_ips[worker] = IPAddresses(ip_address, internal_address)
  return worker_ips


def ParseBatchSize(batch_size_flag, num_ips):
  """Parses the --batch-size flag and validates the flag value.

  Args:
    batch_size_flag: str, batch-size flag argument.
    num_ips: int, number of ip-addresses for the ssh command execution.

  Returns:
    int, batch-size value capped at number of workers in num_ips.

  Raises:
    InvalidArgumentException, if the batch_size_flag is neither a positive
    integer nor equal to the `all` keyword.
  """
  if six.text_type(batch_size_flag).upper() == 'ALL':
    if num_ips > 100:
      log.warning('Executing ssh command on too many workers simultaneously is '
                  'prone to error. Command may fail. Please consider using '
                  '`--batch-size` flag if the command fails, for example, '
                  '--batch-size=100.')
    return num_ips
  else:
    try:
      if int(batch_size_flag) > 0:
        return min(int(batch_size_flag), num_ips)
      else:
        raise ValueError()
    except ValueError as error:
      six.raise_from(
          exceptions.InvalidArgumentException(
              '--batch-size',
              'unable to parse the batch size value {}. Please use a positive '
              'integer not more than the number of TPU workers.'.format(
                  batch_size_flag)), error)


def _ParseHostKeySuffixes(guest_attributes):
  """Returns the host key suffixes."""
  host_key_suffixes = []
  for worker_guest_attributes in guest_attributes:
    for item in worker_guest_attributes.queryValue.items:
      if item.key == 'ssh-ed25519':
        host_key_suffixes.append(item.value[-6:])
        break
  return host_key_suffixes


def _ParseSingleHostKeySuffix(guest_attributes, worker_count, worker):
  """Returns a list with only a single worker's host key suffix populated."""
  suffixes = [''] * worker_count
  for item in guest_attributes[0].queryValue.items:
    if item.key == 'ssh-ed25519':
      suffixes[worker] = item.value[-6:]
      break
  return suffixes


def GetFromGuestAttributes(guest_attributes, worker, key):
  for item in guest_attributes[worker].queryValue.items:
    if item.key == key:
      return item.value
  return None


def GetHostKeySuffixesFromGuestAttributes(guest_attributes_response,
                                          single_pod_worker, worker_ips, node):
  """Retrieves the host key suffixes from the GuestAttributes."""
  if single_pod_worker:
    worker_id = list(worker_ips)[0]
    return _ParseSingleHostKeySuffix(guest_attributes_response.guestAttributes,
                                     len(node.networkEndpoints), worker_id)
  else:
    return _ParseHostKeySuffixes(guest_attributes_response.guestAttributes)


def GetGuestAttributes(tpu_helper, single_pod_worker, worker_ips, tpu_name,
                       zone):
  """Retrieves the GuestAttributes."""
  if single_pod_worker:
    # Retrieve only that worker's GuestAttributes.
    worker_id = list(worker_ips)[0]
    try:
      guest_attributes_response = tpu_helper.GetGuestAttributes(
          tpu_name, zone, six.text_type((worker_id)))
    except HttpError:
      return None
  else:
    # Retrieve the GuestAttributes for all workers in that TPU.
    try:
      guest_attributes_response = tpu_helper.GetGuestAttributes(tpu_name, zone)
    except HttpError:
      return None
  return guest_attributes_response


def TpuHasOsLoginEnabled(node):
  """Returns true if the node has OSLogin enabled."""
  node_dict = encoding_helper.MessageToDict(node)
  if 'metadata' in node_dict and 'enable-oslogin' in node_dict['metadata']:
    return node_dict['metadata']['enable-oslogin'].upper() == 'TRUE'
  return None


def _MetadataHasSSHKey(metadata, public_key):
  """Returns true if the metadata has the SSH key.

  Args:
    metadata: Project metadata.
    public_key: The SSH key.

  Returns:
    True if present, False if not present.
  """
  if not (metadata and metadata.items):
    return False
  matching_values = [
      item.value for item in metadata.items if item.key == SSH_KEYS_METADATA_KEY
  ]
  if not matching_values:
    return False
  return public_key in matching_values[0]


def AddSSHKeyIfNeeded(project, tpu_helper, node, tpu_name, zone, public_key):
  """Verifies that instance has SSH key, and adds it in case it doesn't."""
  # Args: node, project, SSH key?
  # 1. Check the project metadata for the key.
  if _MetadataHasSSHKey(project.commonInstanceMetadata, public_key):
    log.status.Print(
        'SSH key found in project metadata; not updating instance.')
    return
  # 2. Check the instance metadata for the key.
  node_dict = encoding_helper.MessageToDict(node)
  ssh_keys = ''
  if 'metadata' in node_dict and SSH_KEYS_METADATA_KEY in node_dict['metadata']:
    ssh_keys = node_dict['metadata'][SSH_KEYS_METADATA_KEY]
  if public_key in ssh_keys:
    log.debug('SSH key found in instance metadata; not updating instance.')
    return
  # 3. Call update node if not present.
  ssh_keys += '\n' + public_key
  node_for_update = tpu_helper.messages.Node(
      metadata=tpu_helper.UpdateMetadataKey(
          metadata=node.metadata, key=SSH_KEYS_METADATA_KEY, value=ssh_keys))
  try:
    tpu_helper.UpdateNode(
        tpu_name,
        zone,
        node_for_update,
        'metadata',
        'Propagating SSH public key to all TPU workers',
    )
  except HttpConflictError:
    # Do not fail the SSH if there is already an UpdateNode call in flight.
    pass


def GetInstanceID(node_id, worker, host_key_suffixes):
  instance_id = 'tpu.{}-{}'.format(node_id, worker)
  if host_key_suffixes is not None and len(host_key_suffixes) > worker:
    instance_id += '-{}'.format(host_key_suffixes[worker])
  return instance_id


def VerifyKeyInAgent(identity_file):
  """Verifies that the ssh-agent holds the SSH key."""
  # Generate key fingerprint.
  cmd = ['ssh-keygen', '-lf', identity_file]
  keygen_out = io.StringIO()
  err = io.StringIO()
  retcode = execution_utils.Exec(
      cmd, no_exit=True, out_func=keygen_out.write, err_func=err.write)
  if retcode != 0:
    log.debug('ssh-keygen exited with error {}'.format(err.getvalue()))
    log.warning('Cannot generate fingerprint of SSH key. Command may stall.')
    return
  fingerprint_entry = keygen_out.getvalue()
  if len(fingerprint_entry.split()) <= 1:
    log.debug('ssh-keygen returned fingerprint entry in invalid format: "{}"'
              ''.format(fingerprint_entry))
    return
  # Only use the actual fingerprint part of the fingerprint entry.
  fingerprint = fingerprint_entry.split()[1]

  # Get keys in agent.
  cmd = ['ssh-add', '-l']
  out = io.StringIO()
  retcode = execution_utils.Exec(
      cmd, no_exit=True, out_func=out.write, err_func=err.write)
  if retcode != 0:
    log.debug('ssh-add exited with error {}'.format(err.getvalue()))
    log.warning('Cannot retrieve keys in ssh-agent. Command may stall.')
    return

  if fingerprint not in out.getvalue():
    raise tpu_exceptions.SSHKeyNotInAgent(identity_file)


def CreateSshTunnelArgs(args, track, project, zone, instance):
  """Construct an SshTunnelArgs object from command line args and values."""
  # If tunneling through IAP is not available or specified, then abort.
  if not args.IsKnownAndSpecified('tunnel_through_iap'):
    return None

  res = iap_tunnel.SshTunnelArgs()

  res.track = track.prefix
  res.project = project.name
  res.zone = zone
  res.instance = instance

  return res


def WaitForBatchCompletion(ssh_threads, exit_statuses):
  """Waits for all the running ssh threads to complete.

  Exits with a nonzero code, if there are any non-zero exit status in ssh
  command execution. This ensures that if any command failed on a worker,
  we don't end up returning 0 for a value.

  Args:
    ssh_threads: List of ssh threads.
    exit_statuses: List of exit status of each ssh execution.
  """
  for ssh_thread in ssh_threads:
    ssh_thread.join()

  for status in exit_statuses:
    if status:
      sys.exit(status)


def AttemptRunWithRetries(command_name, worker, exit_statuses, cmd, env,
                          output_file, multiple_workers, run_cmd):
  """Attempts to connect to a worker using SSH or SCP."""
  max_attempts = 10
  sleep_interval = 5
  # Since SSH keys may have recently been set in the instance's metadata by
  # the UpdateNode call, it can take some time before those are propagated
  # correctly and the SSH command's authorization is successful. Therefore,
  # we wrap this in a retry loop. No exponential back-off is needed here, as
  # we're not looking to throttle.
  for i in range(max_attempts):
    try:
      log.status.Print('{}: Attempting to connect to worker {}...'.format(
          command_name, worker))
      exit_status = run_cmd(env, cmd, output_file)
      if exit_status:
        # This is the exit status of the remote command.  Problems with SSH
        # itself will result in ssh.CommandError being raised above.
        if multiple_workers:
          log.status.Print('##### Command execution on worker {} failed '
                           'with exit status {}. Continuing.'
                           ''.format(worker, exit_status))
          # Store the exit status in list so that we can check it in the main
          # thread.
          exit_statuses[worker] = exit_status
        sys.exit(exit_status)
    except ssh.CommandError as e:
      if i == max_attempts - 1:
        if multiple_workers:
          # We need to store the exit status, since the exception will not be
          # caught by the calling thread.
          exit_statuses[worker] = 255
        raise e
      if multiple_workers:
        log.status.Print(
            'Failed to execute command on multiple workers. '
            'This may have happened if you have not added '
            'your SSH key to your ssh-agent using "ssh-add '
            '~/.ssh/google_compute_engine".'
        )
      log.status.Print(
          'Retrying: {} command error: {}'.format(
              command_name, six.text_type(e)
          )
      )
      time.sleep(sleep_interval)
      continue
    break


def SSHPrepCmd(args, prepped_node, worker, ips):
  """Prepares the SSH command used to SSH into the worker.

  Args:
    args: The arguments passed in by the user.
    prepped_node: The object that contains all the necessary information to ssh
      into the node.
    worker: the worker to ssh into.
    ips: The ips of the worker

  Returns:
    ssh.SSHCommand that can be used to execute SSH command.
  """
  identity_file = None
  options = None
  if not args.plain:
    identity_file = prepped_node.ssh_helper.keys.key_file
    options = prepped_node.ssh_helper.GetConfig(
        GetInstanceID(prepped_node.id, worker, prepped_node.host_key_suffixes),
        args.strict_host_key_checking,
        None,
    )

  remote = ssh.Remote(ips.ip_address, prepped_node.user)
  extra_flags = ssh.ParseAndSubstituteSSHFlags(
      args, remote, ips.ip_address, ips.internal_address
  )

  iap_tunnel_args = None
  if args.IsKnownAndSpecified('tunnel_through_iap') and args.tunnel_through_iap:
    # Retrieve the instance name from the GuestAttributes.
    instance_name = prepped_node.instance_names[worker]
    iap_tunnel_args = CreateSshTunnelArgs(
        args,
        prepped_node.release_track,
        prepped_node.project,
        args.zone,
        instance_name,
    )

  return ssh.SSHCommand(
      remote=remote,
      identity_file=identity_file,
      remote_command=prepped_node.command_list,
      extra_flags=extra_flags,
      options=options,
      remainder=prepped_node.remainder,
      iap_tunnel_args=iap_tunnel_args,
  )


def SSHRunCmd(env, cmd, output_file_writer):
  """Returns a function to run."""
  return cmd.Run(
      env,
      explicit_output_file=output_file_writer,
      explicit_error_file=output_file_writer,
  )


def PrepareNodeForSSH(
    tpu_name,
    user,
    args,
    release_track,
    enable_batching,
    username_requested,
    prepped_nodes,
    idx,
):
  """Prepares TPU VM Node for SSH.

  Args:
    tpu_name: The unqualified name of the tpu instance to prepare for SSH.
    user: The username to use for SSH.
    args: The command line arguments used for SSH.
    release_track: The release track/version of client protos to use.
    enable_batching: A bool, True if the user opts into batching requests.
    username_requested: A bool, True if the user has passed a specific username
      in the args.
    prepped_nodes: The list to put resulting prepared nodes into.
    idx: The index specifying which slot in the 'prepped_nodes' list to put the
      output node.

  Returns:
    The prepared node that is now ready for SSH.

  Raises:
    BadArgumentException: If the node retrieved is not a TPU VM. Non TPU VMs are
      not supported.
    InvalidArgumentException: If there is no command specified, but multiple
      workers are targeted.
    IapTunnelingUnavailable: If IAP Tunneling is not available, the node cannot
      be SSHed into.
  """
  prepped_node = tpu_utils.SSHPreppedNode(
      tpu_name, user, release_track, enable_batching
  )

  tpu = tpu_utils.TPUNode(release_track)
  node = tpu.Get(tpu_name, args.zone)

  if not tpu_utils.IsTPUVMNode(node):
    raise exceptions.BadArgumentException(
        'TPU',
        'this command is only available for Cloud TPU VM nodes. To access '
        'this node, please see '
        'https://cloud.google.com/tpu/docs/creating-deleting-tpus.',
    )

  ValidateTPUState(node.state, tpu.messages.Node.StateValueValuesEnum, tpu_name)

  prepped_node.worker_ips = ParseWorkerFlag(
      args.worker, node.networkEndpoints, args.internal_ip
  )

  if len(prepped_node.worker_ips) > 1 and not args.command:
    raise exceptions.InvalidArgumentException(
        '--worker',
        'cannot target multiple workers without the `--command` flag.',
    )

  if (
      node.health
      == tpu.messages.Node.HealthValueValuesEnum.UNHEALTHY_MAINTENANCE
  ):
    log.warning(
        '!!! This TPU is going through a maintenance event, and might be'
        ' unavailable !!!'
    )

  # Retrieve GuestAttributes.
  single_pod_worker = (
      len(node.networkEndpoints) > 1 and len(prepped_node.worker_ips) == 1
  )
  guest_attributes_response = GetGuestAttributes(
      tpu, single_pod_worker, prepped_node.worker_ips, tpu_name, args.zone
  )
  if guest_attributes_response is None:
    if (
        args.IsKnownAndSpecified('tunnel_through_iap')
        and args.tunnel_through_iap
    ):
      log.debug('Unable to retrieve host information from guest attributes.')
      log.status.Print('Failed to connect to TPU.')
      log.status.Print(IAP_TROUBLESHOOTING_HELP)
      raise tpu_exceptions.IapTunnelingUnavailable()
    log.debug('Unable to retrieve host keys from guest attributes. Continuing.')
    prepped_node.host_key_suffixes = None
  else:
    prepped_node.host_key_suffixes = GetHostKeySuffixesFromGuestAttributes(
        guest_attributes_response,
        single_pod_worker,
        prepped_node.worker_ips,
        node,
    )

  # Generate the public key.
  prepped_node.ssh_helper = ssh_utils.BaseSSHCLIHelper()
  prepped_node.ssh_helper.Run(args)
  public_key = prepped_node.ssh_helper.keys.GetPublicKey().ToEntry()

  prepped_node.project = tpu_utils.GetProject(
      release_track, prepped_node.ssh_helper
  )

  if not args.plain:
    # If there is an '@' symbol in the user_host arg, the user is requesting
    # to connect as a specific user. This may get overridden by OS Login.
    _, expiration_micros = ssh_utils.GetSSHKeyExpirationFromArgs(args)
    oslogin_state = ssh.GetOsloginState(
        None,
        prepped_node.project,
        user,
        public_key,
        expiration_micros,
        release_track,
        username_requested=username_requested,
        instance_enable_oslogin=TpuHasOsLoginEnabled(node),
        messages=base_classes.ComputeApiHolder(release_track).client.messages,
    )
    prepped_node.user = user = oslogin_state.user

  # Format the key correctly.
  public_key = '{1}:{0} {1}'.format(public_key, user)

  if not args.plain and not args.dry_run:
    AddSSHKeyIfNeeded(
        prepped_node.project, tpu, node, tpu_name, args.zone, public_key
    )

  prepped_node.command_list = args.command.split(' ') if args.command else None

  prepped_node.remainder = []
  if args.ssh_args:
    prepped_node.remainder.extend(args.ssh_args)

  output_directory_path = None
  if args.output_directory:
    log.status.Print(
        'Preparing SSH command execution; output will be logged to {}'.format(
            output_directory_path
        )
    )

  prepped_node.instance_names = {}
  if args.IsKnownAndSpecified('tunnel_through_iap') and args.tunnel_through_iap:
    # Retrieve the instance names from the GuestAttributes.
    for worker in prepped_node.worker_ips:
      # The GuestAttributes will only have one entry if we're targeting a
      # single worker.
      index = 0 if single_pod_worker else worker
      instance_name = GetFromGuestAttributes(
          guest_attributes_response.guestAttributes, index, 'hostname'
      )
      if instance_name is None:
        log.status.Print('Failed to connect to TPU.')
        log.status.Print(IAP_TROUBLESHOOTING_HELP)
        raise tpu_exceptions.IapTunnelingUnavailable()
      prepped_node.instance_names[worker] = instance_name

  prepped_node.id = node.id
  prepped_nodes[idx] = prepped_node
  return prepped_node


def SSHIntoPreppedNodes(
    prepped_nodes,
    args,
    total_ssh_batch_size,
):
  """SSH's into the prepped nodes.

  Args:
    prepped_nodes: The list of prepared nodes to be SSHed into.
    args: The list of arguments passed in to SSH with.
    total_ssh_batch_size: The final parsed batch size to SSH into the workers'
      nodes.
  """
  ssh_threads = []
  current_batch_size = 0

  worker_ips = []
  for prepped_node in prepped_nodes:
    worker_ips.extend(prepped_node.worker_ips.items())

  num_ips = len(worker_ips)
  exit_statuses = [None] * num_ips

  log.status.Print(
      'Using ssh batch size of {}.'
      ' Attempting to SSH into {} nodes with a total of'
      ' {} workers.'.format(total_ssh_batch_size, len(prepped_nodes), num_ips)
  )
  for prepped_node in prepped_nodes:
    for worker, ips in prepped_node.worker_ips.items():
      cmd = SSHPrepCmd(args, prepped_node, worker, ips)

      if args.dry_run:
        log.out.Print(' '.join(cmd.Build(prepped_node.ssh_helper.env)))
        continue

      output_file_writer = None
      output_directory_path = None
      if args.output_directory:
        output_file_writer = FileWriter(
            '{}/{}.log'.format(output_directory_path, six.text_type(worker))
        )

      # Orchestrate threading of ssh commands based on number of workers/nodes,
      if len(prepped_node.worker_ips) > 1 or len(prepped_nodes) > 1:
        # Run the command on multiple workers concurrently.
        ssh_threads.append(
            threading.Thread(
                target=AttemptRunWithRetries,
                args=(
                    'SSH',
                    worker,
                    exit_statuses,
                    cmd,
                    prepped_node.ssh_helper.env,
                    output_file_writer,
                    True,
                    SSHRunCmd,
                ),
            )
        )
        ssh_threads[-1].start()
        current_batch_size += 1
        if (
            prepped_node.enable_batching
            and current_batch_size == total_ssh_batch_size
        ):
          WaitForBatchCompletion(ssh_threads, exit_statuses)
          current_batch_size = 0
          ssh_threads = []
      else:
        # Run on a single worker.
        AttemptRunWithRetries(
            'SSH',
            worker,
            exit_statuses,
            cmd,
            prepped_node.ssh_helper.env,
            output_file_writer,
            False,
            SSHRunCmd,
        )

  if num_ips > 1 and ssh_threads:
    WaitForBatchCompletion(ssh_threads, exit_statuses)


def SCPPrepCmd(args, prepped_node, worker, ips):
  """Prepares the SCP command used to SCP into the worker.

  Args:
    args: The arguments passed in by the user.
    prepped_node: The object that contains all the necessary information to scp
      into the node.
    worker: the worker to scp into.
    ips: The ips of the worker

  Returns:
    ssh.SCPCommand that can be used to execute SCP command.
  """
  # Make a copy of the destination for each worker so that concurrent
  # threads do not mutate the same object. b/238058396
  worker_dst = copy.deepcopy(prepped_node.dst)
  if worker_dst.remote:
    # SCP from local to TPU-VM.
    worker_dst.remote.host = ips.ip_address
  else:
    # SCP from  TPU-VM to local.
    # copy.deepcopy() is not needed for this case because copying from
    # remote to local only supports a single worker, so there is no concern
    # of race conditions that mutate the remote ip address
    prepped_node.srcs[0].remote.host = ips.ip_address

  options = None
  if not args.plain:
    options = prepped_node.ssh_helper.GetConfig(
        GetInstanceID(prepped_node.id, worker, prepped_node.host_key_suffixes),
        args.strict_host_key_checking,
        None,
    )

  iap_tunnel_args = None
  if args.IsKnownAndSpecified('tunnel_through_iap') and args.tunnel_through_iap:
    # Retrieve the instance name from the GuestAttributes.
    instance_name = prepped_node.instance_names[worker]
    iap_tunnel_args = CreateSshTunnelArgs(
        args,
        prepped_node.release_track,
        prepped_node.project,
        args.zone,
        instance_name,
    )

  return ssh.SCPCommand(
      prepped_node.srcs,
      worker_dst,
      identity_file=prepped_node.identity_file,
      options=options,
      recursive=args.recurse,
      compress=args.compress,
      extra_flags=prepped_node.extra_flags,
      iap_tunnel_args=iap_tunnel_args,
  )


def SCPRunCmd(env, cmd, *args):
  """Returns a function to run."""
  del args
  return cmd.Run(env)


def PrepareNodeForSCP(
    tpu_name,
    args,
    release_track,
    enable_batching,
    username_requested,
    prepped_nodes,
    idx,
    srcs,
    dst,
    remote,
):
  """Prepares TPU VM Node for SCP.

  Args:
    tpu_name: The unqualified name of the tpu instance to prepare for SCP.
    args: The command line arguments used for SCP.
    release_track: The release track/version of client protos to use.
    enable_batching: A bool, True if the user opts into batching requests.
    username_requested: A bool, True if the user has passed a specific username
      in the args.
    prepped_nodes: The list to put resulting prepared nodes into.
    idx: The index specifying which slot in the 'prepped_nodes' list to put the
      output node.
    srcs: The list of sources for the file to send from.
    dst: The destination to put the SCP-ed file.
    remote: The remote location for the file to be SCP-ed.

  Returns:
    The prepared node that is now ready for SCP.

  Raises:
    BadArgumentException: If the node retrieved is not a TPU VM. Non TPU VMs are
      not supported.
    InvalidArgumentException: If there are multiple workers targeted.
    IapTunnelingUnavailable: If IAP Tunneling is not available, the node cannot
      be SCPed into.
  """
  prepped_node = tpu_utils.SCPPreppedNode(
      tpu_name, None, release_track, enable_batching, srcs, dst
  )

  tpu = tpu_utils.TPUNode(release_track)
  node = tpu.Get(tpu_name, args.zone)
  if not tpu_utils.IsTPUVMNode(node):
    raise exceptions.BadArgumentException(
        'TPU',
        'this command is only available for Cloud TPU VM nodes. To access '
        'this node, please see '
        'https://cloud.google.com/tpu/docs/creating-deleting-tpus.',
    )

  prepped_node.worker_ips = ParseWorkerFlag(
      args.worker, node.networkEndpoints, args.internal_ip
  )

  if len(prepped_node.worker_ips) > 1 and prepped_node.srcs[0].remote:
    raise exceptions.InvalidArgumentException(
        '--worker',
        'cannot target multiple workers while copying files to client.',
    )

  ValidateTPUState(node.state, tpu.messages.Node.StateValueValuesEnum, tpu_name)

  if (
      node.health
      == tpu.messages.Node.HealthValueValuesEnum.UNHEALTHY_MAINTENANCE
  ):
    log.warning(
        '!!! This TPU is going through a maintenance event, and might be'
        ' unavailable !!!'
    )

  # Retrieve GuestAttributes.
  single_pod_worker = (
      len(node.networkEndpoints) > 1 and len(prepped_node.worker_ips) == 1
  )
  guest_attributes_response = GetGuestAttributes(
      tpu, single_pod_worker, prepped_node.worker_ips, tpu_name, args.zone
  )
  if guest_attributes_response is None:
    if (
        args.IsKnownAndSpecified('tunnel_through_iap')
        and args.tunnel_through_iap
    ):
      log.debug('Unable to retrieve host information from guest attributes.')
      log.status.Print('Failed to connect to TPU.')
      log.status.Print(IAP_TROUBLESHOOTING_HELP)
      raise tpu_exceptions.IapTunnelingUnavailable()
    log.debug('Unable to retrieve host keys from guest attributes. Continuing.')
    prepped_node.host_key_suffixes = None
  else:
    prepped_node.host_key_suffixes = GetHostKeySuffixesFromGuestAttributes(
        guest_attributes_response,
        single_pod_worker,
        prepped_node.worker_ips,
        node,
    )

  # Generate the public key.
  prepped_node.ssh_helper = ssh_utils.BaseSSHCLIHelper()
  prepped_node.ssh_helper.Run(args)
  public_key = prepped_node.ssh_helper.keys.GetPublicKey().ToEntry()

  prepped_node.project = tpu_utils.GetProject(
      release_track, prepped_node.ssh_helper
  )

  if not args.plain:
    # If there is an '@' symbol in the user_host arg, the user is requesting
    # to connect as a specific user. This may get overridden by OS Login.
    _, expiration_micros = ssh_utils.GetSSHKeyExpirationFromArgs(args)
    oslogin_state = ssh.GetOsloginState(
        None,
        prepped_node.project,
        remote.user,
        public_key,
        expiration_micros,
        release_track,
        username_requested=username_requested,
        instance_enable_oslogin=TpuHasOsLoginEnabled(node),
        messages=base_classes.ComputeApiHolder(release_track).client.messages,
    )
    prepped_node.user = remote.user = oslogin_state.user

  # Format the key correctly.
  public_key = '{1}:{0} {1}'.format(public_key, remote.user)
  if not args.plain and not args.dry_run:
    AddSSHKeyIfNeeded(
        prepped_node.project, tpu, node, tpu_name, args.zone, public_key
    )

  prepped_node.identity_file = None
  if not args.plain:
    prepped_node.identity_file = prepped_node.ssh_helper.keys.key_file
    # If the user's key is not in the SSH agent, the command will stall. We
    # want to verify it is added before proceeding, and raise an error if it
    # is not.
    if not args.dry_run and len(prepped_node.worker_ips) > 1:
      VerifyKeyInAgent(prepped_node.identity_file)

  prepped_node.extra_flags = []

  if args.scp_flag:
    prepped_node.extra_flags.extend(args.scp_flag)

  prepped_node.instance_names = {}
  if args.IsKnownAndSpecified('tunnel_through_iap') and args.tunnel_through_iap:
    # Retrieve the instance names from the GuestAttributes.
    for worker in prepped_node.worker_ips:
      # The GuestAttributes will only have one entry if we're targeting a
      # single worker.
      index = 0 if single_pod_worker else worker
      instance_name = GetFromGuestAttributes(
          guest_attributes_response.guestAttributes, index, 'hostname'
      )
      if instance_name is None:
        log.status.Print('Failed to connect to TPU.')
        log.status.Print(IAP_TROUBLESHOOTING_HELP)
        raise tpu_exceptions.IapTunnelingUnavailable()
      prepped_node.instance_names[worker] = instance_name

  prepped_node.id = node.id
  prepped_nodes[idx] = prepped_node
  return prepped_node


def SCPIntoPreppedNodes(
    prepped_nodes,
    args,
    total_scp_batch_size,
):
  """SCP's into the prepped nodes.

  Args:
    prepped_nodes: The list of prepared nodes to be SCPed into.
    args: The list of arguments passed in to SCP with.
    total_scp_batch_size: The final parsed batch size to SCP into the nodes'
      workers.
  """
  scp_threads = []
  current_batch_size = 0

  worker_ips = []
  for prepped_node in prepped_nodes:
    worker_ips.extend(prepped_node.worker_ips.items())

  num_ips = len(worker_ips)
  exit_statuses = [None] * num_ips

  log.status.Print(
      'Using scp batch size of {}.'
      'Attempting to SCP into {} nodes with a total of'
      ' {} workers.'.format(total_scp_batch_size, len(prepped_nodes), num_ips)
  )
  for prepped_node in prepped_nodes:
    for worker, ips in prepped_node.worker_ips.items():
      cmd = SCPPrepCmd(args, prepped_node, worker, ips)

      if args.dry_run:
        log.out.Print(' '.join(cmd.Build(prepped_node.ssh_helper.env)))
        continue

      # Orchestrate threading of scp commands based on number of workers, if
      # batching is enabled, and batch size
      if len(prepped_node.worker_ips) > 1 or len(prepped_nodes) > 1:
        # Run the command on multiple workers concurrently.
        scp_threads.append(
            threading.Thread(
                target=AttemptRunWithRetries,
                args=(
                    'SCP',
                    worker,
                    exit_statuses,
                    cmd,
                    prepped_node.ssh_helper.env,
                    None,
                    True,
                    SCPRunCmd,
                ),
            )
        )
        scp_threads[-1].start()
        current_batch_size += 1
        if (
            prepped_node.enable_batching
            and current_batch_size == total_scp_batch_size
        ):
          WaitForBatchCompletion(scp_threads, exit_statuses)
          current_batch_size = 0
          scp_threads = []
      else:
        # Run on a single worker.
        AttemptRunWithRetries(
            'SCP',
            worker,
            exit_statuses,
            cmd,
            prepped_node.ssh_helper.env,
            None,
            False,
            SCPRunCmd,
        )

  if len(worker_ips) > 1 and scp_threads:
    WaitForBatchCompletion(scp_threads, exit_statuses)
