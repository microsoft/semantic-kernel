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
"""Utility file that contains helpers for the Cloud TPU Execution groups."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import datetime
import os
import re
import sys
import time

from apitools.base.py import list_pager
from apitools.base.py.exceptions import HttpNotFoundError
from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute.operations import poller
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import scope as compute_scope
from googlecloudsdk.command_lib.compute import ssh_utils
from googlecloudsdk.command_lib.compute.instances import flags as instance_flags
from googlecloudsdk.command_lib.projects import util as p_util
from googlecloudsdk.command_lib.util.ssh import ssh
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources
from googlecloudsdk.core.util import retry
from googlecloudsdk.core.util import times
import six


class DefaultArgs(object):
  """Helper to check if required flags are set and sets defaults if not."""

  @staticmethod
  def ValidateName(args):
    """Validates the name arg and sets defaults if values are not set."""
    account = properties.VALUES.core.account.Get(required=True)
    if account.find('@') == -1:
      username = account
    else:
      username = account[0:account.find('@')]

    args.name = args.name or username

  @staticmethod
  def ValidateZone(args):
    """Validates the zone arg and sets defaults if values are not set."""
    args.zone = args.zone or properties.VALUES.compute.zone.Get(required=True)


class TPUNode(object):
  """Helper to create and modify TPU nodes."""

  def __init__(self, release_track):
    if release_track == base.ReleaseTrack.ALPHA:
      self._api_version = 'v1alpha1'
    else:
      self._api_version = 'v1'
    self.client = apis.GetClientInstance('tpu', self._api_version)
    self.messages = apis.GetMessagesModule('tpu', self._api_version)

  def _CreateDefaultNode(
      self, accelerator_type, tf_version, preemptible, network):
    node = self.messages.Node()
    node.acceleratorType = accelerator_type
    node.network = network
    node.tensorflowVersion = tf_version
    node.schedulingConfig = self.messages.SchedulingConfig(
        preemptible=preemptible)
    return node

  def _GetTpuOperationRef(self, operation):
    """Get a resource reference to a long running operation."""
    return resources.REGISTRY.ParseRelativeName(
        operation.name, collection='tpu.projects.locations.operations')

  def Create(
      self, name, accelerator_type, tf_version, zone, preemptible, network):
    """Create builds and issues a request to create a TPU node.

    Args:
      name: Name of the TPU Node to be created.
      accelerator_type: Slice type of TPU accelerator like 'v2-8', 'v2-32'.
      tf_version: Tensorflow Version like '1.1', '1.5'.
      zone: Zone to create the TPU Node in.
      preemptible: Boolean argument, to create a Preemptible node.
      network: The network to create the node in
    Returns:
      A TPU Create response which needs to be polled on.
    """
    project = properties.VALUES.core.project.Get(required=True)
    parent_ref = resources.REGISTRY.Parse(
        zone,
        params={'projectsId': project},
        collection='tpu.projects.locations')
    request = self.messages.TpuProjectsLocationsNodesCreateRequest(
        parent=parent_ref.RelativeName(),
        nodeId=name,
        node=self._CreateDefaultNode(
            accelerator_type, tf_version, preemptible, network))
    operation = self.client.projects_locations_nodes.Create(request)
    return self._GetTpuOperationRef(operation)

  def WaitForOperation(self, operation_ref, message):
    operation_poller = waiter.CloudOperationPoller(
        self.client.projects_locations_nodes,
        self.client.projects_locations_operations)
    return waiter.WaitFor(operation_poller, operation_ref, message)

  def WaitForOperationNoResources(self, operation_ref, message):
    operation_poller = waiter.CloudOperationPollerNoResources(
        self.client.projects_locations_operations)
    return waiter.WaitFor(operation_poller, operation_ref, message)

  def Delete(self, name, zone):
    """Deletes the TPU node with the given name."""
    project = properties.VALUES.core.project.Get(required=True)
    fully_qualified_node_name_ref = resources.REGISTRY.Parse(
        name,
        params={
            'locationsId': zone,
            'projectsId': project
        },
        collection='tpu.projects.locations.nodes',
        )
    request = self.messages.TpuProjectsLocationsNodesDeleteRequest(
        name=fully_qualified_node_name_ref.RelativeName())
    operation = self.client.projects_locations_nodes.Delete(request)
    return self._GetTpuOperationRef(operation)

  def List(self, zone):
    """Retrieves all TPU Nodes."""
    project = properties.VALUES.core.project.Get(required=True)
    parent_ref = resources.REGISTRY.Parse(
        zone,
        params={'projectsId': project},
        collection='tpu.projects.locations')
    request = self.messages.TpuProjectsLocationsNodesListRequest(
        parent=parent_ref.RelativeName())
    return list_pager.YieldFromList(
        service=self.client.projects_locations_nodes,
        request=request,
        method='List',
        batch_size_attribute='pageSize',
        field='nodes'
        )

  def Get(self, name, zone):
    """Retrieves the TPU node in the given zone."""
    project = properties.VALUES.core.project.Get(required=True)
    fully_qualified_node_name_ref = resources.REGISTRY.Parse(
        name,
        params={
            'locationsId': zone,
            'projectsId': project
        },
        collection='tpu.projects.locations.nodes',
        )
    request = self.messages.TpuProjectsLocationsNodesGetRequest(
        name=fully_qualified_node_name_ref.RelativeName())
    return self.client.projects_locations_nodes.Get(request)

  def LatestStableTensorflowVersion(self, zone):
    """Parses available Tensorflow versions to find the most stable version."""
    project = properties.VALUES.core.project.Get(required=True)
    parent_ref = resources.REGISTRY.Parse(
        zone,
        params={'projectsId': project},
        collection='tpu.projects.locations')
    request = self.messages.TpuProjectsLocationsTensorflowVersionsListRequest(
        parent=parent_ref.RelativeName()
        )
    tf_versions = list_pager.YieldFromList(
        service=self.client.projects_locations_tensorflowVersions,
        request=request,
        batch_size_attribute='pageSize',
        field='tensorflowVersions')
    parsed_tf_versions = []
    for tf_version in tf_versions:
      parsed_tf_versions.append(
          TensorflowVersionParser.ParseVersion(tf_version.version))

    sorted_tf_versions = sorted(parsed_tf_versions)
    for version in sorted_tf_versions:
      if version.is_nightly:
        raise HttpNotFoundError('No stable release found', None, None)

      if not version.modifier:
        return version.VersionString()

    raise HttpNotFoundError('No stable release found', None, None)

  def IsRunning(self, node):
    return node.state == self.messages.Node.StateValueValuesEnum.READY or (
        node.state == self.messages.Node.StateValueValuesEnum.CREATING and
        node.ipAddress)

  def NodeName(self, node):
    pattern = 'projects/(.*)/locations/(.*)/nodes/(.*)'
    match = re.search(pattern, node.name, re.IGNORECASE)
    if match:
      return match.group(3)
    return ''


class ComputePollerNoResources(poller.Poller):
  """Compute operations poller that does not create a resource."""

  def __init__(self, resource_service, target_ref=None):
    super(ComputePollerNoResources, self).__init__(
        resource_service=resource_service, target_ref=target_ref)

  def GetResult(self, operation):
    """Overrides."""
    return None


class TensorflowVersionParser(object):
  """Helper to parse tensorflow versions."""

  class ParseError(Exception):
    """Error raised with input is unabled to be parse as a TF version."""

  class Result(object):
    """Helper to capture result of parsing the TF version."""

    def __init__(self,
                 major=0,
                 minor=0,
                 patch=0,
                 is_nightly=False,
                 modifier=''):
      self.major = major
      self.minor = minor
      self.patch = patch
      self.is_nightly = is_nightly
      self.modifier = modifier

    def IsUnknown(self):
      return self.major == 0 and self.minor == 0 and not self.is_nightly

    def VersionString(self):
      if self.is_nightly:
        return 'nightly{}'.format(self.modifier)
      if self.major == 0 and self.minor == 0:
        return self.modifier
      return '{}.{}{}'.format(self.major, self.minor, self.modifier)

    def __hash__(self):
      return hash(self.major) + hash(self.minor) + hash(self.patch) + hash(
          self.is_nightly) + hash(self.modifier)

    def __eq__(self, other):
      return (self.major == other.major and
              self.minor == other.minor and
              self.patch == other.patch and
              self.is_nightly == other.is_nightly and
              self.modifier == other.modifier)

    def __lt__(self, other):
      # Both non-nightlies, non-unknowns
      if not self.is_nightly and not other.is_nightly and not self.IsUnknown(
      ) and not other.IsUnknown():
        if self.major != other.major:
          return self.major > other.major
        if self.minor != other.minor:
          return self.minor > other.minor
        if self.patch != other.patch:
          return self.patch > other.patch
        if not self.modifier:
          return True
        if not other.modifier:
          return False

      # Both nightlies
      if self.is_nightly and other.is_nightly:
        if not self.modifier:
          return True
        if not other.modifier:
          return False

      # Both unknown versions
      if self.IsUnknown() and other.IsUnknown():
        return self.modifier < other.modifier

      # If one is an unknown version, sort after
      if self.IsUnknown():
        return False
      if other.IsUnknown():
        return True

      if self.is_nightly:
        return False

      return True

  _VERSION_REGEX = re.compile('^(\\d+)\\.(\\d+)(.*)$')
  _NIGHTLY_REGEX = re.compile('^nightly(.*)$')
  _PATCH_NUMBER_REGEX = re.compile('^\\.(\\d+)$')

  @staticmethod
  def ParseVersion(tf_version):
    """Helper to parse the tensorflow version into it's subcomponents."""
    if not tf_version:
      raise TensorflowVersionParser.ParseError('Bad argument: '
                                               'tf_version is empty')

    version_match = TensorflowVersionParser._VERSION_REGEX.match(tf_version)
    nightly_match = TensorflowVersionParser._NIGHTLY_REGEX.match(tf_version)

    if version_match is None and nightly_match is None:
      return TensorflowVersionParser.Result(modifier=tf_version)

    if version_match is not None and nightly_match is not None:
      raise TensorflowVersionParser.ParseError(
          'TF version error: bad version: {}'.format(tf_version))
    if version_match:
      major = int(version_match.group(1))
      minor = int(version_match.group(2))
      result = TensorflowVersionParser.Result(major=major, minor=minor)
      if version_match.group(3):
        patch_match = TensorflowVersionParser._PATCH_NUMBER_REGEX.match(
            version_match.group(3))
        if patch_match:
          matched_patch = int(patch_match.group(1))
          if matched_patch:
            result.patch = matched_patch
        else:
          result.modifier = version_match.group(3)
      return result

    if nightly_match:
      result = TensorflowVersionParser.Result(is_nightly=True)
      if nightly_match.group(1):
        result.modifier = nightly_match.group(1)
      return result


