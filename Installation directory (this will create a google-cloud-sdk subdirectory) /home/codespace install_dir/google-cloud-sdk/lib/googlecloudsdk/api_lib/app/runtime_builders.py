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
r"""Library code to support App Engine Flex runtime builders.

The App Engine Flex platform runs a user's application that has been packaged
into a docker image. At the lowest level, the user provides us with a source
directory complete with Dockerfile, which we build into an image and deploy.
To make development easier, Google provides blessed language runtimes that the
user can extend in their Dockerfile to get a working base image for their
application. To further make development easier, we do not require users to
author their own Dockerfiles for "canonical" applications for each of the
Silver Languages.

In order for this to be possible, preprocessing must be done prior to the
Docker build to inspect the user's source code and automatically generate a
Dockerfile.

Flex runtime builders are a per-runtime pipeline that covers the full journey
from source directory to docker image. They are stored as templated .yaml files
representing CloudBuild Build messages. These .yaml files contain a series of
CloudBuild build steps. Additionally, the runtime root stores a `runtimes.yaml`
file which contains a list of runtime names and mappings to the corresponding
builder yaml files.

Such a builder will look something like this (note that <angle_brackets> denote
values to be filled in by the builder author, and $DOLLAR_SIGNS denote a
literal part of the template to be substituted at runtime):

    steps:
    - name: 'gcr.io/google_appengine/python-builder:<version>'
      env: ['GAE_APPLICATION_YAML_PATH=${_GAE_APPLICATION_YAML_PATH}']
    - name: 'gcr.io/cloud-builders/docker:<docker_image_version>'
      args: ['build', '-t', '$_OUTPUT_IMAGE', '.']
    images: ['$_OUTPUT_IMAGE']

To test this out in the context of a real deployment, do something like the
following (ls/grep steps just for illustrating where files are):

    $ ls /tmp/runtime-root
    runtimes.yaml python-v1.yaml
    $ cat /tmp/runtime-root/runtimes.yaml
    schema_version: 1
    runtimes:
      python:
        target:
          file: python-v1.yaml
    $ gcloud config set app/use_runtime_builders true
    $ gcloud config set app/runtime_builders_root file:///tmp/runtime-root
    $ cd $MY_APP_DIR
    $ grep 'runtime' app.yaml
    runtime: python
    $ grep 'env' app.yaml
    env: flex
    $ gcloud beta app deploy

A (possibly) easier way of achieving the same thing if you don't have a
runtime_builders_root set up for development yet:

   $ cd $MY_APP_DIR
   $ export _OUTPUT_IMAGE=gcr.io/$PROJECT/appengine/placeholder
   $ gcloud container builds submit \
       --config=<(envsubst < /path/to/cloudbuild.yaml) .
   $ gcloud app deploy --image-url=$_OUTPUT_IMAGE

Or (even easier) use a 'custom' runtime:

    $ cd $MY_APP_DIR
    $ ls
    cloudbuild.yaml app.yaml
    $ rm -f Dockerfile
    $ grep 'runtime' app.yaml
    runtime: custom
    $ gcloud beta app deploy
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import contextlib
import enum
import os
import re
from googlecloudsdk.api_lib.cloudbuild import cloudbuild_util
from googlecloudsdk.api_lib.cloudbuild import config as cloudbuild_config
from googlecloudsdk.api_lib.storage import storage_api
from googlecloudsdk.api_lib.storage import storage_util
from googlecloudsdk.calliope import exceptions as calliope_exceptions
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core import yaml
import six
import six.moves.urllib.error
import six.moves.urllib.parse
import six.moves.urllib.request


# "test-{ga,beta}" runtimes are canaries for unit testing
_ALLOWLISTED_RUNTIMES_GA = frozenset(
    {'aspnetcore', 'php', 'nodejs', 'ruby', 'java',
     re.compile(r'(python|python-.+)$'),
     re.compile(r'(go|go1\..+)$'),
     re.compile('^gs://'),
     'test-ga', re.compile('test-re-[ab]')})
_ALLOWLISTED_RUNTIMES_BETA = frozenset(
    _ALLOWLISTED_RUNTIMES_GA |
    {'test-beta'})


class FileReadError(exceptions.Error):
  """Error indicating a file read operation failed."""


class ManifestError(exceptions.Error):
  """Error indicating a problem parsing or using the manifest."""


class ExperimentsError(exceptions.Error):
  """Error indicating a problem parsing or using the experiment config."""


class CloudBuildLoadError(exceptions.Error):
  """Error indicating an issue loading the runtime Cloud Build specification."""


class CloudBuildFileNotFound(CloudBuildLoadError):
  """Error indicating a missing Cloud Build file."""


class InvalidRuntimeBuilderURI(CloudBuildLoadError):
  """Error indicating that the runtime builder URI format wasn't recognized."""

  def __init__(self, uri):
    super(InvalidRuntimeBuilderURI, self).__init__(
        '[{}] is not a valid runtime builder URI. '
        'Please set the app/runtime_builders_root property to a URI with '
        'either the Google Cloud Storage (`gs://`) or local file (`file://`) '
        'protocol.'.format(uri))


