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
"""Manage and stream build logs from Cloud Builds."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import collections
import re
import threading
import time

from apitools.base.py import exceptions as api_exceptions

from googlecloudsdk.api_lib.cloudbuild import cloudbuild_util
from googlecloudsdk.api_lib.logging import common
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources
from googlecloudsdk.core.console import console_attr_os
from googlecloudsdk.core.credentials import requests as creds_requests
from googlecloudsdk.core.util import encoding

import requests

LOG_STREAM_HELP_TEXT = """
To live stream log output for this build, please ensure the grpc module is installed. Run:
  pip install grpcio
and set:
  export CLOUDSDK_PYTHON_SITEPACKAGES=1
"""

DEFAULT_LOGS_BUCKET_IS_OUTSIDE_SECURITY_PERIMETER_TEXT = """
The build is running, and logs are being written to the default logs bucket.
This tool can only stream logs if you are Viewer/Owner of the project and, if applicable, allowed by your VPC-SC security policy.

The default logs bucket is always outside any VPC-SC security perimeter.
If you want your logs saved inside your VPC-SC perimeter, use your own bucket.
See https://cloud.google.com/build/docs/securing-builds/store-manage-build-logs.
"""


class NoLogsBucketException(exceptions.Error):

  def __init__(self):
    msg = 'Build does not specify logsBucket, unable to stream logs'
    super(NoLogsBucketException, self).__init__(msg)


class DefaultLogsBucketIsOutsideSecurityPerimeterException(exceptions.Error):

  def __init__(self):
    super(DefaultLogsBucketIsOutsideSecurityPerimeterException,
          self).__init__(DEFAULT_LOGS_BUCKET_IS_OUTSIDE_SECURITY_PERIMETER_TEXT)


Response = collections.namedtuple('Response', ['status', 'headers', 'body'])


class RequestsLogTailer(object):
  """LogTailer transport to make HTTP requests using requests."""

  def __init__(self):
    self.session = creds_requests.GetSession()

  def Request(self, url, cursor):
    try:
      response = self.session.request(
          'GET', url, headers={'Range': 'bytes={0}-'.format(cursor)})
      return Response(response.status_code, response.headers, response.content)
    except requests.exceptions.RequestException as e:
      raise api_exceptions.CommunicationError('Failed to connect: %s' % e)


def GetGCLLogTailer():
  """Return a GCL LogTailer."""
  try:
    # pylint: disable=g-import-not-at-top
    from googlecloudsdk.api_lib.logging import tailing
    # pylint: enable=g-import-not-at-top
  except ImportError:
    log.out.Print(LOG_STREAM_HELP_TEXT)
    return None

  return tailing.LogTailer()


def IsCB4A(build):
  """Separate CB4A requests to print different logs."""
  if build.options:
    if build.options.cluster:
      return bool(build.options.cluster.name)
    elif build.options.anthosCluster:
      return bool(build.options.anthosCluster.membership)
  return False


class TailerBase(object):
  """Base class for log tailer classes."""
  LOG_OUTPUT_BEGIN = ' REMOTE BUILD OUTPUT '
  OUTPUT_LINE_CHAR = '-'

  def _ValidateScreenReader(self, text):
    """Modify output for better screen reader experience."""
    screen_reader = properties.VALUES.accessibility.screen_reader.GetBool()
    if screen_reader:
      return re.sub('---> ', '', text)
    return text

  def _PrintLogLine(self, text):
    """Testing Hook: This method enables better verification of output."""
    if self.out and text:
      self.out.Print(text.rstrip())

  def _PrintFirstLine(self, msg=LOG_OUTPUT_BEGIN):
    """Print a pretty starting line to identify start of build output logs."""
    width, _ = console_attr_os.GetTermSize()
    self._PrintLogLine(msg.center(width, self.OUTPUT_LINE_CHAR))

  def _PrintLastLine(self, msg=''):
    """Print a pretty ending line to identify end of build output logs."""
    width, _ = console_attr_os.GetTermSize()
    # We print an extra blank visually separating the log from other output.
    self._PrintLogLine(msg.center(width, self.OUTPUT_LINE_CHAR) + '\n')


class GCLLogTailer(TailerBase):
  """Helper class to tail logs from GCL, printing content as available."""

  def __init__(self,
               buildId,
               projectId,
               timestamp,
               logUrl=None,
               out=log.status,
               is_cb4a=False):
    self.tailer = GetGCLLogTailer()
    self.build_id = buildId
    self.project_id = projectId
    self.timestamp = timestamp
    self.out = out
    self.buffer_window_seconds = 2
    self.log_url = logUrl
    self.stop = False
    self.is_cb4a = is_cb4a

  @classmethod
  def FromBuild(cls, build, out=log.out):
    """Build a GCLLogTailer from a build resource.

    Args:
      build: Build resource, The build whose logs shall be streamed.
      out: The output stream to write the logs to.

    Returns:
      GCLLogTailer, the tailer of this build's logs.
    """
    return cls(
        buildId=build.id,
        projectId=build.projectId,
        timestamp=build.createTime,
        logUrl=build.logUrl,
        out=out,
        is_cb4a=IsCB4A(build))

  def Tail(self):
    """Tail the GCL logs and print any new bytes to the console."""

    if not self.tailer:
      return

    if self.stop:
      return

    parent = 'projects/{project_id}'.format(project_id=self.project_id)

    log_filter = ('logName="projects/{project_id}/logs/cloudbuild" AND '
                  'resource.type="build" AND '
                  'resource.labels.build_id="{build_id}"').format(
                      project_id=self.project_id, build_id=self.build_id)
    if self.is_cb4a:
      # The labels starting with 'k8s-pod/' in the log entries from GKE-on-GCP
      # clusters are different from other labels. The dots '.' in the labels are
      # converted to '_'. For example, 'k8s-pod/tekton.dev/taskRun' is
      # converted to 'k8s-pod/tekton_dev/taskRun'.
      log_filter = ('labels."k8s-pod/tekton.dev/taskRun"="{build_id}" OR '
                    'labels."k8s-pod/tekton_dev/taskRun"="{build_id}"').format(
                        build_id=self.build_id)

    output_logs = self.tailer.TailLogs(
        [parent], log_filter, buffer_window_seconds=self.buffer_window_seconds)

    self._PrintFirstLine()

    for output in output_logs:
      text = self._ValidateScreenReader(output.text_payload)
      self._PrintLogLine(text)

    self._PrintLastLine(' BUILD FINISHED; TRUNCATING OUTPUT LOGS ')
    if self.log_url:
      self._PrintLogLine(
          'Logs are available at [{log_url}].'.format(log_url=self.log_url))

    return

  def Stop(self):
    """Stop log tailing."""
    self.stop = True
    # Sleep to allow the Tailing API to send the last logs it buffered up
    time.sleep(self.buffer_window_seconds)
    if self.tailer:
      self.tailer.Stop()

  def Print(self):
    """Print GCL logs to the console."""
    parent = 'projects/{project_id}'.format(project_id=self.project_id)

    log_filter = (
        'logName="projects/{project_id}/logs/cloudbuild" AND '
        'resource.type="build" AND '
        # timestamp needed for faster querying in GCL
        'timestamp>="{timestamp}" AND '
        'resource.labels.build_id="{build_id}"').format(
            project_id=self.project_id,
            timestamp=self.timestamp,
            build_id=self.build_id)
    if self.is_cb4a:
      # The labels starting with 'k8s-pod/' in the log entries from GKE-on-GCP
      # clusters are different from other labels. The dots '.' in the labels are
      # converted to '_'. For example, 'k8s-pod/tekton.dev/taskRun' is
      # converted to 'k8s-pod/tekton_dev/taskRun'.
      log_filter = ('(labels."k8s-pod/tekton.dev/taskRun"="{build_id}" OR '
                    'labels."k8s-pod/tekton_dev/taskRun"="{build_id}") AND '
                    'timestamp>="{timestamp}"').format(
                        build_id=self.build_id, timestamp=self.timestamp)

    output_logs = common.FetchLogs(
        log_filter=log_filter, order_by='asc', parent=parent)

    self._PrintFirstLine()

    for output in output_logs:
      text = self._ValidateScreenReader(output.textPayload)
      self._PrintLogLine(text)

    self._PrintLastLine()


class GCSLogTailer(TailerBase):
  """Helper class to tail a GCS logfile, printing content as available."""

  LOG_OUTPUT_INCOMPLETE = ' (possibly incomplete) '
  GCS_URL_PATTERN = (
      'https://www.googleapis.com/storage/v1/b/{bucket}/o/{obj}?alt=media')

  def __init__(self, bucket, obj, out=log.status, url_pattern=None):
    self.transport = RequestsLogTailer()
    url_pattern = url_pattern or self.GCS_URL_PATTERN
    self.url = url_pattern.format(bucket=bucket, obj=obj)
    log.debug('GCS logfile url is ' + self.url)
    # position in the file being read
    self.cursor = 0
    self.out = out
    self.stop = False

  @classmethod
  def FromBuild(cls, build, out=log.out):
    """Build a GCSLogTailer from a build resource.

    Args:
      build: Build resource, The build whose logs shall be streamed.
      out: The output stream to write the logs to.

    Raises:
      NoLogsBucketException: If the build does not specify a logsBucket.

    Returns:
      GCSLogTailer, the tailer of this build's logs.
    """
    if not build.logsBucket:
      raise NoLogsBucketException()

    # remove gs:// prefix from bucket
    log_stripped = build.logsBucket
    gcs_prefix = 'gs://'
    if log_stripped.startswith(gcs_prefix):
      log_stripped = log_stripped[len(gcs_prefix):]

    if '/' not in log_stripped:
      log_bucket = log_stripped
      log_object_dir = ''
    else:
      [log_bucket, log_object_dir] = log_stripped.split('/', 1)
      log_object_dir += '/'

    log_object = '{object}log-{id}.txt'.format(
        object=log_object_dir,
        id=build.id,
    )

    return cls(
        bucket=log_bucket,
        obj=log_object,
        out=out,
        url_pattern='https://storage.googleapis.com/{bucket}/{obj}')

  def Poll(self, is_last=False):
    """Poll the GCS object and print any new bytes to the console.

    Args:
      is_last: True if this is the final poll operation.

    Raises:
      api_exceptions.HttpError: if there is trouble connecting to GCS.
      api_exceptions.CommunicationError: if there is trouble reaching the server
          and is_last=True.
    """
    try:
      res = self.transport.Request(self.url, self.cursor)
    except api_exceptions.CommunicationError:
      # Sometimes this request fails due to read timeouts (b/121307719). When
      # this happens we should just proceed and rely on the next poll to pick
      # up any missed logs. If this is the last request, there won't be another
      # request, and we can just fail.
      if is_last:
        raise
      return

    if res.status == 404:  # Not Found
      # Logfile hasn't been written yet (ie, build hasn't started).
      log.debug('Reading GCS logfile: 404 (no log yet; keep polling)')
      return

    if res.status == 416:  # Requested Range Not Satisfiable
      # We have consumed all available data. We'll get this a lot as we poll.
      log.debug('Reading GCS logfile: 416 (no new content; keep polling)')
      if is_last:
        self._PrintLastLine()
      return

    if res.status == 206 or res.status == 200:  # Partial Content
      # New content available. Print it!
      log.debug('Reading GCS logfile: {code} (read {count} bytes)'.format(
          code=res.status, count=len(res.body)))
      if self.cursor == 0:
        self._PrintFirstLine()
      self.cursor += len(res.body)
      decoded = encoding.Decode(res.body)
      if decoded is not None:
        decoded = self._ValidateScreenReader(decoded)
      self._PrintLogLine(decoded.rstrip('\n'))

      if is_last:
        self._PrintLastLine()
      return

    # For 429/503, there isn't much to do other than retry on the next poll.
    # If we get a 429 after the build has completed, the user may get incomplete
    # logs. This is expected to be rare enough to not justify building a complex
    # exponential retry system.
    if res.status == 429:  # Too Many Requests
      log.warning('Reading GCS logfile: 429 (server is throttling us)')
      if is_last:
        self._PrintLastLine(self.LOG_OUTPUT_INCOMPLETE)
      return

    if res.status >= 500 and res.status < 600:  # Server Error
      log.warning('Reading GCS logfile: got {0}, retrying'.format(res.status))
      if is_last:
        self._PrintLastLine(self.LOG_OUTPUT_INCOMPLETE)
      return

    # Default: any other codes are treated as errors.
    headers = dict(res.headers)
    headers['status'] = res.status
    raise api_exceptions.HttpError(headers, res.body, self.url)

  def Tail(self):
    """Tail the GCS object and print any new bytes to the console."""
    while not self.stop:
      self.Poll()
      time.sleep(1)

    # Poll the logs one final time to ensure we have everything. We know this
    # final poll will get the full log contents because GCS is strongly
    # consistent and Cloud Build waits for logs to finish pushing before
    # marking the build complete.
    self.Poll(is_last=True)

  def Stop(self):
    """Stop log tailing."""
    self.stop = True

  def Print(self):
    """Print GCS logs to the console."""
    self.Poll(is_last=True)


class ThreadInterceptor(threading.Thread):
  """Wrapper to intercept thread exceptions."""

  def __init__(self, target):
    super(ThreadInterceptor, self).__init__()
    self.target = target
    self.exception = None

  def run(self):
    try:
      self.target()
    except api_exceptions.HttpError as e:
      if e.status_code == 403:
        # The only way to successfully create a build and then be unable to read
        # the logs bucket is if you are using the default logs bucket and
        # VPC-SC.
        self.exception = DefaultLogsBucketIsOutsideSecurityPerimeterException()
      else:
        self.exception = e
    except api_exceptions.CommunicationError as e:
      self.exception = e


class CloudBuildClient(object):
  """Client for interacting with the Cloud Build API (and Cloud Build logs)."""

  def __init__(self, client=None, messages=None, support_gcl=False):
    self.client = client or cloudbuild_util.GetClientInstance()
    self.messages = messages or cloudbuild_util.GetMessagesModule()
    self.support_gcl = support_gcl

  def GetBuild(self, build_ref):
    """Get a Build message.

    Args:
      build_ref: Build reference. Expects a cloudbuild.projects.locations.builds
        but also supports cloudbuild.projects.builds.

    Returns:
      Build resource
    """
    # Legacy build_refs (for cloudbuild.projects.builds) don't have a location
    # attached. Convert to the expected type and add the default location.
    if build_ref.Collection() == 'cloudbuild.projects.builds':
      build_ref = resources.REGISTRY.Create(
          collection='cloudbuild.projects.locations.builds',
          projectsId=build_ref.projectId,
          locationsId=cloudbuild_util.DEFAULT_REGION,
          buildsId=build_ref.id)

    return self.client.projects_locations_builds.Get(
        self.messages.CloudbuildProjectsLocationsBuildsGetRequest(
            name=build_ref.RelativeName()))

  def ShouldStopTailer(self, build, build_ref, log_tailer, working_statuses):
    """Checks whether a log tailer should be stopped.

    Args:
      build: Build object, containing build status
      build_ref: Build reference, The build whose logs shall be streamed.
      log_tailer: Specific log tailer object
      working_statuses: Valid working statuses that define we should continue
        tailing

    Returns:
      Build message, the completed or terminated build.
    """
    while build.status in working_statuses:
      build = self.GetBuild(build_ref)
      time.sleep(1)

    if log_tailer:
      log_tailer.Stop()

    return build

  def Stream(self, build_ref, out=log.out):
    """Streams the logs for a build if available.

    Regardless of whether logs are available for streaming, awaits build
    completion before returning.

    Args:
      build_ref: Build reference, The build whose logs shall be streamed.
      out: The output stream to write the logs to.

    Raises:
      NoLogsBucketException: If the build is expected to specify a logsBucket
      but does not.

    Returns:
      Build message, the completed or terminated build.
    """
    build = self.GetBuild(build_ref)
    if not build.options or build.options.logging not in [
        self.messages.BuildOptions.LoggingValueValuesEnum.NONE,
        self.messages.BuildOptions.LoggingValueValuesEnum.STACKDRIVER_ONLY,
        self.messages.BuildOptions.LoggingValueValuesEnum.CLOUD_LOGGING_ONLY,
    ]:
      log_tailer = GCSLogTailer.FromBuild(build, out=out)
    elif build.options.logging in [
        self.messages.BuildOptions.LoggingValueValuesEnum.STACKDRIVER_ONLY,
        self.messages.BuildOptions.LoggingValueValuesEnum.CLOUD_LOGGING_ONLY,
    ] and self.support_gcl:
      log.info('Streaming logs from GCL: requested logging mode is {0}.'.format(
          build.options.logging))
      log_tailer = GCLLogTailer.FromBuild(build, out=out)
    else:
      log.info('Not streaming logs: requested logging mode is {0}.'.format(
          build.options.logging))
      log_tailer = None

    statuses = self.messages.Build.StatusValueValuesEnum
    working_statuses = [
        statuses.QUEUED,
        statuses.WORKING,
    ]

    t = None
    if log_tailer:
      t = ThreadInterceptor(target=log_tailer.Tail)
      t.start()
    build = self.ShouldStopTailer(build, build_ref, log_tailer,
                                  working_statuses)
    if t:
      t.join()
      if t.exception is not None:
        raise t.exception

    return build

  def PrintLog(self, build_ref):
    """Print the logs for a build.

    Args:
      build_ref: Build reference, The build whose logs shall be streamed.

    Raises:
      NoLogsBucketException: If the build does not specify a logsBucket.
    """
    build = self.GetBuild(build_ref)

    if not build.options or build.options.logging not in [
        self.messages.BuildOptions.LoggingValueValuesEnum.NONE,
        self.messages.BuildOptions.LoggingValueValuesEnum.STACKDRIVER_ONLY,
        self.messages.BuildOptions.LoggingValueValuesEnum.CLOUD_LOGGING_ONLY,
    ]:
      log_tailer = GCSLogTailer.FromBuild(build)
    elif build.options.logging in [
        self.messages.BuildOptions.LoggingValueValuesEnum.STACKDRIVER_ONLY,
        self.messages.BuildOptions.LoggingValueValuesEnum.CLOUD_LOGGING_ONLY,
    ]:
      log.info('Printing logs from GCL: requested logging mode is {0}.'.format(
          build.options.logging))
      log_tailer = GCLLogTailer.FromBuild(build)
    else:
      log.info('Logs not available: build logging mode is {0}.'.format(
          build.options.logging))
      log_tailer = None

    if log_tailer:
      log_tailer.Print()