class Instance(object):
  """Helper to create the GCE VM required to work with the TPU Node."""

  def __init__(self, release_track):
    holder = base_classes.ComputeApiHolder(release_track)
    self.client = holder.client.apitools_client
    self.messages = holder.client.messages

  def _ImageFamilyFromTensorflowVersion(self, tf_version, use_dl_image):
    """Generates the image family from the tensorflow version."""
    if tf_version == 'nightly':
      return 'tf-nightly'

    parsed = TensorflowVersionParser.ParseVersion(tf_version)

    if parsed.modifier:
      raise TensorflowVersionParser.ParseError('Invalid tensorflow version:{} '
                                               '(non-empty modifier); please '
                                               'set the --gce-image '
                                               'flag'.format(tf_version))

    if use_dl_image:
      if parsed.major == 2:
        return 'tf2-{}-{}-cpu'.format(parsed.major, parsed.minor)
      else:
        return 'tf-{}-{}-cpu'.format(parsed.major, parsed.minor)

    # From TF 2.4, image family format uses patch format by default,
    # e.g.: `tf-2-4-0` for TF version 2.4
    if parsed.patch or (parsed.major >= 2 and parsed.minor >= 4):
      return 'tf-{}-{}-{}'.format(parsed.major, parsed.minor, parsed.patch)

    return 'tf-{}-{}'.format(parsed.major, parsed.minor)

  def ResolveImageFromTensorflowVersion(self, tf_version, use_dl_image):
    """Queries GCE to find the right image for the given TF version."""
    project = 'ml-images'
    if use_dl_image:
      project = 'deeplearning-platform-release'

    image_family = self._ImageFamilyFromTensorflowVersion(
        tf_version, use_dl_image)
    request = self.messages.ComputeImagesGetFromFamilyRequest(
        family=image_family, project=project)
    image = self.client.images.GetFromFamily(request)
    return image and image.selfLink

  def BuildInstanceSpec(self,
                        name,
                        zone,
                        machine_type,
                        disk_size,
                        preemptible,
                        network,
                        use_with_notebook,
                        source_image=None):
    """Builds an instance spec to be used for Instance creation."""

    disk = self.messages.AttachedDisk(
        boot=True,
        autoDelete=True,
        initializeParams=self.messages.AttachedDiskInitializeParams(
            sourceImage=source_image,
            diskSizeGb=disk_size
        ))
    project_number = p_util.GetProjectNumber(
        properties.VALUES.core.project.Get(required=True))
    network_interface = self.messages.NetworkInterface(
        network='projects/{}/global/networks/{}'.format(
            project_number, network),
        accessConfigs=[self.messages.AccessConfig(
            name='External NAT',
            type=self.messages.AccessConfig.TypeValueValuesEnum.ONE_TO_ONE_NAT)]
        )
    metadata = [self.messages.Metadata.ItemsValueListEntry(
        key='ctpu',
        value=name)]

    if use_with_notebook:
      metadata.append(
          self.messages.Metadata.ItemsValueListEntry(
              key='proxy-mode', value='project_editors'))

    service_account = self.messages.ServiceAccount(
        email='default',
        scopes=[
            'https://www.googleapis.com/auth/devstorage.read_write',
            'https://www.googleapis.com/auth/logging.write',
            'https://www.googleapis.com/auth/monitoring.write',
            'https://www.googleapis.com/auth/cloud-platform'
        ])
    labels = self.messages.Instance.LabelsValue(additionalProperties=[
        self.messages.Instance.LabelsValue.AdditionalProperty(
            key='ctpu', value=name)
    ])

    return self.messages.Instance(
        name=name,
        metadata=self.messages.Metadata(items=metadata),
        machineType='zones/{}/machineTypes/{}'.format(zone, machine_type),
        disks=[disk],
        scheduling=self.messages.Scheduling(preemptible=preemptible),
        networkInterfaces=[network_interface],
        labels=labels,
        serviceAccounts=[service_account])

  def _GetComputeZoneOperationRef(self, operation):
    """Get a resource reference to a long running operation."""
    return resources.REGISTRY.Parse(
        operation.selfLink, collection='compute.zoneOperations')

  def Create(self, name, zone, machine_type, disk_size, preemptible, gce_image,
             network, use_with_notebook):
    """Issue request to create an Instance."""
    request = self.messages.ComputeInstancesInsertRequest(
        project=properties.VALUES.core.project.Get(required=True),
        zone=zone,
        instance=self.BuildInstanceSpec(
            name, zone, machine_type, disk_size, preemptible, network,
            use_with_notebook, gce_image))
    operation = self.client.instances.Insert(request)
    return self._GetComputeZoneOperationRef(operation)

  def Stop(self, name, zone):
    """Issue request to stop the Instance."""
    project = properties.VALUES.core.project.Get(required=True)
    request = self.messages.ComputeInstancesStopRequest(
        instance=name,
        project=project,
        zone=zone
        )
    operation = self.client.instances.Stop(request)
    return self._GetComputeZoneOperationRef(operation)

  def Start(self, name, zone):
    """Issue request to start the Instance."""
    project = properties.VALUES.core.project.Get(required=True)
    request = self.messages.ComputeInstancesStartRequest(
        instance=name,
        project=project,
        zone=zone
        )
    operation = self.client.instances.Start(request)
    return self._GetComputeZoneOperationRef(operation)

  def WaitForOperation(self, operation_ref, message):
    """Wait for Instance operation to complete."""
    operation_poller = poller.Poller(self.client.instances)
    return waiter.WaitFor(operation_poller, operation_ref, message)

  def WaitForOperationNoResources(self, operation_ref, message):
    operation_poller = ComputePollerNoResources(self.client.instances)
    return waiter.WaitFor(operation_poller, operation_ref, message)

  def List(self, zone):
    """Retrieves all Instances created by Execution Group."""
    project = properties.VALUES.core.project.Get(required=True)
    request = self.messages.ComputeInstancesListRequest(
        zone=zone, project=project)
    instances = list_pager.YieldFromList(
        service=self.client.instances,
        request=request,
        method='List',
        field='items')

    result_set = []
    for instance in instances:
      if self._VMCreatedByExecGroup(instance):
        result_set.append(instance)

    return result_set

  def Get(self, instance_name, zone):
    """Retrieves the Instance data."""
    project = properties.VALUES.core.project.Get(required=True)
    request = self.messages.ComputeInstancesGetRequest(
        zone=zone, project=project, instance=instance_name)
    instance = self.client.instances.Get(request)
    if self._VMCreatedByExecGroup(instance):
      return instance
    raise HttpNotFoundError(
        'Instance:{} not found'.format(instance_name), None, None)

  def _VMCreatedByExecGroup(self, instance):
    if instance and instance.labels:
      for label in instance.labels.additionalProperties:
        if label.key == 'ctpu':
          return True
    return False

  def IsRunning(self, instance):
    return instance.status == self.messages.Instance.StatusValueValuesEnum.RUNNING

  def Delete(self, name, zone):
    """Deletes the specified instance in the given zone and project."""
    request = self.messages.ComputeInstancesDeleteRequest(
        project=properties.VALUES.core.project.Get(required=True),
        zone=zone,
        instance=name
        )
    operation = self.client.instances.Delete(request)
    return self._GetComputeZoneOperationRef(operation)


