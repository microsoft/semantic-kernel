# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""Support library to handle the build submit."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os
import re
import uuid

from apitools.base.py import encoding
from apitools.base.py import exceptions as api_exceptions
from googlecloudsdk.api_lib.cloudbuild import cloudbuild_exceptions
from googlecloudsdk.api_lib.cloudbuild import cloudbuild_util
from googlecloudsdk.api_lib.cloudbuild import config
from googlecloudsdk.api_lib.cloudbuild import logs as cb_logs
from googlecloudsdk.api_lib.compute import utils as compute_utils
from googlecloudsdk.api_lib.storage import storage_api
from googlecloudsdk.calliope import exceptions as c_exceptions
from googlecloudsdk.command_lib.builds import flags
from googlecloudsdk.command_lib.builds import staging_bucket_util
from googlecloudsdk.command_lib.cloudbuild import execution
from googlecloudsdk.core import exceptions as core_exceptions
from googlecloudsdk.core import execution_utils
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources
from googlecloudsdk.core.util import times
import six


_CLUSTER_NAME_FMT = (
    'projects/{project}/locations/{location}/clusters/{cluster_name}'
)

_SUPPORTED_REGISTRIES = ['gcr.io', 'pkg.dev']


class BucketForbiddenError(core_exceptions.Error):
  """Error raised when the user is forbidden to use a bucket."""


class FailedBuildException(core_exceptions.Error):
  """Exception for builds that did not succeed."""

  def __init__(self, build):
    super(FailedBuildException, self).__init__(
        'build {id} completed with status "{status}"'.format(
            id=build.id, status=build.status
        )
    )


class RegionMismatchError(core_exceptions.Error):
  """User-specified build region does not match the worker pool region."""

  def __init__(self, build_region, wp_region):
    """Alert that build_region does not match wp_region.

    Args:
      build_region: str, The region specified in the build config.
      wp_region: str, The region where the worker pool is.
    """
    msg = (
        'Builds that run in a worker pool can only run in that worker '
        "pool's region. You selected %s, but your worker pool is in %s. To "
        'fix this, simply omit the --region flag.' % (build_region, wp_region)
    )
    super(RegionMismatchError, self).__init__(msg)


def _GetBuildTimeout():
  """Get the build timeout."""
  build_timeout = properties.VALUES.builds.timeout.Get()
  if build_timeout is not None:
    try:
      # A bare number is interpreted as seconds.
      build_timeout_secs = int(build_timeout)
    except ValueError:
      build_timeout_duration = times.ParseDuration(build_timeout)
      build_timeout_secs = int(build_timeout_duration.total_seconds)
    timeout_str = six.text_type(build_timeout_secs) + 's'
  else:
    timeout_str = None

  return timeout_str


def _GetBuildTag(builder) -> str:
  """Get the builder tag for input builder useful to cloudbuild.

  Args:
    builder: Google owned builder that needs to be tagged. Any other builders
      are marked as other
  Returns:
    Tag identifying the builder being used.
  """
  if (
      builder == 'gcr.io/buildpacks/builder:latest'
      or builder == 'gcr.io/buildpacks/builder'
  ):
    return 'latest'
  elif builder == 'gcr.io/buildpacks/builder:google-22':
    return 'google22'
  elif builder == 'gcr.io/buildpacks/builder:v1':
    return 'v1'
  elif builder is None:
    return 'default'
  else:
    return 'other'


