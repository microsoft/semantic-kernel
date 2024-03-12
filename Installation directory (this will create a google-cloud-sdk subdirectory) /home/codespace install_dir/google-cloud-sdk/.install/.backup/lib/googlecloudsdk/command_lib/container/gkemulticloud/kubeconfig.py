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
"""Utilities for generating kubeconfig entries."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import base64
import os
import subprocess

from googlecloudsdk.api_lib.container import kubeconfig as kubeconfig_util
from googlecloudsdk.api_lib.container import util
from googlecloudsdk.command_lib.container.fleet import connect_gateway_util
from googlecloudsdk.command_lib.container.fleet import gwkubeconfig_util
from googlecloudsdk.command_lib.container.gkemulticloud import errors
from googlecloudsdk.core import config
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core.util import platforms
from googlecloudsdk.core.util import semver

COMMAND_DESCRIPTION = """
Fetch credentials for a running {cluster_type}.

This command updates a kubeconfig file with appropriate credentials and
endpoint information to point kubectl at a specific {cluster_type}.

By default, credentials are written to ``HOME/.kube/config''.
You can provide an alternate path by setting the ``KUBECONFIG'' environment
variable. If ``KUBECONFIG'' contains multiple paths, the first one is used.

This command enables switching to a specific cluster, when working
with multiple clusters. It can also be used to access a previously created
cluster from a new workstation.

