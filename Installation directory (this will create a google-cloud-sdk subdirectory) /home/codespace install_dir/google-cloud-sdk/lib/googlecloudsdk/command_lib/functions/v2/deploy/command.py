# -*- coding: utf-8 -*- #
# Copyright 2021 Google LLC. All Rights Reserved.
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
"""This file provides the implementation of the `functions deploy` command."""


import re
import types
from typing import FrozenSet, Optional, Tuple

from apitools.base.py import base_api
from apitools.base.py import exceptions as apitools_exceptions
from googlecloudsdk.api_lib.functions import api_enablement
from googlecloudsdk.api_lib.functions import cmek_util
from googlecloudsdk.api_lib.functions import secrets as secrets_util
from googlecloudsdk.api_lib.functions.v1 import util as api_util_v1
from googlecloudsdk.api_lib.functions.v2 import client as client_v2
from googlecloudsdk.api_lib.functions.v2 import exceptions
from googlecloudsdk.api_lib.functions.v2 import types as api_types
from googlecloudsdk.api_lib.functions.v2 import util as api_util
from googlecloudsdk.api_lib.storage import storage_util
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.calliope import exceptions as calliope_exceptions
from googlecloudsdk.calliope import parser_extensions
from googlecloudsdk.calliope.arg_parsers import ArgumentTypeError
from googlecloudsdk.command_lib.eventarc import types as trigger_types
from googlecloudsdk.command_lib.functions import flags
from googlecloudsdk.command_lib.functions import labels_util
from googlecloudsdk.command_lib.functions import run_util
from googlecloudsdk.command_lib.functions import secrets_config
from googlecloudsdk.command_lib.functions import source_util
from googlecloudsdk.command_lib.functions.v2 import deploy_util
from googlecloudsdk.command_lib.projects import util as projects_util
from googlecloudsdk.command_lib.run import serverless_operations
from googlecloudsdk.command_lib.util.apis import arg_utils
from googlecloudsdk.command_lib.util.args import map_util
from googlecloudsdk.core import exceptions as core_exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core import resources
from googlecloudsdk.core.console import console_io
from googlecloudsdk.core.console import progress_tracker
from googlecloudsdk.core.util import files as file_utils

_SIGNED_URL_UPLOAD_ERROR_MESSSAGE = (
    'There was a problem uploading the source code to a signed Cloud Storage '
    'URL. Please try again.'
)

_GCS_SOURCE_REGEX = re.compile('gs://([^/]+)/(.*)')
_GCS_SOURCE_ERROR_MESSAGE = (
    'Invalid Cloud Storage URL. Must match the following format: '
    'gs://bucket/object'
)

# https://cloud.google.com/functions/docs/reference/rest/v1/projects.locations.functions#sourcerepository
_CSR_SOURCE_REGEX = re.compile(
    # Minimally required fields
    r'https://source\.developers\.google\.com'
    r'/projects/(?P<project_id>[^/]+)/repos/(?P<repo_name>[^/]+)'
    # Optional oneof revision/alias
    r'(((/revisions/(?P<commit>[^/]+))|'
    r'(/moveable-aliases/(?P<branch>[^/]+))|'
    r'(/fixed-aliases/(?P<tag>[^/]+)))'
    # Optional path
    r'(/paths/(?P<path>[^/]+))?)?'
    # Optional ending forward slash and enforce regex matches end of string
    r'/?$'
)
_CSR_SOURCE_ERROR_MESSAGE = (
    'Invalid Cloud Source Repository URL provided. Must match the '
    'following format: https://source.developers.google.com/projects/'
    '<projectId>/repos/<repoName>. Specify the desired branch by appending '
    '/moveable-aliases/<branchName>, the desired tag with '
    '/fixed-aliases/<tagName>, or the desired commit with /revisions/<commit>. '
)

_INVALID_RETRY_FLAG_ERROR_MESSAGE = (
    '`--retry` is only supported with an event trigger not http triggers.'
)

_LATEST_REVISION_TRAFFIC_WARNING_MESSAGE = (
    'The latest revision of this function is not serving 100% of traffic. '
    'Please see the associated Cloud Run service to '
    'confirm your expected traffic settings.'
)

_V1_ONLY_FLAGS = [
    # Legacy flags
    ('docker_registry', '--docker-registry'),
    ('security_level', '--security-level'),
    # Not yet supported flags
    ('buildpack_stack', '--buildpack-stack'),
]
_V1_ONLY_FLAG_ERROR = (
    '`%s` is only supported in Cloud Functions (First generation).'
)

_DEPLOYMENT_TOOL_LABEL = 'deployment-tool'
_DEPLOYMENT_TOOL_VALUE = 'cli-gcloud'

# Extra progress tracker stages that can appear during rollbacks.
# cs/symbol:google.cloud.functions.v2main.Stage.Name
_ARTIFACT_REGISTRY_STAGE = progress_tracker.Stage(
    '[ArtifactRegistry]', key='ARTIFACT_REGISTRY'
)
_SERVICE_ROLLBACK_STAGE = progress_tracker.Stage(
    '[Healthcheck]', key='SERVICE_ROLLBACK'
)
_TRIGGER_ROLLBACK_STAGE = progress_tracker.Stage(
    '[Triggercheck]', key='TRIGGER_ROLLBACK'
)

_EXTRA_STAGES = [
    _ARTIFACT_REGISTRY_STAGE,
    _SERVICE_ROLLBACK_STAGE,
    _TRIGGER_ROLLBACK_STAGE,
]

# GCF 2nd generation control plane valid memory units
_GCF_GEN2_UNITS = [
    'k',
    'Ki',
    'M',
    'Mi',
    'G',
    'Gi',
    'T',
    'Ti',
    'P',
    'Pi',
]

