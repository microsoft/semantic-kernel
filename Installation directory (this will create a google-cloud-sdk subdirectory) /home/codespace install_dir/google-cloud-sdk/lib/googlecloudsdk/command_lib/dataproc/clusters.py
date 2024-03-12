# -*- coding: utf-8 -*- #
# Copyright 2015 Google LLC. All Rights Reserved.
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
"""Utilities for building the dataproc clusters CLI."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import collections
import re
import textwrap

from apitools.base.py import encoding
from googlecloudsdk.api_lib.compute import utils as api_utils
from googlecloudsdk.api_lib.dataproc import compute_helpers
from googlecloudsdk.api_lib.dataproc import constants
from googlecloudsdk.api_lib.dataproc import exceptions
from googlecloudsdk.api_lib.dataproc import storage_helpers
from googlecloudsdk.api_lib.dataproc import util
from googlecloudsdk.calliope import actions
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.command_lib.compute.instances import flags as instances_flags
from googlecloudsdk.command_lib.dataproc import flags
from googlecloudsdk.command_lib.kms import resource_args as kms_resource_args
from googlecloudsdk.command_lib.util.apis import arg_utils
from googlecloudsdk.command_lib.util.args import labels_util
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core import yaml
from googlecloudsdk.core.console import console_io
from googlecloudsdk.core.util import times
import six

GENERATED_LABEL_PREFIX = 'goog-dataproc-'


# beta is unused but still useful when we add new beta features
# pylint: disable=unused-argument
def ArgsForClusterRef(
    parser,
    dataproc,
    beta=False,
    alpha=False,
    include_deprecated=True,
    include_ttl_config=False,
    include_gke_platform_args=False,
    include_driver_pool_args=False,
):
  """Register flags for creating a dataproc cluster.

  Args:
    parser: The argparse.ArgParser to configure with dataproc cluster arguments.
    dataproc: Dataproc object that contains client, messages, and resources.
    beta: whether or not this is a beta command (may affect flag visibility)
    alpha: whether or not this is a alpha command (may affect flag visibility)
    include_deprecated: whether deprecated flags should be included
    include_ttl_config: whether to include Scheduled Delete(TTL) args
    include_gke_platform_args: whether to include GKE-based cluster args
    include_driver_pool_args: whether to include driver pool cluster args
  """
  labels_util.AddCreateLabelsFlags(parser)
  # 30m is backend timeout + 5m for safety buffer.
  flags.AddTimeoutFlag(parser, default='35m')
  flags.AddZoneFlag(parser, short_flags=include_deprecated)
  flags.AddComponentFlag(parser)

  platform_group = parser.add_argument_group(mutex=True)
  gce_platform_group = platform_group.add_argument_group(help="""\
    Compute Engine options for Dataproc clusters.
    """)

  instances_flags.AddTagsArgs(gce_platform_group)
  gce_platform_group.add_argument(
      '--metadata',
      type=arg_parsers.ArgDict(min_length=1),
      action='append',
      default=None,
      help=(
          'Metadata to be made available to the guest operating system '
          'running on the instances'
      ),
      metavar='KEY=VALUE',
  )

  # Either allow creating a single node cluster (--single-node), or specifying
  # the number of workers in the multi-node cluster (--num-workers and
  # --num-secondary-workers)
  node_group = parser.add_argument_group(mutex=True)  # Mutually exclusive
  node_group.add_argument(
      '--single-node',
      action='store_true',
      help="""\
      Create a single node cluster.

      A single node cluster has all master and worker components.
      It cannot have any separate worker nodes. If this flag is not
      specified, a cluster with separate workers is created.
      """,
  )
  # Not mutually exclusive
  worker_group = node_group.add_argument_group(help='Multi-node cluster flags')
  worker_group.add_argument(
      '--num-workers',
      type=int,
      help=(
          'The number of worker nodes in the cluster. Defaults to '
          'server-specified.'
      ),
  )

  min_workers = worker_group.add_argument_group(mutex=True)
  min_workers.add_argument(
      '--min-num-workers',
      type=int,
      help=(
          'Minimum number of primary worker nodes to provision for cluster'
          ' creation to succeed.'
      ),
  )
  min_workers.add_argument(
      '--min-worker-fraction',
      type=float,
      hidden=True,
      metavar='[0-1]',
      help=(
          'Minimum fraction of worker nodes required to create the cluster.'
          ' If it is not met, cluster creation will fail. Must be a decimal'
          ' value between 0 and 1. The number of required workers will be'
          ' calcualted by ceil(min-worker-fraction * num_workers).'
      ),
  )
  worker_group.add_argument(
      '--secondary-worker-type',
      metavar='TYPE',
      choices=['preemptible', 'non-preemptible', 'spot'],
      default='preemptible',
      help='The type of the secondary worker group.',
  )
  num_secondary_workers = worker_group.add_argument_group(mutex=True)
  num_secondary_workers.add_argument(
      '--num-preemptible-workers',
      action=actions.DeprecationAction(
          '--num-preemptible-workers',
          warn=(
              'The `--num-preemptible-workers` flag is deprecated. '
              'Use the `--num-secondary-workers` flag instead.'
          ),
      ),
      type=int,
      hidden=True,
      help='The number of preemptible worker nodes in the cluster.',
  )
  num_secondary_workers.add_argument(
      '--num-secondary-workers',
      type=int,
      help='The number of secondary worker nodes in the cluster.',
  )

  parser.add_argument(
      '--master-machine-type',
      help=(
          'The type of machine to use for the master. Defaults to '
          'server-specified.'
      ),
  )
  parser.add_argument(
      '--worker-machine-type',
      help=(
          'The type of machine to use for workers. Defaults to '
          'server-specified.'
      ),
  )
  parser.add_argument(
      '--min-secondary-worker-fraction',
      help=(
          'Minimum fraction of secondary worker nodes required to create the'
          ' cluster. If it is not met, cluster creation will fail. Must be a'
          ' decimal value between 0 and 1. The number of required secondary'
          ' workers is calculated by ceil(min-secondary-worker-fraction *'
          ' num_secondary_workers). Defaults to 0.0001.'
      ),
      type=float,
  )
  kms_resource_args.AddKmsKeyResourceArg(parser, 'cluster', name='--kms-key')

  if alpha:
    parser.add_argument(
        '--secondary-worker-standard-capacity-base',
        hidden=False,
        type=int,
        help='The number of standard VMs in the Spot and Standard Mix feature.',
    )
  parser.add_argument(
      '--secondary-worker-machine-types',
      help=(
          'Types of machines with optional rank for secondary workers to use. '
          'Defaults to server-specified.'
          'eg. --secondary-worker-machine-types="type=e2-standard-8,type=t2d-standard-8,rank=0"'
      ),
      metavar='type=MACHINE_TYPE[,type=MACHINE_TYPE...][,rank=RANK]',
      type=ArgMultiValueDict(),
      action=arg_parsers.FlattenAction(),
  )
  image_parser = parser.add_mutually_exclusive_group()
  # TODO(b/73291743): Add external doc link to --image
  image_parser.add_argument(
      '--image',
      metavar='IMAGE',
      help=(
          'The custom image used to create the cluster. It can '
          'be the image name, the image URI, or the image family URI, which '
          'selects the latest image from the family.'
      ),
  )
  image_parser.add_argument(
      '--image-version',
      metavar='VERSION',
      help=(
          'The image version to use for the cluster. Defaults to the '
          'latest version.'
      ),
  )
  parser.add_argument(
      '--bucket',
      help="""\
      The Google Cloud Storage bucket to use by default to stage job
      dependencies, miscellaneous config files, and job driver console output
      when using this cluster.
      """,
  )
  parser.add_argument(
      '--temp-bucket',
      help="""\
      The Google Cloud Storage bucket to use by default to store
      ephemeral cluster and jobs data, such as Spark and MapReduce history files.
      """,
  )

  netparser = gce_platform_group.add_argument_group(mutex=True)
  netparser.add_argument(
      '--network',
      help="""\
      The Compute Engine network that the VM instances of the cluster will be
      part of. This is mutually exclusive with --subnet. If neither is
      specified, this defaults to the "default" network.
      """,
  )
  netparser.add_argument(
      '--subnet',
      help="""\
      Specifies the subnet that the cluster will be part of. This is mutally
      exclusive with --network.
      """,
  )
  parser.add_argument(
      '--num-worker-local-ssds',
      type=int,
      help='The number of local SSDs to attach to each worker in a cluster.',
  )
  parser.add_argument(
      '--num-master-local-ssds',
      type=int,
      help='The number of local SSDs to attach to the master in a cluster.',
  )
  secondary_worker_local_ssds = parser.add_argument_group(mutex=True)
  secondary_worker_local_ssds.add_argument(
      '--num-preemptible-worker-local-ssds',
      type=int,
      hidden=True,
      action=actions.DeprecationAction(
          '--num-preemptible-worker-local-ssds',
          warn=(
              'The `--num-preemptible-worker-local-ssds` flag is deprecated. '
              'Use the `--num-secondary-worker-local-ssds` flag instead.'
          ),
      ),
      help="""\
      The number of local SSDs to attach to each secondary worker in
      a cluster.
      """,
  )
  secondary_worker_local_ssds.add_argument(
      '--num-secondary-worker-local-ssds',
      type=int,
      help="""\
      The number of local SSDs to attach to each preemptible worker in
      a cluster.
      """,
  )
  parser.add_argument(
      '--master-local-ssd-interface',
      help="""\
      Interface to use to attach local SSDs to master node(s) in a cluster.
      """,
  )
  parser.add_argument(
      '--worker-local-ssd-interface',
      help="""\
      Interface to use to attach local SSDs to each worker in a cluster.
      """,
  )
  parser.add_argument(
      '--secondary-worker-local-ssd-interface',
      help="""\
      Interface to use to attach local SSDs to each secondary worker
      in a cluster.
      """,
  )
  parser.add_argument(
      '--initialization-actions',
      type=arg_parsers.ArgList(min_length=1),
      metavar='CLOUD_STORAGE_URI',
      help=(
          'A list of Google Cloud Storage URIs of '
          'executables to run on each node in the cluster.'
      ),
  )
  parser.add_argument(
      '--initialization-action-timeout',
      type=arg_parsers.Duration(),
      metavar='TIMEOUT',
      default='10m',
      help=(
          'The maximum duration of each initialization action. See '
          '$ gcloud topic datetimes for information on duration formats.'
      ),
  )
  parser.add_argument(
      '--num-masters',
      type=arg_parsers.CustomFunctionValidator(
          lambda n: int(n) in [1, 3],
          'Number of masters must be 1 (Standard) or 3 (High Availability)',
          parser=arg_parsers.BoundedInt(1, 3),
      ),
      help="""\
      The number of master nodes in the cluster.

      Number of Masters | Cluster Mode
      --- | ---
      1 | Standard
      3 | High Availability
      """,
  )
  parser.add_argument(
      '--properties',
      type=arg_parsers.ArgDict(),
      action=arg_parsers.UpdateAction,
      default={},
      metavar='PREFIX:PROPERTY=VALUE',
      help="""\