class BuilderResolveError(exceptions.Error):
  """Error indicating that a build file could not be resolved."""


class RuntimeBuilderStrategy(enum.Enum):
  """Enum indicating when to use runtime builders."""
  NEVER = 1
  ALLOWLIST_BETA = 2  # That is, turned on for an allowed set of runtimes
  ALLOWLIST_GA = 3  # That is, turned on for an allowed set of runtimes
  ALWAYS = 4

  def _GetAllowlist(self):
    """Return the allowlist of runtimes for this strategy.

    The allowlist is kept as a constant within this module.

    Returns:
      list of str, the names of runtimes that are allowed for this strategy.

    Raises:
      ValueError: if this strategy is not allowlist-based.
    """
    if self is self.ALLOWLIST_GA:
      return _ALLOWLISTED_RUNTIMES_GA
    elif self is self.ALLOWLIST_BETA:
      return _ALLOWLISTED_RUNTIMES_BETA
    raise ValueError(
        'RuntimeBuilderStrategy {} is not an allowed strategy.'.format(self))

  def _IsAllowed(self, runtime):
    for allowlisted_runtime in self._GetAllowlist():
      try:
        if allowlisted_runtime.match(runtime):
          return True
      except AttributeError:
        if runtime == allowlisted_runtime:
          return True
    return False

  def ShouldUseRuntimeBuilders(self, runtime, needs_dockerfile):
    """Returns True if runtime should use runtime builders under this strategy.

    For the most part, this is obvious: the ALWAYS strategy returns True, the
    ALLOWLIST_${TRACK} strategies return True if the given runtime is in the
    list of _ALLOWLISTED_RUNTIMES_${TRACK}, and the NEVER strategy returns
    False.

    However, in the case of 'custom' runtimes, things get tricky: if the
    strategy *is not* NEVER, we return True only if there is no `Dockerfile` in
    the current directory (this method assumes that there is *either* a
    `Dockerfile` or a `cloudbuild.yaml` file), since one needs to get generated
    by the Cloud Build.

    Args:
      runtime: str, the runtime being built.
      needs_dockerfile: bool, whether the Dockerfile in the source directory is
        absent.

    Returns:
      bool, whether to use the runtime builders.
    Raises:
      ValueError: if an unrecognized runtime_builder_strategy is given
    """
    # For these strategies, if a user provides a 'custom' runtime, we use
    # runtime builders unless there is a Dockerfile. For other strategies, we
    # never use runtime builders with 'custom'.
    if runtime == 'custom' and self in (self.ALWAYS,
                                        self.ALLOWLIST_BETA,
                                        self.ALLOWLIST_GA):
      return needs_dockerfile

    if self is self.ALWAYS:
      return True
    elif self is self.ALLOWLIST_BETA or self is self.ALLOWLIST_GA:
      return self._IsAllowed(runtime)
    elif self is self.NEVER:
      return False
    else:
      raise ValueError('Invalid runtime builder strategy [{}].'.format(self))


def _Join(*args):
  """Join parts of a gs:// Cloud Storage or local file:// path."""
  # URIs always uses '/' as separator, regardless of local platform.
  return '/'.join([arg.strip('/') for arg in args])