# GCF 2nd gen valid cpu units
_GCF_GEN2_CPU_UNITS = ['m'] + _GCF_GEN2_UNITS

_MEMORY_VALUE_PATTERN = r"""
    ^                                    # Beginning of input marker.
    (?P<amount>\d+)                      # Amount.
    ((?P<suffix>[-/ac-zAC-Z]+)([bB])?)?  # Optional scale and optional 'b'.
    $                                    # End of input marker.
"""

_CPU_VALUE_PATTERN = r"""
    ^                                    # Beginning of input marker.
    (?P<amount>\d*.?\d*)                 # Amount.
    (?P<suffix>[-/ac-zAC-Z]+)?           # Optional scale.
    $                                    # End of input marker.
"""


def _GetSourceGCS(messages: types.ModuleType, source: str) -> api_types.Source:
  """Constructs a `Source` message from a Cloud Storage object.

  Args:
    messages: messages module, the GCFv2 message stubs.
    source: the Cloud Storage URL.

  Returns:
    The resulting cloudfunctions_v2_messages.Source.
  """
  match = _GCS_SOURCE_REGEX.match(source)
  if not match:
    raise exceptions.FunctionsError(_GCS_SOURCE_ERROR_MESSAGE)

  return messages.Source(
      storageSource=messages.StorageSource(
          bucket=match.group(1), object=match.group(2)
      )
  )


def _GetSourceCSR(messages: types.ModuleType, source: str) -> api_types.Source:
  """Constructs a `Source` message from a Cloud Source Repository reference.

  Args:
    messages: messages module, the GCFv2 message stubs.
    source: the Cloud Source Repository reference.

  Returns:
    The resulting cloudfunctions_v2_messages.Source.
  """
  match = _CSR_SOURCE_REGEX.match(source)

  if match is None:
    raise exceptions.FunctionsError(_CSR_SOURCE_ERROR_MESSAGE)

  repo_source = messages.RepoSource(
      projectId=match.group('project_id'),
      repoName=match.group('repo_name'),
      dir=match.group('path'),  # Optional
  )

  # Optional oneof revision field
  commit = match.group('commit')
  branch = match.group('branch')
  tag = match.group('tag')

  if commit:
    repo_source.commitSha = commit
  elif tag:
    repo_source.tagName = tag
  else:
    # Default to 'master' branch if no revision/alias provided.
    repo_source.branchName = branch or 'master'

  return messages.Source(repoSource=repo_source)


def _GetSourceLocal(
    args: parser_extensions.Namespace,
    client: base_api.BaseApiClient,
    function_ref: resources.Resource,
    source: str,
    kms_key: Optional[str] = None,
) -> api_types.Source:
  """Constructs a `Source` message from a local file system path.

  Args:
    args: The arguments that this command was invoked with.
    client: The GCFv2 Base API client.
    function_ref: The GCFv2 functions resource reference.
    source: The source path.
    kms_key: resource name of the customer managed KMS key | None

  Returns:
    The resulting cloudfunctions_v2_messages.Source.
  """
  messages = client.MESSAGES_MODULE
  with file_utils.TemporaryDirectory() as tmp_dir:
    zip_file_path = source_util.CreateSourcesZipFile(
        tmp_dir, source, args.ignore_file
    )

    if args.stage_bucket:
      dest_object = source_util.UploadToStageBucket(
          zip_file_path, function_ref, args.stage_bucket
      )
      return messages.Source(
          storageSource=messages.StorageSource(
              bucket=dest_object.bucket, object=dest_object.name
          )
      )
    else:
      generate_upload_url_request = messages.GenerateUploadUrlRequest(
          kmsKeyName=kms_key
      )
      try:
        dest = client.projects_locations_functions.GenerateUploadUrl(
            messages.CloudfunctionsProjectsLocationsFunctionsGenerateUploadUrlRequest(
                generateUploadUrlRequest=generate_upload_url_request,
                parent=function_ref.Parent().RelativeName(),
            )
        )
      except apitools_exceptions.HttpError as e:
        cmek_util.ProcessException(e, kms_key)
        raise e

      source_util.UploadToGeneratedUrl(zip_file_path, dest.uploadUrl)

      return messages.Source(storageSource=dest.storageSource)


def _GetSource(
    args: parser_extensions.Namespace,
    client: base_api.BaseApiClient,
    function_ref: resources.Resource,
    existing_function: Optional[api_types.Function],
) -> Tuple[Optional[api_types.Source], FrozenSet[str]]:
  """Parses the source bucket and object from the --source flag.

  Args:
    args: arguments that this command was invoked with.
    client: The GCFv2 API client
    function_ref: The GCFv2 functions resource reference.
    existing_function: `cloudfunctions_v2_messages.Function | None`,
      pre-existing function.

  Returns:
    A tuple `(function_source, update_field_set)` where
    - `function_source` is the resulting `cloudfunctions_v2_messages.Source`,
    - `update_field_set` is a set of update mask fields.
  """
  if (
      args.source is None
      and existing_function is not None
      and existing_function.buildConfig.source.repoSource
  ):
    # The function was previously deployed from a Cloud Source Repository, and
    # the `--source` flag was not specified this time. Don't set any source,
    # so the control plane will reuse the original one.
    return None, frozenset()

  source = args.source or '.'

  messages = client.MESSAGES_MODULE
  if source.startswith('gs://'):
    return _GetSourceGCS(messages, source), frozenset(['build_config.source'])
  elif source.startswith('https://'):
    return _GetSourceCSR(messages, source), frozenset(['build_config.source'])
  else:
    runtime = args.runtime or existing_function.buildConfig.runtime
    source_util.ValidateDirectoryHasRequiredRuntimeFiles(source, runtime)
    return _GetSourceLocal(
        args,
        client,
        function_ref,
        source,
        kms_key=_GetActiveKmsKey(args, existing_function),
    ), frozenset(['build_config.source'])