def _SetBuildSteps(
    tag,
    no_cache,
    messages,
    substitutions,
    arg_config,
    no_source,
    source,
    timeout_str,
    buildpack,
    client_tag
):
  """Set build steps."""
  if tag is not None:
    if properties.VALUES.builds.check_tag.GetBool() and not any(
        reg in tag for reg in _SUPPORTED_REGISTRIES
    ):
      raise c_exceptions.InvalidArgumentException(
          '--tag', 'Tag value must be in the *gcr.io* or *pkg.dev* namespace.'
      )
    if properties.VALUES.builds.use_kaniko.GetBool():
      if no_cache:
        ttl = '0h'
      else:
        ttl = '{}h'.format(properties.VALUES.builds.kaniko_cache_ttl.Get())
      build_config = messages.Build(
          steps=[
              messages.BuildStep(
                  name=properties.VALUES.builds.kaniko_image.Get(),
                  args=[
                      '--destination',
                      tag,
                      '--cache',
                      '--cache-ttl',
                      ttl,
                      '--cache-dir',
                      '',
                  ],
              ),
          ],
          timeout=timeout_str,
          substitutions=cloudbuild_util.EncodeSubstitutions(
              substitutions, messages
          ),
      )
    else:
      if no_cache:
        raise c_exceptions.InvalidArgumentException(
            'no-cache',
            'Cannot specify --no-cache if builds/use_kaniko property is False',
        )

      if not no_source and os.path.isdir(source):
        found = False
        for filename in os.listdir(source):
          if filename == 'Dockerfile':
            found = True
            break
        if not found:
          raise c_exceptions.InvalidArgumentException(
              'source', 'Dockerfile required when specifying --tag'
          )

      build_config = messages.Build(
          images=[tag],
          steps=[
              messages.BuildStep(
                  name='gcr.io/cloud-builders/docker',
                  args=[
                      'build',
                      '--network',
                      'cloudbuild',
                      '--no-cache',
                      '-t',
                      tag,
                      '.',
                  ],
              ),
          ],
          timeout=timeout_str,
          substitutions=cloudbuild_util.EncodeSubstitutions(
              substitutions, messages
          ),
      )
  elif buildpack is not None:
    if not buildpack:
      raise c_exceptions.InvalidArgumentException(
          '--pack', 'Image value must not be empty.'
      )
    if buildpack[0].get('image') is None:
      raise c_exceptions.InvalidArgumentException(
          '--pack', 'Image value must not be empty.'
      )
    image = buildpack[0].get('image')
    if properties.VALUES.builds.check_tag.GetBool() and not any(
        reg in image for reg in _SUPPORTED_REGISTRIES
    ):
      raise c_exceptions.InvalidArgumentException(
          '--pack', 'Image value must be in the *gcr.io* or *pkg.dev* namespace'
      )
    env = buildpack[0].get('env')
    # envs example: ["key1=value1", "key2=value2"]
    envs = buildpack[0].get('envs')
    builder = buildpack[0].get('builder')
    steps = []
    pack_args = [
        'build',
        image,
        '--network',
        'cloudbuild',
    ]
    build_tags = [_GetBuildTag(builder)]
    # Keep both env and envs for backward compatibility.
    if env is not None:
      pack_args.append('--env')
      pack_args.append(env)
    if envs is not None:
      for env in envs:
        pack_args.append('--env')
        pack_args.append(env)
    if builder is not None:
      pack_args.append('--builder')
      pack_args.append(builder)
    else:
      default_buildpacks_builder = 'gcr.io/buildpacks/builder:latest'
      build_tags.append(_GetBuildTag(default_buildpacks_builder))
      # Use `pack config default-builder` to allow overriding the builder in a
      # project.toml file.
      steps = [
          messages.BuildStep(
              name='gcr.io/k8s-skaffold/pack',
              entrypoint='pack',
              args=[
                  'config',
                  'default-builder',
                  default_buildpacks_builder,
              ],
          ),
      ]

    steps.append(
        messages.BuildStep(
            name='gcr.io/k8s-skaffold/pack',
            entrypoint='pack',
            args=pack_args,
        )
    )

    client_tag = 'other' if client_tag is None else client_tag
    cloudbuild_tags = list(
        map(
            lambda x: 'gcp-runtimes-builder-' + x + '-' + client_tag,
            build_tags,
        )
    )

    build_config = messages.Build(
        images=[image],
        steps=steps,
        timeout=timeout_str,
        substitutions=cloudbuild_util.EncodeSubstitutions(
            substitutions, messages
        ),
        tags=cloudbuild_tags
    )

  else:
    if no_cache:
      raise c_exceptions.ConflictingArgumentsException('--config', '--no-cache')
    if not arg_config:
      raise c_exceptions.InvalidArgumentException(
          '--config', 'Config file path must not be empty.'
      )
    build_config = config.LoadCloudbuildConfigFromPath(
        arg_config, messages, params=substitutions
    )

  # If timeout was set by flag, overwrite the config file.
  if timeout_str:
    build_config.timeout = timeout_str

  return build_config


