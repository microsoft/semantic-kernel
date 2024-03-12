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

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import re

from apitools.base.py import encoding
from googlecloudsdk.api_lib.compute import utils
from googlecloudsdk.api_lib.functions import api_enablement
from googlecloudsdk.api_lib.functions import cmek_util
from googlecloudsdk.api_lib.functions import secrets as secrets_util
from googlecloudsdk.api_lib.functions.v1 import env_vars as env_vars_api_util
from googlecloudsdk.api_lib.functions.v1 import exceptions as function_exceptions
from googlecloudsdk.api_lib.functions.v1 import util as api_util
from googlecloudsdk.api_lib.functions.v2 import client as v2_client
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions as calliope_exceptions
from googlecloudsdk.calliope.arg_parsers import ArgumentTypeError
from googlecloudsdk.command_lib.functions import flags
from googlecloudsdk.command_lib.functions import secrets_config
from googlecloudsdk.command_lib.functions.v1.deploy import enum_util
from googlecloudsdk.command_lib.functions.v1.deploy import labels_util
from googlecloudsdk.command_lib.functions.v1.deploy import source_util
from googlecloudsdk.command_lib.functions.v1.deploy import trigger_util
from googlecloudsdk.command_lib.projects import util as project_util
from googlecloudsdk.command_lib.util.apis import arg_utils
from googlecloudsdk.command_lib.util.args import map_util
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core.console import console_io
from six.moves import urllib

_BUILD_NAME_REGEX = re.compile(
    r'projects\/(?P<projectnumber>[^\/]+)\/locations'
    r'\/(?P<region>[^\/]+)\/builds\/(?P<buildid>[^\/]+)'
)


def _ApplyBuildEnvVarsArgsToFunction(function, args):
  """Determines if build environment variables have to be updated.

  It compares the cli args with the existing build environment variables to
  compute the resulting build environment variables.

  Args:
    function: CloudFunction message to be checked and filled with build env vars
      based on the flags
    args: all cli args

  Returns:
    updated_fields: update mask containing the list of fields that are
    considered for updating based on the cli args and existing variables
  """

  updated_fields = []
  old_build_env_vars = env_vars_api_util.GetEnvVarsAsDict(
      function.buildEnvironmentVariables
  )
  build_env_var_flags = map_util.GetMapFlagsFromArgs('build-env-vars', args)
  new_build_env_vars = map_util.ApplyMapFlags(
      old_build_env_vars, **build_env_var_flags
  )
  if old_build_env_vars != new_build_env_vars:
    build_env_vars_type_class = (
        api_util.GetApiMessagesModule().CloudFunction.BuildEnvironmentVariablesValue
    )
    function.buildEnvironmentVariables = (
        env_vars_api_util.DictToEnvVarsProperty(
            build_env_vars_type_class, new_build_env_vars
        )
    )
    updated_fields.append('buildEnvironmentVariables')
  return updated_fields


def _ApplyEnvVarsArgsToFunction(function, args):
  """Determines if environment variables have to be updated.

  It compares the cli args with the existing environment variables to compute
  the resulting build environment variables.

  Args:
    function: CloudFunction message to be checked and filled with env vars based
      on the flags
    args: all cli args

  Returns:
    updated_fields: update mask containing the list of fields that are
    considered for updating based on the cli args and existing variables
  """

  updated_fields = []
  old_env_vars = env_vars_api_util.GetEnvVarsAsDict(
      function.environmentVariables
  )
  env_var_flags = map_util.GetMapFlagsFromArgs('env-vars', args)
  new_env_vars = map_util.ApplyMapFlags(old_env_vars, **env_var_flags)
  if old_env_vars != new_env_vars:
    env_vars_type_class = (
        api_util.GetApiMessagesModule().CloudFunction.EnvironmentVariablesValue
    )
    function.environmentVariables = env_vars_api_util.DictToEnvVarsProperty(
        env_vars_type_class, new_env_vars
    )
    updated_fields.append('environmentVariables')
  return updated_fields