def _GetServiceConfig(
    args: parser_extensions.Namespace,
    messages: types.ModuleType,
    existing_function: Optional[api_types.Function],
) -> Tuple[api_types.ServiceConfig, FrozenSet[str]]:
  """Constructs a ServiceConfig message from the command-line arguments.

  Args:
    args: arguments that this command was invoked with.
    messages: messages module, the GCFv2 message stubs.
    existing_function: the existing function.

  Returns:
    A tuple `(service_config, updated_fields_set)` where
    - `service_config` is the resulting
    `cloudfunctions_v2_messages.ServiceConfig`.
    - `updated_fields_set` is a set of update mask fields.
  """

  old_env_vars = {}
  if (
      existing_function
      and existing_function.serviceConfig
      and existing_function.serviceConfig.environmentVariables
      and existing_function.serviceConfig.environmentVariables.additionalProperties
  ):
    for (
        additional_property
    ) in (
        existing_function.serviceConfig.environmentVariables.additionalProperties
    ):
      old_env_vars[additional_property.key] = additional_property.value

  env_var_flags = map_util.GetMapFlagsFromArgs('env-vars', args)
  env_vars = map_util.ApplyMapFlags(old_env_vars, **env_var_flags)

  old_secrets = {}
  new_secrets = {}
  if existing_function and existing_function.serviceConfig:
    old_secrets = secrets_util.GetSecretsAsDict(
        existing_function.serviceConfig.secretEnvironmentVariables,
        existing_function.serviceConfig.secretVolumes,
    )

  if secrets_config.IsArgsSpecified(args):
    try:
      new_secrets = secrets_config.ApplyFlags(
          old_secrets,
          args,
          api_util.GetProject(),
          projects_util.GetProjectNumber(api_util.GetProject()),
      )
    except ArgumentTypeError as error:
      core_exceptions.reraise(exceptions.FunctionsError(error))
  else:
    new_secrets = old_secrets

  old_secret_env_vars, old_secret_volumes = secrets_config.SplitSecretsDict(
      old_secrets
  )
  secret_env_vars, secret_volumes = secrets_config.SplitSecretsDict(new_secrets)

  vpc_connector, vpc_egress_settings, vpc_updated_fields = (
      _GetVpcAndVpcEgressSettings(args, messages, existing_function)
  )

  ingress_settings, ingress_updated_fields = _GetIngressSettings(args, messages)

  concurrency = getattr(args, 'concurrency', None)
  cpu = getattr(args, 'cpu', None)

  updated_fields = set()

  if args.serve_all_traffic_latest_revision:
    # only set field if flag is specified, never explicitly set to false.
    updated_fields.add('service_config.all_traffic_on_latest_revision')
  if args.memory is not None:
    updated_fields.add('service_config.available_memory')
  if concurrency is not None:
    updated_fields.add('service_config.max_instance_request_concurrency')
  if cpu is not None:
    updated_fields.add('service_config.available_cpu')
  if args.max_instances is not None or args.clear_max_instances:
    updated_fields.add('service_config.max_instance_count')
  if args.min_instances is not None or args.clear_min_instances:
    updated_fields.add('service_config.min_instance_count')
  if args.run_service_account is not None or args.service_account is not None:
    updated_fields.add('service_config.service_account_email')
  if args.timeout is not None:
    updated_fields.add('service_config.timeout_seconds')
  if env_vars != old_env_vars:
    updated_fields.add('service_config.environment_variables')
  if secret_env_vars != old_secret_env_vars:
    updated_fields.add('service_config.secret_environment_variables')
  if secret_volumes != old_secret_volumes:
    updated_fields.add('service_config.secret_volumes')

  service_updated_fields = frozenset.union(
      vpc_updated_fields, ingress_updated_fields, updated_fields
  )

  return (
      messages.ServiceConfig(
          availableMemory=_ParseMemoryStrToK8sMemory(args.memory),
          maxInstanceCount=None
          if args.clear_max_instances
          else args.max_instances,
          minInstanceCount=None
          if args.clear_min_instances
          else args.min_instances,
          serviceAccountEmail=args.run_service_account or args.service_account,
          timeoutSeconds=args.timeout,
          ingressSettings=ingress_settings,
          vpcConnector=vpc_connector,
          vpcConnectorEgressSettings=vpc_egress_settings,
          allTrafficOnLatestRevision=(
              args.serve_all_traffic_latest_revision or None
          ),
          environmentVariables=messages.ServiceConfig.EnvironmentVariablesValue(
              additionalProperties=[
                  messages.ServiceConfig.EnvironmentVariablesValue.AdditionalProperty(
                      key=key, value=value
                  )
                  for key, value in sorted(env_vars.items())
              ]
          ),
          secretEnvironmentVariables=secrets_util.SecretEnvVarsToMessages(
              secret_env_vars, messages
          ),
          secretVolumes=secrets_util.SecretVolumesToMessages(
              secret_volumes, messages, normalize_for_v2=True
          ),
          maxInstanceRequestConcurrency=concurrency,
          availableCpu=_ValidateK8sCpuStr(cpu),
      ),
      service_updated_fields,
  )


