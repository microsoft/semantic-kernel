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
"""Utils for Kubernetes Operations for GKE Hub commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import io
import json
import os
import re

from googlecloudsdk.api_lib.container import api_adapter as gke_api_adapter
from googlecloudsdk.api_lib.container import kubeconfig as kconfig
from googlecloudsdk.api_lib.container import util as c_util
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.calliope import exceptions as calliope_exceptions
from googlecloudsdk.command_lib.container.fleet import format_util
from googlecloudsdk.command_lib.container.fleet.memberships import gke_util
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import execution_utils
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core import requests
from googlecloudsdk.core.util import encoding
from googlecloudsdk.core.util import files
from kubernetes import client as kube_client_lib
from kubernetes import config as kube_client_config
from six.moves.urllib.parse import urljoin

# import urljoin in a Python 2 and 3 compatible way
NAMESPACE_DELETION_INITIAL_WAIT_MS = 0
NAMESPACE_DELETION_TIMEOUT_MS = 1000 * 60 * 2
NAMESPACE_DELETION_MAX_POLL_INTERVAL_MS = 1000 * 15
NAMESPACE_DELETION_INITIAL_POLL_INTERVAL_MS = 1000 * 5


class RBACError(exceptions.Error):
  """Class for errors raised by GKE Hub commands."""


class KubectlError(exceptions.Error):
  """Class for errors raised when shelling out to kubectl."""


def GetClusterUUID(kube_client):
  """Gets the UUID of the kube-system namespace.

  Args:
    kube_client: A KubernetesClient.

  Returns:
    the namespace UID

  Raises:
    exceptions.Error: If the UID cannot be acquired.
    calliope_exceptions.MinimumArgumentException: if a kubeconfig file cannot be
      deduced from the command line flags or environment
  """
  return kube_client.GetNamespaceUID('kube-system')


def GetClusterServerVersion(kube_client):
  """Gets the UUID of the kube-system namespace.

  Args:
    kube_client: A KubernetesClient.

  Returns:
    the cluster server version

  Raises:
    exceptions.Error: If the cluster server version cannot be acquired.
    calliope_exceptions.MinimumArgumentException: if a kubeconfig file cannot be
      deduced from the command line flags or environment
  """
  return kube_client.GetServerVersion()


def DeleteNamespace(kube_client, namespace):
  """Delete a namespace from the cluster.

  Args:
    kube_client: The KubernetesClient towards the cluster.
    namespace: the namespace of connect agent deployment.

  Raises:
    exceptions.Error: if failed to delete the namespace.
  """
  if kube_client.NamespaceExists(namespace):
    try:
      succeeded, error = waiter.WaitFor(
          KubernetesPoller(),
          NamespaceDeleteOperation(namespace, kube_client),
          'Deleting namespace [{}] in the cluster'.format(namespace),
          pre_start_sleep_ms=NAMESPACE_DELETION_INITIAL_WAIT_MS,
          max_wait_ms=NAMESPACE_DELETION_TIMEOUT_MS,
          wait_ceiling_ms=NAMESPACE_DELETION_MAX_POLL_INTERVAL_MS,
          sleep_ms=NAMESPACE_DELETION_INITIAL_POLL_INTERVAL_MS,
      )
    except waiter.TimeoutError:
      # waiter.TimeoutError assumes that the operation is a Google API
      # operation, and prints a debugging string to that effect.
      raise exceptions.Error(
          'Could not delete namespace [{}] from cluster.'.format(namespace)
      )

    if not succeeded:
      raise exceptions.Error(
          'Could not delete namespace [{}] from cluster. Error: {}'.format(
              namespace, error
          )
      )


class MembershipCRDCreationOperation(object):
  """An operation that waits for a membership CRD to be created."""

  CREATED_KEYWORD = 'unchanged'
  CONFIGURED_KEYWORD = 'configured'

  def __init__(self, kube_client, membership_crd_manifest):
    self.kube_client = kube_client
    self.done = False
    self.succeeded = False
    self.error = None
    self.membership_crd_manifest = membership_crd_manifest

  def __str__(self):
    return '<creating membership CRD>'

  def Update(self):
    """Updates this operation with the latest membership creation status."""
    out, err = self.kube_client.CreateMembershipCRD(
        self.membership_crd_manifest
    )
    if err:
      self.done = True
      self.error = err

    # If creation is successful, the create operation should show "unchanged"
    # or "configured"
    elif self.CREATED_KEYWORD in out or self.CONFIGURED_KEYWORD in out:
      self.done = True
      self.succeeded = True


class KubeconfigProcessor(object):
  """A helper class that processes kubeconfig and context arguments."""

  def __init__(
      self,
      api_adapter,
      gke_uri,
      gke_cluster,
      kubeconfig,
      internal_ip,
      cross_connect_subnetwork,
      private_endpoint_fqdn,
      context,
  ):
    """Constructor for KubeconfigProcessor.

    Args:
      api_adapter: the GKE api adapter used for running kubernetes commands
      gke_uri: the URI of the GKE cluster; for example,
        'https://container.googleapis.com/v1/projects/my-project/locations/us-central1-a/clusters/my-cluster'
      gke_cluster: the "location/name" of the GKE cluster. The location can be a
        zone or a region for e.g `us-central1-a/my-cluster`
      kubeconfig: the kubeconfig path
      internal_ip: whether to persist the internal IP of the endpoint.
      cross_connect_subnetwork: full path of the cross connect subnet whose
        endpoint to persist (optional)
      private_endpoint_fqdn: whether to persist the private fqdn.
      context: the context to use

    Raises:
      exceptions.Error: if kubectl is not installed
    """

    self.api_adapter = api_adapter
    self.gke_uri = gke_uri
    self.gke_cluster = gke_cluster
    self.kubeconfig = kubeconfig
    self.internal_ip = internal_ip
    self.cross_connect_subnetwork = cross_connect_subnetwork
    self.private_endpoint_fqdn = private_endpoint_fqdn
    self.context = context
    # Warn if kubectl is not installed.
    if not c_util.CheckKubectlInstalled():
      raise exceptions.Error('kubectl not installed.')
    self.gke_cluster_self_link = None
    self.gke_cluster_uri = None

  def GetKubeconfigAndContext(self, temp_kubeconfig_dir):
    """Gets the kubeconfig, cluster context and resource link from arguments and defaults.

    Args:
      temp_kubeconfig_dir: a TemporaryDirectoryObject.

    Returns:
      the kubeconfig filepath and context name

    Raises:
      calliope_exceptions.MinimumArgumentException: if a kubeconfig file cannot
        be deduced from the command line flags or environment
      exceptions.Error: if the context does not exist in the deduced kubeconfig
        file
    """

    # Parsing flags to get the name and location of the GKE cluster to register
    if self.gke_uri or self.gke_cluster:
      cluster_project = None
      if self.gke_uri:
        cluster_project, location, name = gke_util.ParseGKEURI(self.gke_uri)
      else:
        cluster_project = properties.VALUES.core.project.GetOrFail()
        location, name = gke_util.ParseGKECluster(self.gke_cluster)

      self.gke_cluster_self_link, self.gke_cluster_uri = (
          gke_util.ConstructGKEClusterResourceLinkAndURI(
              cluster_project, location, name
          )
      )
      return (
          _GetGKEKubeconfig(
              self.api_adapter,
              cluster_project,
              location,
              name,
              temp_kubeconfig_dir,
              self.internal_ip,
              self.cross_connect_subnetwork,
              self.private_endpoint_fqdn,
          ),
          None,
      )

    # We need to support in-cluster configuration so that gcloud can run from
    # a container on the Cluster we are registering. KUBERNETES_SERICE_PORT
    # and KUBERNETES_SERVICE_HOST environment variables are set in a kubernetes
    # cluster automatically, which can be used by kubectl to talk to
    # the API server.
    if (
        not self.kubeconfig
        and encoding.GetEncodedValue(os.environ, 'KUBERNETES_SERVICE_PORT')
        and encoding.GetEncodedValue(os.environ, 'KUBERNETES_SERVICE_HOST')
    ):
      return None, None

    kubeconfig_file = (
        self.kubeconfig
        or encoding.GetEncodedValue(os.environ, 'KUBECONFIG')
        or '~/.kube/config'
    )

    kubeconfig = files.ExpandHomeDir(kubeconfig_file)
    if not kubeconfig:
      raise calliope_exceptions.MinimumArgumentException(
          ['--kubeconfig'],
          'Please specify --kubeconfig, set the $KUBECONFIG environment '
          'variable, or ensure that $HOME/.kube/config exists',
      )
    kc = kconfig.Kubeconfig.LoadFromFile(kubeconfig)

    context_name = self.context

    if context_name not in kc.contexts:
      raise exceptions.Error(
          'context [{}] does not exist in kubeconfig [{}]'.format(
              context_name, kubeconfig
          )
      )

    return kubeconfig, context_name

  def GetKubeClient(self, kubeconfig=None, context=None):
    """Gets a client derived from the kubeconfig and context.

    Args:
      kubeconfig: path to a kubeconfig file, None if in-cluster config.
      context: the kubeconfig context to use, None if in-cluster config.

    Returns:
      kubernetes.client.ApiClient
    """
    # If processor.GetKubeconfigAndContext returns `None` for the kubeconfig
    # path, that indicates we should be using in-cluster config. Otherwise,
    # the first return value is the path to the kubeconfig file.
    if kubeconfig is not None:
      kube_client_config.load_kube_config(
          config_file=kubeconfig, context=context
      )
      return kube_client_lib.ApiClient()
    else:
      kube_client_config.load_incluster_config()
      return kube_client_lib.ApiClient()


class KubernetesPoller(waiter.OperationPoller):
  """An OperationPoller that polls operations targeting Kubernetes clusters."""

  def IsDone(self, operation):
    return operation.done

  def Poll(self, operation_ref):
    operation_ref.Update()
    return operation_ref

  def GetResult(self, operation):
    return (operation.succeeded, operation.error)


class KubernetesClient(object):
  """A client for accessing a subset of the Kubernetes API."""

  def __init__(
      self,
      api_adapter=None,
      gke_uri=None,
      gke_cluster=None,
      kubeconfig=None,
      internal_ip=False,
      cross_connect_subnetwork=None,
      private_endpoint_fqdn=None,
      context=None,
      public_issuer_url=None,
      enable_workload_identity=False,
  ):
    """Constructor for KubernetesClient.

    Args:
      api_adapter: the GKE api adapter used for running kubernetes commands
      gke_uri: the URI of the GKE cluster; for example,
        'https://container.googleapis.com/v1/projects/my-project/locations/us-central1-a/clusters/my-cluster'
      gke_cluster: the "location/name" of the GKE cluster. The location can be a
        zone or a region for e.g `us-central1-a/my-cluster`
      kubeconfig: the kubeconfig path
      internal_ip: whether to persist the internal IP of the endpoint.
      cross_connect_subnetwork: full path of the cross connect subnet whose
        endpoint to persist (optional)
      private_endpoint_fqdn: whether to persist the private fqdn.
      context: the context to use
      public_issuer_url: the public issuer url
      enable_workload_identity: whether to enable workload identity

    Raises:
      exceptions.Error: if the client cannot be configured
      calliope_exceptions.MinimumArgumentException: if a kubeconfig file
        cannot be deduced from the command line flags or environment
    """
    self.kubectl_timeout = '20s'

    self.temp_kubeconfig_dir = None
    # If the cluster to be registered is a GKE cluster, create a temporary
    # directory to store the kubeconfig that will be generated using the
    # GKE GetCluster() API
    if gke_uri or gke_cluster:
      self.temp_kubeconfig_dir = files.TemporaryDirectory()

    self.processor = KubeconfigProcessor(
        api_adapter=api_adapter,
        gke_uri=gke_uri,
        gke_cluster=gke_cluster,
        kubeconfig=kubeconfig,
        internal_ip=internal_ip,
        cross_connect_subnetwork=cross_connect_subnetwork,
        private_endpoint_fqdn=private_endpoint_fqdn,
        context=context,
    )
    self.kubeconfig, self.context = self.processor.GetKubeconfigAndContext(
        self.temp_kubeconfig_dir
    )

    # This previously fixed b/152465794. It is probably unnecessary now that
    # we use the official K8s client, but it's also still true that we don't
    # need a K8s client to talk to the cluster in this case. Consider removing
    # this check later if we need the K8s client in other scenarios. For now,
    # the impact of switching to the official client can be minimized to only
    # scenarios where we actually need it.
    if public_issuer_url or (
        enable_workload_identity and self.processor.gke_cluster_uri
    ):
      return

    if enable_workload_identity:
      self.kube_client = self.processor.GetKubeClient(
          self.kubeconfig, self.context
      )

  def __enter__(self):
    return self

  def __exit__(self, *_):
    # delete temp directory
    if self.temp_kubeconfig_dir is not None:
      self.temp_kubeconfig_dir.Close()

  def CheckClusterAdminPermissions(self):
    """Check to see if the user can perform all the actions in any namespace.

    Raises:
      KubectlError: if failing to get check for cluster-admin permissions.
      RBACError: if cluster-admin permissions are not found.
    """
    out, err = self._RunKubectl(
        ['auth', 'can-i', '*', '*', '--all-namespaces'], None
    )
    if err:
      raise KubectlError(
          'Failed to check if the user is a cluster-admin: {}'.format(err)
      )

    if 'yes' not in out:
      raise RBACError(
          'Missing cluster-admin RBAC role: The cluster-admin role-based access'
          'control (RBAC) ClusterRole grants you the cluster permissions '
          'necessary to connect your clusters back to Google. \nTo create a '
          'ClusterRoleBinding resource in the cluster, run the following '
          'command:\n\n'
          'kubectl create clusterrolebinding [BINDING_NAME]  --clusterrole '
          'cluster-admin --user [USER]'
      )

  def GetNamespaceUID(self, namespace):
    out, err = self._RunKubectl(
        ['get', 'namespace', namespace, '-o', "jsonpath='{.metadata.uid}'"],
        None,
    )
    if err:
      raise exceptions.Error(
          'Failed to get the UID of the cluster: {}'.format(err)
      )
    return out.replace("'", '')

  def GetServerVersion(self):
    """Get server version of the cluster.

    Raises:
      exceptions.Error: if failing to get namespaces.

    Returns:
      Server version of the cluster in major.minor format (e.g. 1.21)
    """
    out, err = self._RunKubectl(['version', '-o', 'json'], None)
    if err:
      raise exceptions.Error(
          'Failed to get the server version of the cluster: {}'.format(err)
      )

    # kubectl version operation does not support jsonpath to retrieve the
    # details of the individual fields, so this is a workaround for now.
    out = json.loads(out)
    version_str = (
        out['serverVersion']['major'] + '.' + out['serverVersion']['minor']
    )
    return version_str

  def GetEvents(self, namespace):
    """Get k8s events for the namespace."""
    out, err = self._RunKubectl(
        [
            'get',
            'events',
            '--namespace=' + namespace,
            "--sort-by='{.lastTimestamp}'",
        ],
        None,
    )
    if err:
      raise exceptions.Error()
    return out

  def NamespacesWithLabelSelector(self, label):
    """Get the Connect Agent namespace by label.

    Args:
      label: the label used for namespace selection

    Raises:
      exceptions.Error: if failing to get namespaces.

    Returns:
      The first namespace with the label selector.
    """
    # Check if any namespace with label exists.
    out, err = self._RunKubectl(
        ['get', 'namespaces', '--selector', label, '-o', 'jsonpath={.items}'],
        None,
    )
    if err:
      raise exceptions.Error(
          'Failed to list namespaces in the cluster: {}'.format(err)
      )
    if out == '[]':
      return []
    out, err = self._RunKubectl(
        [
            'get',
            'namespaces',
            '--selector',
            label,
            '-o',
            'jsonpath={.items[0].metadata.name}',
        ],
        None,
    )
    if err:
      raise exceptions.Error(
          'Failed to list namespaces in the cluster: {}'.format(err)
      )
    return out.strip().split(' ') if out else []

  def DeleteMembership(self):
    _, err = self._RunKubectl(['delete', 'membership', 'membership'])
    return err

  # Get the clusterrolebinding/rolebinding from the RBAC permission policy.
  def GetRbacPermissionPolicy(self, rbac_policy_name, role):
    """Get the RBAC cluster role binding policy."""
    cluster_pattern = re.compile('^clusterrole/')
    namespace_pattern = re.compile('^role/')

    if cluster_pattern.match(role.lower()):
      out, error = self._RunKubectl(
          ['get', 'clusterrolebinding', rbac_policy_name, '-o', 'yaml']
      )
      if error:
        raise exceptions.Error(
            'Error retrieving RBAC policy: {}'.format(rbac_policy_name)
        )
      return out
    if namespace_pattern.match(role.lower()):
      out, error = self._RunKubectl(
          ['get', 'rolebinding', rbac_policy_name, '-o', 'yaml']
      )
      if error:
        raise exceptions.Error(
            'Error retrieving RBAC policy: {}'.format(rbac_policy_name)
        )
      return out

  def CleanUpRbacPolicy(self, rbac_to_check):
    """Clean up the RBAC cluster role binding policy."""
    for rbac_policy_pair in rbac_to_check:
      rbac_type = rbac_policy_pair[0]
      rbac_name = rbac_policy_pair[1]
      out, err = self._RunKubectl(['delete', rbac_type, rbac_name], None)
      if err:
        if 'NotFound' in err:
          log.status.Print(
              '{} for RBAC policy: {} not exist.'.format(rbac_type, rbac_name)
          )
          continue
        else:
          raise exceptions.Error('Error deleting RBAC policy: {}'.format(err))
      else:
        log.status.Print('{}'.format(out))
    return True

  def GetRbacPolicyDiff(self, rbac_policy_file):
    out, err = self._RunKubectlDiff(['diff', '-f', rbac_policy_file], None)
    return out, err

  # Check the existing RBAC policy for specified cluster. Return false if there
  # are existing one.
  def GetRbacPolicy(self, rbac_to_check):
    """Get the RBAC cluster role binding policy."""
    not_found = False
    for rbac_policy_pair in rbac_to_check:
      rbac_type = rbac_policy_pair[0]
      rbac_name = rbac_policy_pair[1]
      _, err = self._RunKubectl(['get', rbac_type, rbac_name])
      if err:
        if 'NotFound' in err:
          not_found = True
        else:
          raise exceptions.Error('Error retrieving RBAC policy: {}'.format(err))
      else:
        return False
    if not_found:
      return True

  def GetRBACForOperations(
      self, membership, role, project_id, identity, is_user, anthos_support
  ):
    """Get the formatted RBAC policy names."""
    cluster_pattern = re.compile('^clusterrole/')
    namespace_pattern = re.compile('^role/')
    rbac_to_check = []

    if is_user:
      rbac_to_check.extend([
          (
              'clusterrole',
              format_util.RbacPolicyName(
                  'impersonate', project_id, membership, identity, is_user
              ),
          ),
          (
              'clusterrolebinding',
              format_util.RbacPolicyName(
                  'impersonate', project_id, membership, identity, is_user
              ),
          ),
      ])
    # Check anthos-support permission policy when '--anthos-support' specified.
    if anthos_support:
      rbac_to_check.append((
          'clusterrolebinding',
          format_util.RbacPolicyName(
              'anthos', project_id, membership, identity, is_user
          ),
      ))
    # Check namespace permission policy when role is specified as
    # 'role/namespace/namespace-permission'.
    elif cluster_pattern.match(role.lower()):
      rbac_to_check.append((
          'clusterrolebinding',
          format_util.RbacPolicyName(
              'permission', project_id, membership, identity, is_user
          ),
      ))
    # Check RBAC permission policy for general clusterrole.
    elif namespace_pattern.match(role.lower()):
      rbac_to_check.append((
          'rolebinding',
          format_util.RbacPolicyName(
              'permission', project_id, membership, identity, is_user
          ),
      ))
    return rbac_to_check

  def MembershipCRDExists(self):
    """Returns a boolean indicating if the Membership CRD exists."""
    _, err = self._RunKubectl(
        [
            'get',
            'customresourcedefinitions.apiextensions.k8s.io',
            'memberships.hub.gke.io',
        ],
        None,
    )
    if err:
      if 'NotFound' in err:
        return False
      raise exceptions.Error('Error retrieving Membership CRD: {}'.format(err))
    return True

  def GetMembershipCR(self):
    """Get the YAML representation of the Membership CR."""
    out, err = self._RunKubectl(
        ['get', 'membership', 'membership', '-o', 'yaml'], None
    )
    if err:
      if 'NotFound' in err:
        return ''
      raise exceptions.Error('Error retrieving membership CR: {}'.format(err))
    return out

  def GetMembershipCRD(self):
    """Get the YAML representation of the Membership CRD."""
    out, err = self._RunKubectl(
        [
            'get',
            'customresourcedefinitions.apiextensions.k8s.io',
            'memberships.hub.gke.io',
            '-o',
            'yaml',
        ],
        None,
    )
    if err:
      if 'NotFound' in err:
        return ''
      raise exceptions.Error('Error retrieving membership CRD: {}'.format(err))
    return out

  def GetMembershipOwnerID(self):
    """Looks up the owner id field in the Membership resource."""
    if not self.MembershipCRDExists():
      return None

    out, err = self._RunKubectl(
        ['get', 'membership', 'membership', '-o', 'jsonpath={.spec.owner.id}'],
        None,
    )
    if err:
      if 'NotFound' in err:
        return None
      raise exceptions.Error('Error retrieving membership id: {}'.format(err))
    return out

  def CreateMembershipCRD(self, membership_crd_manifest):
    return self.Apply(membership_crd_manifest)

  def ApplyMembership(self, membership_crd_manifest, membership_cr_manifest):
    """Apply membership resources."""
    if membership_crd_manifest:
      _, error = waiter.WaitFor(
          KubernetesPoller(),
          MembershipCRDCreationOperation(self, membership_crd_manifest),
          pre_start_sleep_ms=NAMESPACE_DELETION_INITIAL_WAIT_MS,
          max_wait_ms=NAMESPACE_DELETION_TIMEOUT_MS,
          wait_ceiling_ms=NAMESPACE_DELETION_MAX_POLL_INTERVAL_MS,
          sleep_ms=NAMESPACE_DELETION_INITIAL_POLL_INTERVAL_MS,
      )
      if error:
        raise exceptions.Error(
            'Membership CRD creation failed to complete: {}'.format(error)
        )
    if membership_cr_manifest:
      _, err = self.Apply(membership_cr_manifest)
      if err:
        raise exceptions.Error(
            'Failed to apply Membership CR to cluster: {}'.format(err)
        )

  def ApplyRbacPolicy(self, rbac_policy_file):
    """Applying RBAC policy to Cluster."""
    _, err = self.ApplyRbac(rbac_policy_file)
    if err:
      raise exceptions.Error(
          'Failed to apply rbac policy file to cluster: {}'.format(err)
      )

  def NamespaceExists(self, namespace):
    _, err = self._RunKubectl(['get', 'namespace', namespace])
    return err is None

  def DeleteNamespace(self, namespace):
    _, err = self._RunKubectl(
        ['delete', 'namespace', namespace], timeout_flag='--timeout'
    )
    return err

  def GetResourceField(self, namespace, resource, json_path):
    """Returns the value of a field on a Kubernetes resource.

    Args:
      namespace: the namespace of the resource, or None if this resource is
        cluster-scoped
      resource: the resource, in the format <resourceType>/<name>; e.g.,
        'configmap/foo', or <resourceType> for a list of resources
      json_path: the JSONPath expression to filter with

    Returns:
      The field value (which could be empty if there is no such field), or
      the error printed by the command if there is an error.
    """
    cmd = ['-n', namespace] if namespace else []
    cmd.extend(['get', resource, '-o', 'jsonpath={{{}}}'.format(json_path)])
    return self._RunKubectl(cmd)

  def ApplyRbac(self, rbac_policy):
    out, err = self._RunKubectl(['apply', '-f', rbac_policy], None)
    return out, err

  def Apply(self, manifest):
    out, err = self._RunKubectl(['apply', '-f', '-'], stdin=manifest)
    return out, err

  def Delete(self, manifest):
    _, err = self._RunKubectl(['delete', '-f', '-'], stdin=manifest)
    return err

  def Logs(self, namespace, log_target):
    """Gets logs from a workload in the cluster.

    Args:
      namespace: the namespace from which to collect logs.
      log_target: the target for the logs command. Any target supported by
        'kubectl logs' is supported here.

    Returns:
      The logs, or an error if there was an error gathering these logs.
    """
    return self._RunKubectl(['logs', '-n', namespace, log_target])

  def _WebRequest(self, method, url, headers=None):
    """Internal method to make requests against web URLs.

    Args:
      method: request method, e.g. GET
      url: request URL
      headers: dictionary of request headers

    Returns:
      Response body as a string

    Raises:
      Error: If the response has a status code >= 400.
    """
    r = requests.GetSession().request(method, url, headers=headers)
    status = r.status_code
    if status >= 400:
      raise exceptions.Error('status: {}, reason: {}'.format(status, r.reason))
    return r.content

  def _ClusterRequest(self, method, api_path, headers=None):
    """Internal method to make requests against the target cluster.

    Args:
      method: request method, e.g. GET
      api_path: path to request against the API server
      headers: dictionary of request headers

    Returns:
      Response body as a string.

    Raises:
      Error: If the response has a status code >= 400.
    """
    if headers is None:
      headers = {}

    # This works for both client certificate and bearer token auth. Passing
    # auth_settings=['BearerToken'] causes the client to update the headers
    # if a bearer token value is present in the config. If client certs are
    # used instead, there is no token value, and the client skips modifying
    # the headers.
    self.kube_client.update_params_for_auth(
        headers=headers, querys=None, auth_settings=['BearerToken']
    )

    # The official client takes care of raising ApiException on bad HTTP codes,
    # and also takes care of decoding the data from bytes to UTF-8 in PY3.
    url = urljoin(self.kube_client.configuration.host, api_path)
    r = self.kube_client.rest_client.request(method, url, headers=headers)
    return r.data

  def GetOpenIDConfiguration(self, issuer_url=None):
    """Get the OpenID Provider Configuration for the K8s API server.

    Args:
      issuer_url: string, the issuer URL to query for the OpenID Provider
        Configuration. If None, queries the custer's built-in endpoint.

    Returns:
      The JSON response as a string.

    Raises:
      Error: If the query failed.
    """
    headers = {
        'Content-Type': 'application/json',
    }
    url = None
    try:
      if issuer_url is not None:
        url = issuer_url.rstrip('/') + '/.well-known/openid-configuration'
        return self._WebRequest('GET', url, headers=headers)
      else:
        url = '/.well-known/openid-configuration'
        return self._ClusterRequest('GET', url, headers=headers)
    except Exception as e:  # pylint: disable=broad-except
      raise exceptions.Error(
          'Failed to get OpenID Provider Configuration from {}: {}'.format(
              url, e
          )
      )

  def GetOpenIDKeyset(self, jwks_uri=None):
    """Get the JSON Web Key Set for the K8s API server.

    Args:
      jwks_uri: string, the JWKS URI to query for the JSON Web Key Set. If None,
        queries the cluster's built-in endpoint.

    Returns:
      The JSON response as a string.

    Raises:
      Error: If the query failed.
    """
    headers = {
        'Content-Type': 'application/jwk-set+json',
    }
    url = None
    try:
      if jwks_uri is not None:
        url = jwks_uri
        return self._WebRequest('GET', url, headers=headers)
      else:
        url = '/openid/v1/jwks'
        return self._ClusterRequest('GET', url, headers=headers)
    except Exception as e:  # pylint: disable=broad-except
      raise exceptions.Error(
          'Failed to get JSON Web Key Set from {}: {}'.format(url, e)
      )

  def _RunKubectl(self, args, stdin=None, timeout_flag='--request-timeout'):
    """Runs a kubectl command with the cluster referenced by this client.

    Args:
      args: command line arguments to pass to kubectl
      stdin: text to be passed to kubectl via stdin
      timeout_flag: kubectl command flag used to set timeout

    Returns:
      The contents of stdout if the return code is 0, stderr (or a fabricated
      error if stderr is empty) otherwise
    """
    cmd = [c_util.CheckKubectlInstalled()]
    if self.context:
      cmd.extend(['--context', self.context])

    if self.kubeconfig:
      cmd.extend(['--kubeconfig', self.kubeconfig])

    cmd.extend([timeout_flag, self.kubectl_timeout])
    cmd.extend(args)
    out = io.StringIO()
    err = io.StringIO()
    returncode = execution_utils.Exec(
        cmd, no_exit=True, out_func=out.write, err_func=err.write, in_str=stdin
    )

    if returncode != 0 and not err.getvalue():
      err.write('kubectl exited with return code {}'.format(returncode))

    return (
        out.getvalue() if returncode == 0 else None,
        err.getvalue() if returncode != 0 else None,
    )

  def _RunKubectlDiff(self, args, stdin=None):
    """Runs a kubectl diff command with the specified args.

    Args:
      args: command line arguments to pass to kubectl
      stdin: text to be passed to kubectl via stdin

    Returns:
      The contents of stdout if the return code is 1, stderr (or a fabricated
      error if stderr is empty) otherwise
    """
    cmd = [c_util.CheckKubectlInstalled()]
    if self.context:
      cmd.extend(['--context', self.context])

    if self.kubeconfig:
      cmd.extend(['--kubeconfig', self.kubeconfig])

    cmd.extend(['--request-timeout', self.kubectl_timeout])
    cmd.extend(args)
    out = io.StringIO()
    err = io.StringIO()
    returncode = execution_utils.Exec(
        cmd, no_exit=True, out_func=out.write, err_func=err.write, in_str=stdin
    )
    # kubectl diff return is different with other CLI.
    # Exit status: 0 No differences were found. 1 Differences were found.
    # >1 Kubectl or diff failed with an error.
    return (
        out.getvalue() if returncode == 1 else None,
        err.getvalue() if returncode > 1 else None,
    )


class DeploymentPodsAvailableOperation(object):
  """An operation that tracks whether a Deployment's Pods are all available."""

  def __init__(self, namespace, deployment_name, image, kube_client):
    self.namespace = namespace
    self.deployment_name = deployment_name
    self.image = image
    self.kube_client = kube_client
    self.done = False
    self.succeeded = False
    self.error = None

  def __str__(self):
    return '<Pod availability for {}/{}>'.format(
        self.namespace, self.deployment_name
    )

  def Update(self):
    """Updates this operation with the latest Deployment availability status."""
    deployment_resource = 'deployment/{}'.format(self.deployment_name)

    def _HandleErr(err):
      """Updates the operation for the provided error."""
      # If the deployment hasn't been created yet, then wait for it to be.
      if 'NotFound' in err:
        return

      # Otherwise, fail the operation.
      self.done = True
      self.succeeded = False
      self.error = err

    # Ensure that the Deployment has the correct image, so that this operation
    # is tracking the status of a new rollout, not the pre-rollout steady state.
    deployment_image, err = self.kube_client.GetResourceField(
        self.namespace,
        deployment_resource,
        '.spec.template.spec.containers[0].image',
    )
    if err:
      _HandleErr(err)
      return
    if deployment_image != self.image:
      return

    spec_replicas, err = self.kube_client.GetResourceField(
        self.namespace, deployment_resource, '.spec.replicas'
    )
    if err:
      _HandleErr(err)
      return

    status_replicas, err = self.kube_client.GetResourceField(
        self.namespace, deployment_resource, '.status.replicas'
    )
    if err:
      _HandleErr(err)
      return

    available_replicas, err = self.kube_client.GetResourceField(
        self.namespace, deployment_resource, '.status.availableReplicas'
    )
    if err:
      _HandleErr(err)
      return

    updated_replicas, err = self.kube_client.GetResourceField(
        self.namespace, deployment_resource, '.status.updatedReplicas'
    )
    if err:
      _HandleErr(err)
      return

    # This mirrors the replica-count logic used by kubectl rollout status:
    # https://github.com/kubernetes/kubernetes/blob/master/pkg/kubectl/rollout_status.go
    # Not enough replicas are up-to-date.
    if updated_replicas < spec_replicas:
      return
    # Replicas of an older version have not been turned down.
    if status_replicas > updated_replicas:
      return
    # Not enough replicas are up and healthy.
    if available_replicas < updated_replicas:
      return

    self.succeeded = True
    self.done = True