def SetSource(
    build_config,
    messages,
    is_specified_source,
    no_source,
    source,
    gcs_source_staging_dir,
    arg_dir,
    arg_revision,
    arg_git_source_dir,
    arg_git_source_revision,
    ignore_file,
    hide_logs=False,
    build_region=cloudbuild_util.DEFAULT_REGION,
    arg_bucket_behavior=None,
):
  """Set the source for the build config."""
  default_gcs_source = False
  default_bucket_name = None
  default_bucket_location = cloudbuild_util.DEFAULT_REGION
  if gcs_source_staging_dir is None:
    default_gcs_source = True
    if (
        build_region != cloudbuild_util.DEFAULT_REGION
        and arg_bucket_behavior is not None
        and flags.GetDefaultBuckestBehavior(arg_bucket_behavior)
        == messages.BuildOptions.DefaultLogsBucketBehaviorValueValuesEnum.REGIONAL_USER_OWNED_BUCKET
    ):
      default_bucket_location = build_region
      default_bucket_name = staging_bucket_util.GetDefaultRegionalStagingBucket(
          build_region
      )
    else:
      default_bucket_name = staging_bucket_util.GetDefaultStagingBucket()
    gcs_source_staging_dir = 'gs://{}/source'.format(default_bucket_name)
  gcs_client = storage_api.StorageClient()

  # --no-source overrides the default --source.
  if not is_specified_source and no_source:
    source = None

  if source:
    if any(source.startswith(x) for x in ['http://', 'https://']):
      build_config.source = messages.Source(
          gitSource=messages.GitSource(
              url=source,
              dir=arg_git_source_dir,
              revision=arg_git_source_revision,
          )
      )
      return build_config

    if re.match(
        r'projects/.*/locations/.*/connections/.*/repositories/.*', source
    ):
      build_config.source = messages.Source(
          connectedRepository=messages.ConnectedRepository(
              repository=source,
              dir=arg_dir,
              revision=arg_revision,
          )
      )
      return build_config

    suffix = '.tgz'
    if source.startswith('gs://') or os.path.isfile(source):
      _, suffix = os.path.splitext(source)

    # Next, stage the source to Cloud Storage.
    staged_object = '{stamp}-{uuid}{suffix}'.format(
        stamp=times.GetTimeStampFromDateTime(times.Now()),
        uuid=uuid.uuid4().hex,
        suffix=suffix,
    )
    gcs_source_staging_dir = resources.REGISTRY.Parse(
        gcs_source_staging_dir, collection='storage.objects'
    )

    try:
      if default_bucket_location == cloudbuild_util.DEFAULT_REGION:
        gcs_client.CreateBucketIfNotExists(
            gcs_source_staging_dir.bucket,
            check_ownership=default_gcs_source,
        )
      else:
        gcs_client.CreateBucketIfNotExists(
            gcs_source_staging_dir.bucket,
            location=default_bucket_location,
            check_ownership=default_gcs_source,
        )
    except api_exceptions.HttpForbiddenError:
      raise BucketForbiddenError(
          'The user is forbidden from accessing the bucket [{}]. Please check '
          "your organization's policy or if the user has the "
          '"serviceusage.services.use" permission. Giving the user Owner, '
          'Editor, or Viewer roles may also fix this issue. Alternatively, use '
          'the --no-source option and access your source code via a different '
          'method.'.format(gcs_source_staging_dir.bucket)
      )
    except storage_api.BucketInWrongProjectError:
      # If we're using the default bucket but it already exists in a different
      # project, then it could belong to a malicious attacker (b/33046325).
      raise c_exceptions.RequiredArgumentException(
          'gcs-source-staging-dir',
          'A bucket with name {} already exists and is owned by '
          'another project. Specify a bucket using '
          '--gcs-source-staging-dir.'.format(default_bucket_name),
      )

    if gcs_source_staging_dir.object:
      staged_object = gcs_source_staging_dir.object + '/' + staged_object
    gcs_source_staging = resources.REGISTRY.Create(
        collection='storage.objects',
        bucket=gcs_source_staging_dir.bucket,
        object=staged_object,
    )

    staged_source_obj = staging_bucket_util.Upload(
        source,
        gcs_source_staging,
        gcs_client,
        ignore_file=ignore_file,
        hide_logs=hide_logs,
    )
    build_config.source = messages.Source(
        storageSource=messages.StorageSource(
            bucket=staged_source_obj.bucket,
            object=staged_source_obj.name,
            generation=staged_source_obj.generation,
        )
    )
  else:
    # No source
    if not no_source:
      raise c_exceptions.InvalidArgumentException(
          '--no-source', 'To omit source, use the --no-source flag.'
      )

  return build_config


