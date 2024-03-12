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
"""Command to import an Attached cluster."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

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
from googlecloudsdk.command_lib.container.gkemulticloud import flags
from googlecloudsdk.command_lib.run import pretty_print
from googlecloudsdk.core import exceptions
from googlecloudsdk.core.console import console_io
from googlecloudsdk.core.util import retry
import six

_EXAMPLES = """
To import the fleet membership of an attached cluster in fleet ``FLEET_MEMBERSHIP'' managed in location ``us-west1'', run:

$ {command} --location=us-west1 --platform-version=PLATFORM_VERSION --fleet-membership=FLEET_MEMBERSHIP --distribution=DISTRIBUTION --context=CLUSTER_CONTEXT --kubeconfig=KUBECONFIG_PATH
"""


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.GA)
class Import(base.Command):
  """Import fleet membership for an Attached cluster."""

  detailed_help = {'EXAMPLES': _EXAMPLES}

  @staticmethod
  def Args(parser):
    """Registers flags for this command."""
    resource_args.AddLocationResourceArg(parser, 'to import attached cluster.')
    resource_args.AddFleetMembershipResourceArg(parser)

    attached_flags.AddPlatformVersion(parser)
    attached_flags.AddDistribution(parser, required=True)
    attached_flags.AddKubectl(parser)
    attached_flags.AddProxyConfig(parser)

    flags.AddValidateOnly(parser, 'cluster to import')

    base.ASYNC_FLAG.AddToParser(parser)

  def Run(self, args):
    """Runs the import command."""
    location_ref = args.CONCEPTS.location.Parse()
    fleet_membership_ref = args.CONCEPTS.fleet_membership.Parse()

    with endpoint_util.GkemulticloudEndpointOverride(location_ref.locationsId):
      manifest = self._get_manifest(
          args, location_ref, fleet_membership_ref.membershipsId
      )

      import_resp = ''
      with kube_util.KubernetesClient(
          kubeconfig=attached_flags.GetKubeconfig(args),
          context=attached_flags.GetContext(args),
          enable_workload_identity=True,
      ) as kube_client:
        kube_client.CheckClusterAdminPermissions()

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

          import_resp = self._import_attached_cluster(
              args, location_ref, fleet_membership_ref
          )
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

$ gcloud {} container attached clusters generate-install-manifest --location={} --platform-version={} --format="value(manifest)"  {}  | kubectl delete -f -

AFTER the attach operation completes.
""".format(
              six.text_type(self.ReleaseTrack()).lower(),
              location_ref.locationsId,
              attached_flags.GetPlatformVersion(args),
              fleet_membership_ref.membershipsId,
          )
          pretty_print.Info(msg)
          raise
        except:  # pylint: disable=broad-except
          self._remove_manifest(args, kube_client, manifest)
          raise

        self._remove_manifest(args, kube_client, manifest)

      return import_resp

  def _get_manifest(self, args, location_ref, memberships_id):
    location_client = loc_util.LocationsClient()
    resp = location_client.GenerateInstallManifestForImport(
        location_ref, memberships_id, args=args
    )
    return resp.manifest

  def _remove_manifest(self, args, kube_client, manifest):
    if not flags.GetValidateOnly(args):
      pretty_print.Info('Deleting in-cluster install agent')
      kube_client.Delete(manifest)

  def _import_attached_cluster(self, args, location_ref, fleet_membership_ref):
    cluster_client = api_util.ClustersClient()
    message = command_util.ClusterMessage(
        fleet_membership_ref.RelativeName(),
        action='Importing',
        kind=constants.ATTACHED,
    )
    return command_util.Import(
        location_ref=location_ref,
        resource_client=cluster_client,
        fleet_membership_ref=fleet_membership_ref,
        args=args,
        message=message,
        kind=constants.ATTACHED_CLUSTER_KIND,
    )
