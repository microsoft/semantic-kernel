# -*- coding: utf-8 -*- #
# Copyright 2016 Google LLC. All Rights Reserved.
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
"""Module for wrangling bigtable command arguments."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from googlecloudsdk.api_lib.bigtable import util
from googlecloudsdk.calliope import actions
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.calliope.concepts import concepts
from googlecloudsdk.command_lib.util import completers
from googlecloudsdk.command_lib.util.apis import yaml_data
from googlecloudsdk.command_lib.util.args import resource_args
from googlecloudsdk.command_lib.util.concepts import concept_parsers
from googlecloudsdk.command_lib.util.concepts import presentation_specs
from googlecloudsdk.core.util import text


class ClusterCompleter(completers.ListCommandCompleter):

  def __init__(self, **kwargs):
    super(ClusterCompleter, self).__init__(
        collection='bigtableadmin.projects.instances.clusters',
        list_command='beta bigtable clusters list --uri',
        **kwargs
    )


class InstanceCompleter(completers.ListCommandCompleter):

  def __init__(self, **kwargs):
    super(InstanceCompleter, self).__init__(
        collection='bigtableadmin.projects.instances',
        list_command='beta bigtable instances list --uri',
        **kwargs
    )


class TableCompleter(completers.ListCommandCompleter):

  def __init__(self, **kwargs):
    super(TableCompleter, self).__init__(
        collection='bigtableadmin.projects.instances.tables',
        list_command='beta bigtable instances tables list --uri',
        **kwargs
    )


def ProcessInstanceTypeAndNodes(args):
  """Ensure that --instance-type and --num-nodes are consistent.

  If --instance-type is DEVELOPMENT, then no --cluster-num-nodes can be
  specified. If --instance-type is PRODUCTION, then --cluster-num-nodes defaults
  to 3 if not specified, but can be any positive value.

  Args:
    args: an argparse namespace.

  Raises:
    exceptions.InvalidArgumentException: If --cluster-num-nodes is specified
        when --instance-type is DEVELOPMENT, or --cluster-num-nodes is not
        positive.

  Returns:
    Number of nodes or None if DEVELOPMENT instance-type.
  """
  msgs = util.GetAdminMessages()
  num_nodes = args.cluster_num_nodes
  instance_type = msgs.Instance.TypeValueValuesEnum(args.instance_type)
  if not args.IsSpecified('cluster_num_nodes'):
    if instance_type == msgs.Instance.TypeValueValuesEnum.PRODUCTION:
      num_nodes = 3
  else:
    if instance_type == msgs.Instance.TypeValueValuesEnum.DEVELOPMENT:
      raise exceptions.InvalidArgumentException(
          '--cluster-num-nodes',
          'Cannot set --cluster-num-nodes for DEVELOPMENT instances.',
      )
    elif num_nodes < 1:
      raise exceptions.InvalidArgumentException(
          '--cluster-num-nodes',
          'Clusters of PRODUCTION instances must have at least 1 node.',
      )
  return num_nodes


class ArgAdder(object):
  """A class for adding Bigtable command-line arguments."""

  def __init__(self, parser):
    self.parser = parser

  def AddAsync(self):
    base.ASYNC_FLAG.AddToParser(self.parser)
    return self

  def AddCluster(self):
    """Add cluster argument."""
    self.parser.add_argument(
        '--cluster',
        completer=ClusterCompleter,
        help='ID of the cluster.',
        required=True,
    )
    return self

  def AddDeprecatedCluster(self):
    """Add deprecated cluster argument."""
    self.parser.add_argument(
        '--cluster',
        completer=ClusterCompleter,
        help='ID of the cluster',
        required=False,
        action=actions.DeprecationAction(
            '--cluster',
            warn=(
                'The {flag_name} argument is deprecated; use --cluster-config'
                ' instead.'
            ),
            removed=False,
            action='store',
        ),
    )
    return self

  def AddDeprecatedClusterNodes(self):
    """Add deprecated cluster nodes argument."""
    self.parser.add_argument(
        '--cluster-num-nodes',
        help='Number of nodes to serve.',
        required=False,
        type=int,
        action=actions.DeprecationAction(
            '--cluster-num-nodes',
            warn=(
                'The {flag_name} argument is deprecated; use --cluster-config'
                ' instead.'
            ),
            removed=False,
            action='store',
        ),
    )
    return self

  def AddClusterStorage(self):
    storage_argument = base.ChoiceArgument(
        '--cluster-storage-type',
        choices=['hdd', 'ssd'],
        default='ssd',
        help_str='Storage class for the cluster.',
    )
    storage_argument.AddToParser(self.parser)
    return self

  def AddClusterZone(self, in_instance=False):
    self.parser.add_argument(
        '--cluster-zone' if in_instance else '--zone',
        help=(
            'ID of the zone where the cluster is located. Supported zones '
            'are listed at https://cloud.google.com/bigtable/docs/locations.'
        ),
        required=True,
    )
    return self

  def AddDeprecatedClusterZone(self):
    """Add deprecated cluster zone argument."""
    self.parser.add_argument(
        '--cluster-zone',
        help=(
            'ID of the zone where the cluster is located. Supported zones '
            'are listed at https://cloud.google.com/bigtable/docs/locations.'
        ),
        required=False,
        action=actions.DeprecationAction(
            '--cluster-zone',
            warn=(
                'The {flag_name} argument is deprecated; use --cluster-config'
                ' instead.'
            ),
            removed=False,
            action='store',
        ),
    )
    return self

  def AddInstance(
      self, positional=True, required=True, multiple=False, additional_help=None
  ):
    """Add argument for instance ID to parser."""
    help_text = 'ID of the {}.'.format(
        text.Pluralize(2 if multiple else 1, 'instance')
    )
    if additional_help:
      help_text = ' '.join([help_text, additional_help])
    name = 'instance' if positional else '--instance'
    args = {'completer': InstanceCompleter, 'help': help_text}
    if multiple:
      if positional:
        args['nargs'] = '+'
      else:
        name = '--instances'
        args['type'] = arg_parsers.ArgList()
        args['metavar'] = 'INSTANCE'
    if not positional:
      args['required'] = required

    self.parser.add_argument(name, **args)
    return self

  def AddTable(self):
    """Add table argument."""
    self.parser.add_argument(
        '--table',
        completer=TableCompleter,
        help='ID of the table.',
        required=True,
    )
    return self

  def AddAppProfileRouting(
      self,
      required=True,
      allow_failover_radius=False,
      allow_row_affinity=False,
  ):
    """Adds arguments for app_profile routing to parser."""
    routing_group = self.parser.add_mutually_exclusive_group(required=required)
    any_group = routing_group.add_group('Multi Cluster Routing Policy')
    any_group.add_argument(
        '--route-any',
        action='store_true',
        required=True,
        default=False,
        help='Use Multi Cluster Routing policy.',
    )
    any_group.add_argument(
        '--restrict-to',
        type=arg_parsers.ArgList(),
        help=(
            'Cluster IDs to route to using the Multi Cluster Routing Policy.'
            ' If unset, all clusters in the instance are eligible.'
        ),
        metavar='RESTRICT_TO',
    )
    # By default, will not enable/disable unless the user explicitly says so.
    if allow_row_affinity:
      any_group.add_argument(
          '--row-affinity',
          action='store_true',
          default=None,
          help='Use row affinity sticky routing for this app profile.',
          hidden=True,  # TODO(b/279939624): Remove hidden=True for GA
      )
    if allow_failover_radius:
      choices = {
          'ANY_REGION': (
              'Requests will be allowed to fail over to all eligible clusters.'
          ),
          'INITIAL_REGION_ONLY': (
              'Requests will only be allowed to fail over to clusters within '
              'the region the request was first routed to.'
          ),
      }
      any_group.add_argument(
          '--failover-radius',
          type=lambda x: x.replace('-', '_').upper(),
          choices=choices,
          help=(
              'Restricts clusters that requests can fail over to by proximity.'
              ' Failover radius must be either any-region or'
              ' initial-region-only. any-region allows requests to fail over'
              ' without restriction. initial-region-only prohibits requests'
              ' from failing over to any clusters outside of the initial region'
              ' the request was routed to. If omitted, any-region will be used'
              ' by default.'
          ),
          metavar='FAILOVER_RADIUS',
          hidden=True,
      )
    route_to_group = routing_group.add_group('Single Cluster Routing Policy')
    route_to_group.add_argument(
        '--route-to',
        completer=ClusterCompleter,
        required=True,
        help='Cluster ID to route to using Single Cluster Routing policy.',
    )
    transactional_write_help = (
        'Allow transactional writes with a Single Cluster Routing policy.'
    )
    route_to_group.add_argument(
        '--transactional-writes',
        action='store_true',
        default=None,
        help=transactional_write_help,
    )
    return self

  def AddDescription(self, resource, required=True):
    """Add argument for description to parser."""
    self.parser.add_argument(
        '--description',
        help='Friendly name of the {}.'.format(resource),
        required=required,
    )
    return self

  def AddForce(self, verb):
    """Add argument for force to the parser."""
    self.parser.add_argument(
        '--force',
        action='store_true',
        default=False,
        help='Ignore warnings and force {}.'.format(verb),
    )
    return self

  def AddIsolation(self, allow_data_boost=False):
    """Add argument for isolating this app profile's traffic to parser."""
    isolation_group = self.parser.add_mutually_exclusive_group()
    standard_isolation_group = isolation_group.add_group(
        'Standard Isolation',
    )

    choices = {
        'PRIORITY_LOW': 'Requests are treated with low priority.',
        'PRIORITY_MEDIUM': 'Requests are treated with medium priority.',
        'PRIORITY_HIGH': 'Requests are treated with high priority.',
    }
    standard_isolation_group.add_argument(
        '--priority',
        type=lambda x: x.replace('-', '_').upper(),
        choices=choices,
        default=None,
        # TODO(b/293306176): Replace with:
        #
        # help=(
        #     'Specify the request priority under Standard Isolation. Passing'
        #     ' this option implies Standard Isolation, e.g. the --standard'
        #     ' option. If not specified, the app profile uses Standard'
        #     ' Isolation with PRIORITY_HIGH by default. Specifying request'
        #     ' priority on an app profile that has Data Boost Read-Only'
        #     ' Isolation enabled will change the isolation to Standard and'
        #     ' use the specified priority, which may cause unexpected behavior'
        #     ' for running applications.'
        # ),
        help=(
            'Specify the request priority. If not specified, the app profile'
            ' uses PRIORITY_HIGH by default.'
        ),
        required=True,
    )

    if allow_data_boost:
      standard_isolation_group.add_argument(
          '--standard',
          action='store_true',
          default=False,
          help=(
              'Use Standard Isolation, rather than Data Boost Read-only'
              ' Isolation. If specified, --priority is required.'
          ),
          hidden=True,  # TODO(b/293306176): Unhide
      )

      data_boost_isolation_group = isolation_group.add_group(
          'Data Boost Read-only Isolation',
          hidden=True,  # TODO(b/293306176): Unhide
      )

      data_boost_isolation_group.add_argument(
          '--data-boost',
          action='store_true',
          default=False,
          help=(
              'Use Data Boost Read-only Isolation, rather than Standard'
              ' Isolation. If specified, --data-boost-compute-billing-owner is'
              ' required. Specifying Data Boost Read-only Isolation on an app'
              ' profile which has Standard Isolation enabled may cause'
              ' unexpected behavior for running applications.'
          ),
          required=True,
      )

      compute_billing_choices = {
          'HOST_PAYS': (
              'Compute Billing should be accounted towards the host Cloud'
              ' Project (containing the targeted Bigtable Instance / Table).'
          ),
          # TODO(b/307933524): Add this option in the future.
          # 'CONSUMER': (
          #     'Compute Billing should be accounted towards the requester'
          #     ' Cloud Project (targeting the Bigtable Instance / Table with'
          #     ' Data Boost).'
          # ),
      }
      data_boost_isolation_group.add_argument(
          '--data-boost-compute-billing-owner',
          type=lambda x: x.upper(),
          choices=compute_billing_choices,
          default=None,
          help=(
              'Specify the Data Boost Compute Billing Owner, required if'
              ' --data-boost is passed.'
          ),
          required=True,
      )

    return self

  def AddInstanceDisplayName(self, required=False):
    """Add argument group for display-name to parser."""
    self.parser.add_argument(
        '--display-name',
        help='Friendly name of the instance.',
        required=required,
    )
    return self

  def AddDeprecatedInstanceType(self):
    """Add deprecated instance type argument."""
    choices = {
        'PRODUCTION': (
            'Production instances provide high availability and are '
            'suitable for applications in production. Production instances '
            'created with the --instance-type argument have 3 nodes if a value '
            'is not provided for --cluster-num-nodes.'
        ),
        'DEVELOPMENT': (
            'Development instances are low-cost instances meant '
            'for development and testing only. They do not '
            'provide high availability and no service level '
            'agreement applies.'
        ),
    }
    self.parser.add_argument(
        '--instance-type',
        default='PRODUCTION',
        type=lambda x: x.upper(),
        choices=choices,
        help='The type of instance to create.',
        required=False,
        action=actions.DeprecationAction(
            '--instance-type',
            warn=(
                'The {flag_name} argument is deprecated. DEVELOPMENT instances'
                ' are no longer offered. All instances are of type PRODUCTION.'
            ),
            removed=False,
            action='store',
        ),
    )
    return self

  def AddClusterConfig(self):
    """Add the cluster-config argument as repeated kv dicts."""
    self.parser.add_argument(
        '--cluster-config',
        action='append',
        type=arg_parsers.ArgDict(
            spec={
                'id': str,
                'zone': str,
                'nodes': int,
                'kms-key': str,
                'autoscaling-min-nodes': int,
                'autoscaling-max-nodes': int,
                'autoscaling-cpu-target': int,
                'autoscaling-storage-target': int,
            },
            required_keys=['id', 'zone'],
            max_length=8,
        ),
        metavar=(
            'id=ID,zone=ZONE,nodes=NODES,kms-key=KMS_KEY,'
            'autoscaling-min-nodes=AUTOSCALING_MIN_NODES,'
            'autoscaling-max-nodes=AUTOSCALING_MAX_NODES,'
            'autoscaling-cpu-target=AUTOSCALING_CPU_TARGET,'
            'autoscaling-storage-target=AUTOSCALING_STORAGE_TARGET'
        ),
        help=textwrap.dedent("""\
        *Repeatable*. Specify cluster config as a key-value dictionary.

        This is the recommended argument for specifying cluster configurations.

        Keys can be:

          *id*: Required. The ID of the cluster.

          *zone*: Required. ID of the zone where the cluster is located. Supported zones are listed at https://cloud.google.com/bigtable/docs/locations.

          *nodes*: The number of nodes in the cluster. Default=1.

          *kms-key*: The Cloud KMS (Key Management Service) cryptokey that will be used to protect the cluster.

          *autoscaling-min-nodes*: The minimum number of nodes for autoscaling.

          *autoscaling-max-nodes*: The maximum number of nodes for autoscaling.

          *autoscaling-cpu-target*: The target CPU utilization percentage for autoscaling. Accepted values are from 10 to 80.

          *autoscaling-storage-target*: The target storage utilization gibibytes per node for autoscaling. Accepted values are from 2560 to 5120 for SSD clusters and 8192 to 16384 for HDD clusters.

        If this argument is specified, the deprecated arguments for configuring a single cluster will be ignored, including *--cluster*, *--cluster-zone*, *--cluster-num-nodes*.

        See *EXAMPLES* section.
        """),
    )

    return self

  def AddScalingArgs(
      self,
      required=False,
      num_nodes_required=False,
      num_nodes_default=None,
      add_disable_autoscaling=False,
      require_all_essential_autoscaling_args=False,
  ):
    """Add scaling related arguments."""
    scaling_group = self.parser.add_mutually_exclusive_group(required=required)
    manual_scaling_group = scaling_group.add_group('Manual Scaling')
    manual_scaling_group.add_argument(
        '--num-nodes',
        help='Number of nodes to serve.',
        default=num_nodes_default,
        required=num_nodes_required,
        type=int,
        metavar='NUM_NODES',
    )
    if add_disable_autoscaling:
      manual_scaling_group.add_argument(
          '--disable-autoscaling',
          help=(
              'Set this flag and --num-nodes to disable autoscaling. If'
              ' autoscaling is currently not enabled, setting this flag does'
              ' nothing.'
          ),
          action='store_true',
          default=False,
          required=False,
          hidden=False,
      )

    autoscaling_group = scaling_group.add_group('Autoscaling', hidden=False)
    autoscaling_group.add_argument(
        '--autoscaling-min-nodes',
        help='The minimum number of nodes for autoscaling.',
        default=None,
        required=require_all_essential_autoscaling_args,
        type=int,
        metavar='AUTOSCALING_MIN_NODES',
    )
    autoscaling_group.add_argument(
        '--autoscaling-max-nodes',
        help='The maximum number of nodes for autoscaling.',
        default=None,
        required=require_all_essential_autoscaling_args,
        type=int,
        metavar='AUTOSCALING_MAX_NODES',
    )
    autoscaling_group.add_argument(
        '--autoscaling-cpu-target',
        help=(
            'The target CPU utilization percentage for autoscaling. Accepted'
            ' values are from 10 to 80.'
        ),
        default=None,
        required=require_all_essential_autoscaling_args,
        type=int,
        metavar='AUTOSCALING_CPU_TARGET',
    )
    autoscaling_group.add_argument(
        '--autoscaling-storage-target',
        help=(
            'The target storage utilization gibibytes per node for autoscaling.'
            ' Accepted values are from 2560 to 5120 for SSD clusters and 8192'
            ' to 16384 for HDD clusters.'
        ),
        default=None,
        required=False,
        type=int,
        metavar='AUTOSCALING_STORAGE_TARGET',
    )
    return self

  def AddScalingArgsForClusterUpdate(self):
    """Add scaling related arguments."""
    return self.AddScalingArgs(
        required=True, num_nodes_required=True, add_disable_autoscaling=True
    )

  def AddScalingArgsForClusterCreate(self):
    """Add scaling related arguments."""
    return self.AddScalingArgs(
        num_nodes_default=3, require_all_essential_autoscaling_args=True
    )


def InstanceAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='instance', help_text='Cloud Bigtable instance for the {resource}.'
  )


def TableAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='table', help_text='Cloud Bigtable table for the {resource}.'
  )


def ClusterAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='cluster', help_text='Cloud Bigtable cluster for the {resource}.'
  )


def AppProfileAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='app profile',
      help_text='Cloud Bigtable application profile for the {resource}.',
  )


def BackupAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='backup', help_text='Cloud Bigtable backup for the {resource}.'
  )


def KmsKeyAttributeConfig():
  # For anchor attribute, help text is generated automatically.
  return concepts.ResourceParameterAttributeConfig(name='kms-key')


def KmsKeyringAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='kms-keyring', help_text='The KMS keyring id of the {resource}.'
  )


def KmsLocationAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='kms-location', help_text='The Cloud location for the {resource}.'
  )


def KmsProjectAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='kms-project', help_text='The Cloud project id for the {resource}.'
  )


def GetInstanceResourceSpec():
  """Return the resource specification for a Bigtable instance."""
  return concepts.ResourceSpec(
      'bigtableadmin.projects.instances',
      resource_name='instance',
      instancesId=InstanceAttributeConfig(),
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
      disable_auto_completers=False,
  )


def GetTableResourceSpec():
  """Return the resource specification for a Bigtable table."""
  return concepts.ResourceSpec(
      'bigtableadmin.projects.instances.tables',
      resource_name='table',
      tablesId=TableAttributeConfig(),
      instancesId=InstanceAttributeConfig(),
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
      disable_auto_completers=False,
  )


