# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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
"""Command to create an environment."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.composer import environments_util as environments_api_util
from googlecloudsdk.api_lib.composer import operations_util as operations_api_util
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.composer import flags
from googlecloudsdk.command_lib.composer import image_versions_util
from googlecloudsdk.command_lib.composer import parsers
from googlecloudsdk.command_lib.composer import resource_args
from googlecloudsdk.command_lib.composer import util as command_util
from googlecloudsdk.command_lib.kms import resource_args as kms_resource_args
from googlecloudsdk.command_lib.util.args import labels_util
from googlecloudsdk.core import log
import six

_INVALID_OPTION_FOR_V2_ERROR_MSG = """\
Cannot specify --{opt} with Composer 2.X or greater.
"""

_INVALID_OPTION_FOR_V1_ERROR_MSG = """\
Cannot specify --{opt} with Composer 1.X.
"""

DETAILED_HELP = {
    'EXAMPLES':
        """\
          To create an environment called ``env-1'' with all the default values,
          run:

            $ {command} env-1

          To create a new environment named ``env-1'' with the Google Compute
          Engine machine-type ``n1-standard-8'', and the Google Compute Engine
          network ``my-network'', run:

            $ {command} env-1 --machine-type=n1-standard-8 --network=my-network
        """
}


def _CommonArgs(parser, support_max_pods_per_node, release_track):
  """Common arguments that apply to all ReleaseTracks."""
  resource_args.AddEnvironmentResourceArg(parser, 'to create')
  base.ASYNC_FLAG.AddToParser(parser)
  parser.add_argument(
      '--node-count',
      type=int,
      help='The number of nodes to create to run the environment.')
  parser.add_argument(
      '--zone',
      help='The Compute Engine zone in which the environment will '
      'be created. For example `--zone=us-central1-a`.')
  parser.add_argument(
      '--machine-type',
      help='The Compute Engine machine type '
      '(https://cloud.google.com/compute/docs/machine-types) to use for '
      'nodes. For example `--machine-type=n1-standard-1`.')
  parser.add_argument(
      '--disk-size',
      type=arg_parsers.BinarySize(
          lower_bound='20GB',
          upper_bound='64TB',
          suggested_binary_size_scales=['GB', 'TB']),
      help='The disk size for each VM node in the environment. The minimum '
      'size is 20GB, and the maximum is 64TB. Specified value must be an '
      'integer multiple of gigabytes. Cannot be updated after the '
      'environment has been created. If units are not provided, defaults to '
      'GB.',
      action=flags.V1ExclusiveStoreAction)

  network_subnetwork_group = parser.add_group(
        help='Virtual Private Cloud networking'
  )
  if release_track != base.ReleaseTrack.GA:
    flags.NETWORK_ATTACHMENT.AddToParser(parser)
  flags.NETWORK_FLAG.AddToParser(network_subnetwork_group)
  flags.SUBNETWORK_FLAG.AddToParser(network_subnetwork_group)
  flags.STORAGE_BUCKET_FLAG.AddToParser(parser)

  labels_util.AddCreateLabelsFlags(parser)
  flags.CREATE_ENV_VARS_FLAG.AddToParser(parser)
  # Default is provided by API server.
  parser.add_argument(
      '--service-account',
      help='The Google Cloud Platform service account to be used by the node '
      'VMs. If a service account is not specified, the "default" Compute '
      'Engine service account for the project is used. Cannot be updated.')
  # Default is provided by API server.
  parser.add_argument(
      '--oauth-scopes',
      help='The set of Google API scopes to be made available on all of the '
      'node VMs. Defaults to '
      '[\'https://www.googleapis.com/auth/cloud-platform\']. Cannot be '
      'updated.',
      type=arg_parsers.ArgList(),
      metavar='SCOPE',
      action=arg_parsers.UpdateAction)
  parser.add_argument(
      '--tags',
      help='The set of instance tags applied to all node VMs. Tags are used '
      'to identify valid sources or targets for network firewalls. Each tag '
      'within the list must comply with RFC 1035. Cannot be updated.',
      type=arg_parsers.ArgList(),
      metavar='TAG',
      action=arg_parsers.UpdateAction)

  # API server will validate key/value pairs.
  parser.add_argument(
      '--airflow-configs',
      help="""\