class SSH(object):
  """Helper class to SSH to the VM associated with the TPU node."""

  def __init__(self, release_track):
    holder = base_classes.ComputeApiHolder(release_track)
    self.release_track = release_track
    self.client = holder.client
    self.resources = holder.resources

  def _DefaultArgsForSSH(self, args):
    # These arguments are not exposed to the user but are required in
    # order to use the SSH Utils.
    args.plain = None
    args.strict_host_key_checking = 'no'
    args.force_key_file_overwrite = None
    args.ssh_key_file = None
    return args

  def _GetHostKeyFromInstance(self, zone, ssh_helper, instance):
    """Wrapper around SSH Utils to get the host keys for SSH."""
    instance_ref = instance_flags.SSH_INSTANCE_RESOLVER.ResolveResources(
        [instance.name], compute_scope.ScopeEnum.ZONE, zone,
        self.resources,
        scope_lister=instance_flags.GetInstanceZoneScopeLister(self.client))[0]
    project = ssh_helper.GetProject(self.client, instance_ref.project)
    host_keys = ssh_helper.GetHostKeysFromGuestAttributes(
        self.client, instance_ref, instance, project)

    if host_keys is not None and not host_keys:
      # Only display this message if there was an attempt to retrieve
      # host keys but it was unsuccessful(yielded empty dict). If Guest
      # Attributes is disabled, there is no attempt to retrieve host keys.
      log.status.Print('Unable to retrieve host keys from instance metadata. '
                       'Continuing.')
    return host_keys

  def _GetSSHOptions(self, name, ssh_helper, instance, host_keys):
    options = ssh_helper.GetConfig(ssh_utils.HostKeyAlias(instance),
                                   strict_host_key_checking='no',
                                   host_keys_to_add=host_keys)
    os.environ['TPU_NAME'] = name
    options['SendEnv'] = 'TPU_NAME'
    return options

  def _WaitForSSHKeysToPropagate(
      self, ssh_helper, remote, identity_file, user, instance, options,
      putty_force_connect=False):
    """Waits for SSH keys to propagate in order to SSH to the instance."""
    ssh_helper.EnsureSSHKeyExists(
        self.client, user, instance,
        ssh_helper.GetProject(
            self.client, properties.VALUES.core.project.Get(required=True)),
        times.Now() + datetime.timedelta(seconds=300))
    ssh_poller = ssh.SSHPoller(
        remote=remote,
        identity_file=identity_file, options=options, max_wait_ms=300*1000)
    try:
      ssh_poller.Poll(
          ssh_helper.env,
          putty_force_connect=putty_force_connect)
    except retry.WaitException:
      raise ssh_utils.NetworkError()

  def SSHToInstance(self, args, instance):
    """Helper to manage authentication followed by SSH to the instance."""
    args = self._DefaultArgsForSSH(args)

    external_nat = ssh_utils.GetExternalIPAddress(instance)
    log.status.Print(
        'Trying to SSH to VM with NAT IP:{}'.format(external_nat))
    args.ssh_key_file = ssh.Keys.DEFAULT_KEY_FILE

    ssh_helper = ssh_utils.BaseSSHCLIHelper()
    ssh_helper.Run(args)
    identity_file = ssh_helper.keys.key_file

    user, _ = ssh_utils.GetUserAndInstance(args.name)
    host_keys = self._GetHostKeyFromInstance(args.zone, ssh_helper, instance)
    options = self._GetSSHOptions(args.name, ssh_helper,
                                  instance, host_keys)

    public_key = ssh_helper.keys.GetPublicKey().ToEntry(include_comment=True)
    oslogin_state = ssh.GetOsloginState(
        instance,
        ssh_helper.GetProject(
            self.client, properties.VALUES.core.project.Get(required=True)),
        user,
        public_key,
        None,
        self.release_track,
        username_requested=False,
        messages=self.client.messages)
    user = oslogin_state.user
    remote = ssh.Remote(external_nat, user)
    # TODO(b/35355795): Don't force connect in general.
    # At a minimum, avoid injecting 'y' if PuTTY will prompt for a 2FA
    # authentication method (since we know that won't work), or if the user has
    # disabled the property.
    putty_force_connect = (
        not oslogin_state.oslogin_2fa_enabled and
        properties.VALUES.ssh.putty_force_connect.GetBool())

    if not oslogin_state.oslogin_enabled:
      self._WaitForSSHKeysToPropagate(ssh_helper, remote, identity_file, user,
                                      instance, options, putty_force_connect)

    extra_flags = []
    # Ctpu seems to be forwarding some other ports on what
    # seems like the TPU node. Need to understand better before enabling.
    if args.forward_ports:
      extra_flags.extend(
          ['-A', '-L', '6006:localhost:6006', '-L', '8888:localhost:8888'])
    ssh_cmd_args = {
        'remote': remote,
        'identity_file': identity_file,
        'options': options,
        'extra_flags': extra_flags
    }

    cmd = ssh.SSHCommand(**ssh_cmd_args)
    max_attempts = 10
    sleep_interval = 30
    # Since the instance was just created, it can take a while for the instance
    # to be ready to accept ssh connections, therefore retry up to 5m. Doesn't
    # need to be backed off, regular interval retry is sufficient since we
    # aren't looking to throttle.
    for i in range(max_attempts):
      try:
        log.status.Print('SSH Attempt #{}...'.format(i))
        # Errors from SSH itself result in an ssh.CommandError being raised
        return_code = cmd.Run(
            ssh_helper.env,
            putty_force_connect=putty_force_connect)
        if return_code:
          # This is the return code of the remote command.
          # Problems with SSH itself will result in ssh.CommandError
          # being raised above.
          sys.exit(return_code)
      except ssh.CommandError as e:
        if i == max_attempts - 1:
          raise e
        log.status.Print(
            'Retrying: SSH command error: {}'.format(six.text_type(e)))
        time.sleep(sleep_interval)
        continue
      break