def _ParseMemoryStrToK8sMemory(memory: str) -> Optional[str]:
  """Parses user provided memory to kubernetes expected format.

  Ensure --gen2 continues to parse Gen1 --memory passed in arguments. Defaults
  as M if no unit was specified.

  k8s format:
  https://github.com/kubernetes/kubernetes/blob/master/staging/src/k8s.io/apimachinery/pkg/api/resource/generated.proto

  Args:
    memory: input from `args.memory`

  Returns:
    k8s_memory: str|None, in kubernetes memory format. GCF 2nd Gen control plane
      is case-sensitive and only accepts: value + m, k, M, G, T, Ki, Mi, Gi, Ti.

  Raises:
    InvalidArgumentException: User provided invalid input for flag.
  """
  if memory is None or not memory:
    return None

  match = re.match(_MEMORY_VALUE_PATTERN, memory, re.VERBOSE)
  if not match:
    raise exceptions.InvalidArgumentException(
        '--memory', 'Invalid memory value for: {} specified.'.format(memory)
    )

  suffix = match.group('suffix')
  amount = match.group('amount')

  # Default to megabytes (decimal-base) if suffix not provided.
  if suffix is None:
    suffix = 'M'

  # No case enforced since previously didn't enforce case sensitivity.
  uppercased_gen2_units = dict(
      [(unit.upper(), unit) for unit in _GCF_GEN2_UNITS]
  )
  corrected_suffix = uppercased_gen2_units.get(suffix.upper())

  if not corrected_suffix:
    raise exceptions.InvalidArgumentException(
        '--memory', 'Invalid suffix for: {} specified.'.format(memory)
    )

  parsed_memory = amount + corrected_suffix
  return parsed_memory


def _ValidateK8sCpuStr(cpu: str) -> Optional[str]:
  """Validates user provided cpu to kubernetes expected format.

  k8s format:
  https://github.com/kubernetes/kubernetes/blob/master/staging/src/k8s.io/apimachinery/pkg/api/resource/generated.proto

  Args:
    cpu: input from `args.cpu`

  Returns:
    k8s_cpu: str|None, in kubernetes cpu format.

  Raises:
    InvalidArgumentException: User provided invalid input for flag.
  """
  if cpu is None:
    return None

  match = re.match(_CPU_VALUE_PATTERN, cpu, re.VERBOSE)
  if not match:
    raise exceptions.InvalidArgumentException(
        '--cpu', 'Invalid cpu value for: {} specified.'.format(cpu)
    )

  suffix = match.group('suffix') or ''
  amount = match.group('amount')

  if not amount or amount == '.':
    raise exceptions.InvalidArgumentException(
        '--cpu', 'Invalid amount for: {} specified.'.format(cpu)
    )

  if suffix and suffix not in _GCF_GEN2_CPU_UNITS:
    raise exceptions.InvalidArgumentException(
        '--cpu', 'Invalid suffix for: {} specified.'.format(cpu)
    )

  parsed_memory = amount + suffix
  return parsed_memory


def _GetEventTrigger(
    args: parser_extensions.Namespace,
    messages: types.ModuleType,
    existing_function: Optional[api_types.Function],
) -> Tuple[Optional[api_types.EventTrigger], FrozenSet[str]]:
  """Constructs an EventTrigger message from the command-line arguments.

  Args:
    args: The arguments that this command was invoked with.
    messages: messages module, the GCFv2 message stubs.
    existing_function: The pre-existing function.

  Returns:
    A tuple `(event_trigger, update_fields_set)` where:
    - `event_trigger` is a `cloudfunctions_v2_messages.EventTrigger` used to
    request events sent from another service,
    - `updated_fields_set` is a set of update mask fields.
  """
  if args.trigger_http:
    event_trigger, updated_fields_set = None, frozenset(
        ['event_trigger'] if existing_function else []
    )

  elif args.trigger_event or args.trigger_resource:
    event_trigger, updated_fields_set = _GetEventTriggerForEventType(
        args, messages
    ), frozenset(['event_trigger'])
  elif args.trigger_topic or args.trigger_bucket or args.trigger_event_filters:
    event_trigger, updated_fields_set = _GetEventTriggerForOther(
        args, messages
    ), frozenset(['event_trigger'])

  else:
    if existing_function:
      event_trigger, updated_fields_set = (
          existing_function.eventTrigger,
          frozenset(),
      )
    else:
      raise calliope_exceptions.OneOfArgumentsRequiredException(
          [
              '--trigger-topic',
              '--trigger-bucket',
              '--trigger-http',
              '--trigger-event',
              '--trigger-event-filters',
          ],
          'You must specify a trigger when deploying a new function.',
      )

  if args.IsSpecified('retry'):
    retry_policy, retry_updated_field = _GetRetry(args, messages, event_trigger)
    event_trigger.retryPolicy = retry_policy
    updated_fields_set = updated_fields_set.union(retry_updated_field)

  if event_trigger and trigger_types.IsPubsubType(event_trigger.eventType):
    deploy_util.ensure_pubsub_sa_has_token_creator_role()
  if event_trigger and trigger_types.IsAuditLogType(event_trigger.eventType):
    deploy_util.ensure_data_access_logs_are_enabled(event_trigger.eventFilters)

  return event_trigger, updated_fields_set


