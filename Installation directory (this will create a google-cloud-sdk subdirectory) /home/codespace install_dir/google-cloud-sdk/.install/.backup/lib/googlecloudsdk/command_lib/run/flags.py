# -*- coding: utf-8 -*- #
# Copyright 2018 Google LLC. All Rights Reserved.
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
"""Provides common arguments for the Run command surface."""

import enum
import os
import re

from apitools.base.py import exceptions as apitools_exceptions
from googlecloudsdk.api_lib.container import kubeconfig
from googlecloudsdk.api_lib.run import container_resource
from googlecloudsdk.api_lib.run import global_methods
from googlecloudsdk.api_lib.run import k8s_object
from googlecloudsdk.api_lib.run import revision
from googlecloudsdk.api_lib.run import service
from googlecloudsdk.api_lib.run import traffic
from googlecloudsdk.api_lib.services import enable_api
from googlecloudsdk.api_lib.services import exceptions as services_exceptions
from googlecloudsdk.calliope import actions
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.functions.v2.deploy import env_vars_util
from googlecloudsdk.command_lib.run import config_changes
from googlecloudsdk.command_lib.run import exceptions as serverless_exceptions
from googlecloudsdk.command_lib.run import platforms
from googlecloudsdk.command_lib.run import pretty_print
from googlecloudsdk.command_lib.run import resource_args
from googlecloudsdk.command_lib.run import secrets_mapping
from googlecloudsdk.command_lib.run import volumes
from googlecloudsdk.command_lib.util.args import labels_util
from googlecloudsdk.command_lib.util.args import map_util
from googlecloudsdk.command_lib.util.args import repeated
from googlecloudsdk.command_lib.util.concepts import concept_parsers
from googlecloudsdk.core import config
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core.console import console_io
from googlecloudsdk.core.util import encoding
from googlecloudsdk.core.util import files

SERVICE_MESH_FLAG = base.Argument(
    '--mesh',
    hidden=True,
    help='Enables Service Mesh configuration using the specified mesh name.',
)

_VISIBILITY_MODES = {
    'internal': 'Visible only within the cluster.',
    'external': 'Visible from outside the cluster.',
}

_INGRESS_MODES = {
    'all': 'Inbound requests from all sources are allowed.',
    'internal': """\
        For Cloud Run (fully managed), only inbound requests from VPC networks
        in the same project or VPC Service Controls perimeter, as well as
        Pub/Sub subscriptions and Eventarc events in the same project or VPC
        Service Controls perimeter are allowed. All other requests are rejected.
        See https://cloud.google.com/run/docs/securing/ingress for full details
        on the definition of internal traffic for Cloud Run (fully managed). For
        Cloud Run for Anthos, only inbound requests from the same cluster are
        allowed.
        """,
    'internal-and-cloud-load-balancing': """\
        Only supported for Cloud Run (fully managed). Only inbound requests
        from Google Cloud Load Balancing or a traffic source allowed by the
        internal option are allowed.
        """,
}

_SANDBOX_CHOICES = {
    'gen1': 'Run the application in a first generation execution environment.',
    'gen2': 'Run the application in a second generation execution environment.',
}

_DEFAULT_KUBECONFIG_PATH = '~/.kube/config'

_POST_CMEK_KEY_REVOCATION_ACTION_TYPE_CHOICES = {
    'shut-down': """\
        No new instances will be started and the existing instances will be shut
        down after CMEK key revocation.
        """,
    'prevent-new': (
        'No new instances will be started after CMEK key revocation.'
    ),
}

_CONTAINER_NAME_TYPE = arg_parsers.RegexpValidator(
    '[a-z0-9]([a-z0-9-.]{0,61}[a-z0-9])?',
    'must conform to RFC 1123: only lowercase, digits, hyphens, and'
    ' periods are allowed, must begin and end with letter or digit, and'
    ' less than 64 characters.',
)


def _StripKeys(d):
  return {k.strip(): v for k, v in d.items()}


def _MapLStrip(seq):
  return [elem.lstrip() for elem in seq]


class KubeconfigError(exceptions.Error):
  pass


class Product(enum.Enum):
  RUN = 'Run'
  EVENTS = 'Events'
  STACKS = 'Stacks'


def AddImageArg(parser, required=True, image='gcr.io/cloudrun/hello:latest'):
  """Add an image resource arg."""
  parser.add_argument(
      '--image',
      required=required,
      help='Name of the container image to deploy (e.g. `{image}`).'.format(
          image=image
      ),
  )


def ImageArg(required=True, image='gcr.io/cloudrun/hello:latest'):
  """Image resource arg."""
  return base.Argument(
      '--image',
      required=required,
      help='Name of the container image to deploy (e.g. `{image}`).'.format(
          image=image
      ),
  )


_ARG_GROUP_HELP_TEXT = (
    'Only applicable if connecting to {platform_desc}. '
    'Specify {platform} to use:'
)


def _GetOrAddArgGroup(parser, help_text):
  """Create a new arg group or return existing group with given help text."""
  for arg in parser.arguments:
    if arg.is_group and arg.help == help_text:
      return arg
  return parser.add_argument_group(help_text)


def GetManagedArgGroup(parser):
  """Get an arg group for managed CR-only flags."""
  return _GetOrAddArgGroup(
      parser,
      _ARG_GROUP_HELP_TEXT.format(
          platform='`--platform={}`'.format(platforms.PLATFORM_MANAGED),
          platform_desc=platforms.PLATFORM_SHORT_DESCRIPTIONS[
              platforms.PLATFORM_MANAGED
          ],
      ),
  )


def GetGkeArgGroup(parser):
  """Get an arg group for CRoGKE-only flags."""
  return _GetOrAddArgGroup(
      parser,
      _ARG_GROUP_HELP_TEXT.format(
          platform='`--platform={}`'.format(platforms.PLATFORM_GKE),
          platform_desc=platforms.PLATFORM_SHORT_DESCRIPTIONS[
              platforms.PLATFORM_GKE
          ],
      ),
  )


def GetKubernetesArgGroup(parser):
  """Get an arg group for --platform=kubernetes only flags."""
  return _GetOrAddArgGroup(
      parser,
      _ARG_GROUP_HELP_TEXT.format(
          platform='`--platform={}`'.format(platforms.PLATFORM_KUBERNETES),
          platform_desc=platforms.PLATFORM_SHORT_DESCRIPTIONS[
              platforms.PLATFORM_KUBERNETES
          ],
      ),
  )


def GetClusterArgGroup(parser):
  """Get an arg group for any generic cluster flags."""
  return _GetOrAddArgGroup(
      parser,
      _ARG_GROUP_HELP_TEXT.format(
          platform='`--platform={}` or `--platform={}`'.format(
              platforms.PLATFORM_GKE, platforms.PLATFORM_KUBERNETES
          ),
          platform_desc='{} or {}'.format(
              platforms.PLATFORM_SHORT_DESCRIPTIONS[platforms.PLATFORM_GKE],
              platforms.PLATFORM_SHORT_DESCRIPTIONS[
                  platforms.PLATFORM_KUBERNETES
              ],
          ),
      ),
  )


def AddPlatformAndLocationFlags(parser, managed_only=False, anthos_only=False):
  """Adds flags used to determine the platform and the location of resource."""
  assert not (managed_only and anthos_only)
  AddPlatformArg(parser, managed_only, anthos_only)

  if managed_only:
    AddRegionArg(parser)
    return None

  # When multiple platforms are supported, add a arg group that covers the
  # various ways to specify region/zone/cluster.
  platform_helpers_group = parser.add_mutually_exclusive_group(
      help='Arguments to locate resources, depending on the platform used.'
  )

  if not anthos_only:
    # Add --region flag
    managed_group = GetManagedArgGroup(platform_helpers_group)
    AddRegionArg(managed_group)

  # Add --cluster and --cluster-location (plus properties)
  gke_group = GetGkeArgGroup(platform_helpers_group)
  concept_parsers.ConceptParser(
      [resource_args.CLUSTER_PRESENTATION]
  ).AddToParser(gke_group)

  # Add --kubeconfig and --context
  kubernetes_group = GetKubernetesArgGroup(platform_helpers_group)
  AddKubeconfigFlags(kubernetes_group)


def AddAllowUnauthenticatedFlag(parser):
  """Add the --allow-unauthenticated flag."""
  parser.add_argument(
      '--allow-unauthenticated',
      action=arg_parsers.StoreTrueFalseAction,
      help=(
          'Whether to enable allowing unauthenticated access to the service. '
          'This may take a few moments to take effect.'
      ),
  )


def AddAsyncFlag(parser, default_async_for_cluster=False, is_job=False):
  """Add an async flag."""
  help_text = """\
    Return immediately, without waiting for the operation in progress to
    complete."""
  if is_job:
    help_text += ' Defaults to --no-async.'
  else:
    help_text += """ Defaults to --no-async for Cloud Run (fully managed) and --async
    for Cloud Run for Anthos."""
  if default_async_for_cluster:
    modified_async_flag = base.Argument(
        '--async',
        action=arg_parsers.StoreTrueFalseAction,
        dest='async_',
        help=help_text,
    )
    modified_async_flag.AddToParser(parser)
  else:
    base.ASYNC_FLAG.AddToParser(parser)


def AddEndpointVisibilityEnum(parser):
  """Add the --connectivity=[external|internal] flag."""
  parser.add_argument(
      '--connectivity',
      choices=_VISIBILITY_MODES,
      help=(
          "Defaults to 'external'. If 'external', the service can be "
          'invoked through the internet, in addition to through the cluster '
          'network.'
      ),
      action=actions.DeprecationAction(
          '--connectivity',
          warn=(
              'The {flag_name} flag is deprecated but will continue to be '
              'supported. Prefer to use the --ingress flag instead.'
          ),
      ),
  )


def AddIngressFlag(parser):
  """Adds the --ingress flag."""
  parser.add_argument(
      '--ingress',
      choices=_INGRESS_MODES,
      help=(
          'Set the ingress traffic sources allowed to call the service. For '
          'Cloud Run (fully managed) the `--[no-]allow-unauthenticated` flag '
          'separately controls the identities allowed to call the service.'
      ),
      default='all',
  )


def AddServiceFlag(parser):
  """Add a service resource flag."""
  parser.add_argument(
      '--service',
      required=False,
      help='Limit matched revisions to the given service.',
  )


def AddJobFlag(parser):
  """Add a job resource flag."""
  parser.add_argument(
      '--job', required=False, help='Limit matched resources to the given job.'
  )


def AddRegionArg(parser):
  """Add a region arg."""
  parser.add_argument(
      '--region',
      help=(
          'Region in which the resource can be found. '
          'Alternatively, set the property [run/region].'
      ),
  )


def AddFunctionArg(parser):
  """Add a function resource arg."""
  parser.add_argument(
      '--function',
      hidden=True,
      nargs='?',
      const=True,
      help="""\
      Specifies that the deployed object is a function. If a value is
      provided, that value is used as the entrypoint.
      """,
  )


def AddNoTrafficFlag(parser):
  """Add flag to deploy a revision with no traffic."""
  parser.add_argument(
      '--no-traffic',
      default=False,
      action='store_true',
      help=(
          'True to avoid sending traffic to the revision being deployed.'
          ' Setting this flag assigns any traffic assigned to the LATEST'
          ' revision to the specific revision bound to LATEST before the'
          ' deployment. The effect is that the revision being deployed will not'
          ' receive traffic.\n\nAfter a deployment with this flag the LATEST'
          ' revision will not receive traffic on future deployments. To restore'
          ' sending traffic to the LATEST revision by default, run the `gcloud'
          ' run services update-traffic` command with `--to-latest`.'
      ),
  )


def AddCpuThrottlingFlag(parser):
  """Adds flag for deploying a Cloud Run service with CPU throttling."""
  parser.add_argument(
      '--cpu-throttling',
      action=arg_parsers.StoreTrueFalseAction,
      help=(
          'Whether to throttle the CPU when the container is not actively '
          'serving requests.'
      ),
  )


def AddStartupCpuBoostFlag(parser):
  """Adds flag for deploying a Cloud Run service with startup CPU boost."""
  parser.add_argument(
      '--cpu-boost',
      action=arg_parsers.StoreTrueFalseAction,
      help=(
          'Whether to allocate extra CPU to containers on startup to reduce the'
          ' perceived latency of a cold start request. Enabled by default when'
          ' unspecified on new services.'
      ),
  )


def AddTokenFlag(parser):
  parser.add_argument(
      '--token',
      help=(
          'The specific identity token to add to all requests of the '
          'proxied service. If not specified, the identity token of '
          'the currently active authenticated account will be used '
          '(e.g. gcloud auth print-identity-token).'
      ),
  )


_DEFAULT_DEPLOY_TAG_HELP = """Traffic tag to assign to the newly
created revision."""


def AddDeployTagFlag(parser, help_text=_DEFAULT_DEPLOY_TAG_HELP):
  """Add flag to specify a tag for the new revision."""
  parser.add_argument('--tag', help=help_text)


def AddTrafficTagsFlags(parser):
  """Add flags for updating traffic tags for a service."""
  AddMapFlagsNoFile(
      parser,
      group_help=(
          'Specify traffic tags. Traffic tags can be '
          'assigned to a revision by name or to the '
          'latest ready revision. Assigning a tag to a '
          'revision generates a URL prefixed with the '
          'tag that allows addressing that revision '
          'directly, regardless of the percent traffic '
          'specified. Keys are tags. Values are revision names or '
          '"LATEST" for the latest ready revision. For example, '
          '--set-tags=candidate=LATEST,current='
          'myservice-v1 assigns the tag "candidate" '
          'to the latest ready revision and the tag'
          ' "current" to the revision with name '
          '"myservice-v1" and clears any existing tags. '
          'Changing tags does not '
          'affect the traffic percentage assigned to '
          'revisions. When using a tags flag and '
          'one or more of --to-latest and --to-revisions in the same '
          'command, the tags change occurs first then the traffic '
          'percentage change occurs.'
      ),
      flag_name='tags',
      key_metavar='TAG',
      value_metavar='REVISION',
  )