def GetClusterResourceSpec():
  """Return the resource specification for a Bigtable cluster."""
  return concepts.ResourceSpec(
      'bigtableadmin.projects.instances.clusters',
      resource_name='cluster',
      clustersId=ClusterAttributeConfig(),
      instancesId=InstanceAttributeConfig(),
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
      disable_auto_completers=False,
  )


def GetAppProfileResourceSpec():
  """Return the resource specification for a Bigtable app profile."""
  return concepts.ResourceSpec(
      'bigtableadmin.projects.instances.appProfiles',
      resource_name='app profile',
      instancesId=InstanceAttributeConfig(),
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
      disable_auto_completers=False,
  )


def GetKmsKeyResourceSpec():
  return concepts.ResourceSpec(
      'cloudkms.projects.locations.keyRings.cryptoKeys',
      resource_name='key',
      cryptoKeysId=KmsKeyAttributeConfig(),
      keyRingsId=KmsKeyringAttributeConfig(),
      locationsId=KmsLocationAttributeConfig(),
      projectsId=KmsProjectAttributeConfig(),
      disable_auto_completers=False,
  )


def GetBackupResourceSpec():
  return concepts.ResourceSpec(
      'bigtableadmin.projects.instances.clusters.backups',
      resource_name='backup',
      backupsId=BackupAttributeConfig(),
      clustersId=ClusterAttributeConfig(),
      instancesId=InstanceAttributeConfig(),
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
      disable_auto_completers=False,
  )


