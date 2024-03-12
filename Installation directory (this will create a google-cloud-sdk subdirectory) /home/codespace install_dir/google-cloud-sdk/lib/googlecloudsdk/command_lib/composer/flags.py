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
"""Helpers and common arguments for Composer commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import argparse
import ipaddress
import re

from googlecloudsdk.api_lib.composer import util as api_util
from googlecloudsdk.calliope import actions
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.composer import parsers
from googlecloudsdk.command_lib.composer import util as command_util
from googlecloudsdk.command_lib.util.apis import arg_utils
from googlecloudsdk.command_lib.util.args import labels_util
from googlecloudsdk.core import properties

import six

MIN_TRIGGERER_AIRFLOW_VERSION = '2.2.5'
MIN_TRIGGERER_COMPOSER_VERSION = '2.0.31'
MIN_COMPOSER3_VERSION = '3'
MIN_SCHEDULED_SNAPSHOTS_COMPOSER_VERSION = '2.0.32'
MIN_COMPOSER_RUN_AIRFLOW_CLI_VERSION = '2.4.0'

PREREQUISITE_OPTION_ERROR_MSG = """\
Cannot specify --{opt} without --{prerequisite}.
"""

ENABLED_TRIGGERER_IS_REQUIRED_MSG = """\
Cannot specify --{opt} without enabling a triggerer.
"""

INVALID_OPTION_FOR_MIN_IMAGE_VERSION_ERROR_MSG = """\
Cannot specify {opt}. Composer version {composer_version} and Airflow version {airflow_version} are required.
"""

_INVALID_OPTION_FOR_V2_ERROR_MSG = """\
Cannot specify {opt} with Composer 2.X or greater.
"""

_INVALID_OPTION_FOR_V1_ERROR_MSG = """\
Cannot specify {opt} with Composer 1.X.
"""

COMPOSER3_IS_REQUIRED_MSG = """\
Cannot specify {opt}. Composer version {composer_version} or greater is required.
"""

COMPOSER3_IS_NOT_SUPPORTED_MSG = """\
Cannot specify {opt} with Composer version {composer_version} or greater.
"""


def ValidateComposerVersionExclusiveOptionFactory(composer_v1_option,
                                                  error_message):
  """Creates Composer version specific ActionClass decorators."""

  def ValidateComposerVersionExclusiveOptionDecorator(action_class):
    """Decorates ActionClass to cross-validate argument with Composer version."""
    original_call = action_class.__call__

    def DecoratedCall(self, parser, namespace, value, option_string=None):

      def IsImageVersionStringComposerV1(image_version):
        return (image_version.startswith('composer-1.') or
                image_version.startswith('composer-1-'))

      try:
        if namespace.image_version and IsImageVersionStringComposerV1(
            namespace.image_version) != composer_v1_option:
          raise command_util.InvalidUserInputError(
              error_message.format(opt=option_string))
      except AttributeError:
        # Attribute flag for image version is only conditionally added to the
        # parser, so it may be missing in the namespace.
        pass
      original_call(self, parser, namespace, value, option_string)

    action_class.__call__ = DecoratedCall
    return action_class

  return ValidateComposerVersionExclusiveOptionDecorator


@ValidateComposerVersionExclusiveOptionFactory(True,
                                               _INVALID_OPTION_FOR_V2_ERROR_MSG)
class V1ExclusiveStoreAction(argparse._StoreAction):  # pylint: disable=protected-access
  """StoreActionClass first validating if option is Composer 1 exclusive."""


@ValidateComposerVersionExclusiveOptionFactory(False,
                                               _INVALID_OPTION_FOR_V1_ERROR_MSG)
class V2ExclusiveStoreAction(argparse._StoreAction):  # pylint: disable=protected-access
  """StoreActionClass first validating if option is Composer >=2 exclusive."""


_AIRFLOW_VERSION_TYPE = arg_parsers.RegexpValidator(
    r'^(\d+(?:\.\d+(?:\.\d+(?:-build\.\d+)?)?)?)',
    'must be in the form X[.Y[.Z]].',
)

_IMAGE_VERSION_TYPE = arg_parsers.RegexpValidator(
    r'^composer-(\d+(?:\.\d+\.\d+(?:-[a-z]+\.\d+)?)?|latest)-airflow-(\d+(?:\.\d+(?:\.\d+(?:-build\.\d+)?)?)?)',
    'must be in the form \'composer-A[.B.C[-D.E]]-airflow-X[.Y[.Z]]\' or '
    '\'latest\' can be provided in place of the Cloud Composer version '
    'string. For example: \'composer-latest-airflow-1.10.0\'.')

# TODO(b/118349075): Refactor global Argument definitions to be factory methods.
ENVIRONMENT_NAME_ARG = base.Argument(
    'name', metavar='NAME', help='The name of an environment.')

MULTI_ENVIRONMENT_NAME_ARG = base.Argument(
    'name', metavar='NAME', nargs='+', help='The name of an environment.')

MULTI_OPERATION_NAME_ARG = base.Argument(
    'name', metavar='NAME', nargs='+', help='The name or UUID of an operation.')

OPERATION_NAME_ARG = base.Argument(
    'name', metavar='NAME', help='The name or UUID of an operation.')

LOCATION_FLAG = base.Argument(
    '--location',
    required=False,
    help='The Cloud Composer location (e.g., us-central1).',
    action=actions.StoreProperty(properties.VALUES.composer.location))

_ENV_VAR_NAME_ERROR = (
    'Only upper and lowercase letters, digits, and underscores are allowed. '
    'Environment variable names may not start with a digit.')

_INVALID_IPV4_CIDR_BLOCK_ERROR = ('Invalid format of IPV4 CIDR block.')
_INVALID_GKE_MASTER_IPV4_CIDR_BLOCK_ERROR = (
    'Not a valid IPV4 CIDR block value for the kubernetes master')
_INVALID_WEB_SERVER_IPV4_CIDR_BLOCK_ERROR = (
    'Not a valid IPV4 CIDR block value for the Airflow web server')
_INVALID_CLOUD_SQL_IPV4_CIDR_BLOCK_ERROR = (
    'Not a valid IPV4 CIDR block value for the Cloud SQL instance')
_INVALID_COMPOSER_NETWORK_IPV4_CIDR_BLOCK_ERROR = (
    'Not a valid IPV4 CIDR block value for the composer network')
_INVALID_COMPOSER_INTERNAL_IPV4_CIDR_BLOCK_ERROR = (
    'Not a valid IPV4 CIDR block value for the composer network. This should'
    ' have a netmask length of 20.'
)
_ENVIRONMENT_SIZE_MAPPING = {
    'ENVIRONMENT_SIZE_UNSPECIFIED': 'unspecified',
    'ENVIRONMENT_SIZE_SMALL': 'small',
    'ENVIRONMENT_SIZE_MEDIUM': 'medium',
    'ENVIRONMENT_SIZE_LARGE': 'large'
}

AIRFLOW_CONFIGS_FLAG_GROUP_DESCRIPTION = (
    'Group of arguments for modifying the Airflow configuration.')

CLEAR_AIRFLOW_CONFIGS_FLAG = base.Argument(
    '--clear-airflow-configs',
    action='store_true',
    help="""\
    Removes all Airflow config overrides from the environment.
    """)

UPDATE_AIRFLOW_CONFIGS_FLAG = base.Argument(
    '--update-airflow-configs',
    metavar='KEY=VALUE',
    type=arg_parsers.ArgDict(key_type=str, value_type=str),
    action=arg_parsers.UpdateAction,
    help="""\
    A list of Airflow config override KEY=VALUE pairs to set. If a config
    override exists, its value is updated; otherwise, a new config override
    is created.

    KEYs should specify the configuration section and property name,
    separated by a hyphen, for example `core-print_stats_interval`. The
    section may not contain a closing square brace or period. The property
    name must be non-empty and may not contain an equals sign, semicolon,
    or period. By convention, property names are spelled with
    `snake_case.` VALUEs may contain any character.
    """)

REMOVE_AIRFLOW_CONFIGS_FLAG = base.Argument(
    '--remove-airflow-configs',
    metavar='KEY',
    type=arg_parsers.ArgList(),
    action=arg_parsers.UpdateAction,
    help="""\
    A list of Airflow config override keys to remove.
    """)

ENV_VARIABLES_FLAG_GROUP_DESCRIPTION = (
    'Group of arguments for modifying environment variables.')

UPDATE_ENV_VARIABLES_FLAG = base.Argument(
    '--update-env-variables',
    metavar='NAME=VALUE',
    type=arg_parsers.ArgDict(key_type=str, value_type=str),
    action=arg_parsers.UpdateAction,
    help="""\
    A list of environment variable NAME=VALUE pairs to set and provide to the
    Airflow scheduler, worker, and webserver processes. If an environment
    variable exists, its value is updated; otherwise, a new environment
    variable is created.

    NAMEs are the environment variable names and may contain upper and
    lowercase letters, digits, and underscores; they must not begin with a
    digit.

    User-specified environment variables should not be used to set Airflow
    configuration properties. Instead use the `--update-airflow-configs` flag.
    """)

REMOVE_ENV_VARIABLES_FLAG = base.Argument(
    '--remove-env-variables',
    metavar='NAME',
    type=arg_parsers.ArgList(),
    action=arg_parsers.UpdateAction,
    help="""\
    A list of environment variables to remove.

    Environment variables that have system-provided defaults cannot be unset
    with the `--remove-env-variables` or `--clear-env-variables` flags; only
    the user-supplied overrides will be removed.
    """)

CLEAR_ENV_VARIABLES_FLAG = base.Argument(
    '--clear-env-variables',
    action='store_true',
    help="""\
    Removes all environment variables from the environment.

    Environment variables that have system-provided defaults cannot be unset
    with the `--remove-env-variables` or `--clear-env-variables` flags; only
    the user-supplied overrides will be removed.
    """)

ENV_UPGRADE_GROUP_DESCRIPTION = (
    'Group of arguments for performing in-place environment upgrades.')

UPDATE_AIRFLOW_VERSION_FLAG = base.Argument(
    '--airflow-version',
    type=_AIRFLOW_VERSION_TYPE,
    metavar='AIRFLOW_VERSION',
    help="""\
    Upgrade the environment to a later Apache Airflow version in-place.

    Must be of the form `X[.Y[.Z]]`, where `[]` denotes optional fragments.
    Examples: `2`, `2.3`, `2.3.4`.

    The Apache Airflow version is a semantic version or an alias in the form of
    major or major.minor version numbers, resolved to the latest matching Apache
    Airflow version supported in the current Cloud Composer version. The
    resolved version is stored in the upgraded environment.
    """)

UPDATE_IMAGE_VERSION_FLAG = base.Argument(
    '--image-version',
    type=_IMAGE_VERSION_TYPE,
    metavar='IMAGE_VERSION',
    help="""\
    Upgrade the environment to a later version in-place.

    The image version encapsulates the versions of both Cloud Composer and
    Apache Airflow. Must be of the form
    `composer-A[.B.C[-D.E]]-airflow-X[.Y[.Z]]`, where `[]` denotes optional
    fragments.

    Examples: `composer-2-airflow-2`, `composer-2-airflow-2.2`,
    `composer-2.1.2-airflow-2.3.4`.

    The Cloud Composer portion of the image version is a semantic version or
    an alias in the form of major version number or `latest`, resolved to the
    current Cloud Composer version. The Apache Airflow portion of the image
    version is a semantic version or an alias in the form of major or
    major.minor version numbers, resolved to the latest matching Apache Airflow
    version supported in the given Cloud Composer version. The resolved versions
    are stored in the upgraded environment.
    """)

UPDATE_PYPI_FROM_FILE_FLAG = base.Argument(
    '--update-pypi-packages-from-file',
    help="""\
    The path to a file containing a list of PyPI packages to install in
    the environment. Each line in the file should contain a package
    specification in the format of the update-pypi-package argument
    defined above. The path can be a local file path or a Google Cloud Storage
    file path (Cloud Storage file path starts with 'gs://').
    """)

LABELS_FLAG_GROUP_DESCRIPTION = (
    'Group of arguments for modifying environment labels.')

GENERAL_REMOVAL_FLAG_GROUP_DESCRIPTION = 'Arguments available for item removal.'

PYPI_PACKAGES_FLAG_GROUP_DESCRIPTION = (
    'Group of arguments for modifying the PyPI package configuration.')

AUTOSCALING_FLAG_GROUP_DESCRIPTION = (
    'Group of arguments for setting workloads configuration in Composer 2.X '
    'or greater (--scheduler-count flag is available for '
    'Composer 1.X as well).')

SCHEDULED_SNAPSHOTS_GROUP_DESCRIPTION = (
    'Group of arguments for setting scheduled snapshots settings in Composer '
    '{} or greater.').format(MIN_SCHEDULED_SNAPSHOTS_COMPOSER_VERSION)

SCHEDULED_SNAPSHOTS_UPDATE_GROUP_DESCRIPTION = (
    'Group of arguments used during update of scheduled snapshots settings in '
    'Composer {} or greater.').format(MIN_SCHEDULED_SNAPSHOTS_COMPOSER_VERSION)

TRIGGERER_PARAMETERS_FLAG_GROUP_DESCRIPTION = (
    'Group of arguments for setting triggerer settings in Composer {} '
    'or greater.'.format(MIN_TRIGGERER_COMPOSER_VERSION))

DAG_PROCESSOR_PARAMETERS_FLAG_GROUP_DESCRIPTION = (
    'Group of arguments for setting dag processor settings in Composer {} '
    'or greater.'.format(MIN_COMPOSER3_VERSION)
)

TRIGGERER_ENABLED_GROUP_DESCRIPTION = (
    'Group of arguments for setting triggerer settings during update '
    'in Composer {} or greater.'.format(MIN_TRIGGERER_COMPOSER_VERSION))

MASTER_AUTHORIZED_NETWORKS_GROUP_DESCRIPTION = (
    'Group of arguments for setting master authorized networks configuration.')

CLOUD_DATA_LINEAGE_INTEGRATION_GROUP_DESCRIPTION = (
    'Group of arguments for setting Cloud Data Lineage integration '
    'configuration in Composer 2.')

CLEAR_PYPI_PACKAGES_FLAG = base.Argument(
    '--clear-pypi-packages',
    action='store_true',
    help="""\
    Removes all PyPI packages from the environment.

    PyPI packages that are required by the environment's core software
    cannot be uninstalled with the `--remove-pypi-packages` or
    `--clear-pypi-packages` flags.
    """)

UPDATE_PYPI_PACKAGE_FLAG = base.Argument(
    '--update-pypi-package',
    metavar='PACKAGE[EXTRAS_LIST]VERSION_SPECIFIER',
    action='append',
    default=[],
    help="""\
    A PyPI package to add to the environment. If a package exists, its
    value is updated; otherwise, a new package is installed.

    The value takes the form of: `PACKAGE[EXTRAS_LIST]VERSION_SPECIFIER`,
    as one would specify in a pip requirements file.

    PACKAGE is specified as a package name, such as `numpy.` EXTRAS_LIST is
    a comma-delimited list of PEP 508 distribution extras that may be
    empty, in which case the enclosing square brackets may be omitted.
    VERSION_SPECIFIER is an optional PEP 440 version specifier. If both
    EXTRAS_LIST and VERSION_SPECIFIER are omitted, the `=` and
    everything to the right may be left empty.

    This is a repeated argument that can be specified multiple times to
    update multiple packages. If PACKAGE appears more than once, the last
    value will be used.
    """)

REMOVE_PYPI_PACKAGES_FLAG = base.Argument(
    '--remove-pypi-packages',
    metavar='PACKAGE',
    type=arg_parsers.ArgList(),
    action=arg_parsers.UpdateAction,
    help="""\
    A list of PyPI package names to remove.

    PyPI packages that are required by the environment's core software
    cannot be uninstalled with the `--remove-pypi-packages` or
    `--clear-pypi-packages` flags.
    """)

ENABLE_IP_ALIAS_FLAG = base.Argument(
    '--enable-ip-alias',
    default=None,
    action='store_true',
    help="""\
    Enable use of alias IPs (https://cloud.google.com/compute/docs/alias-ip/)
    for Pod IPs. This will require at least two secondary ranges in the
    subnetwork, one for the pod IPs and another to reserve space for the
    services range.
    """)

DISABLE_MASTER_AUTHORIZED_NETWORKS_FLAG = base.Argument(
    '--disable-master-authorized-networks',
    default=None,
    action='store_true',
    help="""\
    Disable Master Authorized Networks feature
    (https://cloud.google.com/kubernetes-engine/docs/how-to/authorized-networks/)
    in the Composer Environment's GKE cluster.
    """)

ENABLE_MASTER_AUTHORIZED_NETWORKS_FLAG = base.Argument(
    '--enable-master-authorized-networks',
    default=None,
    action='store_true',
    help="""\
    Enable Master Authorized Networks feature
    (https://cloud.google.com/kubernetes-engine/docs/how-to/authorized-networks/)
    in the Composer Environment's GKE cluster.
    """)

MASTER_AUTHORIZED_NETWORKS_FLAG = base.Argument(
    '--master-authorized-networks',
    default=None,
    metavar='NETWORK',
    type=arg_parsers.ArgList(),
    help="""
    Comma separated Master Authorized Networks specified in CIDR notation.

    Cannot be specified unless `--enable-master-authorized-networks` is also specified.
    """)

CLUSTER_SECONDARY_RANGE_NAME_FLAG = base.Argument(
    '--cluster-secondary-range-name',
    default=None,
    help="""\
    Secondary range to be used as the source for pod IPs. Alias ranges will be
    allocated from this secondary range. NAME must be the name of an existing
    secondary range in the cluster subnetwork.

    When used with Composer 1.x, cannot be specified unless `--enable-ip-alias`
    is also specified.
    """)

NETWORK_FLAG = base.Argument(
    '--network',
    required=True,
    help=(
        'The Compute Engine Network to which the environment will '
        "be connected. If a 'Custom Subnet Network' is provided, "
        '`--subnetwork` must be specified as well.'
    ),
)

SUBNETWORK_FLAG = base.Argument(
    '--subnetwork',
    help=(
        'The Compute Engine subnetwork '
        '(https://cloud.google.com/compute/docs/subnetworks) to which the '
        'environment will be connected.'
    ),
)

NETWORK_ATTACHMENT = base.Argument(
    '--network-attachment',
    hidden=True,
    help="""\
    Cloud Composer Network Attachment, which provides connectivity with a user's VPC network,
    supported in Composer {} environments or greater.
    """.format(MIN_COMPOSER3_VERSION),
)

SERVICES_SECONDARY_RANGE_NAME_FLAG = base.Argument(
    '--services-secondary-range-name',
    default=None,
    help="""\
    Secondary range to be used for services (e.g. ClusterIPs). NAME must be the
    name of an existing secondary range in the cluster subnetwork.

    When used with Composer 1.x, cannot be specified unless `--enable-ip-alias`
    is also specified.
    """)

MAX_PODS_PER_NODE = base.Argument(
    '--max-pods-per-node',
    type=int,
    help="""\
    Maximum number of pods that can be assigned to a single node, can be used to
    limit the size of IP range assigned to the node in VPC native cluster setup.

    Cannot be specified unless `--enable-ip-alias` is also specified.
    """)

WEB_SERVER_ALLOW_IP = base.Argument(
    '--web-server-allow-ip',
    action='append',
    type=arg_parsers.ArgDict(spec={
        'ip_range': str,
        'description': str
    }),
    help="""\
    Specifies a list of IPv4 or IPv6 ranges that will be allowed to access the
    Airflow web server. By default, all IPs are allowed to access the web
    server.

    This is a repeated argument that can be specified multiple times to specify
    multiple IP ranges.
    (e.g. `--web-server-allow-ip=ip_range=130.211.160.0/28,description="office network"`
    `--web-server-allow-ip=ip_range=130.211.114.0/28,description="legacy network"`)

    *ip_range*::: IPv4 or IPv6 range of addresses allowed to access the Airflow
    web server.

    *description*::: An optional description of the IP range.
    """)

WEB_SERVER_DENY_ALL = base.Argument(
    '--web-server-deny-all',
    action='store_true',
    help="""\
    Denies all incoming traffic to the Airflow web server.
    """)

WEB_SERVER_ALLOW_ALL = base.Argument(
    '--web-server-allow-all',
    action='store_true',
    help="""\
    Allows all IP addresses to access the Airflow web server.
    """)

UPDATE_WEB_SERVER_ALLOW_IP = base.Argument(
    '--update-web-server-allow-ip',
    type=arg_parsers.ArgDict(spec={
        'ip_range': str,
        'description': str
    }),
    action='append',
    help="""\
    Specifies a list of IPv4 or IPv6 ranges that will be allowed to access the
    Airflow web server. By default, all IPs are allowed to access the web
    server.

    *ip_range*::: IPv4 or IPv6 range of addresses allowed to access the Airflow
    web server.

    *description*::: An optional description of the IP range.
    """)

SUPPORT_WEB_SERVER_PLUGINS = base.Argument(
    '--support-web-server-plugins',
    action='store_true',
    default=None,
    hidden=True,
    help="""\
    Enable the support for web server plugins, supported in Composer {}
    or greater.
    """.format(MIN_COMPOSER3_VERSION),
)

ENABLE_PRIVATE_BUILDS_ONLY = base.Argument(
    '--enable-private-builds-only',
    action='store_const',
    default=None,
    const=True,
    hidden=True,
    help="""\
    Builds performed during operations that install Python
    packages have only private connectivity to Google services,
    supported in Composer {} or greater.
    """.format(MIN_COMPOSER3_VERSION),
)

DISABLE_PRIVATE_BUILDS_ONLY = base.Argument(
    '--disable-private-builds-only',
    action='store_const',
    default=None,
    const=True,
    hidden=True,
    help="""\
    Builds performed during operations that install Python
    packages have an access to the internet
    supported in Composer {} or greater.
    """.format(MIN_COMPOSER3_VERSION),
)

CLOUD_SQL_MACHINE_TYPE = base.Argument(
    '--cloud-sql-machine-type',
    type=str,
    action=V1ExclusiveStoreAction,
    help="""\
    Cloud SQL machine type used by the Airflow database. The list of available
    machine types is available here: https://cloud.google.com/composer/pricing#db-machine-types.
    """)

WEB_SERVER_MACHINE_TYPE = base.Argument(
    '--web-server-machine-type',
    type=str,
    action=V1ExclusiveStoreAction,
    help="""\
    machine type used by the Airflow web server. The list of available machine
    types is available here: https://cloud.google.com/composer/pricing.
    """)

SCHEDULER_CPU = base.Argument(
    '--scheduler-cpu',
    type=float,
    default=None,
    action=V2ExclusiveStoreAction,
    help="""\
    CPU allocated to Airflow scheduler.
    """)

DAG_PROCESSOR_CPU = base.Argument(
    '--dag-processor-cpu',
    type=float,
    default=None,
    action=V2ExclusiveStoreAction,
    help="""\
    CPU allocated to Airflow dag processor, supported in Composer {}
    environments or greater.
    """.format(MIN_COMPOSER3_VERSION),
)

TRIGGERER_CPU = base.Argument(
    '--triggerer-cpu',
    type=float,
    default=None,
    action=V2ExclusiveStoreAction,
    help="""\
    CPU allocated to Airflow triggerer. Supported in the Environments with Composer {} and Airflow {} and greater.
    """.format(MIN_TRIGGERER_COMPOSER_VERSION, MIN_TRIGGERER_AIRFLOW_VERSION))

WORKER_CPU = base.Argument(
    '--worker-cpu',
    type=float,
    default=None,
    action=V2ExclusiveStoreAction,
    help="""\
    CPU allocated to each Airflow worker
    """)

WEB_SERVER_CPU = base.Argument(
    '--web-server-cpu',
    type=float,
    default=None,
    action=V2ExclusiveStoreAction,
    help="""\
    CPU allocated to each Airflow web server
    """)

SCHEDULER_MEMORY = base.Argument(
    '--scheduler-memory',
    type=arg_parsers.BinarySize(
        lower_bound='128MB',
        upper_bound='512GB',
        suggested_binary_size_scales=['MB', 'GB'],
        default_unit='G'),
    default=None,
    action=V2ExclusiveStoreAction,
    help="""\
    Memory allocated to Airflow scheduler, ex. 600MB, 3GB, 2. If units are not provided,
    defaults to GB.
    """)

DAG_PROCESSOR_MEMORY = base.Argument(
    '--dag-processor-memory',
    type=arg_parsers.BinarySize(
        lower_bound='1GB',
        upper_bound='128GB',
        suggested_binary_size_scales=['MB', 'GB'],
        default_unit='G',
    ),
    default=None,
    action=V2ExclusiveStoreAction,
    help="""\
    Memory allocated to Airflow dag processor, ex. 1GB, 3GB, 2. If units are not provided,
    defaults to GB, supported in Composer {} environments or greater.
    """.format(MIN_COMPOSER3_VERSION)
)

TRIGGERER_MEMORY = base.Argument(
    '--triggerer-memory',
    type=arg_parsers.BinarySize(
        lower_bound='128MB',
        upper_bound='512GB',
        suggested_binary_size_scales=['MB', 'GB'],
        default_unit='G'),
    default=None,
    action=V2ExclusiveStoreAction,
    help="""\
    Memory allocated to Airflow triggerer, ex. 512MB, 3GB, 2. If units are not provided,
    defaults to GB. Supported in the Environments with Composer {} and Airflow {} and greater.
    """.format(MIN_TRIGGERER_COMPOSER_VERSION, MIN_TRIGGERER_AIRFLOW_VERSION))

WORKER_MEMORY = base.Argument(
    '--worker-memory',
    type=arg_parsers.BinarySize(
        lower_bound='128MB',
        upper_bound='512GB',
        suggested_binary_size_scales=['MB', 'GB'],
        default_unit='G'),
    action=V2ExclusiveStoreAction,
    default=None,
    help="""\
    Memory allocated to Airflow worker, ex. 600MB, 3GB, 2. If units are not provided,
    defaults to GB.
    """)

WEB_SERVER_MEMORY = base.Argument(
    '--web-server-memory',
    type=arg_parsers.BinarySize(
        lower_bound='128MB',
        upper_bound='512GB',
        suggested_binary_size_scales=['MB', 'GB'],
        default_unit='G'),
    action=V2ExclusiveStoreAction,
    default=None,
    help="""\
    Memory allocated to Airflow web server, ex. 600MB, 3GB, 2. If units are not provided,
    defaults to GB.
    """)

SCHEDULER_STORAGE = base.Argument(
    '--scheduler-storage',
    type=arg_parsers.BinarySize(
        lower_bound='5MB',
        upper_bound='10GB',
        suggested_binary_size_scales=['MB', 'GB'],
        default_unit='G'),
    action=V2ExclusiveStoreAction,
    default=None,
    help="""\
    Storage allocated to Airflow scheduler, ex. 600MB, 3GB, 2. If units are not provided,
    defaults to GB.
    """)

DAG_PROCESSOR_STORAGE = base.Argument(
    '--dag-processor-storage',
    type=arg_parsers.BinarySize(
        lower_bound='0',
        upper_bound='100GB',
        suggested_binary_size_scales=['MB', 'GB'],
        default_unit='G',
    ),
    action=V2ExclusiveStoreAction,
    default=None,
    help="""\
    Storage allocated to Airflow dag processor, ex. 600MB, 3GB, 2. If units are not provided,
    defaults to GB, supported in Composer {} environments or greater.
    """.format(MIN_COMPOSER3_VERSION),
)

WORKER_STORAGE = base.Argument(
    '--worker-storage',
    type=arg_parsers.BinarySize(
        lower_bound='0',
        upper_bound='10GB',
        suggested_binary_size_scales=['MB', 'GB'],
        default_unit='G'),
    action=V2ExclusiveStoreAction,
    default=None,
    help="""\
    Storage allocated to Airflow worker, ex. 600MB, 3GB, 2. If units are not provided,
    defaults to GB.
    """)

WEB_SERVER_STORAGE = base.Argument(
    '--web-server-storage',
    type=arg_parsers.BinarySize(
        lower_bound='0',
        upper_bound='10GB',
        suggested_binary_size_scales=['MB', 'GB'],
        default_unit='G'),
    action=V2ExclusiveStoreAction,
    default=None,
    help="""\
    Storage allocated to Airflow web server, ex. 600MB, 3GB, 2. If units are not provided,
    defaults to GB.
    """)

MIN_WORKERS = base.Argument(
    '--min-workers',
    type=int,
    default=None,
    action=V2ExclusiveStoreAction,
    help="""\
    Minimum number of workers in the Environment.
    """)

MAX_WORKERS = base.Argument(
    '--max-workers',
    action=V2ExclusiveStoreAction,
    type=int,
    default=None,
    help="""\
    Maximum number of workers in the Environment.
    """)

NUM_SCHEDULERS = base.Argument(
    '--scheduler-count',
    type=int,
    default=None,
    help="""\
    Number of schedulers, supported in the Environments with Airflow 2.0.1 and later.
    """)

DAG_PROCESSOR_COUNT = base.Argument(
    '--dag-processor-count',
    type=int,
    action=V2ExclusiveStoreAction,
    default=None,
    help="""\
    Number of dag processors, supported in Composer {} environments or greater.
    """.format(MIN_COMPOSER3_VERSION),
)

TRIGGERER_COUNT = base.Argument(
    '--triggerer-count',
    default=None,
    type=int,
    action=V2ExclusiveStoreAction,
    help="""\
    Number of triggerers, supported in the Environments with Composer {} and Airflow {} and greater.
    """.format(MIN_TRIGGERER_COMPOSER_VERSION, MIN_TRIGGERER_AIRFLOW_VERSION),
)

# TODO(b/259928145): Update Composer version in requirements
ENABLE_HIGH_RESILIENCE = base.Argument(
    '--enable-high-resilience',
    default=None,
    const=True,
    action='store_const',
    help="""\
    Enable high resilience, supported for Composer 2 Environments.
    """
)

DISABLE_HIGH_RESILIENCE = base.Argument(
    '--disable-high-resilience',
    default=None,
    const=True,
    action='store_const',
    help="""\
    Disable high resilience, supported for Composer 2 Environments.
    """
)

ENABLE_LOGS_IN_CLOUD_LOGGING_ONLY = base.Argument(
    '--enable-logs-in-cloud-logging-only',
    default=None,
    const=True,
    action='store_const',
    help="""\
    Enable logs in cloud logging only, supported for Composer 2 Environments.
    """,
)

DISABLE_LOGS_IN_CLOUD_LOGGING_ONLY = base.Argument(
    '--disable-logs-in-cloud-logging-only',
    default=None,
    const=True,
    action='store_const',
    help="""\
    Disable logs in cloud logging only, supported for Composer 2 Environments.
    """,
)

CLOUD_SQL_PREFERRED_ZONE = base.Argument(
    '--cloud-sql-preferred-zone',
    default=None,
    action=V2ExclusiveStoreAction,
    help="""\
    Select cloud sql preferred zone, supported for Composer 2 Environments.
    """,
)

DISABLE_VPC_CONNECTIVITY = base.Argument(
    '--disable-vpc-connectivity',
    default=None,
    hidden=True,
    const=True,
    action='store_const',
    help="""\
    Disable connectivity with a user's VPC network,
    supported in Composer {} environments or greater.
    """.format(MIN_COMPOSER3_VERSION),
)

# Composer 3 only for update
ENABLE_PRIVATE_ENVIRONMENT_UPDATE_FLAG = base.Argument(
    '--enable-private-environment',
    default=None,
    hidden=True,
    action='store_true',
    help="""\
    Disable internet connection from any Composer component,
    supported in Composer {} environments or greater.
    """.format(MIN_COMPOSER3_VERSION),
)

# Composer 3 only for update
DISABLE_PRIVATE_ENVIRONMENT_UPDATE_FLAG = base.Argument(
    '--disable-private-environment',
    default=None,
    hidden=True,
    action='store_true',
    help="""\
    Enable internet connection from any Composer component,
    supported in Composer {} environments or greater.
    """.format(MIN_COMPOSER3_VERSION),
)

ENABLE_TRIGGERER = base.Argument(
    '--enable-triggerer',
    default=None,
    const=True,
    action=actions.DeprecationAction(
        '--enable-triggerer',
        action='store_const',
        warn='This flag is deprecated. '
             'Use --triggerer-count instead.'),
    help="""\
    Enable use of a triggerer, supported in the Environments with Composer {} and Airflow {} and greater.
    """.format(MIN_TRIGGERER_COMPOSER_VERSION, MIN_TRIGGERER_AIRFLOW_VERSION))

DISABLE_TRIGGERER = base.Argument(
    '--disable-triggerer',
    default=None,
    const=True,
    action=actions.DeprecationAction(
        '--disable-triggerer',
        action='store_const',
        warn='This flag is deprecated. '
             'Use --triggerer-count 0 instead.'),
    help="""\
    Disable a triggerer, supported in the Environments with Composer {} and Airflow {} and greater.
    """.format(MIN_TRIGGERER_COMPOSER_VERSION, MIN_TRIGGERER_AIRFLOW_VERSION))

ENVIRONMENT_SIZE_GA = arg_utils.ChoiceEnumMapper(
    arg_name='--environment-size',
    help_str='Size of the environment. Unspecified means that the default option will be chosen.',
    message_enum=api_util.GetMessagesModule(release_track=base.ReleaseTrack.GA)
    .EnvironmentConfig.EnvironmentSizeValueValuesEnum,
    custom_mappings=_ENVIRONMENT_SIZE_MAPPING)

ENVIRONMENT_SIZE_BETA = arg_utils.ChoiceEnumMapper(
    arg_name='--environment-size',
    help_str='Size of the environment. Unspecified means that the default option will be chosen.',
    message_enum=api_util.GetMessagesModule(
        release_track=base.ReleaseTrack.BETA).EnvironmentConfig
    .EnvironmentSizeValueValuesEnum,
    custom_mappings=_ENVIRONMENT_SIZE_MAPPING)

ENVIRONMENT_SIZE_ALPHA = arg_utils.ChoiceEnumMapper(
    arg_name='--environment-size',
    help_str='Size of the environment. Unspecified means that the default option will be chosen.',
    message_enum=api_util.GetMessagesModule(
        release_track=base.ReleaseTrack.ALPHA).EnvironmentConfig
    .EnvironmentSizeValueValuesEnum,
    custom_mappings=_ENVIRONMENT_SIZE_MAPPING)

AIRFLOW_DATABASE_RETENTION_DAYS = base.Argument(
    '--airflow-database-retention-days',
    type=int,
    default=None,
    help="""\
    The number of retention
      days for airflow database retention mechanism.
    """)

ENABLE_CLOUD_DATA_LINEAGE_INTEGRATION_FLAG = base.Argument(
    '--enable-cloud-data-lineage-integration',
    default=None,
    action='store_true',
    help="""\
    Enable Cloud Data Lineage integration, supported for Composer 2 Environments.
    """)

DISABLE_CLOUD_DATA_LINEAGE_INTEGRATION_FLAG = base.Argument(
    '--disable-cloud-data-lineage-integration',
    default=None,
    action='store_true',
    help="""\
    Disable Cloud Data Lineage integration, supported for Composer 2 Environments.
    """)

STORAGE_BUCKET_FLAG = base.Argument(
    '--storage-bucket',
    type=str,
    action=V2ExclusiveStoreAction,
    help="""\
    Name of an exisiting Cloud Storage bucket to be used by the environment.
    Supported only for Composer 2.4.X and above.
    """,
)


def _IsValidIpv4CidrBlock(ipv4_cidr_block):
  """Validates that IPV4 CIDR block arg has valid format.

  Intended to be used as an argparse validator.

  Args:
    ipv4_cidr_block: str, the IPV4 CIDR block string to validate

  Returns:
    bool, True if and only if the IPV4 CIDR block is valid
  """
  return ipaddress.IPv4Network(ipv4_cidr_block) is not None


IPV4_CIDR_BLOCK_FORMAT_VALIDATOR = arg_parsers.CustomFunctionValidator(
    _IsValidIpv4CidrBlock, _INVALID_IPV4_CIDR_BLOCK_ERROR)

CLUSTER_IPV4_CIDR_FLAG = base.Argument(
    '--cluster-ipv4-cidr',
    default=None,
    type=IPV4_CIDR_BLOCK_FORMAT_VALIDATOR,
    help="""\
    IP address range for the pods in this cluster in CIDR notation
    (e.g. 10.0.0.0/14).

    When used with Composer 1.x, cannot be specified unless `--enable-ip-alias`
    is also specified.
    """)

SERVICES_IPV4_CIDR_FLAG = base.Argument(
    '--services-ipv4-cidr',
    default=None,
    type=IPV4_CIDR_BLOCK_FORMAT_VALIDATOR,
    help="""\
    IP range for the services IPs.

    Can be specified as a netmask size (e.g. '/20') or as in CIDR notion
    (e.g. '10.100.0.0/20'). If given as a netmask size, the IP range will
    be chosen automatically from the available space in the network.

    If unspecified, the services CIDR range will be chosen with a default
    mask size.

    When used with Composer 1.x, cannot be specified unless `--enable-ip-alias`
    is also specified.
    """)

ENABLE_IP_MASQ_AGENT_FLAG = base.Argument(
    '--enable-ip-masq-agent',
    default=None,
    action='store_true',
    help="""\
    When enabled, the IP Masquarade Agent
    (https://cloud.google.com/composer/docs/enable-ip-masquerade-agent)
    is deployed to your environment's cluster.
    It performs many-to-one IP address translations to hide a pod's IP address
    behind the cluster node's IP address. This is done when sending traffic to
    destinations outside the cluster's pod CIDR range.

    When used with Composer 1.x, cannot be specified unless `--enable-ip-alias`
    is also specified.
    """)

ENABLE_PRIVATE_ENVIRONMENT_FLAG = base.Argument(
    '--enable-private-environment',
    default=None,
    action='store_true',
    help="""\
    Environment cluster is created with no public IP addresses on the cluster
    nodes.

    If not specified, cluster nodes will be assigned public IP addresses.

    When used with Composer 1.x, cannot be specified unless `--enable-ip-alias`
    is also specified.
    """)

ENABLE_PRIVATE_ENDPOINT_FLAG = base.Argument(
    '--enable-private-endpoint',
    default=None,
    action='store_true',
    help="""\
    Environment cluster is managed using the private IP address of the master
    API endpoint. Therefore access to the master endpoint must be from
    internal IP addresses.

    If not specified, the master API endpoint will be accessible by its public
    IP address.

    Cannot be specified unless `--enable-private-environment` is also
    specified.
    """)

ENABLE_PRIVATELY_USED_PUBLIC_IPS_FLAG = base.Argument(
    '--enable-privately-used-public-ips',
    default=None,
    action='store_true',
    help="""\
    When enabled GKE pods and services may use public(non-RFC1918) IP ranges
    privately. The ranges are specified by '--cluster-ipv4-cidr' and
    `--services-ipv4-cidr` flags.

    Cannot be specified unless `--enable-private-environment` is also
    specified.
    """)

CONNECTION_SUBNETWORK_FLAG = base.Argument(
    '--connection-subnetwork',
    default=None,
    action=V2ExclusiveStoreAction,
    help="""\
    Subnetwork from which an IP address for internal communications will be
    reserved. Needs to belong to the Compute network to which the environment is
    connected. Can be the same subnetwork as the one to which the environment is
    connected.

    Can be specified for Composer 2.X or greater. Cannot be specified
    unless `--enable-private-environment` is also specified.
    """)
CONNECTION_TYPE_FLAG_HELP = """\
    Mode of internal communication within the Composer environment. Must be one
    of `VPC_PEERING` or `PRIVATE_SERVICE_CONNECT`.

    Can be specified for Composer 2.X or greater. Cannot be specified
    unless `--enable-private-environment` is also specified. Cannot be set to
    `VPC_PEERING` if `--connection-subnetwork` is also specified.
    """

CONNECTION_TYPE_FLAG_ALPHA = arg_utils.ChoiceEnumMapper(
    '--connection-type',
    help_str=CONNECTION_TYPE_FLAG_HELP,
    required=False,
    message_enum=api_util.GetMessagesModule(
        release_track=base.ReleaseTrack.ALPHA).NetworkingConfig
    .ConnectionTypeValueValuesEnum)

CONNECTION_TYPE_FLAG_BETA = arg_utils.ChoiceEnumMapper(
    '--connection-type',
    help_str=CONNECTION_TYPE_FLAG_HELP,
    required=False,
    message_enum=api_util.GetMessagesModule(
        release_track=base.ReleaseTrack.BETA).NetworkingConfig
    .ConnectionTypeValueValuesEnum)

CONNECTION_TYPE_FLAG_GA = arg_utils.ChoiceEnumMapper(
    '--connection-type',
    help_str=CONNECTION_TYPE_FLAG_HELP,
    required=False,
    message_enum=api_util.GetMessagesModule(release_track=base.ReleaseTrack.GA)
    .NetworkingConfig.ConnectionTypeValueValuesEnum)


def _GetIpv4CidrMaskSize(ipv4_cidr_block):
  """Returns the size of IPV4 CIDR block mask in bits.

  Args:
    ipv4_cidr_block: str, the IPV4 CIDR block string to check.

  Returns:
    int, the size of the block mask if ipv4_cidr_block is a valid CIDR block
    string, otherwise None.
  """
  network = ipaddress.IPv4Network(ipv4_cidr_block)
  if network is None:
    return None

  return 32 - (network.num_addresses.bit_length() - 1)


def _IsValidMasterIpv4CidrBlockWithMaskSize(ipv4_cidr_block, min_mask_size,
                                            max_mask_size):
  """Validates that IPV4 CIDR block arg for the cluster master is a valid value.

  Args:
    ipv4_cidr_block: str, the IPV4 CIDR block string to validate.
    min_mask_size: int, minimum allowed netmask size for CIDR block.
    max_mask_size: int, maximum allowed netmask size for CIDR block.

  Returns:
    bool, True if and only if the IPV4 CIDR block is valid and has the mask
    size between min_mask_size and max_mask_size.
  """
  is_valid = _IsValidIpv4CidrBlock(ipv4_cidr_block)
  if not is_valid:
    return False

  mask_size = _GetIpv4CidrMaskSize(ipv4_cidr_block)
  return min_mask_size <= mask_size and mask_size <= max_mask_size


_IS_VALID_MASTER_IPV4_CIDR_BLOCK = (
    lambda cidr: _IsValidMasterIpv4CidrBlockWithMaskSize(cidr, 23, 28))

MASTER_IPV4_CIDR_BLOCK_FORMAT_VALIDATOR = arg_parsers.CustomFunctionValidator(
    _IS_VALID_MASTER_IPV4_CIDR_BLOCK, _INVALID_GKE_MASTER_IPV4_CIDR_BLOCK_ERROR)

MASTER_IPV4_CIDR_FLAG = base.Argument(
    '--master-ipv4-cidr',
    default=None,
    type=MASTER_IPV4_CIDR_BLOCK_FORMAT_VALIDATOR,
    help="""\
    IPv4 CIDR range to use for the cluster master network. This should have a
    size of the netmask between 23 and 28.

    Cannot be specified unless `--enable-private-environment` is also
    specified.
    """)

_IS_VALID_WEB_SERVER_IPV4_CIDR_BLOCK = (
    lambda cidr: _IsValidMasterIpv4CidrBlockWithMaskSize(cidr, 24, 29))

WEB_SERVER_IPV4_CIDR_BLOCK_FORMAT_VALIDATOR = arg_parsers.CustomFunctionValidator(
    _IS_VALID_WEB_SERVER_IPV4_CIDR_BLOCK,
    _INVALID_WEB_SERVER_IPV4_CIDR_BLOCK_ERROR)

WEB_SERVER_IPV4_CIDR_FLAG = base.Argument(
    '--web-server-ipv4-cidr',
    default=None,
    type=WEB_SERVER_IPV4_CIDR_BLOCK_FORMAT_VALIDATOR,
    help="""\
    IPv4 CIDR range to use for the Airflow web server network. This should have
    a size of the netmask between 24 and 29.

    Cannot be specified unless `--enable-private-environment` is also
    specified.
    """)

_IS_VALID_CLOUD_SQL_IPV4_CIDR_BLOCK = (
    lambda cidr: _IsValidMasterIpv4CidrBlockWithMaskSize(cidr, 0, 24))

CLOUD_SQL_IPV4_CIDR_BLOCK_FORMAT_VALIDATOR = arg_parsers.CustomFunctionValidator(
    _IS_VALID_CLOUD_SQL_IPV4_CIDR_BLOCK,
    _INVALID_CLOUD_SQL_IPV4_CIDR_BLOCK_ERROR)

CLOUD_SQL_IPV4_CIDR_FLAG = base.Argument(
    '--cloud-sql-ipv4-cidr',
    default=None,
    type=CLOUD_SQL_IPV4_CIDR_BLOCK_FORMAT_VALIDATOR,
    help="""\
    IPv4 CIDR range to use for the Cloud SQL network. This should have a size
    of the netmask not greater than 24.

    Cannot be specified unless `--enable-private-environment` is also
    specified.
    """)
_IS_VALID_COMPOSER_NETWORK_IPV4_CIDR_BLOCK = (
    lambda cidr: _IsValidMasterIpv4CidrBlockWithMaskSize(cidr, 24, 29))

COMPOSER_NETWORK_IPV4_CIDR_BLOCK_FORMAT_VALIDATOR = arg_parsers.CustomFunctionValidator(
    _IS_VALID_COMPOSER_NETWORK_IPV4_CIDR_BLOCK,
    _INVALID_COMPOSER_NETWORK_IPV4_CIDR_BLOCK_ERROR)

COMPOSER_NETWORK_IPV4_CIDR_FLAG = base.Argument(
    '--composer-network-ipv4-cidr',
    default=None,
    type=COMPOSER_NETWORK_IPV4_CIDR_BLOCK_FORMAT_VALIDATOR,
    action=V2ExclusiveStoreAction,
    help="""\
    IPv4 CIDR range to use for the Composer network. This must have
    a size of the netmask between 24 and 29.

    Can be specified for Composer 2.X or greater. Cannot be specified
    unless `--enable-private-environment` is also specified.
    """)

_IS_VALID_COMPOSER_INTERNAL_NETWORK_IPV4_CIDR_BLOCK = (
    lambda cidr: _IsValidMasterIpv4CidrBlockWithMaskSize(cidr, 20, 20))

COMPOSER_INTERNAL_NETWORK_IPV4_CIDR_BLOCK_FORMAT_VALIDATOR = (
    arg_parsers.CustomFunctionValidator(
        _IS_VALID_COMPOSER_INTERNAL_NETWORK_IPV4_CIDR_BLOCK,
        _INVALID_COMPOSER_INTERNAL_IPV4_CIDR_BLOCK_ERROR,
    )
)

COMPOSER_INTERNAL_IPV4_CIDR_FLAG = base.Argument(
    '--composer-internal-ipv4-cidr-block',
    default=None,
    hidden=True,
    type=COMPOSER_INTERNAL_NETWORK_IPV4_CIDR_BLOCK_FORMAT_VALIDATOR,
    action=V2ExclusiveStoreAction,
    help="""\
    The IP range in CIDR notation to use internally by Cloud Composer.
    This should have a netmask length of 20.
    Can be specified for Composer {} or greater.
    """.format(MIN_COMPOSER3_VERSION))

# TODO(b/245909413): Update Composer version in requirements
ENABLE_SCHEDULED_SNAPSHOT_CREATION = base.Argument(
    '--enable-scheduled-snapshot-creation',
    default=None,
    const=True,
    action='store_const',
    required=True,
    help="""\
      When specified, snapshots of the environment will be created according to a schedule.
      Can be specified for Composer {} or greater.
    """.format(MIN_SCHEDULED_SNAPSHOTS_COMPOSER_VERSION))

# TODO(b/245909413): Specify the minor Composer version here:
DISABLE_SCHEDULED_SNAPSHOT_CREATION = base.Argument(
    '--disable-scheduled-snapshot-creation',
    default=None,
    const=True,
    action='store_const',
    help="""\
      Disables automated snapshots creation.
      Can be specified for Composer {} or greater.
    """.format(MIN_SCHEDULED_SNAPSHOTS_COMPOSER_VERSION))

SNAPSHOT_CREATION_SCHEDULE = base.Argument(
    '--snapshot-creation-schedule',
    type=str,
    required=True,
    action=V2ExclusiveStoreAction,
    help="""\
      Cron expression specifying when snapshots of the environment should be created.
      Can be specified for Composer {} or greater.
    """.format(MIN_SCHEDULED_SNAPSHOTS_COMPOSER_VERSION))

SNAPSHOT_LOCATION = base.Argument(
    '--snapshot-location',
    type=str,
    action=V2ExclusiveStoreAction,
    required=True,
    help="""\
      The Cloud Storage location for storing automatically created snapshots.
      Can be specified for Composer {} or greater.
    """.format(MIN_SCHEDULED_SNAPSHOTS_COMPOSER_VERSION))

SNAPSHOT_SCHEDULE_TIMEZONE = base.Argument(
    '--snapshot-schedule-timezone',
    type=str,
    action=V2ExclusiveStoreAction,
    required=True,
    help="""\
      Timezone that sets the context to interpret snapshot_creation_schedule.
      Can be specified for Composer {} or greater.
    """.format(MIN_SCHEDULED_SNAPSHOTS_COMPOSER_VERSION))

MAINTENANCE_WINDOW_START_FLAG = base.Argument(
    '--maintenance-window-start',
    type=arg_parsers.Datetime.Parse,
    required=True,
    help="""\
    Start time of the mantenance window in the form of the full date. Only the
    time of the day is used as a reference for a starting time of the window
    with a provided recurrence.
    See $ gcloud topic datetimes for information on time formats.
    """)

MAINTENANCE_WINDOW_END_FLAG = base.Argument(
    '--maintenance-window-end',
    type=arg_parsers.Datetime.Parse,
    required=True,
    help="""\
    End time of the mantenance window in the form of the full date. Only the
    time of the day is used as a reference for an ending time of the window
    with a provided recurrence. Specified date must take place after the one
    specified as a start date, the difference between will be used as a length
    of a single maintenance window.
    See $ gcloud topic datetimes for information on time formats.
    """)

CLEAR_MAINTENANCE_WINDOW_FLAG = base.Argument(
    '--clear-maintenance-window',
    default=None,
    hidden=True,
    action='store_true',
    help="""\
    Clears the maintenance window settings.
    Can be specified for Composer {} or greater.
    """.format(MIN_COMPOSER3_VERSION))

MAINTENANCE_WINDOW_RECURRENCE_FLAG = base.Argument(
    '--maintenance-window-recurrence',
    type=str,
    required=True,
    help="""\
    An RFC 5545 RRULE, specifying how the maintenance window will recur. The
    minimum requirement for the length of the maintenance window is 12 hours a
    week. Only FREQ=DAILY and FREQ=WEEKLY rules are supported.
    """)

MAINTENANCE_WINDOW_FLAG_GROUP_DESCRIPTION = (
    'Group of arguments for setting the maintenance window value.')

MAINTENANCE_WINDOW_FLAG_UPDATE_GROUP_DESCRIPTION = (
    'Group of arguments for setting the maintenance window value during update.'
)

SKIP_PYPI_PACKAGES_INSTALLATION = base.Argument(
    '--skip-pypi-packages-installation',
    default=None,
    action='store_true',
    help="""\
    When specified, skips the installation of custom PyPI packages from
    the snapshot.
    """)

SKIP_ENVIRONMENT_VARIABLES_SETTING = base.Argument(
    '--skip-environment-variables-setting',
    default=None,
    action='store_true',
    help="""\
    When specified, skips setting environment variables from the snapshot.
    """)

SKIP_AIRFLOW_OVERRIDES_SETTING = base.Argument(
    '--skip-airflow-overrides-setting',
    default=None,
    action='store_true',
    help="""\
    When specified, skips setting Airflow overrides from the snapshot.
    """)

SKIP_COPYING_GCS_DATA = base.Argument(
    '--skip-gcs-data-copying',
    default=None,
    action='store_true',
    help="""\
    When specified, skips copying dags, plugins and data folders from
    the snapshot.
    """)


def GetAndValidateKmsEncryptionKey(args):
  """Validates the KMS key name.

  Args:
    args: list of all the arguments

  Returns:
    string, a fully qualified KMS resource name

  Raises:
    exceptions.InvalidArgumentException: key name not fully specified
  """
  kms_ref = args.CONCEPTS.kms_key.Parse()
  if kms_ref:
    return kms_ref.RelativeName()
  for keyword in ['kms-key', 'kms-keyring', 'kms-location', 'kms-project']:
    if getattr(args, keyword.replace('-', '_'), None):
      raise exceptions.InvalidArgumentException(
          '--kms-key', 'Encryption key not fully specified.')


def AddImportSourceFlag(parser, folder):
  """Adds a --source flag for a storage import command to a parser.

  Args:
    parser: argparse.ArgumentParser, the parser to which to add the flag
    folder: str, the top-level folder in the bucket into which the import
      command will write. Should not contain any slashes. For example, 'dags'.
  """
  base.Argument(
      '--source',
      required=True,
      help="""\
      Path to a local directory/file or Cloud Storage bucket/object to be
      imported into the {}/ subdirectory in the environment's Cloud Storage
      bucket. Cloud Storage paths must begin with 'gs://'.
      """.format(folder)).AddToParser(parser)


def AddImportDestinationFlag(parser, folder):
  """Adds a --destination flag for a storage import command to a parser.

  Args:
    parser: argparse.ArgumentParser, the parser to which to add the flag
    folder: str, the top-level folder in the bucket into which the import
      command will write. Should not contain any slashes. For example, 'dags'.
  """
  base.Argument(
      '--destination',
      metavar='DESTINATION',
      required=False,
      help="""\
      An optional subdirectory under the {}/ directory in the environment's
      Cloud Storage bucket into which to import files. May contain forward
      slashes to delimit multiple levels of subdirectory nesting, but should not
      contain leading or trailing slashes. If the DESTINATION does not exist, it
      will be created.
      """.format(folder)).AddToParser(parser)


def AddExportSourceFlag(parser, folder):
  """Adds a --source flag for a storage export command to a parser.

  Args:
    parser: argparse.ArgumentParser, the parser to which to add the flag
    folder: str, the top-level folder in the bucket from which the export
      command will read. Should not contain any slashes. For example, 'dags'.
  """
  base.Argument(
      '--source',
      help="""\
      An optional relative path to a file or directory to be exported from the
      {}/ subdirectory in the environment's Cloud Storage bucket.
      """.format(folder)).AddToParser(parser)


def AddExportDestinationFlag(parser):
  """Adds a --destination flag for a storage export command to a parser.

  Args:
    parser: argparse.ArgumentParser, the parser to which to add the flag
  """
  base.Argument(
      '--destination',
      metavar='DESTINATION',
      required=True,
      help="""\
      The path to an existing local directory or a Cloud Storage
      bucket/directory into which to export files.
      """).AddToParser(parser)


def AddDeleteTargetPositional(parser, folder):
  base.Argument(
      'target',
      nargs='?',
      help="""\
      A relative path to a file or subdirectory to delete within the
      {folder} Cloud Storage subdirectory. If not specified, the entire contents
      of the {folder} subdirectory will be deleted.
      """.format(folder=folder)).AddToParser(parser)


def _IsValidEnvVarName(name):
  """Validates that a user-provided arg is a valid environment variable name.

  Intended to be used as an argparse validator.

  Args:
    name: str, the environment variable name to validate

  Returns:
    bool, True if and only if the name is valid
  """
  return re.match('^[a-zA-Z_][a-zA-Z0-9_]*$', name) is not None


ENV_VAR_NAME_FORMAT_VALIDATOR = arg_parsers.CustomFunctionValidator(
    _IsValidEnvVarName, _ENV_VAR_NAME_ERROR)
CREATE_ENV_VARS_FLAG = base.Argument(
    '--env-variables',
    metavar='NAME=VALUE',
    type=arg_parsers.ArgDict(
        key_type=ENV_VAR_NAME_FORMAT_VALIDATOR, value_type=str),
    action=arg_parsers.UpdateAction,
    help='A comma-delimited list of environment variable `NAME=VALUE` '
    'pairs to provide to the Airflow scheduler, worker, and webserver '
    'processes. NAME may contain upper and lowercase letters, digits, '
    'and underscores, but they may not begin with a digit. '
    'To include commas as part of a `VALUE`, see `{top_command} topic'
    ' escaping` for information about overriding the delimiter.')


def IsValidUserPort(val):
  """Validates that a user-provided arg is a valid user port.

  Intended to be used as an argparse validator.

  Args:
    val: str, a string specifying a TCP port number to be validated

  Returns:
    int, the provided port number

  Raises:
    ArgumentTypeError: if the provided port is not an integer outside the
        system port range
  """
  port = int(val)
  if 1024 <= port and port <= 65535:
    return port
  raise argparse.ArgumentTypeError('PORT must be in range [1024, 65535].')


def ValidateDiskSize(parameter_name, disk_size):
  """Validates that a disk size is a multiple of some number of GB.

  Args:
    parameter_name: parameter_name, the name of the parameter, formatted as it
      would be in help text (e.g., `--disk-size` or 'DISK_SIZE')
    disk_size: int, the disk size in bytes, or None for default value

  Raises:
    exceptions.InvalidArgumentException: the disk size was invalid
  """
  gb_mask = (1 << 30) - 1
  if disk_size and disk_size & gb_mask:
    raise exceptions.InvalidArgumentException(
        parameter_name, 'Must be an integer quantity of GB.')


def _AddPartialDictUpdateFlagsToGroup(update_type_group,
                                      clear_flag,
                                      remove_flag,
                                      update_flag,
                                      group_help_text=None):
  """Adds flags related to a partial update of arg represented by a dictionary.

  Args:
    update_type_group: argument group, the group to which flags should be added.
    clear_flag: flag, the flag to clear dictionary.
    remove_flag: flag, the flag to remove values from dictionary.
    update_flag: flag, the flag to add or update values in dictionary.
    group_help_text: (optional) str, the help info to apply to the created
      argument group. If not provided, then no help text will be applied to
      group.
  """
  group = update_type_group.add_argument_group(help=group_help_text)
  remove_group = group.add_mutually_exclusive_group(
      help=GENERAL_REMOVAL_FLAG_GROUP_DESCRIPTION)
  clear_flag.AddToParser(remove_group)
  remove_flag.AddToParser(remove_group)
  update_flag.AddToParser(group)


def AddNodeCountUpdateFlagToGroup(update_type_group):
  """Adds flag related to setting node count.

  Args:
    update_type_group: argument group, the group to which flag should be added.
  """
  update_type_group.add_argument(
      '--node-count',
      metavar='NODE_COUNT',
      type=arg_parsers.BoundedInt(lower_bound=3),
      help='The new number of nodes running the environment. Must be >= 3.')


def AddIpAliasEnvironmentFlags(update_type_group, support_max_pods_per_node):
  """Adds flags related to IP aliasing to parser.

  IP alias flags are related to similar flags found within GKE SDK:
    /third_party/py/googlecloudsdk/command_lib/container/flags.py

  Args:
    update_type_group: argument group, the group to which flag should be added.
    support_max_pods_per_node: bool, if specifying maximum number of pods is
      supported.
  """
  group = update_type_group.add_group(help='IP Alias (VPC-native)')
  ENABLE_IP_ALIAS_FLAG.AddToParser(group)
  CLUSTER_IPV4_CIDR_FLAG.AddToParser(group)
  SERVICES_IPV4_CIDR_FLAG.AddToParser(group)
  CLUSTER_SECONDARY_RANGE_NAME_FLAG.AddToParser(group)
  SERVICES_SECONDARY_RANGE_NAME_FLAG.AddToParser(group)
  ENABLE_IP_MASQ_AGENT_FLAG.AddToParser(group)

  if support_max_pods_per_node:
    MAX_PODS_PER_NODE.AddToParser(group)


def AddPrivateIpEnvironmentFlags(update_type_group, release_track):
  """Adds flags related to private clusters to parser.

  Private cluster flags are related to similar flags found within GKE SDK:
    /third_party/py/googlecloudsdk/command_lib/container/flags.py

  Args:
    update_type_group: argument group, the group to which flag should be added.
    release_track: which release track messages should we use.
  """
  group = update_type_group.add_group(help='Private Clusters')
  ENABLE_PRIVATE_ENVIRONMENT_FLAG.AddToParser(group)
  ENABLE_PRIVATE_ENDPOINT_FLAG.AddToParser(group)
  MASTER_IPV4_CIDR_FLAG.AddToParser(group)
  WEB_SERVER_IPV4_CIDR_FLAG.AddToParser(group)
  CLOUD_SQL_IPV4_CIDR_FLAG.AddToParser(group)
  COMPOSER_NETWORK_IPV4_CIDR_FLAG.AddToParser(group)
  CONNECTION_SUBNETWORK_FLAG.AddToParser(group)
  if release_track == base.ReleaseTrack.GA:
    CONNECTION_TYPE_FLAG_GA.choice_arg.AddToParser(group)
  elif release_track == base.ReleaseTrack.BETA:
    CONNECTION_TYPE_FLAG_BETA.choice_arg.AddToParser(group)
  elif release_track == base.ReleaseTrack.ALPHA:
    CONNECTION_TYPE_FLAG_ALPHA.choice_arg.AddToParser(group)
  ENABLE_PRIVATELY_USED_PUBLIC_IPS_FLAG.AddToParser(group)


def AddPypiUpdateFlagsToGroup(update_type_group):
  """Adds flag related to setting Pypi updates.

  Args:
    update_type_group: argument group, the group to which flag should be added.
  """
  group = update_type_group.add_mutually_exclusive_group(
      PYPI_PACKAGES_FLAG_GROUP_DESCRIPTION)
  UPDATE_PYPI_FROM_FILE_FLAG.AddToParser(group)
  _AddPartialDictUpdateFlagsToGroup(group, CLEAR_PYPI_PACKAGES_FLAG,
                                    REMOVE_PYPI_PACKAGES_FLAG,
                                    UPDATE_PYPI_PACKAGE_FLAG)


def AddEnvVariableUpdateFlagsToGroup(update_type_group):
  """Adds flags related to updating environent variables.

  Args:
    update_type_group: argument group, the group to which flags should be added.
  """
  _AddPartialDictUpdateFlagsToGroup(update_type_group, CLEAR_ENV_VARIABLES_FLAG,
                                    REMOVE_ENV_VARIABLES_FLAG,
                                    UPDATE_ENV_VARIABLES_FLAG,
                                    ENV_VARIABLES_FLAG_GROUP_DESCRIPTION)


def AddAirflowConfigUpdateFlagsToGroup(update_type_group):
  """Adds flags related to updating Airflow configurations.

  Args:
    update_type_group: argument group, the group to which flags should be added.
  """
  _AddPartialDictUpdateFlagsToGroup(update_type_group,
                                    CLEAR_AIRFLOW_CONFIGS_FLAG,
                                    REMOVE_AIRFLOW_CONFIGS_FLAG,
                                    UPDATE_AIRFLOW_CONFIGS_FLAG,
                                    AIRFLOW_CONFIGS_FLAG_GROUP_DESCRIPTION)


def AddEnvUpgradeFlagsToGroup(update_type_group):
  """Adds flag group to perform in-place env upgrades.

  Args:
    update_type_group: argument group, the group to which flags should be added.
  """
  upgrade_group = update_type_group.add_argument_group(
      ENV_UPGRADE_GROUP_DESCRIPTION, mutex=True)
  UPDATE_AIRFLOW_VERSION_FLAG.AddToParser(upgrade_group)
  UPDATE_IMAGE_VERSION_FLAG.AddToParser(upgrade_group)


def AddLabelsUpdateFlagsToGroup(update_type_group):
  """Adds flags related to updating environment labels.

  Args:
    update_type_group: argument group, the group to which flags should be added.
  """
  labels_update_group = update_type_group.add_argument_group(
      LABELS_FLAG_GROUP_DESCRIPTION)
  labels_util.AddUpdateLabelsFlags(labels_update_group)


def AddScheduledSnapshotFlagsToGroup(update_type_group):
  """Adds flags related to scheduled snapshot.

  Args:
    update_type_group: argument group, the group to which flags should be added.
  """

  update_group = update_type_group.add_argument_group(
      SCHEDULED_SNAPSHOTS_UPDATE_GROUP_DESCRIPTION, mutex=True)
  DISABLE_SCHEDULED_SNAPSHOT_CREATION.AddToParser(update_group)

  scheduled_snapshots_params_group = update_group.add_argument_group(
      SCHEDULED_SNAPSHOTS_GROUP_DESCRIPTION)
  ENABLE_SCHEDULED_SNAPSHOT_CREATION.AddToParser(
      scheduled_snapshots_params_group)
  SNAPSHOT_LOCATION.AddToParser(scheduled_snapshots_params_group)
  SNAPSHOT_CREATION_SCHEDULE.AddToParser(scheduled_snapshots_params_group)
  SNAPSHOT_SCHEDULE_TIMEZONE.AddToParser(scheduled_snapshots_params_group)


def AddAutoscalingUpdateFlagsToGroup(update_type_group, release_track):
  """Adds flags related to updating autoscaling.

  Args:
    update_type_group: argument group, the group to which flags should be added.
    release_track: gcloud version to add flags to.
  """
  if release_track == base.ReleaseTrack.GA:
    ENVIRONMENT_SIZE_GA.choice_arg.AddToParser(update_type_group)
  elif release_track == base.ReleaseTrack.BETA:
    ENVIRONMENT_SIZE_BETA.choice_arg.AddToParser(update_type_group)
  elif release_track == base.ReleaseTrack.ALPHA:
    ENVIRONMENT_SIZE_ALPHA.choice_arg.AddToParser(update_type_group)
  update_group = update_type_group.add_argument_group(
      AUTOSCALING_FLAG_GROUP_DESCRIPTION)
  SCHEDULER_CPU.AddToParser(update_group)
  WORKER_CPU.AddToParser(update_group)
  WEB_SERVER_CPU.AddToParser(update_group)
  SCHEDULER_MEMORY.AddToParser(update_group)
  WORKER_MEMORY.AddToParser(update_group)
  WEB_SERVER_MEMORY.AddToParser(update_group)
  SCHEDULER_STORAGE.AddToParser(update_group)
  WORKER_STORAGE.AddToParser(update_group)
  WEB_SERVER_STORAGE.AddToParser(update_group)
  MIN_WORKERS.AddToParser(update_group)
  MAX_WORKERS.AddToParser(update_group)

  triggerer_params_group = update_group.add_argument_group(
      TRIGGERER_PARAMETERS_FLAG_GROUP_DESCRIPTION, mutex=True)
  triggerer_enabled_group = triggerer_params_group.add_argument_group(
      TRIGGERER_ENABLED_GROUP_DESCRIPTION)
  TRIGGERER_CPU.AddToParser(triggerer_enabled_group)
  TRIGGERER_COUNT.AddToParser(triggerer_enabled_group)
  TRIGGERER_MEMORY.AddToParser(triggerer_enabled_group)
  ENABLE_TRIGGERER.AddToParser(triggerer_enabled_group)
  DISABLE_TRIGGERER.AddToParser(triggerer_params_group)
  if release_track != base.ReleaseTrack.GA:
    dag_processor_params_group = update_group.add_argument_group(
        DAG_PROCESSOR_PARAMETERS_FLAG_GROUP_DESCRIPTION,
        hidden=True,
    )
    DAG_PROCESSOR_CPU.AddToParser(dag_processor_params_group)
    DAG_PROCESSOR_COUNT.AddToParser(dag_processor_params_group)
    DAG_PROCESSOR_MEMORY.AddToParser(dag_processor_params_group)
    DAG_PROCESSOR_STORAGE.AddToParser(dag_processor_params_group)

  # Note: this flag is available for patching of both Composer 1.*.* and 2.*.*
  # environments.
  NUM_SCHEDULERS.AddToParser(update_group)


def AddMasterAuthorizedNetworksUpdateFlagsToGroup(update_type_group):
  """Adds flag group for master authorized networks.

  Args:
    update_type_group: argument group, the group to which flags should be added.
  """
  update_group = update_type_group.add_argument_group(
      MASTER_AUTHORIZED_NETWORKS_GROUP_DESCRIPTION)
  MASTER_AUTHORIZED_NETWORKS_FLAG.AddToParser(update_group)
  ENABLE_MASTER_AUTHORIZED_NETWORKS_FLAG.AddToParser(update_group)
  DISABLE_MASTER_AUTHORIZED_NETWORKS_FLAG.AddToParser(update_group)


def AddMaintenanceWindowFlagsGroup(create_type_group):
  """Adds flag group for maintenance window.

  Args:
    create_type_group: argument group, the group to which flags should be added.
  """
  group = create_type_group.add_group(MAINTENANCE_WINDOW_FLAG_GROUP_DESCRIPTION)
  MAINTENANCE_WINDOW_START_FLAG.AddToParser(group)
  MAINTENANCE_WINDOW_END_FLAG.AddToParser(group)
  MAINTENANCE_WINDOW_RECURRENCE_FLAG.AddToParser(group)


def AddMaintenanceWindowFlagsUpdateGroup(update_type_group):
  """Adds flag group for maintenance window used for an update operation.

  Args:
    update_type_group: argument group, the group to which flags should be added.
  """

  update_group = update_type_group.add_argument_group(
      MAINTENANCE_WINDOW_FLAG_UPDATE_GROUP_DESCRIPTION, mutex=True)

  CLEAR_MAINTENANCE_WINDOW_FLAG.AddToParser(update_group)
  group = update_group.add_group(MAINTENANCE_WINDOW_FLAG_GROUP_DESCRIPTION)
  MAINTENANCE_WINDOW_START_FLAG.AddToParser(group)
  MAINTENANCE_WINDOW_END_FLAG.AddToParser(group)
  MAINTENANCE_WINDOW_RECURRENCE_FLAG.AddToParser(group)


def AddCloudDataLineageIntegrationUpdateFlagsToGroup(update_type_group):
  """Adds flag group for Cloud Data Lineage integration.

  Args:
    update_type_group: argument group, the group to which flags should be added.
  """
  update_group = update_type_group.add_argument_group(
      CLOUD_DATA_LINEAGE_INTEGRATION_GROUP_DESCRIPTION)

  update_enable_disable_group = update_group.add_argument_group(mutex=True)
  ENABLE_CLOUD_DATA_LINEAGE_INTEGRATION_FLAG.AddToParser(
      update_enable_disable_group)
  DISABLE_CLOUD_DATA_LINEAGE_INTEGRATION_FLAG.AddToParser(
      update_enable_disable_group)


def AddComposer3FlagsToGroup(update_type_group):
  """Adds Composer 3 flags to an update group.

  Args:
    update_type_group: argument group, the group to which flags should be added.
  """
  SUPPORT_WEB_SERVER_PLUGINS.AddToParser(update_type_group)

  private_builds_only_group = update_type_group.add_argument_group(
      mutex=True, hidden=True
  )
  ENABLE_PRIVATE_BUILDS_ONLY.AddToParser(private_builds_only_group)
  DISABLE_PRIVATE_BUILDS_ONLY.AddToParser(private_builds_only_group)

  vpc_connectivity_group = update_type_group.add_argument_group(
      hidden=True, mutex=True
  )
  NETWORK_ATTACHMENT.AddToParser(vpc_connectivity_group)
  DISABLE_VPC_CONNECTIVITY.AddToParser(vpc_connectivity_group)
  network_subnetwork_group = vpc_connectivity_group.add_group(
      help='Virtual Private Cloud networking'
  )
  NETWORK_FLAG.AddToParser(network_subnetwork_group)
  SUBNETWORK_FLAG.AddToParser(network_subnetwork_group)

  ENABLE_PRIVATE_ENVIRONMENT_UPDATE_FLAG.AddToParser(update_type_group)
  DISABLE_PRIVATE_ENVIRONMENT_UPDATE_FLAG.AddToParser(update_type_group)


def FallthroughToLocationProperty(location_refs, flag_name, failure_msg):
  """Provides a list containing composer/location if `location_refs` is empty.

  This intended to be used as a fallthrough for a plural Location resource arg.
  The built-in fallthrough for plural resource args doesn't play well with
  properties, as it will iterate over each character in the string and parse
  it as the resource type. This function will parse the entire property and
  return a singleton list if `location_refs` is empty.

  Args:
    location_refs: [core.resources.Resource], a possibly empty list of location
      resource references
    flag_name: str, if `location_refs` is empty, and the composer/location
      property is also missing, an error message will be reported that will
      advise the user to set this flag name
    failure_msg: str, an error message to accompany the advisory described in
      the docs for `flag_name`.

  Returns:
    [core.resources.Resource]: a non-empty list of location resourc references.
    If `location_refs` was non-empty, it will be the same list, otherwise it
    will be a singleton list containing the value of the [composer/location]
    property.

  Raises:
    exceptions.RequiredArgumentException: both the user-provided locations
        and property fallback were empty
  """
  if location_refs:
    return location_refs

  fallthrough_location = parsers.GetLocation(required=False)
  if fallthrough_location:
    return [parsers.ParseLocation(fallthrough_location)]
  else:
    raise exceptions.RequiredArgumentException(flag_name, failure_msg)


def ValidateIpRanges(ip_ranges):
  """Validates list of IP ranges.

  Raises exception when any of the given strings is not a valid IPv4
  or IPv6 network IP range.
  Args:
    ip_ranges: [string], list of IP ranges to validate
  """
  for ip_range in ip_ranges:
    if six.PY2:
      ip_range = ip_range.decode()
    try:
      ipaddress.ip_network(ip_range)
    except:
      raise command_util.InvalidUserInputError(
          'Invalid IP range: [{}].'.format(ip_range))