def _GetEventTriggerForEventType(
    args: parser_extensions.Namespace, messages: types.ModuleType
) -> api_types.EventTrigger:
  """Constructs an EventTrigger message from the command-line arguments.

  Args:
    args: The arguments that this command was invoked with.
    messages: messages module, the GCFv2 message stubs.

  Returns:
    A `cloudfunctions_v2_messages.EventTrigger`, used to request
      events sent from another service.
  """
  trigger_event = args.trigger_event
  trigger_resource = args.trigger_resource
  service_account_email = args.trigger_service_account or args.service_account

  if trigger_event in api_util.PUBSUB_MESSAGE_PUBLISH_TYPES:
    pubsub_topic = api_util_v1.ValidatePubsubTopicNameOrRaise(trigger_resource)
    return messages.EventTrigger(
        eventType=api_util.EA_PUBSUB_MESSAGE_PUBLISHED,
        pubsubTopic=_BuildFullPubsubTopic(pubsub_topic),
        serviceAccountEmail=service_account_email,
        triggerRegion=args.trigger_location,
    )

  elif (
      trigger_event in api_util.EVENTARC_STORAGE_TYPES
      or trigger_event in api_util.EVENTFLOW_TO_EVENTARC_STORAGE_MAP
  ):
    # name without prefix gs://
    bucket_name = storage_util.BucketReference.FromUrl(trigger_resource).bucket
    storage_event_type = api_util.EVENTFLOW_TO_EVENTARC_STORAGE_MAP.get(
        trigger_event, trigger_event
    )
    return messages.EventTrigger(
        eventType=storage_event_type,
        eventFilters=[
            messages.EventFilter(attribute='bucket', value=bucket_name)
        ],
        serviceAccountEmail=service_account_email,
        triggerRegion=args.trigger_location,
    )

  else:
    raise exceptions.InvalidArgumentException(
        '--trigger-event',
        'Event type {} is not supported by this flag, try using'
        ' --trigger-event-filters.'.format(trigger_event),
    )


def _GetEventTriggerForOther(
    args: parser_extensions.Namespace, messages: types.ModuleType
) -> api_types.EventTrigger:
  """Constructs an EventTrigger when using `--trigger-[bucket|topic|filters]`.

  Args:
    args: arguments that this command was invoked with.
    messages: messages module, the GCFv2 message stubs.

  Returns:
    A `cloudfunctions_v2_messages.EventTrigger` used to request
      events sent from another service.
  """
  event_filters = []
  event_type = None
  pubsub_topic = None
  service_account_email = args.trigger_service_account or args.service_account
  trigger_location = args.trigger_location

  if args.trigger_topic:
    event_type = api_util.EA_PUBSUB_MESSAGE_PUBLISHED
    pubsub_topic = _BuildFullPubsubTopic(args.trigger_topic)
  elif args.trigger_bucket:
    bucket = args.trigger_bucket[5:].rstrip('/')  # strip 'gs://' and final '/'
    event_type = api_util.EA_STORAGE_FINALIZE
    event_filters = [messages.EventFilter(attribute='bucket', value=bucket)]
  elif args.trigger_event_filters:
    event_type = args.trigger_event_filters.get('type')
    event_filters = [
        messages.EventFilter(attribute=attr, value=val)
        for attr, val in args.trigger_event_filters.items()
        if attr != 'type'
    ]
    if args.trigger_event_filters_path_pattern:
      operator = 'match-path-pattern'
      event_filters.extend([
          messages.EventFilter(attribute=attr, value=val, operator=operator)
          for attr, val in args.trigger_event_filters_path_pattern.items()
      ])

  trigger_channel = None
  if args.trigger_channel:
    trigger_channel = args.CONCEPTS.trigger_channel.Parse().RelativeName()

  return messages.EventTrigger(
      eventFilters=event_filters,
      eventType=event_type,
      pubsubTopic=pubsub_topic,
      serviceAccountEmail=service_account_email,
      channel=trigger_channel,
      triggerRegion=trigger_location,
  )


def _GetRetry(
    args: parser_extensions.Namespace,
    messages: types.ModuleType,
    event_trigger: Optional[api_types.EventTrigger],
) -> Tuple[api_types.RetryPolicy, FrozenSet[str]]:
  """Constructs an RetryPolicy enum from --(no-)retry flag.

  Args:
    args: arguments that this command was invoked with.
    messages: messages module, the GCFv2 message stubs.
    event_trigger: trigger used to request events sent from another service.

  Returns:
    A tuple `(retry_policy, update_fields_set)` where:
    - `retry_policy` is the retry policy enum value,
    - `update_fields_set` is the set of update mask fields.
  """

  if event_trigger is None:
    raise exceptions.FunctionsError(_INVALID_RETRY_FLAG_ERROR_MESSAGE)

  if args.retry:
    return messages.EventTrigger.RetryPolicyValueValuesEnum(
        'RETRY_POLICY_RETRY'
    ), frozenset(['eventTrigger.retryPolicy'])
  else:
    # explicitly using --no-retry flag
    return messages.EventTrigger.RetryPolicyValueValuesEnum(
        'RETRY_POLICY_DO_NOT_RETRY'
    ), frozenset(['eventTrigger.retryPolicy'])


def _BuildFullPubsubTopic(pubsub_topic: str) -> str:
  return 'projects/{}/topics/{}'.format(api_util.GetProject(), pubsub_topic)