def AddInstancesResourceArg(parser, verb, positional=False):
  """Add --instances resource argument to the parser."""
  concept_parsers.ConceptParser.ForResource(
      'instance' if positional else '--instances',
      GetInstanceResourceSpec(),
      'The instances {}.'.format(verb),
      required=positional,
      plural=True,
  ).AddToParser(parser)


def AddInstanceResourceArg(parser, verb, positional=False, required=True):
  """Add --instance resource argument to the parser."""
  concept_parsers.ConceptParser.ForResource(
      'instance' if positional else '--instance',
      GetInstanceResourceSpec(),
      'The instance {}.'.format(verb),
      required=required,
      plural=False,
  ).AddToParser(parser)


def AddTableResourceArg(parser, verb, positional=False):
  """Add --table resource argument to the parser."""
  concept_parsers.ConceptParser.ForResource(
      'table' if positional else '--table',
      GetTableResourceSpec(),
      'The table {}.'.format(verb),
      required=True,
      plural=False,
  ).AddToParser(parser)


def AddClusterResourceArg(parser, verb):
  """Add cluster positional resource argument to the parser."""
  concept_parsers.ConceptParser.ForResource(
      'cluster',
      GetClusterResourceSpec(),
      'The cluster {}.'.format(verb),
      required=True,
  ).AddToParser(parser)


