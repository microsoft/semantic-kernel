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

"""Utility methods to upload source to GCS and call Cloud Build service."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import gzip
import io
import operator
import os
import tarfile

from apitools.base.py import encoding
from googlecloudsdk.api_lib.cloudbuild import cloudbuild_util
from googlecloudsdk.api_lib.storage import storage_api
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core.util import files
from googlecloudsdk.core.util import times

import six
from six.moves import filter  # pylint: disable=redefined-builtin


# Paths that shouldn't be ignored client-side.
# Behavioral parity with github.com/docker/docker-py.
BLOCKLISTED_DOCKERIGNORE_PATHS = ['Dockerfile', '.dockerignore']


def _CreateTar(upload_dir, gen_files, paths, gz):
  """Create tarfile for upload to GCS.

  The third-party code closes the tarfile after creating, which does not
  allow us to write generated files after calling docker.utils.tar
  since gzipped tarfiles can't be opened in append mode.

  Args:
    upload_dir: the directory to be archived
    gen_files: Generated files to write to the tar
    paths: allowed paths in the tarfile
    gz: gzipped tarfile object
  """
  root = os.path.abspath(upload_dir)
  t = tarfile.open(mode='w', fileobj=gz)
  for path in sorted(paths):
    full_path = os.path.join(root, path)
    t.add(full_path, arcname=path, recursive=False)
  for name, contents in six.iteritems(gen_files):
    genfileobj = io.BytesIO(contents.encode())
    tar_info = tarfile.TarInfo(name=name)
    tar_info.size = len(genfileobj.getvalue())
    t.addfile(tar_info, fileobj=genfileobj)
    genfileobj.close()
  t.close()


def _GetDockerignoreExclusions(upload_dir, gen_files):
  """Helper function to read the .dockerignore on disk or in generated files.

  Args:
    upload_dir: the path to the root directory.
    gen_files: dict of filename to contents of generated files.

  Returns:
    Set of exclusion expressions from the dockerignore file.
  """
  dockerignore = os.path.join(upload_dir, '.dockerignore')
  exclude = set()
  ignore_contents = None
  if os.path.exists(dockerignore):
    ignore_contents = files.ReadFileContents(dockerignore)
  else:
    ignore_contents = gen_files.get('.dockerignore')
  if ignore_contents:
    # Read the exclusions from the dockerignore, filtering out blank lines.
    exclude = set(filter(bool, ignore_contents.splitlines()))
    # Remove paths that shouldn't be excluded on the client.
    exclude -= set(BLOCKLISTED_DOCKERIGNORE_PATHS)
  return exclude


def _GetIncludedPaths(upload_dir, source_files, exclude):
  """Helper function to filter paths in root using dockerignore and skip_files.

  We iterate separately to filter on skip_files in order to preserve expected
  behavior (standard deployment skips directories if they contain only files
  ignored by skip_files).

  Args:
    upload_dir: the path to the root directory.
    source_files: [str], relative paths to upload.
    exclude: the .dockerignore file exclusions.

  Returns:
    Set of paths (relative to upload_dir) to include.
  """
  # Import only when necessary, to decrease startup time.
  # pylint: disable=g-import-not-at-top
  import docker
  # This code replicates how docker.utils.tar() finds the root
  # and excluded paths.
  root = os.path.abspath(upload_dir)
  # Get set of all paths other than exclusions from dockerignore.
  paths = docker.utils.exclude_paths(root, list(exclude))
  # Also filter on the ignore regex from .gcloudignore or skip_files.
  paths.intersection_update(source_files)
  return paths


def UploadSource(upload_dir, source_files, object_ref, gen_files=None):
  """Upload a gzipped tarball of the source directory to GCS.

  Note: To provide parity with docker's behavior, we must respect .dockerignore.

  Args:
    upload_dir: the directory to be archived.
    source_files: [str], relative paths to upload.
    object_ref: storage_util.ObjectReference, the Cloud Storage location to
      upload the source tarball to.
    gen_files: dict of filename to (str) contents of generated config and
      source context files.
  """
  gen_files = gen_files or {}
  dockerignore_contents = _GetDockerignoreExclusions(upload_dir, gen_files)
  included_paths = _GetIncludedPaths(
      upload_dir, source_files, dockerignore_contents)

  # We can't use tempfile.NamedTemporaryFile here because ... Windows.
  # See https://bugs.python.org/issue14243. There are small cleanup races
  # during process termination that will leave artifacts on the filesystem.
  # eg, CTRL-C on windows leaves both the directory and the file. Unavoidable.
  # On Posix, `kill -9` has similar behavior, but CTRL-C allows cleanup.
  with files.TemporaryDirectory() as temp_dir:
    f = files.BinaryFileWriter(os.path.join(temp_dir, 'src.tgz'))
    with gzip.GzipFile(mode='wb', fileobj=f) as gz:
      _CreateTar(upload_dir, gen_files, included_paths, gz)
    f.close()
    storage_client = storage_api.StorageClient()
    storage_client.CopyFileToGCS(f.name, object_ref)


def GetServiceTimeoutSeconds(timeout_property_str):
  """Returns the service timeout in seconds given the duration string."""
  if timeout_property_str is None:
    return None
  build_timeout_duration = times.ParseDuration(timeout_property_str,
                                               default_suffix='s')
  return int(build_timeout_duration.total_seconds)


def GetServiceTimeoutString(timeout_property_str):
  """Returns the service timeout duration string with suffix appended."""
  if timeout_property_str is None:
    return None
  build_timeout_secs = GetServiceTimeoutSeconds(timeout_property_str)
  return six.text_type(build_timeout_secs) + 's'


class InvalidBuildError(ValueError):
  """Error indicating that ExecuteCloudBuild was given a bad Build message."""

  def __init__(self, field):
    super(InvalidBuildError, self).__init__(
        'Field [{}] was provided, but should not have been. '
        'You may be using an improper Cloud Build pipeline.'.format(field))


def _ValidateBuildFields(build, fields):
  """Validates that a Build message doesn't have fields that we populate."""
  for field in fields:
    if getattr(build, field, None) is not None:
      raise InvalidBuildError(field)