def AddUpdateTrafficFlags(parser):
  """Add flags for updating traffic assignments for a service."""

  @staticmethod
  def TrafficTargetKey(key):
    return key

  @staticmethod
  def TrafficPercentageValue(value):
    """Type validation for traffic percentage flag values."""
    try:
      result = int(value)
    except (TypeError, ValueError):
      raise serverless_exceptions.ArgumentError(
          'Traffic percentage value %s is not an integer.' % value
      )

    if result < 0 or result > 100:
      raise serverless_exceptions.ArgumentError(
          'Traffic percentage value %s is not between 0 and 100.' % value
      )
    return result

  group = parser.add_mutually_exclusive_group()

  group.add_argument(
      '--to-revisions',
      metavar='REVISION-NAME=PERCENTAGE',
      action=arg_parsers.UpdateAction,
      type=arg_parsers.ArgDict(
          key_type=TrafficTargetKey.__func__,
          value_type=TrafficPercentageValue.__func__,
      ),
      help=(
          'Comma separated list of traffic assignments in the form'
          ' REVISION-NAME=PERCENTAGE. REVISION-NAME must be the name for a'
          " revision for the service as returned by 'gcloud beta run list"
          " revisions'. PERCENTAGE must be an integer percentage between 0 and"
          ' 100 inclusive.  Ex service-nw9hs=10,service-nw9hs=20 Up to 100'
          ' percent of traffic may be assigned. If 100 percent of traffic is'
          ' assigned,  the Service traffic is updated as specified. If under'
          ' 100 percent of traffic is assigned, the Service traffic is updated'
          ' as specified for revisions with assignments and traffic is scaled'
          ' up or down down proportionally as needed for revision that are'
          ' currently serving traffic but that do not have new assignments. For'
          ' example assume revision-1 is serving 40 percent of traffic and'
          ' revision-2 is serving 60 percent. If revision-1 is assigned 45'
          ' percent of traffic and no assignment is made for revision-2, the'
          ' service is updated with revsion-1 assigned 45 percent of traffic'
          ' and revision-2 scaled down to 55 percent. You can use "LATEST" as a'
          ' special revision name to always put the given percentage of traffic'
          ' on the latest ready revision.'
      ),
  )

  group.add_argument(
      '--to-tags',
      metavar='TAG=PERCENTAGE',
      action=arg_parsers.UpdateAction,
      type=arg_parsers.ArgDict(
          key_type=TrafficTargetKey.__func__,
          value_type=TrafficPercentageValue.__func__,
      ),
      help=(
          'Comma separated list of traffic assignments in the form'
          ' TAG=PERCENTAGE. TAG must match a traffic tag on a revision of the'
          ' service. It may match a previously-set tag, or one assigned using'
          ' the `--set-tags` or `--update-tags` flags on this command.'
          ' PERCENTAGE must be an integer percentage between 0 and 100'
          ' inclusive. Up to 100 percent of traffic may be assigned. If 100'
          ' percent of traffic is assigned, the service traffic is updated as'
          ' specified. If under 100 percent of traffic is assigned, the service'
          ' traffic is updated as specified to the given tags, and other'
          ' traffic is scaled up or down proportionally. For example, assume'
          ' the revision tagged `next` is serving 40 percent of traffic and the'
          ' revision tagged `current` is serving 60 percent. If `next` is'
          ' assigned 45 percent of traffic and no assignment is made for'
          ' `current`, the service is updated with `next` assigned 45 percent'
          ' of traffic and `current` scaled down to 55 percent. '
      ),
  )

  group.add_argument(
      '--to-latest',
      default=False,
      action='store_true',
      help=(
          "True to assign 100 percent of traffic to the 'latest' "
          'revision of this service. Note that when a new revision is '
          "created, it will become the 'latest' and traffic will be "
          'directed to it. Defaults to False. Synonymous with '
          "'--to-revisions=LATEST=100'."
      ),
  )


def AddSetCloudSQLFlag(parser):
  """Add only the --set-cloudsql-instances flag."""
  parser.add_argument(
      '--set-cloudsql-instances',
      type=arg_parsers.ArgList(),
      metavar='CLOUDSQL-INSTANCES',
      help="""You can specify a name of a Cloud SQL instance if it's in the same
      project and region as your Cloud Run resource; otherwise specify
      <project>:<region>:<instance> for the instance.""",
  )


def AddCloudSQLFlags(parser):
  """Add flags for setting CloudSQL stuff."""
  repeated.AddPrimitiveArgs(
      parser,
      'Service',
      'cloudsql-instances',
      'Cloud SQL instances',
      auto_group_help=False,
      additional_help="""\
      These flags modify the Cloud SQL instances this Service connects to.
      You can specify a name of a Cloud SQL instance if it's in the same
      project and region as your Cloud Run service; otherwise specify
      <project>:<region>:<instance> for the instance.""",
  )


def AddVolumesFlags(parser, release_track):
  """Add flags for adding and removing volumes."""
  group = parser.add_group()
  group.add_argument(
      '--add-volume',
      type=arg_parsers.ArgDict(required_keys=['name', 'type']),
      action='append',
      metavar='KEY=VALUE',
      help=(
          'Adds a volume to the Cloud Run resource. To add more than one '
          'volume, specify this flag multiple times.'
          ' Volumes must have a `name` and `type` key. '
          'Only certain values are supported for `type`. Depending on the '
          'provided type, other keys will be required. The following types '
          'are supported with the specified additional keys:\n\n'
          + volumes.volume_help(release_track)
      ),
  )
  group.add_argument(
      '--remove-volume',
      type=arg_parsers.ArgList(),
      action=arg_parsers.UpdateAction,
      metavar='VOLUME',
      help='Removes volumes from the Cloud Run resource.',
  )
  group.add_argument(
      '--clear-volumes',
      action='store_true',
      help=(
          'Remove all existing volumes from the Cloud Run resource, including'
          ' volumes mounted as secrets'
      ),
  )


def AddVolumeMountFlag():
  """Returns container flag for adding a volume mount."""

  def _LimitMountKeys(key):
    if key not in {'volume', 'mount-path'}:
      raise serverless_exceptions.ArgumentError(
          'Key [{}] not recognized for volume mount. Only keys "volume" and'
          ' "mount-path" are supported'.format(key)
      )
    return key

  return base.Argument(
      '--add-volume-mount',
      action='append',
      type=arg_parsers.ArgDict(
          required_keys=['volume', 'mount-path'], key_type=_LimitMountKeys
      ),
      metavar='volume=NAME,mount-path=MOUNT_PATH',
      help=(
          'Adds a mount to the current container. Must contain the keys'
          ' `volume=NAME` and `mount-path=/PATH` where NAME is the name of a'
          ' volume on this resource and PATH is the path within the'
          " container's filesystem to mount this volume."
      ),
  )


def RemoveVolumeMountFlag():
  """Returns container flag for removing a volume mount."""
  return base.Argument(
      '--remove-volume-mount',
      action=arg_parsers.UpdateAction,
      type=arg_parsers.ArgList(),
      metavar='MOUNT_PATH',
      help=(
          'Removes the volume mounted at the specified path from the current'
          ' container.'
      ),
  )


def ClearVolumeMountsFlag():
  """Returns container flag for clearing volume mounts."""
  return base.Argument(
      '--clear-volume-mounts',
      action='store_true',
      help='Remove all existing mounts from the current container.',
  )


def MapFlagsNoFile(
    flag_name,
    group_help='',
    long_name=None,
    key_type=None,
    value_type=None,
    key_metavar='KEY',
    value_metavar='VALUE',
):
  """Create an argument group like map_util.AddUpdateMapFlags but without the file one.

  Args:
    flag_name: The name for the property to be used in flag names
    group_help: Help text for the group of flags
    long_name: The name for the property to be used in help text
    key_type: A function to apply to map keys.
    value_type: A function to apply to map values.
    key_metavar: Metavariable to list for the key.
    value_metavar: Metavariable to list for the value.

  Returns:
    A mutually exclusive group for the map flags.
  """
  if not long_name:
    long_name = flag_name

  group = base.ArgumentGroup(mutex=True, help=group_help)
  update_remove_group = base.ArgumentGroup(
      help=(
          'Only --update-{0} and --remove-{0} can be used together. If both '
          'are specified, --remove-{0} will be applied first.'
      ).format(flag_name)
  )
  update_remove_group.AddArgument(
      map_util.MapUpdateFlag(
          flag_name,
          long_name,
          key_type=key_type,
          value_type=value_type,
          key_metavar=key_metavar,
          value_metavar=value_metavar,
      )
  )
  update_remove_group.AddArgument(
      map_util.MapRemoveFlag(
          flag_name,
          long_name,
          key_type=key_type,
          key_metavar=key_metavar,
      )
  )
  group.AddArgument(update_remove_group)
  group.AddArgument(map_util.MapClearFlag(flag_name, long_name))
  group.AddArgument(
      map_util.MapSetFlag(
          flag_name,
          long_name,
          key_type=key_type,
          value_type=value_type,
          key_metavar=key_metavar,
          value_metavar=value_metavar,
      )
  )
  return group


def AddMapFlagsNoFile(
    parser,
    flag_name,
    group_help='',
    long_name=None,
    key_type=None,
    value_type=None,
    key_metavar='KEY',
    value_metavar='VALUE',
):
  """Add flags like map_util.AddUpdateMapFlags but without the file one.

  Args:
    parser: The argument parser
    flag_name: The name for the property to be used in flag names
    group_help: Help text for the group of flags
    long_name: The name for the property to be used in help text
    key_type: A function to apply to map keys.
    value_type: A function to apply to map values.
    key_metavar: Metavariable to list for the key.
    value_metavar: Metavariable to list for the value.

  Returns:
    A mutually exclusive group for the map flags.
  """
  return MapFlagsNoFile(
      flag_name,
      group_help,
      long_name,
      key_type,
      value_type,
      key_metavar=key_metavar,
      value_metavar=value_metavar,
  ).AddToParser(parser)


def AddSetEnvVarsFlag(parser):
  """Add only the --set-env-vars flag."""
  parser.add_argument(
      '--set-env-vars',
      metavar='KEY=VALUE',
      action=arg_parsers.UpdateAction,
      type=arg_parsers.ArgDict(
          key_type=env_vars_util.EnvVarKeyType,
          value_type=env_vars_util.EnvVarValueType,
      ),
      help='List of key-value pairs to set as environment variables.',
  )


def MutexEnvVarsFlags():
  """Return argument group for setting, updating and deleting env vars."""
  group = MapFlagsNoFile(
      'env-vars',
      long_name='environment variables',
      key_type=env_vars_util.EnvVarKeyType,
      value_type=env_vars_util.EnvVarValueType,
  )
  group.AddArgument(
      base.Argument(
          '--env-vars-file',
          metavar='FILE_PATH',
          type=map_util.ArgDictFile(
              key_type=env_vars_util.EnvVarKeyType,
              value_type=env_vars_util.EnvVarValueType,
          ),
          help="""Path to a local YAML file with definitions for all environment
            variables. All existing environment variables will be removed before
            the new environment variables are added. Example YAML content:

              ```
              KEY_1: "value1"
              KEY_2: "value 2"
              ```
            """,
      )
  )
  return group


def AddMutexEnvVarsFlags(parser):
  """Add flags for setting, updating and deleting env vars."""
  return MutexEnvVarsFlags().AddToParser(parser)


def AddMutexEnvVarsFlagsForCreate(parser):
  """Add flags for setting env vars."""
  group = parser.add_mutually_exclusive_group()
  AddSetEnvVarsFlag(group)
  group.add_argument(
      '--env-vars-file',
      metavar='FILE_PATH',
      type=map_util.ArgDictFile(
          key_type=env_vars_util.EnvVarKeyType,
          value_type=env_vars_util.EnvVarValueType,
      ),
      help="""Path to a local YAML file with definitions for all environment
            variables. Example YAML content:

              ```
              KEY_1: "value1"
              KEY_2: "value 2"
              ```
            """,
  )


def AddOverrideEnvVarsFlag(parser):
  """Add the --update-env-vars flag."""
  parser.add_argument(
      '--update-env-vars',
      metavar='KEY=VALUE',
      action=arg_parsers.UpdateAction,
      type=arg_parsers.ArgDict(
          key_type=env_vars_util.EnvVarKeyType,
          value_type=env_vars_util.EnvVarValueType,
      ),
      help=(
          'List of key-value pairs to set as environment variables overrides'
          ' for an execution of a job. If provided, an execution will be'
          ' created with the merge result of the input values and the existing'
          ' environment variables. New value overrides existing value if they'
          ' have the same key. If not provided, existing environment variables'
          ' are used.'
      ),
  )


def MemoryFlag():
  return base.Argument('--memory', help='Set a memory limit. Ex: 1024Mi, 4Gi.')


def AddMemoryFlag(parser):
  MemoryFlag().AddToParser(parser)


def CpuFlag(managed_only=False):
  """Create the --cpu flag."""
  help_msg = (
      'Set a CPU limit in Kubernetes cpu units.\n\n'
      'Cloud Run (fully managed) supports values 1, 2 and 4.'
      '  For Cloud Run (fully managed), 4 cpus also requires a minimum '
      '2Gi `--memory` value.  Examples 2, 2.0, 2000m'
  )
  if not managed_only:
    help_msg += (
        '\n\nCloud Run for Anthos and Knative-compatible Kubernetes '
        'clusters support fractional values.  Examples .5, 500m, 2'
    )
  return base.Argument('--cpu', help=help_msg)


def AddCpuFlag(parser, managed_only=False):
  """Add the --cpu flag."""
  CpuFlag(managed_only=managed_only).AddToParser(parser)


def AddGpuTypeFlag(parser):
  """Add the --gpu-type flag."""
  parser.add_argument(
      '--gpu-type',
      metavar='GPU_TYPE',
      hidden=True,
      help='The GPU type to use.',
  )


def GpuFlag():
  """Add the --gpu flag."""
  return base.Argument(
      '--gpu',
      metavar='GPU',
      hidden=True,
      help=(
          'Cloud Run supports values 0 or 1.'
          '  1 gpu also requires a minimum 4 `--cpu` value'
          '  1 gpu also requires a minimum 8Gi `--memory` value.'
      ),
  )


def _ConcurrencyValue(value):
  """Returns True if value is an int > 0 or 'default'."""
  try:
    return value == 'default' or int(value) > 0
  except ValueError:
    return False


def AddConcurrencyFlag(parser):
  parser.add_argument(
      '--concurrency',
      type=arg_parsers.CustomFunctionValidator(
          _ConcurrencyValue, 'must be an integer greater than 0 or "default".'
      ),
      help=(
          'Set the maximum number of concurrent requests allowed per '
          'container instance. Leave concurrency unspecified or provide the '
          "special value 'default' to receive the server default value."
      ),
  )


def AddTimeoutFlag(parser):
  parser.add_argument(
      '--timeout',
      type=arg_parsers.Duration(lower_bound='1s'),
      help=(
          'Set the maximum request execution time (timeout). It is specified as'
          ' a duration; for example, "10m5s" is ten minutes, and five seconds.'
          ' If you don\'t specify a unit, seconds is assumed. For example, "10"'
          ' is 10 seconds.'
      ),
  )


def AddServiceAccountFlag(parser, managed_only=False):
  """Add the --service-account flag."""
  help_text = (
      'Service account associated with the revision of the service. '
      'The service account represents the identity of '
      'the running revision, and determines what permissions the revision has. '
  )
  if managed_only:
    help_text += 'This is the email address of an IAM service account.'
  else:
    help_text += (
        'For the {} platform, this is the email address of an IAM service '
        'account. For the Kubernetes-based platforms ({}, {}), this is the '
        'name of a Kubernetes service account in the same namespace as the '
        'service. If not provided, the revision will use the default service '
        'account of the project, or default Kubernetes namespace service '
        'account respectively.'.format(
            platforms.PLATFORM_MANAGED,
            platforms.PLATFORM_GKE,
            platforms.PLATFORM_KUBERNETES,
        )
    )

  parser.add_argument('--service-account', help=help_text)


def AddPlatformArg(parser, managed_only=False, anthos_only=False):
  """Add a platform arg."""
  assert not (managed_only and anthos_only)
  choices = platforms.PLATFORMS
  if managed_only:
    choices = platforms.PLATFORMS_MANAGED_ONLY
  if anthos_only:
    choices = platforms.PLATFORMS_ANTHOS_ONLY
  parser.add_argument(
      '--platform',
      choices=choices,
      action=actions.StoreProperty(properties.VALUES.run.platform),
      default=platforms.PLATFORM_MANAGED,
      help=(
          'Target platform for running commands. '
          'Alternatively, set the property [run/platform]. '
      ),
  )


def AddKubeconfigFlags(parser):
  parser.add_argument(
      '--kubeconfig',
      help=(
          'The absolute path to your kubectl config file. If not specified, '
          'the colon- or semicolon-delimited list of paths specified by '
          '$KUBECONFIG will be used. If $KUBECONFIG is unset, this defaults to '
          '`{}`.'.format(_DEFAULT_KUBECONFIG_PATH)
      ),
  )
  parser.add_argument(
      '--context',
      help=(
          'The name of the context in your kubectl config file to use for '
          'connecting.'
      ),
  )