def AddAppProfileResourceArg(parser, verb):
  """Add app profile positional resource argument to the parser."""
  concept_parsers.ConceptParser.ForResource(
      'app_profile',
      GetAppProfileResourceSpec(),
      'The app profile {}.'.format(verb),
      required=True,
  ).AddToParser(parser)


def AddBackupResourceArg(parser, verb):
  """Add backup positional resource argument to the parser."""
  concept_parsers.ConceptParser([
      presentation_specs.ResourcePresentationSpec(
          '--instance',
          GetInstanceResourceSpec(),
          'The instance {}.'.format(verb),
          required=False,
      ),
      presentation_specs.ResourcePresentationSpec(
          '--cluster',
          GetClusterResourceSpec(),
          'The cluster {}.'.format(verb),
          required=False,
          flag_name_overrides={'instance': ''},
      ),
  ]).AddToParser(parser)


def AddTableRestoreResourceArg(parser):
  """Add Table resource args (source, destination) for restore command."""
  table_spec_data = yaml_data.ResourceYAMLData.FromPath('bigtable.table')
  backup_spec_data = yaml_data.ResourceYAMLData.FromPath('bigtable.backup')

  arg_specs = [
      resource_args.GetResourcePresentationSpec(
          verb='to restore from',
          name='source',
          required=True,
          prefixes=True,
          attribute_overrides={'backup': 'source'},
          positional=False,
          resource_data=backup_spec_data.GetData(),
      ),
      resource_args.GetResourcePresentationSpec(
          verb='to restore to',
          name='destination',
          required=True,
          prefixes=True,
          attribute_overrides={'table': 'destination'},
          positional=False,
          resource_data=table_spec_data.GetData(),
      ),
  ]
  fallthroughs = {
      '--source.instance': ['--destination.instance'],
      '--destination.instance': ['--source.instance'],
  }
  concept_parsers.ConceptParser(arg_specs, fallthroughs).AddToParser(parser)


