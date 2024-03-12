# -*- coding: utf-8 -*- #
# Copyright 2013 Google LLC. All Rights Reserved.
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

"""Utility methods used by the deploy command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import json
import os
import re

from apitools.base.py import exceptions as apitools_exceptions
from gae_ext_runtime import ext_runtime

from googlecloudsdk.api_lib.app import appengine_api_client
from googlecloudsdk.api_lib.app import build as app_build
from googlecloudsdk.api_lib.app import cloud_build
from googlecloudsdk.api_lib.app import docker_image
from googlecloudsdk.api_lib.app import metric_names
from googlecloudsdk.api_lib.app import runtime_builders
from googlecloudsdk.api_lib.app import util
from googlecloudsdk.api_lib.app import yaml_parsing
from googlecloudsdk.api_lib.app.images import config
from googlecloudsdk.api_lib.app.runtimes import fingerprinter
from googlecloudsdk.api_lib.cloudbuild import build as cloudbuild_build
from googlecloudsdk.api_lib.services import enable_api
from googlecloudsdk.api_lib.services import exceptions as s_exceptions
from googlecloudsdk.api_lib.storage import storage_util
from googlecloudsdk.api_lib.util import exceptions as api_lib_exceptions
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core import metrics
from googlecloudsdk.core import properties
from googlecloudsdk.core.console import progress_tracker
from googlecloudsdk.core.credentials import creds
from googlecloudsdk.core.credentials import store as c_store
from googlecloudsdk.core.util import files
from googlecloudsdk.core.util import platforms
from googlecloudsdk.third_party.appengine.api import appinfo
from googlecloudsdk.third_party.appengine.tools import context_util
import six
from six.moves import filter  # pylint: disable=redefined-builtin
from six.moves import zip  # pylint: disable=redefined-builtin

DEFAULT_SERVICE = 'default'
ALT_SEPARATOR = '-dot-'
MAX_DNS_LABEL_LENGTH = 63  # http://tools.ietf.org/html/rfc2181#section-11

# https://msdn.microsoft.com/en-us/library/windows/desktop/aa365247(v=vs.85).aspx
# Technically, this should be 260 because of the drive, ':\', and a null
# terminator, but any time we're getting close we're in dangerous territory.
_WINDOWS_MAX_PATH = 256

# The admin API has a timeout for individual tasks; if the build is greater
# than 10 minutes, it might trigger that timeout, so it's not a candidate for
# parallelized builds.
MAX_PARALLEL_BUILD_TIME = 600

FLEXIBLE_SERVICE_VERIFY_WARNING = (
    'Unable to verify that the Appengine Flexible API is enabled for project '
    '[{}]. You may not have permission to list enabled services on this '
    'project. If it is not enabled, this may cause problems in running your '
    'deployment. Please ask the project owner to ensure that the Appengine '
    'Flexible API has been enabled and that this account has permission to '
    'list enabled APIs.')


FLEXIBLE_SERVICE_VERIFY_WITH_SERVICE_ACCOUNT = (
    'Note: When deploying with a service account, the Service Management API '
    'needs to be enabled in order to verify that the Appengine Flexible API '
    'is enabled. Please ensure the Service Management API has been enabled '
    'on this project by the project owner.')


PREPARE_FAILURE_MSG = (
    'Enabling the Appengine Flexible API failed on project [{}]. You '
    'may not have permission to enable APIs on this project. Please ask '
    'the project owner to enable the Appengine Flexible API on this project.')


class Error(exceptions.Error):
  """Base error for this module."""


class PrepareFailureError(Error):
  pass


class WindowMaxPathError(Error):
  """Raised if a file cannot be read because of the MAX_PATH limitation."""

  _WINDOWS_MAX_PATH_ERROR_TEMPLATE = """\
The following file couldn't be read because its path is too long:

  [{0}]

For more information on this issue and possible workarounds, please read the
following (links are specific to Node.js, but the information is generally
applicable):