def AddRevisionSuffixArg(parser):
  parser.add_argument(
      '--revision-suffix',
      help=(
          'Specify the suffix of the revision name. Revision names always '
          'start with the service name automatically. For example, specifying '
          "[--revision-suffix=v1] for a service named 'helloworld', "
          "would lead to a revision named 'helloworld-v1'."
      ),
  )


def AddSandboxArg(parser, hidden=False):
  parser.add_argument(
      '--execution-environment',
      choices=_SANDBOX_CHOICES,
      hidden=hidden,
      help='Selects the execution environment where the application will run.',
  )


def AddVpcConnectorArg(parser):
  parser.add_argument(
      '--vpc-connector',
      help='Set a VPC connector for this resource.',
  )


def AddVpcConnectorArgs(parser):
  AddVpcConnectorArg(parser)
  parser.add_argument(
      '--clear-vpc-connector',
      action='store_true',
      help='Remove the VPC connector for this resource.',
  )


def AddEgressSettingsFlag(parser):
  """Adds a flag for configuring VPC egress for fully-managed."""
  parser.add_argument(
      '--vpc-egress',
      help=(
          'Specify which of the outbound traffic to send through Direct VPC'
          ' egress or the VPC connector for this resource. This resource must'
          ' have Direct VPC egress enabled or a VPC connector to set this flag.'
      ),
      choices={
          container_resource.EGRESS_SETTINGS_PRIVATE_RANGES_ONLY: (
              'Default option. Sends outbound traffic to private IP addresses'
              ' (RFC 1918 and Private Google Access IPs) through Direct VPC'
              ' egress or the VPC connector.\n\nTraffic to other Cloud Run'
              ' services might require additional configuration. See'
              ' https://cloud.google.com/run/docs/securing/private-networking#send_requests_to_other_services_and_services'
              ' for more information.'
          ),
          container_resource.EGRESS_SETTINGS_ALL_TRAFFIC: (
              'Sends all outbound traffic through Direct VPC egress or the VPC'
              ' connector.'
          ),
          container_resource.EGRESS_SETTINGS_ALL: (
              '(DEPRECATED) Sends all outbound traffic through Direct VPC'
              ' egress or the VPC connector. Provides the same functionality'
              " as '{all_traffic}'. Prefer to use '{all_traffic}'"
              ' instead.'.format(
                  all_traffic=container_resource.EGRESS_SETTINGS_ALL_TRAFFIC
              )
          ),
      },
  )


def SetSecretsFlag():
  return base.Argument(
      '--set-secrets',
      metavar='KEY=SECRET_NAME:SECRET_VERSION',
      action=arg_parsers.UpdateAction,
      type=arg_parsers.ArgDict(),
      help=(
          'Specify secrets to provide as environment variables. '
          "For example: '--set-secrets=ENV=mysecret:latest,"
          "OTHER_ENV=othersecret:1' "
          'will create an environment variable named ENV whose value is the '
          "latest version of secret 'mysecret' and an environment variable "
          "OTHER_ENV whose value is version of 1 of secret 'othersecret'."
      ),
  )


def AddSetSecretsFlag(parser):
  SetSecretsFlag().AddToParser(parser)


def SecretsFlags():
  """Creates flags for creating, updating, and deleting secrets."""
  return MapFlagsNoFile(
      group_help=(
          'Specify secrets to mount or provide as environment '
          "variables. Keys starting with a forward slash '/' are mount "
          'paths. All other keys correspond to environment variables. '
          'Values should be in the form SECRET_NAME:SECRET_VERSION. '
          'For example: '
          "'--update-secrets=/secrets/api/key=mysecret:latest,"
          "ENV=othersecret:1' "
          "will mount a volume at '/secrets/api' containing a file "
          "'key' with the latest version of secret 'mysecret'. "
          'An environment variable named ENV will also be created '
          "whose value is version 1 of secret 'othersecret'."
      ),
      flag_name='secrets',
  )


def AddSecretsFlags(parser):
  """Adds flags for creating, updating, and deleting secrets."""
  SecretsFlags().AddToParser(parser)


def AddConfigMapsFlags(parser):
  """Adds flags for creating, updating, and deleting config maps."""
  AddMapFlagsNoFile(
      parser,
      group_help=(
          'Specify config map to mount or provide as environment '
          "variables. Keys starting with a forward slash '/' are mount "
          'paths. All other keys correspond to environment variables. '
          'The values associated with each of these should be in the '
          'form CONFIG_MAP_NAME:KEY_IN_CONFIG_MAP; you may omit the '
          'key within the config map to specify a mount of all keys '
          'within the config map. For example: '
          "'--update-config-maps=/my/path=myconfig,"
          "ENV=otherconfig:key.json' "
          "will create a volume with config map 'myconfig' "
          "and mount that volume at '/my/path'. Because no config map "
          "key was specified, all keys in 'myconfig' will be included. "
          'An environment variable named ENV will also be created '
          "whose value is the value of 'key.json' in 'otherconfig. Not "
          'supported on the fully managed version of Cloud Run.'
      ),
      flag_name='config-maps',
  )


def AddDescriptionFlag(parser):
  parser.add_argument(
      '--description',
      help='Provides an optional, human-readable description of the service.',
  )


def AddLabelsFlag(parser, extra_message=''):
  """Add only the --labels flag."""
  labels_util.GetCreateLabelsFlag(
      extra_message=extra_message, validate_keys=False, validate_values=False
  ).AddToParser(parser)


def AddLabelsFlags(parser):
  """Adds update command labels flags to an argparse parser.

  Args:
    parser: The argparse parser to add the flags to.
  """
  group = parser.add_group()
  add_group = group.add_mutually_exclusive_group()
  AddLabelsFlag(add_group, 'An alias to --update-labels.')
  labels_util.GetUpdateLabelsFlag(
      '', validate_keys=False, validate_values=False
  ).AddToParser(add_group)
  remove_group = group.add_mutually_exclusive_group()
  labels_util.GetClearLabelsFlag().AddToParser(remove_group)
  labels_util.GetRemoveLabelsFlag('').AddToParser(remove_group)


def AddGeneralAnnotationFlags(parser):
  """Adds the update command annotation flag to an argparse parser.

  Args:
    parser: The argparse parser to add the flags to.
  """
  parser.add_argument(
      '--update-annotations',
      metavar='KEY=VALUE',
      type=arg_parsers.ArgDict(),
      action=arg_parsers.UpdateAction,
      hidden=True,
      help=(
          'List of annotation KEY=VALUE pairs to update. If an annotation '
          'exists, its value is modified. Otherwise, a new annotation is '
          'created.'
      ),
  )


class _ScaleValue(object):
  """Type for min/max-instances flag values."""

  def __init__(self, value):
    self.restore_default = value == 'default'
    if not self.restore_default:
      try:
        self.instance_count = int(value)
      except (TypeError, ValueError):
        raise serverless_exceptions.ArgumentError(
            "Instance count value %s is not an integer or 'default'." % value
        )

      if self.instance_count < 0:
        raise serverless_exceptions.ArgumentError(
            'Instance count value %s is negative.' % value
        )


def AddMinInstancesFlag(parser, resource_kind='service'):
  """Add min scaling flag."""
  help_text = (
      'The minimum number of container instances for this Revision of the'
      " Service to run or 'default' to remove any minimum."
  )
  if resource_kind == 'worker':
    help_text = (
        'The minimum number of container instances for this Worker to run or'
        " 'default' to remove any minimum. These instances will be divided"
        ' among all Revisions receiving a percentage of instance split.'
    )
  parser.add_argument(
      '--min-instances',
      type=_ScaleValue,
      help=help_text,
  )


def AddServiceMinInstancesFlag(parser):
  """Add service-level min scaling flag."""
  parser.add_argument(
      '--service-min-instances',
      type=_ScaleValue,
      help=(
          'The minimum number of container instances for this Service to run '
          "or 'default' to remove any minimum. These instances will be divided "
          'among all Revisions receiving a percentage of traffic.'
      ),
  )


def AddMaxInstancesFlag(parser):
  """Add max scaling flag."""
  parser.add_argument(
      '--max-instances',
      type=_ScaleValue,
      help=(
          'The maximum number of container instances of the Service to run. '
          "Use 'default' to unset the limit and use the platform default."
      ),
  )


def CommandFlag():
  """Create a flag for specifying container's startup command."""
  return base.Argument(
      '--command',
      metavar='COMMAND',
      type=arg_parsers.ArgList(),
      action=arg_parsers.UpdateAction,
      help=(
          'Entrypoint for the container image. If not specified, the '
          "container image's default Entrypoint is run. "
          'To reset this field to its default, pass an empty string.'
      ),
  )


def AddCommandFlag(parser):
  """Add flags for specifying container's startup command."""
  CommandFlag().AddToParser(parser)


def ArgsFlag(for_execution_overrides=False):
  """Creates a flag for specifying container's startup args."""
  help_text = (
      'Comma-separated arguments passed to the command run by the container'
      ' image.'
  )
  if for_execution_overrides:
    help_text += (
        ' If provided, an execution will be created with the input values.'
        ' Otherwise, the existing arguments of the job are used.'
    )
  else:
    help_text += (
        " If not specified and no '--command' is provided, the"
        " container image's default Cmd is used. Otherwise, if not specified,"
        ' no arguments are passed. To reset this field to its default, pass'
        ' an empty string.'
    )
  return base.Argument(
      '--args',
      metavar='ARG',
      type=arg_parsers.ArgList(),
      action=arg_parsers.UpdateAction,
      help=help_text,
  )


def AddArgsFlag(parser, for_execution_overrides=False):
  """Add flags for specifying container's startup args."""
  ArgsFlag(for_execution_overrides=for_execution_overrides).AddToParser(parser)


def AddDeployHealthCheckFlag(parser):
  """Add flag enable and disable deploy health check."""
  parser.add_argument(
      '--deploy-health-check',
      action=arg_parsers.StoreTrueFalseAction,
      help=(
          'Schedules a single instance of the Revision and waits for it to'
          ' pass its startup probe for the deployment to succeed. If disabled,'
          ' the startup probe runs only when the revision is first started via'
          ' invocation or by setting min-instances. This check is enabled by'
          ' default when unspecified.'
      ),
  )


def AddDefaultUrlFlag(parser):
  """Add flag enable and disable default url."""
  parser.add_argument(
      '--default-url',
      action=arg_parsers.StoreTrueFalseAction,
      help=(
          'Toggles the default url for a run service. This is enabled by'
          ' default if not specified.'
      ),
  )


def AddInvokerIamCheckFlag(parser):
  """Add flag enable and disable invoker iam check."""
  parser.add_argument(
      '--invoker-iam-check',
      action=arg_parsers.StoreTrueFalseAction,
      help=(
          'Indicates whether an IAM check should occur when invoking the '
          'container. This is Enabled by default. Disabling this flag is not '
          'available in all projects.'
      ),
  )


def AddClientNameAndVersionFlags(parser):
  """Add flags for specifying the client name and version annotations."""
  parser.add_argument(
      '--client-name',
      hidden=True,
      help=(
          "Name of the client handling the deployment. Defaults to ``global'' "
          'if this and --client-version are both unspecified.'
      ),
  )
  parser.add_argument(
      '--client-version',
      hidden=True,
      help=(
          'Version of the client handling the deployment. Defaults to the'
          ' current gcloud version if this and --client-name are both'
          ' unspecified.'
      ),
  )


def AddCmekKeyFlag(parser, with_clear=True):
  """Add CMEK key flag."""
  policy_group = parser
  if with_clear:
    policy_group = parser.add_mutually_exclusive_group()
    policy_group.add_argument(
        '--clear-key',
        default=False,
        action='store_true',
        help='Remove any previously set CMEK key reference.',
    )
  policy_group.add_argument(
      '--key', help='CMEK key reference to encrypt the container with.'
  )


def AddCmekKeyRevocationActionTypeFlag(parser, with_clear=True):
  """Add post CMEK key revocation action type flag."""
  policy_group = parser
  if with_clear:
    policy_group = parser.add_mutually_exclusive_group()
    policy_group.add_argument(
        '--clear-post-key-revocation-action-type',
        default=False,
        action='store_true',
        help='Remove any previously set post CMEK key revocation action type.',
    )
  policy_group.add_argument(
      '--post-key-revocation-action-type',
      choices=_POST_CMEK_KEY_REVOCATION_ACTION_TYPE_CHOICES,
      help='Action type after CMEK key revocation.',
  )


def AddEncryptionKeyShutdownHoursFlag(parser, with_clear=True):
  """Add Cmek key shutdown hours flag."""
  policy_group = parser
  if with_clear:
    policy_group = parser.add_mutually_exclusive_group()
    policy_group.add_argument(
        '--clear-encryption-key-shutdown-hours',
        default=False,
        action='store_true',
        help='Remove any previously set CMEK key shutdown hours setting.',
    )
  policy_group.add_argument(
      '--encryption-key-shutdown-hours',
      help=(
          'The number of hours to wait before an automatic shutdown server'
          ' after CMEK key revocation is detected.'
      ),
  )


def _PortValue(value):
  """Returns True if port value is an int within range or 'default'."""
  try:
    return value == 'default' or (1 <= int(value) <= 65535)
  except ValueError:
    return False


_DEFAULT_PORT_HELP = """Container port to receive requests at. Also sets
the $PORT environment variable. Must be a number between 1 and 65535, inclusive.
To unset this field, pass the special value "default".
If updating an existing service with a TCP startup probe pointing to the
previous container port, this will also update the probe port.
"""


def PortArg(help_text=_DEFAULT_PORT_HELP):
  """Port argument for overriding $PORT."""
  return base.Argument(
      '--port',
      type=arg_parsers.CustomFunctionValidator(
          _PortValue,
          'must be an integer between 1 and 65535, inclusive, or "default".',
      ),
      help=help_text,
  )


def AddPortFlag(parser, help_text=_DEFAULT_PORT_HELP):
  """Add port flag to override $PORT."""
  parser.add_argument(
      '--port',
      type=arg_parsers.CustomFunctionValidator(
          _PortValue,
          'must be an integer between 1 and 65535, inclusive, or "default".',
      ),
      help=help_text,
  )


def Http2Flag():
  """Create http/2 flag to set the port name."""
  return base.Argument(
      '--use-http2',
      action=arg_parsers.StoreTrueFalseAction,
      help='Whether to use HTTP/2 for connections to the service.',
  )


def AddHttp2Flag(parser):
  """Add http/2 flag to set the port name."""
  Http2Flag().AddToParser(parser)


def AddParallelismFlag(parser):
  """Add job parallelism/concurrency flag."""
  parser.add_argument(
      '--parallelism',
      type=arg_parsers.BoundedInt(lower_bound=0),
      help=(
          'Number of tasks that may run concurrently. Must be less than or'
          ' equal to the number of tasks. Set to 0 to unset.'
      ),
  )


def AddTasksFlag(parser, for_execution_overrides=False):
  """Add job number of tasks flag which maps to job.spec.template.spec.task_count."""
  help_text = (
      'Number of tasks that must run to completion for the execution to be'
      ' considered done.'
  )
  if for_execution_overrides:
    help_text += (
        ' If provided, an execution will be created with this value. Otherwise'
        ' the existing task count of the job is used.'
    )
    parser.add_argument(
        '--tasks',
        type=arg_parsers.BoundedInt(lower_bound=1),
        help=help_text,
    )
  else:
    parser.add_argument(
        '--tasks',
        type=arg_parsers.BoundedInt(lower_bound=1),
        default=1,
        help=help_text,
    )