def _SetLogsBucket(build_config, arg_gcs_log_dir):
  """Set a Google Cloud Storage directory to hold build logs."""
  if arg_gcs_log_dir:
    # Parse the logs directory as a folder object.
    try:
      gcs_log_dir = resources.REGISTRY.Parse(
          arg_gcs_log_dir, collection='storage.objects'
      )
      build_config.logsBucket = (
          'gs://' + gcs_log_dir.bucket + '/' + gcs_log_dir.object
      )
      return build_config
    except resources.WrongResourceCollectionException:
      pass

    # Parse the logs directory as a bucket.
    try:
      gcs_log_dir = resources.REGISTRY.Parse(
          arg_gcs_log_dir, collection='storage.buckets'
      )
      build_config.logsBucket = 'gs://' + gcs_log_dir.bucket
    except resources.WrongResourceCollectionException as e:
      raise resources.WrongResourceCollectionException(
          expected='storage.buckets,storage.objects', got=e.got, path=e.path
      )

  return build_config


def _SetMachineType(build_config, messages, arg_machine_type):
  """Set the machine type used to run the build."""
  if arg_machine_type is not None:
    machine_type = flags.GetMachineType(arg_machine_type)
    if not build_config.options:
      build_config.options = messages.BuildOptions()
    build_config.options.machineType = machine_type

  return build_config


def _SetDiskSize(build_config, messages, arg_disk_size):
  """Set the disk size used to run the build."""
  if arg_disk_size is not None:
    disk_size = compute_utils.BytesToGb(arg_disk_size)
    if not build_config.options:
      build_config.options = messages.BuildOptions()
    build_config.options.diskSizeGb = int(disk_size)

  return build_config


def _SetWorkerPool(build_config, messages, arg_worker_pool):
  """Set the worker pool to run the build in."""
  if arg_worker_pool is not None:
    worker_pool = resources.REGISTRY.Parse(
        arg_worker_pool, collection='cloudbuild.projects.locations.workerPools'
    )
    if not build_config.options:
      build_config.options = messages.BuildOptions()
    build_config.options.pool = messages.PoolOption()
    build_config.options.pool.name = worker_pool.RelativeName()

  return build_config


def _SetWorkerPoolConfig(
    build_config, messages, arg_disk_size, arg_memory, arg_vcpu_count
):
  """Set the worker pool config."""
  if (
      (
          arg_disk_size is not None
          and cloudbuild_util.WorkerPoolIsSpecified(build_config)
      )
      or arg_memory is not None
      or arg_vcpu_count is not None
  ):
    if not build_config.options:
      build_config.options = messages.BuildOptions()

    if not build_config.options.pool:
      build_config.options.pool = messages.PoolOption()
    if not build_config.options.pool.workerConfig:
      build_config.options.pool.workerConfig = (
          messages.GoogleDevtoolsCloudbuildV1BuildOptionsPoolOptionWorkerConfig()
      )

    if arg_disk_size is not None:
      disk_size = compute_utils.BytesToGb(arg_disk_size)
      build_config.options.pool.workerConfig.diskSizeGb = disk_size
    if arg_memory is not None:
      memory = cloudbuild_util.BytesToGb(arg_memory)
      build_config.options.pool.workerConfig.memoryGb = memory
    if arg_vcpu_count is not None:
      build_config.options.pool.workerConfig.vcpuCount = arg_vcpu_count

  return build_config


def _SetDefaultLogsBucketBehavior(
    build_config, messages, arg_bucket_behavior=None
):
  """Sets the behavior of the default logs bucket on Build options.

  Args:
    build_config: apitools.base.protorpclite.messages.Message, The Build message
      to analyze.
    messages: API messages class. The CloudBuild API messages.
    arg_bucket_behavior: The default buckets behavior flag.

  Returns:
    build_config: apitools.base.protorpclite.messages.Message, The Build message
      to analyze.
  """
  if arg_bucket_behavior is not None:
    bucket_behavior = flags.GetDefaultBuckestBehavior(arg_bucket_behavior)
    if not build_config.options:
      build_config.options = messages.BuildOptions()
    build_config.options.defaultLogsBucketBehavior = bucket_behavior

  return build_config