* https://github.com/Microsoft/nodejstools/issues/69
* https://github.com/Microsoft/nodejs-guidelines/blob/master/windows-environment.md#max_path-explanation-and-workarounds\
"""

  def __init__(self, filename):
    super(WindowMaxPathError, self).__init__(
        self._WINDOWS_MAX_PATH_ERROR_TEMPLATE.format(filename))


class DockerfileError(exceptions.Error):
  """Raised if a Dockerfile was found along with a non-custom runtime."""


class CloudbuildYamlError(exceptions.Error):
  """Raised if a cloudbuild.yaml was found along with a non-custom runtime."""


class CustomRuntimeFilesError(exceptions.Error):
  """Raised if a custom runtime has both a Dockerfile and a cloudbuild.yaml."""


class NoDockerfileError(exceptions.Error):
  """No Dockerfile found."""


class UnsatisfiedRequirementsError(exceptions.Error):
  """Raised if we are unable to detect the runtime."""


def _NeedsDockerfile(info, source_dir):
  """Returns True if the given directory needs a Dockerfile for this app.

  A Dockerfile is necessary when there is no Dockerfile in source_dir,
  regardless of whether we generate it here on the client-side, or in Cloud
  Container Builder server-side.

  The reason this function is more complicated than that is that it additionally
  verifies the sanity of the provided configuration by raising an exception if:

  - The runtime is "custom", but no Dockerfile is present
  - The runtime is not "custom", and a Dockerfile or cloudbuild.yaml is present
  - The runtime is "custom", and has both a cloudbuild.yaml and a Dockerfile.

  (The reason cloudbuild.yaml is tied into this method is that its use should be
  mutually exclusive with the Dockerfile.)

  Args:
    info: (googlecloudsdk.api_lib.app.yaml_parsing.ServiceYamlInfo). The
      configuration for the service.
    source_dir: str, the path to the service's source directory

  Raises:
    CloudbuildYamlError: if a cloudbuild.yaml is present, but the runtime is not
      "custom".
    DockerfileError: if a Dockerfile is present, but the runtime is not
      "custom".
    NoDockerfileError: Raised if a user didn't supply a Dockerfile and chose a
      custom runtime.
    CustomRuntimeFilesError: if a custom runtime had both a Dockerfile and a
      cloudbuild.yaml file.

  Returns:
    bool, whether Dockerfile generation is necessary.
  """
  has_dockerfile = os.path.exists(
      os.path.join(source_dir, config.DOCKERFILE))
  has_cloudbuild = os.path.exists(
      os.path.join(source_dir, runtime_builders.Resolver.CLOUDBUILD_FILE))
  if info.runtime == 'custom':
    if has_dockerfile and has_cloudbuild:
      raise CustomRuntimeFilesError(
          ('A custom runtime must have exactly one of [{}] and [{}] in the '
           'source directory; [{}] contains both').format(
               config.DOCKERFILE, runtime_builders.Resolver.CLOUDBUILD_FILE,
               source_dir))
    elif has_dockerfile:
      log.info('Using %s found in %s', config.DOCKERFILE, source_dir)
      return False
    elif has_cloudbuild:
      log.info('Not using %s because cloudbuild.yaml was found instead.',
               config.DOCKERFILE)
      return True
    else:
      raise NoDockerfileError(
          'You must provide your own Dockerfile when using a custom runtime. '
          'Otherwise provide a "runtime" field with one of the supported '
          'runtimes.')
  else:
    if has_dockerfile:
      raise DockerfileError(
          'There is a Dockerfile in the current directory, and the runtime '
          'field in {0} is currently set to [runtime: {1}]. To use your '
          'Dockerfile to build a custom runtime, set the runtime field to '
          '[runtime: custom]. To continue using the [{1}] runtime, please '
          'remove the Dockerfile from this directory.'.format(info.file,
                                                              info.runtime))
    elif has_cloudbuild:
      raise CloudbuildYamlError(
          'There is a cloudbuild.yaml in the current directory, and the '
          'runtime field in {0} is currently set to [runtime: {1}]. To use '
          'your cloudbuild.yaml to build a custom runtime, set the runtime '
          'field to [runtime: custom]. To continue using the [{1}] runtime, '
          'please remove the cloudbuild.yaml from this directory.'.format(
              info.file, info.runtime))
    log.info('Need Dockerfile to be generated for runtime %s', info.runtime)
    return True


def ShouldUseRuntimeBuilders(service, strategy, needs_dockerfile):
  """Returns whether we whould use runtime builders for this application build.

  If there is no image that needs to be built (service.RequiresImage() ==
  False), runtime builders are irrelevant, so they do not need to be built.

  If there is an image that needs to be built, whether to use runtime builders
  is determined by the RuntimeBuilderStrategy, based on the service runtime and
  whether the service being deployed has a Dockerfile already made, or whether
  it needs one built.

  Args:
    service: ServiceYamlInfo, The parsed service config.
    strategy: runtime_builders.RuntimeBuilderStrategy, the strategy for
      determining whether a runtime should use runtime builders.
    needs_dockerfile: bool, whether the Dockerfile in the source directory is
      absent.

  Returns:
    bool, whether to use the runtime builders.

  Raises:
    ValueError: if an unrecognized runtime_builder_strategy is given
  """
  return (service.RequiresImage() and
          strategy.ShouldUseRuntimeBuilders(service.runtime, needs_dockerfile))


def _GetDockerfiles(info, dockerfile_dir):
  """Returns map of in-memory Docker-related files to be packaged.

  Returns the files in-memory, so that we don't have to drop them on disk;
  instead, we include them in the archive sent to App Engine directly.

  Args:
    info: (googlecloudsdk.api_lib.app.yaml_parsing.ServiceYamlInfo)
      The service config.
    dockerfile_dir: str, path to the directory to fingerprint and generate
      Dockerfiles for.

  Raises:
    UnsatisfiedRequirementsError: Raised if the code in the directory doesn't
      satisfy the requirements of the specified runtime type.

  Returns:
    A dictionary of filename relative to the archive root (str) to file contents
    (str).
  """
  params = ext_runtime.Params(appinfo=info.parsed, deploy=True)
  configurator = fingerprinter.IdentifyDirectory(dockerfile_dir, params)
  if configurator:
    dockerfiles = configurator.GenerateConfigData()
    return {d.filename: d.contents for d in dockerfiles}
  else:
    raise UnsatisfiedRequirementsError(
        'Your application does not satisfy all of the requirements for a '
        'runtime of type [{0}].  Please correct the errors and try '
        'again.'.format(info.runtime))


def _GetSourceContextsForUpload(source_dir):
  """Gets source context file information.

  Args:
    source_dir: str, path to the service's source directory
  Returns:
    A dict of filename to (str) source context file contents.
  """
  source_contexts = {}
  # Error message in case of failure.
  m = ('Could not generate [{name}]: {error}\n'
       'Stackdriver Debugger may not be configured or enabled on this '
       'application. See https://cloud.google.com/debugger/ for more '
       'information.')
  try:
    contexts = context_util.CalculateExtendedSourceContexts(source_dir)
  except context_util.GenerateSourceContextError as e:
    log.info(m.format(name=context_util.CONTEXT_FILENAME, error=e))
    return source_contexts

  try:
    context = context_util.BestSourceContext(contexts)
    source_contexts[context_util.CONTEXT_FILENAME] = six.text_type(
        json.dumps(context))
  except KeyError as e:
    log.info(m.format(name=context_util.CONTEXT_FILENAME, error=e))
  return source_contexts


def _GetDomainAndDisplayId(project_id):
  """Returns tuple (displayed app id, domain)."""
  l = project_id.split(':')
  if len(l) == 1:
    return l[0], None
  return l[1], l[0]


def _GetImageName(project, service, version, gcr_domain):
  """Returns image tag according to App Engine convention."""
  display, domain = _GetDomainAndDisplayId(project)
  return (config.DOCKER_IMAGE_NAME_DOMAIN_FORMAT if domain
          else config.DOCKER_IMAGE_NAME_FORMAT).format(
              gcr_domain=gcr_domain,
              display=display,
              domain=domain,
              service=service,
              version=version)


def _GetYamlPath(source_dir, service_path, skip_files, gen_files):
  """Returns the yaml path, optionally updating gen_files.

  Args:
    source_dir: str, the absolute path to the root of the application directory.
    service_path: str, the absolute path to the service YAML file
    skip_files: appengine.api.Validation._RegexStr, the validated regex object
      from the service info file.
    gen_files: dict, the dict of files to generate. May be updated if a file
      needs to be generated.

  Returns:
    str, the relative path to the service YAML file that should be used for
      build.
  """
  if files.IsDirAncestorOf(source_dir, service_path):
    rel_path = os.path.relpath(service_path, start=source_dir)
    if not util.ShouldSkip(skip_files, rel_path):
      return rel_path
  yaml_contents = files.ReadFileContents(service_path)
  # Use a checksum to ensure file uniqueness, not for security reasons.
  checksum = files.Checksum().AddContents(yaml_contents.encode()).HexDigest()
  generated_path = '_app_{}.yaml'.format(checksum)
  gen_files[generated_path] = yaml_contents
  return generated_path


def BuildAndPushDockerImage(
    project,
    service,
    upload_dir,
    source_files,
    version_id,
    code_bucket_ref,
    gcr_domain,
    runtime_builder_strategy=runtime_builders.RuntimeBuilderStrategy.NEVER,
    parallel_build=False,
    use_flex_with_buildpacks=False):
  """Builds and pushes a set of docker images.

  Args:
    project: str, The project being deployed to.
    service: ServiceYamlInfo, The parsed service config.
    upload_dir: str, path to the service's upload directory
    source_files: [str], relative paths to upload.
    version_id: The version id to deploy these services under.
    code_bucket_ref: The reference to the GCS bucket where the source will be
      uploaded.
    gcr_domain: str, Cloud Registry domain, determines the physical location
      of the image. E.g. `us.gcr.io`.
    runtime_builder_strategy: runtime_builders.RuntimeBuilderStrategy, whether
      to use the new CloudBuild-based runtime builders (alternative is old
      externalized runtimes).
    parallel_build: bool, if True, enable parallel build and deploy.
    use_flex_with_buildpacks: bool, if true, use the build-image and
      run-image built through buildpacks.

  Returns:
    BuildArtifact, Representing the pushed container image or in-progress build.

  Raises:
    DockerfileError: if a Dockerfile is present, but the runtime is not
      "custom".
    NoDockerfileError: Raised if a user didn't supply a Dockerfile and chose a
      custom runtime.
    UnsatisfiedRequirementsError: Raised if the code in the directory doesn't
      satisfy the requirements of the specified runtime type.
    ValueError: if an unrecognized runtime_builder_strategy is given
  """
  needs_dockerfile = _NeedsDockerfile(service, upload_dir)
  use_runtime_builders = ShouldUseRuntimeBuilders(service,
                                                  runtime_builder_strategy,
                                                  needs_dockerfile)

  # Nothing to do if this is not an image-based deployment.
  if not service.RequiresImage():
    return None
  log.status.Print(
      'Building and pushing image for service [{service}]'
      .format(service=service.module))

  gen_files = dict(_GetSourceContextsForUpload(upload_dir))
  if needs_dockerfile and not use_runtime_builders:
    # The runtime builders will generate a Dockerfile in the Cloud, so we only
    # need to do this if use_runtime_builders is True
    gen_files.update(_GetDockerfiles(service, upload_dir))

  image = docker_image.Image(
      dockerfile_dir=upload_dir,
      repo=_GetImageName(project, service.module, version_id, gcr_domain),
      nocache=False,
      tag=config.DOCKER_IMAGE_TAG)

  metrics.CustomTimedEvent(metric_names.CLOUDBUILD_UPLOAD_START)
  object_ref = storage_util.ObjectReference.FromBucketRef(
      code_bucket_ref, image.tagged_repo)
  relative_yaml_path = _GetYamlPath(upload_dir, service.file,
                                    service.parsed.skip_files, gen_files)

  try:
    cloud_build.UploadSource(upload_dir, source_files, object_ref,
                             gen_files=gen_files)
  except (OSError, IOError) as err:
    if platforms.OperatingSystem.IsWindows():
      if err.filename and len(err.filename) > _WINDOWS_MAX_PATH:
        raise WindowMaxPathError(err.filename)
    raise
  metrics.CustomTimedEvent(metric_names.CLOUDBUILD_UPLOAD)

  if use_runtime_builders:
    builder_reference = runtime_builders.FromServiceInfo(
        service, upload_dir, use_flex_with_buildpacks)
    log.info('Using runtime builder [%s]', builder_reference.build_file_uri)
    builder_reference.WarnIfDeprecated()
    yaml_path = util.ConvertToPosixPath(relative_yaml_path)
    substitute = {
        '_OUTPUT_IMAGE': image.tagged_repo,
        '_GAE_APPLICATION_YAML_PATH': yaml_path,
    }
    if use_flex_with_buildpacks:
      python_version = yaml_parsing.GetRuntimeConfigAttr(
          service.parsed, 'python_version')
      if yaml_parsing.GetRuntimeConfigAttr(service.parsed, 'python_version'):
        substitute['_GOOGLE_RUNTIME_VERSION'] = python_version

    build = builder_reference.LoadCloudBuild(substitute)

  else:
    build = cloud_build.GetDefaultBuild(image.tagged_repo)

  build = cloud_build.FixUpBuild(build, object_ref)
  return _SubmitBuild(build, image, project, parallel_build)


def _SubmitBuild(build, image, project, parallel_build):
  """Builds and pushes a set of docker images.

  Args:
    build: A fixed up Build object.
    image: docker_image.Image, A docker image.
    project: str, The project being deployed to.
    parallel_build: bool, if True, enable parallel build and deploy.

  Returns:
    BuildArtifact, Representing the pushed container image or in-progress build.
  """
  build_timeout = cloud_build.GetServiceTimeoutSeconds(
      properties.VALUES.app.cloud_build_timeout.Get())
  if build_timeout and build_timeout > MAX_PARALLEL_BUILD_TIME:
    parallel_build = False
    log.info(
        'Property cloud_build_timeout configured to [{0}], which exceeds '
        'the maximum build time for parallelized beta deployments of [{1}] '
        'seconds. Performing serial deployment.'.format(
            build_timeout, MAX_PARALLEL_BUILD_TIME))

  if parallel_build:
    metrics.CustomTimedEvent(metric_names.CLOUDBUILD_EXECUTE_ASYNC_START)
    build_op = cloudbuild_build.CloudBuildClient().ExecuteCloudBuildAsync(
        build, project=project)
    return app_build.BuildArtifact.MakeBuildIdArtifactFromOp(build_op)
  else:
    metrics.CustomTimedEvent(metric_names.CLOUDBUILD_EXECUTE_START)
    cloudbuild_build.CloudBuildClient().ExecuteCloudBuild(
        build, project=project)
    metrics.CustomTimedEvent(metric_names.CLOUDBUILD_EXECUTE)
    return app_build.BuildArtifact.MakeImageArtifact(image.tagged_repo)


def DoPrepareManagedVms(gae_client):
  """Call an API to prepare the for App Engine Flexible."""
  metrics.CustomTimedEvent(metric_names.PREPARE_ENV_START)
  try:
    message = 'If this is your first deployment, this may take a while'
    with progress_tracker.ProgressTracker(message):
      # Note: this doesn't actually boot the VM, it just prepares some stuff
      # for the project via an undocumented Admin API.
      gae_client.PrepareVmRuntime()
    log.status.Print()
  except util.RPCError as err:
    # Any failures later due to an unprepared project will be noisy, so it's
    # okay not to fail here.
    log.warning(
        ("We couldn't validate that your project is ready to deploy to App "
         'Engine Flexible Environment. If deployment fails, please check the '
         'following message and try again:\n') + six.text_type(err))
  metrics.CustomTimedEvent(metric_names.PREPARE_ENV)


def PossiblyEnableFlex(project):
  """Attempts to enable the Flexible Environment API on the project.

  Possible scenarios:
  -If Flexible Environment is already enabled, success.
  -If Flexible Environment API is not yet enabled, attempts to enable it. If
   that succeeds, success.
  -If the account doesn't have permissions to confirm that the Flexible
   Environment API is or isn't enabled on this project, succeeds with a warning.
     -If the account is a service account, adds an additional warning that
      the Service Management API may need to be enabled.
  -If the Flexible Environment API is not enabled on the project and the attempt
   to enable it fails, raises PrepareFailureError.

  Args:
    project: str, the project ID.

  Raises:
    PrepareFailureError: if enabling the API fails with a 403 or 404 error code.
    googlecloudsdk.api_lib.util.exceptions.HttpException: miscellaneous errors
        returned by server.
  """
  try:
    enable_api.EnableServiceIfDisabled(project,
                                       'appengineflex.googleapis.com')
  except s_exceptions.GetServicePermissionDeniedException:
    # If we can't find out whether the Flexible API is enabled, proceed with
    # a warning.
    warning = FLEXIBLE_SERVICE_VERIFY_WARNING.format(project)
    # If user is using a service account, add more info about what might
    # have gone wrong.
    credential = c_store.LoadIfEnabled(use_google_auth=True)
    if credential and creds.IsServiceAccountCredentials(credential):
      warning += '\n\n{}'.format(FLEXIBLE_SERVICE_VERIFY_WITH_SERVICE_ACCOUNT)
    log.warning(warning)
  except s_exceptions.EnableServicePermissionDeniedException:
    # If enabling the Flexible API fails due to a permissions error, the
    # deployment fails.
    raise PrepareFailureError(PREPARE_FAILURE_MSG.format(project))
  except apitools_exceptions.HttpError as err:
    # The deployment should also fail if there are unforeseen errors in
    # enabling the Flexible API. If so, display detailed information.
    raise api_lib_exceptions.HttpException(
        err, error_format=('Error [{status_code}] {status_message}'
                           '{error.details?'
                           '\nDetailed error information:\n{?}}'))


def UseSsl(service_info):
  """Returns whether the root URL for an application is served over HTTPS.

  More specifically, returns the 'secure' setting of the handler that will serve
  the application. This can be 'always', 'optional', or 'never', depending on
  when the URL is served over HTTPS.

  Will miss a small number of cases, but HTTP is always okay (an HTTP URL to an
  HTTPS-only service will result in a redirect).

  Args:
    service_info: ServiceYamlInfo, the service configuration.

  Returns:
    str, the 'secure' setting of the handler for the root URL.
  """
  if service_info.is_ti_runtime and not service_info.parsed.handlers:
    return appinfo.SECURE_HTTP_OR_HTTPS
  for handler in service_info.parsed.handlers:
    try:
      if re.match(handler.url + '$', '/'):
        return handler.secure
    except re.error:
      # AppEngine uses POSIX Extended regular expressions, which are not 100%
      # compatible with Python's re module.
      pass
  return appinfo.SECURE_HTTP


def GetAppHostname(app=None, app_id=None, service=None, version=None,
                   use_ssl=appinfo.SECURE_HTTP, deploy=True):
  """Returns the hostname of the given version of the deployed app.

  Args:
    app: Application resource. One of {app, app_id} must be given.
    app_id: str, project ID. One of {app, app_id} must be given. If both are
      provided, the hostname from app is preferred.
    service: str, the (optional) service being deployed
    version: str, the deployed version ID (omit to get the default version URL).
    use_ssl: bool, whether to construct an HTTPS URL.
    deploy: bool, if this is called during a deployment.

  Returns:
    str. Constructed URL.

  Raises:
    TypeError: if neither an app nor an app_id is provided
  """
  if not app and not app_id:
    raise TypeError('Must provide an application resource or application ID.')
  version = version or ''
  service_name = service or ''
  if service == DEFAULT_SERVICE:
    service_name = ''

  if not app:
    api_client = appengine_api_client.AppengineApiClient.GetApiClient()
    app = api_client.GetApplication()
  if app:
    app_id, domain = app.defaultHostname.split('.', 1)

  # Normally, AppEngine URLs are of the form
  # 'http[s]://version.service.app.appspot.com'. However, the SSL certificate
  # for appspot.com is not valid for subdomains of subdomains of appspot.com
  # (e.g. 'https://app.appspot.com/' is okay; 'https://service.app.appspot.com/'
  # is not). To deal with this, AppEngine recognizes URLs like
  # 'http[s]://version-dot-service-dot-app.appspot.com/'.
  #
  # This works well as long as the domain name part constructed in this fashion
  # is less than 63 characters long, as per the DNS spec. If the domain name
  # part is longer than that, we are forced to use the URL with an invalid
  # certificate.
  #
  # We've tried to do the best possible thing in every case here.
  subdomain_parts = list(filter(bool, [version, service_name, app_id]))
  scheme = 'http'
  if use_ssl == appinfo.SECURE_HTTP:
    subdomain = '.'.join(subdomain_parts)
    scheme = 'http'
  else:
    subdomain = ALT_SEPARATOR.join(subdomain_parts)
    if len(subdomain) <= MAX_DNS_LABEL_LENGTH:
      scheme = 'https'
    else:
      if deploy:
        format_parts = ['$VERSION_ID', '$SERVICE_ID', '$APP_ID']
        subdomain_format = ALT_SEPARATOR.join(
            [j for (i, j) in zip([version, service_name, app_id], format_parts)
             if i])
        msg = ('This deployment will result in an invalid SSL certificate for '
               'service [{0}]. The total length of your subdomain in the '
               'format {1} should not exceed {2} characters. Please verify '
               'that the certificate corresponds to the parent domain of your '
               'application when you connect.').format(service,
                                                       subdomain_format,
                                                       MAX_DNS_LABEL_LENGTH)
        log.warning(msg)
      subdomain = '.'.join(subdomain_parts)
      if use_ssl == appinfo.SECURE_HTTP_OR_HTTPS:
        scheme = 'http'
      elif use_ssl == appinfo.SECURE_HTTPS:
        if not deploy:
          msg = ('Most browsers will reject the SSL certificate for '
                 'service [{0}].').format(service)
          log.warning(msg)
        scheme = 'https'

  return '{0}://{1}.{2}'.format(scheme, subdomain, domain)


DEFAULT_DEPLOYABLE = 'app.yaml'
