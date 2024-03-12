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
"""Command to register an Attached cluster with the fleet.

This command performs the full end-to-end steps required to attach a cluster.
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import json

from googlecloudsdk.api_lib.container.gkemulticloud import attached as api_util
from googlecloudsdk.api_lib.container.gkemulticloud import locations as loc_util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.container.attached import cluster_util
from googlecloudsdk.command_lib.container.attached import flags as attached_flags
from googlecloudsdk.command_lib.container.attached import resource_args
from googlecloudsdk.command_lib.container.fleet import kube_util
from googlecloudsdk.command_lib.container.gkemulticloud import command_util
from googlecloudsdk.command_lib.container.gkemulticloud import constants
from googlecloudsdk.command_lib.container.gkemulticloud import endpoint_util
from googlecloudsdk.command_lib.container.gkemulticloud import errors
from googlecloudsdk.command_lib.container.gkemulticloud import flags
from googlecloudsdk.command_lib.run import pretty_print
from googlecloudsdk.core import exceptions
from googlecloudsdk.core.console import console_io
from googlecloudsdk.core.util import retry
import six

# Command needs to be in one line for the docgen tool to format properly.
_EXAMPLES = """
Register a cluster to a fleet.

To register a cluster with a private OIDC issuer, run:

$ {command} my-cluster --location=us-west1 --platform-version=PLATFORM_VERSION --fleet-project=FLEET_PROJECT_NUM --distribution=DISTRIBUTION --context=CLUSTER_CONTEXT --has-private-issuer

To register a cluster with a public OIDC issuer, run:

$ {command} my-cluster --location=us-west1 --platform-version=PLATFORM_VERSION --fleet-project=FLEET_PROJECT_NUM --distribution=DISTRIBUTION --context=CLUSTER_CONTEXT --issuer-url=https://ISSUER_URL

To specify a kubeconfig file, run:

$ {command} my-cluster --location=us-west1 --platform-version=PLATFORM_VERSION --fleet-project=FLEET_PROJECT_NUM --distribution=DISTRIBUTION --context=CLUSTER_CONTEXT --has-private-issuer --kubeconfig=KUBECONFIG_PATH

To register and set cluster admin users, run:

$ {command} my-cluster --location=us-west1 --platform-version=PLATFORM_VERSION --fleet-project=FLEET_PROJECT_NUM --distribution=DISTRIBUTION --context=CLUSTER_CONTEXT --issuer-url=https://ISSUER_URL --admin-users=USER1,USER2
"""


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.GA)
class Register(base.CreateCommand):
  """Register an Attached cluster."""

  detailed_help = {'EXAMPLES': _EXAMPLES}

  @staticmethod
  def Args(parser):
    """Registers flags for this command."""
    resource_args.AddAttachedClusterResourceArg(parser, 'to register')

    attached_flags.AddPlatformVersion(parser)
    attached_flags.AddRegisterOidcConfig(parser)
    attached_flags.AddDistribution(parser, required=True)
    attached_flags.AddAdminUsers(parser)
    attached_flags.AddKubectl(parser)
    attached_flags.AddProxyConfig(parser)

    flags.AddAnnotations(parser)
    flags.AddValidateOnly(parser, 'cluster to create')
    flags.AddFleetProject(parser)
    flags.AddDescription(parser)
    flags.AddLogging(parser, True)
    flags.AddMonitoringConfig(parser, True)
    flags.AddBinauthzEvaluationMode(parser)
    flags.AddAdminGroups(parser)

    parser.display_info.AddFormat(constants.ATTACHED_CLUSTERS_FORMAT)

  def Run(self, args):
    location = resource_args.ParseAttachedClusterResourceArg(args).locationsId
    with endpoint_util.GkemulticloudEndpointOverride(location):
      cluster_ref = resource_args.ParseAttachedClusterResourceArg(args)
      manifest = self._get_manifest(args, cluster_ref)

      with kube_util.KubernetesClient(
          kubeconfig=attached_flags.GetKubeconfig(args),
          context=attached_flags.GetContext(args),
          enable_workload_identity=True,
      ) as kube_client:
        kube_client.CheckClusterAdminPermissions()

        if attached_flags.GetHasPrivateIssuer(args):
          pretty_print.Info('Fetching cluster OIDC information')
          issuer_url, jwks = self._get_authority(kube_client)
          setattr(args, 'issuer_url', issuer_url)
          setattr(args, 'oidc_jwks', jwks)

        try:
          if not flags.GetValidateOnly(args):
            pretty_print.Info('Creating in-cluster install agent')
            kube_client.Apply(manifest)
            retryer = retry.Retryer(
                max_retrials=constants.ATTACHED_INSTALL_AGENT_VERIFY_RETRIES
            )
            retryer.RetryOnException(
                cluster_util.verify_install_agent_deployed,
                args=(kube_client,),
                sleep_ms=constants.ATTACHED_INSTALL_AGENT_VERIFY_WAIT_MS,
            )

          create_resp = self._create_attached_cluster(args, cluster_ref)
        except retry.RetryException as e:
          self._remove_manifest(args, kube_client, manifest)
          # last_result[1] holds information about the last exception the
          # retryer caught. last_result[1][1] holds the exception type and
          # last_result[1][2] holds the exception value. The retry exception is
          # not useful to users, so reraise whatever error caused it to timeout.
          if e.last_result[1]:
            exceptions.reraise(e.last_result[1][1], e.last_result[1][2])
          raise
        except console_io.OperationCancelledError:
          msg = """To manually clean up the in-cluster install agent, run:

$ gcloud container attached clusters generate-install-manifest --location={} --platform-version={} --format="value(manifest)"  {}  | kubectl delete -f -

AFTER the attach operation completes.
""".format(
              location,
              attached_flags.GetPlatformVersion(args),
              cluster_ref.attachedClustersId,
          )
          pretty_print.Info(msg)
          raise
        except:  # pylint: disable=broad-except
          self._remove_manifest(args, kube_client, manifest)
          raise

        self._remove_manifest(args, kube_client, manifest)

      return create_resp

  def _get_manifest(self, args, cluster_ref):
    location_client = loc_util.LocationsClient()
    resp = location_client.GenerateInstallManifest(cluster_ref, args=args)
    return resp.manifest

  def _remove_manifest(self, args, kube_client, manifest):
    if not flags.GetValidateOnly(args):
      pretty_print.Info('Deleting in-cluster install agent')
      kube_client.Delete(manifest)

  def _get_authority(self, kube_client):
    openid_config_json = six.ensure_str(
        kube_client.GetOpenIDConfiguration(), encoding='utf-8'
    )
    issuer_url = json.loads(openid_config_json).get('issuer')
    if not issuer_url:
      raise errors.MissingOIDCIssuerURL(openid_config_json)
    jwks = kube_client.GetOpenIDKeyset()
    return issuer_url, jwks

  def _create_attached_cluster(self, args, cluster_ref):
    cluster_client = api_util.ClustersClient()
    message = command_util.ClusterMessage(
        cluster_ref.attachedClustersId,
        action='Creating',
        kind=constants.ATTACHED,
    )
    return command_util.Create(
        resource_ref=cluster_ref,
        resource_client=cluster_client,
        args=args,
        message=message,
        kind=constants.ATTACHED_CLUSTER_KIND,
    )
