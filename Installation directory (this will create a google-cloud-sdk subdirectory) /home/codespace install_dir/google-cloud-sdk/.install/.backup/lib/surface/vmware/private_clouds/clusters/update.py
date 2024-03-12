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
"""'vmware clusters update' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from typing import List
from googlecloudsdk.api_lib.vmware import clusters
from googlecloudsdk.calliope import actions
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.vmware import flags
from googlecloudsdk.command_lib.vmware.clusters import util
from googlecloudsdk.core import log

DETAILED_HELP = {
    'DESCRIPTION': """
          Adjust the number of nodes in the VMware Engine cluster. Successful addition or removal of a node results in a cluster in READY state. Check the progress of a cluster using `{parent_command} list`.
        """,
    'EXAMPLES': """
          To resize a cluster called `my-cluster` in private cloud `my-private-cloud` and zone `us-west2-a` to have `3` nodes of type `standard-72`, run:

            $ {command} my-cluster --location=us-west2-a --project=my-project --private-cloud=my-private-cloud --update-nodes-config=type=standard-72,count=3

            Or:

            $ {command} my-cluster --private-cloud=my-private-cloud --update-nodes-config=type=standard-72,count=3

           In the second example, the project and location are taken from gcloud properties core/project and compute/zone.
    """,
}

_NODE_TYPE_CONFIG_HELP = """
        Information about the type and number of nodes associated with the cluster.

        type (required): canonical identifier of the node type.

        count (required): number of nodes of this type in the cluster.
"""

_OLD_NODE_TYPE_CONFIG_HELP = _NODE_TYPE_CONFIG_HELP + """

        custom_core_count: can be passed, but the value will be ignored. Updating custom core count is not supported.