def AddMaxRetriesFlag(parser):
  """Add job max retries flag to specify number of task restarts."""
  parser.add_argument(
      '--max-retries',
      type=arg_parsers.BoundedInt(lower_bound=0),
      help=(
          'Number of times a task is allowed to restart in case of '
          'failure before being failed permanently. This applies per-task, not '
          'per-job. If set to 0, tasks will only run once and never be '
          'retried on failure.'
      ),
  )


def AddWaitForCompletionFlag(parser, implies_execute_now=False):
  """Add job flag to poll until completion on create."""
  help_text = (
      'Wait until the execution has completed running before exiting. '
      'If not set, gcloud exits successfully when the execution has started.'
  )
  if implies_execute_now:
    help_text += '  Implies --execute-now.'
  parser.add_argument(
      '--wait', default=False, action='store_true', help=help_text
  )


def AddTaskTimeoutFlags(parser, for_execution_overrides=False):
  """Add job flags for job and task deadline."""
  help_text = (
      ' In the case of retries, this deadline applies to each attempt of a'
      ' task. If the task attempt does not complete within this time, it will'
      ' be killed. It is specified as a duration; for example, "10m5s" is ten'
      " minutes, and five seconds. If you don't specify a unit, seconds is"
      ' assumed. For example, "10" is 10 seconds.'
  )
  if for_execution_overrides:
    help_text = (
        'The existing maximum time (deadline) a job task attempt can run for.'
        ' If provided, an execution will be created with this value. Otherwise'
        ' existing maximum time of the job is used.'
        + help_text
    )
  else:
    help_text = (
        'Set the maximum time (deadline) a job task attempt can run for.'
        + help_text
    )
  parser.add_argument(
      '--task-timeout',
      type=arg_parsers.Duration(lower_bound='1s'),
      help=help_text,
  )


def AddBinAuthzPolicyFlags(parser, with_clear=True):
  """Add flags for BinAuthz."""
  policy_group = parser
  if with_clear:
    policy_group = parser.add_mutually_exclusive_group()
    policy_group.add_argument(
        '--clear-binary-authorization',
        default=False,
        action='store_true',
        help='Remove any previously set Binary Authorization policy.',
    )
  policy_group.add_argument(
      '--binary-authorization',
      metavar='POLICY',
      # Don't actually validate the value here, let that happen server-side
      # so the future change to support named policies will be backwards
      # compatible with older gcloud versions.
      help=(
          'Binary Authorization policy to check against. This must be set to '
          '"default".'
      ),
  )


def AddBinAuthzBreakglassFlag(parser):
  parser.add_argument(
      '--breakglass',
      metavar='JUSTIFICATION',
      help=(
          'Justification to bypass Binary Authorization policy constraints '
          'and allow the operation. See '
          'https://cloud.google.com/binary-authorization/docs/using-breakglass '
          'for more information. '
          'Next update or deploy command will automatically clear existing '
          'breakglass justification.'
      ),
  )


def AddVpcNetworkFlags(parser, resource_kind='service'):
  """Add flags for setting VPC network."""
  parser.add_argument(
      '--network',
      metavar='NETWORK',
      help=(
          'The VPC network that the Cloud Run {kind} will be able to send'
          ' traffic to. If --subnet is also specified, subnet must be a'
          ' subnetwork of the network specified by this --network flag. To'
          ' clear existing VPC network settings, use --clear-network.'.format(
              kind=resource_kind
          )
      ),
  )


def AddVpcSubnetFlags(parser, resource_kind='service'):
  """Add flags for setting VPC subnetwork."""
  parser.add_argument(
      '--subnet',
      metavar='SUBNET',
      help=(
          'The VPC subnetwork that the Cloud Run {kind} will get IPs from. The'
          ' subnetwork must be `/26` or larger. If --network is also specified,'
          ' subnet must be a subnetwork of the network specified by the'
          ' --network flag. If --network is not specified, network will be'
          ' looked up from this subnetwork. To clear existing VPC network'
          ' settings, use --clear-network.'.format(kind=resource_kind)
      ),
  )


def AddVpcNetworkTagsFlags(parser, resource_kind='service'):
  """Add flags for setting VPC network tags."""
  parser.add_argument(
      '--network-tags',
      metavar='TAG',
      type=arg_parsers.ArgList(),
      action=arg_parsers.UpdateAction,
      help=(
          'Applies the given Compute Engine tags (comma separated) to the '
          'Cloud Run {kind}. '
          'To clear existing tags, use --clear-network-tags.'.format(
              kind=resource_kind
          )
      ),
  )


def AddClearVpcNetworkFlags(parser, resource_kind='service'):
  """Add flags for clearing VPC network."""
  parser.add_argument(
      '--clear-network',
      action='store_true',
      help=(
          'Disconnect this Cloud Run {kind} from the VPC network it is'
          ' connected to.'.format(kind=resource_kind)
      ),
  )


def AddClearVpcNetworkTagsFlags(parser, resource_kind='service'):
  """Add flags for clearing VPC network tags."""
  parser.add_argument(
      '--clear-network-tags',
      action='store_true',
      help=(
          'Clears all existing Compute Engine tags from the Cloud Run {kind}. '
          .format(kind=resource_kind)
      ),
  )


def AddVpcNetworkGroupFlags(parser, resource_kind='service', is_update=False):
  """Add flags for all VPC network settings."""
  group = parser.add_argument_group('Direct VPC egress setting flags group.')
  AddVpcNetworkFlags(group, resource_kind)
  AddVpcSubnetFlags(group, resource_kind)
  if not is_update:
    AddVpcNetworkTagsFlags(group, resource_kind)
    return
  tags_group = group.add_mutually_exclusive_group()
  AddVpcNetworkTagsFlags(tags_group, resource_kind)
  AddClearVpcNetworkTagsFlags(tags_group, resource_kind)


def AddVpcNetworkGroupFlagsForCreate(parser, resource_kind='service'):
  """Add flags for all VPC network settings when creating a resource."""
  AddVpcNetworkGroupFlags(parser, resource_kind, is_update=False)


def AddVpcNetworkGroupFlagsForUpdate(parser, resource_kind='service'):
  """Add flags for all VPC network settings when updating a resource."""
  group = parser.add_mutually_exclusive_group()
  AddVpcNetworkGroupFlags(group, resource_kind, is_update=True)
  AddClearVpcNetworkFlags(group, resource_kind)


def AddCustomAudiencesFlag(parser):
  """Add flags for setting custom audiences."""
  repeated.AddPrimitiveArgs(
      parser,
      'Service',
      'custom-audiences',
      'custom audiences',
      auto_group_help=False,
      additional_help=(
          'These flags modify the custom audiences that can be '
          'used in the audience field of ID token for '
          'authenticated requests.'
      ),
  )


def AddSessionAffinityFlag(parser):
  """Add session affinity flag to enable session affinity."""
  parser.add_argument(
      '--session-affinity',
      action=arg_parsers.StoreTrueFalseAction,
      help='Whether to enable session affinity for connections to the service.',
  )


def AddRuntimeFlag(parser):
  """Add flags for Wasm runtime."""
  parser.add_argument(
      '--runtime',
      metavar='RUNTIME',
      hidden=True,
      help=(
          'The runtime to use. "wasm" for WebAssembly runtime, '
          '"default" for the default Linux runtime.'
      ),
  )


def _HasChanges(args, flags):
  """True iff any of the passed flags are set."""
  return any(FlagIsExplicitlySet(args, flag) for flag in flags)


def _HasEnvChanges(args):
  """True iff any of the env var flags are set."""
  env_flags = [
      'update_env_vars',
      'set_env_vars',
      'remove_env_vars',
      'clear_env_vars',
      'env_vars_file',
  ]
  return _HasChanges(args, env_flags)


def _HasCloudSQLChanges(args):
  """True iff any of the cloudsql flags are set."""
  instances_flags = [
      'add_cloudsql_instances',
      'set_cloudsql_instances',
      'remove_cloudsql_instances',
      'clear_cloudsql_instances',
  ]
  return _HasChanges(args, instances_flags)


def _EnabledCloudSqlApiRequired(args):
  """True iff flags that add or set cloud sql instances are set."""
  instances_flags = (
      'add_cloudsql_instances',
      'set_cloudsql_instances',
  )
  return _HasChanges(args, instances_flags)


def _HasLabelChanges(args):
  """True iff any of the label flags are set."""
  label_flags = ['labels', 'update_labels', 'clear_labels', 'remove_labels']
  return _HasChanges(args, label_flags)


def _HasSecretsChanges(args):
  """True iff any of the secret flags are set."""
  secret_flags = [
      'update_secrets',
      'set_secrets',
      'remove_secrets',
      'clear_secrets',
  ]
  return _HasChanges(args, secret_flags)


def _HasConfigMapsChanges(args):
  """True iff any of the config maps flags are set."""
  config_maps_flags = [
      'update_config_maps',
      'set_config_maps',
      'remove_config_maps',
      'clear_config_maps',
  ]
  return _HasChanges(args, config_maps_flags)


def _HasTrafficTagsChanges(args):
  """True iff any of the traffic tags flags are set."""
  tags_flags = ['update_tags', 'set_tags', 'remove_tags', 'clear_tags']
  return _HasChanges(args, tags_flags)


def _HasTrafficChanges(args):
  """True iff any of the traffic flags are set."""
  traffic_flags = ['to_revisions', 'to_tags', 'to_latest']
  return _HasChanges(args, traffic_flags) or _HasTrafficTagsChanges(args)


def _HasCustomAudiencesChanges(args):
  """True iff any of the custom audiences flags are set."""
  instances_flags = [
      'add_custom_audiences',
      'set_custom_audiences',
      'remove_custom_audiences',
      'clear_custom_audiences',
  ]
  return _HasChanges(args, instances_flags)


def HasExecutionOverrides(args):
  overrides_flags = [
      'args',
      'update_env_vars',
      'task_timeout',
      'tasks',
  ]
  return _HasChanges(args, overrides_flags)


def HasContainerOverrides(args):
  overrides_flags = [
      'args',
      'update_env_vars',
  ]
  return _HasChanges(args, overrides_flags)


def _GetEnvChanges(args, **kwargs):
  """Return config_changes.EnvVarLiteralChanges for given args."""
  return config_changes.EnvVarLiteralChanges(
      updates=_StripKeys(
          getattr(args, 'update_env_vars', None)
          or args.set_env_vars
          or args.env_vars_file
          or {}
      ),
      removes=_MapLStrip(getattr(args, 'remove_env_vars', None) or []),
      clear_others=bool(
          args.set_env_vars or args.env_vars_file or args.clear_env_vars
      ),
      **kwargs,
  )


def _GetScalingChanges(args):
  """Returns the list of changes for scaling for given args."""
  result = []
  if 'min_instances' in args and args.min_instances is not None:
    scale_value = args.min_instances
    if scale_value.restore_default or scale_value.instance_count == 0:
      result.append(
          config_changes.DeleteTemplateAnnotationChange(
              revision.MIN_SCALE_ANNOTATION
          )
      )
    else:
      result.append(
          config_changes.SetTemplateAnnotationChange(
              revision.MIN_SCALE_ANNOTATION, str(scale_value.instance_count)
          )
      )
  if 'max_instances' in args and args.max_instances is not None:
    scale_value = args.max_instances
    if scale_value.restore_default:
      result.append(
          config_changes.DeleteTemplateAnnotationChange(
              revision.MAX_SCALE_ANNOTATION
          )
      )
    else:
      result.append(
          config_changes.SetTemplateAnnotationChange(
              revision.MAX_SCALE_ANNOTATION, str(scale_value.instance_count)
          )
      )
  return result


def _GetServiceScalingChanges(args):
  """Return the changes for service-level scaling for the given args."""
  result = []
  if 'service_min_instances' in args and args.service_min_instances is not None:
    scale_value = args.service_min_instances
    if scale_value.restore_default or scale_value.instance_count == 0:
      result.append(
          config_changes.DeleteAnnotationChange(
              service.SERVICE_MIN_SCALE_ANNOTATION
          )
      )
    else:
      result.append(
          config_changes.SetAnnotationChange(
              service.SERVICE_MIN_SCALE_ANNOTATION,
              str(scale_value.instance_count),
          )
      )
  return result


def _GetWorkerScalingChanges(args):
  """Return the changes for engine-level scaling for Worker resources for the given args."""
  result = []
  if 'min_instances' in args and args.min_instances is not None:
    # TODO(b/322180968): Once Worker API is ready, replace Service related
    # references.
    scale_value = args.min_instances
    if scale_value.restore_default or scale_value.instance_count == 0:
      result.append(
          config_changes.DeleteAnnotationChange(
              service.SERVICE_MIN_SCALE_ANNOTATION
          )
      )
    else:
      result.append(
          config_changes.SetAnnotationChange(
              service.SERVICE_MIN_SCALE_ANNOTATION,
              str(scale_value.instance_count),
          )
      )
  return result


def _IsVolumeMountKey(key):
  """Returns True if the key refers to a volume mount."""
  return key.startswith('/')


def _ValidatedMountPoint(key):
  if _IsVolumeMountKey(key):
    segments = key.split('/')
    too_short = len(segments) < 3
    if not too_short:
      disallowed = {'', '.', '..'}
      all_legal_segments = all(seg not in disallowed for seg in segments[1:])
      if all_legal_segments:
        return key
  raise serverless_exceptions.ConfigurationError(
      'Mount path [{}] must be in the form /<mountPath>/<path>'.format(key)
  )


def _GetSecretsChanges(args, container_name=None):
  """Return secret env var and volume changes for given args."""
  volume_kwargs = {}
  env_kwargs = {}

  updates = _StripKeys(
      getattr(args, 'update_secrets', None) or args.set_secrets or {}
  )
  volume_kwargs['updates'] = {
      k: secrets_mapping.ReachableSecret(v, _ValidatedMountPoint(k))
      for k, v in updates.items()
      if _IsVolumeMountKey(k)
  }
  env_kwargs['updates'] = {
      k: secrets_mapping.ReachableSecret(v, k)
      for k, v in updates.items()
      if not _IsVolumeMountKey(k)
  }

  removes = _MapLStrip(getattr(args, 'remove_secrets', None) or [])
  volume_kwargs['removes'] = [k for k in removes if _IsVolumeMountKey(k)]
  env_kwargs['removes'] = [k for k in removes if not _IsVolumeMountKey(k)]

  clear_others = bool(args.set_secrets or args.clear_secrets)
  env_kwargs['clear_others'] = clear_others
  volume_kwargs['clear_others'] = clear_others

  secret_changes = []
  if any(env_kwargs.values()):
    secret_changes.append(
        config_changes.SecretEnvVarChanges(
            container_name=container_name, **env_kwargs
        )
    )
  if any(volume_kwargs.values()):
    secret_changes.append(
        config_changes.SecretVolumeChanges(
            container_name=container_name, **volume_kwargs
        )
    )
  return secret_changes


def _GetConfigMapsChanges(args):
  """Return config map env var and volume changes for given args."""
  volume_kwargs = {}
  env_kwargs = {}

  updates = _StripKeys(
      getattr(args, 'update_config_maps', None) or args.set_config_maps or {}
  )
  volume_kwargs['updates'] = {
      k: v for k, v in updates.items() if _IsVolumeMountKey(k)
  }
  env_kwargs['updates'] = {
      k: v for k, v in updates.items() if not _IsVolumeMountKey(k)
  }

  removes = _MapLStrip(getattr(args, 'remove_config_maps', None) or [])
  volume_kwargs['removes'] = [k for k in removes if _IsVolumeMountKey(k)]
  env_kwargs['removes'] = [k for k in removes if not _IsVolumeMountKey(k)]

  clear_others = bool(args.set_config_maps or args.clear_config_maps)
  env_kwargs['clear_others'] = clear_others
  volume_kwargs['clear_others'] = clear_others

  config_maps_changes = []
  if any(env_kwargs.values()):
    config_maps_changes.append(
        config_changes.ConfigMapEnvVarChanges(**env_kwargs)
    )
  if any(volume_kwargs.values()):
    config_maps_changes.append(
        config_changes.ConfigMapVolumeChanges(**volume_kwargs)
    )
  return config_maps_changes