class NamespaceDeleteOperation(object):
  """An operation that waits for a namespace to be deleted."""

  def __init__(self, namespace, kube_client):
    self.namespace = namespace
    self.kube_client = kube_client
    self.done = False
    self.succeeded = False
    self.error = None

  def __str__(self):
    return '<deleting namespace {}>'.format(self.namespace)

  def Update(self):
    """Updates this operation with the latest namespace deletion status."""
    err = self.kube_client.DeleteNamespace(self.namespace)

    # The first delete request should succeed.
    if not err:
      return

    # If deletion is successful, the delete command will return a NotFound
    # error.
    if 'NotFound' in err:
      self.done = True
      self.succeeded = True
    else:
      self.error = err


def _GetGKEKubeconfig(
    api_adapter,
    project,
    location_id,
    cluster_id,
    temp_kubeconfig_dir,
    internal_ip,
    cross_connect_subnetwork,
    private_endpoint_fqdn,
):
  """The kubeconfig of GKE Cluster is fetched using the GKE APIs.

  The 'KUBECONFIG' value in `os.environ` will be temporarily updated with
  the temporary kubeconfig's path if the kubeconfig arg is not None.
  Consequently, subprocesses started with
  googlecloudsdk.core.execution_utils.Exec will see the temporary KUBECONFIG
  environment variable.

  Using GKE APIs the GKE cluster is validated, and the ClusterConfig object, is
  persisted in the temporarily updated 'KUBECONFIG'.

  Args:
    api_adapter: the GKE api adapter used for running kubernetes commands
    project: string, the project id of the cluster for which kube config is to
      be fetched
    location_id: string, the id of the location to which the cluster belongs
    cluster_id: string, the id of the cluster
    temp_kubeconfig_dir: TemporaryDirectory object
    internal_ip: whether to persist the internal IP of the endpoint.
    cross_connect_subnetwork: full path of the cross connect subnet whose
      endpoint to persist (optional)
    private_endpoint_fqdn: whether to persist the private fqdn.

  Raises:
    Error: If unable to get credentials for kubernetes cluster.

  Returns:
    the path to the kubeconfig file
  """
  kubeconfig = os.path.join(temp_kubeconfig_dir.path, 'kubeconfig')
  old_kubeconfig = encoding.GetEncodedValue(os.environ, 'KUBECONFIG')
  try:
    encoding.SetEncodedValue(os.environ, 'KUBECONFIG', kubeconfig)
    if api_adapter is None:
      api_adapter = gke_api_adapter.NewAPIAdapter('v1')
    cluster_ref = api_adapter.ParseCluster(cluster_id, location_id, project)
    cluster = api_adapter.GetCluster(cluster_ref)
    auth = cluster.masterAuth
    valid_creds = auth and auth.clientCertificate and auth.clientKey
    # c_util.ClusterConfig.UseGCPAuthProvider() checks for
    # container/use_client_certificate setting
    if not valid_creds and not c_util.ClusterConfig.UseGCPAuthProvider():
      raise c_util.Error(
          'Unable to get cluster credentials. User must have edit '
          'permission on {}'.format(cluster_ref.projectId)
      )
    c_util.ClusterConfig.Persist(
        cluster,
        cluster_ref.projectId,
        internal_ip,
        cross_connect_subnetwork,
        private_endpoint_fqdn,
    )
  finally:
    if old_kubeconfig:
      encoding.SetEncodedValue(os.environ, 'KUBECONFIG', old_kubeconfig)
    else:
      del os.environ['KUBECONFIG']
  return kubeconfig