By default, the command will configure kubectl to automatically refresh its
credentials using the same identity as the gcloud command-line tool.
If you are running kubectl as part of an application, it is recommended to use
[application default credentials](https://cloud.google.com/docs/authentication/production).
To configure a kubeconfig file to use application default credentials, set
the ``container/use_application_default_credentials''
[Google Cloud CLI property](https://cloud.google.com/sdk/docs/properties) to
``true'' before running the command.

See [](https://cloud.google.com/kubernetes-engine/docs/kubectl) for
kubectl documentation.
"""

COMMAND_EXAMPLE = """
To get credentials of a cluster named ``my-cluster'' managed in location ``us-west1'',
run:

$ {command} my-cluster --location=us-west1
"""

NOT_RUNNING_MSG = """\
Cluster {} is not RUNNING. The Kubernetes API may or may not be available. \
Check the cluster status for more information."""

STILL_PROVISIONING_MSG = 'Is it still PROVISIONING?'


def GenerateContext(kind, project_id, location, cluster_id):
  """Generates a kubeconfig context for an Anthos Multi-Cloud cluster.

  Args:
    kind: str, kind of the cluster e.g. aws, azure.
    project_id: str, project ID accociated with the cluster.
    location: str, Google location of the cluster.
    cluster_id: str, ID of the cluster.

  Returns:
    The context for the kubeconfig entry.
  """
  template = 'gke_{kind}_{project_id}_{location}_{cluster_id}'
  return template.format(
      kind=kind, project_id=project_id, location=location, cluster_id=cluster_id
  )


def GenerateAuthProviderCmdArgs(kind, cluster_id, location, project):
  """Generates command arguments for kubeconfig's authorization provider.

  Args:
    kind: str, kind of the cluster e.g. aws, azure.
    cluster_id: str, ID of the cluster.
    location: str, Google location of the cluster.
    project: str, Google Cloud project of the cluster.

  Returns:
    The command arguments for kubeconfig's authorization provider.
  """
  template = (
      'container {kind} clusters print-access-token '
      '{cluster_id} --project={project} --location={location} '
      '--format=json --exec-credential'
  )
  return template.format(
      kind=kind, cluster_id=cluster_id, location=location, project=project
  )


def GenerateAttachedKubeConfig(cluster, cluster_id, context, cmd_path):
  """Generates a kubeconfig entry for an Anthos Multi-cloud attached cluster.

  Args:
    cluster: object, Anthos Multi-cloud cluster.
    cluster_id: str, the cluster ID.
    context: str, context for the kubeconfig entry.
    cmd_path: str, authentication provider command path.
  """
  kubeconfig = kubeconfig_util.Kubeconfig.Default()
  # Use the same key for context, cluster, and user.
  kubeconfig.contexts[context] = kubeconfig_util.Context(
      context, context, context
  )

  _CheckPreqs()
  _ConnectGatewayKubeconfig(kubeconfig, cluster, cluster_id, context, cmd_path)

  kubeconfig.SetCurrentContext(context)
  kubeconfig.SaveToFile()
  log.status.Print(
      'A new kubeconfig entry "{}" has been generated and set as the '
      'current context.'.format(context)
  )


def GenerateKubeconfig(
    cluster, cluster_id, context, cmd_path, cmd_args, private_ep=False
):
  """Generates a kubeconfig entry for an Anthos Multi-cloud cluster.

  Args:
    cluster: object, Anthos Multi-cloud cluster.
    cluster_id: str, the cluster ID.
    context: str, context for the kubeconfig entry.
    cmd_path: str, authentication provider command path.
    cmd_args: str, authentication provider command arguments.
    private_ep: bool, whether to use private VPC for authentication.

  Raises:
      Error: don't have the permission to open kubeconfig file.
  """
  kubeconfig = kubeconfig_util.Kubeconfig.Default()
  # Use the same key for context, cluster, and user.
  kubeconfig.contexts[context] = kubeconfig_util.Context(
      context, context, context
  )

  # Only default to use Connect Gateway for 1.21+.
  version = _GetSemver(cluster, cluster_id)
  if private_ep or version < semver.SemVer('1.21.0'):
    _CheckPreqs(private_endpoint=True)
    _PrivateVPCKubeconfig(
        kubeconfig, cluster, cluster_id, context, cmd_path, cmd_args
    )
  else:
    _CheckPreqs()
    _ConnectGatewayKubeconfig(
        kubeconfig, cluster, cluster_id, context, cmd_path
    )

  kubeconfig.SetCurrentContext(context)
  kubeconfig.SaveToFile()
  log.status.Print(
      'A new kubeconfig entry "{}" has been generated and set as the '
      'current context.'.format(context)
  )


def _CheckPreqs(private_endpoint=False):
  """Checks the prerequisites to run get-credentials commands."""
  util.CheckKubectlInstalled()
  if not private_endpoint:
    project_id = properties.VALUES.core.project.GetOrFail()
    connect_gateway_util.CheckGatewayApiEnablement(
        project_id, _GetConnectGatewayEndpoint()
    )


def _ConnectGatewayKubeconfig(
    kubeconfig, cluster, cluster_id, context, cmd_path
):
  """Generates the Connect Gateway kubeconfig entry.

  Args:
    kubeconfig: object, Kubeconfig object.
    cluster: object, Anthos Multi-cloud cluster.
    cluster_id: str, the cluster ID.
    context: str, context for the kubeconfig entry.
    cmd_path: str, authentication provider command path.

  Raises:
      errors.MissingClusterField: cluster is missing required fields.
  """
  if cluster.fleet is None or cluster.fleet.membership is None:
    raise errors.MissingClusterField(
        cluster_id, 'Fleet membership', STILL_PROVISIONING_MSG
    )
  server = 'https://{}/v1/{}'.format(
      _GetConnectGatewayEndpoint(), cluster.fleet.membership
  )
  user_kwargs = {'auth_provider': 'gcp', 'auth_provider_cmd_path': cmd_path}
  kubeconfig.users[context] = kubeconfig_util.User(context, **user_kwargs)
  kubeconfig.clusters[context] = gwkubeconfig_util.Cluster(context, server)


def _PrivateVPCKubeconfig(
    kubeconfig, cluster, cluster_id, context, cmd_path, cmd_args
):
  """Generates the kubeconfig entry to connect using private VPC.

  Args:
    kubeconfig: object, Kubeconfig object.
    cluster: object, Anthos Multi-cloud cluster.
    cluster_id: str, the cluster ID.
    context: str, context for the kubeconfig entry.
    cmd_path: str, authentication provider command path.
    cmd_args: str, authentication provider command arguments.
  """
  user = {}
  user['exec'] = _ExecAuthPlugin(cmd_path, cmd_args)
  kubeconfig.users[context] = {'name': context, 'user': user}

  cluster_kwargs = {}
  if cluster.clusterCaCertificate is None:
    log.warning('Cluster is missing certificate authority data.')
  else:
    cluster_kwargs['ca_data'] = _GetCaData(cluster.clusterCaCertificate)
  if cluster.endpoint is None:
    raise errors.MissingClusterField(
        cluster_id, 'endpoint', STILL_PROVISIONING_MSG
    )
  kubeconfig.clusters[context] = kubeconfig_util.Cluster(
      context, 'https://{}'.format(cluster.endpoint), **cluster_kwargs
  )


def ValidateClusterVersion(cluster, cluster_id):
  """Validates the cluster version.

  Args:
    cluster: object, Anthos Multi-cloud cluster.
    cluster_id: str, the cluster ID.

  Raises:
      UnsupportedClusterVersion: cluster version is not supported.
      MissingClusterField: expected cluster field is missing.
  """
  version = _GetSemver(cluster, cluster_id)
  if version < semver.SemVer('1.20.0'):
    raise errors.UnsupportedClusterVersion(
        'The command get-credentials is supported in cluster version 1.20 '
        'and newer. For older versions, use get-kubeconfig.'
    )


def _GetCaData(pem):
  # Field certificate-authority-data in kubeconfig
  # expects a base64 encoded string of a PEM.
  return base64.b64encode(pem.encode('utf-8')).decode('utf-8')


def _GetSemver(cluster, cluster_id):
  if cluster.controlPlane is None or cluster.controlPlane.version is None:
    raise errors.MissingClusterField(cluster_id, 'version')
  version = cluster.controlPlane.version
  # The dev version e.g. 1.21-next does not conform to semantic versioning.
  # Replace the -next suffix before parsing semver for version comparison.
  if version.endswith('-next'):
    v = version.replace('-next', '.0', 1)
    return semver.SemVer(v)
  return semver.SemVer(version)


def _GetConnectGatewayEndpoint():
  """Gets the corresponding Connect Gateway endpoint for Multicloud environment.

  http://g3doc/cloud/kubernetes/multicloud/g3doc/oneplatform/team/how-to/hub

  Returns:
    The Connect Gateway endpoint.

  Raises:
    Error: Unknown API override.
  """
  # TODO(b/196964566): Use per-region URL for Connect Gatway once GA e.g.
  # us-west1-connectgateway.googleapis.com.
  endpoint = properties.VALUES.api_endpoint_overrides.gkemulticloud.Get()
  # Multicloud overrides prod endpoint at run time with the regionalized version
  # so we can't simply check that endpoint is not overridden.
  if (
      endpoint is None
      or endpoint.endswith('gkemulticloud.googleapis.com/')
      or endpoint.endswith('preprod-gkemulticloud.sandbox.googleapis.com/')
  ):
    return 'connectgateway.googleapis.com'
  if 'staging-gkemulticloud' in endpoint:
    return 'staging-connectgateway.sandbox.googleapis.com'
  if endpoint.startswith('http://localhost') or endpoint.endswith(
      'gkemulticloud.sandbox.googleapis.com/'
  ):
    return 'autopush-connectgateway.sandbox.googleapis.com'
  raise errors.UnknownApiEndpointOverrideError('gkemulticloud')


def ExecCredential(expiration_timestamp=None, access_token=None):
  """Generates a Kubernetes execCredential object."""
  return {
      'kind': 'ExecCredential',
      'apiVersion': 'client.authentication.k8s.io/v1',
      'status': {
          'expirationTimestamp': expiration_timestamp,
          'token': access_token,
      },
  }


def _ExecAuthPlugin(cmd_path, cmd_args):
  """Generates and returns an exec auth plugin config.

  Args:
    cmd_path: str, exec command path.
    cmd_args: str, exec command arguments.

  Returns:
    dict, valid exec auth plugin config entry.
  """
  if cmd_path is None:
    bin_name = 'gcloud'
    if platforms.OperatingSystem.IsWindows():
      bin_name = 'gcloud.cmd'
    command = bin_name

    # Check if command is in PATH and executable. Else, print critical(RED)
    # warning as kubectl will break if command is not executable.
    try:
      subprocess.run(
          [command, '--version'],
          timeout=5,
          check=False,
          stdout=subprocess.DEVNULL,
          stderr=subprocess.DEVNULL,
      )
      cmd_path = command
    except Exception:  # pylint: disable=broad-except
      # Provide SDK Full path if command is not in PATH. This helps work
      # around scenarios where cloud-sdk install location is not in PATH
      # as sdk was installed using other distributions methods Eg: brew
      try:
        # config.Paths().sdk_bin_path throws an exception in some test envs,
        # but is commonly defined in prod environments
        sdk_bin_path = config.Paths().sdk_bin_path
        if sdk_bin_path is None:
          log.critical(kubeconfig_util.SDK_BIN_PATH_NOT_FOUND)
          raise kubeconfig_util.Error(kubeconfig_util.SDK_BIN_PATH_NOT_FOUND)
        else:
          sdk_path_bin_name = os.path.join(sdk_bin_path, command)
          subprocess.run(
              [sdk_path_bin_name, '--version'],
              timeout=5,
              check=False,
              stdout=subprocess.DEVNULL,
              stderr=subprocess.DEVNULL,
          )
          # update command if sdk_path_bin_name works
          cmd_path = sdk_path_bin_name
      except Exception:  # pylint: disable=broad-except
        log.critical(kubeconfig_util.SDK_BIN_PATH_NOT_FOUND)

  cfg = {
      'command': cmd_path,
      'apiVersion': 'client.authentication.k8s.io/v1',
      'provideClusterInfo': True,
      'args': cmd_args.split(' '),
      'interactiveMode': 'Never',
  }

  endpoint = properties.VALUES.api_endpoint_overrides.gkemulticloud.Get()
  if endpoint:
    cfg['env'] = [{
        'name': (
            properties.VALUES.api_endpoint_overrides.gkemulticloud.EnvironmentName()
        ),
        'value': endpoint,
    }]
  return cfg


def CheckClusterHasNodePools(cluster_client, cluster_ref):
  """Checks and gives a warning if the cluster does not have a node pool."""
  try:
    if not cluster_client.HasNodePools(cluster_ref):
      log.warning(
          'Cluster does not have a node pool. To use Connect Gateway, '
          'ensure you have at least one Linux node pool running.'
      )
  # pylint: disable=bare-except, this function is just a warning and should not
  # add new failures.
  except:
    pass


def ConnectGatewayInNodePools(cluster, cluster_id):
  version = _GetSemver(cluster, cluster_id)
  return version < semver.SemVer('1.25.0')