def PromptToEnableApi(service_name):
  """Prompts to enable the API and throws if the answer is no.

  Args:
    service_name: str, The service token of the API to prompt for.
  """
  if not properties.VALUES.core.should_prompt_to_enable_api.GetBool():
    return

  project = properties.VALUES.core.project.Get(required=True)
  # Don't prompt to enable an already enabled API
  if not enable_api.IsServiceEnabled(project, service_name):
    if console_io.PromptContinue(
        default=False,
        cancel_on_no=True,
        prompt_string=(
            'API [{}] not enabled on project [{}]. '
            'Would you like to enable and retry (this will take a '
            'few minutes)?'
        ).format(service_name, project),
    ):
      enable_api.EnableService(project, service_name)


_CLOUD_SQL_API_SERVICE_TOKEN = 'sql-component.googleapis.com'
_CLOUD_SQL_ADMIN_API_SERVICE_TOKEN = 'sqladmin.googleapis.com'


def _CheckCloudSQLApiEnablement():
  if not properties.VALUES.core.should_prompt_to_enable_api.GetBool():
    return
  try:
    PromptToEnableApi(_CLOUD_SQL_API_SERVICE_TOKEN)
    PromptToEnableApi(_CLOUD_SQL_ADMIN_API_SERVICE_TOKEN)
  except (
      services_exceptions.GetServicePermissionDeniedException,
      apitools_exceptions.HttpError,
  ):
    log.status.Print(
        'Skipped validating Cloud SQL API and Cloud SQL Admin API'
        ' enablement due to an issue contacting the Service Usage '
        ' API. Please ensure the Cloud SQL API and Cloud SQL Admin'
        ' API are activated (see '
        'https://console.cloud.google.com/apis/dashboard).'
    )


def _GetTrafficChanges(args):
  """Returns a changes for traffic assignment based on the flags."""
  update_tags = args.update_tags or args.set_tags or {}
  remove_tags = args.remove_tags or []
  clear_other_tags = bool(args.set_tags) or args.clear_tags
  by_tag = False
  if args.to_latest:
    # Mutually exclusive flag with to-revisions, to-tags
    new_percentages = {traffic.LATEST_REVISION_KEY: 100}
  elif args.to_revisions:
    new_percentages = args.to_revisions
  elif FlagIsExplicitlySet(args, 'to_tags'):
    new_percentages = args.to_tags
    by_tag = True
  else:
    new_percentages = {}

  return config_changes.TrafficChanges(
      new_percentages,
      by_tag,
      update_tags,
      remove_tags,
      clear_other_tags,
  )


def _GetIngressChanges(args):
  """Returns changes to ingress traffic allowed based on the flags."""
  platform = platforms.GetPlatform()
  if platform == platforms.PLATFORM_MANAGED:
    return config_changes.SetAnnotationChange(
        service.INGRESS_ANNOTATION, args.ingress
    )
  elif args.ingress == service.INGRESS_INTERNAL:
    return config_changes.EndpointVisibilityChange(True)
  elif args.ingress == service.INGRESS_ALL:
    return config_changes.EndpointVisibilityChange(False)
  else:
    raise serverless_exceptions.ConfigurationError(
        'Ingress value `{}` is not supported on platform `{}`.'.format(
            args.ingress, platform
        )
    )


def _GetBaseImagesToSet(container_args):
  """Returns a dict of base images to set."""

  return {
      name: args.base_image
      for (name, args) in container_args.items()
      if hasattr(args, 'base_image') and args.base_image
  }


def _GetBaseImagesToClear(container_args):
  """Returns a list of containers to clear base images from."""

  return [
      name
      for name, args in container_args.items()
      if hasattr(args, 'clear_base_image') and args.clear_base_image
  ]


def _GetBaseImageChanges(args):
  """Returns changes to base image based on the flags."""
  base_images_to_set = _GetBaseImagesToSet(args.containers)
  base_images_to_clear = _GetBaseImagesToClear(args.containers)
  if base_images_to_set or base_images_to_clear:
    return [
        config_changes.BaseImagesAnnotationChange(
            updates=base_images_to_set, deletes=base_images_to_clear
        ),
    ]
  return []


def _PrependClientNameAndVersionChange(args, changes):
  """Set client name and version regardless of whether or not it was specified."""
  if 'client_name' in args:
    is_either_specified = args.IsSpecified('client_name') or args.IsSpecified(
        'client_version'
    )
    changes.insert(
        0,
        config_changes.SetClientNameAndVersionAnnotationChange(
            args.client_name if is_either_specified else 'gcloud',
            args.client_version
            if is_either_specified
            else config.CLOUD_SDK_VERSION,
            set_on_template=config_changes.AdjustsTemplate(changes),
        ),
    )


def _GetConfigurationChanges(args, release_track=base.ReleaseTrack.GA):
  """Returns a list of changes shared by multiple resources, based on the flags set."""
  changes = []

  # FlagIsExplicitlySet can't be used here because args.image is also set from
  # code in deploy.py.
  if hasattr(args, 'image') and args.image is not None:
    changes.append(config_changes.ImageChange(args.image))

  if _HasEnvChanges(args):
    changes.append(_GetEnvChanges(args))

  if _HasCloudSQLChanges(args):
    region = GetRegion(args)
    project = getattr(
        args, 'project', None
    ) or properties.VALUES.core.project.Get(required=True)
    if _EnabledCloudSqlApiRequired(args):
      _CheckCloudSQLApiEnablement()
    changes.append(
        config_changes.CloudSQLChanges.FromArgs(
            project=project, region=region, args=args
        )
    )

  # we need to sandwich secrets changes between removing and adding volumes
  # because secrets changes can also impact volumes
  if (
      FlagIsExplicitlySet(args, 'remove_volume_mount')
      and args.remove_volume_mount
  ) or (
      FlagIsExplicitlySet(args, 'clear_volume_mounts')
      and args.clear_volume_mounts
  ):
    changes.append(
        config_changes.RemoveVolumeMountChange(
            removed_mounts=args.remove_volume_mount,
            clear_mounts=args.clear_volume_mounts,
        )
    )
  if (FlagIsExplicitlySet(args, 'remove_volume') and args.remove_volume) or (
      FlagIsExplicitlySet(args, 'clear_volumes') and args.clear_volumes
  ):
    changes.append(
        config_changes.RemoveVolumeChange(
            args.remove_volume, args.clear_volumes
        )
    )
  if _HasSecretsChanges(args):
    changes.extend(_GetSecretsChanges(args))
  if FlagIsExplicitlySet(args, 'add_volume') and args.add_volume:
    changes.append(
        config_changes.AddVolumeChange(args.add_volume, release_track)
    )

  if FlagIsExplicitlySet(args, 'add_volume_mount') and args.add_volume_mount:
    changes.append(
        config_changes.AddVolumeMountChange(new_mounts=args.add_volume_mount)
    )
  if _HasConfigMapsChanges(args):
    changes.extend(_GetConfigMapsChanges(args))

  if 'cpu' in args and args.cpu:
    changes.append(config_changes.ResourceChanges(cpu=args.cpu))
  if 'memory' in args and args.memory:
    changes.append(config_changes.ResourceChanges(memory=args.memory))
  if 'gpu' in args and args.gpu:
    changes.append(config_changes.ResourceChanges(gpu=args.gpu))
  if 'service_account' in args and args.service_account:
    changes.append(
        config_changes.ServiceAccountChanges(
            service_account=args.service_account
        )
    )
  if _HasLabelChanges(args):
    additions = (
        args.labels
        if FlagIsExplicitlySet(args, 'labels')
        else args.update_labels
    )
    diff = labels_util.Diff(
        additions=additions,
        subtractions=args.remove_labels if 'remove_labels' in args else [],
        clear=args.clear_labels if 'clear_labels' in args else False,
    )
    if diff.MayHaveUpdates():
      changes.append(config_changes.LabelChanges(diff))
  if 'vpc_connector' in args and args.vpc_connector:
    changes.append(config_changes.VpcConnectorChange(args.vpc_connector))
  if FlagIsExplicitlySet(args, 'vpc_egress'):
    changes.append(
        config_changes.SetTemplateAnnotationChange(
            container_resource.EGRESS_SETTINGS_ANNOTATION, args.vpc_egress
        )
    )
  if 'clear_vpc_connector' in args and args.clear_vpc_connector:
    # MUST be after 'vpc_egress' change.
    changes.append(config_changes.ClearVpcConnectorChange())
  if 'command' in args and args.command is not None:
    # Allow passing an empty string here to reset the field
    changes.append(config_changes.ContainerCommandChange(args.command))
  if 'args' in args and args.args is not None:
    # Allow passing an empty string here to reset the field
    changes.append(config_changes.ContainerArgsChange(args.args))
  if FlagIsExplicitlySet(args, 'binary_authorization'):
    changes.append(
        config_changes.SetAnnotationChange(
            k8s_object.BINAUTHZ_POLICY_ANNOTATION, args.binary_authorization
        )
    )
  if FlagIsExplicitlySet(args, 'clear_binary_authorization'):
    changes.append(
        config_changes.DeleteAnnotationChange(
            k8s_object.BINAUTHZ_POLICY_ANNOTATION
        )
    )
  if FlagIsExplicitlySet(args, 'breakglass'):
    changes.append(
        config_changes.SetAnnotationChange(
            k8s_object.BINAUTHZ_BREAKGLASS_ANNOTATION, args.breakglass
        )
    )
  if FlagIsExplicitlySet(args, 'key'):
    changes.append(
        config_changes.SetTemplateAnnotationChange(
            container_resource.CMEK_KEY_ANNOTATION, args.key
        )
    )
  if FlagIsExplicitlySet(args, 'post_key_revocation_action_type'):
    changes.append(
        config_changes.SetTemplateAnnotationChange(
            container_resource.POST_CMEK_KEY_REVOCATION_ACTION_TYPE_ANNOTATION,
            args.post_key_revocation_action_type,
        )
    )
  if FlagIsExplicitlySet(args, 'encryption_key_shutdown_hours'):
    changes.append(
        config_changes.SetTemplateAnnotationChange(
            container_resource.ENCRYPTION_KEY_SHUTDOWN_HOURS_ANNOTATION,
            args.encryption_key_shutdown_hours,
        )
    )
  if FlagIsExplicitlySet(args, 'clear_key'):
    changes.append(
        config_changes.DeleteTemplateAnnotationChange(
            container_resource.CMEK_KEY_ANNOTATION
        )
    )
    changes.append(
        config_changes.DeleteTemplateAnnotationChange(
            container_resource.POST_CMEK_KEY_REVOCATION_ACTION_TYPE_ANNOTATION
        )
    )
    changes.append(
        config_changes.DeleteTemplateAnnotationChange(
            container_resource.ENCRYPTION_KEY_SHUTDOWN_HOURS_ANNOTATION
        )
    )
  if FlagIsExplicitlySet(args, 'clear_post_key_revocation_action_type'):
    changes.append(
        config_changes.DeleteTemplateAnnotationChange(
            container_resource.POST_CMEK_KEY_REVOCATION_ACTION_TYPE_ANNOTATION
        )
    )
    changes.append(
        config_changes.DeleteTemplateAnnotationChange(
            container_resource.ENCRYPTION_KEY_SHUTDOWN_HOURS_ANNOTATION
        )
    )
  if FlagIsExplicitlySet(args, 'clear_encryption_key_shutdown_hours'):
    changes.append(
        config_changes.DeleteTemplateAnnotationChange(
            container_resource.ENCRYPTION_KEY_SHUTDOWN_HOURS_ANNOTATION
        )
    )
  if FlagIsExplicitlySet(args, 'description'):
    changes.append(
        config_changes.SetAnnotationChange(
            k8s_object.DESCRIPTION_ANNOTATION, args.description
        )
    )
  if 'execution_environment' in args and args.execution_environment:
    changes.append(config_changes.SandboxChange(args.execution_environment))
  if (
      FlagIsExplicitlySet(args, 'network')
      or FlagIsExplicitlySet(args, 'subnet')
      or FlagIsExplicitlySet(args, 'network_tags')
      or FlagIsExplicitlySet(args, 'clear_network_tags')
  ):
    network_tags_is_set = FlagIsExplicitlySet(args, 'clear_network_tags')
    network_tags = None
    if FlagIsExplicitlySet(args, 'network_tags'):
      network_tags_is_set = True
      network_tags = args.network_tags
    changes.append(
        config_changes.NetworkInterfacesChange(
            FlagIsExplicitlySet(args, 'network'),
            args.network,
            FlagIsExplicitlySet(args, 'subnet'),
            args.subnet,
            network_tags_is_set,
            network_tags,
        )
    )
  if 'clear_network' in args and args.clear_network:
    # MUST be after 'vpc_egress' change.
    changes.append(config_changes.ClearNetworkInterfacesChange())
  if _HasCustomAudiencesChanges(args):
    changes.append(config_changes.CustomAudiencesChanges(args))

  if FlagIsExplicitlySet(args, 'remove_containers'):
    changes.append(
        config_changes.RemoveContainersChange.FromContainerNames(
            args.remove_containers
        )
    )
    # Add an empty ContainerDependenciesChange to update dependencies.
    changes.append(config_changes.ContainerDependenciesChange())

  if FlagIsExplicitlySet(args, 'containers'):
    for container_name, container_args in args.containers.items():
      changes.extend(
          _GetContainerConfigurationChanges(
              container_args, container_name=container_name
          )
      )

  if FlagIsExplicitlySet(args, 'mesh'):
    if args.mesh:
      changes.append(
          config_changes.SetTemplateAnnotationChange(
              revision.MESH_ANNOTATION, args.mesh
          )
      )
    else:
      changes.append(
          config_changes.DeleteTemplateAnnotationChange(
              revision.MESH_ANNOTATION
          )
      )

  return changes


def _GetContainerConfigurationChanges(container_args, container_name=None):
  """Returns per-container configuration changes."""
  changes = []
  # FlagIsExplicitlySet can't be used here because args.image is also set from
  # code in deploy.py.
  if hasattr(container_args, 'image') and container_args.image is not None:
    changes.append(
        config_changes.ImageChange(
            container_args.image, container_name=container_name
        )
    )
  if _HasEnvChanges(container_args):
    changes.append(
        _GetEnvChanges(container_args, container_name=container_name)
    )
  if container_args.IsSpecified('cpu'):
    changes.append(
        config_changes.ResourceChanges(
            cpu=container_args.cpu, container_name=container_name
        )
    )
  if container_args.IsSpecified('memory'):
    changes.append(
        config_changes.ResourceChanges(
            memory=container_args.memory, container_name=container_name
        )
    )
  if container_args.IsSpecified('command'):
    # Allow passing an empty string here to reset the field
    changes.append(
        config_changes.ContainerCommandChange(
            container_args.command, container_name=container_name
        )
    )
  if container_args.IsSpecified('args'):
    # Allow passing an empty string here to reset the field
    changes.append(
        config_changes.ContainerArgsChange(
            container_args.args, container_name=container_name
        )
    )
  if FlagIsExplicitlySet(
      container_args, 'remove_volume_mount'
  ) or FlagIsExplicitlySet(container_args, 'clear_volume_mounts'):
    changes.append(
        config_changes.RemoveVolumeMountChange(
            removed_mounts=container_args.remove_volume_mount,
            clear_mounts=container_args.clear_volume_mounts,
            container_name=container_name,
        )
    )
  if _HasSecretsChanges(container_args):
    changes.extend(
        _GetSecretsChanges(container_args, container_name=container_name)
    )
  if FlagIsExplicitlySet(container_args, 'add_volume_mount'):
    changes.append(
        config_changes.AddVolumeMountChange(
            new_mounts=container_args.add_volume_mount,
            container_name=container_name,
        )
    )
  return changes