@contextlib.contextmanager
def _Read(uri):
  """Read a file/object (local file:// or gs:// Cloud Storage path).

  >>> with _Read('gs://builder/object.txt') as f:
  ...   assert f.read() == 'foo'
  >>> with _Read('file:///path/to/object.txt') as f:
  ...   assert f.read() == 'bar'

  Args:
    uri: str, the path to the file/object to read. Must begin with 'file://' or
      'gs://'

  Yields:
    a file-like context manager.

  Raises:
    FileReadError: If opening or reading the file failed.
    InvalidRuntimeBuilderPath: If the path is invalid (doesn't begin with an
        appropriate prefix).
  """
  try:
    if uri.startswith('file://'):
      with contextlib.closing(six.moves.urllib.request.urlopen(uri)) as req:
        yield req
    elif uri.startswith('gs://'):
      storage_client = storage_api.StorageClient()
      object_ = storage_util.ObjectReference.FromUrl(uri)
      with contextlib.closing(storage_client.ReadObject(object_)) as f:
        yield f
    else:
      raise InvalidRuntimeBuilderURI(uri)
  except (six.moves.urllib.error.HTTPError, six.moves.urllib.error.URLError,
          calliope_exceptions.BadFileException) as e:
    log.debug('', exc_info=True)
    raise FileReadError(six.text_type(e))


class BuilderReference(object):
  """A reference to a specific cloudbuild.yaml file to use."""

  def __init__(self, runtime, build_file_uri, deprecation_message=None):
    """Constructs a BuilderReference.

    Args:
      runtime: str, The runtime this builder corresponds to.
      build_file_uri: str, The full URI of the build configuration or None if
        this runtime existed but no longer can be built (deprecated).
      deprecation_message: str, A message to print when using this builder or
        None if not deprecated.
    """
    self.runtime = runtime
    self.build_file_uri = build_file_uri
    self.deprecation_message = deprecation_message

  def LoadCloudBuild(self, params):
    """Loads the Cloud Build configuration file for this builder reference.

    Args:
      params: dict, a dictionary of values to be substituted in to the
        Cloud Build configuration template corresponding to this runtime
        version.

    Returns:
      Build message, the parsed and parameterized Cloud Build configuration
        file.

    Raises:
      CloudBuildLoadError: If the Cloud Build configuration file is unknown.
      FileReadError: If reading the configuration file fails.
      InvalidRuntimeBuilderPath: If the path of the configuration file is
        invalid.
    """
    if not self.build_file_uri:
      raise CloudBuildLoadError(
          'There is no build file associated with runtime [{runtime}]'
          .format(runtime=self.runtime))
    messages = cloudbuild_util.GetMessagesModule()
    with _Read(self.build_file_uri) as data:
      build = cloudbuild_config.LoadCloudbuildConfigFromStream(
          data, messages=messages, params=params)
    if build.options is None:
      build.options = messages.BuildOptions()
    build.options.substitutionOption = (
        build.options.SubstitutionOptionValueValuesEnum.ALLOW_LOOSE)
    for step in build.steps:
      has_yaml_path = False
      has_runtime_version = False
      for env in step.env:
        parts = env.split('=')
        log.debug('Env var in build step: ' + str(parts))
        if 'GAE_APPLICATION_YAML_PATH' in parts:
          has_yaml_path = True
        if 'GOOGLE_RUNTIME_VERSION' in parts:
          has_runtime_version = True
      if not has_yaml_path:
        step.env.append(
            'GAE_APPLICATION_YAML_PATH=${_GAE_APPLICATION_YAML_PATH}')
      if not has_runtime_version and '_GOOGLE_RUNTIME_VERSION' in params:
        step.env.append('GOOGLE_RUNTIME_VERSION=${_GOOGLE_RUNTIME_VERSION}')
    return build

  def WarnIfDeprecated(self):
    """Warns that this runtime is deprecated (if it has been marked as such)."""
    if self.deprecation_message:
      log.warning(self.deprecation_message)

  def __eq__(self, other):
    return (self.runtime == other.runtime and
            self.build_file_uri == other.build_file_uri and
            self.deprecation_message == other.deprecation_message)

  def __ne__(self, other):
    return not self.__eq__(other)