def _LogSecretsPermissionMessage(project, service_account_email):
  """Logs a warning message asking the user to grant access to secrets.

  This will be removed once access checker is added.

  Args:
    project: Project id.
    service_account_email: Runtime service account email.
  """
  if not service_account_email:
    service_account_email = '{project}@appspot.gserviceaccount.com'.format(
        project=project
    )
  message = (
      'This deployment uses secrets. Ensure that the runtime service '
      "account '{sa}' has access to the secrets. You can do that by "
      "granting the permission 'roles/secretmanager.secretAccessor' to "
      'the runtime service account on the project or secrets.\n'
  )
  command = (
      'E.g. gcloud projects add-iam-policy-binding {project} --member='
      "'serviceAccount:{sa}' --role='roles/secretmanager.secretAccessor'"
  )
  # TODO(b/185133105): Log this message for secret access failures only
  log.warning(
      (message + command).format(project=project, sa=service_account_email)
  )


def _ApplySecretsArgsToFunction(function, args):
  """Populates cloud function message with secrets payload if applicable.

  It compares the CLI args with the existing secrets configuration to compute
  the effective secrets configuration.

  Args:
    function: Cloud function message to be checked and populated.
    args: All CLI arguments.

  Returns:
    updated_fields: update mask containing the list of fields to be updated.
  """
  if not secrets_config.IsArgsSpecified(args):
    return []

  old_secrets = secrets_util.GetSecretsAsDict(
      function.secretEnvironmentVariables, function.secretVolumes
  )
  new_secrets = {}
  try:
    new_secrets = secrets_config.ApplyFlags(
        old_secrets,
        args,
        _GetProject(),
        project_util.GetProjectNumber(_GetProject()),
    )
  except ArgumentTypeError as error:
    exceptions.reraise(function_exceptions.FunctionsError(error))

  if new_secrets:
    _LogSecretsPermissionMessage(_GetProject(), function.serviceAccountEmail)

  old_secret_env_vars, old_secret_volumes = secrets_config.SplitSecretsDict(
      old_secrets
  )
  new_secret_env_vars, new_secret_volumes = secrets_config.SplitSecretsDict(
      new_secrets
  )

  updated_fields = []
  if old_secret_env_vars != new_secret_env_vars:
    function.secretEnvironmentVariables = secrets_util.SecretEnvVarsToMessages(
        new_secret_env_vars, api_util.GetApiMessagesModule()
    )
    updated_fields.append('secretEnvironmentVariables')
  if old_secret_volumes != new_secret_volumes:
    function.secretVolumes = secrets_util.SecretVolumesToMessages(
        new_secret_volumes, api_util.GetApiMessagesModule()
    )
    updated_fields.append('secretVolumes')
  return updated_fields


def _ApplyCMEKArgsToFunction(function_ref, function, args):
  """Configures CMEK related fields for the Cloud Function.

  It sets or clears the kms_key_name and docker_repository fields based on the
  CLI args.

  Args:
    function_ref: Function resource.
    function: Cloud function message to be configured.
    args: All CLI arguments.

  Returns:
    updated_fields: update mask containing the list of fields to be updated.

  Raises:
    InvalidArgumentException: If the specified KMS key or Docker repository is
      not compatible with the function.
    RequiredArgumentException: If Docker repository is not specified when KMS
      key is configured.
  """
  updated_fields = []
  if args.IsSpecified('kms_key') or args.IsSpecified('clear_kms_key'):
    old_kms_key = function.kmsKeyName
    function.kmsKeyName = None if args.clear_kms_key else args.kms_key
    if function.kmsKeyName != old_kms_key:
      if function.kmsKeyName:
        cmek_util.ValidateKMSKeyForFunction(function.kmsKeyName, function_ref)
      updated_fields.append('kmsKeyName')
  if args.IsSpecified('docker_repository') or args.IsSpecified(
      'clear_docker_repository'
  ):
    old_docker_repository = function.dockerRepository
    new_docker_repository = (
        None
        if args.IsSpecified('clear_docker_repository')
        else cmek_util.NormalizeDockerRepositoryFormat(args.docker_repository)
    )
    function.dockerRepository = new_docker_repository
    if function.dockerRepository != old_docker_repository:
      if function.dockerRepository:
        cmek_util.ValidateDockerRepositoryForFunction(
            function.dockerRepository, function_ref
        )
      updated_fields.append('dockerRepository')
  if function.kmsKeyName and not function.dockerRepository:
    raise calliope_exceptions.RequiredArgumentException(
        '--docker-repository',
        (
            'A Docker repository must be specified when a KMS key is configured'
            ' for the function.'
        ),
    )
  return updated_fields