Specifies configuration properties for installed packages, such as Hadoop
and Spark.

Properties are mapped to configuration files by specifying a prefix, such as
"core:io.serializations". The following are supported prefixes and their
mappings:

Prefix | File | Purpose of file
--- | --- | ---
capacity-scheduler | capacity-scheduler.xml | Hadoop YARN Capacity Scheduler configuration
core | core-site.xml | Hadoop general configuration
distcp | distcp-default.xml | Hadoop Distributed Copy configuration
hadoop-env | hadoop-env.sh | Hadoop specific environment variables
hdfs | hdfs-site.xml | Hadoop HDFS configuration
hive | hive-site.xml | Hive configuration
mapred | mapred-site.xml | Hadoop MapReduce configuration
mapred-env | mapred-env.sh | Hadoop MapReduce specific environment variables
pig | pig.properties | Pig configuration
spark | spark-defaults.conf | Spark configuration
spark-env | spark-env.sh | Spark specific environment variables
yarn | yarn-site.xml | Hadoop YARN configuration
yarn-env | yarn-env.sh | Hadoop YARN specific environment variables

See https://cloud.google.com/dataproc/docs/concepts/configuring-clusters/cluster-properties
for more information.

""",
  )
  gce_platform_group.add_argument(
      '--service-account',
      help='The Google Cloud IAM service account to be authenticated as.',
  )
  gce_platform_group.add_argument(
      '--scopes',
      type=arg_parsers.ArgList(min_length=1),
      metavar='SCOPE',
      help="""\
Specifies scopes for the node instances. Multiple SCOPEs can be specified,
separated by commas.
Examples:

  $ {{command}} example-cluster --scopes https://www.googleapis.com/auth/bigtable.admin

  $ {{command}} example-cluster --scopes sqlservice,bigquery

The following *minimum scopes* are necessary for the cluster to function
properly and are always added, even if not explicitly specified:

  {minimum_scopes}

If the `--scopes` flag is not specified, the following *default scopes*
are also included:

  {additional_scopes}

If you want to enable all scopes use the 'cloud-platform' scope.