def AddKmsKeyResourceArg(parser, resource, flag_overrides=None, required=False):
  """Add a resource argument for a KMS key.

  Args:
    parser: the parser for the command.
    resource: str, the name of the resource that the cryptokey will be used to
      protect.
    flag_overrides: dict, The default flag names are 'kms-key', 'kms-keyring',
      'kms-location' and 'kms-project'. You can pass a dict of overrides where
      the keys of the dict are the default flag names, and the values are the
      override names.
    required: bool, optional. True if the flag must be parsable by the parser.
  """
  concept_parsers.ConceptParser.ForResource(
      '--kms-key',
      GetKmsKeyResourceSpec(),
      'The Cloud KMS (Key Management Service) cryptokey that will be used to '
      'protect the {}.'.format(resource),
      flag_name_overrides=flag_overrides,
      required=required,
  ).AddToParser(parser)


def GetAndValidateKmsKeyName(args):
  """Parse the KMS key resource arg, make sure the key format is correct."""
  kms_ref = args.CONCEPTS.kms_key.Parse()
  if kms_ref:
    return kms_ref.RelativeName()
  else:
    # If parsing failed but args were specified, raise error
    for keyword in ['kms-key', 'kms-keyring', 'kms-location', 'kms-project']:
      if getattr(args, keyword.replace('-', '_'), None):
        raise exceptions.InvalidArgumentException(
            '--kms-project --kms-location --kms-keyring --kms-key',
            'Specify fully qualified KMS key ID with --kms-key, or use '
            + 'combination of --kms-project, --kms-location, --kms-keyring and '
            + '--kms-key to specify the key ID in pieces.',
        )
    return None  # User didn't specify KMS key