def _ApplyDockerRegistryArgsToFunction(function, args):
  """Populates the `docker_registry` field of a Cloud Function message.

  Args:
    function: Cloud function message to be checked and populated.
    args: All CLI arguments.

  Returns:
    updated_fields: update mask containing the list of fields to be updated.

  Raises:
    InvalidArgumentException: If Container Registry is specified for a CMEK
    deployment (CMEK is only supported by Artifact Registry).
  """
  updated_fields = []
  if args.IsSpecified('docker_registry'):
    kms_key = function.kmsKeyName
    if args.IsSpecified('kms_key') or args.IsSpecified('clear_kms_key'):
      kms_key = None if args.clear_kms_key else args.kms_key
    if kms_key is not None and args.docker_registry == 'container-registry':
      raise calliope_exceptions.InvalidArgumentException(
          '--docker-registry',
          (
              'CMEK deployments are not supported by Container Registry.'
              'Please either use Artifact Registry or do not specify a KMS key '
              'for the function (you may need to clear it).'
          ),
      )
    function.dockerRegistry = enum_util.ParseDockerRegistry(
        args.docker_registry
    )
    updated_fields.append('dockerRegistry')

  return updated_fields


def _DefaultDockerRegistryIfUnspecified(function, all_updated_fields):
  """Sets the default for `docker_registry` field of a Cloud Function message.

  Args:
    function: Cloud function message to be checked and populated.
    all_updated_fields: List of all fields that are being updated within the
      deployment request.

  Returns:
    updated_fields: update mask containing the list of fields to be updated.
  """
  updated_fields = []
  # Set the default only if the request is not completely empty.
  if all_updated_fields and 'dockerRegistry' not in all_updated_fields:
    function.dockerRegistry = enum_util.ParseDockerRegistry('artifact-registry')
    updated_fields.append('dockerRegistry')

  return updated_fields


def _PromptToEnableArtifactRegistryIfRequired(cli_args):
  """Checks if the deployment needs Artifact Registry and prompts to enable it.

  Args:
    cli_args: CLI arguments passed to the deployment request.
  """
  if (
      cli_args.IsSpecified('docker_registry')
      and cli_args.docker_registry == 'container-registry'
  ):
    return

  api_enablement.PromptToEnableApiIfDisabled(
      'artifactregistry.googleapis.com', enable_by_default=True
  )


def _GetActiveKMSKey(function, args):
  """Retrieves the KMS key for the function.

  This is either the KMS key provided via the kms-key flag or the KMS key
  configured for the existing function if any.

  Args:
    function: existing cloud function if any.
    args: CLI arguments.

  Returns:
    kms_key: KMS key if any.
  """
  kms_key = function.kmsKeyName
  if args.IsSpecified('kms_key') or args.IsSpecified('clear_kms_key'):
    kms_key = None if args.clear_kms_key else args.kms_key
  return kms_key


def _ApplyBuildpackStackArgsToFunction(function, args, track):
  """Populates the `buildpack_stack` field of a Cloud Function message.

  Args:
    function: Cloud function message to be populated.
    args: All CLI arguments.
    track: release track.

  Returns:
    updated_fields: update mask containing the list of fields to be updated.
  """
  if track is not base.ReleaseTrack.ALPHA:
    return []

  updated_fields = []
  if args.IsSpecified('buildpack_stack'):
    function.buildpackStack = args.buildpack_stack
    updated_fields.append('buildpack_stack')

  return updated_fields


