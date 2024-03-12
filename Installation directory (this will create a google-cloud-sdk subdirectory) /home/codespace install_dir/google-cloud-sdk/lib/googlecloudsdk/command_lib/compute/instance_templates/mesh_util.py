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
"""Utils for mesh flag in the instance template commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import collections
import io
import json
import re

from googlecloudsdk.api_lib.container import util as c_util
from googlecloudsdk.command_lib.compute.instance_templates import service_proxy_aux_data
from googlecloudsdk.command_lib.container.fleet import api_util
from googlecloudsdk.command_lib.container.fleet import kube_util as hub_kube_util
from googlecloudsdk.command_lib.projects import util as project_util
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import execution_utils
from googlecloudsdk.core import yaml
from googlecloudsdk.core.util import files

_EXPANSION_GATEWAY_NAME = 'istio-eastwestgateway'
_SERVICE_PROXY_BUCKET_NAME = (
    'gs://gce-service-proxy/service-proxy-agent/releases/'
    'service-proxy-agent-asm-{}-stable.tgz')
_SERVICE_PROXY_INSTALLER_BUCKET_NAME = (
    'gs://gce-service-proxy/service-proxy-agent-installer/'
    'releases/installer.tgz')
_GCE_SERVICE_PROXY_ASM_VERSION_METADATA = 'gce-service-proxy-asm-version'
_GCE_SERVICE_PROXY_INSTALLER_BUCKET_METADATA = (
    'gce-service-proxy-installer-bucket')
_GCE_SERVICE_PROXY_AGENT_BUCKET_METADATA = 'gce-service-proxy-agent-bucket'

_ISTIO_CANONICAL_SERVICE_NAME_LABEL = 'service.istio.io/canonical-name'
_ISTIO_CANONICAL_SERVICE_REVISION_LABEL = 'service.istio.io/canonical-revision'
_KUBERNETES_APP_NAME_LABEL = 'app.kubernetes.io/name'
_KUBERNETES_APP_VERSION_LABEL = 'app.kubernetes.io/version'

_ISTIO_META_CLOUDRUN_ADDR_KEY = 'ISTIO_META_CLOUDRUN_ADDR'
_CLOUDRUN_ADDR_KEY = 'CLOUDRUN_ADDR'

_ISTIO_DISCOVERY_PORT = '15012'

_WORKLOAD_PATTERN = r'(.*)\/(.*)'
# Allow non-prod GKE Hub memberships to be specified.
_GKEHUB_PATTERN = r'\/\/gkehub(.*).googleapis.com\/(.*)'
_ASM_VERSION_PATTERN = r':(.*)-'

_INCLUSTER_WEBHOOK_PREFIX = 'istio-sidecar-injector'
_MCP_WEBHOOK_PREFIX = 'istiod'

_MCP_ADDRESS = 'meshconfig.googleapis.com:443'

ServiceProxyMetadataArgs = collections.namedtuple('ServiceProxyMetadataArgs', [
    'asm_version', 'project_id', 'expansionagateway_ip',
    'service_proxy_api_server', 'identity_provider', 'service_account',
    'asm_proxy_config', 'mcp_env_config', 'trust_domain', 'mesh_id', 'network',
    'asm_labels', 'workload_name', 'workload_namespace', 'canonical_service',
    'canonical_revision', 'asm_revision', 'root_cert'
])


def ParseWorkload(workload):
  """Parses the workload value to workload namespace and name.

  Args:
    workload: The workload value with namespace/name format.

  Returns:
    workload namespace and workload name.

  Raises:
    Error: if the workload value is invalid.
  """
  workload_match = re.search(_WORKLOAD_PATTERN, workload)
  if workload_match:
    return workload_match.group(1), workload_match.group(2)
  raise exceptions.Error(
      'value workload: {} is invalid. Workload value should have the format'
      'namespace/name.'.format(workload))


def _ParseMembershipName(owner_id):
  """Get membership name from an owner id value.

  Args:
    owner_id: The owner ID value of a membership. e.g.,
    //gkehub.googleapis.com/projects/123/locations/global/memberships/test.

  Returns:
    The full resource name of the membership, e.g.,
      projects/foo/locations/global/memberships/name.

  Raises:
    Error: if the membership name cannot be parsed.
  """
  membership_match = re.search(_GKEHUB_PATTERN, owner_id)
  if membership_match:
    return membership_match.group(2)
  raise exceptions.Error(
      'value owner_id: {} is invalid.'.format(owner_id))


def _GetVMIdentityProvider(membership_manifest, workload_namespace):
  """Get the identity provider for the VMs.

  Args:
    membership_manifest: The membership manifest from the cluster.
    workload_namespace: The namespace of the VM workload.

  Returns:
    The identity provider value to be used on the VM connected to the cluster.

  Raises:
    ClusterError: If the membership manifest cannot be read.
  """
  if not membership_manifest:
    raise ClusterError('Cannot verify an empty membership from the cluster')

  try:
    membership_data = yaml.load(membership_manifest)
  except yaml.Error as e:
    raise exceptions.Error(
        'Invalid membership from the cluster {}'.format(membership_manifest), e)

  owner_id = _GetNestedKeyFromManifest(
      membership_data, 'spec', 'owner', 'id')
  if not owner_id:
    raise ClusterError('Invalid membership does not have an owner id. Please '
                       'make sure your cluster is correctly registered and '
                       'retry.')

  membership_name = _ParseMembershipName(owner_id)
  membership = api_util.GetMembership(membership_name)
  if not membership.uniqueId:
    raise exceptions.Error('Invalid membership {} does not have a unique_Id '
                           'field. Please make sure your cluster is correctly '
                           'registered and retry.'.format(membership_name))

  return '{}@google@{}'.format(membership.uniqueId, workload_namespace)


def _RetrieveProxyConfig(is_mcp, mesh_config):
  """Retrieve proxy config from a mesh config.

  Args:
    is_mcp: Whether the control plane is managed or not.
    mesh_config: A mesh config from the cluster.

  Returns:
    proxy_config: The proxy config from the mesh config.
  """
  try:
    proxy_config = mesh_config['defaultConfig']
  except (KeyError, TypeError):
    if is_mcp:
      return {}
    raise exceptions.Error(
        'Proxy config cannot be found in the Anthos Service Mesh.')

  return proxy_config


def _RetrieveTrustDomain(is_mcp, mesh_config):
  """Retrieve trust domain from a mesh config.

  Args:
    is_mcp: Whether the control plane is managed or not.
    mesh_config: A mesh config from the cluster.

  Returns:
    trust_domain: The trust domain from the mesh config.
  """
  try:
    trust_domain = mesh_config['trustDomain']
  except (KeyError, TypeError):
    if is_mcp:
      return None
    raise exceptions.Error(
        'Trust Domain cannot be found in the Anthos Service Mesh.')

  return trust_domain


def _RetrieveMeshId(is_mcp, mesh_config):
  """Retrieve mesh id from a mesh config.

  Args:
    is_mcp: Whether the control plane is managed or not.
    mesh_config: A mesh config from the cluster.

  Returns:
    mesh_id: The mesh id from the mesh config.
  """
  proxy_config = _RetrieveProxyConfig(is_mcp, mesh_config)

  try:
    mesh_id = proxy_config['meshId']
  except (KeyError, TypeError):
    if is_mcp:
      return None
    raise exceptions.Error(
        'Mesh ID cannot be found in the Anthos Service Mesh.')

  return mesh_id


def _RetrieveDiscoveryAddress(mesh_config):
  """Get the discovery address used in the MCP installation.

  Args:
    mesh_config: A mesh config from the cluster.

  Returns:
    The discovery address.
  """
  proxy_config = _RetrieveProxyConfig(is_mcp=True, mesh_config=mesh_config)

  if proxy_config is None:
    proxy_config = {}

  # When user does not provide a discoveryAddress in the proxy config, the
  # default MCP discovery address is used here. We expect mesh agent to get
  # the correct discoveryAddress during bootstrap.
  return proxy_config.get('discoveryAddress', _MCP_ADDRESS)


def _IsMCP(kube_client, revision):
  """Check if ASM control plane is managed.

  Args:
    kube_client: A kubernetes client for the cluster.
    revision: The ASM revision to check for control plane type.

  Returns:
    True if the control plane is MCP, otherwise False.
  """
  # MCP uses the url field in the webhook ClientConfig and In-cluster CP uses
  # the service field instead.
  # TODO(b/195018417): Further validate the URL format when it is using
  # meshconfig endpoint.
  url = kube_client.RetrieveMutatingWebhookURL(revision)

  if url:
    return True
  return False


def _GetWorkloadLabels(workload_manifest):
  """Get the workload labels from a workload manifest.

  Args:
    workload_manifest: The manifest of the workload.

  Returns:
    The workload labels.

  Raises:
    WorkloadError: If the workload manifest cannot be read.
  """
  if not workload_manifest:
    raise WorkloadError('Cannot verify an empty workload from the cluster')

  try:
    workload_data = yaml.load(workload_manifest)
  except yaml.Error as e:
    raise exceptions.Error(
        'Invalid workload from the cluster {}'.format(workload_data), e)

  workload_labels = _GetNestedKeyFromManifest(workload_data, 'spec', 'metadata',
                                              'labels')

  return workload_labels


def _GetCanonicalServiceName(workload_name, workload_manifest):
  """Get the canonical service name of the workload.

  Args:
    workload_name: The name of the workload.
    workload_manifest: The manifest of the workload.

  Returns:
    The canonical service name of the workload.
  """
  workload_labels = _GetWorkloadLabels(workload_manifest)

  return _ExtractCanonicalServiceName(workload_labels, workload_name)


def _GetCanonicalServiceRevision(workload_manifest):
  """Get the canonical service revision of the workload.

  Args:
    workload_manifest: The manifest of the workload.

  Returns:
    The canonical service revision of the workload.
  """
  workload_labels = _GetWorkloadLabels(workload_manifest)

  return _ExtractCanonicalServiceRevision(workload_labels)


def _ExtractCanonicalServiceName(workload_labels, workload_name):
  """Get the canonical service name of the workload.

  Args:
    workload_labels: A map of workload labels.
    workload_name: The name of the workload.

  Returns:
    The canonical service name of the workload.
  """
  if not workload_labels:
    return workload_name

  svc = workload_labels.get(_ISTIO_CANONICAL_SERVICE_NAME_LABEL)
  if svc:
    return svc

  svc = workload_labels.get(_KUBERNETES_APP_NAME_LABEL)
  if svc:
    return svc

  svc = workload_labels.get('app')
  if svc:
    return svc

  return workload_name


def _ExtractCanonicalServiceRevision(workload_labels):
  """Get the canonical service revision of the workload.

  Args:
    workload_labels: A map of workload labels.

  Returns:
    The canonical service revision of the workload.
  """
  if not workload_labels:
    return 'latest'

  rev = workload_labels.get(_ISTIO_CANONICAL_SERVICE_REVISION_LABEL)
  if rev:
    return rev

  rev = workload_labels.get(_KUBERNETES_APP_VERSION_LABEL)
  if rev:
    return rev

  rev = workload_labels.get('version')
  if rev:
    return rev

  return 'latest'


def VerifyWorkloadSetup(workload_manifest):
  """Verify VM workload setup in the cluster."""
  if not workload_manifest:
    raise WorkloadError('Cannot verify an empty workload from the cluster')

  try:
    workload_data = yaml.load(workload_manifest)
  except yaml.Error as e:
    raise exceptions.Error(
        'Invalid workload from the cluster {}'.format(workload_manifest), e)

  identity_provider_value = _GetNestedKeyFromManifest(
      workload_data, 'spec', 'metadata', 'annotations',
      'security.cloud.google.com/IdentityProvider')
  if identity_provider_value != 'google':
    raise WorkloadError('Unable to find the GCE IdentityProvider in the '
                        'specified WorkloadGroup. Please make sure the '
                        'GCE IdentityProvider is specified in the '
                        'WorkloadGroup.')


def RetrieveWorkloadRevision(namespace_manifest):
  """Retrieve the Anthos Service Mesh revision for the workload."""
  if not namespace_manifest:
    raise WorkloadError('Cannot verify an empty namespace from the cluster')

  try:
    namespace_data = yaml.load(namespace_manifest)
  except yaml.Error as e:
    raise exceptions.Error(
        'Invalid namespace from the cluster {}'.format(namespace_manifest), e)

  workload_revision = _GetNestedKeyFromManifest(namespace_data, 'metadata',
                                                'labels', 'istio.io/rev')
  if not workload_revision:
    raise WorkloadError('Workload namespace does not have an Anthos Service '
                        'Mesh revision label. Please make sure the namespace '
                        'is labeled and try again.')

  return workload_revision


def _RetrieveWorkloadServiceAccount(workload_manifest):
  """Retrieve the service account used for the workload."""
  if not workload_manifest:
    raise WorkloadError('Cannot verify an empty workload from the cluster')

  try:
    workload_data = yaml.load(workload_manifest)
  except yaml.Error as e:
    raise exceptions.Error(
        'Invalid workload from the cluster {}'.format(workload_manifest), e)

  service_account = _GetNestedKeyFromManifest(workload_data, 'spec', 'template',
                                              'serviceAccount')
  return service_account


def _RetrieveServiceProxyMetadata(args, is_mcp, kube_client, project_id,
                                  network_resource, workload_namespace,
                                  workload_name, workload_manifest,
                                  membership_manifest, asm_revision,
                                  mesh_config):
  """Retrieve the necessary metadata to configure the service proxy."""

  if is_mcp:
    asm_version = None
    expansionagateway_ip = None
    root_cert = None
    service_proxy_api_server = _RetrieveDiscoveryAddress(mesh_config)
    env_config = kube_client.RetrieveEnvConfig(asm_revision)
  else:
    if _GCE_SERVICE_PROXY_ASM_VERSION_METADATA in args.metadata:
      asm_version = args.metadata[_GCE_SERVICE_PROXY_ASM_VERSION_METADATA]
    else:
      asm_version = kube_client.RetrieveASMVersion(asm_revision)
    expansionagateway_ip = kube_client.RetrieveExpansionGatewayIP()
    root_cert = kube_client.RetrieveKubernetesRootCert()
    service_proxy_api_server = '{}:{}'.format(expansionagateway_ip,
                                              _ISTIO_DISCOVERY_PORT)
    env_config = None

  identity_provider = _GetVMIdentityProvider(membership_manifest,
                                             workload_namespace)

  service_account = _RetrieveWorkloadServiceAccount(workload_manifest)

  asm_proxy_config = _RetrieveProxyConfig(is_mcp, mesh_config)

  trust_domain = _RetrieveTrustDomain(is_mcp, mesh_config)

  mesh_id = _RetrieveMeshId(is_mcp, mesh_config)

  network = network_resource.split('/')[-1]

  asm_labels = _GetWorkloadLabels(workload_manifest)

  canonical_service = _GetCanonicalServiceName(workload_name, workload_manifest)

  canonical_revision = _GetCanonicalServiceRevision(workload_manifest)

  return ServiceProxyMetadataArgs(
      asm_version, project_id, expansionagateway_ip, service_proxy_api_server,
      identity_provider, service_account, asm_proxy_config, env_config,
      trust_domain, mesh_id, network, asm_labels, workload_name,
      workload_namespace, canonical_service, canonical_revision, asm_revision,
      root_cert)


def _ModifyInstanceTemplate(args, is_mcp, metadata_args):
  """Modify the instance template to include the service proxy metadata."""

  if metadata_args.asm_labels:
    asm_labels = metadata_args.asm_labels
  else:
    asm_labels = collections.OrderedDict()

  asm_labels[
      _ISTIO_CANONICAL_SERVICE_NAME_LABEL] = metadata_args.canonical_service
  asm_labels[
      _ISTIO_CANONICAL_SERVICE_REVISION_LABEL] = metadata_args.canonical_revision

  asm_labels_string = json.dumps(asm_labels, sort_keys=True)

  service_proxy_config = collections.OrderedDict()
  service_proxy_config['mode'] = 'ON'

  service_proxy_config['proxy-spec'] = {
      'network': metadata_args.network,
      'api-server': metadata_args.service_proxy_api_server,
      'log-level': 'info',
  }

  service_proxy_config['service'] = {}

  proxy_config = metadata_args.asm_proxy_config
  if not proxy_config:
    proxy_config = collections.OrderedDict()
  if 'proxyMetadata' not in proxy_config:
    proxy_config['proxyMetadata'] = collections.OrderedDict()
  else:
    proxy_config['proxyMetadata'] = collections.OrderedDict(
        proxy_config['proxyMetadata'])

  proxy_metadata = proxy_config['proxyMetadata']
  proxy_metadata['ISTIO_META_WORKLOAD_NAME'] = metadata_args.workload_name
  proxy_metadata['POD_NAMESPACE'] = metadata_args.workload_namespace
  proxy_metadata['USE_TOKEN_FOR_CSR'] = 'true'
  proxy_metadata['ISTIO_META_DNS_CAPTURE'] = 'true'
  proxy_metadata['ISTIO_META_AUTO_REGISTER_GROUP'] = metadata_args.workload_name
  proxy_metadata['SERVICE_ACCOUNT'] = metadata_args.service_account
  proxy_metadata[
      'CREDENTIAL_IDENTITY_PROVIDER'] = metadata_args.identity_provider
  if metadata_args.trust_domain:
    proxy_metadata['TRUST_DOMAIN'] = metadata_args.trust_domain
  if metadata_args.mesh_id:
    proxy_metadata['ISTIO_META_MESH_ID'] = metadata_args.mesh_id
  proxy_metadata['ISTIO_META_NETWORK'] = '{}-{}'.format(
      metadata_args.project_id, metadata_args.network)
  proxy_metadata['CANONICAL_SERVICE'] = metadata_args.canonical_service
  proxy_metadata['CANONICAL_REVISION'] = metadata_args.canonical_revision
  proxy_metadata['ISTIO_METAJSON_LABELS'] = asm_labels_string

  if metadata_args.asm_revision == 'default':
    proxy_metadata['ASM_REVISION'] = ''
  else:
    proxy_metadata['ASM_REVISION'] = metadata_args.asm_revision

  gce_software_declaration = collections.OrderedDict()
  service_proxy_agent_recipe = collections.OrderedDict()

  service_proxy_agent_recipe['name'] = 'install-gce-service-proxy-agent'
  service_proxy_agent_recipe['desired_state'] = 'INSTALLED'

  if is_mcp:
    service_proxy_agent_recipe['installSteps'] = [{
        'scriptRun': {
            'script':
                service_proxy_aux_data
                .startup_script_for_asm_service_proxy_installer
        }
    }]
    proxy_metadata.update(metadata_args.mcp_env_config)
    # ISTIO_META_CLOUDRUN_ADDR must be set to generate node metadata on VM.
    if _CLOUDRUN_ADDR_KEY in proxy_metadata:
      proxy_metadata[_ISTIO_META_CLOUDRUN_ADDR_KEY] = proxy_metadata[
          _CLOUDRUN_ADDR_KEY]
    if 'gce-service-proxy-installer-bucket' not in args.metadata:
      args.metadata['gce-service-proxy-installer-bucket'] = (
          _SERVICE_PROXY_INSTALLER_BUCKET_NAME)
  else:
    service_proxy_agent_recipe['installSteps'] = [{
        'scriptRun': {
            'script':
                service_proxy_aux_data.startup_script_for_asm_service_proxy
                .format(
                    ingress_ip=metadata_args.expansionagateway_ip,
                    asm_revision=metadata_args.asm_revision)
        }
    }]
    proxy_metadata['ISTIO_META_ISTIO_VERSION'] = metadata_args.asm_version
    args.metadata['rootcert'] = metadata_args.root_cert
    if _GCE_SERVICE_PROXY_AGENT_BUCKET_METADATA not in args.metadata:
      args.metadata[
          _GCE_SERVICE_PROXY_AGENT_BUCKET_METADATA] = (
              _SERVICE_PROXY_BUCKET_NAME.format(metadata_args.asm_version))

  gce_software_declaration['softwareRecipes'] = [service_proxy_agent_recipe]

  service_proxy_config['asm-config'] = proxy_config

  args.metadata['enable-osconfig'] = 'true'
  args.metadata['enable-guest-attributes'] = 'true'
  args.metadata['osconfig-disabled-features'] = 'tasks'
  args.metadata['gce-software-declaration'] = json.dumps(
      gce_software_declaration)
  args.metadata['gce-service-proxy'] = json.dumps(
      service_proxy_config, sort_keys=True)

  if args.labels is None:
    args.labels = collections.OrderedDict()
  args.labels['asm_service_name'] = metadata_args.canonical_service
  args.labels['asm_service_namespace'] = metadata_args.workload_namespace
  if metadata_args.mesh_id:
    args.labels['mesh_id'] = metadata_args.mesh_id
  else:
    # This works for now as we only support adding VM to the Fleet project. But
    # it should be the Fleet project instead.
    project_number = project_util.GetProjectNumber(metadata_args.project_id)
    args.labels['mesh_id'] = 'proj-{}'.format(project_number)
  # For ASM VM usage tracking.
  args.labels['gce-service-proxy'] = 'asm-istiod'


def ConfigureInstanceTemplate(args, kube_client, project_id, network_resource,
                              workload_namespace, workload_name,
                              workload_manifest, membership_manifest,
                              asm_revision, mesh_config):
  """Configure the provided instance template args with ASM metadata."""
  is_mcp = _IsMCP(kube_client, asm_revision)

  service_proxy_metadata_args = _RetrieveServiceProxyMetadata(
      args, is_mcp, kube_client, project_id, network_resource,
      workload_namespace, workload_name, workload_manifest, membership_manifest,
      asm_revision, mesh_config)

  _ModifyInstanceTemplate(args, is_mcp, service_proxy_metadata_args)


class KubernetesClient(object):
  """Kubernetes client for access Kubernetes APIs."""

  def __init__(self, gke_cluster=None):
    """KubernetesClient constructor.

    Args:
      gke_cluster: the location/name of the GKE cluster.
    """
    self.kubectl_timeout = '20s'

    self.temp_kubeconfig_dir = files.TemporaryDirectory()
    self.processor = hub_kube_util.KubeconfigProcessor(
        api_adapter=None, gke_uri=None, gke_cluster=gke_cluster,
        kubeconfig=None, internal_ip=False, cross_connect_subnetwork=None,
        private_endpoint_fqdn=None, context=None)
    self.kubeconfig, self.context = self.processor.GetKubeconfigAndContext(
        self.temp_kubeconfig_dir)

  def __enter__(self):
    return self

  def __exit__(self, *_):
    # delete temp directory
    if self.temp_kubeconfig_dir is not None:
      self.temp_kubeconfig_dir.Close()

  def HasNamespaceReaderPermissions(self, *namespaces):
    """Check to see if the user has read permissions in the namespaces.

    Args:
      *namespaces: The namespaces to verify reader permissions.

    Returns:
      true, if reads can be performed on all of the specified namespaces.

    Raises:
      Error: if failing to get check for read permissions.
      Error: if read permissions are not found.
    """
    for ns in namespaces:
      out, err = self._RunKubectl(
          ['auth', 'can-i', 'get', '*', '-n', ns], None)
      if err:
        raise exceptions.Error(
            'Failed to check if the user can read resources in {} namespace: {}'
            .format(ns, err))
      if 'yes' not in out:
        raise exceptions.Error(
            'Missing permissions to read resources in {} namespace'.format(ns))
    return True

  def NamespacesExist(self, *namespaces):
    """Check to see if the namespaces exist in the cluster.

    Args:
      *namespaces: The namespaces to check.

    Returns:
      true, if namespaces exist.

    Raises:
      Error: if failing to verify the namespaces.
      Error: if at least one of the namespaces do not exist.
    """
    for ns in namespaces:
      _, err = self._RunKubectl(['get', 'namespace', ns], None)
      if err:
        if 'NotFound' in err:
          raise exceptions.Error('Namespace {} does not exist: {}'.format(
              ns, err))
        raise exceptions.Error(
            'Failed to check if namespace {} exists: {}'.format(ns, err))
    return True

  def GetNamespace(self, namespace):
    """Get the YAML output of the specified namespace."""
    out, err = self._RunKubectl([
        'get', 'namespace', namespace, '-o', 'yaml'], None)
    if err:
      raise exceptions.Error(
          'Error retrieving Namespace {}: {}'.format(namespace, err))
    return out

  def GetMembershipCR(self):
    """Get the YAML output of the Membership CR."""
    if not self._MembershipCRDExists():
      raise ClusterError(
          'Membership CRD is not found in the cluster. Please make sure your '
          'cluster is registered and retry.')

    out, err = self._RunKubectl(
        ['get',
         'memberships.hub.gke.io',
         'membership', '-o', 'yaml'], None)
    if err:
      if 'NotFound' in err:
        raise ClusterError(
            'The specified cluster is not registered to a fleet. '
            'Please make sure your cluster is registered and retry.')
      raise exceptions.Error(
          'Error retrieving the Membership CR: {}'.format(err))
    return out

  def _MembershipCRDExists(self):
    """Verifies if GKE Hub membership CRD exists."""
    _, err = self._RunKubectl(
        ['get',
         'customresourcedefinitions.v1.apiextensions.k8s.io',
         'memberships.hub.gke.io'], None)
    if err:
      if 'NotFound' in err:
        return False
      raise exceptions.Error(
          'Error retrieving the Membership CRD: {}'.format(err))
    return True

  def GetIdentityProviderCR(self):
    """Get the YAML output of the IdentityProvider CR."""
    if not self._IdentityProviderCRDExists():
      raise ClusterError(
          'IdentityProvider CRD is not found in the cluster. Please install '
          'Anthos Service Mesh with VM support and retry.')

    out, err = self._RunKubectl(
        ['get',
         'identityproviders.security.cloud.google.com',
         'google', '-o', 'yaml'], None)
    if err:
      if 'NotFound' in err:
        raise ClusterError(
            'GCE identity provider is not found in the cluster. '
            'Please install Anthos Service Mesh with VM support.')
      raise exceptions.Error(
          'Error retrieving IdentityProvider google in default namespace: {}'
          .format(err))
    return out

  def _IdentityProviderCRDExists(self):
    """Verifies if Identity Provider CRD exists."""
    _, err = self._RunKubectl(
        ['get',
         'customresourcedefinitions.v1.apiextensions.k8s.io',
         'identityproviders.security.cloud.google.com'], None)
    if err:
      if 'NotFound' in err:
        return False
      raise exceptions.Error(
          'Error retrieving the Identity Provider CRD: {}'.format(err))
    return True

  def GetWorkloadGroupCR(self, workload_namespace, workload_name):
    """Get the YAML output of the specified WorkloadGroup CR."""
    if not self._WorkloadGroupCRDExists():
      raise ClusterError(
          'WorkloadGroup CRD is not found in the cluster. Please install '
          'Anthos Service Mesh and retry.')

    out, err = self._RunKubectl([
        'get', 'workloadgroups.networking.istio.io', workload_name, '-n',
        workload_namespace, '-o', 'yaml'
    ], None)
    if err:
      if 'NotFound' in err:
        raise WorkloadError(
            'WorkloadGroup {} in namespace {} is not found in the '
            'cluster. Please create the WorkloadGroup and retry.'.format(
                workload_name, workload_namespace))
      raise exceptions.Error(
          'Error retrieving WorkloadGroup {} in namespace {}: {}'.format(
              workload_name, workload_namespace, err))
    return out

  def _WorkloadGroupCRDExists(self):
    """Verifies if WorkloadGroup CRD exists."""
    _, err = self._RunKubectl(
        ['get',
         'customresourcedefinitions.v1.apiextensions.k8s.io',
         'workloadgroups.networking.istio.io'], None)
    if err:
      if 'NotFound' in err:
        return False
      raise exceptions.Error(
          'Error retrieving the WorkloadGroup CRD: {}'.format(err))
    return True

  def ExpansionGatewayDeploymentExists(self):
    """Verifies if the ASM Expansion Gateway deployment exists."""
    _, err = self._RunKubectl(
        ['get', 'deploy', _EXPANSION_GATEWAY_NAME, '-n', 'istio-system'], None)
    if err:
      if 'NotFound' in err:
        return False
      raise exceptions.Error(
          'Error retrieving the expansion gateway deployment: {}'.format(err))
    return True

  def ExpansionGatewayServiceExists(self):
    """Verifies if the ASM Expansion Gateway service exists."""
    _, err = self._RunKubectl(
        ['get', 'service', _EXPANSION_GATEWAY_NAME, '-n', 'istio-system'], None)
    if err:
      if 'NotFound' in err:
        return False
      raise exceptions.Error(
          'Error retrieving the expansion gateway service: {}'.format(err))
    return True

  def RetrieveExpansionGatewayIP(self):
    """Retrieves the expansion gateway IP from the cluster."""
    if not self.ExpansionGatewayDeploymentExists():
      raise ClusterError(
          'The gateway {} deployment is not found in the cluster. Please '
          'install Anthos Service Mesh with VM support and retry.'.format(
              _EXPANSION_GATEWAY_NAME))

    if not self.ExpansionGatewayServiceExists():
      raise ClusterError(
          'The gateway {} service is not found in the cluster. Please '
          'install Anthos Service Mesh with VM support and retry.'.format(
              _EXPANSION_GATEWAY_NAME))

    out, err = self._RunKubectl([
        'get', 'svc', _EXPANSION_GATEWAY_NAME, '-n', 'istio-system', '-o',
        'jsonpath={.status.loadBalancer.ingress[0].ip}'
    ], None)
    if err:
      raise exceptions.Error(
          'Error retrieving expansion gateway IP: {}'.format(err))
    return out

  def RetrieveKubernetesRootCert(self):
    """Retrieves the root cert from the cluster."""
    out, err = self._RunKubectl(
        ['get', 'configmap', 'kube-root-ca.crt', '-o',
         r'jsonpath="{.data.ca\.crt}"'], None)
    if err:
      if 'NotFound' in err:
        raise ClusterError(
            'Cluster root certificate is not found.')
      raise exceptions.Error(
          'Error retrieving Kubernetes root cert: {}'.format(err))
    return out.strip('\"')

  def RetrieveASMVersion(self, revision):
    """Retrieves the version of ASM."""
    image, err = self._RunKubectl([
        'get', 'deploy', '-l', 'istio.io/rev={},app=istiod'.format(revision),
        '-n', 'istio-system', '-o',
        'jsonpath="{.items[0].spec.template.spec.containers[0].image}"'
    ], None)
    if err:
      if 'NotFound' in err:
        raise ClusterError(
            'Anthos Service Mesh revision {} is not found in '
            'the cluster. Please install Anthos Service Mesh and '
            'try again.'.format(revision))
      raise exceptions.Error(
          'Error retrieving the version of Anthos Service Mesh: {}'.format(err))

    if not image:
      raise ClusterError('Anthos Service Mesh revision {} does not have an '
                         'image property. Please re-install Anthos Service '
                         'Mesh.'.format(revision))

    version_match = re.search(_ASM_VERSION_PATTERN, image)
    if version_match:
      return version_match.group(1)
    raise exceptions.Error(
        'Value image: {} is invalid.'.format(image))

  def RetrieveEnvConfig(self, revision):
    """Retrieves the env-* config map for MCP."""
    if revision == 'default':
      env_config_name = 'env'
    else:
      env_config_name = 'env-{}'.format(revision)

    out, err = self._RunKubectl(
        ['get', 'configmap', env_config_name, '-n', 'istio-system',
         '-o', 'jsonpath={.data}'], None)
    if err:
      if 'NotFound' in err:
        raise ClusterError(
            'Managed Control Plane revision {} is not found in '
            'the cluster. Please install Managed Control Plane and '
            'try again.'.format(revision))
      raise exceptions.Error(
          'Error retrieving the config map {} from the cluster: {}'.format(
              env_config_name, err))

    try:
      env_config = yaml.load(out)
    except yaml.Error:
      raise exceptions.Error(
          'Invalid config map from the cluster: {}'.format(out))

    return env_config

  def RetrieveMeshConfig(self, revision):
    """Retrieves the MeshConfig for the ASM revision."""
    if revision == 'default':
      mesh_config_name = 'istio'
    else:
      mesh_config_name = 'istio-{}'.format(revision)

    out, err = self._RunKubectl(
        ['get', 'configmap', mesh_config_name, '-n', 'istio-system',
         '-o', 'jsonpath={.data.mesh}'], None)
    if err:
      if 'NotFound' in err:
        raise ClusterError(
            'Anthos Service Mesh revision {} is not found in '
            'the cluster. Please install Anthos Service Mesh and '
            'try again.'.format(revision))
      raise exceptions.Error(
          'Error retrieving the mesh config from the cluster: {}'.format(
              err))

    try:
      mesh_config = yaml.load(out)
    except yaml.Error:
      raise exceptions.Error(
          'Invalid mesh config from the cluster: {}'.format(out))

    return mesh_config

  def RetrieveMutatingWebhookURL(self, revision):
    """Retrieves the Mutating Webhook URL used for a revision."""
    # There are two patterns of mutating webhook name in ASM. We check both in
    # case they are being used interchaeably.
    if revision == 'default':
      incluster_webhook = _INCLUSTER_WEBHOOK_PREFIX
    else:
      incluster_webhook = '{}-{}'.format(_INCLUSTER_WEBHOOK_PREFIX, revision)

    mcp_webhook = '{}-{}'.format(_MCP_WEBHOOK_PREFIX, revision)

    incluster_out, incluster_err = self._RunKubectl(
        ['get', 'mutatingwebhookconfiguration', incluster_webhook,
         '-o', 'jsonpath={.webhooks[0].clientConfig.url}'], None)
    mcp_out, mcp_err = self._RunKubectl(
        ['get', 'mutatingwebhookconfiguration', mcp_webhook,
         '-o', 'jsonpath={.webhooks[0].clientConfig.url}'], None)

    if incluster_err and mcp_err:
      if 'NotFound' in incluster_err and 'NotFound' in mcp_err:
        raise ClusterError(
            'Anthos Service Mesh revision {} is not found in '
            'the cluster. Please install Anthos Service Mesh and '
            'try again.'.format(revision))
      raise exceptions.Error(
          'Error retrieving the mutating webhook configuration from the cluster'
          ': {}'.format(incluster_err))

    if incluster_out:
      return incluster_out
    return mcp_out

  def _RunKubectl(self, args, stdin=None):
    """Runs a kubectl command with the cluster referenced by this client.

    Args:
      args: command line arguments to pass to kubectl
      stdin: text to be passed to kubectl via stdin

    Returns:
      The contents of stdout if the return code is 0, stderr (or a fabricated
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

    if returncode != 0 and not err.getvalue():
      err.write('kubectl exited with return code {}'.format(returncode))

    return out.getvalue() if returncode == 0 else None, err.getvalue(
    ) if returncode != 0 else None


def _GetNestedKeyFromManifest(manifest, *keys):
  """Get the value of a key path from a dict.

  Args:
    manifest: the dict representation of a manifest
    *keys: an ordered list of items in the nested key

  Returns:
    The value of the nested key in the manifest. None, if the nested key does
    not exist.
  """
  for key in keys:
    if not isinstance(manifest, dict):
      return None
    try:
      manifest = manifest[key]
    except KeyError:
      return None
  return manifest


class PermissionsError(exceptions.Error):
  """Class for errors raised when verifying permissions."""


class ClusterError(exceptions.Error):
  """Class for errors raised when verifying cluster setup."""


class WorkloadError(exceptions.Error):
  """Class for errors raised when verifying workload setup."""
