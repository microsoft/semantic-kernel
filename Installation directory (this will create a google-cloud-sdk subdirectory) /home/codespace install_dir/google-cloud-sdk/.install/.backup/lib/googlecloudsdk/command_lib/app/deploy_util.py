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
"""Utilities for `gcloud app` deployment.

Mostly created to selectively enable Cloud Endpoints in the beta/preview release
tracks.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import enum
import os
import re

from apitools.base.py import exceptions as apitools_exceptions
from googlecloudsdk.api_lib import scheduler
from googlecloudsdk.api_lib import tasks
from googlecloudsdk.api_lib.app import build as app_cloud_build
from googlecloudsdk.api_lib.app import deploy_app_command_util
from googlecloudsdk.api_lib.app import deploy_command_util
from googlecloudsdk.api_lib.app import env
from googlecloudsdk.api_lib.app import metric_names
from googlecloudsdk.api_lib.app import runtime_builders
from googlecloudsdk.api_lib.app import util
from googlecloudsdk.api_lib.app import version_util
from googlecloudsdk.api_lib.app import yaml_parsing
from googlecloudsdk.api_lib.datastore import index_api
from googlecloudsdk.api_lib.storage import storage_util
from googlecloudsdk.api_lib.tasks import app_deploy_migration_util
from googlecloudsdk.api_lib.util import exceptions as core_api_exceptions
from googlecloudsdk.calliope import actions
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.app import create_util
from googlecloudsdk.command_lib.app import deployables
from googlecloudsdk.command_lib.app import exceptions
from googlecloudsdk.command_lib.app import flags
from googlecloudsdk.command_lib.app import output_helpers
from googlecloudsdk.command_lib.app import source_files_util
from googlecloudsdk.command_lib.app import staging
from googlecloudsdk.core import exceptions as core_exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core import metrics
from googlecloudsdk.core import properties
from googlecloudsdk.core.configurations import named_configs
from googlecloudsdk.core.console import console_io
from googlecloudsdk.core.console import progress_tracker
from googlecloudsdk.core.util import files
from googlecloudsdk.core.util import times
import six

_TASK_CONSOLE_LINK = """\
https://console.cloud.google.com/appengine/taskqueues/cron?project={}
"""

# The regex for runtimes prior to runtime builders support. Used to deny the
# use of pinned runtime builders when this feature is disabled.
ORIGINAL_RUNTIME_RE_STRING = r'[a-z][a-z0-9\-]{0,29}'
ORIGINAL_RUNTIME_RE = re.compile(ORIGINAL_RUNTIME_RE_STRING + r'\Z')

# Max App Engine file size; see https://cloud.google.com/appengine/docs/quotas
_MAX_FILE_SIZE_STANDARD = 32 * 1024 * 1024

# 1rst gen runtimes that still need the _MAX_FILE_SIZE_STANDARD check:
_RUNTIMES_WITH_FILE_SIZE_LIMITS = [
    'java7', 'java8', 'java8g', 'python27', 'go19', 'php55'
]


class Error(core_exceptions.Error):
  """Base error for this module."""


class VersionPromotionError(Error):

  def __init__(self, err_str):
    super(VersionPromotionError, self).__init__(
        'Your deployment has succeeded, but promoting the new version to '
        'default failed. '
        'You may not have permissions to change traffic splits. '
        'Changing traffic splits requires the Owner, Editor, App Engine Admin, '
        'or App Engine Service Admin role. '
        'Please contact your project owner and use the '
        '`gcloud app services set-traffic --splits <version>=1` command to '
        'redirect traffic to your newly deployed version.\n\n'
        'Original error: ' + err_str)


class StoppedApplicationError(Error):
  """Error if deployment fails because application is stopped/disabled."""

  def __init__(self, app):
    super(StoppedApplicationError, self).__init__(
        'Unable to deploy to application [{}] with status [{}]: Deploying '
        'to stopped apps is not allowed.'.format(app.id, app.servingStatus))


class InvalidRuntimeNameError(Error):
  """Error for runtime names that are not allowed in the given environment."""

  def __init__(self, runtime, allowed_regex):
    super(InvalidRuntimeNameError,
          self).__init__('Invalid runtime name: [{}]. '
                         'Must match regular expression [{}].'.format(
                             runtime, allowed_regex))


class RequiredFileMissingError(Error):
  """Error for skipped/ignored files that must be uploaded."""

  def __init__(self, filename):
    super(RequiredFileMissingError, self).__init__(
        'Required file is not uploaded: [{}]. '
        'This file should not be added to an ignore list ('
        'https://cloud.google.com/sdk/gcloud/reference/topic/gcloudignore)'
        .format(filename))


class FlexImageBuildOptions(enum.Enum):
  """Enum declaring different options for building image for flex deploys."""
  ON_CLIENT = 1
  ON_SERVER = 2
  BUILDPACK_ON_CLIENT = 3


def GetFlexImageBuildOption(default_strategy=FlexImageBuildOptions.ON_CLIENT):
  """Determines where the build should be performed."""
  trigger_build_server_side = (
      properties.VALUES.app.trigger_build_server_side.GetBool(required=False))
  use_flex_with_buildpacks = (
      properties.VALUES.app.use_flex_with_buildpacks.GetBool(required=False))

  if trigger_build_server_side:
    result = FlexImageBuildOptions.ON_SERVER
  elif (trigger_build_server_side is None and not use_flex_with_buildpacks):
    result = default_strategy
  elif use_flex_with_buildpacks:
    result = FlexImageBuildOptions.BUILDPACK_ON_CLIENT
  else:
    result = FlexImageBuildOptions.ON_CLIENT

  log.debug('Flex image build option: %s', result)
  return result


class DeployOptions(object):
  """Values of options that affect deployment process in general.

  No deployment details (e.g. sources for a specific deployment).

  Attributes:
    promote: True if the deployed version should receive all traffic.
    stop_previous_version: Stop previous version
    runtime_builder_strategy: runtime_builders.RuntimeBuilderStrategy, when to
      use the new CloudBuild-based runtime builders (alternative is old
      externalized runtimes).
    parallel_build: bool, whether to use parallel build and deployment path.
      Only supported in v1beta and v1alpha App Engine Admin API.
    flex_image_build_option: FlexImageBuildOptions, whether a flex deployment
      should upload files so that the server can build the image, or build the
      image on client, or build the image on client using the buildpacks.
  """

  def __init__(self,
               promote,
               stop_previous_version,
               runtime_builder_strategy,
               parallel_build=False,
               flex_image_build_option=FlexImageBuildOptions.ON_CLIENT):
    self.promote = promote
    self.stop_previous_version = stop_previous_version
    self.runtime_builder_strategy = runtime_builder_strategy
    self.parallel_build = parallel_build
    self.flex_image_build_option = flex_image_build_option

  @classmethod
  def FromProperties(cls,
                     runtime_builder_strategy,
                     parallel_build=False,
                     flex_image_build_option=FlexImageBuildOptions.ON_CLIENT):
    """Initialize DeloyOptions using user properties where necessary.

    Args:
      runtime_builder_strategy: runtime_builders.RuntimeBuilderStrategy, when to
        use the new CloudBuild-based runtime builders (alternative is old
        externalized runtimes).
      parallel_build: bool, whether to use parallel build and deployment path.
        Only supported in v1beta and v1alpha App Engine Admin API.
      flex_image_build_option: FlexImageBuildOptions, whether a flex deployment
        should upload files so that the server can build the image or build the
        image on client or build the image on client using the buildpacks.

    Returns:
      DeployOptions, the deploy options.
    """
    promote = properties.VALUES.app.promote_by_default.GetBool()
    stop_previous_version = (
        properties.VALUES.app.stop_previous_version.GetBool())
    return cls(promote, stop_previous_version, runtime_builder_strategy,
               parallel_build, flex_image_build_option)


class ServiceDeployer(object):
  """Coordinator (reusable) for deployment of one service at a time.

  Attributes:
    api_client: api_lib.app.appengine_api_client.AppengineClient, App Engine
      Admin API client.
    deploy_options: DeployOptions, the options to use for services deployed by
      this ServiceDeployer.
  """

  def __init__(self, api_client, deploy_options):
    self.api_client = api_client
    self.deploy_options = deploy_options

  def _ValidateRuntime(self, service_info):
    """Validates explicit runtime builders are not used without the feature on.

    Args:
      service_info: yaml_parsing.ServiceYamlInfo, service configuration to be
        deployed

    Raises:
      InvalidRuntimeNameError: if the runtime name is invalid for the deployment
        (see above).
    """
    runtime = service_info.runtime
    if runtime == 'custom':
      return

    # This may or may not be accurate, but it only matters for custom runtimes,
    # which are handled above.
    needs_dockerfile = True
    strategy = self.deploy_options.runtime_builder_strategy
    use_runtime_builders = deploy_command_util.ShouldUseRuntimeBuilders(
        service_info, strategy, needs_dockerfile)
    if not use_runtime_builders and not ORIGINAL_RUNTIME_RE.match(runtime):
      raise InvalidRuntimeNameError(runtime, ORIGINAL_RUNTIME_RE_STRING)

  def _PossiblyBuildAndPush(self, new_version, service, upload_dir,
                            source_files, image, code_bucket_ref, gcr_domain,
                            flex_image_build_option):
    """Builds and Pushes the Docker image if necessary for this service.

    Args:
      new_version: version_util.Version describing where to deploy the service
      service: yaml_parsing.ServiceYamlInfo, service configuration to be
        deployed
      upload_dir: str, path to the service's upload directory
      source_files: [str], relative paths to upload.
      image: str or None, the URL for the Docker image to be deployed (if image
        already exists).
      code_bucket_ref: cloud_storage.BucketReference where the service's files
        have been uploaded
      gcr_domain: str, Cloud Registry domain, determines the physical location
        of the image. E.g. `us.gcr.io`.
      flex_image_build_option: FlexImageBuildOptions, whether a flex deployment
        should upload files so that the server can build the image or build the
        image on client or build the image on client using the buildpacks.

    Returns:
      BuildArtifact, a wrapper which contains either the build ID for
        an in-progress build, or the name of the container image for a serial
        build. Possibly None if the service does not require an image.
    Raises:
      RequiredFileMissingError: if a required file is not uploaded.
    """
    build = None
    if image:
      if service.RequiresImage() and service.parsed.skip_files.regex:
        log.warning('Deployment of service [{0}] will ignore the skip_files '
                    'field in the configuration file, because the image has '
                    'already been built.'.format(new_version.service))
      return app_cloud_build.BuildArtifact.MakeImageArtifact(image)
    elif service.RequiresImage():
      if not _AppYamlInSourceFiles(source_files, service.GetAppYamlBasename()):
        raise RequiredFileMissingError(service.GetAppYamlBasename())

      if flex_image_build_option == FlexImageBuildOptions.ON_SERVER:
        cloud_build_options = {
            'appYamlPath': service.GetAppYamlBasename(),
        }
        timeout = properties.VALUES.app.cloud_build_timeout.Get()
        if timeout:
          build_timeout = int(
              times.ParseDuration(timeout, default_suffix='s').total_seconds)
          cloud_build_options['cloudBuildTimeout'] = six.text_type(
              build_timeout) + 's'
        build = app_cloud_build.BuildArtifact.MakeBuildOptionsArtifact(
            cloud_build_options)
      else:
        build = deploy_command_util.BuildAndPushDockerImage(
            new_version.project, service, upload_dir, source_files,
            new_version.id, code_bucket_ref, gcr_domain,
            self.deploy_options.runtime_builder_strategy,
            self.deploy_options.parallel_build, flex_image_build_option ==
            FlexImageBuildOptions.BUILDPACK_ON_CLIENT)

    return build

  def _PossiblyPromote(self, all_services, new_version, wait_for_stop_version):
    """Promotes the new version to default (if specified by the user).

    Args:
      all_services: dict of service ID to service_util.Service objects
        corresponding to all pre-existing services (used to determine how to
        promote this version to receive all traffic, if applicable).
      new_version: version_util.Version describing where to deploy the service
      wait_for_stop_version: bool, indicating whether to wait for stop operation
        to finish.

    Raises:
      VersionPromotionError: if the version could not successfully promoted
    """
    if self.deploy_options.promote:
      try:
        version_util.PromoteVersion(all_services, new_version, self.api_client,
                                    self.deploy_options.stop_previous_version,
                                    wait_for_stop_version)
      except apitools_exceptions.HttpError as err:
        err_str = six.text_type(core_api_exceptions.HttpException(err))
        raise VersionPromotionError(err_str)
    elif self.deploy_options.stop_previous_version:
      log.info('Not stopping previous version because new version was '
               'not promoted.')

  def _PossiblyUploadFiles(self, image, service_info, upload_dir, source_files,
                           code_bucket_ref, flex_image_build_option):
    """Uploads files for this deployment is required for this service.

    Uploads if flex_image_build_option is FlexImageBuildOptions.ON_SERVER,
    or if the deployment is non-hermetic and the image is not provided.

    Args:
      image: str or None, the URL for the Docker image to be deployed (if image
        already exists).
      service_info: yaml_parsing.ServiceYamlInfo, service configuration to be
        deployed
      upload_dir: str, path to the service's upload directory
      source_files: [str], relative paths to upload.
      code_bucket_ref: cloud_storage.BucketReference where the service's files
        have been uploaded
      flex_image_build_option: FlexImageBuildOptions, whether a flex deployment
        should upload files so that the server can build the image or build the
        image on client or build the image on client using the buildpacks.

    Returns:
      Dictionary mapping source files to Google Cloud Storage locations.

    Raises:
      RequiredFileMissingError: if a required file is not uploaded.
    """
    manifest = None
    # "Non-hermetic" services require file upload outside the Docker image
    # unless an image was already built.
    if (not image and
        (flex_image_build_option == FlexImageBuildOptions.ON_SERVER or
         not service_info.is_hermetic)):
      if (service_info.env == env.FLEX and not _AppYamlInSourceFiles(
          source_files, service_info.GetAppYamlBasename())):
        raise RequiredFileMissingError(service_info.GetAppYamlBasename())

      limit = None
      if (service_info.env == env.STANDARD and
          service_info.runtime in _RUNTIMES_WITH_FILE_SIZE_LIMITS):
        limit = _MAX_FILE_SIZE_STANDARD
      manifest = deploy_app_command_util.CopyFilesToCodeBucket(
          upload_dir, source_files, code_bucket_ref, max_file_size=limit)
    return manifest

  def Deploy(self,
             service,
             new_version,
             code_bucket_ref,
             image,
             all_services,
             gcr_domain,
             disable_build_cache,
             wait_for_stop_version,
             flex_image_build_option=FlexImageBuildOptions.ON_CLIENT,
             ignore_file=None,
             service_account=None):
    """Deploy the given service.

    Performs all deployment steps for the given service (if applicable):
    * Enable endpoints (for beta deployments)
    * Build and push the Docker image (Flex only, if image_url not provided)
    * Upload files (non-hermetic deployments and flex deployments with
      flex_image_build_option=FlexImageBuildOptions.ON_SERVER)
    * Create the new version
    * Promote the version to receive all traffic (if --promote given (default))
    * Stop the previous version (if new version promoted and
      --stop-previous-version given (default))

    Args:
      service: deployables.Service, service to be deployed.
      new_version: version_util.Version describing where to deploy the service
      code_bucket_ref: cloud_storage.BucketReference where the service's files
        will be uploaded
      image: str or None, the URL for the Docker image to be deployed (if image
        already exists).
      all_services: dict of service ID to service_util.Service objects
        corresponding to all pre-existing services (used to determine how to
        promote this version to receive all traffic, if applicable).
      gcr_domain: str, Cloud Registry domain, determines the physical location
        of the image. E.g. `us.gcr.io`.
      disable_build_cache: bool, disable the build cache.
      wait_for_stop_version: bool, indicating whether to wait for stop operation
        to finish.
      flex_image_build_option: FlexImageBuildOptions, whether a flex deployment
        should upload files so that the server can build the image or build the
        image on client or build the image on client using the buildpacks.
      ignore_file: custom ignore_file name. Override .gcloudignore file to
        customize files to be skipped.
      service_account: identity this version runs as. If not set, Admin API will
        fallback to use the App Engine default appspot SA.
    """
    log.status.Print('Beginning deployment of service [{service}]...'.format(
        service=new_version.service))
    if (service.service_info.env == env.MANAGED_VMS and
        flex_image_build_option == FlexImageBuildOptions.ON_SERVER):
      # Server-side builds are not supported for Managed VMs.
      flex_image_build_option = FlexImageBuildOptions.ON_CLIENT

    service_info = service.service_info
    self._ValidateRuntime(service_info)

    source_files = source_files_util.GetSourceFiles(
        service.upload_dir,
        service_info.parsed.skip_files.regex,
        service_info.HasExplicitSkipFiles(),
        service_info.runtime,
        service_info.env,
        service.source,
        ignore_file=ignore_file)

    # Tar-based upload for flex
    build = self._PossiblyBuildAndPush(new_version, service_info,
                                       service.upload_dir, source_files, image,
                                       code_bucket_ref, gcr_domain,
                                       flex_image_build_option)

    # Manifest-based incremental source upload for all envs
    manifest = self._PossiblyUploadFiles(image, service_info,
                                         service.upload_dir, source_files,
                                         code_bucket_ref,
                                         flex_image_build_option)

    del source_files  # Free some memory

    extra_config_settings = {}
    if disable_build_cache:
      extra_config_settings['no-cache'] = 'true'

    # Actually create the new version of the service.
    metrics.CustomTimedEvent(metric_names.DEPLOY_API_START)
    self.api_client.DeployService(new_version.service, new_version.id,
                                  service_info, manifest, build,
                                  extra_config_settings, service_account)
    metrics.CustomTimedEvent(metric_names.DEPLOY_API)
    self._PossiblyPromote(all_services, new_version, wait_for_stop_version)


def ArgsDeploy(parser):
  """Get arguments for this command.

  Args:
    parser: argparse.ArgumentParser, the parser for this command.
  """
  flags.SERVER_FLAG.AddToParser(parser)
  flags.IGNORE_CERTS_FLAG.AddToParser(parser)
  flags.DOCKER_BUILD_FLAG.AddToParser(parser)
  flags.IGNORE_FILE_FLAG.AddToParser(parser)
  parser.add_argument(
      '--version',
      '-v',
      type=flags.VERSION_TYPE,
      help='The version of the app that will be created or replaced by this '
      'deployment.  If you do not specify a version, one will be generated for '
      'you.')
  parser.add_argument(
      '--bucket',
      type=storage_util.BucketReference.FromArgument,
      help=('The Google Cloud Storage bucket used to stage files associated '
            'with the deployment. If this argument is not specified, the '
            "application's default code bucket is used."))
  parser.add_argument(
      '--service-account',
      help=('The service account that this deployed version will run as. '
            'If this argument is not specified, the App Engine default '
            'service account will be used for your current deployed version.'))
  parser.add_argument(
      'deployables',
      nargs='*',
      help="""\
      The yaml files for the services or configurations you want to deploy.
      If not given, defaults to `app.yaml` in the current directory.
      If that is not found, attempts to automatically generate necessary
      configuration files (such as app.yaml) in the current directory.""")
  parser.add_argument(
      '--stop-previous-version',
      action=actions.StoreBooleanProperty(
          properties.VALUES.app.stop_previous_version),
      help="""\
      Stop the previously running version when deploying a new version that
      receives all traffic.

      Note that if the version is running on an instance
      of an auto-scaled service in the App Engine Standard
      environment, using `--stop-previous-version` will not work
      and the previous version will continue to run because auto-scaled service
      instances are always running.""")
  parser.add_argument(
      '--image-url',
      help='(App Engine flexible environment only.) Deploy with a specific '
      'Docker image. Docker url must be from one of the valid Container '
      'Registry hostnames.')
  parser.add_argument(
      '--appyaml',
      help='Deploy with a specific app.yaml that will replace '
      'the one defined in the DEPLOYABLE.')
  parser.add_argument(
      '--promote',
      action=actions.StoreBooleanProperty(
          properties.VALUES.app.promote_by_default),
      help='Promote the deployed version to receive all traffic.')
  parser.add_argument(
      '--cache',
      action='store_true',
      default=True,
      help='Enable caching mechanisms involved in the deployment process, '
      'particularly in the build step.')
  staging_group = parser.add_mutually_exclusive_group(hidden=True)
  staging_group.add_argument(
      '--skip-staging',
      action='store_true',
      default=False,
      help='THIS ARGUMENT NEEDS HELP TEXT.')
  staging_group.add_argument(
      '--staging-command', help='THIS ARGUMENT NEEDS HELP TEXT.')


def _MakeStager(skip_staging, use_beta_stager, staging_command, staging_area):
  """Creates the appropriate stager for the given arguments/release track.

  The stager is responsible for invoking the right local staging depending on
  env and runtime.

  Args:
    skip_staging: bool, if True use a no-op Stager. Takes precedence over other
      arguments.
    use_beta_stager: bool, if True, use a stager that includes beta staging
      commands.
    staging_command: str, path to an executable on disk. If given, use this
      command explicitly for staging. Takes precedence over later arguments.
    staging_area: str, the path to the staging area

  Returns:
    staging.Stager, the appropriate stager for the command
  """
  if skip_staging:
    return staging.GetNoopStager(staging_area)
  elif staging_command:
    command = staging.ExecutableCommand.FromInput(staging_command)
    return staging.GetOverrideStager(command, staging_area)
  elif use_beta_stager:
    return staging.GetBetaStager(staging_area)
  else:
    return staging.GetStager(staging_area)


def RunDeploy(
    args,
    api_client,
    use_beta_stager=False,
    runtime_builder_strategy=runtime_builders.RuntimeBuilderStrategy.NEVER,
    parallel_build=True,
    flex_image_build_option=FlexImageBuildOptions.ON_CLIENT,
):
  """Perform a deployment based on the given args.

  Args:
    args: argparse.Namespace, An object that contains the values for the
      arguments specified in the ArgsDeploy() function.
    api_client: api_lib.app.appengine_api_client.AppengineClient, App Engine
      Admin API client.
    use_beta_stager: Use the stager registry defined for the beta track rather
      than the default stager registry.
    runtime_builder_strategy: runtime_builders.RuntimeBuilderStrategy, when to
      use the new CloudBuild-based runtime builders (alternative is old
      externalized runtimes).
    parallel_build: bool, whether to use parallel build and deployment path.
      Only supported in v1beta and v1alpha App Engine Admin API.
    flex_image_build_option: FlexImageBuildOptions, whether a flex deployment
      should upload files so that the server can build the image or build the
      image on client or build the image on client using the buildpacks.

  Returns:
    A dict on the form `{'versions': new_versions, 'configs': updated_configs}`
    where new_versions is a list of version_util.Version, and updated_configs
    is a list of config file identifiers, see yaml_parsing.ConfigYamlInfo.
  """
  project = properties.VALUES.core.project.Get(required=True)
  deploy_options = DeployOptions.FromProperties(
      runtime_builder_strategy=runtime_builder_strategy,
      parallel_build=parallel_build,
      flex_image_build_option=flex_image_build_option)

  with files.TemporaryDirectory() as staging_area:
    stager = _MakeStager(args.skip_staging, use_beta_stager,
                         args.staging_command, staging_area)
    services, configs = deployables.GetDeployables(
        args.deployables, stager, deployables.GetPathMatchers(), args.appyaml)

    wait_for_stop_version = _CheckIfConfigsContainDispatch(configs)

    service_infos = [d.service_info for d in services]

    flags.ValidateImageUrl(args.image_url, service_infos)

    # pylint: disable=protected-access
    log.debug('API endpoint: [{endpoint}], API version: [{version}]'.format(
        endpoint=api_client.client.url, version=api_client.client._VERSION))
    app = _PossiblyCreateApp(api_client, project)
    _RaiseIfStopped(api_client, app)

    # Call _PossiblyRepairApp when --bucket param is unspecified
    if not args.bucket:
      app = _PossiblyRepairApp(api_client, app)

    # Tell the user what is going to happen, and ask them to confirm.
    version_id = args.version or util.GenerateVersionId()
    deployed_urls = output_helpers.DisplayProposedDeployment(
        app, project, services, configs, version_id, deploy_options.promote,
        args.service_account, api_client.client._VERSION)
    console_io.PromptContinue(cancel_on_no=True)
    if service_infos:
      # Do generic app setup if deploying any services.
      # All deployment paths for a service involve uploading source to GCS.
      metrics.CustomTimedEvent(metric_names.GET_CODE_BUCKET_START)
      code_bucket_ref = args.bucket or flags.GetCodeBucket(app, project)
      metrics.CustomTimedEvent(metric_names.GET_CODE_BUCKET)
      log.debug('Using bucket [{b}].'.format(b=code_bucket_ref.ToUrl()))

      # Prepare Flex if any service is going to deploy an image.
      if any([s.RequiresImage() for s in service_infos]):
        deploy_command_util.PossiblyEnableFlex(project)

      all_services = dict([(s.id, s) for s in api_client.ListServices()])
    else:
      code_bucket_ref = None
      all_services = {}
    new_versions = []
    deployer = ServiceDeployer(api_client, deploy_options)

    # Track whether a service has been deployed yet, for metrics.
    service_deployed = False
    for service in services:
      if not service_deployed:
        metrics.CustomTimedEvent(metric_names.FIRST_SERVICE_DEPLOY_START)
      new_version = version_util.Version(project, service.service_id,
                                         version_id)
      deployer.Deploy(
          service,
          new_version,
          code_bucket_ref,
          args.image_url,
          all_services,
          app.gcrDomain,
          disable_build_cache=(not args.cache),
          wait_for_stop_version=wait_for_stop_version,
          flex_image_build_option=flex_image_build_option,
          ignore_file=args.ignore_file,
          service_account=args.service_account)
      new_versions.append(new_version)
      log.status.Print('Deployed service [{0}] to [{1}]'.format(
          service.service_id, deployed_urls[service.service_id]))
      if not service_deployed:
        metrics.CustomTimedEvent(metric_names.FIRST_SERVICE_DEPLOY)
      service_deployed = True

  # Deploy config files.
  if configs:
    metrics.CustomTimedEvent(metric_names.UPDATE_CONFIG_START)
    for config in configs:
      message = 'Updating config [{config}]'.format(config=config.name)
      with progress_tracker.ProgressTracker(message):
        if config.name == 'dispatch':
          api_client.UpdateDispatchRules(config.GetRules())
        elif config.name == yaml_parsing.ConfigYamlInfo.INDEX:
          index_api.CreateMissingIndexes(project, config.parsed)
        elif config.name == yaml_parsing.ConfigYamlInfo.QUEUE:
          RunDeployCloudTasks(config)
        elif config.name == yaml_parsing.ConfigYamlInfo.CRON:
          RunDeployCloudScheduler(config)
        else:
          raise ValueError(
              'Unkonwn config [{config}]'.format(config=config.name)
          )
    metrics.CustomTimedEvent(metric_names.UPDATE_CONFIG)

  updated_configs = [c.name for c in configs]

  PrintPostDeployHints(new_versions, updated_configs)

  # Return all the things that were deployed.
  return {'versions': new_versions, 'configs': updated_configs}


def RunDeployCloudTasks(config):
  """Perform a deployment using Cloud Tasks API based on the given args.

  Args:
    config: A yaml_parsing.ConfigYamlInfo object for the parsed YAML file we are
      going to process.

  Returns:
    A list of config file identifiers, see yaml_parsing.ConfigYamlInfo.
  """
  # TODO(b/169069379): Upgrade to use GA once the relevant code is promoted
  tasks_api = tasks.GetApiAdapter(base.ReleaseTrack.BETA)
  queues_data = app_deploy_migration_util.FetchCurrentQueuesData(tasks_api)
  app_deploy_migration_util.ValidateQueueYamlFileConfig(config)
  app_deploy_migration_util.DeployQueuesYamlFile(tasks_api, config, queues_data)


def RunDeployCloudScheduler(config):
  """Perform a deployment using Cloud Scheduler APIs based on the given args.

  Args:
    config: A yaml_parsing.ConfigYamlInfo object for the parsed YAML file we are
      going to process.

  Returns:
    A list of config file identifiers, see yaml_parsing.ConfigYamlInfo.
  """
  # TODO(b/169069379): Upgrade to use GA once the relevant code is promoted
  scheduler_api = scheduler.GetApiAdapter(
      base.ReleaseTrack.BETA, legacy_cron=True)
  jobs_data = app_deploy_migration_util.FetchCurrentJobsData(scheduler_api)
  app_deploy_migration_util.ValidateCronYamlFileConfig(config)
  app_deploy_migration_util.DeployCronYamlFile(scheduler_api, config, jobs_data)


# TODO(b/30632016): Move to Epilog() when we have a good way to pass
# information about the deployed versions
def PrintPostDeployHints(new_versions, updated_configs):
  """Print hints for user at the end of a deployment."""
  if yaml_parsing.ConfigYamlInfo.CRON in updated_configs:
    log.status.Print('\nCron jobs have been updated.')
    if yaml_parsing.ConfigYamlInfo.QUEUE not in updated_configs:
      log.status.Print('\nVisit the Cloud Platform Console Task Queues page '
                       'to view your queues and cron jobs.')
      log.status.Print(
          _TASK_CONSOLE_LINK.format(properties.VALUES.core.project.Get()))
  if yaml_parsing.ConfigYamlInfo.DISPATCH in updated_configs:
    log.status.Print('\nCustom routings have been updated.')
  if yaml_parsing.ConfigYamlInfo.QUEUE in updated_configs:
    log.status.Print('\nTask queues have been updated.')
    log.status.Print('\nVisit the Cloud Platform Console Task Queues page '
                     'to view your queues and cron jobs.')
  if yaml_parsing.ConfigYamlInfo.INDEX in updated_configs:
    log.status.Print('\nIndexes are being rebuilt. This may take a moment.')

  if not new_versions:
    return
  elif len(new_versions) > 1:
    service_hint = ' -s <service>'
  elif new_versions[0].service == 'default':
    service_hint = ''
  else:
    service = new_versions[0].service
    service_hint = ' -s {svc}'.format(svc=service)

  proj_conf = named_configs.ActivePropertiesFile.Load().Get('core', 'project')
  project = properties.VALUES.core.project.Get()
  if proj_conf != project:
    project_hint = ' --project=' + project
  else:
    project_hint = ''
  log.status.Print('\nYou can stream logs from the command line by running:\n'
                   '  $ gcloud app logs tail' + (service_hint or ' -s default'))
  log.status.Print('\nTo view your application in the web browser run:\n'
                   '  $ gcloud app browse' + service_hint + project_hint)


def _PossiblyCreateApp(api_client, project):
  """Returns an app resource, and creates it if the stars are aligned.

  App creation happens only if the current project is app-less, we are running
  in interactive mode and the user explicitly wants to.

  Args:
    api_client: Admin API client.
    project: The GCP project/app id.

  Returns:
    An app object (never returns None).

  Raises:
    MissingApplicationError: If an app does not exist and cannot be created.
  """
  try:
    return api_client.GetApplication()
  except apitools_exceptions.HttpNotFoundError:
    # Invariant: GCP Project does exist but (singleton) GAE app is not yet
    # created.
    #
    # Check for interactive mode, since this action is irreversible and somewhat
    # surprising. CreateAppInteractively will provide a cancel option for
    # interactive users, and MissingApplicationException includes instructions
    # for non-interactive users to fix this.
    log.debug('No app found:', exc_info=True)
    if console_io.CanPrompt():

      # Equivalent to running `gcloud app create`
      create_util.CreateAppInteractively(api_client, project)
      # App resource must be fetched again
      return api_client.GetApplication()
    raise exceptions.MissingApplicationError(project)
  except apitools_exceptions.HttpForbiddenError:
    active_account = properties.VALUES.core.account.Get()
    # pylint: disable=protected-access
    raise core_api_exceptions.HttpException(
        ('Permissions error fetching application [{}]. Please '
         'make sure that you have permission to view applications on the '
         'project and that {} has the App Engine Deployer '
         '(roles/appengine.deployer) role.'.format(api_client._FormatApp(),
                                                   active_account)))


def _PossiblyRepairApp(api_client, app):
  """Repairs the app if necessary and returns a healthy app object.

  An app is considered unhealthy if the codeBucket field is missing.
  This may include more conditions in the future.

  Args:
    api_client: Admin API client.
    app: App object (with potentially missing resources).

  Returns:
    An app object (either the same or a new one), which contains the right
    resources, including code bucket.
  """
  if not app.codeBucket:
    message = 'Initializing App Engine resources'
    api_client.RepairApplication(progress_message=message)
    app = api_client.GetApplication()
  return app


def _RaiseIfStopped(api_client, app):
  """Checks if app is disabled and raises error if so.

  Deploying to a disabled app is not allowed.

  Args:
    api_client: Admin API client.
    app: App object (including status).

  Raises:
    StoppedApplicationError: if the app is currently disabled.
  """
  if api_client.IsStopped(app):
    raise StoppedApplicationError(app)


def _CheckIfConfigsContainDispatch(configs):
  """Checks if list of configs contains dispatch config.

  Args:
    configs: list of configs

  Returns:
    bool, indicating if configs contain dispatch config.
  """
  for config in configs:
    if config.name == 'dispatch':
      return True

  return False


def GetRuntimeBuilderStrategy(release_track):
  """Gets the appropriate strategy to use for runtime builders.

  Depends on the release track (beta or GA; alpha is not supported) and whether
  the hidden `app/use_runtime_builders` configuration property is set (in which
  case it overrides).

  Args:
    release_track: the base.ReleaseTrack that determines the default strategy.

  Returns:
    The RuntimeBuilderStrategy to use.

  Raises:
    ValueError: if the release track is not supported (and there is no property
      override set).
  """
  # Use Get(), not GetBool, since GetBool() doesn't differentiate between "None"
  # and "False"
  if properties.VALUES.app.use_runtime_builders.Get() is not None:
    if properties.VALUES.app.use_runtime_builders.GetBool():
      return runtime_builders.RuntimeBuilderStrategy.ALWAYS
    else:
      return runtime_builders.RuntimeBuilderStrategy.NEVER

  if release_track is base.ReleaseTrack.GA:
    return runtime_builders.RuntimeBuilderStrategy.ALLOWLIST_GA
  elif release_track is base.ReleaseTrack.BETA:
    return runtime_builders.RuntimeBuilderStrategy.ALLOWLIST_BETA
  else:
    raise ValueError('Unrecognized release track [{}]'.format(release_track))


def _AppYamlInSourceFiles(source_files, app_yaml_path):
  if not source_files:
    return False

  # TODO(b/171495697) until the bug is fixed, the app yaml has to be located in
  #  the root of the app code, hence we're searching only the filename
  app_yaml_filename = os.path.basename(app_yaml_path)
  return any([f == app_yaml_filename for f in source_files])