def AddStartTimeArgs(parser, verb):
  parser.add_argument(
      '--start-time',
      required=False,
      type=arg_parsers.Datetime.Parse,
      help=(
          'Start time of the time range {}. '
          'See $ gcloud topic datetimes for information on time formats.'
          .format(verb)
      ),
  )


def AddEndTimeArgs(parser, verb):
  parser.add_argument(
      '--end-time',
      required=False,
      type=arg_parsers.Datetime.Parse,
      help=(
          'End time of the time range {}. '
          'See $ gcloud topic datetimes for information on time formats.'
          .format(verb)
      ),
  )


def AddCopyBackupResourceArgs(parser):
  """Add backup resource args (source, destination) for copy command."""
  arg_specs = [
      presentation_specs.ResourcePresentationSpec(
          '--source',
          GetBackupResourceSpec(),
          'The source backup to copy from.',
          required=True,
          flag_name_overrides={
              'project': '--source-project',
              'instance': '--source-instance',
              'cluster': '--source-cluster',
              'backup': '--source-backup',
          },
      ),
      presentation_specs.ResourcePresentationSpec(
          '--destination',
          GetBackupResourceSpec(),
          'The destination backup to copy to.',
          required=True,
          flag_name_overrides={
              'project': '--destination-project',
              'instance': '--destination-instance',
              'cluster': '--destination-cluster',
              'backup': '--destination-backup',
          },
      ),
  ]
  fallthroughs = {
      '--source.project': ['--destination.project'],
      '--destination.project': ['--source.project'],
      '--source.instance': ['--destination.instance'],
      '--destination.instance': ['--source.instance'],
  }
  concept_parsers.ConceptParser(arg_specs, fallthroughs).AddToParser(parser)