def _ApplyBuildServiceAccountToFunction(function, args, track):
  """Populates the `build_service_account` field of a Cloud Function message.

  Args:
    function: Cloud function message to be populated.
    args: All CLI arguments.
    track: release track.

  Returns:
    updated_fields: update mask containing the list of fields to be updated.
  """
  if track is base.ReleaseTrack.GA:
    return []

  updated_fields = []
  if args.IsSpecified('build_service_account'):
    function.buildServiceAccount = args.build_service_account
    updated_fields.append('build_service_account')

  return updated_fields


def _CreateBindPolicyCommand(function_ref):
  template = (
      'gcloud functions add-iam-policy-binding %s --region=%s '
      '--member=allUsers --role=roles/cloudfunctions.invoker'
  )
  return template % (function_ref.Name(), function_ref.locationsId)


def _CreateStackdriverURLforBuildLogs(build_id, project_id):
  query_param = (
      'resource.type=build\nresource.labels.build_id=%s\n'
      'logName=projects/%s/logs/cloudbuild' % (build_id, project_id)
  )
  return (
      'https://console.cloud.google.com/logs/viewer?'
      'project=%s&advancedFilter=%s'
      % (project_id, urllib.parse.quote(query_param, safe=''))
  )


def _GetProject():
  return properties.VALUES.core.project.GetOrFail()


def _CreateCloudBuildLogURL(build_name):
  matched_groups = _BUILD_NAME_REGEX.match(build_name).groupdict()
  return (
      'https://console.cloud.google.com/'
      'cloud-build/builds;region=%s/%s?project=%s'
      % (
          matched_groups['region'],
          matched_groups['buildid'],
          matched_groups['projectnumber'],
      )
  )


def _ValidateV1Flag(args):
  if args.timeout and args.timeout > 540:
    raise ArgumentTypeError(
        '--timeout: value must be less than or equal to '
        '540s; received: {}s'.format(args.timeout)
    )