class Manifest(object):
  """Loads and parses a runtimes.yaml manifest.

  To resolve a builder configuration file to use, a given runtime name is
  looked up in this manifest. For each runtime, it either points to a
  configuration file directly, or to another runtime. If it points to a runtime,
  resolution continues until a configuration file is reached.

  The following is the proto-ish spec for the yaml schema of the mainfest:

  # Used to determine if this client can parse this manifest. If the number is
  # less than or equal to the version this client knows about, it is compatible.
  int schema_version; # Required

  # The registry of all the runtimes that this manifest defines. The key of the
  # map is the runtime name that appears in app.yaml.
  <string, Runtime> runtimes {

    # Determines which builder this runtime points to.
    Target target {

      oneof {
        # A path relative to the manifest's location of the builder spec to use.
        string file;

        # Another runtime registered in this file that should be resolved and
        # used for this runtime.
        string runtime;
      }
    }

    # Specifies deprecation information about this runtime.
    Deprecation deprecation {

      # A message to be displayed to the user on use of this runtime.
      string message;
    }
  }
  """
  SCHEMA_VERSION = 1

  @classmethod
  def LoadFromURI(cls, uri):
    """Loads a manifest from a gs:// or file:// path.

    Args:
      uri: str, A gs:// or file:// URI

    Returns:
      Manifest, the loaded manifest.
    """
    log.debug('Loading runtimes manifest from [%s]', uri)
    with _Read(uri) as f:
      data = yaml.load(f, file_hint=uri)
    return cls(uri, data)

  def __init__(self, uri, data):
    """Use LoadFromFile, not this constructor directly."""
    self._uri = uri
    self._data = data
    required_version = self._data.get('schema_version', None)
    if required_version is None:
      raise ManifestError(
          'Unable to parse the runtimes manifest: [{}]'.format(uri))
    if required_version > Manifest.SCHEMA_VERSION:
      raise ManifestError(
          'Unable to parse the runtimes manifest. Your client supports schema '
          'version [{supported}] but requires [{required}]. Please update your '
          'SDK to a later version.'.format(supported=Manifest.SCHEMA_VERSION,
                                           required=required_version))

  def Runtimes(self):
    """Get all registered runtimes in the manifest.

    Returns:
      [str], The runtime names.
    """
    return list(self._data.get('runtimes', {}).keys())

  def GetBuilderReference(self, runtime):
    """Gets the associated reference for the given runtime.

    Args:
      runtime: str, The name of the runtime.

    Returns:
      BuilderReference, The reference pointed to by the manifest, or None if the
      runtime is not registered.

    Raises:
      ManifestError: if a problem occurred parsing the manifest.
    """
    runtimes = self._data.get('runtimes', {})
    current_runtime = runtime
    seen = {current_runtime}

    while True:
      runtime_def = runtimes.get(current_runtime, None)
      if not runtime_def:
        log.debug('Runtime [%s] not found in manifest [%s]',
                  current_runtime, self._uri)
        return None

      new_runtime = runtime_def.get('target', {}).get('runtime', None)
      if new_runtime:
        # Runtime is an alias for another runtime, resolve the alias.
        log.debug('Runtime [%s] is an alias for [%s]',
                  current_runtime, new_runtime)
        if new_runtime in seen:
          raise ManifestError(
              'A circular dependency was found while resolving the builder for '
              'runtime [{runtime}]'.format(runtime=runtime))
        seen.add(new_runtime)
        current_runtime = new_runtime
        continue

      deprecation_msg = runtime_def.get('deprecation', {}).get('message', None)
      build_file = runtime_def.get('target', {}).get('file', None)
      if build_file:
        # This points to a build configuration file, create the reference.
        full_build_uri = _Join(os.path.dirname(self._uri), build_file)
        log.debug('Resolved runtime [%s] as build configuration [%s]',
                  current_runtime, full_build_uri)
        return BuilderReference(
            current_runtime, full_build_uri, deprecation_msg)

      # There is no alias or build file. This means the runtime exists, but
      # cannot be used. There might still be a deprecation message we can show
      # to the user.
      log.debug('Resolved runtime [%s] has no build configuration',
                current_runtime)
      return BuilderReference(current_runtime, None, deprecation_msg)