def GetServiceConfigurationChanges(args, release_track=base.ReleaseTrack.GA):
  """Returns a list of changes to the service config, based on the flags set."""
  changes = _GetConfigurationChanges(args, release_track=release_track)

  changes.extend(_GetScalingChanges(args))
  changes.extend(_GetServiceScalingChanges(args))
  if _HasTrafficChanges(args):
    changes.append(_GetTrafficChanges(args))
  if 'no_traffic' in args and args.no_traffic:
    changes.append(config_changes.NoTrafficChange())
  if 'concurrency' in args and args.concurrency:
    changes.append(config_changes.ConcurrencyChanges.FromFlag(args.concurrency))
  if 'timeout' in args and args.timeout:
    changes.append(config_changes.TimeoutChanges(timeout=args.timeout))
  if 'update_annotations' in args and args.update_annotations:
    for key, value in args.update_annotations.items():
      changes.append(config_changes.SetAnnotationChange(key, value))
  if 'revision_suffix' in args and args.revision_suffix:
    changes.append(config_changes.RevisionNameChanges(args.revision_suffix))
  if 'connectivity' in args and args.connectivity:
    if args.connectivity == 'internal':
      changes.append(config_changes.EndpointVisibilityChange(True))
    elif args.connectivity == 'external':
      changes.append(config_changes.EndpointVisibilityChange(False))
  if FlagIsExplicitlySet(args, 'ingress'):
    changes.append(_GetIngressChanges(args))
  if FlagIsExplicitlySet(args, 'port'):
    changes.append(config_changes.ContainerPortChange(port=args.port))
  if FlagIsExplicitlySet(args, 'use_http2'):
    changes.append(config_changes.ContainerPortChange(use_http2=args.use_http2))
  if FlagIsExplicitlySet(args, 'tag'):
    # MUST be after 'revision_suffix' change
    changes.append(config_changes.TagOnDeployChange(args.tag))
  if FlagIsExplicitlySet(args, 'cpu_throttling'):
    changes.append(
        config_changes.CpuThrottlingChange(throttling=args.cpu_throttling)
    )
  if FlagIsExplicitlySet(args, 'cpu_boost'):
    changes.append(
        config_changes.StartupCpuBoostChange(cpu_boost=args.cpu_boost)
    )
  if FlagIsExplicitlySet(args, 'deploy_health_check'):
    changes.append(
        config_changes.HealthCheckChange(health_check=args.deploy_health_check)
    )
  if FlagIsExplicitlySet(args, 'default_url'):
    changes.append(
        config_changes.DefaultUrlChange(default_url=args.default_url)
    )
  if FlagIsExplicitlySet(args, 'invoker_iam_check'):
    changes.append(
        config_changes.InvokerIamChange(
            invoker_iam_check=args.invoker_iam_check
        )
    )
  if FlagIsExplicitlySet(args, 'session_affinity'):
    if args.session_affinity:
      changes.append(
          config_changes.SetTemplateAnnotationChange(
              revision.SESSION_AFFINITY_ANNOTATION,
              str(args.session_affinity).lower(),
          )
      )
    else:
      changes.append(
          config_changes.DeleteTemplateAnnotationChange(
              revision.SESSION_AFFINITY_ANNOTATION
          )
      )
  if FlagIsExplicitlySet(args, 'runtime'):
    changes.append(config_changes.RuntimeChange(runtime=args.runtime))

  if 'gpu_type' in args and args.gpu_type:
    changes.append(config_changes.GpuTypeChange(gpu_type=args.gpu_type))

  _PrependClientNameAndVersionChange(args, changes)

  if FlagIsExplicitlySet(args, 'depends_on'):
    changes.append(
        config_changes.ContainerDependenciesChange({'': args.depends_on})
    )

  if FlagIsExplicitlySet(args, 'containers'):
    for container_name, container_args in args.containers.items():
      changes.extend(
          _GetServiceContainerChanges(container_args, container_name)
      )
    dependency_changes = {
        container_name: container_args.depends_on
        for container_name, container_args in args.containers.items()
        if container_args.IsSpecified('depends_on')
    }
    if dependency_changes:
      changes.append(
          config_changes.ContainerDependenciesChange(dependency_changes)
      )
    base_image_changes = _GetBaseImageChanges(args)
    if base_image_changes:
      changes.extend(base_image_changes)
  return changes


def _GetServiceContainerChanges(container_args, container_name=None):
  """Returns per-container Service changes."""
  changes = []
  if container_args.IsSpecified('port'):
    changes.append(
        config_changes.ContainerPortChange(
            container_name=container_name, port=container_args.port
        )
    )
  if container_args.IsSpecified('use_http2'):
    changes.append(
        config_changes.ContainerPortChange(
            use_http2=container_args.use_http2, container_name=container_name
        )
    )
  return changes


def GetJobConfigurationChanges(args, release_track=base.ReleaseTrack.GA):
  """Returns a list of changes to the job config, based on the flags set."""
  changes = _GetConfigurationChanges(args, release_track=release_track)
  # Deletes existing breakglass annotation first.
  changes.insert(
      0,
      config_changes.DeleteAnnotationChange(
          k8s_object.BINAUTHZ_BREAKGLASS_ANNOTATION
      ),
  )

  if FlagIsExplicitlySet(args, 'parallelism'):
    changes.append(
        config_changes.ExecutionTemplateSpecChange(
            'parallelism', args.parallelism
        )
    )
  if FlagIsExplicitlySet(args, 'tasks'):
    changes.append(
        config_changes.ExecutionTemplateSpecChange('taskCount', args.tasks)
    )
  if FlagIsExplicitlySet(args, 'image'):
    changes.append(config_changes.JobNonceChange())
  if FlagIsExplicitlySet(args, 'max_retries'):
    changes.append(config_changes.JobMaxRetriesChange(args.max_retries))
  if FlagIsExplicitlySet(args, 'task_timeout'):
    changes.append(config_changes.JobTaskTimeoutChange(args.task_timeout))

  _PrependClientNameAndVersionChange(args, changes)

  if FlagIsExplicitlySet(args, 'containers'):
    dependency_changes = {
        container_name: container_args.depends_on
        for container_name, container_args in args.containers.items()
        if container_args.IsSpecified('depends_on')
    }
    if dependency_changes:
      changes.append(
          config_changes.ContainerDependenciesChange(dependency_changes)
      )

  return changes


def GetRunJobConfigurationOverrides(args):
  """Returns a list of overrides to the job config."""
  overrides = []
  if FlagIsExplicitlySet(args, 'update_env_vars'):
    overrides.append(
        config_changes.EnvVarLiteralChanges(
            updates=_StripKeys(getattr(args, 'update_env_vars', None) or {}),
        )
    )
  return overrides


# TODO(b/322180968): There exist a few configurations that are "locked" while
# calling Services API for Workers.
# These will be done in the server side once Worker API is ready.
def GetWorkerConfigurationChanges(args, release_track=base.ReleaseTrack.ALPHA):
  """Returns a list of changes to the worker config, based on the flags set."""
  changes = []
  # ingress = none
  changes.append(
      config_changes.SetAnnotationChange(service.INGRESS_ANNOTATION, 'none')
  )
  # cpu is always on
  changes.append(config_changes.CpuThrottlingChange(throttling=False))
  # healthcheck disabled by default
  changes.append(config_changes.HealthCheckChange(health_check=False))
  # disable default url
  changes.append(config_changes.DefaultUrlChange(default_url=False))
  changes.extend(_GetConfigurationChanges(args, release_track=release_track))
  changes.extend(_GetWorkerScalingChanges(args))
  if _HasTrafficChanges(args):
    changes.append(_GetTrafficChanges(args))
  if 'update_annotations' in args and args.update_annotations:
    for key, value in args.update_annotations.items():
      changes.append(config_changes.SetAnnotationChange(key, value))
  if 'revision_suffix' in args and args.revision_suffix:
    changes.append(config_changes.RevisionNameChanges(args.revision_suffix))
  if 'gpu_type' in args and args.gpu_type:
    changes.append(config_changes.GpuTypeChange(gpu_type=args.gpu_type))

  _PrependClientNameAndVersionChange(args, changes)

  if FlagIsExplicitlySet(args, 'depends_on'):
    changes.append(
        config_changes.ContainerDependenciesChange({'': args.depends_on})
    )

  if FlagIsExplicitlySet(args, 'containers'):
    dependency_changes = {
        container_name: container_args.depends_on
        for container_name, container_args in args.containers.items()
        if container_args.IsSpecified('depends_on')
    }
    if dependency_changes:
      changes.append(
          config_changes.ContainerDependenciesChange(dependency_changes)
      )

  return changes


def ValidateResource(resource_ref):
  """Validate resource name."""
  # Valid resource names comprise only alphanumeric characters and dashes. Must
  # not begin or end with a dash, and must not contain more than 63 characters.
  # Must be lowercase.
  k8s_resource_name_regex = re.compile(
      r'(?=^[a-z0-9-]{1,63}$)(?!^\-.*)(?!.*\-$)'
  )
  if not k8s_resource_name_regex.match(resource_ref.Name()):
    raise serverless_exceptions.ArgumentError(
        'Invalid resource name [{}]. The name must use only lowercase '
        'alphanumeric characters and dashes, cannot begin or end with a dash, '
        'and cannot be longer than 63 characters.'.format(resource_ref.Name())
    )


def PromptForRegion():
  """Prompt for region from list of available regions.

  This method is referenced by the declaritive iam commands as a fallthrough
  for getting the region.

  Returns:
    The region specified by the user, str
  """
  if console_io.CanPrompt():
    client = global_methods.GetServerlessClientInstance()
    all_regions = global_methods.ListRegions(client)
    idx = console_io.PromptChoice(
        all_regions,
        message='Please specify a region:\n',
        cancel_option=True,
        allow_freeform=True,
    )
    region = all_regions[idx]
    log.status.Print(
        'To make this the default region, run '
        '`gcloud config set run/region {}`.\n'.format(region)
    )
    return region


def GetRegion(args, prompt=False, region_label=None):
  """Prompt for region if not provided.

  Region is decided in the following order:
  - region argument;
  - region label
  - run/region gcloud config;
  - prompt user.

  Args:
    args: Namespace, The args namespace.
    prompt: bool, whether to attempt to prompt.
    region_label: a k8s label for the region

  Returns:
    A str representing region.
  """
  if getattr(args, 'region', None):
    return args.region
  if region_label is not None:
    return region_label
  if properties.VALUES.run.region.IsExplicitlySet():
    return properties.VALUES.run.region.Get()
  if prompt:
    region = PromptForRegion()
    if region:
      # set the region on args, so we're not embarassed the next time we call
      # GetRegion
      args.region = region
      return region


def GetAllowUnauthenticated(args, client=None, service_ref=None, prompt=False):
  """Return bool for the explicit intent to allow unauth invocations or None.

  If --[no-]allow-unauthenticated is set, return that value. If not set,
  prompt for value if desired. If prompting not necessary or doable,
  return None, indicating that no action needs to be taken.

  Args:
    args: Namespace, The args namespace
    client: from googlecloudsdk.command_lib.run import serverless_operations
      serverless_operations.ServerlessOperations object
    service_ref: service resource reference (e.g. args.CONCEPTS.service.Parse())
    prompt: bool, whether to attempt to prompt.

  Returns:
    bool indicating whether to allow/unallow unauthenticated or None if N/A
  """
  if getattr(args, 'allow_unauthenticated', None) is not None:
    return args.allow_unauthenticated

  if FlagIsExplicitlySet(args, 'default_url') and not args.default_url:
    return None

  if prompt:
    # Need to check if the user has permissions before we prompt
    assert client is not None and service_ref is not None
    if client.CanSetIamPolicyBinding(service_ref):
      return console_io.PromptContinue(
          prompt_string='Allow unauthenticated invocations to [{}]'.format(
              service_ref.servicesId
          ),
          default=False,
      )
    else:
      pretty_print.Info(
          'This service will require authentication to be invoked.'
      )
  return None


def GetKubeconfig(file_path=None):
  """Get config from kubeconfig file.

  Get config from potentially 3 different places, falling back to the next
  option as necessary:
  1. file_path specified as argument by the user
  2. List of file paths specified in $KUBECONFIG
  3. Default config path (~/.kube/config)

  Args:
    file_path: str, the path to the kubeconfig if provided by the user

  Returns:
    dict: config object

  Raises:
    KubeconfigError: if $KUBECONFIG is set but contains no valid paths
  """
  if file_path:
    return kubeconfig.Kubeconfig.LoadFromFile(files.ExpandHomeDir(file_path))
  if encoding.GetEncodedValue(os.environ, 'KUBECONFIG'):
    config_paths = encoding.GetEncodedValue(os.environ, 'KUBECONFIG').split(
        os.pathsep
    )
    kube_config = None
    # Merge together all valid paths into single config
    for path in config_paths:
      try:
        other_config = kubeconfig.Kubeconfig.LoadFromFile(
            files.ExpandHomeDir(path)
        )
        if not kube_config:
          kube_config = other_config
        else:
          kube_config.Merge(other_config)
      except kubeconfig.Error:
        pass
    if not kube_config:
      raise KubeconfigError('No valid file paths found in $KUBECONFIG')
    return kube_config
  return kubeconfig.Kubeconfig.LoadFromFile(
      files.ExpandHomeDir(_DEFAULT_KUBECONFIG_PATH)
  )


def FlagIsExplicitlySet(args, flag):
  """Return True if --flag is explicitly passed by the user."""
  # hasattr check is to allow the same code to work for release tracks that
  # don't have the args at all yet.
  return hasattr(args, flag) and args.IsSpecified(flag)


