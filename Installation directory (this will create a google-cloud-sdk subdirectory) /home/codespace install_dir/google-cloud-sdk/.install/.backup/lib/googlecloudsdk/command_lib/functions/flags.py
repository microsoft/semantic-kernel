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
"""Helpers for flags in commands working with Google Cloud Functions."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import json

from argcomplete.completers import DirectoriesCompleter
from googlecloudsdk.api_lib.functions.v1 import util as api_util
from googlecloudsdk.api_lib.functions.v2 import client as client_v2
from googlecloudsdk.calliope import actions
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.calliope.concepts import concepts
from googlecloudsdk.calliope.concepts import deps
from googlecloudsdk.command_lib.eventarc import flags as eventarc_flags
from googlecloudsdk.command_lib.util import completers
from googlecloudsdk.command_lib.util.concepts import concept_parsers
from googlecloudsdk.command_lib.util.concepts import presentation_specs
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources
from googlecloudsdk.core.console import console_io
import six

API = 'cloudfunctions'
API_VERSION = 'v1'
LOCATIONS_COLLECTION = API + '.projects.locations'

SIGNATURE_TYPES = ['http', 'event', 'cloudevent']
SEVERITIES = ['DEBUG', 'INFO', 'ERROR']
EGRESS_SETTINGS = ['PRIVATE-RANGES-ONLY', 'ALL']
INGRESS_SETTINGS = ['ALL', 'INTERNAL-ONLY', 'INTERNAL-AND-GCLB']
SECURITY_LEVEL = ['SECURE-ALWAYS', 'SECURE-OPTIONAL']
INGRESS_SETTINGS_MAPPING = {
    'ALLOW_ALL': 'all',
    'ALLOW_INTERNAL_ONLY': 'internal-only',
    'ALLOW_INTERNAL_AND_GCLB': 'internal-and-gclb',
}

EGRESS_SETTINGS_MAPPING = {
    'PRIVATE_RANGES_ONLY': 'private-ranges-only',
    'ALL_TRAFFIC': 'all',
}

SECURITY_LEVEL_MAPPING = {
    'SECURE_ALWAYS': 'secure-always',
    'SECURE_OPTIONAL': 'secure-optional',
}

_KMS_KEY_NAME_PATTERN = (
    r'^projects/[^/]+/locations/[^/]+/keyRings/[a-zA-Z0-9_-]+'
    '/cryptoKeys/[a-zA-Z0-9_-]+$'
)
_KMS_KEY_NAME_ERROR = (
    'KMS key name should match projects/{project}/locations/{location}'
    '/keyRings/{keyring}/cryptoKeys/{cryptokey} and only contain characters '
    'from the valid character set for a KMS key.'
)
_DOCKER_REPOSITORY_NAME_RESOURCE_PATTERN = (
    r'^projects/[^/]+/locations/[^/]+/repositories/[a-z]([a-z0-9-]*[a-z0-9])?$'
)
_DOCKER_REPOSITORY_NAME_PKG_PATTERN = (
    r'^(?P<location>.*)-docker.pkg.dev\/(?P<project>[^\/]+)\/(?P<repo>[^\/]+)'
)
_DOCKER_REPOSITORY_NAME_PATTERN = '({}|{})'.format(
    _DOCKER_REPOSITORY_NAME_RESOURCE_PATTERN,
    _DOCKER_REPOSITORY_NAME_PKG_PATTERN,
)
_DOCKER_REPOSITORY_NAME_ERROR = (
    'Docker repository name should match'
    ' `projects/{project}/locations/{location}/repositories/{repository}` or'
    ' `{location}-docker.pkg.dev/{project}/{repository}` and only contain'
    ' characters from the valid character set for a repository.'
)

DOCKER_REGISTRY_MAPPING = {
    'CONTAINER_REGISTRY': 'container-registry',
    'ARTIFACT_REGISTRY': 'artifact-registry',
}

RUNTIME_UPDATE_POLICY_MAPPING = {
    'AUTOMATIC': 'automatic',
    'ON_DEPLOY': 'on-deploy',
}


def AddMinLogLevelFlag(parser):
  min_log_arg = base.ChoiceArgument(
      '--min-log-level',
      choices=[x.lower() for x in SEVERITIES],
      help_str='Minimum level of logs to be fetched.',
  )
  min_log_arg.AddToParser(parser)


def AddIngressSettingsFlag(parser):
  ingress_settings_arg = base.ChoiceArgument(
      '--ingress-settings',
      choices=[x.lower() for x in INGRESS_SETTINGS],
      help_str=(
          'Ingress settings controls what traffic can reach the '
          'function. By default `all` will be used.'
      ),
  )
  ingress_settings_arg.AddToParser(parser)


def AddEgressSettingsFlag(parser):
  egress_settings_arg = base.ChoiceArgument(
      '--egress-settings',
      choices=[x.lower() for x in EGRESS_SETTINGS],
      help_str=(
          'Egress settings controls what traffic is diverted through the '
          'VPC Access Connector resource. '
          'By default `private-ranges-only` will be used.'
      ),
  )
  egress_settings_arg.AddToParser(parser)


def AddSecurityLevelFlag(parser):
  security_level_arg = base.ChoiceArgument(
      '--security-level',
      default='secure-always',
      choices=[x.lower() for x in SECURITY_LEVEL],
      help_str=(
          "Security level controls whether a function's URL supports "
          'HTTPS only or both HTTP and HTTPS. By default, `secure-always` will'
          ' be used, meaning only HTTPS is supported.'
      ),
  )
  security_level_arg.AddToParser(parser)


def GetLocationsUri(resource):
  registry = resources.REGISTRY.Clone()
  registry.RegisterApiByName(API, API_VERSION)
  ref = registry.Parse(
      resource.name,
      params={'projectsId': properties.VALUES.core.project.GetOrFail},
      collection=LOCATIONS_COLLECTION,
  )
  return ref.SelfLink()


def AddFunctionMemoryAndCpuFlags(parser):
  """Add flags for specifying function memory and cpu to the parser."""

  memory_help_text = """\
  Limit on the amount of memory the function can use.

  Allowed values for v1 are: 128MB, 256MB, 512MB, 1024MB, 2048MB, 4096MB,
  and 8192MB.

  Allowed values for GCF 2nd gen are in the format: <number><unit> with allowed units
  of "k", "M", "G", "Ki", "Mi", "Gi". Ending 'b' or 'B' is allowed.

  Examples: 100000k, 128M, 10Mb, 1024Mi, 750K, 4Gi.

  By default, a new function is limited to 256MB of memory. When
  deploying an update to an existing function, the function keeps its old
  memory limit unless you specify this flag."""
  group = parser.add_group(required=False)
  cpu_help_text = """\
    The number of available CPUs to set. Only valid when `--gen2`
    and `--memory=MEMORY` are specified.

    Examples: .5, 2, 2.0, 2000m.

    By default, a new function's available CPUs is determined based on its memory value.

    When deploying an update that includes memory changes to an existing function,
    the function's available CPUs will be recalculated based on the new memory unless this flag
    is specified. When deploying an update that does not include memory changes to an existing function,
    the function's "available CPUs" setting will keep its old value unless you use this flag
    to change the setting.
    """
  group.add_argument('--memory', type=str, help=memory_help_text, required=True)
  group.add_argument('--cpu', help=cpu_help_text)


def ParseMemoryStrToNumBytes(binary_size):
  """Parse binary size to number of bytes.

  Args:
    binary_size: str, memory with size suffix

  Returns:
    num_bytes: int, the number of bytes
  """

  binary_size_parser = arg_parsers.BinarySize(
      suggested_binary_size_scales=['KB', 'MB', 'MiB', 'GB', 'GiB'],
      default_unit='MB',
  )
  return binary_size_parser(binary_size)


def ValidateV1TimeoutFlag(args):
  if args.timeout and args.timeout > 540:
    raise arg_parsers.ArgumentTypeError(
        '--timeout: value must be less than or equal to 540s; received: {}s'
        .format(args.timeout)
    )


def AddFunctionTimeoutFlag(parser):
  """Add flag for specifying function timeout to the parser.

  Args:
    parser: the argparse parser for the command.

  Returns:
    None
  """

  help_text = """\
      The function execution timeout, e.g. 30s for 30 seconds. Defaults to
      original value for existing function or 60 seconds for new functions.

      For GCF 1st gen functions, cannot be more than 540s.

      For GCF 2nd gen functions, cannot be more than 3600s.

      See $ gcloud topic datetimes for information on duration formats."""

  parser.add_argument(
      '--timeout', help=help_text, type=arg_parsers.Duration(lower_bound='1s')
  )


def AddFunctionRetryFlag(parser):
  """Add flag for specifying function retry behavior to the parser."""
  parser.add_argument(
      '--retry',
      help=(
          'If specified, then the function will be retried in case of a '
          'failure.'
      ),
      action='store_true',
  )


def AddAllowUnauthenticatedFlag(parser):
  """Add the --allow-unauthenticated flag."""
  parser.add_argument(
      '--allow-unauthenticated',
      action=arg_parsers.StoreTrueFalseAction,
      help=(
          'If set, makes this a public function. This will allow all '
          'callers, without checking authentication.'
      ),
  )


def AddServeAllTrafficLatestRevisionFlag(parser):
  help_text = (
      'If specified, latest function revision will be served all traffic. '
      'This is only relevant when `--gen2` is provided.'
  )
  parser.add_argument(
      '--serve-all-traffic-latest-revision',
      action='store_true',
      default=False,
      help=help_text,
  )


def AddBuildpackStackFlag(parser):
  """Add flag for specifying function memory to the parser."""
  # TODO(b/211892283): refer to Buildpack stacks guide, once it is available
  help_text = """\
  Specifies one of the Google provided buildpack stacks.
  """
  parser.add_argument('--buildpack-stack', type=str, help=help_text)


def AddGen2Flag(
    parser, operates_on_existing_function=True, hidden=False, allow_v2=False
):
  """Add the --gen2 flag."""
  help_text = (
      'If enabled, this command will use Cloud Functions (Second generation).'
      ' If disabled with `--no-gen2`, Cloud Functions (First generation) will'
      ' be used. If not specified, the value of this flag will be taken from'
      ' the `functions/gen2` configuration property.'
  )
  if operates_on_existing_function:
    help_text += (
        ' If the `functions/gen2` configuration property is not set, defaults'
        ' to looking up the given function and using its generation.'
    )
  if allow_v2:
    help_text += (
        ' This command could conflict with `--v2`. If specified `--gen2`'
        ' with `--no-v2`, or `--no-gen2` with `--v2`, Second generation will be'
        ' used.'
    )
  parser.add_argument(
      '--gen2',
      default=False,
      action=actions.StoreBooleanProperty(properties.VALUES.functions.gen2),
      help=help_text,
      hidden=hidden,
  )


def ShouldUseGen2():
  """Returns whether 2nd gen should be used for Cloud Functions."""
  return bool(properties.VALUES.functions.gen2.GetBool())


def ShouldUseGen1():
  """Returns whether 1st gen should be used for Cloud Functions."""
  return (
      properties.VALUES.functions.gen2.IsExplicitlySet() and not ShouldUseGen2()
  )


def ShouldEnsureAllUsersInvoke(args):
  return args.allow_unauthenticated


def ShouldDenyAllUsersInvoke(args):
  return (
      args.IsSpecified('allow_unauthenticated')
      and not args.allow_unauthenticated
  )


def AddV2Flag(parser):
  """Add the --v2 flag."""
  help_text = (
      'If specified, this command will use Cloud Functions v2 APIs and return'
      ' the result in the v2 format (See'
      ' https://cloud.google.com/functions/docs/reference/rest/v2/projects.locations.functions#Function).'
      ' If not specified, 1st gen and 2nd gen functions will use v1 and v2 APIs'
      ' respectively and return the result in the corresponding format (For v1'
      ' format, see'
      ' https://cloud.google.com/functions/docs/reference/rest/v1/projects.locations.functions#resource:-cloudfunction).'
      ' This command conflicts with `--no-gen2`. If specified with this'
      ' combination, v2 APIs will be used.'
  )
  parser.add_argument(
      '--v2',
      action='store_true',
      default=None,
      help=help_text,
  )


def AddSourceFlag(parser):
  """Add flag for specifying function source code to the parser."""
  parser.add_argument(
      '--source',
      completer=DirectoriesCompleter,
      help="""\
      Location of source code to deploy.

      Location of the source can be one of the following three options:

      * Source code in Google Cloud Storage (must be a `.zip` archive),
      * Reference to source repository or,
      * Local filesystem path (root directory of function source).

      Note that, depending on your runtime type, Cloud Functions will look
      for files with specific names for deployable functions. For Node.js,
      these filenames are `index.js` or `function.js`. For Python, this is
      `main.py`.

      If you do not specify the `--source` flag:

      * The current directory will be used for new function deployments.
      * If the function was previously deployed using a local filesystem path,
      then the function's source code will be updated using the current
      directory.
      * If the function was previously deployed using a Google Cloud Storage
      location or a source repository, then the function's source code will not
      be updated.

      The value of the flag will be interpreted as a Cloud Storage location, if
      it starts with `gs://`.

      The value will be interpreted as a reference to a source repository, if it
      starts with `https://`.

      Otherwise, it will be interpreted as the local filesystem path. When
      deploying source from the local filesystem, this command skips files
      specified in the `.gcloudignore` file (see `gcloud topic gcloudignore` for
      more information). If the `.gcloudignore` file doesn't exist, the command
      will try to create it.

      The minimal source repository URL is:
      `https://source.developers.google.com/projects/${PROJECT}/repos/${REPO}`

      By using the URL above, sources from the root directory of the
      repository on the revision tagged `master` will be used.

      If you want to deploy from a revision different from `master`, append one
      of the following three sources to the URL:

      * `/revisions/${REVISION}`,
      * `/moveable-aliases/${MOVEABLE_ALIAS}`,
      * `/fixed-aliases/${FIXED_ALIAS}`.

      If you'd like to deploy sources from a directory different from the root,
      you must specify a revision, a moveable alias, or a fixed alias, as above,
      and append `/paths/${PATH_TO_SOURCES_DIRECTORY}` to the URL.

      Overall, the URL should match the following regular expression:

      ```
      ^https://source\\.developers\\.google\\.com/projects/
      (?<accountId>[^/]+)/repos/(?<repoName>[^/]+)
      (((/revisions/(?<commit>[^/]+))|(/moveable-aliases/(?<branch>[^/]+))|
      (/fixed-aliases/(?<tag>[^/]+)))(/paths/(?<path>.*))?)?$
      ```

      An example of a validly formatted source repository URL is:

      ```
      https://source.developers.google.com/projects/123456789/repos/testrepo/
      moveable-aliases/alternate-branch/paths/path-to=source
      ```

      """,
  )


def AddStageBucketFlag(parser):
  """Add flag for specifying stage bucket to the parser."""
  parser.add_argument(
      '--stage-bucket',
      help=(
          "When deploying a function from a local directory, this flag's "
          'value is the name of the Google Cloud Storage bucket in which '
          'source code will be stored. Note that if you set the '
          '`--stage-bucket` flag when deploying a function, you will need to '
          'specify `--source` or `--stage-bucket` in subsequent deployments '
          'to update your source code. To use this flag successfully, the '
          'account in use must have permissions to write to this bucket. For '
          'help granting access, refer to this guide: '
          'https://cloud.google.com/storage/docs/access-control/'
      ),
      type=api_util.ValidateAndStandarizeBucketUriOrRaise,
  )


def AddRuntimeFlag(parser):
  parser.add_argument(
      '--runtime',
      help="""\
          Runtime in which to run the function.

          Required when deploying a new function; optional when updating
          an existing function.

          For a list of available runtimes, run `gcloud functions runtimes list`.
          """,
  )


def GetVpcConnectorResourceSpec():
  return concepts.ResourceSpec(
      'vpcaccess.projects.locations.connectors',
      resource_name='connector',
      disable_auto_completers=False,
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
      locationsId=RegionAttributeConfig(),
      connectorsId=VpcConnectorAttributeConfig(),
  )


def AddVPCConnectorMutexGroup(parser):
  """Add flag for specifying VPC connector to the parser."""
  mutex_group = parser.add_group(mutex=True)
  resource = presentation_specs.ResourcePresentationSpec(
      '--vpc-connector',
      GetVpcConnectorResourceSpec(),
      """\
        The VPC Access connector that the function can connect to. It can be
        either the fully-qualified URI, or the short name of the VPC Access
        connector resource. If the short name is used, the connector must
        belong to the same project. The format of this field is either
        `projects/${PROJECT}/locations/${LOCATION}/connectors/${CONNECTOR}`
        or `${CONNECTOR}`, where `${CONNECTOR}` is the short name of the VPC
        Access connector.
      """,
      group=mutex_group,
      # This hides the region flag for the connector resource.
      flag_name_overrides={'region': ''},
  )

  concept_parsers.ConceptParser(
      [resource],
      # This configures the fallthrough from the vpc-connector's region to
      # the primary flag for the function's region.
      command_level_fallthroughs={'--vpc-connector.region': ['--region']},
  ).AddToParser(parser)

  mutex_group.add_argument(
      '--clear-vpc-connector',
      action='store_true',
      help="""\
        Clears the VPC connector field.
      """,
  )


def AddBuildWorkerPoolMutexGroup(parser):
  """Add flag for specifying Build Worker Pool to the parser."""
  mutex_group = parser.add_group(mutex=True)
  mutex_group.add_argument(
      '--build-worker-pool',
      help="""\
        Name of the Cloud Build Custom Worker Pool that should be used to build
        the function. The format of this field is
        `projects/${PROJECT}/locations/${LOCATION}/workerPools/${WORKERPOOL}`
        where ${PROJECT} is the project id and ${LOCATION} is the location where
        the worker pool is defined and ${WORKERPOOL} is the short name of the
        worker pool.
      """,
  )
  mutex_group.add_argument(
      '--clear-build-worker-pool',
      action='store_true',
      help="""\
        Clears the Cloud Build Custom Worker Pool field.
      """,
  )


def AddEntryPointFlag(parser):
  """Add flag for specifying entry point to the parser."""
  parser.add_argument(
      '--entry-point',
      help="""\
      Name of a Google Cloud Function (as defined in source code) that will
      be executed. Defaults to the resource name suffix (ID of the function), if
       not specified.
