# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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
"""Cloud Spanner backups API helper."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import exceptions as c_exceptions
from googlecloudsdk.core import exceptions as core_exceptions
from googlecloudsdk.core.credentials import http
from googlecloudsdk.core.util import times
import six
from six.moves import http_client as httplib
from six.moves import urllib


class HttpRequestFailedError(core_exceptions.Error):
  """Indicates that the http request failed in some way."""
  pass


# General Utils
def ParseExpireTime(expiration_value):
  """Parse flag value into Datetime format for expireTime."""
  # expiration_value could be in Datetime format or Duration format.
  datetime = (
      times.ParseDuration(expiration_value).GetRelativeDateTime(
          times.Now(times.UTC)))
  parsed_datetime = times.FormatDateTime(
      datetime, '%Y-%m-%dT%H:%M:%S.%6f%Ez', tzinfo=times.UTC)
  return parsed_datetime


def CheckAndGetExpireTime(args):
  """Check if fields for expireTime are correctly specified and parse value."""

  # User can only specify either expiration_date or retention_period, not both.
  if (args.IsSpecified('expiration_date') and
      args.IsSpecified('retention_period')) or not(
          args.IsSpecified('expiration_date') or
          args.IsSpecified('retention_period')):
    raise c_exceptions.InvalidArgumentException(
        '--expiration-date or --retention-period',
        'Must specify either --expiration-date or --retention-period.')
  if args.expiration_date:
    return args.expiration_date
  elif args.retention_period:
    return ParseExpireTime(args.retention_period)


def GetBackup(backup_ref):
  """Get a backup."""
  client = apis.GetClientInstance('spanner', 'v1')
  msgs = apis.GetMessagesModule('spanner', 'v1')
  req = msgs.SpannerProjectsInstancesBackupsGetRequest(
      name=backup_ref.RelativeName())
  return client.projects_instances_backups.Get(req)


def CreateBackup(backup_ref, args, encryption_type=None, kms_key=None):
  """Create a new backup."""
  client = apis.GetClientInstance('spanner', 'v1')
  msgs = apis.GetMessagesModule('spanner', 'v1')

  query_params = {'alt': 'json', 'backupId': args.backup}
  if encryption_type:
    query_params['encryptionConfig.encryptionType'] = encryption_type
  if kms_key:
    query_params['encryptionConfig.kmsKeyName'] = kms_key
  parent = backup_ref.Parent().RelativeName()
  url = '{}v1/{}/backups?{}'.format(client.url, parent,
                                    urllib.parse.urlencode(query_params))
  backup = msgs.Backup(
      database=parent + '/databases/' + args.database,
      expireTime=CheckAndGetExpireTime(args))
  if args.IsSpecified('version_time'):
    backup.versionTime = args.version_time

  # Workaround since gcloud cannot handle HttpBody properly (b/31403673).
  response_encoding = None if six.PY2 else 'utf-8'
  # Make an http request directly instead of using the apitools client which
  # does not support '.' characters in query parameters (b/31244944).
  response, response_body = http.Http(
      response_encoding=response_encoding).request(
          uri=url, method='POST', body=client.SerializeMessage(backup))

  if int(response.get('status')) != httplib.OK:
    raise HttpRequestFailedError('HTTP request failed. Response: ' +
                                 response_body)
  message_type = getattr(msgs, 'Operation')
  return client.DeserializeMessage(message_type, response_body)


def CopyBackup(source_backup_ref,
               destination_backup_ref,
               args,
               encryption_type=None,
               kms_key=None):
  """Copy a backup."""
  client = apis.GetClientInstance('spanner', 'v1')
  msgs = apis.GetMessagesModule('spanner', 'v1')
  copy_backup_request = msgs.CopyBackupRequest(
      backupId=destination_backup_ref.Name(),
      sourceBackup=source_backup_ref.RelativeName())
  copy_backup_request.expireTime = CheckAndGetExpireTime(args)
  if encryption_type or kms_key:
    copy_backup_request.encryptionConfig = msgs.CopyBackupEncryptionConfig(
        encryptionType=encryption_type, kmsKeyName=kms_key)

  req = msgs.SpannerProjectsInstancesBackupsCopyRequest(
      parent=destination_backup_ref.Parent().RelativeName(),
      copyBackupRequest=copy_backup_request)
  return client.projects_instances_backups.Copy(req)


def ModifyUpdateMetadataRequest(backup_ref, args, req):
  """Parse arguments and construct update backup request."""
  req.backup.name = backup_ref.Parent().RelativeName(
  ) + '/backups/' + args.backup
  req.backup.expireTime = CheckAndGetExpireTime(args)
  req.updateMask = 'expire_time'
  return req


def ModifyListRequest(instance_ref, args, req):
  """Parse arguments and construct list backups request."""
  req.parent = instance_ref.RelativeName()
  if args.database:
    database = instance_ref.RelativeName() + '/databases/' + args.database
    req.filter = 'database="{}"'.format(database)
  return req


def CheckBackupExists(backup_ref, _, req):
  """Checks if backup exists, if so, returns request."""

  # The delete API returns a 200 regardless of whether the backup being
  # deleted exists. In order to show users feedback for incorrectly
  # entered backup names, we have to make a request to check if the backup
  # exists. If the backup exists, it's deleted, otherwise, we display the
  # error from backups.Get.
  GetBackup(backup_ref)
  return req