def VerifyManagedFlags(args, release_track, product):
  """Raise ConfigurationError if args aren't valid for managed Cloud Run."""

  if product == Product.EVENTS:
    raise serverless_exceptions.ConfigurationError(
        'The flag --platform={0} is not supported. '
        'Instead of using the flag --platform={0} in "gcloud events", '
        'run "gcloud eventarc".'.format(platforms.PLATFORM_MANAGED)
    )

  error_msg = (
      'The `{flag}` flag is not supported on the fully managed '
      'version of Cloud Run. Specify `--platform {platform}` or run '
      '`gcloud config set run/platform {platform}` to work with '
      '{platform_desc}.'
  )

  if FlagIsExplicitlySet(args, 'connectivity'):
    raise serverless_exceptions.ConfigurationError(
        error_msg.format(
            flag='--connectivity=[internal|external]',
            platform=platforms.PLATFORM_GKE,
            platform_desc=platforms.PLATFORM_SHORT_DESCRIPTIONS[
                platforms.PLATFORM_GKE
            ],
        )
    )

  if FlagIsExplicitlySet(args, 'namespace'):
    raise serverless_exceptions.ConfigurationError(
        error_msg.format(
            flag='--namespace',
            platform=platforms.PLATFORM_GKE,
            platform_desc=platforms.PLATFORM_SHORT_DESCRIPTIONS[
                platforms.PLATFORM_GKE
            ],
        )
    )

  if FlagIsExplicitlySet(args, 'cluster'):
    raise serverless_exceptions.ConfigurationError(
        error_msg.format(
            flag='--cluster',
            platform=platforms.PLATFORM_GKE,
            platform_desc=platforms.PLATFORM_SHORT_DESCRIPTIONS[
                platforms.PLATFORM_GKE
            ],
        )
    )

  if FlagIsExplicitlySet(args, 'cluster_location'):
    raise serverless_exceptions.ConfigurationError(
        error_msg.format(
            flag='--cluster-location',
            platform=platforms.PLATFORM_GKE,
            platform_desc=platforms.PLATFORM_SHORT_DESCRIPTIONS[
                platforms.PLATFORM_GKE
            ],
        )
    )

  if _HasConfigMapsChanges(args):
    raise serverless_exceptions.ConfigurationError(
        error_msg.format(
            flag='--[update|set|remove|clear]-config-maps',
            platform=platforms.PLATFORM_GKE,
            platform_desc=platforms.PLATFORM_SHORT_DESCRIPTIONS[
                platforms.PLATFORM_GKE
            ],
        )
    )

  if FlagIsExplicitlySet(args, 'broker'):
    raise serverless_exceptions.ConfigurationError(
        error_msg.format(
            flag='--broker',
            platform=platforms.PLATFORM_GKE,
            platform_desc=platforms.PLATFORM_SHORT_DESCRIPTIONS[
                platforms.PLATFORM_GKE
            ],
        )
    )

  if FlagIsExplicitlySet(args, 'custom_type') and product == Product.EVENTS:
    raise serverless_exceptions.ConfigurationError(
        error_msg.format(
            flag='--custom-type',
            platform=platforms.PLATFORM_GKE,
            platform_desc=platforms.PLATFORM_SHORT_DESCRIPTIONS[
                platforms.PLATFORM_GKE
            ],
        )
    )

  if FlagIsExplicitlySet(args, 'kubeconfig'):
    raise serverless_exceptions.ConfigurationError(
        error_msg.format(
            flag='--kubeconfig',
            platform=platforms.PLATFORM_KUBERNETES,
            platform_desc=platforms.PLATFORM_SHORT_DESCRIPTIONS[
                platforms.PLATFORM_KUBERNETES
            ],
        )
    )

  if FlagIsExplicitlySet(args, 'context'):
    raise serverless_exceptions.ConfigurationError(
        error_msg.format(
            flag='--context',
            platform=platforms.PLATFORM_KUBERNETES,
            platform_desc=platforms.PLATFORM_SHORT_DESCRIPTIONS[
                platforms.PLATFORM_KUBERNETES
            ],
        )
    )

  if FlagIsExplicitlySet(args, 'trigger_filters'):
    raise serverless_exceptions.ConfigurationError(
        error_msg.format(
            flag='--trigger-filters',
            platform=platforms.PLATFORM_GKE,
            platform_desc=platforms.PLATFORM_SHORT_DESCRIPTIONS[
                platforms.PLATFORM_GKE
            ],
        )
    )


def VerifyGKEFlags(args, release_track, product):
  """Raise ConfigurationError if args includes OnePlatform only arguments."""
  error_msg = (
      'The `{flag}` flag is not supported with Cloud Run for Anthos '
      'deployed on Google Cloud. Specify `--platform {platform}` or '
      'run `gcloud config set run/platform {platform}` to work with '
      '{platform_desc}.'
  )

  if FlagIsExplicitlySet(args, 'allow_unauthenticated'):
    raise serverless_exceptions.ConfigurationError(
        'The `--[no-]allow-unauthenticated` flag is not supported with '
        'Cloud Run for Anthos deployed on Google Cloud. All deployed '
        'services allow unauthenticated requests. The `--connectivity` '
        'flag can limit which network a service is available on to reduce '
        'access.'
    )

  if FlagIsExplicitlySet(args, 'connectivity') and FlagIsExplicitlySet(
      args, 'ingress'
  ):
    raise serverless_exceptions.ConfigurationError(
        'Cannot specify both the `--connectivity` and `--ingress` flags.'
        ' `--connectivity` is deprecated in favor of `--ingress`.'
    )

  if FlagIsExplicitlySet(args, 'region'):
    raise serverless_exceptions.ConfigurationError(
        error_msg.format(
            flag='--region',
            platform=platforms.PLATFORM_MANAGED,
            platform_desc=platforms.PLATFORM_SHORT_DESCRIPTIONS[
                platforms.PLATFORM_MANAGED
            ],
        )
    )

  if FlagIsExplicitlySet(args, 'execution_environment'):
    raise serverless_exceptions.ConfigurationError(
        error_msg.format(
            flag='--execution-environment',
            platform=platforms.PLATFORM_MANAGED,
            platform_desc=platforms.PLATFORM_SHORT_DESCRIPTIONS[
                platforms.PLATFORM_MANAGED
            ],
        )
    )

  if FlagIsExplicitlySet(args, 'vpc_connector'):
    raise serverless_exceptions.ConfigurationError(
        error_msg.format(
            flag='--vpc-connector',
            platform=platforms.PLATFORM_MANAGED,
            platform_desc=platforms.PLATFORM_SHORT_DESCRIPTIONS[
                platforms.PLATFORM_MANAGED
            ],
        )
    )

  if FlagIsExplicitlySet(args, 'clear_vpc_connector'):
    raise serverless_exceptions.ConfigurationError(
        error_msg.format(
            flag='--clear-vpc-connector',
            platform=platforms.PLATFORM_MANAGED,
            platform_desc=platforms.PLATFORM_SHORT_DESCRIPTIONS[
                platforms.PLATFORM_MANAGED
            ],
        )
    )

  if FlagIsExplicitlySet(args, 'vpc_egress'):
    raise serverless_exceptions.ConfigurationError(
        error_msg.format(
            flag='--vpc-egress',
            platform=platforms.PLATFORM_MANAGED,
            platform_desc=platforms.PLATFORM_SHORT_DESCRIPTIONS[
                platforms.PLATFORM_MANAGED
            ],
        )
    )

  if FlagIsExplicitlySet(args, 'binary_authorization'):
    raise serverless_exceptions.ConfigurationError(
        error_msg.format(
            flag='--binary-authorization',
            platform=platforms.PLATFORM_MANAGED,
            platform_desc=platforms.PLATFORM_SHORT_DESCRIPTIONS[
                platforms.PLATFORM_MANAGED
            ],
        )
    )

  if FlagIsExplicitlySet(args, 'clear_binary_authorization'):
    raise serverless_exceptions.ConfigurationError(
        error_msg.format(
            flag='--clear-binary-authorization',
            platform=platforms.PLATFORM_MANAGED,
            platform_desc=platforms.PLATFORM_SHORT_DESCRIPTIONS[
                platforms.PLATFORM_MANAGED
            ],
        )
    )

  if FlagIsExplicitlySet(args, 'breakglass'):
    raise serverless_exceptions.ConfigurationError(
        error_msg.format(
            flag='--breakglass',
            platform=platforms.PLATFORM_MANAGED,
            platform_desc=platforms.PLATFORM_SHORT_DESCRIPTIONS[
                platforms.PLATFORM_MANAGED
            ],
        )
    )

  if FlagIsExplicitlySet(args, 'network'):
    raise serverless_exceptions.ConfigurationError(
        error_msg.format(
            flag='--network',
            platform=platforms.PLATFORM_MANAGED,
            platform_desc=platforms.PLATFORM_SHORT_DESCRIPTIONS[
                platforms.PLATFORM_MANAGED
            ],
        )
    )

  if FlagIsExplicitlySet(args, 'subnet'):
    raise serverless_exceptions.ConfigurationError(
        error_msg.format(
            flag='--subnet',
            platform=platforms.PLATFORM_MANAGED,
            platform_desc=platforms.PLATFORM_SHORT_DESCRIPTIONS[
                platforms.PLATFORM_MANAGED
            ],
        )
    )

  if FlagIsExplicitlySet(args, 'network-tags'):
    raise serverless_exceptions.ConfigurationError(
        error_msg.format(
            flag='--network-tags',
            platform=platforms.PLATFORM_MANAGED,
            platform_desc=platforms.PLATFORM_SHORT_DESCRIPTIONS[
                platforms.PLATFORM_MANAGED
            ],
        )
    )

  if FlagIsExplicitlySet(args, 'key'):
    raise serverless_exceptions.ConfigurationError(
        error_msg.format(
            flag='--key',
            platform=platforms.PLATFORM_MANAGED,
            platform_desc=platforms.PLATFORM_SHORT_DESCRIPTIONS[
                platforms.PLATFORM_MANAGED
            ],
        )
    )

  if FlagIsExplicitlySet(args, 'post_key_revocation_action_type'):
    raise serverless_exceptions.ConfigurationError(
        error_msg.format(
            flag='--post-key-revocation-action-type',
            platform=platforms.PLATFORM_MANAGED,
            platform_desc=platforms.PLATFORM_SHORT_DESCRIPTIONS[
                platforms.PLATFORM_MANAGED
            ],
        )
    )

  if FlagIsExplicitlySet(args, 'encryption_key_shutdown_hours'):
    raise serverless_exceptions.ConfigurationError(
        error_msg.format(
            flag='--encryption-key-shutdown-hours',
            platform=platforms.PLATFORM_MANAGED,
            platform_desc=platforms.PLATFORM_SHORT_DESCRIPTIONS[
                platforms.PLATFORM_MANAGED
            ],
        )
    )

  if FlagIsExplicitlySet(args, 'clear_key'):
    raise serverless_exceptions.ConfigurationError(
        error_msg.format(
            flag='--clear-key',
            platform=platforms.PLATFORM_MANAGED,
            platform_desc=platforms.PLATFORM_SHORT_DESCRIPTIONS[
                platforms.PLATFORM_MANAGED
            ],
        )
    )

  if FlagIsExplicitlySet(args, 'clear_post_key_revocation_action_type'):
    raise serverless_exceptions.ConfigurationError(
        error_msg.format(
            flag='--clear-post-key-revocation-action-type',
            platform=platforms.PLATFORM_MANAGED,
            platform_desc=platforms.PLATFORM_SHORT_DESCRIPTIONS[
                platforms.PLATFORM_MANAGED
            ],
        )
    )

  if FlagIsExplicitlySet(args, 'clear_encryption_key_shutdown_hours'):
    raise serverless_exceptions.ConfigurationError(
        error_msg.format(
            flag='--clear-encryption-key-shutdown-hours',
            platform=platforms.PLATFORM_MANAGED,
            platform_desc=platforms.PLATFORM_SHORT_DESCRIPTIONS[
                platforms.PLATFORM_MANAGED
            ],
        )
    )

  if FlagIsExplicitlySet(args, 'set_custom_audiences'):
    raise serverless_exceptions.ConfigurationError(
        error_msg.format(
            flag='--set-custom-audiences',
            platform=platforms.PLATFORM_MANAGED,
            platform_desc=platforms.PLATFORM_SHORT_DESCRIPTIONS[
                platforms.PLATFORM_MANAGED
            ],
        )
    )

  if FlagIsExplicitlySet(args, 'add_custom_audiences'):
    raise serverless_exceptions.ConfigurationError(
        error_msg.format(
            flag='--add-custom-audiences',
            platform=platforms.PLATFORM_MANAGED,
            platform_desc=platforms.PLATFORM_SHORT_DESCRIPTIONS[
                platforms.PLATFORM_MANAGED
            ],
        )
    )

  if FlagIsExplicitlySet(args, 'remove_custom_audiences'):
    raise serverless_exceptions.ConfigurationError(
        error_msg.format(
            flag='--remove-custom-audiences',
            platform=platforms.PLATFORM_MANAGED,
            platform_desc=platforms.PLATFORM_SHORT_DESCRIPTIONS[
                platforms.PLATFORM_MANAGED
            ],
        )
    )

  if FlagIsExplicitlySet(args, 'clear_custom_audiences'):
    raise serverless_exceptions.ConfigurationError(
        error_msg.format(
            flag='--clear-custom-audiences',
            platform=platforms.PLATFORM_MANAGED,
            platform_desc=platforms.PLATFORM_SHORT_DESCRIPTIONS[
                platforms.PLATFORM_MANAGED
            ],
        )
    )

  if FlagIsExplicitlySet(args, 'session_affinity'):
    raise serverless_exceptions.ConfigurationError(
        error_msg.format(
            flag='--session-affinity',
            platform=platforms.PLATFORM_MANAGED,
            platform_desc=platforms.PLATFORM_SHORT_DESCRIPTIONS[
                platforms.PLATFORM_MANAGED
            ],
        )
    )

  if FlagIsExplicitlySet(args, 'kubeconfig'):
    raise serverless_exceptions.ConfigurationError(
        error_msg.format(
            flag='--kubeconfig',
            platform=platforms.PLATFORM_KUBERNETES,
            platform_desc=platforms.PLATFORM_SHORT_DESCRIPTIONS[
                platforms.PLATFORM_KUBERNETES
            ],
        )
    )

  if FlagIsExplicitlySet(args, 'context'):
    raise serverless_exceptions.ConfigurationError(
        error_msg.format(
            flag='--context',
            platform=platforms.PLATFORM_KUBERNETES,
            platform_desc=platforms.PLATFORM_SHORT_DESCRIPTIONS[
                platforms.PLATFORM_KUBERNETES
            ],
        )
    )

  if FlagIsExplicitlySet(args, 'add_volume'):
    raise serverless_exceptions.ConfigurationError(
        error_msg.format(
            flag='--add-volume',
            platform=platforms.PLATFORM_MANAGED,
            platform_desc=platforms.PLATFORM_SHORT_DESCRIPTIONS[
                platforms.PLATFORM_MANAGED
            ],
        )
    )