def GetDefaultBuild(output_image):
  """Get the default build for this runtime.

  This build just uses the latest docker builder image (location pulled from the
  app/container_builder_image property) to run a `docker build` with the given
  tag.

  Args:
    output_image: GCR location for the output docker image (e.g.
      `gcr.io/test-gae/hardcoded-output-tag`)

  Returns:
    Build, a CloudBuild Build message with the given steps (ready to be given to
      FixUpBuild).
  """
  messages = cloudbuild_util.GetMessagesModule()
  builder = properties.VALUES.app.container_builder_image.Get()
  log.debug('Using builder image: [{0}]'.format(builder))
  return messages.Build(
      steps=[messages.BuildStep(name=builder,
                                args=['build', '-t', output_image, '.'])],
      images=[output_image])


def FixUpBuild(build, object_ref):
  """Return a modified Build object with run-time values populated.

  Specifically:
  - `source` is pulled from the given object_ref
  - `timeout` comes from the app/cloud_build_timeout property
  - `logsBucket` uses the bucket from object_ref

  Args:
    build: cloudbuild Build message. The Build to modify. Fields 'timeout',
      'source', and 'logsBucket' will be added and may not be given.
    object_ref: storage_util.ObjectReference, the Cloud Storage location of the
      source tarball.

  Returns:
    Build, (copy) of the given Build message with the specified fields
      populated.

  Raises:
    InvalidBuildError: if the Build message had one of the fields this function
      sets pre-populated
  """
  messages = cloudbuild_util.GetMessagesModule()
  # Make a copy, so we don't modify the original
  build = encoding.CopyProtoMessage(build)
  # CopyProtoMessage doesn't preserve the order of additionalProperties; sort
  # these so that they're in a consistent order for tests (this *only* matters
  # for tests).
  if build.substitutions:
    build.substitutions.additionalProperties.sort(
        key=operator.attrgetter('key'))

  # Check that nothing we're expecting to fill in has been set already
  _ValidateBuildFields(build, ('source', 'timeout', 'logsBucket'))

  build.timeout = GetServiceTimeoutString(
      properties.VALUES.app.cloud_build_timeout.Get())
  build.logsBucket = object_ref.bucket
  build.source = messages.Source(
      storageSource=messages.StorageSource(
          bucket=object_ref.bucket,
          object=object_ref.name,
      ),
  )

  return build
