# -*- coding: utf-8 -*- #
# Copyright 2022 Google LLC. All Rights Reserved.
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
"""Utils for running gcloud command and kubectl command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import contextlib
import fnmatch
import io
import json
import os
import re
import signal

from googlecloudsdk.api_lib.container import util
from googlecloudsdk.command_lib.anthos.config.sync.common import exceptions
from googlecloudsdk.core import execution_utils
from googlecloudsdk.core import log
from googlecloudsdk.core.util import files

_KUBECONFIGENV = 'KUBECONFIG'
_DEFAULTKUBECONFIG = 'config_sync'
_KUBECTL_TIMEOUT = 20


def GetObjectKey(obj):
  """Return the Object Key containing namespace and name."""
  namespace = obj['metadata'].get('namespace', '')
  name = obj['metadata']['name']
  return namespace, name


def MembershipMatched(membership, target_membership):
  """Check if the current membership matches the specified memberships.

  Args:
    membership: string The current membership.
    target_membership: string The specified memberships.

  Returns:
    Returns True if matching; False otherwise.
  """
  if not target_membership:
    return True

  if target_membership and '*' in target_membership:
    return fnmatch.fnmatch(membership, target_membership)
  else:
    members = target_membership.split(',')
    for m in members:
      if m == membership:
        return True
    return False


def GetConfigManagement(membership):
  """Get ConfigManagement to check if multi-repo is enabled.

  Args:
    membership: The membership name or cluster name of the current cluster.

  Raises:
    Error: errors that happen when getting the object from the cluster.
  """
  config_management = None
  err = None
  timed_out = True
  with Timeout(_KUBECTL_TIMEOUT):
    config_management, err = RunKubectl([
        'get', 'configmanagements.configmanagement.gke.io/config-management',
        '-o', 'json'
    ])
    timed_out = False
  if timed_out:
    if IsConnectGatewayContext():
      raise exceptions.ConfigSyncError(
          'Timed out getting ConfigManagement object. ' +
          'Make sure you have setup Connect Gateway for ' + membership +
          ' following the instruction from ' +
          'https://cloud.google.com/anthos/multicluster-management/gateway/setup'
      )
    else:
      raise exceptions.ConfigSyncError(
          'Timed out getting ConfigManagement object from ' + membership)

  if err:
    raise exceptions.ConfigSyncError(
        'Error getting ConfigManagement object from {}: {}\n'.format(
            membership, err))
  config_management_obj = json.loads(config_management)
  if 'enableMultiRepo' not in config_management_obj['spec'] or (
      not config_management_obj['spec']['enableMultiRepo']):
    raise exceptions.ConfigSyncError(
        'Legacy mode is used in {}. '.format(membership) +
        'Please enable the multi-repo feature to use this command.')
  if 'status' not in config_management_obj:
    log.status.Print('The ConfigManagement object is not reconciled in {}. '
                     .format(membership) +
                     'Please check if the Config Management is running on it.')
  errors = config_management_obj.get('status', {}).get('errors')
  if errors:
    log.status.Print(
        'The ConfigManagement object contains errors in{}:\n{}'.format(
            membership, errors))


def KubeconfigForMembership(project, membership):
  """Get the kubeconfig of a membership.

  If the kubeconfig for the membership already exists locally, use it;
  Otherwise run a gcloud command to get the credential for it.

  Args:
    project: The project ID of the membership.
    membership: The name of the membership.

  Returns:
    None

  Raises:
      Error: The error occured when it failed to get credential for the
      membership.
  """
  context = 'connectgateway_{project}_{membership}'.format(
      project=project, membership=membership)
  command = ['config', 'use-context', context]
  _, err = RunKubectl(command)
  if err is None:
    return

  # kubeconfig for the membership doesn't exit locally
  # run a gcloud command to get the credential of the given
  # membership

  # Check if the membership is for a GKE cluster.
  # If it is, use the kubeconfig for the GKE cluster.
  args = [
      'container', 'fleet', 'memberships', 'describe', membership, '--project',
      project, '--format', 'json'
  ]
  output, err = _RunGcloud(args)
  if err:
    raise exceptions.ConfigSyncError(
        'Error describing the membership {}: {}'.format(membership, err))
  if output:
    description = json.loads(output)
    cluster_link = description.get('endpoint',
                                   {}).get('gkeCluster',
                                           {}).get('resourceLink', '')
    if cluster_link:
      m = re.compile('.*/projects/(.*)/locations/(.*)/clusters/(.*)').match(
          cluster_link)
      project = ''
      location = ''
      cluster = ''
      try:
        project = m.group(1)
        location = m.group(2)
        cluster = m.group(3)
      except IndexError:
        pass
      if project and location and cluster:
        KubeconfigForCluster(project, location, cluster)
        return

  args = [
      'container', 'fleet', 'memberships', 'get-credentials', membership,
      '--project', project
  ]
  _, err = _RunGcloud(args)
  if err:
    raise exceptions.ConfigSyncError(
        'Error getting credential for membership {}: {}'.format(
            membership, err))


def KubeconfigForCluster(project, region, cluster):
  """Get the kubeconfig of a GKE cluster.

  If the kubeconfig for the GKE cluster already exists locally, use it;
  Otherwise run a gcloud command to get the credential for it.

  Args:
    project: The project ID of the cluster.
    region: The region of the cluster.
    cluster: The name of the cluster.

  Returns:
    None

  Raises:
    Error: The error occured when it failed to get credential for the cluster.
  """
  context = 'gke_{project}_{region}_{cluster}'.format(
      project=project, region=region, cluster=cluster)
  command = ['config', 'use-context', context]
  _, err = RunKubectl(command)
  if err is None:
    return None
  # kubeconfig for the cluster doesn't exit locally
  # run a gcloud command to get the credential of the given
  # cluster
  args = [
      'container', 'clusters', 'get-credentials', cluster, '--region', region,
      '--project', project
  ]
  _, err = _RunGcloud(args)
  if err:
    raise exceptions.ConfigSyncError(
        'Error getting credential for cluster {}: {}'.format(cluster, err))


def ListConfigControllerClusters(project):
  """Runs a gcloud command to list the clusters that host Config Controller.

  Currently the Config Controller only works in select regions.
  Refer to the Config Controller doc:
  https://cloud.google.com/anthos-config-management/docs/how-to/config-controller-setup

  Args:
    project: project that the Config Controller is in.

  Returns:
    The list of (cluster, region) for Config Controllers.

  Raises:
    Error: The error occured when it failed to list clusters.
  """
  # TODO(b/202418506) Check if there is any library
  # function to list the clusters.
  args = [
      'container', 'clusters', 'list', '--project', project, '--filter',
      'name:krmapihost', '--format', 'json(name,location)'
  ]
  output, err = _RunGcloud(args)
  if err:
    raise exceptions.ConfigSyncError('Error listing clusters: {}'.format(err))

  output_json = json.loads(output)
  clusters = [(c['name'], c['location']) for c in output_json]
  return clusters


def ListMemberships(project):
  """List hte memberships from a given project.

  Args:
    project: project that the memberships are in.

  Returns:
    The memberships registered to the fleet hosted by the given project.

  Raises:
    Error: The error occured when it failed to list memberships.
  """
  # TODO(b/202418506) Check if there is any library
  # function to list the memberships.
  args = [
      'container', 'fleet', 'memberships', 'list', '--format', 'json(name)',
      '--project', project
  ]
  output, err = _RunGcloud(args)
  if err:
    raise exceptions.ConfigSyncError(
        'Error listing memberships: {}'.format(err))
  json_output = json.loads(output)
  memberships = [m['name'] for m in json_output]
  return memberships


def RunKubectl(args):
  """Runs a kubectl command with the cluster referenced by this client.

  Args:
    args: command line arguments to pass to kubectl

  Returns:
    The contents of stdout if the return code is 0, stderr (or a fabricated
    error if stderr is empty) otherwise
  """
  cmd = [util.CheckKubectlInstalled()]
  cmd.extend(args)
  out = io.StringIO()
  err = io.StringIO()
  env = _GetEnvs()
  returncode = execution_utils.Exec(
      cmd,
      no_exit=True,
      out_func=out.write,
      err_func=err.write,
      in_str=None,
      env=env)

  if returncode != 0 and not err.getvalue():
    err.write('kubectl exited with return code {}'.format(returncode))

  return out.getvalue() if returncode == 0 else None, err.getvalue(
  ) if returncode != 0 else None


def _RunGcloud(args):
  """Runs a gcloud command.

  Args:
    args: command line arguments to pass to gcloud

  Returns:
    The contents of stdout if the return code is 0, stderr (or a fabricated
    error if stderr is empty) otherwise
  """
  cmd = execution_utils.ArgsForGcloud()
  cmd.extend(args)
  out = io.StringIO()
  err = io.StringIO()
  env = _GetEnvs()
  returncode = execution_utils.Exec(
      cmd,
      no_exit=True,
      out_func=out.write,
      err_func=err.write,
      in_str=None,
      env=env)

  if returncode != 0 and not err.getvalue():
    err.write('gcloud exited with return code {}'.format(returncode))
  return out.getvalue() if returncode == 0 else None, err.getvalue(
  ) if returncode != 0 else None


def _GetEnvs():
  """Get the environment variables that should be passed to kubectl/gcloud commands.

  Returns:
    The dictionary that includes the environment varialbes.
  """
  env = dict(os.environ)
  if _KUBECONFIGENV not in env:
    env[_KUBECONFIGENV] = files.ExpandHomeDir(
        os.path.join('~', '.kube', _DEFAULTKUBECONFIG))
  return env


@contextlib.contextmanager
def Timeout(time):
  """set timeout for a python function."""
  # Register a function to raise a TimeoutError on the signal.
  signal.signal(signal.SIGALRM, RaiseTimeout)
  # Schedule the signal to be sent after ``time``
  signal.alarm(time)

  try:
    yield
  except KubectlTimeOutError:
    pass
  finally:
    # Unregister the signal so it won't be triggered
    # if the timeout is not reached.
    signal.signal(signal.SIGALRM, signal.SIG_IGN)


def RaiseTimeout(signum, frame):
  """Raise a timeout error."""
  raise KubectlTimeOutError


class KubectlTimeOutError(Exception):
  pass


def GetActuationCondition(resource_status):
  """Produces a reconciliation condition based on actuation/strategy fields.

    These fields are only present in Config Sync 1.11+.

  Args:
    resource_status (dict): Managed resource status object.

  Returns:
    Condition dict or None.
  """
  actuation = resource_status.get('actuation')
  strategy = resource_status.get('strategy')
  if not actuation or not strategy:
    return None
  statuses_to_report = ['pending', 'skipped', 'failed']
  if str(actuation).lower() in statuses_to_report:
    return {
        'message': 'Resource pending {}'.format(strategy),
    }
  return None


def IsConnectGatewayContext():
  """Checks to see if the current kubeconfig context points to a Connect Gateway cluster.

  Returns:
    Boolean indicating if the cluster is using Connect Gateway or not.
  """
  # Get the current context name
  args = ['config', 'current-context']
  context, err = RunKubectl(args)
  if err:
    raise exceptions.ConfigSyncError('Error getting kubeconfig context')

  # Get the server address linked to the current context
  json_path = 'jsonpath={{.clusters[?(@.name=="{ctx}")].cluster.server}}'.format(
      ctx=context.strip())
  args = ['config', 'view', '-o', json_path]
  cgw, err = RunKubectl(args)
  if err:
    raise exceptions.ConfigSyncError(
        'Error getting kubeconfig context server address')

  # Determine if the server url contains connectgateway in its address,
  # eg. https://connectgateway.googleapis.com
  return 'connectgateway' in cgw