def _GetBuildConfig(
    args: parser_extensions.Namespace,
    client: client_v2.FunctionsClient,
    function_ref: resources.Resource,
    existing_function: Optional[api_types.Function],
) -> Tuple[api_types.BuildConfig, FrozenSet[str]]:
  """Constructs a BuildConfig message from the command-line arguments.

  Args:
    args: arguments that this command was invoked with.
    client: The GCFv2 API client.
    function_ref: The GCFv2 functions resource reference.
    existing_function: The pre-existing function.

  Returns:
    The resulting build config and the set of update mask fields.
  """
  function_source, source_updated_fields = _GetSource(
      args,
      client,
      function_ref,
      existing_function,
  )

  old_build_env_vars = {}
  if (
      existing_function
      and existing_function.buildConfig
      and existing_function.buildConfig.environmentVariables
      and existing_function.buildConfig.environmentVariables.additionalProperties
  ):
    for (
        additional_property
    ) in (
        existing_function.buildConfig.environmentVariables.additionalProperties
    ):
      old_build_env_vars[additional_property.key] = additional_property.value

  build_env_var_flags = map_util.GetMapFlagsFromArgs('build-env-vars', args)
  # Dict
  build_env_vars = map_util.ApplyMapFlags(
      old_build_env_vars, **build_env_var_flags
  )

  updated_fields = set()

  if build_env_vars != old_build_env_vars:
    updated_fields.add('build_config.environment_variables')

  if args.entry_point is not None:
    updated_fields.add('build_config.entry_point')
  if args.runtime is not None:
    updated_fields.add('build_config.runtime')

  worker_pool = None if args.clear_build_worker_pool else args.build_worker_pool

  if args.build_worker_pool is not None or args.clear_build_worker_pool:
    updated_fields.add('build_config.worker_pool')

  service_account = None
  if args.IsKnownAndSpecified('build_service_account'):
    updated_fields.add('build_config.service_account')
    service_account = args.build_service_account
  messages = client.MESSAGES_MODULE

  automatic_update_policy = None
  on_deploy_update_policy = None
  if args.IsSpecified('runtime_update_policy'):
    updated_fields.update((
        'build_config.automatic_update_policy',
        'build_config.on_deploy_update_policy',
    ))
    if args.runtime_update_policy == 'automatic':
      automatic_update_policy = messages.AutomaticUpdatePolicy()
    if args.runtime_update_policy == 'on-deploy':
      on_deploy_update_policy = messages.OnDeployUpdatePolicy()

  build_updated_fields = frozenset.union(source_updated_fields, updated_fields)
  return (
      messages.BuildConfig(
          entryPoint=args.entry_point,
          runtime=args.runtime,
          source=function_source,
          workerPool=worker_pool,
          environmentVariables=messages.BuildConfig.EnvironmentVariablesValue(
              additionalProperties=[
                  messages.BuildConfig.EnvironmentVariablesValue.AdditionalProperty(
                      key=key, value=value
                  )
                  for key, value in sorted(build_env_vars.items())
              ]
          ),
          serviceAccount=service_account,
          automaticUpdatePolicy=automatic_update_policy,
          onDeployUpdatePolicy=on_deploy_update_policy,
      ),
      build_updated_fields,
  )


def _GetActiveKmsKey(
    args: parser_extensions.Namespace,
    existing_function: Optional[api_types.Function],
) -> Optional[str]:
  """Retrives KMS key applicable to the deployment request.

  Args:
    args: arguments that this command was invoked with.
    existing_function: the pre-existing function.

  Returns:
    Either newly passed or pre-existing KMS key.
  """
  if args.IsSpecified('kms_key'):
    return args.kms_key
  elif args.IsSpecified('clear_kms_key'):
    return None
  return None if not existing_function else existing_function.kmsKeyName


def _GetIngressSettings(
    args: parser_extensions.Namespace, messages: types.ModuleType
) -> Tuple[Optional[api_types.IngressSettings], FrozenSet[str]]:
  """Constructs ingress setting enum from command-line arguments.

  Args:
    args: arguments that this command was invoked with.
    messages: messages module, the GCFv2 message stubs.

  Returns:
    A tuple `(ingress_settings_enum, updated_fields_set)` where:
    - `ingress_settings_enum` is the ingress setting enum value,
    - `updated_fields_set` is the set of update mask fields.
  """
  if args.ingress_settings:
    ingress_settings_enum = arg_utils.ChoiceEnumMapper(
        arg_name='ingress_settings',
        message_enum=messages.ServiceConfig.IngressSettingsValueValuesEnum,
        custom_mappings=flags.INGRESS_SETTINGS_MAPPING,
    ).GetEnumForChoice(args.ingress_settings)
    return ingress_settings_enum, frozenset(['service_config.ingress_settings'])
  else:
    return None, frozenset()


def _GetVpcAndVpcEgressSettings(
    args: parser_extensions.Namespace,
    messages: types.ModuleType,
    existing_function,
) -> Tuple[
    Optional[str],
    Optional[api_types.VpcConnectorEgressSettings],
    FrozenSet[str],
]:
  """Constructs vpc connector and egress settings from command-line arguments.

  Args:
    args: The arguments that this command was invoked with.
    messages: messages module, the GCFv2 message stubs.
    existing_function: The pre-existing function.

  Returns:
    A tuple `(vpc_connector, egress_settings, updated_fields_set)` where:
    - `vpc_connector` is the name of the vpc connector,
    - `egress_settings` is the egress settings for the vpc connector,
    - `updated_fields_set` is the set of update mask fields.
  """
  if args.clear_vpc_connector:
    return (
        None,
        None,
        frozenset([
            'service_config.vpc_connector',
            'service_config.vpc_connector_egress_settings',
        ]),
    )

  update_fields_set = set()

  vpc_connector = None
  if args.vpc_connector:
    vpc_connector = args.CONCEPTS.vpc_connector.Parse().RelativeName()
    update_fields_set.add('service_config.vpc_connector')
  elif (
      existing_function
      and existing_function.serviceConfig
      and existing_function.serviceConfig.vpcConnector
  ):
    vpc_connector = existing_function.serviceConfig.vpcConnector

  egress_settings = None
  if args.egress_settings:
    if not vpc_connector:
      raise exceptions.RequiredArgumentException(
          'vpc-connector',
          'Flag `--vpc-connector` is required for setting `--egress-settings`.',
      )

    egress_settings = arg_utils.ChoiceEnumMapper(
        arg_name='egress_settings',
        message_enum=messages.ServiceConfig.VpcConnectorEgressSettingsValueValuesEnum,
        custom_mappings=flags.EGRESS_SETTINGS_MAPPING,
    ).GetEnumForChoice(args.egress_settings)
    update_fields_set.add('service_config.vpc_connector_egress_settings')

  return vpc_connector, egress_settings, frozenset(update_fields_set)