{scopes_help}
""".format(
          minimum_scopes='\n  '.join(constants.MINIMUM_SCOPE_URIS),
          additional_scopes='\n  '.join(
              constants.ADDITIONAL_DEFAULT_SCOPE_URIS
          ),
          scopes_help=compute_helpers.SCOPES_HELP,
      ),
  )

  if include_deprecated:
    _AddDiskArgsDeprecated(parser, include_driver_pool_args)
  else:
    _AddDiskArgs(parser, include_driver_pool_args)

  ip_address_parser = parser.add_mutually_exclusive_group()

  # --no-address is an exception to the no negative-flag style guildline to be
  # consistent with gcloud compute instances create --no-address
  ip_address_parser.add_argument(
      '--no-address',
      action='store_true',
      help="""\
      If provided, the instances in the cluster will not be assigned external
      IP addresses.

      If omitted, then the Dataproc service will apply a default policy to determine if each instance in the cluster gets an external IP address or not.

      Note: Dataproc VMs need access to the Dataproc API. This can be achieved
      without external IP addresses using Private Google Access
      (https://cloud.google.com/compute/docs/private-google-access).
      """,
  )

  ip_address_parser.add_argument(
      '--public-ip-address',
      action='store_true',
      help="""\
      If provided, cluster instances are assigned external IP addresses.

      If omitted, the Dataproc service applies a default policy to determine
      whether or not each instance in the cluster gets an external IP address.

      Note: Dataproc VMs need access to the Dataproc API. This can be achieved
      without external IP addresses using Private Google Access
      (https://cloud.google.com/compute/docs/private-google-access).
      """,
  )

  parser.add_argument(
      '--private-ipv6-google-access-type',
      choices=['inherit-subnetwork', 'outbound', 'bidirectional'],
      help="""\
      The private IPv6 Google access type for the cluster.
      """,
  )

  boot_disk_type_detailed_help = """\
      The type of the boot disk. The value must be `pd-balanced`,
      `pd-ssd`, or `pd-standard`.
      """
  parser.add_argument(
      '--master-boot-disk-type', help=boot_disk_type_detailed_help
  )
  parser.add_argument(
      '--worker-boot-disk-type', help=boot_disk_type_detailed_help
  )
  secondary_worker_boot_disk_type = parser.add_argument_group(mutex=True)
  secondary_worker_boot_disk_type.add_argument(
      '--preemptible-worker-boot-disk-type',
      help=boot_disk_type_detailed_help,
      hidden=True,
      action=actions.DeprecationAction(
          '--preemptible-worker-boot-disk-type',
          warn=(
              'The `--preemptible-worker-boot-disk-type` flag is deprecated. '
              'Use the `--secondary-worker-boot-disk-type` flag instead.'
          ),
      ),
  )
  secondary_worker_boot_disk_type.add_argument(
      '--secondary-worker-boot-disk-type', help=boot_disk_type_detailed_help
  )

  if include_driver_pool_args:
    flags.AddDriverPoolId(parser)
    parser.add_argument(
        '--driver-pool-boot-disk-type', help=boot_disk_type_detailed_help
    )
    parser.add_argument(
        '--driver-pool-size',
        type=int,
        help='The size of the cluster driver pool.',
    )
    parser.add_argument(
        '--driver-pool-machine-type',
        help=(
            'The type of machine to use for the cluster driver pool nodes.'
            ' Defaults to server-specified.'
        ),
    )
    parser.add_argument(
        '--num-driver-pool-local-ssds',
        type=int,
        help="""\
        The number of local SSDs to attach to each cluster driver pool node.
        """,
    )
    parser.add_argument(
        '--driver-pool-local-ssd-interface',
        help="""\
        Interface to use to attach local SSDs to cluster driver pool node(s).
        """,
    )

  parser.add_argument(
      '--enable-component-gateway',
      action='store_true',
      help="""\
        Enable access to the web UIs of selected components on the cluster
        through the component gateway.
        """,
  )
  parser.add_argument(
      '--node-group',
      help="""\
        The name of the sole-tenant node group to create the cluster on. Can be
        a short name ("node-group-name") or in the format
        "projects/{project-id}/zones/{zone}/nodeGroups/{node-group-name}".
        """,
  )
  parser.add_argument(
      '--shielded-secure-boot',
      action='store_true',
      help="""\
        The cluster's VMs will boot with secure boot enabled.
        """,
  )
  parser.add_argument(
      '--shielded-vtpm',
      action='store_true',
      help="""\
        The cluster's VMs will boot with the TPM (Trusted Platform Module) enabled.
        A TPM is a hardware module that can be used for different security
        operations, such as remote attestation, encryption, and sealing of keys.
        """,
  )
  parser.add_argument(
      '--shielded-integrity-monitoring',
      action='store_true',
      help="""\
        Enables monitoring and attestation of the boot integrity of the
        cluster's VMs. vTPM (virtual Trusted Platform Module) must also be
        enabled. A TPM is a hardware module that can be used for different
        security operations, such as remote attestation, encryption, and sealing
        of keys.
        """,
  )
  if not beta:
    parser.add_argument(
        '--confidential-compute',
        action='store_true',
        help="""\
        Enables Confidential VM. See https://cloud.google.com/compute/confidential-vm/docs for more information.
        Note that Confidential VM can only be enabled when the machine types
        are N2D (https://cloud.google.com/compute/docs/machine-types#n2d_machine_types)
        and the image is SEV Compatible.
        """,
    )
  parser.add_argument(
      '--dataproc-metastore',
      help="""\
      Specify the name of a Dataproc Metastore service to be used as an
      external metastore in the format:
      "projects/{project-id}/locations/{region}/services/{service-name}".
      """,
  )

  parser.add_argument(
      '--enable-node-groups',
      hidden=True,
      help="""\
      Create cluster nodes using Dataproc NodeGroups. All the required VMs will be created using GCE MIG.
      """,
      type=bool,
  )

  autoscaling_group = parser.add_argument_group()
  flags.AddAutoscalingPolicyResourceArgForCluster(
      autoscaling_group, api_version='v1'
  )

  if include_ttl_config:
    parser.add_argument(
        '--max-idle',
        type=arg_parsers.Duration(),
        help="""\
          The duration before cluster is auto-deleted after last job completes,
          such as "2h" or "1d".
          See $ gcloud topic datetimes for information on duration formats.
          """,
    )

    auto_delete_group = parser.add_mutually_exclusive_group()
    auto_delete_group.add_argument(
        '--max-age',
        type=arg_parsers.Duration(),
        help="""\
          The lifespan of the cluster before it is auto-deleted, such as
          "2h" or "1d".
          See $ gcloud topic datetimes for information on duration formats.
          """,
    )

    auto_delete_group.add_argument(
        '--expiration-time',
        type=arg_parsers.Datetime.Parse,
        help="""\
          The time when cluster will be auto-deleted, such as
          "2017-08-29T18:52:51.142Z." See $ gcloud topic datetimes for
          information on time formats.
          """,
    )

  AddKerberosGroup(parser)

  if not beta:
    AddSecureMultiTenancyGroup(parser)

  flags.AddMinCpuPlatformArgs(parser, include_driver_pool_args)

  _AddAcceleratorArgs(parser, include_driver_pool_args)

  if not beta:
    _AddMetricConfigArgs(parser, dataproc)

  AddReservationAffinityGroup(
      gce_platform_group,
      group_text='Specifies the reservation for the instance.',
      affinity_text='The type of reservation for the instance.',
  )
  if include_gke_platform_args:
    gke_based_cluster_group = platform_group.add_argument_group(
        hidden=True,
        help="""\
          Options for creating a GKE-based Dataproc cluster. Specifying any of these
          will indicate that this cluster is intended to be a GKE-based cluster.
          These options are mutually exclusive with GCE-based options.
          """,
    )
    gke_based_cluster_group.add_argument(
        '--gke-cluster',
        hidden=True,
        help="""\
            Required for GKE-based clusters. Specify the name of the GKE cluster to
            deploy this GKE-based Dataproc cluster to. This should be the short name
            and not the full path name.
            """,
    )
    gke_based_cluster_group.add_argument(
        '--gke-cluster-namespace',
        hidden=True,
        help="""\
            Optional. Specify the name of the namespace to deploy Dataproc system
            components into. This namespace does not need to already exist.
            """,
    )


def _GetValidMetricSourceChoices(dataproc):
  metric_sources_enum = dataproc.messages.Metric.MetricSourceValueValuesEnum
  return [
      arg_utils.ChoiceToEnumName(n)
      for n in sorted(metric_sources_enum.names())
      if n != 'METRIC_SOURCE_UNSPECIFIED'
  ]


def _AddMetricConfigArgs(parser, dataproc):
  """Adds DataprocMetricConfig related args to the parser."""
  metric_overrides_detailed_help = """
  List of metrics that override the default metrics enabled for the metric
  sources. Any of the
  [available OSS metrics](https://cloud.google.com/dataproc/docs/guides/monitoring#available_oss_metrics)
  and all Spark metrics, can be listed for collection as a metric override.
  Override metric values are case sensitive, and must be provided, if
  appropriate, in CamelCase format, for example:

  *sparkHistoryServer:JVM:Memory:NonHeapMemoryUsage.committed*
  *hiveserver2:JVM:Memory:NonHeapMemoryUsage.used*

  Only the specified overridden metrics will be collected from a given metric
  source. For example, if one or more *spark:executive* metrics are listed as
  metric overrides, other *SPARK* metrics will not be collected. The collection
  of default OSS metrics from other metric sources is unaffected. For example,
  if both *SPARK* and *YARN* metric sources are enabled, and overrides are
  provided for Spark metrics only, all default YARN metrics will be collected.

  The source of the specified metric override must be enabled. For example,
  if one or more *spark:driver* metrics are provided as metric overrides,
  the spark metric source must be enabled (*--metric-sources=spark*).
  """

  metric_config_group = parser.add_group()
  metric_config_group.add_argument(
      '--metric-sources',
      metavar='METRIC_SOURCE',
      type=arg_parsers.ArgList(
          arg_utils.ChoiceToEnumName,
          choices=_GetValidMetricSourceChoices(dataproc),
      ),
      required=True,
      help=(
          'Specifies a list of cluster [Metric'
          ' Sources](https://cloud.google.com/dataproc/docs/guides/monitoring#available_oss_metrics)'
          ' to collect custom metrics.'
      ),
  )
  metric_overrides_group = metric_config_group.add_mutually_exclusive_group()
  metric_overrides_group.add_argument(
      '--metric-overrides',
      type=arg_parsers.ArgList(),
      action=arg_parsers.UpdateAction,
      metavar='METRIC_SOURCE:INSTANCE:GROUP:METRIC',
      help=metric_overrides_detailed_help,
  )
  metric_overrides_group.add_argument(
      '--metric-overrides-file',
      help="""\
      Path to a file containing list of Metrics that override the default metrics enabled for the metric sources.
      The path can be a Cloud Storage URL (example: `gs://path/to/file`) or a local file system path.
      """,
  )


def _AddAcceleratorArgs(parser, include_driver_pool_args=False):
  """Adds accelerator related args to the parser."""
  accelerator_help_fmt = """\
      Attaches accelerators, such as GPUs, to the {instance_type}
      instance(s).
      """
  accelerator_help_fmt += """
      *type*::: The specific type of accelerator to attach to the instances,
      such as `nvidia-tesla-k80` for NVIDIA Tesla K80. Use `gcloud compute
      accelerator-types list` to display available accelerator types.

      *count*::: The number of accelerators to attach to each instance. The default value is 1.
      """

  parser.add_argument(
      '--master-accelerator',
      type=arg_parsers.ArgDict(
          spec={
              'type': str,
              'count': int,
          }
      ),
      metavar='type=TYPE,[count=COUNT]',
      help=accelerator_help_fmt.format(instance_type='master'),
  )

  parser.add_argument(
      '--worker-accelerator',
      type=arg_parsers.ArgDict(
          spec={
              'type': str,
              'count': int,
          }
      ),
      metavar='type=TYPE,[count=COUNT]',
      help=accelerator_help_fmt.format(instance_type='worker'),
  )

  secondary_worker_accelerator = parser.add_argument_group(mutex=True)

  secondary_worker_accelerator.add_argument(
      '--secondary-worker-accelerator',
      type=arg_parsers.ArgDict(
          spec={
              'type': str,
              'count': int,
          }
      ),
      metavar='type=TYPE,[count=COUNT]',
      help=accelerator_help_fmt.format(instance_type='secondary-worker'),
  )

  secondary_worker_accelerator.add_argument(
      '--preemptible-worker-accelerator',
      type=arg_parsers.ArgDict(
          spec={
              'type': str,
              'count': int,
          }
      ),
      metavar='type=TYPE,[count=COUNT]',
      help=accelerator_help_fmt.format(instance_type='preemptible-worker'),
      hidden=True,
      action=actions.DeprecationAction(
          '--preemptible-worker-accelerator',
          warn=(
              'The `--preemptible-worker-accelerator` flag is deprecated. '
              'Use the `--secondary-worker-accelerator` flag instead.'
          ),
      ),
  )
  if include_driver_pool_args:
    parser.add_argument(
        '--driver-pool-accelerator',
        type=arg_parsers.ArgDict(
            spec={
                'type': str,
                'count': int,
            }
        ),
        metavar='type=TYPE,[count=COUNT]',
        help=accelerator_help_fmt.format(instance_type='driver-pool'),
    )


def _AddDiskArgs(parser, include_driver_pool_args=False):
  """Adds disk related args to the parser."""
  boot_disk_size_detailed_help = """\
      The size of the boot disk. The value must be a
      whole number followed by a size unit of ``KB'' for kilobyte, ``MB''
      for megabyte, ``GB'' for gigabyte, or ``TB'' for terabyte. For example,
      `10GB` will produce a 10 gigabyte disk. The minimum boot disk size is 10 GB. Boot disk size must be a multiple of 1 GB.
      """
  parser.add_argument(
      '--master-boot-disk-size',
      type=arg_parsers.BinarySize(lower_bound='10GB'),
      help=boot_disk_size_detailed_help,
  )
  parser.add_argument(
      '--worker-boot-disk-size',
      type=arg_parsers.BinarySize(lower_bound='10GB'),
      help=boot_disk_size_detailed_help,
  )
  secondary_worker_boot_disk_size = parser.add_argument_group(mutex=True)
  secondary_worker_boot_disk_size.add_argument(
      '--preemptible-worker-boot-disk-size',
      type=arg_parsers.BinarySize(lower_bound='10GB'),
      help=boot_disk_size_detailed_help,
      hidden=True,
      action=actions.DeprecationAction(
          '--preemptible-worker-boot-disk-size',
          warn=(
              'The `--preemptible-worker-boot-disk-size` flag is deprecated. '
              'Use the `--secondary-worker-boot-disk-size` flag instead.'
          ),
      ),
  )
  secondary_worker_boot_disk_size.add_argument(
      '--secondary-worker-boot-disk-size',
      type=arg_parsers.BinarySize(lower_bound='10GB'),
      help=boot_disk_size_detailed_help,
  )
  if include_driver_pool_args:
    parser.add_argument(
        '--driver-pool-boot-disk-size',
        type=arg_parsers.BinarySize(lower_bound='10GB'),
        help=boot_disk_size_detailed_help,
    )


def _AddDiskArgsDeprecated(parser, include_driver_pool_args=False):
  """Adds deprecated disk related args to the parser."""
  master_boot_disk_size = parser.add_mutually_exclusive_group()
  worker_boot_disk_size = parser.add_mutually_exclusive_group()

  # Deprecated, to be removed at a future date.
  master_boot_disk_size.add_argument(
      '--master-boot-disk-size-gb',
      action=actions.DeprecationAction(
          '--master-boot-disk-size-gb',
          warn=(
              'The `--master-boot-disk-size-gb` flag is deprecated. '
              'Use `--master-boot-disk-size` flag with "GB" after value.'
          ),
      ),
      type=int,
      hidden=True,
      help='Use `--master-boot-disk-size` flag with "GB" after value.',
  )
  worker_boot_disk_size.add_argument(
      '--worker-boot-disk-size-gb',
      action=actions.DeprecationAction(
          '--worker-boot-disk-size-gb',
          warn=(
              'The `--worker-boot-disk-size-gb` flag is deprecated. '
              'Use `--worker-boot-disk-size` flag with "GB" after value.'
          ),
      ),
      type=int,
      hidden=True,
      help='Use `--worker-boot-disk-size` flag with "GB" after value.',
  )

  boot_disk_size_detailed_help = """\
      The size of the boot disk. The value must be a
      whole number followed by a size unit of ``KB'' for kilobyte, ``MB''
      for megabyte, ``GB'' for gigabyte, or ``TB'' for terabyte. For example,
      ``10GB'' will produce a 10 gigabyte disk. The minimum size a boot disk
      can have is 10 GB. Disk size must be a multiple of 1 GB.
      """
  master_boot_disk_size.add_argument(
      '--master-boot-disk-size',
      type=arg_parsers.BinarySize(lower_bound='10GB'),
      help=boot_disk_size_detailed_help,
  )
  worker_boot_disk_size.add_argument(
      '--worker-boot-disk-size',
      type=arg_parsers.BinarySize(lower_bound='10GB'),
      help=boot_disk_size_detailed_help,
  )
  secondary_worker_boot_disk_size = parser.add_argument_group(mutex=True)
  secondary_worker_boot_disk_size.add_argument(
      '--preemptible-worker-boot-disk-size',
      type=arg_parsers.BinarySize(lower_bound='10GB'),
      help=boot_disk_size_detailed_help,
      hidden=True,
      action=actions.DeprecationAction(
          '--preemptible-worker-boot-disk-size',
          warn=(
              'The `--preemptible-worker-boot-disk-size` flag is deprecated. '
              'Use the `--secondary-worker-boot-disk-size` flag instead.'
          ),
      ),
  )
  secondary_worker_boot_disk_size.add_argument(
      '--secondary-worker-boot-disk-size',
      type=arg_parsers.BinarySize(lower_bound='10GB'),
      help=boot_disk_size_detailed_help,
  )
  if include_driver_pool_args:
    parser.add_argument(
        '--driver-pool-boot-disk-size',
        type=arg_parsers.BinarySize(lower_bound='10GB'),
        help=boot_disk_size_detailed_help,
    )


# DEPRECATED Beta release track should no longer be used, Google Cloud
# no longer supports it.
def BetaArgsForClusterRef(parser):
  """Register beta-only flags for creating a Dataproc cluster."""
  pass


def GetClusterConfig(
    args,
    dataproc,
    project_id,
    compute_resources,
    beta=False,
    alpha=False,
    include_deprecated=True,
    include_ttl_config=False,
    include_gke_platform_args=False,
):
  """Get dataproc cluster configuration.

  Args:
    args: Arguments parsed from argparse.ArgParser.
    dataproc: Dataproc object that contains client, messages, and resources
    project_id: Dataproc project ID
    compute_resources: compute resource for cluster
    beta: use BETA only features
    alpha: use ALPHA only features
    include_deprecated: whether to include deprecated args
    include_ttl_config: whether to include Scheduled Delete(TTL) args
    include_gke_platform_args: whether to include GKE-based cluster args

  Returns:
    cluster_config: Dataproc cluster configuration
  """
  master_accelerator_type = None
  worker_accelerator_type = None
  secondary_worker_accelerator_type = None
  driver_pool_accelerator_type = None

  if args.master_accelerator:
    if 'type' in args.master_accelerator.keys():
      master_accelerator_type = args.master_accelerator['type']
    else:
      raise exceptions.ArgumentError('master-accelerator missing type!')
    master_accelerator_count = args.master_accelerator.get('count', 1)

  if args.worker_accelerator:
    if 'type' in args.worker_accelerator.keys():
      worker_accelerator_type = args.worker_accelerator['type']
    else:
      raise exceptions.ArgumentError('worker-accelerator missing type!')
    worker_accelerator_count = args.worker_accelerator.get('count', 1)

  secondary_worker_accelerator = _FirstNonNone(
      args.secondary_worker_accelerator, args.preemptible_worker_accelerator
  )
  if secondary_worker_accelerator:
    if 'type' in secondary_worker_accelerator.keys():
      secondary_worker_accelerator_type = secondary_worker_accelerator['type']
    else:
      raise exceptions.ArgumentError(
          'secondary-worker-accelerator missing type!'
      )
    secondary_worker_accelerator_count = secondary_worker_accelerator.get(
        'count', 1
    )

  if args.min_worker_fraction and (
      args.min_worker_fraction < 0 or args.min_worker_fraction > 1
  ):
    raise exceptions.ArgumentError(
        '--min-worker-fraction must be between 0 and 1'
    )

  if hasattr(args, 'driver_pool_accelerator') and args.driver_pool_accelerator:
    if 'type' in args.driver_pool_accelerator.keys():
      driver_pool_accelerator_type = args.driver_pool_accelerator['type']
    else:
      raise exceptions.ArgumentError('driver-pool-accelerator missing type!')
    driver_pool_accelerator_count = args.driver_pool_accelerator.get('count', 1)

  # Resolve non-zonal GCE resources
  # We will let the server resolve short names of zonal resources because
  # if auto zone is requested, we will not know the zone before sending the
  # request
  image_ref = args.image and compute_resources.Parse(
      args.image, params={'project': project_id}, collection='compute.images'
  )
  network_ref = args.network and compute_resources.Parse(
      args.network,
      params={'project': project_id},
      collection='compute.networks',
  )
  subnetwork_ref = args.subnet and compute_resources.Parse(
      args.subnet,
      params={
          'project': project_id,
          'region': properties.VALUES.compute.region.GetOrFail,
      },
      collection='compute.subnetworks',
  )
  timeout_str = six.text_type(args.initialization_action_timeout) + 's'
  init_actions = [
      dataproc.messages.NodeInitializationAction(
          executableFile=exe, executionTimeout=timeout_str
      )
      for exe in (args.initialization_actions or [])
  ]
  # Increase the client timeout for each initialization action.
  args.timeout += args.initialization_action_timeout * len(init_actions)

  expanded_scopes = compute_helpers.ExpandScopeAliases(args.scopes)

  software_config = dataproc.messages.SoftwareConfig(
      imageVersion=args.image_version
  )

  if include_deprecated:
    master_boot_disk_size_gb = args.master_boot_disk_size_gb
  else:
    master_boot_disk_size_gb = None
  if args.master_boot_disk_size:
    master_boot_disk_size_gb = api_utils.BytesToGb(args.master_boot_disk_size)

  if include_deprecated:
    worker_boot_disk_size_gb = args.worker_boot_disk_size_gb
  else:
    worker_boot_disk_size_gb = None
  if args.worker_boot_disk_size:
    worker_boot_disk_size_gb = api_utils.BytesToGb(args.worker_boot_disk_size)

  secondary_worker_boot_disk_size_gb = api_utils.BytesToGb(
      _FirstNonNone(
          args.secondary_worker_boot_disk_size,
          args.preemptible_worker_boot_disk_size,
      )
  )

  driver_pool_boot_disk_size_gb = None
  if (
      hasattr(args, 'driver_pool_boot_disk_size')
      and args.driver_pool_boot_disk_size
  ):
    driver_pool_boot_disk_size_gb = api_utils.BytesToGb(
        args.driver_pool_boot_disk_size
    )

  if args.single_node or args.num_workers == 0:
    # Explicitly specifying --num-workers=0 gives you a single node cluster,
    # but if --num-workers is omitted, args.num_workers is None (not 0), and
    # this property will not be set
    args.properties[constants.ALLOW_ZERO_WORKERS_PROPERTY] = 'true'

  if args.enable_node_groups is not None:
    args.properties[constants.ENABLE_NODE_GROUPS_PROPERTY] = str(
        args.enable_node_groups
    ).lower()

  if args.properties:
    software_config.properties = encoding.DictToAdditionalPropertyMessage(
        args.properties,
        dataproc.messages.SoftwareConfig.PropertiesValue,
        sort_items=True,
    )

  if args.components:
    software_config_cls = dataproc.messages.SoftwareConfig
    software_config.optionalComponents.extend(
        list(
            map(
                software_config_cls.OptionalComponentsValueListEntryValuesEnum,
                args.components,
            )
        )
    )

  gce_cluster_config = dataproc.messages.GceClusterConfig(
      networkUri=network_ref and network_ref.SelfLink(),
      subnetworkUri=subnetwork_ref and subnetwork_ref.SelfLink(),
      privateIpv6GoogleAccess=_GetPrivateIpv6GoogleAccess(
          dataproc, args.private_ipv6_google_access_type
      ),
      serviceAccount=args.service_account,
      serviceAccountScopes=expanded_scopes,
      zoneUri=properties.VALUES.compute.zone.GetOrFail(),
  )

  if args.public_ip_address:
    gce_cluster_config.internalIpOnly = not args.public_ip_address
  if args.no_address:
    gce_cluster_config.internalIpOnly = args.no_address

  reservation_affinity = GetReservationAffinity(args, dataproc)
  gce_cluster_config.reservationAffinity = reservation_affinity

  if args.tags:
    gce_cluster_config.tags = args.tags

  if args.metadata:
    flat_metadata = collections.OrderedDict()
    for entry in args.metadata:
      for k, v in entry.items():
        flat_metadata[k] = v
    gce_cluster_config.metadata = encoding.DictToAdditionalPropertyMessage(
        flat_metadata, dataproc.messages.GceClusterConfig.MetadataValue
    )

  master_accelerators = []
  if master_accelerator_type:
    master_accelerators.append(
        dataproc.messages.AcceleratorConfig(
            acceleratorTypeUri=master_accelerator_type,
            acceleratorCount=master_accelerator_count,
        )
    )
  worker_accelerators = []
  if worker_accelerator_type:
    worker_accelerators.append(
        dataproc.messages.AcceleratorConfig(
            acceleratorTypeUri=worker_accelerator_type,
            acceleratorCount=worker_accelerator_count,
        )
    )
  secondary_worker_accelerators = []
  if secondary_worker_accelerator_type:
    secondary_worker_accelerators.append(
        dataproc.messages.AcceleratorConfig(
            acceleratorTypeUri=secondary_worker_accelerator_type,
            acceleratorCount=secondary_worker_accelerator_count,
        )
    )
  driver_pool_accelerators = []
  if driver_pool_accelerator_type:
    driver_pool_accelerators.append(
        dataproc.messages.AcceleratorConfig(
            acceleratorTypeUri=driver_pool_accelerator_type,
            acceleratorCount=driver_pool_accelerator_count,
        )
    )

  cluster_config = dataproc.messages.ClusterConfig(
      configBucket=args.bucket,
      tempBucket=args.temp_bucket,
      gceClusterConfig=gce_cluster_config,
      masterConfig=dataproc.messages.InstanceGroupConfig(
          numInstances=args.num_masters,
          imageUri=image_ref and image_ref.SelfLink(),
          machineTypeUri=args.master_machine_type,
          accelerators=master_accelerators,
          diskConfig=GetDiskConfig(
              dataproc,
              args.master_boot_disk_type,
              master_boot_disk_size_gb,
              args.num_master_local_ssds,
              args.master_local_ssd_interface,
          ),
          minCpuPlatform=args.master_min_cpu_platform,
      ),
      workerConfig=dataproc.messages.InstanceGroupConfig(
          numInstances=args.num_workers,
          minNumInstances=args.min_num_workers,
          imageUri=image_ref and image_ref.SelfLink(),
          machineTypeUri=args.worker_machine_type,
          accelerators=worker_accelerators,
          diskConfig=GetDiskConfig(
              dataproc,
              args.worker_boot_disk_type,
              worker_boot_disk_size_gb,
              args.num_worker_local_ssds,
              args.worker_local_ssd_interface,
          ),
          minCpuPlatform=args.worker_min_cpu_platform,
      ),
      initializationActions=init_actions,
      softwareConfig=software_config,
  )

  if args.min_worker_fraction:
    cluster_config.workerConfig.startupConfig = dataproc.messages.StartupConfig(
        requiredRegistrationFraction=args.min_worker_fraction,
    )

  if (
      args.kerberos_config_file
      or args.enable_kerberos
      or args.kerberos_root_principal_password_uri
  ):
    cluster_config.securityConfig = dataproc.messages.SecurityConfig()
    if args.kerberos_config_file:
      cluster_config.securityConfig.kerberosConfig = ParseKerberosConfigFile(
          dataproc, args.kerberos_config_file
      )
    else:
      kerberos_config = dataproc.messages.KerberosConfig()
      if args.enable_kerberos:
        kerberos_config.enableKerberos = args.enable_kerberos
      else:
        kerberos_config.enableKerberos = True
      if args.kerberos_root_principal_password_uri:
        kerberos_config.rootPrincipalPasswordUri = (
            args.kerberos_root_principal_password_uri
        )
        kerberos_kms_ref = args.CONCEPTS.kerberos_kms_key.Parse()
        if kerberos_kms_ref:
          kerberos_config.kmsKeyUri = kerberos_kms_ref.RelativeName()
      cluster_config.securityConfig.kerberosConfig = kerberos_config

  if not beta:
    if args.identity_config_file or args.secure_multi_tenancy_user_mapping:
      if cluster_config.securityConfig is None:
        cluster_config.securityConfig = dataproc.messages.SecurityConfig()

      if args.identity_config_file:
        cluster_config.securityConfig.identityConfig = ParseIdentityConfigFile(
            dataproc, args.identity_config_file
        )
      else:
        user_service_account_mapping = (
            ParseSecureMultiTenancyUserServiceAccountMappingString(
                args.secure_multi_tenancy_user_mapping
            )
        )
        identity_config = dataproc.messages.IdentityConfig()
        identity_config.userServiceAccountMapping = (
            encoding.DictToAdditionalPropertyMessage(
                user_service_account_mapping,
                dataproc.messages.IdentityConfig.UserServiceAccountMappingValue,
            )
        )
        cluster_config.securityConfig.identityConfig = identity_config

  if args.autoscaling_policy:
    cluster_config.autoscalingConfig = dataproc.messages.AutoscalingConfig(
        policyUri=args.CONCEPTS.autoscaling_policy.Parse().RelativeName()
    )

  if args.node_group:
    gce_cluster_config.nodeGroupAffinity = dataproc.messages.NodeGroupAffinity(
        nodeGroupUri=args.node_group
    )

  if (
      args.IsSpecified('shielded_secure_boot')
      or args.IsSpecified('shielded_vtpm')
      or args.IsSpecified('shielded_integrity_monitoring')
  ):
    gce_cluster_config.shieldedInstanceConfig = (
        dataproc.messages.ShieldedInstanceConfig(
            enableSecureBoot=args.shielded_secure_boot,
            enableVtpm=args.shielded_vtpm,
            enableIntegrityMonitoring=args.shielded_integrity_monitoring,
        )
    )

  if not beta and args.IsSpecified('confidential_compute'):
    gce_cluster_config.confidentialInstanceConfig = (
        dataproc.messages.ConfidentialInstanceConfig(
            enableConfidentialCompute=args.confidential_compute
        )
    )

  if args.dataproc_metastore:
    cluster_config.metastoreConfig = dataproc.messages.MetastoreConfig(
        dataprocMetastoreService=args.dataproc_metastore
    )

  if include_ttl_config:
    lifecycle_config = dataproc.messages.LifecycleConfig()
    changed_config = False
    if args.max_age is not None:
      lifecycle_config.autoDeleteTtl = six.text_type(args.max_age) + 's'
      changed_config = True
    if args.expiration_time is not None:
      lifecycle_config.autoDeleteTime = times.FormatDateTime(
          args.expiration_time
      )
      changed_config = True
    if args.max_idle is not None:
      lifecycle_config.idleDeleteTtl = six.text_type(args.max_idle) + 's'
      changed_config = True
    if changed_config:
      cluster_config.lifecycleConfig = lifecycle_config

  encryption_config = dataproc.messages.EncryptionConfig()
  if hasattr(args.CONCEPTS, 'gce_pd_kms_key'):
    gce_pd_kms_ref = args.CONCEPTS.gce_pd_kms_key.Parse()
    if gce_pd_kms_ref:
      encryption_config.gcePdKmsKeyName = gce_pd_kms_ref.RelativeName()
    else:
      # Did user use any gce-pd-kms-key flags?
      for keyword in [
          'gce-pd-kms-key',
          'gce-pd-kms-key-project',
          'gce-pd-kms-key-location',
          'gce-pd-kms-key-keyring',
      ]:
        if getattr(args, keyword.replace('-', '_'), None):
          raise exceptions.ArgumentError(
              '--gce-pd-kms-key was not fully specified.'
          )
  if hasattr(args.CONCEPTS, 'kms_key'):
    kms_ref = args.CONCEPTS.kms_key.Parse()
    if kms_ref:
      encryption_config.kmsKey = kms_ref.RelativeName()
    else:
      for keyword in [
          'kms-key',
          'kms-project',
          'kms-location',
          'kms-keyring',
      ]:
        if getattr(args, keyword.replace('-', '_'), None):
          raise exceptions.ArgumentError(
              '--kms-key was not fully specified.'
          )
  if encryption_config.gcePdKmsKeyName or encryption_config.kmsKey:
    cluster_config.encryptionConfig = encryption_config

  # Secondary worker group is optional. However, users may specify
  # future pVMs configuration at creation time.
  num_secondary_workers = _FirstNonNone(
      args.num_secondary_workers, args.num_preemptible_workers
  )
  secondary_worker_boot_disk_type = _FirstNonNone(
      args.secondary_worker_boot_disk_type,
      args.preemptible_worker_boot_disk_type,
  )
  num_secondary_worker_local_ssds = _FirstNonNone(
      args.num_secondary_worker_local_ssds,
      args.num_preemptible_worker_local_ssds,
  )
  if (
      num_secondary_workers is not None
      or secondary_worker_boot_disk_size_gb is not None
      or secondary_worker_boot_disk_type is not None
      or num_secondary_worker_local_ssds is not None
      or args.worker_min_cpu_platform is not None
      or args.secondary_worker_type == 'non-preemptible'
      or args.secondary_worker_type == 'spot'
      or args.secondary_worker_machine_types is not None
      or args.min_secondary_worker_fraction is not None
  ):
    instance_flexibility_policy = GetInstanceFlexibilityPolicy(
        dataproc, args, alpha
    )
    startup_config = GetStartupConfig(dataproc, args)
    cluster_config.secondaryWorkerConfig = (
        dataproc.messages.InstanceGroupConfig(
            numInstances=num_secondary_workers,
            accelerators=secondary_worker_accelerators,
            diskConfig=GetDiskConfig(
                dataproc,
                secondary_worker_boot_disk_type,
                secondary_worker_boot_disk_size_gb,
                num_secondary_worker_local_ssds,
                args.secondary_worker_local_ssd_interface,
            ),
            minCpuPlatform=args.worker_min_cpu_platform,
            preemptibility=_GetInstanceGroupPreemptibility(
                dataproc, args.secondary_worker_type
            ),
            instanceFlexibilityPolicy=instance_flexibility_policy,
            startupConfig=startup_config,
        )
    )

  # Add input-only auxiliaryNodeGroups
  if _AtLeastOneGceNodePoolSpecified(args, driver_pool_boot_disk_size_gb):
    cluster_config.auxiliaryNodeGroups = [
        dataproc.messages.AuxiliaryNodeGroup(
            nodeGroup=(
                dataproc.messages.NodeGroup(
                    labels=labels_util.ParseCreateArgs(
                        args, dataproc.messages.NodeGroup.LabelsValue
                    ),
                    roles=[
                        dataproc.messages.NodeGroup.RolesValueListEntryValuesEnum.DRIVER
                    ],
                    nodeGroupConfig=dataproc.messages.InstanceGroupConfig(
                        numInstances=args.driver_pool_size,
                        imageUri=image_ref and image_ref.SelfLink(),
                        machineTypeUri=args.driver_pool_machine_type,
                        accelerators=driver_pool_accelerators,
                        diskConfig=GetDiskConfig(
                            dataproc,
                            args.driver_pool_boot_disk_type,
                            driver_pool_boot_disk_size_gb,
                            args.num_driver_pool_local_ssds,
                            args.driver_pool_local_ssd_interface,
                        ),
                        minCpuPlatform=args.driver_pool_min_cpu_platform,
                    ),
                )
            ),
            # FE should generate the driver pool id if none is provided
            nodeGroupId=args.driver_pool_id,
        )
    ]

  if args.enable_component_gateway:
    cluster_config.endpointConfig = dataproc.messages.EndpointConfig(
        enableHttpPortAccess=args.enable_component_gateway
    )

  if include_gke_platform_args:
    if args.gke_cluster is not None:
      location = args.zone or args.region
      target_gke_cluster = 'projects/{0}/locations/{1}/clusters/{2}'.format(
          project_id, location, args.gke_cluster
      )
      cluster_config.gkeClusterConfig = dataproc.messages.GkeClusterConfig(
          namespacedGkeDeploymentTarget=dataproc.messages.NamespacedGkeDeploymentTarget(
              targetGkeCluster=target_gke_cluster,
              clusterNamespace=args.gke_cluster_namespace,
          )
      )
      cluster_config.gceClusterConfig = None
      cluster_config.masterConfig = None
      cluster_config.workerConfig = None
      cluster_config.secondaryWorkerConfig = None

  if not beta and args.metric_sources:
    _SetDataprocMetricConfig(args, cluster_config, dataproc)
  return cluster_config


def _GetMetricOverrides(args):
  """Gets metric overrides from from input file or metric_overrides list."""
  if args.metric_overrides:
    return args.metric_overrides
  if args.metric_overrides_file:
    if args.metric_overrides_file.startswith('gs://'):
      data = storage_helpers.ReadObject(args.metric_overrides_file)
    else:
      data = console_io.ReadFromFileOrStdin(
          args.metric_overrides_file, binary=False
      )
    return data.split('\n')
  return []


def _SetDataprocMetricConfig(args, cluster_config, dataproc):
  """Method to set Metric source and the corresponding optional overrides to DataprocMetricConfig.

  Metric overrides can be read from either metric-overrides or
  metric-overrides-file argument.
  We do basic validation on metric-overrides :
  * Ensure that all entries of metric-overrides are prefixed with camel case of
  the metric source.
    Example :
    "sparkHistoryServer:JVM:Memory:NonHeapMemoryUsage.used" is valid metric
    override for the metric-source spark-history-server
    but "spark-history-server:JVM:Memory:NonHeapMemoryUsage.used" is not.
  * Metric overrides are passed only for the metric sources enabled via
  args.metric_sources.

  Args:
    args: arguments passed to create cluster command.
    cluster_config: cluster configuration to be updated with
      DataprocMetricConfig.
    dataproc: Dataproc API definition.
  """

  def _GetCamelCaseMetricSource(ms):
    title_case = ms.lower().title().replace('_', '').replace('-', '')
    return title_case[0].lower() + title_case[1:]

  metric_source_to_overrides_dict = dict()
  metric_overrides = [m.strip() for m in _GetMetricOverrides(args) if m.strip()]
  if metric_overrides:
    invalid_metric_overrides = []
    valid_metric_prefixes = [
        _GetCamelCaseMetricSource(ms) for ms in args.metric_sources
    ]
    for metric in metric_overrides:
      prefix = metric.split(':')[0]
      if prefix not in valid_metric_prefixes:
        invalid_metric_overrides.append(metric)
      metric_source_to_overrides_dict.setdefault(prefix, []).append(metric)
    if invalid_metric_overrides:
      raise exceptions.ArgumentError(
          'Found invalid metric overrides: '
          + ','.join(invalid_metric_overrides)
          + '. Please ensure the metric overrides only have the following'
          ' prefixes that correspond to the metric-sources that are enabled: '
          + ','.join(valid_metric_prefixes)
      )

  cluster_config.dataprocMetricConfig = dataproc.messages.DataprocMetricConfig(
      metrics=[]
  )
  for metric_source in args.metric_sources:
    metric_source_in_camel_case = _GetCamelCaseMetricSource(metric_source)
    metric_overrides = metric_source_to_overrides_dict.get(
        metric_source_in_camel_case, []
    )
    cluster_config.dataprocMetricConfig.metrics.append(
        dataproc.messages.Metric(
            metricSource=arg_utils.ChoiceToEnum(
                metric_source,
                dataproc.messages.Metric.MetricSourceValueValuesEnum,
            ),
            metricOverrides=metric_overrides,
        )
    )


def _AtLeastOneGceNodePoolSpecified(args, driver_pool_boot_disk_size_gb):
  return hasattr(args, 'driver_pool_size') and (
      args.IsSpecified('driver_pool_size')
      or args.IsSpecified('driver_pool_machine_type')
      or args.IsSpecified('driver_pool_boot_disk_type')
      or driver_pool_boot_disk_size_gb is not None
      or args.IsSpecified('num_driver_pool_local_ssds')
      or args.IsSpecified('driver_pool_local_ssd_interface')
      or args.IsSpecified('driver_pool_min_cpu_platform')
      or args.IsSpecified('driver_pool_id')
  )


def _FirstNonNone(first, second):
  return first if first is not None else second


def _GetInstanceGroupPreemptibility(dataproc, secondary_worker_type):
  if secondary_worker_type == 'non-preemptible':
    return dataproc.messages.InstanceGroupConfig.PreemptibilityValueValuesEnum(
        'NON_PREEMPTIBLE'
    )
  elif secondary_worker_type == 'spot':
    return dataproc.messages.InstanceGroupConfig.PreemptibilityValueValuesEnum(
        'SPOT'
    )
  return None


def _GetPrivateIpv6GoogleAccess(dataproc, private_ipv6_google_access_type):
  """Get PrivateIpv6GoogleAccess enum value.

  Converts private_ipv6_google_access_type argument value to
  PrivateIpv6GoogleAccess API enum value.

  Args:
    dataproc: Dataproc API definition
    private_ipv6_google_access_type: argument value

  Returns:
    PrivateIpv6GoogleAccess API enum value
  """
  if private_ipv6_google_access_type == 'inherit-subnetwork':
    return dataproc.messages.GceClusterConfig.PrivateIpv6GoogleAccessValueValuesEnum(
        'INHERIT_FROM_SUBNETWORK'
    )
  if private_ipv6_google_access_type == 'outbound':
    return dataproc.messages.GceClusterConfig.PrivateIpv6GoogleAccessValueValuesEnum(
        'OUTBOUND'
    )
  if private_ipv6_google_access_type == 'bidirectional':
    return dataproc.messages.GceClusterConfig.PrivateIpv6GoogleAccessValueValuesEnum(
        'BIDIRECTIONAL'
    )
  if private_ipv6_google_access_type is None:
    return None
  raise exceptions.ArgumentError(
      'Unsupported --private-ipv6-google-access-type flag value: '
      + private_ipv6_google_access_type
  )


def GetDiskConfig(
    dataproc,
    boot_disk_type,
    boot_disk_size,
    num_local_ssds,
    local_ssd_interface,
):
  """Get dataproc cluster disk configuration.

  Args:
    dataproc: Dataproc object that contains client, messages, and resources
    boot_disk_type: Type of the boot disk
    boot_disk_size: Size of the boot disk
    num_local_ssds: Number of the Local SSDs
    local_ssd_interface: Interface used to attach local SSDs

  Returns:
    disk_config: Dataproc cluster disk configuration
  """

  return dataproc.messages.DiskConfig(
      bootDiskType=boot_disk_type,
      bootDiskSizeGb=boot_disk_size,
      numLocalSsds=num_local_ssds,
      localSsdInterface=local_ssd_interface,
  )


def GetInstanceFlexibilityPolicy(dataproc, args, alpha):
  """Get instance flexibility policy.

  Args:
    dataproc: Dataproc object that contains client, messages, and resources
    args: arguments of the request
    alpha: checks if the release track is alpha

  Returns:
    InstanceFlexibilityPolicy of the secondary worker group.
  """

  if alpha and args.secondary_worker_standard_capacity_base is None:
    return None
  provisioning_model_mix = None
  instance_selection_list = []
  if alpha:
    provisioning_model_mix = dataproc.messages.ProvisioningModelMix(
        standardCapacityBase=args.secondary_worker_standard_capacity_base
    )
  else:
    instance_selection_list = GetInstanceSelectionList(dataproc, args)
  if provisioning_model_mix is None and not instance_selection_list:
    return None
  instance_flexibility_policy = dataproc.messages.InstanceFlexibilityPolicy(
      instanceSelectionList=instance_selection_list,
      provisioningModelMix=provisioning_model_mix,
  )
  return instance_flexibility_policy


def GetStartupConfig(dataproc, args):
  """Get startup config.

  Args:
    dataproc: Dataproc object that contains client, messages, and resources
    args: arguments of the request

  Returns:
    startup_config: Startup config of the secondary worker group.
  """
  if args.min_secondary_worker_fraction is None:
    return None
  return dataproc.messages.StartupConfig(
      requiredRegistrationFraction=args.min_secondary_worker_fraction
  )


def CreateCluster(
    dataproc,
    cluster_ref,
    cluster,
    is_async,
    timeout,
    enable_create_on_gke=False,
    action_on_failed_primary_workers=None,
):
  """Create a cluster.

  Args:
    dataproc: Dataproc object that contains client, messages, and resources
    cluster_ref: Full resource ref of cluster with name, region, and project id
    cluster: Cluster to create
    is_async: Whether to wait for the operation to complete
    timeout: Timeout used when waiting for the operation to complete
    enable_create_on_gke: Whether to enable creation of GKE-based clusters
    action_on_failed_primary_workers: Action to be performed when primary
      workers fail during cluster creation. Should be None for dataproc of
      v1beta2 version

  Returns:
    Created cluster, or None if async
  """
  # Get project id and region.
  request_id = util.GetUniqueId()
  request = dataproc.GetCreateClusterRequest(
      cluster=cluster,
      project_id=cluster_ref.projectId,
      region=cluster_ref.region,
      request_id=request_id,
      action_on_failed_primary_workers=action_on_failed_primary_workers,
  )
  operation = dataproc.client.projects_regions_clusters.Create(request)

  if is_async:
    log.status.write(
        'Creating [{0}] with operation [{1}].'.format(
            cluster_ref, operation.name
        )
    )
    return

  operation = util.WaitForOperation(
      dataproc,
      operation,
      message='Waiting for cluster creation operation',
      timeout_s=timeout,
  )

  get_request = dataproc.messages.DataprocProjectsRegionsClustersGetRequest(
      projectId=cluster_ref.projectId,
      region=cluster_ref.region,
      clusterName=cluster_ref.clusterName,
  )
  cluster = dataproc.client.projects_regions_clusters.Get(get_request)
  if cluster.status.state == (
      dataproc.messages.ClusterStatus.StateValueValuesEnum.RUNNING
  ):
    if enable_create_on_gke and cluster.config.gkeClusterConfig is not None:
      log.CreatedResource(
          cluster_ref,
          details='Cluster created on GKE cluster {0}'.format(
              cluster.config.gkeClusterConfig.namespacedGkeDeploymentTarget.targetGkeCluster
          ),
      )
    elif cluster.virtualClusterConfig is not None:
      if (
          cluster.virtualClusterConfig.kubernetesClusterConfig.gkeClusterConfig
          is not None
      ):
        log.CreatedResource(
            cluster_ref,
            details='Virtual Cluster created on GKE cluster: {0}'.format(
                cluster.virtualClusterConfig.kubernetesClusterConfig.gkeClusterConfig.gkeClusterTarget
            ),
        )
    else:
      zone_uri = cluster.config.gceClusterConfig.zoneUri
      zone_short_name = zone_uri.split('/')[-1]

      # Log the URL of the cluster
      log.CreatedResource(
          cluster_ref,
          # Also indicate which zone the cluster was placed in. This is helpful
          # if the server picked a zone (auto zone)
          details='Cluster placed in zone [{0}]'.format(zone_short_name),
      )
  else:
    # The operation didn't have an error, but the cluster is not RUNNING.
    log.error('Create cluster failed!')
    if cluster.status.detail:
      log.error('Details:\n' + cluster.status.detail)
  return cluster


def DeleteGeneratedLabels(cluster, dataproc):
  """Filter out Dataproc-generated cluster labels.

  Args:
    cluster: Cluster to filter
    dataproc: Dataproc object that contains client, messages, and resources
  """
  # Filter out Dataproc-generated labels.
  if cluster.labels:
    labels = encoding.MessageToPyValue(cluster.labels)
    labels_to_delete = []
    for label in labels:
      if label.startswith(GENERATED_LABEL_PREFIX):
        labels_to_delete.append(label)
    for label in labels_to_delete:
      del labels[label]
    if not labels:
      cluster.labels = None
    else:
      cluster.labels = encoding.DictToAdditionalPropertyMessage(
          labels, dataproc.messages.Cluster.LabelsValue
      )


def DeleteGeneratedProperties(cluster, dataproc):
  """Filter out Dataproc-generated cluster properties.

  Args:
    cluster: Cluster to filter
    dataproc: Dataproc object that contains client, messages, and resources
  """
  try:
    if cluster.config.softwareConfig.properties:
      _DeleteClusterGeneratedProperties(cluster, dataproc)
  except AttributeError:
    # The field is not set.
    pass
  try:
    if (
        cluster.virtualClusterConfig.kubernetesClusterConfig.kubernetesSoftwareConfig.properties
    ):
      _DeleteVirtualClusterGeneratedProperties(cluster, dataproc)
  except AttributeError:
    # The field is not set.
    pass


def _DeleteClusterGeneratedProperties(cluster, dataproc):
  """Removes Dataproc generated properties from GCE-based Clusters."""
  # Filter out Dataproc-generated properties.
  props = encoding.MessageToPyValue(cluster.config.softwareConfig.properties)
  # We don't currently have a nice way to tell which properties are
  # Dataproc-generated, so for now, delete a few properties that we know contain
  # cluster-specific info.
  prop_prefixes_to_delete = (
      'hdfs:dfs.namenode.lifeline.rpc-address',
      'hdfs:dfs.namenode.servicerpc-address',
  )

  prop_keys_to_delete = [
      prop_key
      for prop_key in props.keys()
      if prop_key.startswith(prop_prefixes_to_delete)
  ]

  for prop in prop_keys_to_delete:
    del props[prop]
  if not props:
    cluster.config.softwareConfig.properties = None
  else:
    cluster.config.softwareConfig.properties = (
        encoding.DictToAdditionalPropertyMessage(
            props, dataproc.messages.SoftwareConfig.PropertiesValue
        )
    )


def _DeleteVirtualClusterGeneratedProperties(cluster, dataproc):
  """Removes Dataproc generated properties from Virtual Clusters."""
  # Filter out Dataproc-generated properties.
  props = encoding.MessageToPyValue(
      cluster.virtualClusterConfig.kubernetesClusterConfig.kubernetesSoftwareConfig.properties
  )
  # We don't currently have a nice way to tell which properties are
  # Dataproc-generated, so for now, delete a few properties that we know contain
  # cluster-specific info.
  prop_prefixes_to_delete = (
      # Output only properties from DPGKE.
      'dpgke:dpgke.unstable.outputOnly.',
  )

  prop_keys_to_delete = [
      prop_key
      for prop_key in props.keys()
      if prop_key.startswith(prop_prefixes_to_delete)
  ]

  for prop in prop_keys_to_delete:
    del props[prop]

  if not props:
    cluster.virtualClusterConfig.kubernetesClusterConfig.kubernetesSoftwareConfig.properties = (
        None
    )
  else:
    cluster.virtualClusterConfig.kubernetesClusterConfig.kubernetesSoftwareConfig.properties = encoding.DictToAdditionalPropertyMessage(
        props, dataproc.messages.KubernetesSoftwareConfig.PropertiesValue
    )


def ClusterKey(cluster, key_type):
  """Return a cluster-generated public encryption key if there is one.

  Args:
    cluster: Cluster to check for an encryption key.
    key_type: Dataproc clusters publishes both RSA and ECIES public keys.

  Returns:
    The public key for the cluster if there is one, otherwise None
  """
  master_instance_refs = cluster.config.masterConfig.instanceReferences
  if not master_instance_refs:
    return None
  if key_type == 'ECIES':
    return master_instance_refs[0].publicEciesKey
  return master_instance_refs[0].publicKey


def AddReservationAffinityGroup(parser, group_text, affinity_text):
  """Adds the argument group to handle reservation affinity configurations."""
  group = parser.add_group(help=group_text)
  group.add_argument(
      '--reservation-affinity',
      choices=['any', 'none', 'specific'],
      default='any',
      help=affinity_text,
  )
  group.add_argument(
      '--reservation',
      help="""
The name of the reservation, required when `--reservation-affinity=specific`.
""",
  )


def ValidateReservationAffinityGroup(args):
  """Validates flags specifying reservation affinity."""
  affinity = getattr(args, 'reservation_affinity', None)
  if affinity == 'specific':
    if not args.IsSpecified('reservation'):
      raise exceptions.ArgumentError(
          '--reservation must be specified with --reservation-affinity=specific'
      )


def GetReservationAffinity(args, client):
  """Returns the message of reservation affinity for the instance."""
  if args.IsSpecified('reservation_affinity'):
    type_msgs = (
        client.messages.ReservationAffinity.ConsumeReservationTypeValueValuesEnum
    )

    reservation_key = None
    reservation_values = []

    if args.reservation_affinity == 'none':
      reservation_type = type_msgs.NO_RESERVATION
    elif args.reservation_affinity == 'specific':
      reservation_type = type_msgs.SPECIFIC_RESERVATION
      # Currently, the key is fixed and the value is the name of the
      # reservation.
      # The value being a repeated field is reserved for future use when user
      # can specify more than one reservation names from which the VM can take
      # capacity from.
      reservation_key = RESERVATION_AFFINITY_KEY
      reservation_values = [args.reservation]
    else:
      reservation_type = type_msgs.ANY_RESERVATION

    return client.messages.ReservationAffinity(
        consumeReservationType=reservation_type,
        key=reservation_key or None,
        values=reservation_values,
    )

  return None


RESERVATION_AFFINITY_KEY = 'compute.googleapis.com/reservation-name'


def AddKerberosGroup(parser):
  """Adds the argument group to handle Kerberos configurations."""
  kerberos_group = parser.add_argument_group(
      mutex=True,
      help='Specifying these flags will enable Kerberos for the cluster.',
  )
  # Not mutually exclusive
  kerberos_flag_group = kerberos_group.add_argument_group()
  kerberos_flag_group.add_argument(
      '--enable-kerberos',
      action='store_true',
      help="""\
        Enable Kerberos on the cluster.
        """,
  )
  kerberos_flag_group.add_argument(
      '--kerberos-root-principal-password-uri',
      help="""\
        Google Cloud Storage URI of a KMS encrypted file containing the root
        principal password. Must be a Cloud Storage URL beginning with 'gs://'.
        """,
  )
  # Add kerberos-kms-key args
  kerberos_kms_flag_overrides = {
      'kms-key': '--kerberos-kms-key',
      'kms-keyring': '--kerberos-kms-key-keyring',
      'kms-location': '--kerberos-kms-key-location',
      'kms-project': '--kerberos-kms-key-project',
  }
  kms_resource_args.AddKmsKeyResourceArg(
      kerberos_flag_group,
      'password',
      flag_overrides=kerberos_kms_flag_overrides,
      name='--kerberos-kms-key',
  )

  kerberos_group.add_argument(
      '--kerberos-config-file',
      help="""\
Path to a YAML (or JSON) file containing the configuration for Kerberos on the
cluster. If you pass `-` as the value of the flag the file content will be read
from stdin.

The YAML file is formatted as follows:

```
  # Optional. Flag to indicate whether to Kerberize the cluster.
  # The default value is true.
  enable_kerberos: true

  # Optional. The Google Cloud Storage URI of a KMS encrypted file
  # containing the root principal password.
  root_principal_password_uri: gs://bucket/password.encrypted

  # Optional. The URI of the Cloud KMS key used to encrypt
  # sensitive files.
  kms_key_uri:
    projects/myproject/locations/global/keyRings/mykeyring/cryptoKeys/my-key

  # Configuration of SSL encryption. If specified, all sub-fields
  # are required. Otherwise, Dataproc will provide a self-signed
  # certificate and generate the passwords.
  ssl:
    # Optional. The Google Cloud Storage URI of the keystore file.
    keystore_uri: gs://bucket/keystore.jks

    # Optional. The Google Cloud Storage URI of a KMS encrypted
    # file containing the password to the keystore.
    keystore_password_uri: gs://bucket/keystore_password.encrypted

    # Optional. The Google Cloud Storage URI of a KMS encrypted
    # file containing the password to the user provided key.
    key_password_uri: gs://bucket/key_password.encrypted

    # Optional. The Google Cloud Storage URI of the truststore
    # file.
    truststore_uri: gs://bucket/truststore.jks

    # Optional. The Google Cloud Storage URI of a KMS encrypted
    # file containing the password to the user provided
    # truststore.
    truststore_password_uri:
      gs://bucket/truststore_password.encrypted

  # Configuration of cross realm trust.
  cross_realm_trust:
    # Optional. The remote realm the Dataproc on-cluster KDC will
    # trust, should the user enable cross realm trust.
    realm: REMOTE.REALM

    # Optional. The KDC (IP or hostname) for the remote trusted
    # realm in a cross realm trust relationship.
    kdc: kdc.remote.realm

    # Optional. The admin server (IP or hostname) for the remote
    # trusted realm in a cross realm trust relationship.
    admin_server: admin-server.remote.realm

    # Optional. The Google Cloud Storage URI of a KMS encrypted
    # file containing the shared password between the on-cluster
    # Kerberos realm and the remote trusted realm, in a cross
    # realm trust relationship.
    shared_password_uri:
      gs://bucket/cross-realm.password.encrypted

  # Optional. The Google Cloud Storage URI of a KMS encrypted file
  # containing the master key of the KDC database.
  kdc_db_key_uri: gs://bucket/kdc_db_key.encrypted

  # Optional. The lifetime of the ticket granting ticket, in
  # hours. If not specified, or user specifies 0, then default
  # value 10 will be used.
  tgt_lifetime_hours: 1

  # Optional. The name of the Kerberos realm. If not specified,
  # the uppercased domain name of the cluster will be used.
  realm: REALM.NAME
```
        """,
  )


def ParseKerberosConfigFile(dataproc, kerberos_config_file):
  """Parse a kerberos-config-file into the KerberosConfig message."""
  data = console_io.ReadFromFileOrStdin(kerberos_config_file, binary=False)
  try:
    kerberos_config_data = yaml.load(data)
  except Exception as e:
    raise exceptions.ParseError('Cannot parse YAML:[{0}]'.format(e))

  ssl_config = kerberos_config_data.get('ssl', {})
  keystore_uri = ssl_config.get('keystore_uri')
  truststore_uri = ssl_config.get('truststore_uri')
  keystore_password_uri = ssl_config.get('keystore_password_uri')
  key_password_uri = ssl_config.get('key_password_uri')
  truststore_password_uri = ssl_config.get('truststore_password_uri')

  cross_realm_trust_config = kerberos_config_data.get('cross_realm_trust', {})
  cross_realm_trust_realm = cross_realm_trust_config.get('realm')
  cross_realm_trust_kdc = cross_realm_trust_config.get('kdc')
  cross_realm_trust_admin_server = cross_realm_trust_config.get('admin_server')
  cross_realm_trust_shared_password_uri = cross_realm_trust_config.get(
      'shared_password_uri'
  )
  kerberos_config_msg = dataproc.messages.KerberosConfig(
      # Unless user explicitly disable kerberos in kerberos config,
      # consider the existence of the kerberos config is enabling
      # kerberos, explicitly or implicitly.
      enableKerberos=kerberos_config_data.get('enable_kerberos', True),
      rootPrincipalPasswordUri=kerberos_config_data.get(
          'root_principal_password_uri'
      ),
      kmsKeyUri=kerberos_config_data.get('kms_key_uri'),
      kdcDbKeyUri=kerberos_config_data.get('kdc_db_key_uri'),
      tgtLifetimeHours=kerberos_config_data.get('tgt_lifetime_hours'),
      realm=kerberos_config_data.get('realm'),
      keystoreUri=keystore_uri,
      keystorePasswordUri=keystore_password_uri,
      keyPasswordUri=key_password_uri,
      truststoreUri=truststore_uri,
      truststorePasswordUri=truststore_password_uri,
      crossRealmTrustRealm=cross_realm_trust_realm,
      crossRealmTrustKdc=cross_realm_trust_kdc,
      crossRealmTrustAdminServer=cross_realm_trust_admin_server,
      crossRealmTrustSharedPasswordUri=cross_realm_trust_shared_password_uri,
  )

  return kerberos_config_msg


def AddSecureMultiTenancyGroup(parser):
  """Adds the argument group to handle Secure Multi-Tenancy configurations."""
  secure_multi_tenancy_group = parser.add_argument_group(
      mutex=True,
      help=(
          'Specifying these flags will enable Secure Multi-Tenancy for the'
          ' cluster.'
      ),
  )
  secure_multi_tenancy_group.add_argument(
      '--identity-config-file',
      help="""\
Path to a YAML (or JSON) file containing the configuration for Secure Multi-Tenancy
on the cluster. The path can be a Cloud Storage URL (Example: 'gs://path/to/file')
or a local file system path. If you pass "-" as the value of the flag the file content
will be read from stdin.

The YAML file is formatted as follows:

```
  # Required. The mapping from user accounts to service accounts.
  user_service_account_mapping:
    bob@company.com: service-account-bob@project.iam.gserviceaccount.com
    alice@company.com: service-account-alice@project.iam.gserviceaccount.com
```
        """,
  )
  secure_multi_tenancy_group.add_argument(
      '--secure-multi-tenancy-user-mapping',
      help=textwrap.dedent(
          """\
          A string of user-to-service-account mappings. Mappings are separated
          by commas, and each mapping takes the form of
          "user-account:service-account". Example:
          "bob@company.com:service-account-bob@project.iam.gserviceaccount.com,alice@company.com:service-account-alice@project.iam.gserviceaccount.com"."""
      ),
  )


def ParseIdentityConfigFile(dataproc, identity_config_file):
  """Parses a identity-config-file into the IdentityConfig message."""

  if identity_config_file.startswith('gs://'):
    data = storage_helpers.ReadObject(identity_config_file)
  else:
    data = console_io.ReadFromFileOrStdin(identity_config_file, binary=False)

  try:
    identity_config_data = yaml.load(data)
  except Exception as e:
    raise exceptions.ParseError('Cannot parse YAML:[{0}]'.format(e))

  user_service_account_mapping = encoding.DictToAdditionalPropertyMessage(
      identity_config_data.get('user_service_account_mapping', {}),
      dataproc.messages.IdentityConfig.UserServiceAccountMappingValue,
  )

  identity_config_data_msg = dataproc.messages.IdentityConfig(
      userServiceAccountMapping=user_service_account_mapping
  )

  return identity_config_data_msg


def ParseSecureMultiTenancyUserServiceAccountMappingString(
    user_service_account_mapping_string,
):
  """Parses a secure-multi-tenancy-user-mapping string into a dictionary."""

  user_service_account_mapping = collections.OrderedDict()
  # parse the string, throw error if string is not in
  # "user1:service-account1,user2:service-account2" format
  mapping_str_list = user_service_account_mapping_string.split(',')
  for mapping_str in mapping_str_list:
    mapping = mapping_str.split(':')
    if len(mapping) != 2:
      raise exceptions.ArgumentError(
          'Invalid Secure Multi-Tenancy User Mapping.'
      )
    user_service_account_mapping[mapping[0]] = mapping[1]
  return user_service_account_mapping


def GetInstanceSelectionList(dataproc, args):
  """Build List of InstanceSelection from the given flags."""
  if args.secondary_worker_machine_types is None:
    return []
  instance_selection_list = []
  for machine_type_config in args.secondary_worker_machine_types:
    if 'type' not in machine_type_config or not machine_type_config['type']:
      raise exceptions.ArgumentError(
          'Missing machine type for secondary-worker-machine-types'
      )
    machine_types = machine_type_config['type']

    if 'rank' not in machine_type_config:
      rank = 0
    else:
      rank = machine_type_config['rank']
      if len(rank) != 1 or not rank[0].isdigit():
        raise exceptions.ArgumentError(
            'Invalid value for rank in secondary-worker-machine-types'
        )
      rank = int(rank[0])

    instance_selection = dataproc.messages.InstanceSelection()
    instance_selection.machineTypes = machine_types
    instance_selection.rank = rank

    instance_selection_list.append(instance_selection)

  return instance_selection_list


class ArgMultiValueDict:
  """Converts argument values into multi-valued mappings.

  Values for the repeated keys are collected in a list.
  """

  def __init__(self):
    ops = '='
    key_op_value_pattern = '([^{ops}]+)([{ops}]?)(.*)'.format(ops=ops)
    self.key_op_value = re.compile(key_op_value_pattern, re.DOTALL)

  def __call__(self, arg_value):
    arg_list = [item.strip() for item in arg_value.split(',')]
    arg_dict = collections.OrderedDict()
    for arg in arg_list:
      match = self.key_op_value.match(arg)
      if not match:
        raise arg_parsers.ArgumentTypeError(
            'Invalid flag value [{0}]'.format(arg)
        )
      key, _, value = (
          match.group(1).strip(),
          match.group(2),
          match.group(3).strip(),
      )
      arg_dict.setdefault(key, []).append(value)
    return arg_dict