def CreateBuildConfig(
    tag,
    no_cache,
    messages,
    substitutions,
    arg_config,
    is_specified_source,
    no_source,
    source,
    gcs_source_staging_dir,
    ignore_file,
    arg_gcs_log_dir,
    arg_machine_type,
    arg_disk_size,
    arg_worker_pool,
    arg_dir,
    arg_revision,
    arg_git_source_dir,
    arg_git_source_revision,
    buildpack,
    hide_logs=False,
    arg_bucket_behavior=None,
    skip_set_source=False,
    client_tag=None,
):
  """Returns a build config."""

  timeout_str = _GetBuildTimeout()
  build_config = _SetBuildSteps(
      tag,
      no_cache,
      messages,
      substitutions,
      arg_config,
      no_source,
      source,
      timeout_str,
      buildpack,
      client_tag
  )
  if not skip_set_source:
    build_config = SetSource(
        build_config,
        messages,
        is_specified_source,
        no_source,
        source,
        gcs_source_staging_dir,
        arg_dir,
        arg_revision,
        arg_git_source_dir,
        arg_git_source_revision,
        ignore_file,
        hide_logs=hide_logs,
    )
  build_config = _SetLogsBucket(build_config, arg_gcs_log_dir)
  build_config = _SetMachineType(build_config, messages, arg_machine_type)
  build_config = _SetDiskSize(build_config, messages, arg_disk_size)
  build_config = _SetWorkerPool(build_config, messages, arg_worker_pool)
  build_config = _SetDefaultLogsBucketBehavior(
      build_config, messages, arg_bucket_behavior
  )

  return build_config


def CreateBuildConfigAlpha(
    tag,
    no_cache,
    messages,
    substitutions,
    arg_config,
    is_specified_source,
    no_source,
    source,
    gcs_source_staging_dir,
    ignore_file,
    arg_gcs_log_dir,
    arg_machine_type,
    arg_disk_size,
    arg_memory,
    arg_vcpu_count,
    arg_worker_pool,
    arg_dir,
    arg_revision,
    arg_git_source_dir,
    arg_git_source_revision,
    buildpack,
    hide_logs=False,
    arg_bucket_behavior=None,
    skip_set_source=False,
    client_tag=None,
):
  """Returns a build config."""
  timeout_str = _GetBuildTimeout()

  build_config = _SetBuildSteps(
      tag,
      no_cache,
      messages,
      substitutions,
      arg_config,
      no_source,
      source,
      timeout_str,
      buildpack,
      client_tag
  )
  if not skip_set_source:
    build_config = SetSource(
        build_config,
        messages,
        is_specified_source,
        no_source,
        source,
        gcs_source_staging_dir,
        arg_dir,
        arg_revision,
        arg_git_source_dir,
        arg_git_source_revision,
        ignore_file,
        hide_logs=hide_logs,
    )
  build_config = _SetLogsBucket(build_config, arg_gcs_log_dir)
  build_config = _SetMachineType(build_config, messages, arg_machine_type)
  build_config = _SetWorkerPool(build_config, messages, arg_worker_pool)
  build_config = _SetWorkerPoolConfig(
      build_config, messages, arg_disk_size, arg_memory, arg_vcpu_count
  )
  build_config = _SetDefaultLogsBucketBehavior(
      build_config, messages, arg_bucket_behavior
  )

  if cloudbuild_util.WorkerPoolConfigIsSpecified(
      build_config
  ) and not cloudbuild_util.WorkerPoolIsSpecified(build_config):
    raise cloudbuild_exceptions.WorkerConfigButNoWorkerpoolError

  if not cloudbuild_util.WorkerPoolIsSpecified(build_config):
    build_config = _SetDiskSize(build_config, messages, arg_disk_size)

  return build_config