def _ValidateV1OnlyFlags(args: parser_extensions.Namespace) -> None:
  """Ensures that only the arguments supported in V2 are passing through."""
  for flag_variable, flag_name in _V1_ONLY_FLAGS:
    if args.IsKnownAndSpecified(flag_variable):
      raise exceptions.FunctionsError(_V1_ONLY_FLAG_ERROR % flag_name)


def _GetLabels(
    args: parser_extensions.Namespace,
    messages: types.ModuleType,
    existing_function: Optional[api_types.Function],
) -> Tuple[Optional[api_types.LabelsValue], FrozenSet[str]]:
  """Constructs labels from command-line arguments.

  Args:
    args: The arguments that this command was invoked with
    messages: messages module, the GCFv2 message stubs.
    existing_function: The pre-existing function.

  Returns:
    A tuple `(labels, updated_fields_set)` where:
    - `labels` is functions labels metadata,
    - `updated_fields_set` is the set of update mask fields.
  """
  if existing_function:
    required_labels = {}
  else:
    required_labels = {_DEPLOYMENT_TOOL_LABEL: _DEPLOYMENT_TOOL_VALUE}
  labels_diff = labels_util.Diff.FromUpdateArgs(
      args, required_labels=required_labels
  )
  labels_update = labels_diff.Apply(
      messages.Function.LabelsValue,
      existing_function.labels if existing_function else None,
  )
  if labels_update.needs_update:
    return labels_update.labels, frozenset(['labels'])
  else:
    return None, frozenset()


def _SetCmekFields(
    args: parser_extensions.Namespace,
    function: api_types.Function,
    existing_function: Optional[api_types.Function],
    function_ref: resources.Resource,
) -> FrozenSet[str]:
  """Sets CMEK-related fields on the function.

  Args:
    args: arguments that this command was invoked with.
    function: `cloudfunctions_v2alpha_messages.Function`, the recently created
      or updated GCF function.
    existing_function: `cloudfunctions_v2_messages.Function | None`, the
      pre-existing function.
    function_ref: resource reference.

  Returns:
    A set of update mask fields.
  """
  updated_fields = set()
  function.kmsKeyName = (
      existing_function.kmsKeyName if existing_function else None
  )
  if args.IsSpecified('kms_key') or args.IsSpecified('clear_kms_key'):
    function.kmsKeyName = (
        None if args.IsSpecified('clear_kms_key') else args.kms_key
    )
  if (
      existing_function is None
      or function.kmsKeyName != existing_function.kmsKeyName
  ):
    if args.kms_key is not None:
      cmek_util.ValidateKMSKeyForFunction(function.kmsKeyName, function_ref)
    updated_fields.add('kms_key_name')
  return updated_fields


def _SetDockerRepositoryConfig(
    args: parser_extensions.Namespace,
    function: api_types.Function,
    existing_function: Optional[api_types.Function],
    function_ref: resources.Resource,
) -> FrozenSet[str]:
  """Sets user-provided docker repository field on the function.

  Args:
    args: arguments that this command was invoked with
    function: `cloudfunctions_v2_messages.Function`, recently created or updated
      GCF function.
    existing_function: `cloudfunctions_v2_messages.Function | None`,
      pre-existing function.
    function_ref: resource reference.

  Returns:
    A set of update mask fields.
  """
  updated_fields = set()
  function.buildConfig.dockerRepository = (
      existing_function.buildConfig.dockerRepository
      if existing_function
      else None
  )
  if args.IsSpecified('docker_repository'):
    cmek_util.ValidateDockerRepositoryForFunction(
        args.docker_repository, function_ref
    )
  if args.IsSpecified('docker_repository') or args.IsSpecified(
      'clear_docker_repository'
  ):
    updated_docker_repository = (
        None
        if args.IsSpecified('clear_docker_repository')
        else args.docker_repository
    )
    function.buildConfig.dockerRepository = (
        cmek_util.NormalizeDockerRepositoryFormat(updated_docker_repository)
    )
    if (
        existing_function is None
        or function.buildConfig.dockerRepository
        != existing_function.buildConfig.dockerRepository
    ):
      updated_fields.add('build_config.docker_repository')
  if function.kmsKeyName and not function.buildConfig.dockerRepository:
    raise calliope_exceptions.RequiredArgumentException(
        '--docker-repository',
        (
            'A Docker repository must be specified when a KMS key is configured'
            ' for the function.'
        ),
    )
  return updated_fields


def _PromptToAllowUnauthenticatedInvocations(name: str) -> bool:
  """Prompts the user to allow unauthenticated invocations for the given function."""
  return console_io.PromptContinue(
      prompt_string=(
          'Allow unauthenticated invocations of new function [{}]?'.format(name)
      ),
      default=False,
  )


def _CreateAndWait(
    gcf_client: client_v2.FunctionsClient,
    function_ref: resources.Resource,
    function: api_types.Function,
) -> None:
  """Create a function.

  This does not include setting the invoker permissions.

  Args:
    gcf_client: The GCFv2 API client.
    function_ref: The GCFv2 functions resource reference.
    function: `cloudfunctions_v2_messages.Function`, The function to create.

  Returns:
    None
  """
  client = gcf_client.client
  messages = gcf_client.messages
  create_request = (
      messages.CloudfunctionsProjectsLocationsFunctionsCreateRequest(
          parent=function_ref.Parent().RelativeName(),
          functionId=function_ref.Name(),
          function=function,
      )
  )
  operation = client.projects_locations_functions.Create(create_request)
  operation_description = 'Deploying function'

  api_util.WaitForOperation(
      client, messages, operation, operation_description, _EXTRA_STAGES
  )