def Run(args, track=None):
  """Run a function deployment with the given args."""
  flags.ValidateV1TimeoutFlag(args)

  # Check for labels that start with `deployment`, which is not allowed.
  labels_util.CheckNoDeploymentLabels('--remove-labels', args.remove_labels)
  labels_util.CheckNoDeploymentLabels('--update-labels', args.update_labels)

  # Check that exactly one trigger type is specified properly.
  trigger_util.ValidateTriggerArgs(
      args.trigger_event,
      args.trigger_resource,
      args.IsSpecified('retry'),
      args.IsSpecified('trigger_http'),
  )
  trigger_params = trigger_util.GetTriggerEventParams(
      args.trigger_http,
      args.trigger_bucket,
      args.trigger_topic,
      args.trigger_event,
      args.trigger_resource,
  )

  function_ref = args.CONCEPTS.name.Parse()
  function_url = function_ref.RelativeName()

  messages = api_util.GetApiMessagesModule(track)

  # Get an existing function or create a new one.
  function = api_util.GetFunction(function_url)

  is_new_function = function is None
  had_vpc_connector = (
      bool(function.vpcConnector) if not is_new_function else False
  )
  had_http_trigger = (
      bool(function.httpsTrigger) if not is_new_function else False
  )
  if is_new_function:
    trigger_util.CheckTriggerSpecified(args)
    function = messages.CloudFunction()
    function.name = function_url
  elif trigger_params:
    # If the new deployment would implicitly change the trigger_event type
    # raise error
    trigger_util.CheckLegacyTriggerUpdate(
        function.eventTrigger, trigger_params['trigger_event']
    )

  # Keep track of which fields are updated in the case of patching.
  updated_fields = []

  # Populate function properties based on args.
  if args.entry_point:
    function.entryPoint = args.entry_point
    updated_fields.append('entryPoint')
  if args.timeout:
    function.timeout = '{}s'.format(args.timeout)
    updated_fields.append('timeout')
  if args.memory:
    # For v1 convert args.memory from str to number of bytes in int
    args.memory = flags.ParseMemoryStrToNumBytes(args.memory)
    function.availableMemoryMb = utils.BytesToMb(args.memory)
    updated_fields.append('availableMemoryMb')
  if args.service_account:
    function.serviceAccountEmail = args.service_account
    updated_fields.append('serviceAccountEmail')
  if args.IsSpecified('max_instances') or args.IsSpecified(
      'clear_max_instances'
  ):
    max_instances = 0 if args.clear_max_instances else args.max_instances
    function.maxInstances = max_instances
    updated_fields.append('maxInstances')
  if args.IsSpecified('min_instances') or args.IsSpecified(
      'clear_min_instances'
  ):
    min_instances = 0 if args.clear_min_instances else args.min_instances
    function.minInstances = min_instances
    updated_fields.append('minInstances')
  if args.IsSpecified('runtime'):
    function.runtime = args.runtime
    updated_fields.append('runtime')
  elif is_new_function:
    raise calliope_exceptions.RequiredArgumentException(
        'runtime', 'Flag `--runtime` is required for new functions.'
    )

  if args.IsSpecified('runtime_update_policy'):
    if args.runtime_update_policy == 'automatic':
      function.automaticUpdatePolicy = messages.AutomaticUpdatePolicy()
      function.onDeployUpdatePolicy = None
    if args.runtime_update_policy == 'on-deploy':
      function.onDeployUpdatePolicy = messages.OnDeployUpdatePolicy()
      function.automaticUpdatePolicy = None
    updated_fields.extend(['automaticUpdatePolicy', 'onDeployUpdatePolicy'])

  warning = api_util.ValidateRuntimeOrRaise(
      v2_client.FunctionsClient(base.ReleaseTrack.GA),
      function.runtime,
      function_ref.locationsId,
  )
  if warning:
    log.warning(warning)

  vpc_connector_ref = args.CONCEPTS.vpc_connector.Parse()

  if vpc_connector_ref or args.clear_vpc_connector:
    function.vpcConnector = (
        '' if args.clear_vpc_connector else vpc_connector_ref.RelativeName()
    )
    updated_fields.append('vpcConnector')
  if args.IsSpecified('egress_settings'):
    will_have_vpc_connector = (
        had_vpc_connector and not args.clear_vpc_connector
    ) or vpc_connector_ref
    if not will_have_vpc_connector:
      raise calliope_exceptions.RequiredArgumentException(
          'vpc-connector',
          'Flag `--vpc-connector` is required for setting `egress-settings`.',
      )
    egress_settings_enum = arg_utils.ChoiceEnumMapper(
        arg_name='egress_settings',
        message_enum=function.VpcConnectorEgressSettingsValueValuesEnum,
        custom_mappings=flags.EGRESS_SETTINGS_MAPPING,
    ).GetEnumForChoice(args.egress_settings)
    function.vpcConnectorEgressSettings = egress_settings_enum
    updated_fields.append('vpcConnectorEgressSettings')
  if args.IsSpecified('ingress_settings'):
    ingress_settings_enum = arg_utils.ChoiceEnumMapper(
        arg_name='ingress_settings',
        message_enum=function.IngressSettingsValueValuesEnum,
        custom_mappings=flags.INGRESS_SETTINGS_MAPPING,
    ).GetEnumForChoice(args.ingress_settings)
    function.ingressSettings = ingress_settings_enum
    updated_fields.append('ingressSettings')
  if args.build_worker_pool or args.clear_build_worker_pool:
    function.buildWorkerPool = (
        '' if args.clear_build_worker_pool else args.build_worker_pool
    )
    updated_fields.append('buildWorkerPool')
  # Populate trigger properties of function based on trigger args.
  if args.trigger_http:
    function.httpsTrigger = messages.HttpsTrigger()
    function.eventTrigger = None
    updated_fields.extend(['eventTrigger', 'httpsTrigger'])
  if trigger_params:
    function.eventTrigger = trigger_util.CreateEventTrigger(**trigger_params)
    function.httpsTrigger = None
    updated_fields.extend(['eventTrigger', 'httpsTrigger'])
  if args.IsSpecified('retry'):
    updated_fields.append('eventTrigger.failurePolicy')
    if args.retry:
      function.eventTrigger.failurePolicy = messages.FailurePolicy()
      function.eventTrigger.failurePolicy.retry = messages.Retry()
    else:
      function.eventTrigger.failurePolicy = None
  elif function.eventTrigger:
    function.eventTrigger.failurePolicy = None

  will_have_http_trigger = had_http_trigger or args.trigger_http

  if args.IsSpecified('security_level') or (
      will_have_http_trigger and is_new_function
  ):
    if not will_have_http_trigger:
      raise calliope_exceptions.RequiredArgumentException(
          'trigger-http',
          'Flag `--trigger-http` is required for setting `security-level`.',
      )

    # SecurityLevelValueValuesEnum('SECURE_ALWAYS' | 'SECURE_OPTIONAL')
    security_level_enum = arg_utils.ChoiceEnumMapper(
        arg_name='security_level',
        message_enum=function.httpsTrigger.SecurityLevelValueValuesEnum,
        custom_mappings=flags.SECURITY_LEVEL_MAPPING,
    ).GetEnumForChoice(args.security_level)
    function.httpsTrigger.securityLevel = security_level_enum
    updated_fields.append('httpsTrigger.securityLevel')

  kms_key = _GetActiveKMSKey(function, args)

  # Populate source properties of function based on source args.
  # Only Add source to function if its explicitly provided, a new function,
  # using a stage bucket or deploy of an existing function that previously
  # used local source.
  if (
      args.source
      or args.stage_bucket
      or is_new_function
      or function.sourceUploadUrl
  ):
    updated_fields.extend(
        source_util.SetFunctionSourceProps(
            function,
            function_ref,
            args.source,
            args.stage_bucket,
            args.ignore_file,
            kms_key,
        )
    )

  # Apply label args to function
  if labels_util.SetFunctionLabels(
      function, args.update_labels, args.remove_labels, args.clear_labels
  ):
    updated_fields.append('labels')

  # Apply build environment variables args to function
  updated_fields.extend(_ApplyBuildEnvVarsArgsToFunction(function, args))

  # Apply environment variables args to function
  updated_fields.extend(_ApplyEnvVarsArgsToFunction(function, args))

  ensure_all_users_invoke = flags.ShouldEnsureAllUsersInvoke(args)
  deny_all_users_invoke = flags.ShouldDenyAllUsersInvoke(args)

  # Applies secrets args to function
  updated_fields.extend(_ApplySecretsArgsToFunction(function, args))

  # Applies CMEK args to function
  updated_fields.extend(_ApplyCMEKArgsToFunction(function_ref, function, args))

  # Applies remaining Artifact Registry args to the function. Note that one of
  # them, docker_repository, was already added as part of CMEK
  updated_fields.extend(_ApplyDockerRegistryArgsToFunction(function, args))

  # Applies Buildpack stack args to the function.
  updated_fields.extend(
      _ApplyBuildpackStackArgsToFunction(function, args, track)
  )

  # TODO(b/287538740): Can be cleaned up after a full transition to the AR.
  updated_fields.extend(
      _DefaultDockerRegistryIfUnspecified(function, updated_fields)
  )

  updated_fields.extend(
      _ApplyBuildServiceAccountToFunction(function, args, track)
  )

  api_enablement.PromptToEnableApiIfDisabled('cloudbuild.googleapis.com')
  _PromptToEnableArtifactRegistryIfRequired(args)

  if is_new_function:
    if (
        function.httpsTrigger
        and not ensure_all_users_invoke
        and not deny_all_users_invoke
        and api_util.CanAddFunctionIamPolicyBinding(_GetProject())
    ):
      ensure_all_users_invoke = console_io.PromptContinue(
          prompt_string=(
              'Allow unauthenticated invocations of new function [{}]?'.format(
                  args.NAME
              )
          ),
          default=False,
      )

    op = api_util.CreateFunction(function, function_ref.Parent().RelativeName())
    if api_util.IsGcrRepository(function):
      api_util.ValidateSecureImageRepositoryOrWarn(
          function_ref.locationsId, _GetProject()
      )
    if (
        function.httpsTrigger
        and not ensure_all_users_invoke
        and not deny_all_users_invoke
    ):
      template = (
          'Function created with limited-access IAM policy. '
          'To enable unauthorized access consider `%s`'
      )
      log.warning(template % _CreateBindPolicyCommand(function_ref))
      deny_all_users_invoke = True

  elif updated_fields:
    op = api_util.PatchFunction(function, updated_fields)
    if api_util.IsGcrRepository(function):
      api_util.ValidateSecureImageRepositoryOrWarn(
          function_ref.locationsId, _GetProject()
      )
  else:
    op = None  # Nothing to wait for
    if not ensure_all_users_invoke and not deny_all_users_invoke:
      log.status.Print('Nothing to update.')
      return

  stop_trying_perm_set = [False]

  # The server asyncrhonously sets allUsers invoker permissions some time after
  # we create the function. That means, to remove it, we need do so after the
  # server adds it. We can remove this mess after the default changes.
  # TODO(b/130604453): Remove the "remove" path, only bother adding. Remove the
  # logic from the polling loop. Remove the ability to add logic like this to
  # the polling loop.
  # Because of the DRS policy restrictions, private-by-default behavior is not
  # guaranteed for all projects and we need this hack until IAM deny is
  # implemented and all projects have private-by-default.
  def TryToSetInvokerPermission():
    """Try to make the invoker permission be what we said it should.

    This is for executing in the polling loop, and will stop trying as soon as
    it succeeds at making a change.
    """
    if stop_trying_perm_set[0]:
      return
    try:
      if ensure_all_users_invoke:
        api_util.AddFunctionIamPolicyBinding(function.name)
        stop_trying_perm_set[0] = True
      elif deny_all_users_invoke:
        stop_trying_perm_set[0] = (
            api_util.RemoveFunctionIamPolicyBindingIfFound(function.name)
        )
    except calliope_exceptions.HttpException:
      stop_trying_perm_set[0] = True
      log.warning(
          'Setting IAM policy failed, try `%s`'
          % _CreateBindPolicyCommand(function_ref)
      )

  log_stackdriver_url = [True]

  def TryToLogStackdriverURL(op):
    """Logs stackdriver URL.

    This is for executing in the polling loop, and will stop trying as soon as
    it succeeds at making a change.

    Args:
      op: the operation
    """
    if log_stackdriver_url[0] and op.metadata:
      metadata = encoding.PyValueToMessage(
          messages.OperationMetadataV1, encoding.MessageToPyValue(op.metadata)
      )
      if metadata.buildName and _BUILD_NAME_REGEX.match(metadata.buildName):
        log.status.Print(
            '\nFor Cloud Build Logs, visit: %s'
            % _CreateCloudBuildLogURL(metadata.buildName)
        )
        log_stackdriver_url[0] = False
      elif metadata.buildId:
        sd_info_template = '\nFor Cloud Build Stackdriver Logs, visit: %s'
        log.status.Print(
            sd_info_template
            % _CreateStackdriverURLforBuildLogs(metadata.buildId, _GetProject())
        )
        log_stackdriver_url[0] = False

  if op:
    try_set_invoker = None
    if function.httpsTrigger:
      try_set_invoker = TryToSetInvokerPermission
    api_util.WaitForFunctionUpdateOperation(
        op,
        try_set_invoker=try_set_invoker,
        on_every_poll=[TryToLogStackdriverURL],
    )
  return api_util.GetFunction(function.name)