def DetermineBuildRegion(build_config, desired_region=None):
  """Determine what region of the GCB service this build should be sent to.

  Args:
    build_config: apitools.base.protorpclite.messages.Message, The Build message
      to analyze.
    desired_region: str, The region requested by the user, if any.

  Raises:
    RegionMismatchError: If the config conflicts with the desired region.

  Returns:
    str, The region that the build should be sent to, or None if it should be
    sent to the global region.

  Note: we do not validate region strings so that old versions of gcloud are
  able to access new regions. This is aligned with the approach used by other
  teams.
  """
  # If the build is configured to run in a worker pool, use the worker
  # pool's resource ID to determine which regional GCB service to send it to.
  wp_options = build_config.options
  if not wp_options:
    return desired_region
  wp_resource = wp_options.pool.name if wp_options.pool else ''
  if not wp_resource:
    wp_resource = wp_options.workerPool
  if not wp_resource:
    return desired_region
  if not cloudbuild_util.IsWorkerPool(wp_resource):
    return desired_region
  wp_region = cloudbuild_util.WorkerPoolRegion(wp_resource)
  # If the configuration includes a substitution for the region, and the user
  # fails to include a --region flag, issue a warning
  matches = []
  if build_config.substitutions and wp_region:
    substitution_keys = list(
        p.key for p in build_config.substitutions.additionalProperties
    )
    matches = [(k in wp_region) for k in substitution_keys]
  if (not desired_region) and wp_region and matches:
    raise c_exceptions.InvalidArgumentException(
        '--region',
        (
            '--region flag required when workerpool resource includes region '
            'substitution'
        ),
    )
  # Prefer the region specified in the command line flag
  if desired_region and desired_region != wp_region:
    return desired_region
  return wp_region


def Build(
    messages,
    async_,
    build_config,
    hide_logs=False,
    build_region=cloudbuild_util.DEFAULT_REGION,
    support_gcl=False,
    suppress_logs=False,
    skip_activation_prompt=False,
):
  """Starts the build."""
  log.debug('submitting build: ' + repr(build_config))
  client = cloudbuild_util.GetClientInstance(
      skip_activation_prompt=skip_activation_prompt
  )

  parent_resource = resources.REGISTRY.Create(
      collection='cloudbuild.projects.locations',
      projectsId=properties.VALUES.core.project.GetOrFail(),
      locationsId=build_region,
  )

  op = client.projects_locations_builds.Create(
      messages.CloudbuildProjectsLocationsBuildsCreateRequest(
          parent=parent_resource.RelativeName(), build=build_config
      )
  )

  json = encoding.MessageToJson(op.metadata)
  build = encoding.JsonToMessage(messages.BuildOperationMetadata, json).build

  # Need to set the default version to 'v1'
  build_ref = resources.REGISTRY.Parse(
      None,
      collection='cloudbuild.projects.locations.builds',
      api_version='v1',
      params={
          'projectsId': build.projectId,
          'locationsId': build_region,
          'buildsId': build.id,
      },
  )

  if not hide_logs:
    log.CreatedResource(build_ref)
    if build.logUrl:
      log.status.Print(
          'Logs are available at [ {log_url} ].'.format(log_url=build.logUrl)
      )
    else:
      log.status.Print('Logs are available in the Cloud Console.')

  # If the command is run --async, we just print out a reference to the build.
  if async_:
    return build, op

  if (
      not support_gcl
      and build.options
      and build.options.logging
      in [
          messages.BuildOptions.LoggingValueValuesEnum.STACKDRIVER_ONLY,
          messages.BuildOptions.LoggingValueValuesEnum.CLOUD_LOGGING_ONLY,
      ]
  ):
    log.status.Print(
        '\ngcloud builds submit only displays logs from Cloud'
        ' Storage. To view logs from Cloud Logging, run:\ngcloud'
        ' beta builds submit\n'
    )

  mash_handler = execution.MashHandler(
      execution.GetCancelBuildHandler(client, messages, build_ref)
  )

  out = log.out if not suppress_logs else None
  # Otherwise, logs are streamed from the chosen logging service
  # (defaulted to GCS).
  with execution_utils.CtrlCSection(mash_handler):
    build = cb_logs.CloudBuildClient(client, messages, support_gcl).Stream(
        build_ref, out
    )

  if build.status == messages.Build.StatusValueValuesEnum.TIMEOUT:
    log.status.Print(
        'Your build timed out. Use the [--timeout=DURATION] flag to change '
        'the timeout threshold.'
    )

  if build.warnings:
    for warn in build.warnings:
      log.status.Print(
          '\n{priority}: {text}'.format(text=warn.text, priority=warn.priority)
      )

    log.status.Print(
        '\n{count} message(s) issued.'.format(count=len(build.warnings))
    )

  if build.failureInfo:
    log.status.Print(
        '\nBUILD FAILURE: {detail}'.format(detail=build.failureInfo.detail)
    )

  if build.status != messages.Build.StatusValueValuesEnum.SUCCESS:
    raise FailedBuildException(build)

  return build, op