A list of Airflow software configuration override KEY=VALUE pairs to set. For
information on how to structure KEYs and VALUEs, run
`$ {top_command} help composer environments update`.""",
      type=arg_parsers.ArgDict(),
      metavar='KEY=VALUE',
      action=arg_parsers.UpdateAction)

  parser.add_argument(
      '--python-version',
      type=str,
      choices={
          '2': 'Created environment will use Python 2',
          '3': 'Created environment will use Python 3'
      },
      action=flags.V1ExclusiveStoreAction,
      help='The Python version to be used within the created environment. '
      'Supplied value should represent the desired major Python version. '
      'Cannot be updated.')

  version_group = parser.add_mutually_exclusive_group()
  airflow_version_type = arg_parsers.RegexpValidator(
      r'^(\d+(?:\.\d+(?:\.\d+(?:-build\.\d+)?)?)?)',
      'must be in the form X[.Y[.Z]].',
  )
  version_group.add_argument(
      '--airflow-version',
      type=airflow_version_type,
      help="""Version of Apache Airflow to run in the environment.

      Must be of the form `X[.Y[.Z]]`, where `[]` denotes optional fragments.
      Examples: `2`, `2.3`, `2.3.4`.

      The current Cloud Composer version will be used within the created
      environment. The Apache Airflow version is a semantic version or an alias
      in the form of major or major.minor version numbers, resolved to the
      latest matching Apache Airflow version supported in the current Cloud
      Composer version. The resolved version is stored in the created
      environment.""")

  image_version_type = arg_parsers.RegexpValidator(
      r'^composer-(\d+(?:\.\d+.\d+(?:-[a-z]+\.\d+)?)?|latest)-airflow-(\d+(?:\.\d+(?:\.\d+(?:-build\.\d+)?)?)?)',
      "must be in the form 'composer-A[.B.C[-D.E]]-airflow-X[.Y[.Z]]' or "
      "'latest' can be provided in place of the Cloud Composer version "
      "string. For example: 'composer-latest-airflow-1.10.0'.",
  )
  version_group.add_argument(
      '--image-version',
      type=image_version_type,
      help="""Version of the image to run in the environment.

      The image version encapsulates the versions of both Cloud Composer
      and Apache Airflow. Must be of the form
      `composer-A[.B.C[-D.E]]-airflow-X[.Y[.Z]]`, where `[]` denotes optional
      fragments.

      Examples: `composer-2-airflow-2`, `composer-2-airflow-2.2`,
      `composer-2.1.2-airflow-2.3.4`.

      The Cloud Composer portion of the image version is a semantic version or
      an alias in the form of major version number or `latest`, resolved to the
      current Cloud Composer version. The Apache Airflow portion of the image
      version is a semantic version or an alias in the form of major or
      major.minor version numbers, resolved to the latest matching Apache
      Airflow version supported in the given Cloud Composer version. The
      resolved versions are stored in the created environment.""")
  flags.AddIpAliasEnvironmentFlags(parser, support_max_pods_per_node)
  flags.AddPrivateIpEnvironmentFlags(parser, release_track)

  web_server_group = parser.add_mutually_exclusive_group()
  flags.WEB_SERVER_ALLOW_IP.AddToParser(web_server_group)
  flags.WEB_SERVER_ALLOW_ALL.AddToParser(web_server_group)
  flags.WEB_SERVER_DENY_ALL.AddToParser(web_server_group)
  flags.CLOUD_SQL_MACHINE_TYPE.AddToParser(parser)
  flags.CLOUD_SQL_PREFERRED_ZONE.AddToParser(parser)
  flags.WEB_SERVER_MACHINE_TYPE.AddToParser(parser)
  flags.AddMaintenanceWindowFlagsGroup(parser)

  permission_info = '{} must hold permission {}'.format(
      "The 'Cloud Composer Service Agent' service account",
      "'Cloud KMS CryptoKey Encrypter/Decrypter'")
  kms_resource_args.AddKmsKeyResourceArg(
      parser, 'environment', permission_info=permission_info)

  if release_track == base.ReleaseTrack.GA:
    flags.ENVIRONMENT_SIZE_GA.choice_arg.AddToParser(parser)
  elif release_track == base.ReleaseTrack.BETA:
    flags.ENVIRONMENT_SIZE_BETA.choice_arg.AddToParser(parser)
  elif release_track == base.ReleaseTrack.ALPHA:
    flags.ENVIRONMENT_SIZE_ALPHA.choice_arg.AddToParser(parser)

  autoscaling_group_parser = parser.add_argument_group(
      flags.AUTOSCALING_FLAG_GROUP_DESCRIPTION)
  flags.SCHEDULER_CPU.AddToParser(autoscaling_group_parser)
  flags.WORKER_CPU.AddToParser(autoscaling_group_parser)
  flags.WEB_SERVER_CPU.AddToParser(autoscaling_group_parser)
  flags.SCHEDULER_MEMORY.AddToParser(autoscaling_group_parser)
  flags.WORKER_MEMORY.AddToParser(autoscaling_group_parser)
  flags.WEB_SERVER_MEMORY.AddToParser(autoscaling_group_parser)
  flags.SCHEDULER_STORAGE.AddToParser(autoscaling_group_parser)
  flags.WORKER_STORAGE.AddToParser(autoscaling_group_parser)
  flags.WEB_SERVER_STORAGE.AddToParser(autoscaling_group_parser)
  flags.MIN_WORKERS.AddToParser(autoscaling_group_parser)
  flags.MAX_WORKERS.AddToParser(autoscaling_group_parser)
  flags.NUM_SCHEDULERS.AddToParser(autoscaling_group_parser)
  master_authorized_networks_group = parser.add_group(
      help='Master Authorized Networks configuration')
  flags.ENABLE_MASTER_AUTHORIZED_NETWORKS_FLAG.AddToParser(
      master_authorized_networks_group)
  flags.MASTER_AUTHORIZED_NETWORKS_FLAG.AddToParser(
      master_authorized_networks_group)

  flags.ENABLE_HIGH_RESILIENCE.AddToParser(parser)

  flags.ENABLE_LOGS_IN_CLOUD_LOGGING_ONLY.AddToParser(parser)
  flags.DISABLE_LOGS_IN_CLOUD_LOGGING_ONLY.AddToParser(parser)

  scheduled_snapshots_params_group = parser.add_argument_group(
      flags.SCHEDULED_SNAPSHOTS_GROUP_DESCRIPTION)
  flags.ENABLE_SCHEDULED_SNAPSHOT_CREATION.AddToParser(
      scheduled_snapshots_params_group)
  flags.SNAPSHOT_LOCATION.AddToParser(scheduled_snapshots_params_group)
  flags.SNAPSHOT_CREATION_SCHEDULE.AddToParser(scheduled_snapshots_params_group)
  flags.SNAPSHOT_SCHEDULE_TIMEZONE.AddToParser(scheduled_snapshots_params_group)

  triggerer_params_group = parser.add_argument_group(
      flags.TRIGGERER_PARAMETERS_FLAG_GROUP_DESCRIPTION
  )
  flags.TRIGGERER_CPU.AddToParser(triggerer_params_group)
  flags.TRIGGERER_COUNT.AddToParser(triggerer_params_group)
  flags.TRIGGERER_MEMORY.AddToParser(triggerer_params_group)
  flags.ENABLE_TRIGGERER.AddToParser(triggerer_params_group)

  flags.AIRFLOW_DATABASE_RETENTION_DAYS.AddToParser(
      parser.add_argument_group(hidden=True))


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Create(base.Command):
  """Create and initialize a Cloud Composer environment.

  If run asynchronously with `--async`, exits after printing an operation
  that can be used to poll the status of the creation operation via:

    {top_command} composer operations describe
  """

  detailed_help = DETAILED_HELP
  _support_max_pods_per_node = False

  @classmethod
  def Args(cls, parser, release_track=base.ReleaseTrack.GA):
    _CommonArgs(parser, cls._support_max_pods_per_node, release_track)

    AddLineageIntegrationParser(parser)

  def Run(self, args):
    if image_versions_util.IsDefaultImageVersion(args.image_version):
      message = image_versions_util.BuildDefaultComposerVersionWarning(
          args.image_version, args.airflow_version
      )
      log.warning(message)
    self.image_version = None
    if args.airflow_version:
      self.image_version = image_versions_util.ImageVersionFromAirflowVersion(
          args.airflow_version)
    elif args.image_version:
      self.image_version = args.image_version

    self.ParseIpAliasConfigOptions(args, self.image_version)
    self.ParsePrivateEnvironmentConfigOptions(args, self.image_version)
    self.ParsePrivateEnvironmentWebServerCloudSqlRanges(args,
                                                        self.image_version,
                                                        self.ReleaseTrack())
    self.ParseWebServerAccessControlConfigOptions(args)
    self.ParseMasterAuthorizedNetworksConfigOptions(args, self.ReleaseTrack())
    self.ValidateTriggererFlags(args)
    self.ValidateComposer3Flags(args)
    self.ValidateFlagsAddedInComposer2(
        args,
        image_versions_util.IsImageVersionStringComposerV1(self.image_version),
        self.ReleaseTrack())
    self.ValidateComposer1ExclusiveFlags(
        args,
        image_versions_util.IsImageVersionStringComposerV1(self.image_version),
        self.ReleaseTrack())

    flags.ValidateDiskSize('--disk-size', args.disk_size)
    self.env_ref = args.CONCEPTS.environment.Parse()
    env_name = self.env_ref.Name()
    self.ParseComposer3Flags(args)
    if not command_util.IsValidEnvironmentName(env_name):
      raise command_util.InvalidUserInputError(
          'Invalid environment name: [{}]. Must match pattern: {}'.format(
              env_name, command_util.ENVIRONMENT_NAME_PATTERN.pattern))

    self.zone_ref = parsers.ParseZone(args.zone) if args.zone else None
    self.zone = self.zone_ref.RelativeName() if self.zone_ref else None
    self.machine_type = None
    self.network = None
    self.subnetwork = None
    if args.machine_type:
      self.machine_type = parsers.ParseMachineType(
          args.machine_type,
          fallback_zone=self.zone_ref.Name()
          if self.zone_ref else None).RelativeName()
    if args.network:
      self.network = parsers.ParseNetwork(args.network).RelativeName()
    if args.subnetwork:
      self.subnetwork = parsers.ParseSubnetwork(
          args.subnetwork,
          fallback_region=self.env_ref.Parent().Name()).RelativeName()

    self.kms_key = None
    if args.kms_key:
      self.kms_key = flags.GetAndValidateKmsEncryptionKey(args)

    operation = self.GetOperationMessage(
        args,
        image_versions_util.IsImageVersionStringComposerV1(self.image_version))

    details = 'with operation [{0}]'.format(operation.name)
    if args.async_:
      log.CreatedResource(
          self.env_ref.RelativeName(),
          kind='environment',
          is_async=True,
          details=details)
      return operation
    else:
      try:
        operations_api_util.WaitForOperation(
            operation,
            'Waiting for [{}] to be created with [{}]'.format(
                self.env_ref.RelativeName(), operation.name),
            release_track=self.ReleaseTrack())
      except command_util.OperationError as e:
        raise command_util.EnvironmentCreateError(
            'Error creating [{}]: {}'.format(self.env_ref.RelativeName(),
                                             six.text_type(e)))

  def ParseIpAliasConfigOptions(self, args, image_version):
    """Parses the options for VPC-native configuration."""
    if (args.enable_ip_alias and
        not image_versions_util.IsImageVersionStringComposerV1(image_version)):
      raise command_util.InvalidUserInputError(
          _INVALID_OPTION_FOR_V2_ERROR_MSG.format(opt='enable-ip-alias'))
    if (args.cluster_ipv4_cidr and not args.enable_ip_alias and
        image_versions_util.IsImageVersionStringComposerV1(image_version)):
      raise command_util.InvalidUserInputError(
          flags.PREREQUISITE_OPTION_ERROR_MSG.format(
              prerequisite='enable-ip-alias', opt='cluster-ipv4-cidr'))
    if (args.cluster_secondary_range_name and not args.enable_ip_alias and
        image_versions_util.IsImageVersionStringComposerV1(image_version)):
      raise command_util.InvalidUserInputError(
          flags.PREREQUISITE_OPTION_ERROR_MSG.format(
              prerequisite='enable-ip-alias',
              opt='cluster-secondary-range-name'))
    if (args.services_ipv4_cidr and not args.enable_ip_alias and
        image_versions_util.IsImageVersionStringComposerV1(image_version)):
      raise command_util.InvalidUserInputError(
          flags.PREREQUISITE_OPTION_ERROR_MSG.format(
              prerequisite='enable-ip-alias', opt='services-ipv4-cidr'))
    if (args.services_secondary_range_name and not args.enable_ip_alias and
        image_versions_util.IsImageVersionStringComposerV1(image_version)):
      raise command_util.InvalidUserInputError(
          flags.PREREQUISITE_OPTION_ERROR_MSG.format(
              prerequisite='enable-ip-alias',
              opt='services-secondary-range-name'))
    if (self._support_max_pods_per_node and args.max_pods_per_node and
        not image_versions_util.IsImageVersionStringComposerV1(image_version)):
      raise command_util.InvalidUserInputError(
          _INVALID_OPTION_FOR_V2_ERROR_MSG.format(opt='max-pods-per-node'))
    if (self._support_max_pods_per_node and args.max_pods_per_node and
        not args.enable_ip_alias):
      raise command_util.InvalidUserInputError(
          flags.PREREQUISITE_OPTION_ERROR_MSG.format(
              prerequisite='enable-ip-alias', opt='max-pods-per-node'))
    if (args.enable_ip_masq_agent and not args.enable_ip_alias and
        image_versions_util.IsImageVersionStringComposerV1(image_version)):
      raise command_util.InvalidUserInputError(
          flags.PREREQUISITE_OPTION_ERROR_MSG.format(
              prerequisite='enable-ip-alias', opt='enable-ip-masq-agent'))

  def ParsePrivateEnvironmentConfigOptions(self, args, image_version):
    """Parses the options for Private Environment configuration."""

    if self.isComposer3(args):
      return

    if (args.enable_private_environment and not args.enable_ip_alias and
        image_versions_util.IsImageVersionStringComposerV1(image_version)):
      raise command_util.InvalidUserInputError(
          flags.PREREQUISITE_OPTION_ERROR_MSG.format(
              prerequisite='enable-ip-alias', opt='enable-private-environment'))

    if args.enable_private_endpoint and not args.enable_private_environment:
      raise command_util.InvalidUserInputError(
          flags.PREREQUISITE_OPTION_ERROR_MSG.format(
              prerequisite='enable-private-environment',
              opt='enable-private-endpoint'))

    if (args.enable_privately_used_public_ips and
        not args.enable_private_environment):
      raise command_util.InvalidUserInputError(
          flags.PREREQUISITE_OPTION_ERROR_MSG.format(
              prerequisite='enable-private-environment',
              opt='enable-privately-used-public-ips'))

    if args.master_ipv4_cidr and not args.enable_private_environment:
      raise command_util.InvalidUserInputError(
          flags.PREREQUISITE_OPTION_ERROR_MSG.format(
              prerequisite='enable-private-environment',
              opt='master-ipv4-cidr'))

  def ParsePrivateEnvironmentWebServerCloudSqlRanges(self, args, image_version,
                                                     release_track):
    if (args.web_server_ipv4_cidr and
        not image_versions_util.IsImageVersionStringComposerV1(image_version)):
      raise command_util.InvalidUserInputError(
          _INVALID_OPTION_FOR_V2_ERROR_MSG.format(opt='web-server-ipv4-cidr'))

    if args.web_server_ipv4_cidr and not args.enable_private_environment:
      raise command_util.InvalidUserInputError(
          flags.PREREQUISITE_OPTION_ERROR_MSG.format(
              prerequisite='enable-private-environment',
              opt='web-server-ipv4-cidr'))

    if args.cloud_sql_ipv4_cidr and not args.enable_private_environment:
      raise command_util.InvalidUserInputError(
          flags.PREREQUISITE_OPTION_ERROR_MSG.format(
              prerequisite='enable-private-environment',
              opt='cloud-sql-ipv4-cidr'))

    if (args.composer_network_ipv4_cidr and
        image_versions_util.IsImageVersionStringComposerV1(image_version)):
      raise command_util.InvalidUserInputError(
          _INVALID_OPTION_FOR_V1_ERROR_MSG.format(
              opt='composer-network-ipv4-cidr'))

    if (args.composer_network_ipv4_cidr and
        not args.enable_private_environment):
      raise command_util.InvalidUserInputError(
          flags.PREREQUISITE_OPTION_ERROR_MSG.format(
              prerequisite='enable-private-environment',
              opt='composer-network-ipv4-cidr'))

  def isComposer3(self, args):
    return False

  def ParseWebServerAccessControlConfigOptions(self, args):
    if (
        args.enable_private_environment
        and not args.web_server_allow_ip
        and not args.web_server_allow_all
        and not args.web_server_deny_all
    ):
      raise command_util.InvalidUserInputError(
          'Cannot specify --enable-private-environment without one of: ' +
          '--web-server-allow-ip, --web-server-allow-all ' +
          'or --web-server-deny-all')

    # Default to allow all if no flag is specified.
    self.web_server_access_control = (
        environments_api_util.BuildWebServerAllowedIps(
            args.web_server_allow_ip, args.web_server_allow_all or
            not args.web_server_allow_ip, args.web_server_deny_all))
    flags.ValidateIpRanges(
        [acl['ip_range'] for acl in self.web_server_access_control])

  def ParseMasterAuthorizedNetworksConfigOptions(self, args, release_track):
    if args.enable_master_authorized_networks:
      self.enable_master_authorized_networks = args.enable_master_authorized_networks
    elif args.master_authorized_networks:
      raise command_util.InvalidUserInputError(
          'Cannot specify --master-authorized-networks without ' +
          '--enable-master-authorized-networks.')
    command_util.ValidateMasterAuthorizedNetworks(
        args.master_authorized_networks)
    self.master_authorized_networks = args.master_authorized_networks

  def ValidateScheduledSnapshotFlags(self, args):
    pass

  def ValidateTriggererFlags(self, args):
    if args.image_version:
      triggerer_supported = image_versions_util.IsVersionTriggererCompatible(
          args.image_version
      )
      possible_args = {
          'enable-triggerer': args.enable_triggerer,
          'triggerer-cpu': args.triggerer_cpu,
          'triggerer-memory': args.triggerer_memory,
          'triggerer-count': args.triggerer_count,
      }
      for k, v in possible_args.items():
        if v and not triggerer_supported:
          raise command_util.InvalidUserInputError(
              flags.INVALID_OPTION_FOR_MIN_IMAGE_VERSION_ERROR_MSG.format(
                  opt=k,
                  composer_version=flags.MIN_TRIGGERER_COMPOSER_VERSION,
                  airflow_version=flags.MIN_TRIGGERER_AIRFLOW_VERSION,
              )
          )
    if not (
        args.enable_triggerer
        or (args.triggerer_count and args.triggerer_count > 0)
    ):
      if args.triggerer_cpu:
        raise command_util.InvalidUserInputError(
            flags.ENABLED_TRIGGERER_IS_REQUIRED_MSG.format(opt='triggerer-cpu')
        )
      if args.triggerer_memory:
        raise command_util.InvalidUserInputError(
            flags.ENABLED_TRIGGERER_IS_REQUIRED_MSG.format(
                opt='triggerer-memory'
            )
        )

  def ValidateComposer3Flags(self, args):
    pass

  def ParseComposer3Flags(self, args):
    pass

  def ValidateFlagsAddedInComposer2(self, args, is_composer_v1, release_track):
    """Raises InputError if flags from Composer v2 are used when creating v1."""
    if args.environment_size and is_composer_v1:
      raise command_util.InvalidUserInputError(
          _INVALID_OPTION_FOR_V1_ERROR_MSG.format(opt='environment-size'))
    composer_v2_flag_used = (
        args.scheduler_cpu or args.worker_cpu or args.web_server_cpu or
        args.scheduler_memory or args.worker_memory or args.web_server_memory or
        args.scheduler_storage or args.worker_storage or
        args.web_server_storage or args.min_workers or args.max_workers)
    if composer_v2_flag_used and is_composer_v1:
      raise command_util.InvalidUserInputError(
          'Workloads Config flags introduced in Composer 2.X'
          ' cannot be used when creating Composer 1.X environments.')
    if args.enable_high_resilience and is_composer_v1:
      raise command_util.InvalidUserInputError(
          _INVALID_OPTION_FOR_V1_ERROR_MSG.format(opt='enable-high-resilience'))
    if args.enable_logs_in_cloud_logging_only and is_composer_v1:
      raise command_util.InvalidUserInputError(
          _INVALID_OPTION_FOR_V1_ERROR_MSG.format(
              opt='enable-logs-in-cloud-logging-only'
          )
      )
    if args.disable_logs_in_cloud_logging_only and is_composer_v1:
      raise command_util.InvalidUserInputError(
          _INVALID_OPTION_FOR_V1_ERROR_MSG.format(
              opt='disable-logs-in-cloud-logging-only'
          )
      )
    if args.enable_cloud_data_lineage_integration and is_composer_v1:
      raise command_util.InvalidUserInputError(
          _INVALID_OPTION_FOR_V1_ERROR_MSG.format(
              opt='enable-cloud-data-lineage-integration'
          )
      )
    if args.disable_cloud_data_lineage_integration and is_composer_v1:
      raise command_util.InvalidUserInputError(
          _INVALID_OPTION_FOR_V1_ERROR_MSG.format(
              opt='disable-cloud-data-lineage-integration'
          )
      )
    if args.cloud_sql_preferred_zone and is_composer_v1:
      raise command_util.InvalidUserInputError(
          _INVALID_OPTION_FOR_V1_ERROR_MSG.format(
              opt='cloud-sql-preferred-zone'
          )
      )
    if args.connection_subnetwork and is_composer_v1:
      raise command_util.InvalidUserInputError(
          _INVALID_OPTION_FOR_V1_ERROR_MSG.format(opt='connection-subnetwork'))
    if args.connection_subnetwork and not args.enable_private_environment:
      raise command_util.InvalidUserInputError(
          flags.PREREQUISITE_OPTION_ERROR_MSG.format(
              prerequisite='enable-private-environment',
              opt='connection-subnetwork'))
    if args.connection_type and is_composer_v1:
      raise command_util.InvalidUserInputError(
          _INVALID_OPTION_FOR_V1_ERROR_MSG.format(opt='connection-type'))
    if args.connection_type and not args.enable_private_environment:
      raise command_util.InvalidUserInputError(
          flags.PREREQUISITE_OPTION_ERROR_MSG.format(
              prerequisite='enable-private-environment', opt='connection-type'))
    if (args.connection_type and args.connection_type == 'vpc-peering' and
        args.connection_subnetwork):
      raise command_util.InvalidUserInputError(
          'You cannot specify a connection subnetwork if connection type '
          "'VPC_PEERING' is selected.")

  def ValidateComposer1ExclusiveFlags(self, args, is_composer_v1,
                                      release_track):
    """Raises InputError if flags from Composer v2 are used when creating v1."""
    # Composer 2 flags are currently unavailable in GA release track.
    if args.python_version and not is_composer_v1:
      raise command_util.InvalidUserInputError(
          _INVALID_OPTION_FOR_V2_ERROR_MSG.format(opt='python-version'))
    if args.disk_size and not is_composer_v1:
      raise command_util.InvalidUserInputError(
          _INVALID_OPTION_FOR_V2_ERROR_MSG.format(opt='disk-size'))
    if args.machine_type and not is_composer_v1:
      raise command_util.InvalidUserInputError(
          _INVALID_OPTION_FOR_V2_ERROR_MSG.format(opt='machine-type'))

  def GetOperationMessage(self, args, is_composer_v1):
    """Constructs Create message."""

    create_flags = environments_api_util.CreateEnvironmentFlags(
        node_count=args.node_count,
        labels=args.labels,
        location=self.zone,
        machine_type=self.machine_type,
        network=self.network,
        subnetwork=self.subnetwork,
        env_variables=args.env_variables,
        airflow_config_overrides=args.airflow_configs,
        service_account=args.service_account,
        oauth_scopes=args.oauth_scopes,
        tags=args.tags,
        disk_size_gb=environments_api_util.DiskSizeBytesToGB(args.disk_size),
        python_version=args.python_version,
        image_version=self.image_version,
        use_ip_aliases=args.enable_ip_alias,
        cluster_secondary_range_name=args.cluster_secondary_range_name,
        services_secondary_range_name=args.services_secondary_range_name,
        cluster_ipv4_cidr_block=args.cluster_ipv4_cidr,
        services_ipv4_cidr_block=args.services_ipv4_cidr,
        enable_ip_masq_agent=args.enable_ip_masq_agent,
        kms_key=self.kms_key,
        private_environment=args.enable_private_environment,
        private_endpoint=args.enable_private_endpoint,
        privately_used_public_ips=args.enable_privately_used_public_ips,
        master_ipv4_cidr=args.master_ipv4_cidr,
        web_server_ipv4_cidr=args.web_server_ipv4_cidr,
        cloud_sql_ipv4_cidr=args.cloud_sql_ipv4_cidr,
        composer_network_ipv4_cidr=args.composer_network_ipv4_cidr,
        web_server_access_control=self.web_server_access_control,
        connection_subnetwork=args.connection_subnetwork,
        connection_type=args.connection_type,
        cloud_sql_machine_type=args.cloud_sql_machine_type,
        web_server_machine_type=args.web_server_machine_type,
        scheduler_cpu=args.scheduler_cpu,
        triggerer_cpu=args.triggerer_cpu,
        triggerer_count=args.triggerer_count,
        worker_cpu=args.worker_cpu,
        web_server_cpu=args.web_server_cpu,
        scheduler_memory_gb=environments_api_util.MemorySizeBytesToGB(
            args.scheduler_memory
        ),
        triggerer_memory_gb=environments_api_util.MemorySizeBytesToGB(
            args.triggerer_memory
        ),
        worker_memory_gb=environments_api_util.MemorySizeBytesToGB(
            args.worker_memory
        ),
        web_server_memory_gb=environments_api_util.MemorySizeBytesToGB(
            args.web_server_memory
        ),
        scheduler_storage_gb=environments_api_util.MemorySizeBytesToGB(
            args.scheduler_storage
        ),
        worker_storage_gb=environments_api_util.MemorySizeBytesToGB(
            args.worker_storage
        ),
        web_server_storage_gb=environments_api_util.MemorySizeBytesToGB(
            args.web_server_storage
        ),
        min_workers=args.min_workers,
        max_workers=args.max_workers,
        scheduler_count=args.scheduler_count,
        enable_triggerer=args.enable_triggerer,
        environment_size=args.environment_size,
        maintenance_window_start=args.maintenance_window_start,
        maintenance_window_end=args.maintenance_window_end,
        maintenance_window_recurrence=args.maintenance_window_recurrence,
        enable_master_authorized_networks=(
            args.enable_master_authorized_networks
        ),
        master_authorized_networks=args.master_authorized_networks,
        enable_scheduled_snapshot_creation=(
            args.enable_scheduled_snapshot_creation
        ),
        snapshot_creation_schedule=args.snapshot_creation_schedule,
        snapshot_location=args.snapshot_location,
        snapshot_schedule_timezone=args.snapshot_schedule_timezone,
        enable_cloud_data_lineage_integration=args.enable_cloud_data_lineage_integration,
        disable_cloud_data_lineage_integration=args.disable_cloud_data_lineage_integration,
        enable_high_resilience=args.enable_high_resilience,
        enable_logs_in_cloud_logging_only=args.enable_logs_in_cloud_logging_only,
        disable_logs_in_cloud_logging_only=args.disable_logs_in_cloud_logging_only,
        cloud_sql_preferred_zone=args.cloud_sql_preferred_zone,
        release_track=self.ReleaseTrack(),
        storage_bucket=args.storage_bucket,
        airflow_database_retention_days=args.airflow_database_retention_days,
    )
    return environments_api_util.Create(self.env_ref, create_flags,
                                        is_composer_v1)


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class CreateBeta(Create):
  """Create and initialize a Cloud Composer environment.

  If run asynchronously with `--async`, exits after printing an operation
  that can be used to poll the status of the creation operation via:

    {top_command} composer operations describe
  """

  _support_max_pods_per_node = True

  @classmethod
  def Args(cls, parser, release_track=base.ReleaseTrack.BETA):
    super(CreateBeta, cls).Args(parser, release_track)

    AddComposer3Flags(parser)

  def GetOperationMessage(self, args, is_composer_v1):
    """See base class."""

    create_flags = environments_api_util.CreateEnvironmentFlags(
        node_count=args.node_count,
        labels=args.labels,
        location=self.zone,
        machine_type=self.machine_type,
        network=self.network,
        subnetwork=self.subnetwork,
        network_attachment=args.network_attachment,
        env_variables=args.env_variables,
        airflow_config_overrides=args.airflow_configs,
        service_account=args.service_account,
        oauth_scopes=args.oauth_scopes,
        tags=args.tags,
        disk_size_gb=environments_api_util.DiskSizeBytesToGB(args.disk_size),
        python_version=args.python_version,
        image_version=self.image_version,
        use_ip_aliases=args.enable_ip_alias,
        cluster_secondary_range_name=args.cluster_secondary_range_name,
        services_secondary_range_name=args.services_secondary_range_name,
        cluster_ipv4_cidr_block=args.cluster_ipv4_cidr,
        services_ipv4_cidr_block=args.services_ipv4_cidr,
        max_pods_per_node=args.max_pods_per_node,
        kms_key=self.kms_key,
        private_environment=args.enable_private_environment,
        private_endpoint=args.enable_private_endpoint,
        privately_used_public_ips=args.enable_privately_used_public_ips,
        connection_subnetwork=args.connection_subnetwork,
        connection_type=args.connection_type,
        master_ipv4_cidr=args.master_ipv4_cidr,
        web_server_ipv4_cidr=args.web_server_ipv4_cidr,
        cloud_sql_ipv4_cidr=args.cloud_sql_ipv4_cidr,
        composer_network_ipv4_cidr=args.composer_network_ipv4_cidr,
        enable_ip_masq_agent=args.enable_ip_masq_agent,
        web_server_access_control=self.web_server_access_control,
        cloud_sql_machine_type=args.cloud_sql_machine_type,
        web_server_machine_type=args.web_server_machine_type,
        scheduler_cpu=args.scheduler_cpu,
        triggerer_cpu=args.triggerer_cpu,
        triggerer_count=args.triggerer_count,
        worker_cpu=args.worker_cpu,
        web_server_cpu=args.web_server_cpu,
        scheduler_memory_gb=environments_api_util.MemorySizeBytesToGB(
            args.scheduler_memory
        ),
        triggerer_memory_gb=environments_api_util.MemorySizeBytesToGB(
            args.triggerer_memory
        ),
        worker_memory_gb=environments_api_util.MemorySizeBytesToGB(
            args.worker_memory
        ),
        web_server_memory_gb=environments_api_util.MemorySizeBytesToGB(
            args.web_server_memory
        ),
        scheduler_storage_gb=environments_api_util.MemorySizeBytesToGB(
            args.scheduler_storage
        ),
        worker_storage_gb=environments_api_util.MemorySizeBytesToGB(
            args.worker_storage
        ),
        web_server_storage_gb=environments_api_util.MemorySizeBytesToGB(
            args.web_server_storage
        ),
        min_workers=args.min_workers,
        max_workers=args.max_workers,
        scheduler_count=args.scheduler_count,
        enable_triggerer=args.enable_triggerer,
        maintenance_window_start=args.maintenance_window_start,
        maintenance_window_end=args.maintenance_window_end,
        maintenance_window_recurrence=args.maintenance_window_recurrence,
        environment_size=args.environment_size,
        enable_master_authorized_networks=args.enable_master_authorized_networks,
        master_authorized_networks=args.master_authorized_networks,
        enable_scheduled_snapshot_creation=args.enable_scheduled_snapshot_creation,
        snapshot_creation_schedule=args.snapshot_creation_schedule,
        snapshot_location=args.snapshot_location,
        snapshot_schedule_timezone=args.snapshot_schedule_timezone,
        enable_cloud_data_lineage_integration=args.enable_cloud_data_lineage_integration,
        disable_cloud_data_lineage_integration=args.disable_cloud_data_lineage_integration,
        enable_high_resilience=args.enable_high_resilience,
        enable_logs_in_cloud_logging_only=args.enable_logs_in_cloud_logging_only,
        disable_logs_in_cloud_logging_only=args.disable_logs_in_cloud_logging_only,
        cloud_sql_preferred_zone=args.cloud_sql_preferred_zone,
        support_web_server_plugins=args.support_web_server_plugins,
        dag_processor_cpu=args.dag_processor_cpu,
        dag_processor_count=args.dag_processor_count,
        dag_processor_memory_gb=environments_api_util.MemorySizeBytesToGB(
            args.dag_processor_memory
        ),
        dag_processor_storage_gb=environments_api_util.MemorySizeBytesToGB(
            args.dag_processor_storage
        ),
        composer_internal_ipv4_cidr_block=args.composer_internal_ipv4_cidr_block,
        enable_private_builds_only=args.enable_private_builds_only,
        disable_private_builds_only=args.disable_private_builds_only,
        release_track=self.ReleaseTrack(),
        storage_bucket=args.storage_bucket,
        airflow_database_retention_days=args.airflow_database_retention_days,
    )

    return environments_api_util.Create(self.env_ref, create_flags,
                                        is_composer_v1)

  def ValidateComposer3Flags(self, args):
    is_composer3 = self.isComposer3(args)
    # Composer2 flags that are not supported in Composer3
    forbidden_args = {
        'cloud-sql-ipv4-cidr': args.cloud_sql_ipv4_cidr,
        'composer-network-ipv4-cidr': args.composer_network_ipv4_cidr,
        'connection-subnetwork': args.connection_subnetwork,
        'enable-private-endpoint': args.enable_private_endpoint,
        'master-ipv4-cidr': args.master_ipv4_cidr,
    }
    possible_args = {
        'support-web-server-plugins': args.support_web_server_plugins,
        'dag-processor-cpu': args.dag_processor_cpu,
        'dag-processor-memory': args.dag_processor_memory,
        'dag-processor-count': args.dag_processor_count,
        'dag-processor-storage': args.dag_processor_storage,
        'network-attachment': args.network_attachment,
        'composer-internal-ipv4-cidr-block': (
            args.composer_internal_ipv4_cidr_block
        ),
        'enable-private-builds-only': args.enable_private_builds_only,
        'disable-private-builds-only': args.disable_private_builds_only,
    }

    for k, v in possible_args.items():
      if v is not None and not is_composer3:
        raise command_util.InvalidUserInputError(
            flags.COMPOSER3_IS_REQUIRED_MSG.format(
                opt=k,
                composer_version=flags.MIN_COMPOSER3_VERSION,
            )
        )
    for k, v in forbidden_args.items():
      if v is not None and is_composer3:
        raise command_util.InvalidUserInputError(
            flags.COMPOSER3_IS_NOT_SUPPORTED_MSG.format(
                opt=k,
                composer_version=flags.MIN_COMPOSER3_VERSION,
            )
        )
    if args.network_attachment and (args.network or args.subnetwork):
      raise command_util.InvalidUserInputError(
          'argument --network-attachment: At most one of --network-attachment'
          ' | [--network : --subnetwork] can be specified'
      )

  def ValidateTriggererFlags(self, args):
    if args.image_version:
      triggerer_supported = image_versions_util.IsVersionTriggererCompatible(
          args.image_version)
      possible_args = {
          'enable-triggerer': args.enable_triggerer,
          'triggerer-cpu': args.triggerer_cpu,
          'triggerer-memory': args.triggerer_memory,
          'triggerer-count': args.triggerer_count,
      }
      for k, v in possible_args.items():
        if v and not triggerer_supported:
          raise command_util.InvalidUserInputError(
              flags.INVALID_OPTION_FOR_MIN_IMAGE_VERSION_ERROR_MSG.format(
                  opt=k,
                  composer_version=flags.MIN_TRIGGERER_COMPOSER_VERSION,
                  airflow_version=flags.MIN_TRIGGERER_AIRFLOW_VERSION))
    if not (args.enable_triggerer or (args.triggerer_count and
                                      args.triggerer_count > 0)):
      if args.triggerer_cpu:
        raise command_util.InvalidUserInputError(
            flags.ENABLED_TRIGGERER_IS_REQUIRED_MSG.format(
                opt='triggerer-cpu'))
      if args.triggerer_memory:
        raise command_util.InvalidUserInputError(
            flags.ENABLED_TRIGGERER_IS_REQUIRED_MSG.format(
                opt='triggerer-memory'))

  def isComposer3(self, args):
    return image_versions_util.IsVersionComposer3Compatible(args.image_version)

  def ParseComposer3Flags(self, args):
    if args.network_attachment:
      args.network_attachment = parsers.ParseNetworkAttachment(
          args.network_attachment, fallback_region=self.env_ref.Parent().Name()
      ).RelativeName()


def AddLineageIntegrationParser(parser):
  """Adds lineage integration flags to the parser."""

  lineage_params_group = parser.add_mutually_exclusive_group()

  flags.ENABLE_CLOUD_DATA_LINEAGE_INTEGRATION_FLAG.AddToParser(
      lineage_params_group
  )
  flags.DISABLE_CLOUD_DATA_LINEAGE_INTEGRATION_FLAG.AddToParser(
      lineage_params_group
  )


def AddComposer3Flags(parser):
  """Adds Composer 3 flags to the parser."""
  # web-server-plugins-support
  flags.SUPPORT_WEB_SERVER_PLUGINS.AddToParser(parser)
  # Dag processor
  dag_processor_params_group = parser.add_argument_group(
      flags.DAG_PROCESSOR_PARAMETERS_FLAG_GROUP_DESCRIPTION,
      hidden=True,
  )
  flags.DAG_PROCESSOR_CPU.AddToParser(dag_processor_params_group)
  flags.DAG_PROCESSOR_COUNT.AddToParser(dag_processor_params_group)
  flags.DAG_PROCESSOR_MEMORY.AddToParser(dag_processor_params_group)
  flags.DAG_PROCESSOR_STORAGE.AddToParser(dag_processor_params_group)
  # other flags
  flags.COMPOSER_INTERNAL_IPV4_CIDR_FLAG.AddToParser(parser)
  # support-private-builds-only
  private_builds_only_group = parser.add_mutually_exclusive_group(hidden=True)
  flags.ENABLE_PRIVATE_BUILDS_ONLY.AddToParser(private_builds_only_group)
  flags.DISABLE_PRIVATE_BUILDS_ONLY.AddToParser(private_builds_only_group)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class CreateAlpha(CreateBeta):
  """Create and initialize a Cloud Composer environment.

  If run asynchronously with `--async`, exits after printing an operation
  that can be used to poll the status of the creation operation via:

    {top_command} composer operations describe
  """

  @classmethod
  def Args(cls, parser, release_track=base.ReleaseTrack.ALPHA):
    super(CreateAlpha, cls).Args(parser, release_track)

    # Adding alpha arguments
    parser.add_argument(
        '--airflow-executor-type',
        hidden=True,
        choices={
            'CELERY': 'Task instances will run by CELERY executor',
            'KUBERNETES': 'Task instances will run by KUBERNETES executor'
        },
        help="""The type of executor by which task instances are run on Airflow;
        currently supported executor types are CELERY and KUBERNETES.
        Defaults to CELERY. Cannot be updated.""")

  def GetOperationMessage(self, args, is_composer_v1):
    """See base class."""

    create_flags = environments_api_util.CreateEnvironmentFlags(
        node_count=args.node_count,
        environment_size=args.environment_size,
        labels=args.labels,
        location=self.zone,
        machine_type=self.machine_type,
        network=self.network,
        subnetwork=self.subnetwork,
        network_attachment=args.network_attachment,
        env_variables=args.env_variables,
        airflow_config_overrides=args.airflow_configs,
        service_account=args.service_account,
        oauth_scopes=args.oauth_scopes,
        tags=args.tags,
        disk_size_gb=environments_api_util.DiskSizeBytesToGB(args.disk_size),
        python_version=args.python_version,
        image_version=self.image_version,
        airflow_executor_type=args.airflow_executor_type,
        use_ip_aliases=args.enable_ip_alias,
        cluster_secondary_range_name=args.cluster_secondary_range_name,
        services_secondary_range_name=args.services_secondary_range_name,
        cluster_ipv4_cidr_block=args.cluster_ipv4_cidr,
        services_ipv4_cidr_block=args.services_ipv4_cidr,
        max_pods_per_node=args.max_pods_per_node,
        enable_ip_masq_agent=args.enable_ip_masq_agent,
        kms_key=self.kms_key,
        private_environment=args.enable_private_environment,
        private_endpoint=args.enable_private_endpoint,
        web_server_ipv4_cidr=args.web_server_ipv4_cidr,
        cloud_sql_ipv4_cidr=args.cloud_sql_ipv4_cidr,
        composer_network_ipv4_cidr=args.composer_network_ipv4_cidr,
        master_ipv4_cidr=args.master_ipv4_cidr,
        privately_used_public_ips=args.enable_privately_used_public_ips,
        connection_subnetwork=args.connection_subnetwork,
        connection_type=args.connection_type,
        web_server_access_control=self.web_server_access_control,
        cloud_sql_machine_type=args.cloud_sql_machine_type,
        web_server_machine_type=args.web_server_machine_type,
        scheduler_cpu=args.scheduler_cpu,
        triggerer_cpu=args.triggerer_cpu,
        triggerer_count=args.triggerer_count,
        worker_cpu=args.worker_cpu,
        web_server_cpu=args.web_server_cpu,
        scheduler_memory_gb=environments_api_util.MemorySizeBytesToGB(
            args.scheduler_memory
        ),
        triggerer_memory_gb=environments_api_util.MemorySizeBytesToGB(
            args.triggerer_memory
        ),
        worker_memory_gb=environments_api_util.MemorySizeBytesToGB(
            args.worker_memory
        ),
        web_server_memory_gb=environments_api_util.MemorySizeBytesToGB(
            args.web_server_memory
        ),
        scheduler_storage_gb=environments_api_util.MemorySizeBytesToGB(
            args.scheduler_storage
        ),
        worker_storage_gb=environments_api_util.MemorySizeBytesToGB(
            args.worker_storage
        ),
        web_server_storage_gb=environments_api_util.MemorySizeBytesToGB(
            args.web_server_storage
        ),
        min_workers=args.min_workers,
        max_workers=args.max_workers,
        scheduler_count=args.scheduler_count,
        enable_triggerer=args.enable_triggerer,
        maintenance_window_start=args.maintenance_window_start,
        maintenance_window_end=args.maintenance_window_end,
        maintenance_window_recurrence=args.maintenance_window_recurrence,
        enable_master_authorized_networks=args.enable_master_authorized_networks,
        master_authorized_networks=args.master_authorized_networks,
        airflow_database_retention_days=args.airflow_database_retention_days,
        enable_scheduled_snapshot_creation=args.enable_scheduled_snapshot_creation,
        snapshot_creation_schedule=args.snapshot_creation_schedule,
        snapshot_location=args.snapshot_location,
        snapshot_schedule_timezone=args.snapshot_schedule_timezone,
        enable_cloud_data_lineage_integration=args.enable_cloud_data_lineage_integration,
        disable_cloud_data_lineage_integration=args.disable_cloud_data_lineage_integration,
        enable_high_resilience=args.enable_high_resilience,
        enable_logs_in_cloud_logging_only=args.enable_logs_in_cloud_logging_only,
        disable_logs_in_cloud_logging_only=args.disable_logs_in_cloud_logging_only,
        cloud_sql_preferred_zone=args.cloud_sql_preferred_zone,
        support_web_server_plugins=args.support_web_server_plugins,
        dag_processor_cpu=args.dag_processor_cpu,
        dag_processor_count=args.dag_processor_count,
        dag_processor_memory_gb=environments_api_util.MemorySizeBytesToGB(
            args.dag_processor_memory
        ),
        dag_processor_storage_gb=environments_api_util.MemorySizeBytesToGB(
            args.dag_processor_storage
        ),
        composer_internal_ipv4_cidr_block=args.composer_internal_ipv4_cidr_block,
        enable_private_builds_only=args.enable_private_builds_only,
        disable_private_builds_only=args.disable_private_builds_only,
        release_track=self.ReleaseTrack(),
        storage_bucket=args.storage_bucket,
    )

    return environments_api_util.Create(self.env_ref, create_flags,
                                        is_composer_v1)
