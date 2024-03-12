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
"""The register command for registering a clusters with the fleet."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import json
import textwrap

from apitools.base.py import exceptions as apitools_exceptions
from googlecloudsdk.api_lib.container import api_adapter as gke_api_adapter
from googlecloudsdk.api_lib.util import exceptions as core_api_exceptions
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.container import flags
from googlecloudsdk.command_lib.container.fleet import agent_util
from googlecloudsdk.command_lib.container.fleet import api_util
from googlecloudsdk.command_lib.container.fleet import exclusivity_util
from googlecloudsdk.command_lib.container.fleet import kube_util
from googlecloudsdk.command_lib.container.fleet import resources
from googlecloudsdk.command_lib.container.fleet import util as hub_util
from googlecloudsdk.command_lib.container.fleet.memberships import gke_util
from googlecloudsdk.command_lib.util.apis import arg_utils
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core.console import console_io
from googlecloudsdk.core.util import files
import six

SERVICE_ACCOUNT_KEY_FILE_FLAG = '--service-account-key-file'
DOCKER_CREDENTIAL_FILE_FLAG = '--docker-credential-file'


def _ValidateConnectAgentCredentialFlags(args):
  enable_workload_identity = getattr(args, 'enable_workload_identity', False)
  if not args.service_account_key_file and not enable_workload_identity:
    raise exceptions.Error(
        '--enable-workload-identity --service-account-key-file',
        'One of (--enable-workload-identity | --service-account-key-file) ' +
        'must be specified for Connect agent authentication.')


class Register(base.CreateCommand):
  r"""Register a cluster with a fleet.

  This command registers a cluster with the fleet by:

    1. Creating a Fleet Membership resource corresponding to the cluster.
    2. Adding in-cluster Kubernetes Resources that make the cluster exclusive
       to one fleet.
    3. Installing the Connect agent into this cluster (optional for GKE).

  A successful registration implies that the cluster is now exclusive to a
  single Fleet. If the cluster is already registered to another Fleet, the
  registration will not be successful.

  To register a GKE cluster, use `--gke-cluster` or `--gke-uri` flag (no
  `--kubeconfig` flag is required). Connect agent will not be installed by
  default for GKE clusters. To install it, specify `--install-connect-agent`.
  The default value for `--location` is the same as the cluster's region or zone,
  can be specified as `global`.

  Anthos clusters on VMware, bare metal, AWS, and Azure are registered
  with a fleet when the clusters are created. To register Amazon EKS
  clusters, see
  [Attach your EKS cluster](https://cloud.google.com/anthos/clusters/docs/multi-cloud/attached/eks/how-to/attach-cluster).
  To regiser Microsoft Azure clusters, see
  [Attach your AKS cluster](https://cloud.google.com/anthos/clusters/docs/multi-cloud/attached/aks/how-to/attach-cluster).

  To register a third-party cluster, use --context flag (with an optional
  --kubeconfig flag). Connect agent will always be installed for these
  clusters.

  If Connect agent is to be installed, its authentication needs to be configured
  by `--enable-workload-identity` or `--service-account-key-file`. For the
  latter case, the corresponding service account must have been granted
  `gkehub.connect` permissions. For more information about Connect agent, go to:
  https://cloud.google.com/anthos/multicluster-management/connect/overview/

  Rerunning this command against the same cluster with the same MEMBERSHIP_NAME
  and target fleet is successful, and will upgrade the Connect agent if it is
  supposed to be installed and a newer version is avaible.

  ## EXAMPLES

    Register a non-GKE cluster referenced from a specific
    kubeconfig file, and install the Connect agent:

      $ {command} my-cluster \
        --context=my-cluster-context \
        --kubeconfig=/home/user/custom_kubeconfig \
        --service-account-key-file=/tmp/keyfile.json

    Register a non-GKE cluster referenced from the default
    kubeconfig file, and install the Connect agent:

      $ {command} my-cluster \
        --context=my-cluster-context \
        --service-account-key-file=/tmp/keyfile.json

    Register a non-GKE cluster, and install a specific version
    of the Connect agent:

      $ {command} my-cluster \
        --context=my-cluster-context \
        --version=gkeconnect_20190802_02_00 \
        --service-account-key-file=/tmp/keyfile.json

    Register a non-GKE cluster and output a manifest that can be used to
    install the Connect agent by kubectl:

      $ {command} my-cluster \
        --context=my-cluster-context \
        --manifest-output-file=/tmp/manifest.yaml \
        --service-account-key-file=/tmp/keyfile.json

    Register a GKE cluster referenced from a GKE URI:

      $ {command} my-cluster \
        --gke-uri=my-cluster-gke-uri

    Register a GKE cluster referenced from a GKE URI, and install the Connect
    agent using service account key file:

      $ {command} my-cluster \
        --gke-uri=my-cluster-gke-uri \
        --install-connect-agent \
        --service-account-key-file=/tmp/keyfile.json

    Register a GKE cluster and output a manifest that can be used to
    install the Connect agent by kubectl:

      $ {command} my-cluster \
        --gke-uri=my-cluster-gke-uri \
        --enable-workload-identity \
        --install-connect-agent \
        --manifest-output-file=/tmp/manifest.yaml

    Register a GKE cluster first, and install the Connect agent later.

      $ {command} my-cluster \
        --gke-cluster=my-cluster-region-or-zone/my-cluster

      $ {command} my-cluster \
        --gke-cluster=my-cluster-region-or-zone/my-cluster \
        --install-connect-agent \
        --enable-workload-identity

    Register a GKE cluster, and install a specific version of the Connect
    agent:

      $ {command} my-cluster \
        --gke-cluster=my-cluster-region-or-zone/my-cluster \
        --install-connect-agent \
        --version=20220819-00-00 \
        --service-account-key-file=/tmp/keyfile.json

    Register a GKE cluster and output a manifest that can be used to install the
    Connect agent:

      $ {command} my-cluster \
        --gke-uri=my-cluster-gke-uri \
        --install-connect-agent \
        --manifest-output-file=/tmp/manifest.yaml \
        --service-account-key-file=/tmp/keyfile.json
  """

  @classmethod
  def Args(cls, parser):
    resources.AddMembershipResourceArg(
        parser,
        membership_help=textwrap.dedent("""\
          The membership name that you choose to uniquely represents the cluster
          being registered in the fleet.
        """),
        location_help=textwrap.dedent("""\
          The location for the membership resource, e.g. `us-central1`.
          If not specified, defaults to `global`. Not supported for GKE clusters,
          whose membership location will be the location of the cluster.
        """),
        membership_required=True,
        positional=True)
    hub_util.AddClusterConnectionCommonArgs(parser)
    parser.add_argument(
        '--install-connect-agent',
        action='store_true',
        help=textwrap.dedent("""\
          If set to True for a GKE cluster, Connect agent will be installed in
          the cluster. No-op for Non-GKE clusters, where Connect agent will
          always be installed.
          """),
        default=False,
    )
    parser.add_argument(
        '--manifest-output-file',
        type=str,
        help=textwrap.dedent("""\
            The full path of the file into which the Connect agent installation
            manifest should be stored. If this option is provided, then the
            manifest will be written to this file and will not be deployed into
            the cluster by gcloud, and it will need to be deployed manually.
          """),
    )
    parser.add_argument(
        '--proxy',
        type=str,
        help=textwrap.dedent("""\
            The proxy address in the format of http[s]://{hostname}. The proxy
            must support the HTTP CONNECT method in order for this connection to
            succeed.
          """),
    )
    parser.add_argument(
        '--version',
        type=str,
        hidden=True,
        help=textwrap.dedent("""\
          The version of the Connect agent to install/upgrade if not using the
          latest connect version.
          """),
    )
    parser.add_argument(
        DOCKER_CREDENTIAL_FILE_FLAG,
        type=str,
        hidden=True,
        help=textwrap.dedent("""\
          The credentials to be used if a private registry is provided and auth
          is required. The contents of the file will be stored into a Secret and
          referenced from the imagePullSecrets of the Connect agent workload.
          """),
    )
    parser.add_argument(
        '--docker-registry',
        type=str,
        hidden=True,
        help=textwrap.dedent("""\
        The registry to pull GKE Connect agent image if not using gcr.io/gkeconnect.
          """),
    )
    parser.add_argument(
        '--internal-ip',
        help='Whether to use the internal IP address of the cluster endpoint.',
        action='store_true')
    if cls.ReleaseTrack() is not base.ReleaseTrack.GA:
      parser.add_argument(
          '--cross-connect-subnetwork',
          hidden=True,
          help='full path of cross connect subnet whose endpoint to persist')
      parser.add_argument(
          '--private-endpoint-fqdn',
          help='whether to persist the private fqdn',
          hidden=True,
          default=None,
          action='store_true')
    credentials = parser.add_mutually_exclusive_group()
    credentials.add_argument(
        SERVICE_ACCOUNT_KEY_FILE_FLAG,
        type=str,
        help=textwrap.dedent("""\
            The JSON file of a Google Cloud service account private key. This
            service account key is stored as a secret named ``creds-gcp'' in
            gke-connect namespace. To update the ``creds-gcp'' secret in
            gke-connect namespace with a new service account key file, run the
            following command:

            kubectl delete secret creds-gcp -n gke-connect

            kubectl create secret generic creds-gcp -n gke-connect --from-file=creds-gcp.json=/path/to/file
         """),
    )

    # Optional groups with required arguments are "modal,"
    # meaning that if any of the required arguments is specified,
    # all are required.
    workload_identity = credentials.add_group(help='Workload Identity')
    workload_identity.add_argument(
        '--enable-workload-identity',
        required=True,
        action='store_true',
        help=textwrap.dedent("""\
          Enable Workload Identity when registering the cluster with a fleet.
          Ensure that GKE Workload Identity is enabled on your GKE cluster, it
          is a requirement for using Workload Identity with memberships. Refer
          to the `Enable GKE Workload Identity` section in
          https://cloud.google.com/kubernetes-engine/docs/how-to/workload-identity#enable
          --service_account_key_file flag should not be set if this is set.
          """),
    )
    workload_identity_mutex = workload_identity.add_group(mutex=True)
    workload_identity_mutex.add_argument(
        '--public-issuer-url',
        type=str,
        help=textwrap.dedent("""\
          Skip auto-discovery and register the cluster with this issuer URL.
          Use this option when the OpenID Provider Configuration and associated
          JSON Web Key Set for validating the cluster's service account JWTs
          are served at a public endpoint different from the cluster API server.
          Requires --enable-workload-identity.
          """),
    )

    workload_identity_mutex.add_argument(
        '--has-private-issuer',
        action='store_true',
        help=textwrap.dedent("""\
          Set to true for clusters where no publicly-routable OIDC discovery
          endpoint for the Kubernetes service account token issuer exists.

          When set to true, the gcloud command-line tool will read the
          private issuer URL and JSON Web Key Set (JWKS) (public keys) for
          validating service account tokens from the cluster's API server
          and upload both when creating the Membership. Google Cloud Platform
          will then use the JWKS, instead of a public OIDC endpoint,
          to validate service account tokens issued by this cluster.
          Note the JWKS establishes the uniqueness of issuers in this
          configuration, but issuer claims in tokens are still compared to the
          issuer URL associated with the Membership when validating tokens.

          Note the cluster's OIDC discovery endpoints
          (https://[KUBE-API-ADDRESS]/.well-known/openid-configuration and
          https://[KUBE-API-ADDRESS]/openid/v1/jwks) must still be
          network-accessible to the gcloud client running this command.
          """),
    )

  def Run(self, args):
    project = arg_utils.GetFromNamespace(args, '--project', use_defaults=True)
    # This incidentally verifies that the kubeconfig and context args are valid.
    if self.ReleaseTrack() is base.ReleaseTrack.BETA or self.ReleaseTrack(
    ) is base.ReleaseTrack.ALPHA:
      api_adapter = gke_api_adapter.NewAPIAdapter('v1beta1')
    else:
      api_adapter = gke_api_adapter.NewAPIAdapter('v1')

    location = 'global'

    # Allow attempting to override location for register
    # e.g. in case of global GKE cluster memberships
    if args.location:
      location = args.location
    elif hub_util.LocationFromGKEArgs(args):
      location = hub_util.LocationFromGKEArgs(args)

    # Register GKE cluster with simple Add-to-Hub API call. Connect agent will
    # not get installed. And Kubernetes Client is not needed.
    gke_cluster_resource_link, gke_cluster_uri = gke_util.GetGKEClusterResoureLinkAndURI(
        gke_uri=args.GetValue('gke_uri'),
        gke_cluster=args.GetValue('gke_cluster'))
    manifest_path = args.GetValue('manifest_output_file')
    if (
        gke_cluster_resource_link
        and manifest_path
        and not args.GetValue('install_connect_agent')
    ):
      raise exceptions.Error(
          'For GKE clusters,  "manifest-output-file" should be specified'
          ' together with "install-connect-agent".  '
      )
    if gke_cluster_resource_link and not args.GetValue('install_connect_agent'):
      return self._RegisterGKE(gke_cluster_resource_link, gke_cluster_uri,
                               project, location, args)

    # Register non-GKE cluster, or GKE with --install-connect-agent.
    # It will require a kube client.
    _ValidateConnectAgentCredentialFlags(args)
    with kube_util.KubernetesClient(
        api_adapter=api_adapter,
        gke_uri=getattr(args, 'gke_uri', None),
        gke_cluster=getattr(args, 'gke_cluster', None),
        kubeconfig=getattr(args, 'kubeconfig', None),
        internal_ip=getattr(args, 'internal_ip', False),
        cross_connect_subnetwork=getattr(args, 'cross_connect_subnetwork',
                                         None),
        private_endpoint_fqdn=getattr(args, 'private_endpoint_fqdn', None),
        context=getattr(args, 'context', None),
        public_issuer_url=getattr(args, 'public_issuer_url', None),
        enable_workload_identity=getattr(args, 'enable_workload_identity',
                                         False),
    ) as kube_client:
      kube_client.CheckClusterAdminPermissions()
      kube_util.ValidateClusterIdentifierFlags(kube_client, args)
      if self.ReleaseTrack() is not base.ReleaseTrack.GA:
        flags.VerifyGetCredentialsFlags(args)
      uuid = kube_util.GetClusterUUID(kube_client)
      # Read the service account files provided in the arguments early, in order
      # to catch invalid files before performing mutating operations.
      # Service Account key file is required if Workload Identity is not
      # enabled.
      # If Workload Identity is enabled, then the Connect agent uses
      # a Kubernetes Service Account token instead and hence a Google Cloud
      # Platform Service Account key is not required.
      service_account_key_data = ''
      if args.service_account_key_file:
        try:
          service_account_key_data = hub_util.Base64EncodedFileContents(
              args.service_account_key_file)
        except files.Error as e:
          raise exceptions.Error('Could not process {}: {}'.format(
              SERVICE_ACCOUNT_KEY_FILE_FLAG, e))

      docker_credential_data = None
      if args.docker_credential_file:
        try:
          file_content = files.ReadBinaryFileContents(
              files.ExpandHomeDir(args.docker_credential_file))
          docker_credential_data = six.ensure_str(
              file_content, encoding='utf-8')
        except files.Error as e:
          raise exceptions.Error('Could not process {}: {}'.format(
              DOCKER_CREDENTIAL_FILE_FLAG, e))

      gke_cluster_self_link = kube_client.processor.gke_cluster_self_link
      issuer_url = None
      private_keyset_json = None
      if args.enable_workload_identity:
        # public_issuer_url can be None or given by user or gke_cluster_uri
        # (incase of a gke cluster).
        # args.public_issuer_url takes precedence over gke_cluster_uri.
        public_issuer_url = (
            args.public_issuer_url
            or kube_client.processor.gke_cluster_uri
            or None
        )

        try:
          openid_config_json = six.ensure_str(
              kube_client.GetOpenIDConfiguration(issuer_url=public_issuer_url),
              encoding='utf-8')
        except Exception as e:  # pylint: disable=broad-except
          raise exceptions.Error(
              'Error getting the OpenID Provider Configuration: '
              '{}'.format(e))

        # Extract the issuer URL from the discovery doc.
        issuer_url = json.loads(openid_config_json).get('issuer')
        if not issuer_url:
          raise exceptions.Error(
              'Invalid OpenID Config: '
              'missing issuer: {}'.format(openid_config_json))
        # Ensure public_issuer_url (only non-empty) matches what came back in
        # the discovery doc.
        if public_issuer_url and (public_issuer_url != issuer_url):
          raise exceptions.Error('--public-issuer-url {} did not match issuer '
                                 'returned in discovery doc: {}'.format(
                                     public_issuer_url, issuer_url))

        # In the private issuer case, we set private_keyset_json,
        # which is used later to upload the JWKS
        # in the Fleet Membership.
        if args.has_private_issuer:
          private_keyset_json = kube_client.GetOpenIDKeyset()

      # Attempt to create a membership.
      already_exists = False

      obj = None
      # For backward compatiblity, check if a membership was previously created
      # using the cluster uuid.
      parent = api_util.ParentRef(project, location)
      membership_id = uuid
      resource_name = api_util.MembershipRef(project, location, uuid)
      obj = self._CheckMembershipWithUUID(resource_name, args.MEMBERSHIP_NAME)

      # get api version version to pass into create/update membership
      api_server_version = kube_util.GetClusterServerVersion(kube_client)
      if obj:
        # The membership exists and has the same description.
        already_exists = True
      else:
        # Attempt to create a new membership using MEMBERSHIP_NAME.
        membership_id = args.MEMBERSHIP_NAME
        resource_name = api_util.MembershipRef(project, location,
                                               args.MEMBERSHIP_NAME)
        try:
          self._VerifyClusterExclusivity(kube_client, parent, membership_id)
          obj = api_util.CreateMembership(project, args.MEMBERSHIP_NAME,
                                          args.MEMBERSHIP_NAME, location,
                                          gke_cluster_self_link, uuid,
                                          self.ReleaseTrack(), issuer_url,
                                          private_keyset_json,
                                          api_server_version)
          # Generate CRD Manifest should only be called afer create/update.
          self._InstallOrUpdateExclusivityArtifacts(kube_client, resource_name)
        except apitools_exceptions.HttpConflictError as e:
          # If the error is not due to the object already existing, re-raise.
          error = core_api_exceptions.HttpErrorPayload(e)
          if error.status_description != 'ALREADY_EXISTS':
            raise
          obj = api_util.GetMembership(resource_name, self.ReleaseTrack())
          if not obj.externalId:
            raise exceptions.Error(
                'invalid membership {0} does not have '
                'external_id field set. We cannot determine '
                'if registration is requested against a '
                'valid existing Membership. Consult the '
                'documentation on container fleet memberships '
                'update for more information or run gcloud '
                'container fleet memberships delete {0} if you '
                'are sure that this is an invalid or '
                'otherwise stale Membership'.format(membership_id))
          if obj.externalId != uuid:
            raise exceptions.Error(
                'membership {0} already exists in the project'
                ' with another cluster. If this operation is'
                ' intended, please run `gcloud container '
                'fleet memberships delete {0}` and register '
                'again.'.format(membership_id))

          # The membership exists with same MEMBERSHIP_NAME.
          already_exists = True

      # In case of an existing membership, check with the user to upgrade the
      # Connect-Agent.
      if already_exists:
        # Update Membership when required. Scenarios that require updates:
        # 1. membership.authority is set, but there is now no issuer URL.
        #    This means the user is disabling Workload Identity.
        # 2. membership.authority is not set, but there is now an
        #    issuer URL. This means the user is enabling Workload Identity.
        # 3. membership.authority is set, but the issuer URL is different
        #    from that set in membership.authority.issuer. This is technically
        #    an error, but we defer to validation in the API.
        # 4. membership.authority.oidcJwks is set, but the private keyset
        #    we got from the cluster differs from the keyset in the membership.
        #    This means the user is updating the public keys, and we should
        #    update to the latest keyset in the membership.
        if (  # scenario 1, disabling WI
            (obj.authority and not issuer_url) or
            # scenario 2, enabling WI
            (issuer_url and not obj.authority) or
            (obj.authority and
             # scenario 3, issuer changed
             ((obj.authority.issuer != issuer_url) or
              # scenario 4, JWKS changed
              (private_keyset_json and obj.authority.oidcJwks and
               (obj.authority.oidcJwks.decode('utf-8') != private_keyset_json))
             ))):
          console_io.PromptContinue(
              message=hub_util.GenerateWIUpdateMsgString(
                  obj, issuer_url, resource_name, args.MEMBERSHIP_NAME),
              cancel_on_no=True)
          try:
            api_util.UpdateMembership(
                resource_name,
                obj,
                'authority',
                self.ReleaseTrack(),
                issuer_url=issuer_url,
                oidc_jwks=private_keyset_json)
            # Generate CRD Manifest should only be called afer create/update.
            self._InstallOrUpdateExclusivityArtifacts(kube_client,
                                                      resource_name)
            log.status.Print(
                'Updated the membership [{}] for the cluster [{}]'.format(
                    resource_name, args.MEMBERSHIP_NAME))
          except Exception as e:
            raise exceptions.Error(
                'Error in updating the membership [{}]:{}'.format(
                    resource_name, e))
        else:
          console_io.PromptContinue(
              message='A membership [{}] for the cluster [{}] already exists. '
              'Continuing will reinstall the Connect agent deployment to use a '
              'new image (if one is available).'.format(resource_name,
                                                        args.MEMBERSHIP_NAME),
              cancel_on_no=True)
      else:
        log.status.Print(
            'Created a new membership [{}] for the cluster [{}]'.format(
                resource_name, args.MEMBERSHIP_NAME))

      # Attempt to update the existing agent deployment, or install a new agent
      # if necessary.
      try:
        agent_util.DeployConnectAgent(kube_client, args,
                                      service_account_key_data,
                                      docker_credential_data, resource_name,
                                      self.ReleaseTrack())
      except Exception as e:
        log.status.Print('Error in installing the Connect agent: {}'.format(e))
        # In case of a new membership, we need to clean up membership and
        # resources if we failed to install the Connect agent.
        if not already_exists:
          api_util.DeleteMembership(resource_name, self.ReleaseTrack())
          exclusivity_util.DeleteMembershipResources(kube_client)
        raise
      log.status.Print(
          'Finished registering the cluster [{}] with the fleet.'.format(
              args.MEMBERSHIP_NAME))
      return obj

  def _CheckMembershipWithUUID(self, resource_name, membership_name):
    """Checks for an existing Membership with UUID.

    In the past, by default we used Cluster UUID to create a membership. Now
    we use user supplied membership_name. This check ensures that we don't
    reregister a cluster.

    Args:
      resource_name: The full membership resource name using the cluster uuid.
      membership_name: User supplied membership_name.

    Returns:
     The Membership resource or None.

    Raises:
      exceptions.Error: If it fails to getMembership.
    """
    obj = None
    try:
      obj = api_util.GetMembership(resource_name, self.ReleaseTrack())
      if (hasattr(obj, 'description') and obj.description != membership_name):
        # A membership exists, but does not have the same membership_name.
        # This is possible if two different users attempt to register the same
        # cluster, or if the user is upgrading and has passed a different
        # membership_name. Treat this as an error: even in the upgrade case,
        # this is useful to prevent the user from upgrading the wrong cluster.
        raise exceptions.Error(
            'There is an existing membership, [{}], that conflicts with [{}]. '
            'Please delete it before continuing:\n\n'
            '  gcloud {}container fleet memberships delete {}'.format(
                obj.description, membership_name,
                hub_util.ReleaseTrackCommandPrefix(self.ReleaseTrack()),
                resource_name))
    except apitools_exceptions.HttpNotFoundError:
      # We couldn't find a membership with uuid, so it's safe to create a
      # new one.
      pass
    return obj

  def _VerifyClusterExclusivity(self, kube_client, parent, membership_id):
    """Verifies that the cluster can be registered to the project.

    Args:
      kube_client: a KubernetesClient
      parent: the parent collection the user is attempting to register the
        cluster with.
      membership_id: the ID of the membership to be created for the cluster.

    Raises:
      apitools.base.py.HttpError: if the API request returns an HTTP error.
      exceptions.Error: if the cluster is in an invalid exclusivity state.
    """

    cr_manifest = ''
    # The cluster has been registered.
    if kube_client.MembershipCRDExists():
      cr_manifest = kube_client.GetMembershipCR()

    res = api_util.ValidateExclusivity(cr_manifest, parent, membership_id,
                                       self.ReleaseTrack())

    if res.status.code:
      raise exceptions.Error(
          'Error validating cluster\'s exclusivity state '
          'with the Fleet under parent collection [{}]: {}. '
          'Cannot proceed with the cluster registration.'.format(
              parent, res.status.message))

  def _InstallOrUpdateExclusivityArtifacts(self, kube_client, membership_ref):
    """Install the exclusivity artifacts for the cluster.

    Update the exclusivity artifacts if a new version is available if the
    cluster has already being registered.

    Args:
      kube_client: a KubernetesClient
      membership_ref: the full resource name of the membership the cluster is
        registered with.

    Raises:
      apitools.base.py.HttpError: if the API request returns an HTTP error.
      exceptions.Error: if the kubectl interation with the cluster failed.
    """
    crd_manifest = kube_client.GetMembershipCRD()
    cr_manifest = kube_client.GetMembershipCR() if crd_manifest else ''
    res = api_util.GenerateExclusivityManifest(crd_manifest, cr_manifest,
                                               membership_ref)
    kube_client.ApplyMembership(res.crdManifest, res.crManifest)

  def _RegisterGKE(self, gke_cluster_resource_link, gke_cluster_uri, project,
                   location, args):
    """Register a GKE cluster without installing Connect agent."""
    obj = None
    issuer_url = None
    if args.enable_workload_identity:
      issuer_url = gke_cluster_uri
    try:
      obj = api_util.CreateMembership(
          project=project,
          membership_id=args.MEMBERSHIP_NAME,
          description=args.MEMBERSHIP_NAME,
          location=location,
          gke_cluster_self_link=gke_cluster_resource_link,
          external_id=None,
          release_track=self.ReleaseTrack(),
          issuer_url=issuer_url,
          oidc_jwks=None,
          api_server_version=None)
    except apitools_exceptions.HttpConflictError as e:
      error = core_api_exceptions.HttpErrorPayload(e)
      if error.status_description != 'ALREADY_EXISTS':
        # If the error is not due to the object already existing, re-raise.
        raise
      resource_name = api_util.MembershipRef(project, location,
                                             args.MEMBERSHIP_NAME)
      obj = api_util.GetMembership(resource_name, self.ReleaseTrack())
      if obj.endpoint.gkeCluster.resourceLink == gke_cluster_resource_link:
        log.status.Print(
            'Membership [{}] already registered with the cluster [{}] in the Fleet.'
            .format(resource_name, obj.endpoint.gkeCluster.resourceLink))
      else:
        raise exceptions.Error(
            'membership [{}] already exists in the Fleet '
            'with another cluster link [{}]. If this operation is '
            'intended, please delete the membership and register '
            'again.'.format(resource_name,
                            obj.endpoint.gkeCluster.resourceLink))

    log.status.Print('Finished registering to the Fleet.')
    return obj