def ValidateClusterIdentifierFlags(kube_client, args):
  """Validates if --gke-cluster | --gke-uri is supplied for GKE cluster, and --context for non GKE clusters.

  Args:
    kube_client: A Kubernetes client for the cluster to be registered.
    args: An argparse namespace. All arguments that were provided to this
      command invocation.

  Raises:
    calliope_exceptions.ConflictingArgumentsException: --context, --gke-uri,
    --gke-cluster are conflicting arguments.
    calliope_exceptions.ConflictingArgumentsException is raised if more than
    one of these arguments is set.

    calliope_exceptions.InvalidArgumentException is raised if --context is set
    for non GKE clusters.
  """
  is_gke_cluster = IsGKECluster(kube_client)
  if args.context and is_gke_cluster:
    raise calliope_exceptions.InvalidArgumentException(
        '--context',
        '--context cannot be used for GKE clusters. '
        'Either --gke-uri | --gke-cluster must be specified',
    )

  if args.gke_uri and not is_gke_cluster:
    raise calliope_exceptions.InvalidArgumentException(
        '--gke-uri', 'use --context for non GKE clusters.'
    )

  if args.gke_cluster and not is_gke_cluster:
    raise calliope_exceptions.InvalidArgumentException(
        '--gke-cluster', 'use --context for non GKE clusters.'
    )