class Experiments(object):
  """Runtime experiment configs as read from a gs:// or a file:// source.

  The experiment config file follows the following protoish schema:

  # Used to determine if this client can parse this manifest. If the number is
  # less than or equal to the version this client knows about, it is compatible.
  int schema_version; # Required

  # Map of experiments and their rollout percentage.
  # The key is the name of the experiment, the value is an integer between 0
  # and 100 representing the rollout percentage
  # In case no experiments are defined, an empty 'experiments:' section needs to
  # be present.
  <String, Number> experiments
  """
  SCHEMA_VERSION = 1
  CONFIG_FILE = 'experiments.yaml'
  TRIGGER_BUILD_SERVER_SIDE = 'trigger_build_server_side'

  @classmethod
  def LoadFromURI(cls, dir_uri):
    """Loads a runtime experiment config from a gs:// or file:// path.

    Args:
      dir_uri: str, A gs:// or file:// URI pointing to a folder that contains
        the file called Experiments.CONFIG_FILE

    Returns:
      Experiments, the loaded runtime experiments config.
    """
    uri = _Join(dir_uri, cls.CONFIG_FILE)
    log.debug('Loading runtimes experiment config from [%s]', uri)
    try:
      with _Read(uri) as f:
        data = yaml.load(f, file_hint=uri)
      return cls(uri, data)
    except FileReadError as e:
      raise ExperimentsError(
          'Unable to read the runtimes experiment config: [{}], error: {}'
          .format(uri, e))
    except yaml.YAMLParseError as e:
      raise ExperimentsError(
          'Unable to read the runtimes experiment config: [{}], error: {}'
          .format(uri, e))

  def __init__(self, uri, data):
    """Use LoadFromFile, not this constructor directly."""
    self._uri = uri
    self._data = data
    required_version = self._data.get('schema_version', None)
    if required_version is None:
      raise ExperimentsError(
          'Unable to parse the runtimes experiment config due to missing '
          'schema_version field: [{}]'.format(uri))
    if required_version > Experiments.SCHEMA_VERSION:
      raise ExperimentsError(
          'Unable to parse the runtimes experiments config. Your client '
          'supports schema version [{supported}] but requires [{required}]. '
          'Please update your SDK to a newer version.'.format(
              supported=Manifest.SCHEMA_VERSION, required=required_version))

  def Experiments(self):
    """Get all experiments and their rollout percentage.

    Returns:
      dict[str,int] Experiments and their rollout state.
    """
    return self._data.get('experiments')

  def GetExperimentPercentWithDefault(self, experiment, default=0):
    """Get the rollout percentage of an experiment or return 'default'.

    Args:
      experiment: the name of the experiment
      default: the value to return if the experiment was not found

    Returns:
      int the percent of the experiment
    """
    try:
      return self._data.get('experiments')[experiment]
    except KeyError:
      return default