def VerifyKubernetesFlags(args, release_track, product):
  """Raise ConfigurationError if args includes OnePlatform or GKE only arguments."""
  error_msg = (
      'The `{flag}` flag is not supported with Cloud Run for Anthos '
      'deployed on VMware. Specify `--platform {platform}` or run '
      '`gcloud config set run/platform {platform}` to work with '
      '{platform_desc}.'
  )

  if FlagIsExplicitlySet(args, 'allow_unauthenticated'):
    raise serverless_exceptions.ConfigurationError(
        'The `--[no-]allow-unauthenticated` flag is not supported with '
        'Cloud Run for Anthos deployed on VMware. All deployed '
        'services allow unauthenticated requests. The `--connectivity` '
        'flag can limit which network a service is available on to reduce '
        'access.'
    )

  if FlagIsExplicitlySet(args, 'connectivity') and FlagIsExplicitlySet(
      args, 'ingress'
  ):
    raise serverless_exceptions.ConfigurationError(
        'Cannot specify both the `--connectivity` and `--ingress` flags.'
        ' `--connectivity` is deprecated in favor of `--ingress`.'
    )

  if FlagIsExplicitlySet(args, 'region'):
    raise serverless_exceptions.ConfigurationError(
        error_msg.format(
            flag='--region',
            platform=platforms.PLATFORM_MANAGED,
            platform_desc=platforms.PLATFORM_SHORT_DESCRIPTIONS[
                platforms.PLATFORM_MANAGED
            ],
        )
    )

  if FlagIsExplicitlySet(args, 'execution_environment'):
    raise serverless_exceptions.ConfigurationError(
        error_msg.format(
            flag='--execution-environment',
            platform=platforms.PLATFORM_MANAGED,
            platform_desc=platforms.PLATFORM_SHORT_DESCRIPTIONS[
                platforms.PLATFORM_MANAGED
            ],
        )
    )

  if FlagIsExplicitlySet(args, 'vpc_connector'):
    raise serverless_exceptions.ConfigurationError(
        error_msg.format(
            flag='--vpc-connector',
            platform='managed',
            platform_desc=platforms.PLATFORM_SHORT_DESCRIPTIONS['managed'],
        )
    )

  if FlagIsExplicitlySet(args, 'clear_vpc_connector'):
    raise serverless_exceptions.ConfigurationError(
        error_msg.format(
            flag='--clear-vpc-connector',
            platform=platforms.PLATFORM_MANAGED,
            platform_desc=platforms.PLATFORM_SHORT_DESCRIPTIONS[
                platforms.PLATFORM_MANAGED
            ],
        )
    )

  if FlagIsExplicitlySet(args, 'vpc_egress'):
    raise serverless_exceptions.ConfigurationError(
        error_msg.format(
            flag='--vpc-egress',
            platform=platforms.PLATFORM_MANAGED,
            platform_desc=platforms.PLATFORM_SHORT_DESCRIPTIONS[
                platforms.PLATFORM_MANAGED
            ],
        )
    )

  if FlagIsExplicitlySet(args, 'binary_authorization'):
    raise serverless_exceptions.ConfigurationError(
        error_msg.format(
            flag='--binary-authorization',
            platform=platforms.PLATFORM_MANAGED,
            platform_desc=platforms.PLATFORM_SHORT_DESCRIPTIONS[
                platforms.PLATFORM_MANAGED
            ],
        )
    )

  if FlagIsExplicitlySet(args, 'clear_binary_authorization'):
    raise serverless_exceptions.ConfigurationError(
        error_msg.format(
            flag='--clear-binary-authorization',
            platform=platforms.PLATFORM_MANAGED,
            platform_desc=platforms.PLATFORM_SHORT_DESCRIPTIONS[
                platforms.PLATFORM_MANAGED
            ],
        )
    )

  if FlagIsExplicitlySet(args, 'breakglass'):
    raise serverless_exceptions.ConfigurationError(
        error_msg.format(
            flag='--breakglass',
            platform=platforms.PLATFORM_MANAGED,
            platform_desc=platforms.PLATFORM_SHORT_DESCRIPTIONS[
                platforms.PLATFORM_MANAGED
            ],
        )
    )

  if FlagIsExplicitlySet(args, 'key'):
    raise serverless_exceptions.ConfigurationError(
        error_msg.format(
            flag='--key',
            platform=platforms.PLATFORM_MANAGED,
            platform_desc=platforms.PLATFORM_SHORT_DESCRIPTIONS[
                platforms.PLATFORM_MANAGED
            ],
        )
    )

  if FlagIsExplicitlySet(args, 'post_key_revocation_action_type'):
    raise serverless_exceptions.ConfigurationError(
        error_msg.format(
            flag='--post-key-revocation-action-type',
            platform=platforms.PLATFORM_MANAGED,
            platform_desc=platforms.PLATFORM_SHORT_DESCRIPTIONS[
                platforms.PLATFORM_MANAGED
            ],
        )
    )

  if FlagIsExplicitlySet(args, 'encryption_key_shutdown_hours'):
    raise serverless_exceptions.ConfigurationError(
        error_msg.format(
            flag='--encryption-key-shutdown-hours',
            platform=platforms.PLATFORM_MANAGED,
            platform_desc=platforms.PLATFORM_SHORT_DESCRIPTIONS[
                platforms.PLATFORM_MANAGED
            ],
        )
    )

  if FlagIsExplicitlySet(args, 'clear_key'):
    raise serverless_exceptions.ConfigurationError(
        error_msg.format(
            flag='--clear-key',
            platform=platforms.PLATFORM_MANAGED,
            platform_desc=platforms.PLATFORM_SHORT_DESCRIPTIONS[
                platforms.PLATFORM_MANAGED
            ],
        )
    )

  if FlagIsExplicitlySet(args, 'clear_post_key_revocation_action_type'):
    raise serverless_exceptions.ConfigurationError(
        error_msg.format(
            flag='--clear-post-key-revocation-action-type',
            platform=platforms.PLATFORM_MANAGED,
            platform_desc=platforms.PLATFORM_SHORT_DESCRIPTIONS[
                platforms.PLATFORM_MANAGED
            ],
        )
    )

  if FlagIsExplicitlySet(args, 'clear_encryption_key_shutdown_hours'):
    raise serverless_exceptions.ConfigurationError(
        error_msg.format(
            flag='--clear-encryption-key-shutdown-hours',
            platform=platforms.PLATFORM_MANAGED,
            platform_desc=platforms.PLATFORM_SHORT_DESCRIPTIONS[
                platforms.PLATFORM_MANAGED
            ],
        )
    )

  if FlagIsExplicitlySet(args, 'set_custom_audiences'):
    raise serverless_exceptions.ConfigurationError(
        error_msg.format(
            flag='--set-custom-audiences',
            platform=platforms.PLATFORM_MANAGED,
            platform_desc=platforms.PLATFORM_SHORT_DESCRIPTIONS[
                platforms.PLATFORM_MANAGED
            ],
        )
    )

  if FlagIsExplicitlySet(args, 'add_custom_audiences'):
    raise serverless_exceptions.ConfigurationError(
        error_msg.format(
            flag='--add-custom-audiences',
            platform=platforms.PLATFORM_MANAGED,
            platform_desc=platforms.PLATFORM_SHORT_DESCRIPTIONS[
                platforms.PLATFORM_MANAGED
            ],
        )
    )

  if FlagIsExplicitlySet(args, 'remove_custom_audiences'):
    raise serverless_exceptions.ConfigurationError(
        error_msg.format(
            flag='--remove-custom-audiences',
            platform=platforms.PLATFORM_MANAGED,
            platform_desc=platforms.PLATFORM_SHORT_DESCRIPTIONS[
                platforms.PLATFORM_MANAGED
            ],
        )
    )

  if FlagIsExplicitlySet(args, 'clear_custom_audiences'):
    raise serverless_exceptions.ConfigurationError(
        error_msg.format(
            flag='--clear-custom-audiences',
            platform=platforms.PLATFORM_MANAGED,
            platform_desc=platforms.PLATFORM_SHORT_DESCRIPTIONS[
                platforms.PLATFORM_MANAGED
            ],
        )
    )

  if FlagIsExplicitlySet(args, 'session_affinity'):
    raise serverless_exceptions.ConfigurationError(
        error_msg.format(
            flag='--session-affinity',
            platform=platforms.PLATFORM_MANAGED,
            platform_desc=platforms.PLATFORM_SHORT_DESCRIPTIONS[
                platforms.PLATFORM_MANAGED
            ],
        )
    )

  if FlagIsExplicitlySet(args, 'cluster'):
    raise serverless_exceptions.ConfigurationError(
        error_msg.format(
            flag='--cluster',
            platform=platforms.PLATFORM_GKE,
            platform_desc=platforms.PLATFORM_SHORT_DESCRIPTIONS[
                platforms.PLATFORM_GKE
            ],
        )
    )

  if FlagIsExplicitlySet(args, 'cluster_location'):
    raise serverless_exceptions.ConfigurationError(
        error_msg.format(
            flag='--cluster-location',
            platform=platforms.PLATFORM_GKE,
            platform_desc=platforms.PLATFORM_SHORT_DESCRIPTIONS[
                platforms.PLATFORM_GKE
            ],
        )
    )

  if FlagIsExplicitlySet(args, 'add_volume'):
    raise serverless_exceptions.ConfigurationError(
        error_msg.format(
            flag='--add-volume',
            platform=platforms.PLATFORM_MANAGED,
            platform_desc=platforms.PLATFORM_SHORT_DESCRIPTIONS[
                platforms.PLATFORM_MANAGED
            ],
        )
    )


def GetAndValidatePlatform(args, release_track, product):
  """Returns the platform to run on and validates specified flags.

  A given command may support multiple platforms, but not every flag is
  supported by every platform. This method validates that all specified flags
  are supported by the specified platform.

  Args:
    args: Namespace, The args namespace.
    release_track: base.ReleaseTrack, calliope release track.
    product: Product, which product the command was executed for (e.g. Run or
      Events).

  Raises:
    ArgumentError if an unknown platform type is found.
  """
  platform = platforms.GetPlatform()
  if platform == platforms.PLATFORM_MANAGED:
    VerifyManagedFlags(args, release_track, product)
  elif platform == platforms.PLATFORM_GKE:
    VerifyGKEFlags(args, release_track, product)
  elif platform == platforms.PLATFORM_KUBERNETES:
    VerifyKubernetesFlags(args, release_track, product)
  if platform not in platforms.PLATFORMS:
    raise serverless_exceptions.ArgumentError(
        'Invalid target platform specified: [{}].\n'
        'Available platforms:\n{}'.format(
            platform,
            '\n'.join([
                '- {}: {}'.format(k, v) for k, v in platforms.PLATFORMS.items()
            ]),
        )
    )
  return platform


def AddTaskFilterFlags(parser):
  """Add filter flags for task list."""
  parser.add_argument(
      '--succeeded',
      action='append_const',
      dest='filter_flags',
      const='Succeeded',
      help='Include succeeded tasks.',
  )
  parser.add_argument(
      '--failed',
      action='append_const',
      dest='filter_flags',
      const='Failed',
      help='Include failed tasks.',
  )
  parser.add_argument(
      '--cancelled',
      action='append_const',
      dest='filter_flags',
      const='Cancelled',
      help='Include cancelled tasks.',
  )
  parser.add_argument(
      '--running',
      action='append_const',
      dest='filter_flags',
      const='Running',
      help='Include running tasks.',
  )
  parser.add_argument(
      '--abandoned',
      action='append_const',
      dest='filter_flags',
      const='Abandoned',
      help='Include abandoned tasks.',
  )
  parser.add_argument(
      '--pending',
      action='append_const',
      dest='filter_flags',
      const='Pending',
      help='Include pending tasks.',
  )
  parser.add_argument(
      '--completed',
      action=arg_parsers.ExtendConstAction,
      dest='filter_flags',
      const=['Succeeded', 'Failed', 'Cancelled'],
      help='Include succeeded, failed, and cancelled tasks.',
  )
  parser.add_argument(
      '--no-completed',
      action=arg_parsers.ExtendConstAction,
      dest='filter_flags',
      const=['Running', 'Pending'],
      help='Include running and pending tasks.',
  )
  parser.add_argument(
      '--started',
      action=arg_parsers.ExtendConstAction,
      dest='filter_flags',
      const=['Succeeded', 'Failed', 'Cancelled', 'Running'],
      help='Include running, succeeded, failed, and cancelled tasks.',
  )
  parser.add_argument(
      '--no-started',
      action=arg_parsers.ExtendConstAction,
      dest='filter_flags',
      const=['Pending', 'Abandoned'],
      help='Include pending and abandoned tasks.',
  )


def AddExecuteNowFlag(parser):
  """Add --execute-now flag for Job creation or update."""
  parser.add_argument(
      '--execute-now',
      action='store_true',
      help='Execute the job immediately after the creation or update '
      + ' completes. gcloud exits once the job has started unless the '
      + '`--wait` flag is set.',
  )


def SourceArg():
  return base.Argument(
      '--source',
      help=(
          'The location of the source to build. If a Dockerfile is present in'
          ' the source code directory, it will be built using that Dockerfile,'
          ' otherwise it will use Google Cloud buildpacks. See'
          ' https://cloud.google.com/run/docs/deploying-source-code for more'
          ' details. The location can be a directory on a local disk or a'
          ' gzipped archive file (.tar.gz) in Google Cloud Storage. If the'
          ' source is a local directory, this command skips the files specified'
          ' in the `--ignore-file`. If `--ignore-file` is not specified, use'
          ' `.gcloudignore` file. If a `.gcloudignore` file is absent and a'
          ' `.gitignore` file is present in the local source directory, gcloud'
          ' will use a generated Git-compatible `.gcloudignore` file that'
          ' respects your .gitignored files. The global `.gitignore` is not'
          ' respected. For more information on `.gcloudignore`, see `gcloud'
          ' topic gcloudignore`.'
      ),
  )


def AddSourceAndImageFlags(parser, image='gcr.io/cloudrun/hello:latest'):
  """Add deploy source flags, an image or a source for build."""
  SourceAndImageFlags(image=image).AddToParser(parser)


def SourceAndImageFlags(image='gcr.io/cloudrun/hello:latest'):
  group = base.ArgumentGroup(mutex=True)
  group.AddArgument(ImageArg(required=False, image=image))
  group.AddArgument(SourceArg())
  return group


def ContainerFlag():
  """Create a dummy --container flag for usage."""

  help_text = """
  Specifies a container by name. Flags following --container will apply to the specified container.
  """
  return base.Argument(
      '--container',
      metavar='CONTAINER',
      dest='containers',
      help=help_text,
  )


def RemoveContainersFlag():
  return base.Argument(
      '--remove-containers',
      action=arg_parsers.UpdateAction,
      type=arg_parsers.ArgList(element_type=_CONTAINER_NAME_TYPE, max_length=9),
      metavar='CONTAINER',
      help='List of containers to remove.',
  )


def DependsOnFlag():
  return base.Argument(
      '--depends-on',
      action=arg_parsers.UpdateAction,
      type=arg_parsers.ArgList(element_type=_CONTAINER_NAME_TYPE, max_length=9),
      metavar='CONTAINER',
      help='List of container dependencies to add to the current container.',
  )


def PromptForDefaultSource(container_name=None):
  """Prompt for source code location when image flag is not set.

  Returns:
    The source code location
  Args:
    container_name: The name of the container to prompt for.
  """
  if console_io.CanPrompt():
    pretty_print.Info(
        'Deploying from source. To deploy a container use [--image]. '
        'See https://cloud.google.com/run/docs/deploying-source-code '
        'for more details.'
    )
    cwd = files.GetCWD()
    if container_name:
      message = 'Source code location for {container}'.format(
          container=container_name
      )
    else:
      message = 'Source code location'
    source = console_io.PromptWithDefault(message=message, default=cwd)

    log.status.Print(
        'Next time, use `gcloud run deploy --source .` '
        'to deploy the current directory.\n'
    )
    return source


def PromptForClearCommand():
  """Prompt for clearing --command when user tries to deploy function to CR."""
  if console_io.CanPrompt():
    message = (
        'Deploying a function to Cloud Run has the effect of removing any value'
        ' previously set for --command in the same container.'
    )
    return console_io.PromptContinue(
        message=message,
        default=False,
    )
  return False


def AddDryRunFlag(parser):
  """Add --dry-run flag."""
  parser.add_argument(
      '--dry-run',
      action='store_true',
      default=False,
      help=(
          'If set to true, only validates the configuration. The configuration'
          ' will not be applied.'
      ),
  )


def FunctionArg():
  """Specify that the deployed resource is a function."""
  return base.Argument(
      '--function',
      hidden=True,
      help=(
          'Specifies that the deployed object is a function. If a value'
          ' is provided, that value is used as the entrypoint.'
      ),
  )


# TODO(b/312784518) link to/list supported values
def BaseImageArg():
  """Adds automatic base image update related flags."""
  group = base.ArgumentGroup(mutex=True, hidden=True)
  group.AddArgument(
      base.Argument(
          '--base-image',
          hidden=True,
          help=(
              'Opts in to use automatic base image updates using the specified'
              ' image.'
          ),
      )
  )
  group.AddArgument(
      base.Argument(
          '--clear-base-image',
          action='store_true',
          hidden=True,
          help='Opts out of use of automatic base image updates.',
      )
  )
  return group


def AddCommandAndFunctionFlag():
  """Add --function and --command flag, which are mutually exclusive."""
  group = base.ArgumentGroup(mutex=True)
  group.AddArgument(FunctionArg())
  group.AddArgument(CommandFlag())
  return group