""",
  )


def AddMaxInstancesFlag(parser):
  """Add flag for specifying the max instances for a function."""
  mutex_group = parser.add_group(mutex=True)
  mutex_group.add_argument(
      '--max-instances',
      type=arg_parsers.BoundedInt(lower_bound=1),
      help="""\
        Sets the maximum number of instances for the function. A function
        execution that would exceed max-instances times out.
      """,
  )
  mutex_group.add_argument(
      '--clear-max-instances',
      action='store_true',
      help="""\
        Clears the maximum instances setting for the function.
      """,
  )


def AddMinInstancesFlag(parser):
  """Add flag for specifying the min instances for a function."""
  mutex_group = parser.add_group(mutex=True)
  mutex_group.add_argument(
      '--min-instances',
      type=arg_parsers.BoundedInt(lower_bound=0),
      help="""\
        Sets the minimum number of instances for the function. This is helpful
        for reducing cold start times. Defaults to zero.
      """,
  )
  mutex_group.add_argument(
      '--clear-min-instances',
      action='store_true',
      help="""\
        Clears the minimum instances setting for the function.
      """,
  )


def AddTriggerFlagGroup(parser):
  """Add arguments specifying functions trigger to the parser.

  Args:
    parser: the argparse parser for the command.
  """
  trigger_group = parser.add_mutually_exclusive_group(help="""\
      If you don't specify a trigger when deploying an update to an existing
      function it will keep its current trigger. You must specify one of the
      following when deploying a new function:
      - `--trigger-topic`,
      - `--trigger-bucket`,
      - `--trigger-http`,
      - `--trigger-event` AND `--trigger-resource`,
      - `--trigger-event-filters` and optionally `--trigger-event-filters-path-pattern`.
      """)
  trigger_group.add_argument(
      '--trigger-topic',
      help=(
          'Name of Pub/Sub topic. Every message published in this topic '
          'will trigger function execution with message contents passed as '
          'input data. Note that this flag does not accept the format of '
          'projects/PROJECT_ID/topics/TOPIC_ID. Use this flag to specify the '
          'final element TOPIC_ID. The PROJECT_ID will be read from the '
          'active configuration.'
      ),
      type=api_util.ValidatePubsubTopicNameOrRaise,
  )
  trigger_group.add_argument(
      '--trigger-bucket',
      help=(
          'Google Cloud Storage bucket name. Trigger the function when an '
          'object is created or overwritten in the specified Cloud Storage '
          'bucket.'
      ),
      type=api_util.ValidateAndStandarizeBucketUriOrRaise,
  )
  trigger_group.add_argument(
      '--trigger-http',
      action='store_true',
      help="""\
      Function will be assigned an endpoint, which you can view by using
      the `describe` command. Any HTTP request (of a supported type) to the
      endpoint will trigger function execution. Supported HTTP request
      types are: POST, PUT, GET, DELETE, and OPTIONS.""",
  )
  eventarc_trigger_group = trigger_group.add_argument_group()
  concept_parsers.ConceptParser(
      [
          presentation_specs.ResourcePresentationSpec(
              '--trigger-channel',
              eventarc_flags.ChannelResourceSpec(),
              """\
              The channel to use in the trigger for third-party event sources.
              This is only relevant when `--gen2` is provided.""",
              flag_name_overrides={'location': ''},
              group=eventarc_trigger_group,
              hidden=True,
          )
      ],
      command_level_fallthroughs={
          '--trigger-channel.location': ['--trigger-location'],
      },
  ).AddToParser(parser)
  eventarc_trigger_group.add_argument(
      '--trigger-event-filters',
      type=arg_parsers.ArgDict(),
      action=arg_parsers.UpdateAction,
      metavar='ATTRIBUTE=VALUE',
      help="""\
      The Eventarc matching criteria for the trigger. The criteria can be
      specified either as a single comma-separated argument or as multiple
      arguments. The filters must include the ``type'' attribute, as well as any
      other attributes that are expected for the chosen type. This is only
      relevant when `--gen2` is provided.
      """,
  )
  eventarc_trigger_group.add_argument(
      '--trigger-event-filters-path-pattern',
      type=arg_parsers.ArgDict(),
      action=arg_parsers.UpdateAction,
      metavar='ATTRIBUTE=PATH_PATTERN',
      help="""\
      The Eventarc matching criteria for the trigger in path pattern format.
      The criteria can be specified as a single comma-separated argument or as
      multiple arguments. This is only relevant when `--gen2` is provided.

      The provided attribute/value pair will be used with the
      `match-path-pattern` operator to configure the trigger, see
      https://cloud.google.com/eventarc/docs/reference/rest/v1/projects.locations.triggers#eventfilter
      and https://cloud.google.com/eventarc/docs/path-patterns for more details about on
      how to construct path patterns.

      For example, to filter on events for Compute Engine VMs in a given zone:
      `--trigger-event-filters-path-pattern=resourceName='/projects/*/zones/us-central1-a/instances/*'""",
  )

  trigger_provider_spec_group = trigger_group.add_argument_group()
  # check later as type of applicable input depends on options above
  trigger_provider_spec_group.add_argument(
      '--trigger-event',
      metavar='EVENT_TYPE',
      help=(
          'Specifies which action should trigger the function. For a '
          'list of acceptable values, call '
          '`gcloud functions event-types list`.'
      ),
  )
  trigger_provider_spec_group.add_argument(
      '--trigger-resource',
      metavar='RESOURCE',
      help=(
          'Specifies which resource from `--trigger-event` is being '
          'observed. E.g. if `--trigger-event` is  '
          '`providers/cloud.storage/eventTypes/object.change`, '
          '`--trigger-resource` must be a bucket name. For a list of '
          'expected resources, call '
          '`gcloud functions event-types list`.'
      ),
  )


class LocationsCompleter(completers.ListCommandCompleter):

  def __init__(self, **kwargs):
    super(LocationsCompleter, self).__init__(
        collection=LOCATIONS_COLLECTION,
        list_command='alpha functions regions list --uri',
        **kwargs,
    )


class RegionFallthrough(deps.PropertyFallthrough):
  """Custom fallthrough for region dependent on GCF generation.

  For GCF gen1 this falls back to the functions/region property.

  For GCF gen2 the property fallback is only used if it is explicitly set.
  Otherwise the region is prompted for.
  """

  def __init__(self, release_track=base.ReleaseTrack.ALPHA):
    super(RegionFallthrough, self).__init__(properties.VALUES.functions.region)
    self.release_track = release_track

  def _Call(self, parsed_args):
    use_gen1 = not ShouldUseGen2()
    if use_gen1 or self.property.IsExplicitlySet():
      return super(RegionFallthrough, self)._Call(parsed_args)

    if not console_io.CanPrompt():
      raise exceptions.RequiredArgumentException(
          'region',
          (
              'You must specify a region. Either use the flag `--region` or set'
              ' the functions/region property.'
          ),
      )

    client = client_v2.FunctionsClient(self.release_track)
    regions = [l.locationId for l in client.ListRegions()]
    idx = console_io.PromptChoice(regions, message='Please specify a region:\n')
    region = regions[idx]
    log.status.Print(
        'To make this the default region, run '
        '`gcloud config set functions/region {}`.\n'.format(region)
    )

    return region


def AddRegionFlag(parser, help_text):
  parser.add_argument(
      '--region',
      help=help_text,
      completer=LocationsCompleter,
      action=actions.StoreProperty(properties.VALUES.functions.region),
  )


def RegionAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='region',
      help_text=(
          'The Cloud region for the {resource}. Overrides the default '
          '`functions/region` property value for this command invocation.'
      ),
      completer=LocationsCompleter,
      fallthroughs=[RegionFallthrough()],
  )


def AddTriggerLocationFlag(parser):
  """Add flag for specifying trigger location to the parser."""
  parser.add_argument(
      '--trigger-location',
      help=(
          'The location of the trigger, which must be a region or multi-'
          'region where the relevant events originate. This is only '
          'relevant when `--gen2` is provided.'
      ),
      completer=LocationsCompleter,
  )


def FunctionAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='function',
      help_text='The name of the {resource}.',
      value_type=api_util.ValidateFunctionNameOrRaise,
  )


def VpcConnectorAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='connector',
      help_text='The name of the {resource}.',
  )


def GetFunctionResourceSpec():
  return concepts.ResourceSpec(
      'cloudfunctions.projects.locations.functions',
      resource_name='function',
      disable_auto_completers=False,
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
      locationsId=RegionAttributeConfig(),
      functionsId=FunctionAttributeConfig(),
  )


def AddFunctionResourceArg(parser, verb, required=True):
  """Adds a Cloud function resource argument.

  NOTE: May be used only if it's the only resource arg in the command.

  Args:
    parser: the argparse parser for the command.
    verb: str, the verb to describe the resource, such as 'to update'.
    required: bool, whether the argument is required.
  """
  concept_parsers.ConceptParser.ForResource(
      'NAME',
      GetFunctionResourceSpec(),
      'The Cloud function name {}.'.format(verb),
      required=required,
  ).AddToParser(parser)


def AddServiceAccountFlag(parser):
  parser.add_argument(
      '--service-account',
      help="""\
      The email address of the IAM service account associated with the
      function at runtime. The service account represents the identity of the
      running function, and determines what permissions the function has.

      If not provided, the function will use the project's default service
      account.
      """,
  )


def AddRunServiceAccountFlag(parser):
  parser.add_argument(
      '--run-service-account',
      help="""\
      The email address of the IAM service account associated with the Cloud
      Run service for the function. The service account represents the identity
      of the running function, and determines what permissions the function
      has.

      If not provided, the function will use the project's default service
      account for Compute Engine.

      This is only relevant when `--gen2` is provided.
      """,
  )


def AddTriggerServiceAccountFlag(parser):
  parser.add_argument(
      '--trigger-service-account',
      help="""\
      The email address of the IAM service account associated with the Eventarc
      trigger for the function. This is used for authenticated invocation.

      If not provided, the function will use the project's default service
      account for Compute Engine.

      This is only relevant when `--gen2` is provided.
      """,
  )


def AddDataFlag(parser):
  parser.add_argument(
      '--data',
      help="""JSON string with data that will be passed to the function.""",
      type=_ValidateJsonOrRaiseDataError,
  )


def AddCloudEventsFlag(parser):
  parser.add_argument(
      '--cloud-event',
      help="""
      JSON encoded string with a CloudEvent in structured content mode.

      Mutually exclusive with --data flag.

      Use for Cloud Functions 2nd Gen CloudEvent functions. The CloudEvent
      object will be sent to your function as a binary content mode message with
      the top-level 'data' field set as the HTTP body and all other JSON fields
      sent as HTTP headers.
      """,
      type=_ValidateJsonOrRaiseCloudEventError,
  )


def AddGcloudHttpTimeoutFlag(parser):
  """Add flag for specifying gcloud timeout to the parser."""

  help_text = """\
      The gcloud command timeout, e.g. 30s for 30 seconds. Defaults to the
      function execution timeout duration of the function.

      See $ gcloud topic datetimes for information on duration formats."""
  parser.add_argument(
      '--timeout',
      help=help_text,
      type=arg_parsers.Duration(lower_bound='1s'),
      hidden=True,
  )


def AddIAMPolicyFileArg(parser):
  parser.add_argument(
      'policy_file',
      metavar='POLICY_FILE',
      help=(
          'Path to a local JSON or YAML formatted file '
          'containing a valid policy.'
      ),
  )


def AddIgnoreFileFlag(parser):
  parser.add_argument(
      '--ignore-file',
      help=(
          'Override the .gcloudignore file and use the specified file instead.'
      ),
  )


# Flags for Runtime Updates
def AddRuntimeUpdatePolicy(parser, track):
  """Adds flags for selecting the runtime update policy."""
  if track in (
      base.ReleaseTrack.ALPHA,
      base.ReleaseTrack.BETA,
      base.ReleaseTrack.GA,
  ):
    parser.add_argument(
        '--runtime-update-policy',
        help="""\
        Runtime update policy for the 1st Gen function being deployed.
        The option `on-deploy` is used by default.
      """,
    )


# Flags for Artifact Registry
def AddDockerRegistryFlags(parser):
  """Adds flags for selecting the Docker registry type for Cloud Function."""
  docker_registry_arg = base.ChoiceArgument(
      '--docker-registry',
      choices=sorted(DOCKER_REGISTRY_MAPPING.values()),
      help_str="""\
        Docker Registry to use for storing the function's Docker images.
        The option `artifact-registry` is used by default.

        Warning: Artifact Registry and Container Registry have different image
        storage costs. For more details, please see
        https://cloud.google.com/functions/pricing#deployment_costs
      """,
  )
  docker_registry_arg.AddToParser(parser)


# Flags for CMEK
def AddKMSKeyFlags(parser):
  """Adds flags for configuring the CMEK key."""
  kmskey_group = parser.add_group(mutex=True)
  kmskey_group.add_argument(
      '--kms-key',
      type=arg_parsers.RegexpValidator(
          _KMS_KEY_NAME_PATTERN, _KMS_KEY_NAME_ERROR
      ),
      help="""\
        Sets the user managed KMS crypto key used to encrypt the Cloud Function
        and its resources.

        The KMS crypto key name should match the pattern
        `projects/${PROJECT}/locations/${LOCATION}/keyRings/${KEYRING}/cryptoKeys/${CRYPTOKEY}`
        where ${PROJECT} is the project, ${LOCATION} is the location of the key
        ring, and ${KEYRING} is the key ring that contains the ${CRYPTOKEY}
        crypto key.

        If this flag is set, then a Docker repository created in Artifact
        Registry must be specified using the `--docker-repository` flag and the
        repository must be encrypted using the `same` KMS key.
      """,
  )
  kmskey_group.add_argument(
      '--clear-kms-key',
      action='store_true',
      help="""\
        Clears the KMS crypto key used to encrypt the function.
      """,
  )


def AddDockerRepositoryFlags(parser):
  """Adds flags for configuring the Docker repository for Cloud Function."""
  kmskey_group = parser.add_group(mutex=True)
  kmskey_group.add_argument(
      '--docker-repository',
      type=arg_parsers.RegexpValidator(
          _DOCKER_REPOSITORY_NAME_PATTERN, _DOCKER_REPOSITORY_NAME_ERROR
      ),
      help="""\
        Sets the Docker repository to be used for storing the Cloud Function's
        Docker images while the function is being deployed. `DOCKER_REPOSITORY`
        must be an Artifact Registry Docker repository present in the `same`
        project and location as the Cloud Function.

        The repository name should match one of these patterns:

        * `projects/${PROJECT}/locations/${LOCATION}/repositories/${REPOSITORY}`,
        * `{LOCATION}-docker.pkg.dev/{PROJECT}/{REPOSITORY}`.

        where `${PROJECT}` is the project, `${LOCATION}` is the location of the
        repository and `${REPOSITORY}` is a valid repository ID.
      """,
  )
  kmskey_group.add_argument(
      '--clear-docker-repository',
      action='store_true',
      help="""\
        Clears the Docker repository configuration of the function.
      """,
  )


def AddConcurrencyFlag(parser):
  parser.add_argument(
      '--concurrency',
      type=arg_parsers.BoundedInt(lower_bound=1, upper_bound=1000),
      help=(
          'Set the maximum number of concurrent requests allowed per'
          ' container instance. Leave concurrency unspecified to receive the'
          ' server default value. Only applicable when the `--gen2` flag is'
          ' provided.'
      ),
  )


def AddUpgradeFlags(parser):
  """Adds upgrade related function flags."""
  upgrade_group = parser.add_group(mutex=True)
  upgrade_group.add_argument(
      '--setup-config',
      action='store_true',
      help=(
          'Sets up the function upgrade config by creating a 2nd gen copy of'
          " the function's code and configuration."
      ),
  )
  upgrade_group.add_argument(
      '--redirect-traffic',
      action='store_true',
      help='Redirects production traffic to the 2nd gen copy of the function.',
  )
  upgrade_group.add_argument(
      '--rollback-traffic',
      action='store_true',
      help=(
          'Rolls back production traffic to the original 1st gen copy of the'
          ' function. The 2nd gen copy will still be available for testing.'
      ),
  )
  upgrade_group.add_argument(
      '--commit',
      action='store_true',
      help=(
          'Finishes the upgrade process and permanently deletes the original'
          ' 1st gen copy of the function.'
      ),
  )
  upgrade_group.add_argument(
      '--abort',
      action='store_true',
      help=(
          'Undoes all steps of the upgrade process done so far. All traffic'
          ' will point to the original 1st gen function copy and the 2nd gen'
          ' function copy will be deleted.'
      ),
  )


def _ValidateJsonOrRaiseDataError(data):
  return _ValidateJsonOrRaiseError(data, '--data')


def _ValidateJsonOrRaiseCloudEventError(data):
  return _ValidateJsonOrRaiseError(data, '--cloud-event')


def _ValidateJsonOrRaiseError(data, arg_name):
  """Checks validity of json string or raises an InvalidArgumentException."""
  try:
    json.loads(data)
    return data
  except ValueError as e:
    raise exceptions.InvalidArgumentException(
        arg_name, 'Is not a valid JSON: ' + six.text_type(e)
    )


def AddBuildServiceAccountFlag(parser, track):
  if track in (base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA):
    parser.add_argument(
        '--build-service-account',
        help="""\
            IAM service account whose credentials will be used for the build step.
            Must be of the format projects/${PROJECT_ID}/serviceAccounts/${ACCOUNT_EMAIL_ADDRESS}.

            If not provided, the function will use the project's default
            service account for Cloud Build.
        """,
    )