class Resolver(object):
  """Resolves the location of a builder configuration for a runtime.

  There are several possible locations that builder configuration can be found
  for a given runtime, and they are checked in order. Check GetBuilderReference
  for the locations checked.
  """

  # The name of the manifest in the builders root that registers the runtimes.
  MANIFEST_NAME = 'runtimes.yaml'
  BUILDPACKS_MANIFEST_NAME = 'runtimes_buildpacks.yaml'
  # The name of the file in your local source for when you are using custom.
  CLOUDBUILD_FILE = 'cloudbuild.yaml'

  def __init__(self, runtime, source_dir, legacy_runtime_version,
               use_flex_with_buildpacks=False):
    """Instantiates a resolver.

    Args:
      runtime: str, The name of the runtime to be resolved.
      source_dir: str, The local path of the source code being deployed.
      legacy_runtime_version: str, The value from runtime_config.runtime_version
        in app.yaml. This is only used in legacy mode.
      use_flex_with_buildpacks: bool, if true, use the build-image and
      run-image built through buildpacks.

    Returns:
      Resolver, The instantiated resolver.
    """
    self.runtime = runtime
    self.source_dir = os.path.abspath(source_dir)
    self.legacy_runtime_version = legacy_runtime_version
    self.build_file_root = properties.VALUES.app.runtime_builders_root.Get(
        required=True)
    self.use_flex_with_buildpacks = use_flex_with_buildpacks
    log.debug('Using use_flex_with_buildpacks [%s]',
              self.use_flex_with_buildpacks)
    log.debug('Using runtime builder root [%s]', self.build_file_root)

  def GetBuilderReference(self):
    """Resolve the builder reference.

    Returns:
      BuilderReference, The reference to the builder configuration.

    Raises:
      BuilderResolveError: if this fails to resolve a builder.
    """
    # Try builder resolution in the following order, stopping once one is found.
    builder_def = (
        self._GetReferenceCustom() or
        self._GetReferencePinned() or
        self._GetReferenceFromManifest() or
        self._GetReferenceFromLegacy()
    )
    if not builder_def:
      raise BuilderResolveError(
          'Unable to resolve a builder for runtime: [{runtime}]'
          .format(runtime=self.runtime))
    return builder_def

  def _GetReferenceCustom(self):
    """Tries to resolve the reference for runtime: custom.

    If the user has an app.yaml with runtime: custom we will look in the root
    of their source directory for a custom build pipeline named cloudbuild.yaml.

    This should only be called if there is *not* a Dockerfile in the source
    root since that means they just want to build and deploy that Docker image.

    Returns:
      BuilderReference or None
    """
    if self.runtime == 'custom':
      log.debug('Using local cloud build file [%s] for custom runtime.',
                Resolver.CLOUDBUILD_FILE)
      return BuilderReference(
          self.runtime,
          _Join('file:///' + self.source_dir.replace('\\', '/').strip('/'),
                Resolver.CLOUDBUILD_FILE))
    return None

  def _GetReferencePinned(self):
    """Tries to resolve the reference for when a runtime is pinned.

    Usually a runtime is looked up in the manifest and resolved to a
    configuration file. The user does have the option of 'pinning' their build
    to a specific configuration by specifying the absolute path to a builder
    in the runtime field.

    Returns:
      BuilderReference or None
    """
    if self.runtime.startswith('gs://'):
      log.debug('Using pinned cloud build file [%s].', self.runtime)
      return BuilderReference(self.runtime, self.runtime)
    return None

  def _GetReferenceFromManifest(self):
    """Tries to resolve the reference by looking up the runtime in the manifest.

    Calculate the location of the manifest based on the builder root and load
    that data. Then try to resolve a reference based on the contents of the
    manifest.

    Returns:
      BuilderReference or None
    """

    manifest_file_name = (
        Resolver.BUILDPACKS_MANIFEST_NAME
        if self.use_flex_with_buildpacks
        else Resolver.MANIFEST_NAME)

    manifest_uri = _Join(self.build_file_root, manifest_file_name)

    log.debug('Using manifest_uri [%s]', manifest_uri)
    try:
      manifest = Manifest.LoadFromURI(manifest_uri)
      return manifest.GetBuilderReference(self.runtime)
    except FileReadError:
      log.debug('', exc_info=True)
      return None

  def _GetReferenceFromLegacy(self):
    """Tries to resolve the reference by the legacy resolution process.

    TODO(b/37542861): This can be removed after all runtimes have been migrated
    to publish their builders in the manifest instead of <runtime>.version
    files.

    If the runtime is not found in the manifest, use legacy resolution. If the
    app.yaml contains a runtime_config.runtime_version, this loads the file from
    '<runtime>-<version>.yaml' in the runtime builders root. Otherwise, it
    checks '<runtime>.version' to get the default version, and loads the
    configuration for that version.

    Returns:
      BuilderReference or None
    """
    if self.legacy_runtime_version:
      # We already have a pinned version specified, just use that file.
      return self._GetReferenceFromLegacyWithVersion(
          self.legacy_runtime_version)

    log.debug('Fetching version for runtime [%s] in legacy mode', self.runtime)
    version_file_name = self.runtime + '.version'
    version_file_uri = _Join(self.build_file_root, version_file_name)
    try:
      with _Read(version_file_uri) as f:
        version = f.read().decode().strip()
    except FileReadError:
      log.debug('', exc_info=True)
      return None

    # Now that we resolved the default version, use that for the file.
    log.debug('Using version [%s] for runtime [%s] in legacy mode',
              version, self.runtime)
    return self._GetReferenceFromLegacyWithVersion(version)

  def _GetReferenceFromLegacyWithVersion(self, version):
    """Gets the name of configuration file to use for legacy mode.

    Args:
      version: str, The pinned version of the configuration file.

    Returns:
      BuilderReference
    """
    file_name = '-'.join([self.runtime, version]) + '.yaml'
    file_uri = _Join(self.build_file_root, file_name)
    log.debug('Calculated builder definition using legacy version [%s]',
              file_uri)
    return BuilderReference(self.runtime, file_uri)


def FromServiceInfo(service, source_dir, use_flex_with_buildpacks=False):
  """Constructs a BuilderReference from a ServiceYamlInfo.

  Args:
    service: ServiceYamlInfo, The parsed service config.
    source_dir: str, the source containing the application directory to build.
    use_flex_with_buildpacks: bool, if true, use the build-image and
      run-image built through buildpacks.

  Returns:
    RuntimeBuilderVersion for the service.
  """
  runtime_config = service.parsed.runtime_config
  legacy_version = (runtime_config.get('runtime_version', None)
                    if runtime_config else None)
  resolver = Resolver(service.runtime, source_dir, legacy_version,
                      use_flex_with_buildpacks)
  return resolver.GetBuilderReference()