def IsGKECluster(kube_client):
  """Returns true if the cluster to be registered is a GKE cluster.

  There is no straightforward way to obtain this information from the cluster
  API server directly. This method uses metadata on the Kubernetes nodes to
  determine the instance ID. The instance ID field is unique to GKE clusters:
  Kubernetes-on-GCE clusters do not have this field. This test doesn't work in
  identifing a GKE cluster with zero nodes.

  Args:
    kube_client: A Kubernetes client for the cluster to be registered.

  Raises:
      exceptions.Error: if failing there's a permission error or for invalid
      command.

  Returns:
    bool: True if kubeclient communicates with a GKE Cluster, false otherwise.
  """
  # gke_cluster_self_link is sufficient to test for a GKE cluster.
  # If gke_cluster_self_link is not populated, then use metadata on the
  # Kubernetes nodes to identify a GKE cluster.
  if kube_client.processor and kube_client.processor.gke_cluster_self_link:
    return True

  vm_instance_id, err = kube_client.GetResourceField(
      None,
      'nodes',
      '.items[*].metadata.annotations.container\\.googleapis\\.com/instance_id',
  )

  if err:
    raise exceptions.Error(
        'kubectl returned non-zero status code: {}'.format(err)
    )

  if not vm_instance_id:
    return False
  return True