class ResourceManager(object):
  """Helper to interact with Cloud Resource Manager and related ACLs."""

  logging_role = 'roles/logging.logWriter'
  storage_role = 'roles/storage.admin'  # Note storage.objectAdmin does not work
  # in certain cases, and thus we need
  # roles/storage.admin.
  tpu_service_agent = 'roles/tpu.serviceAgent'

  def __init__(self):
    self._api_version = 'v1'
    self.client = apis.GetClientInstance(
        'cloudresourcemanager', self._api_version)
    self.messages = apis.GetMessagesModule(
        'cloudresourcemanager', self._api_version)

  def AddTpuUserAgent(self, tpu_user_agent):
    """AddTPUUserAgent adds the TPU user agent to enable Cloud Storage access and send logging."""
    project = properties.VALUES.core.project.Get(required=True)
    get_iam_policy_request = self.messages.CloudresourcemanagerProjectsGetIamPolicyRequest(
        resource=project)
    policy = self.client.projects.GetIamPolicy(get_iam_policy_request)
    policy = self._AddAgentToPolicy(policy, tpu_user_agent)
    if policy is None:
      log.status.Print('TPU Service account:{} has already been enabled'
                       .format(tpu_user_agent))
    else:
      set_iam_policy_request = self.messages.CloudresourcemanagerProjectsSetIamPolicyRequest(
          resource=project,
          setIamPolicyRequest=self.messages.SetIamPolicyRequest(
              policy=policy
              ))
      self.client.projects.SetIamPolicy(set_iam_policy_request)
      log.status.Print(
          'Added Storage and Logging permissions to TPU Service Account:{}'
          .format(tpu_user_agent))

  def _AddAgentToPolicy(self, policy, tpu_user_agent):
    """Adds the tpuUserAgent to the policy and return it."""
    logging_binding = None
    storage_binding = None
    tpu_member_str = 'serviceAccount:{}'.format(tpu_user_agent)

    for binding in policy.bindings:
      if binding.role == self.logging_role:
        logging_binding = binding
      if binding.role == self.storage_role:
        storage_binding = binding

      # Skip checking bindings if this is the tpuServiceAgent role.
      if binding.role != self.tpu_service_agent:
        # Check if the tpuMemberStr is already in a binding.
        for member in binding.members:
          if member == tpu_member_str:
            # The TPU service account has already been enabled. Make no
            # modifications.
            return None

    if logging_binding is None:
      logging_binding = self.messages.Binding(role=self.logging_role)
      policy.bindings.append(logging_binding)

    if storage_binding is None:
      storage_binding = self.messages.Binding(role=self.storage_role)
      policy.bindings.append(storage_binding)

    logging_binding.members.append(tpu_member_str)
    storage_binding.members.append(tpu_member_str)

    return policy
