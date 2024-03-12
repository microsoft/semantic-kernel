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
"""Triggers instance to gather logs and upload them to a GCS Bucket."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import base64
import datetime
import json
import time

from apitools.base.py.exceptions import HttpError

from googlecloudsdk.api_lib.cloudresourcemanager import projects_api
from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute.diagnose import diagnose_utils
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute.instances import flags as instance_flags
from googlecloudsdk.command_lib.projects import util as projects_util
from googlecloudsdk.command_lib.util import time_util
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
import six

_DIAGNOSTICS_METADATA_KEY = 'diagnostics'
_SERVICE_ACCOUNT_NAME = 'gce-diagnostics-extract-logs'
_GCS_LOGS_BUCKET_PREFIX = 'diagnostics_logs_project'
_SUCCESS_MSG = """Log collection has begun.
It may take several minutes for this operation to complete.

Logs will be made available shortly at:
gs://{0}/{1}

Status has been sent to the serial port and can be viewed by running:
gcloud compute instances get-serial-port-output $VM-NAME$ \
--project=$PROJECT$ --zone=$ZONE$"""
DETAILED_HELP = {
    'EXAMPLES':
        """\
        To export logs and upload them to a Cloud Storage Bucket, run:

          $ {command} example-instance --zone=us-central1
        """,
}
_SERVICE_ACCOUNT_TOKEN_CREATOR_ROLE_MISSING_MSG = """
To use this feature you must grant the iam.serviceAccountTokenCreator role on the project.
For more information please refer to Collecting diagnostic information:
[https://cloud.google.com/compute/docs/instances/collecting-diagnostic-information]
"""


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.GA)
class ExportLogs(base_classes.BaseCommand):
  """Triggers instance to gather logs and upload them to a Cloud Storage Bucket.

  Gathers logs from a running Compute Engine VM and exports them to a Google
  Cloud Storage Bucket. Outputs a path to the logs within the Bucket.
  """

  detailed_help = DETAILED_HELP

  @classmethod
  def Args(cls, parser):
    """See base class."""
    instance_flags.INSTANCE_ARG.AddArgument(parser)
    parser.add_argument(
        '--collect-process-traces',
        action='store_true',
        help=('Collect a 10 minute trace of the running system. On Windows, '
              'this utilizes Windows Performance Recorder. It records CPU, '
              'disk, file, and network activity during that time.'))
    parser.display_info.AddFormat('none')
    return

  def Run(self, args):
    """See base class."""
    self._diagnose_client = diagnose_utils.DiagnoseClient()
    instance_ref = self._ResolveInstance(args)
    project = properties.VALUES.core.project.Get(required=True)

    service_account = self._GetDiagnosticsServiceAccount(project)
    expiration_time = self._GetSignedUrlExpiration()
    bucket = self._GetLogBucket(project)
    log_path = self._GetLogPath(instance_ref.instance)
    url = self._CreateResumableSignedUrl(service_account, expiration_time,
                                         bucket, log_path)

    diagnostics_entry = self._ConstructDiagnosticsKeyEntry(
        url, args.collect_process_traces)
    self._diagnose_client.UpdateMetadata(
        project, instance_ref, _DIAGNOSTICS_METADATA_KEY, diagnostics_entry)

    log.Print(_SUCCESS_MSG.format(bucket, log_path))

    return {'bucket': bucket, 'logPath': log_path, 'signedUrl': url}

  def _CreateResumableSignedUrl(self, service_account, expiration, bucket,
                                filepath):
    """Make a resumable signed url using the SignBlob API of a Service Account.

    This creates a signed url that can be used by another program to upload a
    single file to the specified bucket with the specified file name.

    Args:
      service_account: The email of a service account that has permissions to
        sign a blob and create files within GCS Buckets.
      expiration: The time at which the returned signed url becomes invalid,
        measured in seconds since the epoch.
      bucket: The name of the bucket the signed url will point to.
      filepath: The name or relative path the file will have within the bucket
        once uploaded.

    Returns:
      A string url that can be used until its expiration to upload a file.
    """

    url_data = six.ensure_binary(
        'POST\n\n\n{0}\nx-goog-resumable:start\n/{1}/{2}'.format(
            expiration, bucket, filepath))

    signed_blob = ''
    try:
      signed_blob = self._diagnose_client.SignBlob(service_account, url_data)
    except HttpError as e:
      if e.status_code == 403:
        log.Print(_SERVICE_ACCOUNT_TOKEN_CREATOR_ROLE_MISSING_MSG)
      raise

    signature = six.ensure_binary(signed_blob)
    encoded_sig = base64.b64encode(signature)

    url = ('https://storage.googleapis.com/'
           '{0}/{1}?GoogleAccessId={2}&Expires={3}&Signature={4}')

    url_suffix = six.moves.urllib.parse.quote_plus(encoded_sig)

    return url.format(bucket, filepath, service_account, expiration, url_suffix)

  def _GetDiagnosticsServiceAccount(self, project):
    """Locates or creates a service account with the correct permissions.

    Attempts to locate the service account meant for creating the signed url.
    If not found, it will subsequently create the service account. It will then
    give the service account the correct IAM permissions to create a signed url
    to a GCS Bucket.

    Args:
      project: The project to search for the service account in.

    Returns:
      A string email of the service account to use.
    """
    # Search for service account by name.
    service_account = None
    for account in self._diagnose_client.ListServiceAccounts(project):
      if account.email.startswith('{}@'.format(_SERVICE_ACCOUNT_NAME)):
        service_account = account.email

    if service_account is None:
      service_account = self._diagnose_client.CreateServiceAccount(
          project, _SERVICE_ACCOUNT_NAME)

    # We can apply the correct IAM permissions for accessing the GCS Bucket
    # regardless of whether or not the account already has them.
    project_ref = projects_util.ParseProject(project)
    service_account_ref = 'serviceAccount:{}'.format(service_account)
    projects_api.AddIamPolicyBinding(project_ref, service_account_ref,
                                     'roles/storage.objectCreator')
    projects_api.AddIamPolicyBinding(project_ref, service_account_ref,
                                     'roles/storage.objectViewer')

    return service_account

  def _GetSignedUrlExpiration(self, hours=1):
    """Generate a string expiration time based on some hours in the future.

    Args:
      hours: The number of hours in the future for your timestamp to represent
    Returns:
      A string timestamp measured in seconds since the epoch.
    """
    expiration = datetime.datetime.now() + datetime.timedelta(hours=hours)
    expiration_seconds = time.mktime(expiration.timetuple())
    return six.text_type(int(expiration_seconds))

  def _GetLogBucket(self, project_id):
    """Locates or creates the GCS Bucket for logs associated with the project.

    Args:
      project_id: The id number of the project the bucket is associated with.
    Returns:
      The name of the GCS Bucket.
    """
    project_number = self._GetProjectNumber(project_id)
    bucket_name = '{}_{}'.format(_GCS_LOGS_BUCKET_PREFIX, project_number)

    bucket = self._diagnose_client.FindBucket(project_id, bucket_name)

    if bucket is None:
      bucket = self._diagnose_client.CreateBucketWithLifecycle(days_to_live=10)
      bucket.name = bucket_name
      suffix = 0

      # We can't guarantee that our chosen bucket name isn't already taken, so
      # we may have to try multiple suffixes before we generate a unique name.
      bucket_name_taken = True
      while bucket_name_taken:
        try:
          self._diagnose_client.InsertBucket(project_id, bucket)
          bucket_name_taken = False
        except HttpError as e:
          # Error 409 means that bucket name already exists.
          if e.status_code != 409:
            raise e
          bucket.name = '{}_{}'.format(bucket_name, suffix)
          suffix += 1

    return bucket.name

  def _GetProjectNumber(self, project_id):
    """Converts a project id to a project number."""
    project_ref = projects_util.ParseProject(project_id)
    project = projects_api.Get(project_ref)
    return project.projectNumber

  def _GetLogPath(self, instance):
    """Creates a timestamped filename that should be realistically unique."""
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S-%f')
    return '{}-logs-{}.zip'.format(instance, timestamp)

  def _ResolveInstance(self, args):
    """Resolves the arguments into an instance.

    Args:
      args: The command line arguments.
    Returns:
      An instance reference to a VM.
    """
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    compute_client = holder.client
    resources = holder.resources
    instance_ref = instance_flags.INSTANCE_ARG.ResolveAsResource(
        args,
        resources,
        scope_lister=instance_flags.GetInstanceZoneScopeLister(compute_client))
    return instance_ref

  def _ConstructDiagnosticsKeyEntry(self, signed_url, trace):
    """Generates a JSON String that is a command for the VM to extract the logs.

    Args:
      signed_url: The url where the logs can be uploaded.
      trace: Whether or not to take a 10 minute trace on the VM.
    Returns:
      A JSON String that can be written to the metadata server to trigger the
      extraction of logs.
    """
    expire_str = time_util.CalculateExpiration(300)
    diagnostics_key_data = {
        'signedUrl': signed_url,
        'trace': trace,
        'expireOn': expire_str
    }
    return json.dumps(diagnostics_key_data, sort_keys=True)