def _UpdateAndWait(
    gcf_client: client_v2.FunctionsClient,
    function_ref: resources.Resource,
    function: api_types.Function,
    updated_fields_set: FrozenSet[str],
) -> None:
  """Update a function.

  This does not include setting the invoker permissions.

  Args:
    gcf_client: The GCFv2 API client.
    function_ref: The GCFv2 functions resource reference.
    function: `cloudfunctions_v2_messages.Function`, The function to update.
    updated_fields_set: A set of update mask fields.

  Returns:
    None
  """
  client = gcf_client.client
  messages = gcf_client.messages
  if updated_fields_set:
    update_request = (
        messages.CloudfunctionsProjectsLocationsFunctionsPatchRequest(
            name=function_ref.RelativeName(),
            updateMask=','.join(sorted(updated_fields_set)),
            function=function,
        )
    )

    operation = client.projects_locations_functions.Patch(update_request)
    operation_description = 'Updating function (may take a while)'

    api_util.WaitForOperation(
        client, messages, operation, operation_description, _EXTRA_STAGES
    )
  else:
    log.status.Print('Nothing to update.')


def Run(
    args: parser_extensions.Namespace, release_track: calliope_base.ReleaseTrack
) -> api_types.Function:
  """Runs a function deployment with the given args."""
  client = client_v2.FunctionsClient(release_track=release_track)
  messages = client.messages

  function_ref = args.CONCEPTS.name.Parse()

  _ValidateV1OnlyFlags(args)

  existing_function = client.GetFunction(function_ref.RelativeName())

  is_new_function = existing_function is None
  if is_new_function and not args.runtime:
    if not console_io.CanPrompt():
      raise calliope_exceptions.RequiredArgumentException(
          'runtime', 'Flag `--runtime` is required for new functions.'
      )

    runtimes = [
        r.name
        for r in client.ListRuntimes(function_ref.locationsId).runtimes
        if str(r.environment) == 'GEN_2'
    ]
    idx = console_io.PromptChoice(
        runtimes, message='Please select a runtime:\n'
    )
    args.runtime = runtimes[idx]
    log.status.Print(
        'To skip this prompt, add `--runtime={}` to your command next time.\n'
        .format(args.runtime)
    )

  if (
      flags.ShouldUseGen2()
      and existing_function
      and str(existing_function.environment) == 'GEN_1'
  ):
    raise exceptions.InvalidArgumentException(
        '--gen2',
        "Function already exists in 1st gen, can't change the environment.",
    )

  if existing_function and existing_function.serviceConfig:
    has_all_traffic_on_latest_revision = (
        existing_function.serviceConfig.allTrafficOnLatestRevision
    )
    if (
        has_all_traffic_on_latest_revision is not None
        and not has_all_traffic_on_latest_revision
    ):
      log.warning(_LATEST_REVISION_TRAFFIC_WARNING_MESSAGE)

  event_trigger, trigger_updated_fields = _GetEventTrigger(
      args, messages, existing_function
  )

  build_config, build_updated_fields = _GetBuildConfig(
      args,
      client.client,
      function_ref,
      existing_function,
  )

  service_config, service_updated_fields = _GetServiceConfig(
      args, messages, existing_function
  )

  labels_value, labels_updated_fields = _GetLabels(
      args, messages, existing_function
  )

  # cs/symbol:google.cloud.functions.v2main.Function$
  function = messages.Function(
      name=function_ref.RelativeName(),
      buildConfig=build_config,
      eventTrigger=event_trigger,
      serviceConfig=service_config,
      labels=labels_value,
  )

  cmek_updated_fields = _SetCmekFields(
      args, function, existing_function, function_ref
  )
  docker_repository_updated_fields = _SetDockerRepositoryConfig(
      args, function, existing_function, function_ref
  )

  api_enablement.PromptToEnableApiIfDisabled('run.googleapis.com')
  api_enablement.PromptToEnableApiIfDisabled('cloudbuild.googleapis.com')
  api_enablement.PromptToEnableApiIfDisabled('artifactregistry.googleapis.com')

  allow_unauthenticated = None
  if args.IsSpecified('allow_unauthenticated'):
    allow_unauthenticated = args.allow_unauthenticated
  elif is_new_function and not event_trigger:
    allow_unauthenticated = _PromptToAllowUnauthenticatedInvocations(args.NAME)

  if is_new_function:
    _CreateAndWait(client, function_ref, function)
  else:
    updated_fields = frozenset.union(
        trigger_updated_fields,
        build_updated_fields,
        service_updated_fields,
        labels_updated_fields,
        cmek_updated_fields,
        docker_repository_updated_fields,
    )
    _UpdateAndWait(client, function_ref, function, updated_fields)

  function = client.GetFunction(function_ref.RelativeName())

  if (
      # New functions do not allow unauthenticated invocations by default so we
      # only ever need to add the permission.
      is_new_function
      and allow_unauthenticated
      # Existing functions' permissions should only change if explicitly
      # requested.
      or existing_function
      and args.IsSpecified('allow_unauthenticated')
  ):
    run_util.AddOrRemoveInvokerBinding(
        function,
        add_binding=allow_unauthenticated,
        member=serverless_operations.ALLOW_UNAUTH_POLICY_BINDING_MEMBER,
    )

  log.status.Print(
      'You can view your function in the Cloud Console here: '
      + 'https://console.cloud.google.com/functions/details/{}/{}?project={}\n'
      .format(
          function_ref.locationsId, function_ref.Name(), api_util.GetProject()
      )
  )

  return function