"""


def _ParseOldNodesConfigsParameters(existing_cluster, nodes_configs):
  """Parses the node configs parameters passed in the old format.

  In the old format, the nodes configs are passed in a way that specifies what
  exact node configs should be attached to the cluster after the operation. It's
  not possible to remove existing node types. Even unchanged nodes configs have
  to be specified in the parameters.

  Args:
    existing_cluster: cluster whose nodes configs should be updated
    nodes_configs: nodes configs to be attached to the cluster

  Returns:
    list of NodeTypeConfig objects prepared for further processing

  Raises:
    InvalidNodeConfigsProvidedError:
      if duplicate node types were specified or if a config for an existing node
      type is not specified
  """
  current_node_types = [
      prop.key for prop in existing_cluster.nodeTypeConfigs.additionalProperties
  ]
  requested_node_types = [config['type'] for config in nodes_configs]

  duplicated_types = util.FindDuplicatedTypes(requested_node_types)
  if duplicated_types:
    raise util.InvalidNodeConfigsProvidedError(
        f'types: {duplicated_types} provided more than once.'
    )

  unspecified_types = set(current_node_types) - set(requested_node_types)
  if unspecified_types:
    raise util.InvalidNodeConfigsProvidedError(
        'when using `--node-type-config` parameters you need to specify node'
        ' counts for all node types present in the cluster. Missing node'
        f' types: {list(unspecified_types)}.'
    )

  return [
      util.NodeTypeConfig(
          type=config['type'], count=config['count'], custom_core_count=0
      )
      for config in nodes_configs
  ]


def _ParseNewNodesConfigsParameters(
    existing_cluster, updated_nodes_configs, removed_types
):
  """Parses the node configs parameters passed in the new format.

  In the new format, the nodes configs are passed using two parameters. One of
  them specifies which configs should be updated or created (unchanged configs
  don't have to be specified at all). The other lists the configs to be removed.
  This format is more flexible than the old one because it allows for config
  removal and doesn't require re-specifying unchanged configs.

  Args:
    existing_cluster: cluster whose nodes configs should be updated
    updated_nodes_configs: list of nodes configs to update or create
    removed_types: list of node types for which nodes configs should be removed

  Returns:
    list of NodeTypeConfig objects prepared for further processing

  Raises:
    InvalidNodeConfigsProvidedError:
      if duplicate node types were specified
  """
  requested_node_types = [
      config['type'] for config in updated_nodes_configs
  ] + removed_types

  duplicated_types = util.FindDuplicatedTypes(requested_node_types)
  if duplicated_types:
    raise util.InvalidNodeConfigsProvidedError(
        f'types: {duplicated_types} provided more than once.'
    )

  node_count = {}
  for prop in existing_cluster.nodeTypeConfigs.additionalProperties:
    node_count[prop.key] = prop.value.nodeCount

  for config in updated_nodes_configs:
    node_count[config['type']] = config['count']

  for node_type in removed_types:
    node_count[node_type] = 0

  return [
      util.NodeTypeConfig(type=node_type, count=count, custom_core_count=0)
      for node_type, count in node_count.items()
  ]


def _ValidatePoliciesToRemove(
    existing_cluster, updated_settings, policies_to_remove
):
  """Checks if the policies specified for removal actually exist and that they are not updated in the same call.

  Args:
    existing_cluster: cluster before the update
    updated_settings: updated autoscale settings
    policies_to_remove: list of policy names to remove

  Raises:
    InvalidAutoscalingSettingsProvidedError: if the validation fails.
  """
  if not policies_to_remove:
    return

  if updated_settings and updated_settings.autoscaling_policies:
    for name in updated_settings.autoscaling_policies:
      if name in policies_to_remove:
        raise util.InvalidAutoscalingSettingsProvidedError(
            f"policy '{name}' specified both for update and removal"
        )

  if not existing_cluster.autoscalingSettings:
    raise util.InvalidAutoscalingSettingsProvidedError(
        f"nonexistent policies '{policies_to_remove}' specified for removal"
    )

  existing_policies = {
      p.key
      for p in existing_cluster.autoscalingSettings.autoscalingPolicies.additionalProperties
  }
  for name in policies_to_remove:
    if name not in existing_policies:
      raise util.InvalidAutoscalingSettingsProvidedError(
          f"nonexistent policies '{policies_to_remove}' specified for removal"
      )


def _RemoveAutoscalingPolicies(
    autoscaling_settings: util.AutoscalingSettings,
    policies_to_remove: List[str],
) -> util.AutoscalingSettings:
  if not policies_to_remove:
    return autoscaling_settings

  for policy in policies_to_remove:
    del autoscaling_settings.autoscaling_policies[policy]

  return autoscaling_settings


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Update(base.UpdateCommand):
  """Update a Google Cloud VMware Engine cluster."""

  detailed_help = DETAILED_HELP

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    flags.AddClusterArgToParser(parser, positional=True)
    base.ASYNC_FLAG.AddToParser(parser)
    base.ASYNC_FLAG.SetDefault(parser, True)
    parser.display_info.AddFormat('yaml')
    parser.add_argument(
        '--node-type-config',
        required=False,
        type=arg_parsers.ArgDict(
            spec={'type': str, 'count': int, 'custom-core-count': int},
            required_keys=('type', 'count'),
        ),
        action=actions.DeprecationAction(
            '--node-type-config',
            warn=(
                'The {flag_name} option is deprecated; please use'
                ' --update-nodes-config and --remove-nodes-config instead.'
            ),
            removed=False,
            action='append',
        ),
        metavar='[count=COUNT],[type=TYPE]',
        help=_OLD_NODE_TYPE_CONFIG_HELP,
    )
    parser.add_argument(
        '--update-nodes-config',
        required=False,
        default=list(),
        type=arg_parsers.ArgDict(
            spec={'type': str, 'count': int},
            required_keys=('type', 'count'),
        ),
        action='append',
        help=_NODE_TYPE_CONFIG_HELP,
    )
    parser.add_argument(
        '--remove-nodes-config',
        required=False,
        metavar='TYPE',
        default=list(),
        type=str,
        action='append',
        help='Type of node that should be removed from the cluster',
    )
    autoscaling_settings_group = parser.add_mutually_exclusive_group(
        required=False, hidden=True
    )
    inlined_autoscaling_settings_group = autoscaling_settings_group.add_group()
    inlined_autoscaling_settings_group.add_argument(
        '--autoscaling-min-cluster-node-count',
        type=int,
        help='Minimum number of nodes in the cluster',
    )
    inlined_autoscaling_settings_group.add_argument(
        '--autoscaling-max-cluster-node-count',
        type=int,
        help='Maximum number of nodes in the cluster',
    )
    inlined_autoscaling_settings_group.add_argument(
        '--autoscaling-cool-down-period',
        type=str,
        help=(
            'Cool down period (in minutes) between consecutive cluster'
            ' expansions/contractions'
        ),
    )
    inlined_autoscaling_settings_group.add_argument(
        '--update-autoscaling-policy',
        type=arg_parsers.ArgDict(
            spec={
                'name': str,
                'node-type-id': str,
                'scale-out-size': int,
                'min-node-count': int,
                'max-node-count': int,
                'cpu-thresholds-scale-in': int,
                'cpu-thresholds-scale-out': int,
                'granted-memory-thresholds-scale-in': int,
                'granted-memory-thresholds-scale-out': int,
                'consumed-memory-thresholds-scale-in': int,
                'consumed-memory-thresholds-scale-out': int,
                'storage-thresholds-scale-in': int,
                'storage-thresholds-scale-out': int,
            },
            required_keys=['name'],
        ),
        action='append',
        default=list(),
        help='Autoscaling policy to be applied to the cluster',
    )
    autoscaling_settings_group.add_argument(
        '--autoscaling-settings-from-file',
        type=arg_parsers.YAMLFileContents(),
        help=(
            'A YAML file containing the autoscaling settings to be applied to'
            ' the cluster'
        ),
    )
    parser.add_argument(
        '--remove-autoscaling-policy',
        required=False,
        hidden=True,
        metavar='NAME',
        default=list(),
        type=str,
        action='append',
        help=(
            'Names of autoscaling policies that should be removed from the'
            ' cluster'
        ),
    )

  def Run(self, args):
    cluster = args.CONCEPTS.cluster.Parse()
    client = clusters.ClustersClient()

    if args.node_type_config and (
        args.update_nodes_config or args.remove_nodes_config
    ):
      raise util.InvalidNodeConfigsProvidedError(
          'flag `--node-type-config` is mutually exclusive with'
          ' `--update-nodes-config` and `--remove-nodes-config` flags.'
      )

    existing_cluster = client.Get(cluster)

    if args.node_type_config:
      configs = _ParseOldNodesConfigsParameters(
          existing_cluster, args.node_type_config
      )
    elif args.update_nodes_config or args.remove_nodes_config:
      configs = _ParseNewNodesConfigsParameters(
          existing_cluster, args.update_nodes_config, args.remove_nodes_config
      )
    else:
      configs = None

    if args.autoscaling_settings_from_file:
      updated_settings = util.ParseAutoscalingSettingsFromFileFormat(
          args.autoscaling_settings_from_file
      )
    elif (
        args.autoscaling_min_cluster_node_count
        or args.autoscaling_max_cluster_node_count
        or args.autoscaling_cool_down_period
        or args.update_autoscaling_policy
    ):
      updated_settings = util.ParseAutoscalingSettingsFromInlinedFormat(
          args.autoscaling_min_cluster_node_count,
          args.autoscaling_max_cluster_node_count,
          args.autoscaling_cool_down_period,
          args.update_autoscaling_policy,
      )
    else:
      updated_settings = None

    _ValidatePoliciesToRemove(
        existing_cluster, updated_settings, args.remove_autoscaling_policy
    )

    autoscaling_settings = None
    if updated_settings is not None or args.remove_autoscaling_policy:
      old_settings = util.ParseAutoscalingSettingsFromApiFormat(
          existing_cluster
      )
      autoscaling_settings = util.MergeAutoscalingSettings(
          old_settings, updated_settings
      )

      autoscaling_settings = _RemoveAutoscalingPolicies(
          autoscaling_settings, args.remove_autoscaling_policy
      )

    operation = client.Update(cluster, configs, autoscaling_settings)
    is_async = args.async_

    if is_async:
      log.UpdatedResource(operation.name, kind='cluster', is_async=True)
      return

    resource = client.WaitForOperation(
        operation_ref=client.GetOperationRef(operation),
        message='waiting for cluster [{}] to be updated'.format(
            cluster.RelativeName()
        ),
    )
    log.UpdatedResource(cluster.RelativeName(), kind='cluster')
    return resource
