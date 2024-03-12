# -*- coding: utf-8 -*-
# Copyright 2011 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Implementation of mb command for creating cloud storage buckets."""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals

import re
import textwrap

from gslib.cloud_api import AccessDeniedException, BadRequestException
from gslib.command import Command
from gslib.command_argument import CommandArgument
from gslib.commands.rpo import VALID_RPO_VALUES
from gslib.commands.rpo import VALID_RPO_VALUES_STRING
from gslib.cs_api_map import ApiSelector
from gslib.exception import CommandException
from gslib.exception import InvalidUrlError
from gslib.storage_url import StorageUrlFromString
from gslib.third_party.storage_apitools import storage_v1_messages as apitools_messages
from gslib.utils.constants import NO_MAX
from gslib.utils.retention_util import RetentionInSeconds
from gslib.utils.shim_util import GcloudStorageFlag
from gslib.utils.shim_util import GcloudStorageMap
from gslib.utils.text_util import InsistAscii
from gslib.utils.text_util import InsistOnOrOff
from gslib.utils.text_util import NormalizeStorageClass
from gslib.utils.encryption_helper import ValidateCMEK

_SYNOPSIS = """
  gsutil mb [-b (on|off)] [-c <class>] [-k <key>] [-l <location>] [-p <project>]
            [--autoclass] [--retention <time>] [--pap <setting>]
            [--placement <region1>,<region2>]
            [--rpo {}] gs://<bucket_name>...
""".format(VALID_RPO_VALUES_STRING)

_DETAILED_HELP_TEXT = ("""
<B>SYNOPSIS</B>
""" + _SYNOPSIS + """


<B>DESCRIPTION</B>
  Create one or more new buckets. Google Cloud Storage has a single namespace,
  so you are not allowed to create a bucket with a name already in use by
  another user. You can, however, carve out parts of the bucket name space
  corresponding to your company's domain name (see "gsutil help naming").

  If you don't specify a project ID or project number using the -p option, the
  buckets are created using the default project ID specified in your `gsutil
  configuration file <https://cloud.google.com/storage/docs/boto-gsutil>`_.

  The -l option specifies the location for the buckets. Once a bucket is created
  in a given location, it cannot be moved to a different location. Instead, you
  need to create a new bucket, move the data over, and then delete the original
  bucket.

<B>BUCKET STORAGE CLASSES</B>
  You can specify one of the `storage classes
  <https://cloud.google.com/storage/docs/storage-classes>`_ for a bucket
  with the -c option.

  Example:

    gsutil mb -c nearline gs://some-bucket

  See online documentation for
  `pricing <https://cloud.google.com/storage/pricing>`_ and
  `SLA <https://cloud.google.com/storage/sla>`_ details.

  If you don't specify a -c option, the bucket is created with the
  default storage class Standard Storage.

<B>BUCKET LOCATIONS</B>
  You can specify one of the `available locations
  <https://cloud.google.com/storage/docs/locations>`_ for a bucket
  with the -l option.

  Examples:

    gsutil mb -l asia gs://some-bucket

    gsutil mb -c standard -l us-east1 gs://some-bucket

  If you don't specify a -l option, the bucket is created in the default
  location (US).

<B>Retention Policy</B>
  You can specify retention period in one of the following formats:

  --retention <number>s
      Specifies retention period of <number> seconds for objects in this bucket.

  --retention <number>d
      Specifies retention period of <number> days for objects in this bucket.

  --retention <number>m
      Specifies retention period of <number> months for objects in this bucket.

  --retention <number>y
      Specifies retention period of <number> years for objects in this bucket.

  Examples:

    gsutil mb --retention 1y gs://some-bucket

    gsutil mb --retention 36m gs://some-bucket

  If you don't specify a --retention option, the bucket is created with no
  retention policy.

<B>OPTIONS</B>
  --autoclass            Enables the Autoclass feature that automatically
                         sets object storage classes.

  -b <on|off>            Specifies the uniform bucket-level access setting.
                         When "on", ACLs assigned to objects in the bucket are
                         not evaluated. Consequently, only IAM policies grant
                         access to objects in these buckets. Default is "off".

  -c class               Specifies the default storage class. Default is
                         ``Standard``. See `Available storage classes
                         <https://cloud.google.com/storage/docs/storage-classes#classes>`_
                         for a list of possible values.

  -k <key>               Set the default KMS key using the full path to the key,
                         which has the following form:
                         ``projects/[project-id]/locations/[location]/keyRings/[key-ring]/cryptoKeys/[my-key]``

  -l location            Can be any supported location. See
                         https://cloud.google.com/storage/docs/locations
                         for a discussion of this distinction. Default is US.
                         Locations are case insensitive.

  -p project             Specifies the project ID or project number to create
                         the bucket under.

  -s class               Same as -c.

  --retention time       Specifies the retention policy. Default is no retention
                         policy. This can only be set on gs:// buckets and
                         requires using the JSON API. For more details about
                         retention policy see "gsutil help retention"

  --pap setting          Specifies the public access prevention setting. Valid
                         values are "enforced" or "inherited". When
                         "enforced", objects in this bucket cannot be made
                         publicly accessible. Default is "inherited".

  --placement reg1,reg2  Two regions that form the custom dual-region.
                         Only regions within the same continent are or will ever
                         be valid. Invalid location pairs (such as
                         mixed-continent, or with unsupported regions)
                         will return an error.

  --rpo setting          Specifies the `replication setting
                         <https://cloud.google.com/storage/docs/availability-durability#cross-region-redundancy>`_.
                         This flag is not valid for single-region buckets,
                         and multi-region buckets only accept a value of
                         DEFAULT. Valid values for dual region buckets
                         are {rpo_values}. If unspecified, DEFAULT is applied
                         for dual-region and multi-region buckets.

""".format(rpo_values=VALID_RPO_VALUES_STRING))

# Regex to disallow buckets violating charset or not [3..255] chars total.
BUCKET_NAME_RE = re.compile(r'^[a-zA-Z0-9][a-zA-Z0-9\._-]{1,253}[a-zA-Z0-9]$')
# Regex to disallow buckets with individual DNS labels longer than 63.
TOO_LONG_DNS_NAME_COMP = re.compile(r'[-_a-z0-9]{64}')
_RETENTION_FLAG = '--retention'

IamConfigurationValue = apitools_messages.Bucket.IamConfigurationValue
BucketPolicyOnlyValue = IamConfigurationValue.BucketPolicyOnlyValue


class MbCommand(Command):
  """Implementation of gsutil mb command."""

  # Command specification. See base class for documentation.
  command_spec = Command.CreateCommandSpec(
      'mb',
      command_name_aliases=['makebucket', 'createbucket', 'md', 'mkdir'],
      usage_synopsis=_SYNOPSIS,
      min_args=1,
      max_args=NO_MAX,
      supported_sub_args='b:c:l:p:s:k:',
      supported_private_args=[
          'autoclass', 'retention=', 'pap=', 'placement=', 'rpo='
      ],
      file_url_ok=False,
      provider_url_ok=False,
      urls_start_arg=0,
      gs_api_support=[ApiSelector.XML, ApiSelector.JSON],
      gs_default_api=ApiSelector.JSON,
      argparse_arguments=[
          CommandArgument.MakeZeroOrMoreCloudBucketURLsArgument()
      ],
  )
  # Help specification. See help_provider.py for documentation.
  help_spec = Command.HelpSpec(
      help_name='mb',
      help_name_aliases=[
          'createbucket',
          'makebucket',
          'md',
          'mkdir',
          'location',
          'dra',
          'dras',
          'reduced_availability',
          'durable_reduced_availability',
          'rr',
          'reduced_redundancy',
          'standard',
          'storage class',
          'nearline',
          'nl',
      ],
      help_type='command_help',
      help_one_line_summary='Make buckets',
      help_text=_DETAILED_HELP_TEXT,
      subcommand_help_text={},
  )

  gcloud_storage_map = GcloudStorageMap(
      gcloud_command=['storage', 'buckets', 'create'],
      flag_map={
          '-b':
              GcloudStorageFlag({
                  'on': '--uniform-bucket-level-access',
                  'off': None,
              }),
          '-c':
              GcloudStorageFlag('--default-storage-class'),
          '-k':
              GcloudStorageFlag('--default-encryption-key'),
          '-l':
              GcloudStorageFlag('--location'),
          '-p':
              GcloudStorageFlag('--project'),
          '--pap':
              GcloudStorageFlag({
                  'enforced': '--public-access-prevention',
                  'inherited': None,
              }),
          '--placement':
              GcloudStorageFlag('--placement'),
          _RETENTION_FLAG:
              GcloudStorageFlag('--retention-period'),
          '--rpo':
              GcloudStorageFlag('--recovery-point-objective')
      },
  )

  def get_gcloud_storage_args(self):
    retention_arg_idx = 0
    while retention_arg_idx < len(self.sub_opts):
      if self.sub_opts[retention_arg_idx][0] == _RETENTION_FLAG:
        break
      retention_arg_idx += 1
    if retention_arg_idx < len(self.sub_opts):
      # Convert retention time to seconds, which gcloud knows how to handle.
      self.sub_opts[retention_arg_idx] = (
          _RETENTION_FLAG,
          str(RetentionInSeconds(self.sub_opts[retention_arg_idx][1])) + 's')
    return super().get_gcloud_storage_args(MbCommand.gcloud_storage_map)

  def RunCommand(self):
    """Command entry point for the mb command."""
    autoclass = False
    bucket_policy_only = None
    kms_key = None
    location = None
    storage_class = None
    seconds = None
    placements = None
    public_access_prevention = None
    rpo = None
    json_only_flags_in_command = []
    if self.sub_opts:
      for o, a in self.sub_opts:
        if o == '--autoclass':
          autoclass = True
          json_only_flags_in_command.append(o)
        elif o == '-k':
          kms_key = a
          ValidateCMEK(kms_key)
          json_only_flags_in_command.append(o)
        elif o == '-l':
          location = a
        elif o == '-p':
          # Project IDs are sent as header values when using gs and s3 XML APIs.
          InsistAscii(a, 'Invalid non-ASCII character found in project ID')
          self.project_id = a
        elif o == '-c' or o == '-s':
          storage_class = NormalizeStorageClass(a)
        elif o == _RETENTION_FLAG:
          seconds = RetentionInSeconds(a)
        elif o == '--rpo':
          rpo = a.strip()
          if rpo not in VALID_RPO_VALUES:
            raise CommandException(
                'Invalid value for --rpo. Must be one of: {},'
                ' provided: {}'.format(VALID_RPO_VALUES_STRING, a))
          json_only_flags_in_command.append(o)
        elif o == '-b':
          InsistOnOrOff(a, 'Only on and off values allowed for -b option')
          bucket_policy_only = (a == 'on')
          json_only_flags_in_command.append(o)
        elif o == '--pap':
          public_access_prevention = a
          json_only_flags_in_command.append(o)
        elif o == '--placement':
          placements = a.split(',')
          if len(placements) != 2:
            raise CommandException(
                'Please specify two regions separated by comma without space.'
                ' Specified: {}'.format(a))
          json_only_flags_in_command.append(o)

    bucket_metadata = apitools_messages.Bucket(location=location,
                                               rpo=rpo,
                                               storageClass=storage_class)
    if autoclass:
      bucket_metadata.autoclass = apitools_messages.Bucket.AutoclassValue(
          enabled=autoclass)
    if bucket_policy_only or public_access_prevention:
      bucket_metadata.iamConfiguration = IamConfigurationValue()
      iam_config = bucket_metadata.iamConfiguration
      if bucket_policy_only:
        iam_config.bucketPolicyOnly = BucketPolicyOnlyValue()
        iam_config.bucketPolicyOnly.enabled = bucket_policy_only
      if public_access_prevention:
        iam_config.publicAccessPrevention = public_access_prevention

    if kms_key:
      encryption = apitools_messages.Bucket.EncryptionValue()
      encryption.defaultKmsKeyName = kms_key
      bucket_metadata.encryption = encryption

    if placements:
      placement_config = apitools_messages.Bucket.CustomPlacementConfigValue()
      placement_config.dataLocations = placements
      bucket_metadata.customPlacementConfig = placement_config

    for bucket_url_str in self.args:
      bucket_url = StorageUrlFromString(bucket_url_str)
      if seconds is not None:
        if bucket_url.scheme != 'gs':
          raise CommandException('Retention policy can only be specified for '
                                 'GCS buckets.')
        retention_policy = (apitools_messages.Bucket.RetentionPolicyValue(
            retentionPeriod=seconds))
        bucket_metadata.retentionPolicy = retention_policy

      if json_only_flags_in_command and self.gsutil_api.GetApiSelector(
          bucket_url.scheme) != ApiSelector.JSON:
        raise CommandException('The {} option(s) can only be used for GCS'
                               ' Buckets with the JSON API'.format(
                                   ', '.join(json_only_flags_in_command)))

      if not bucket_url.IsBucket():
        raise CommandException('The mb command requires a URL that specifies a '
                               'bucket.\n"%s" is not valid.' % bucket_url)
      if (not BUCKET_NAME_RE.match(bucket_url.bucket_name) or
          TOO_LONG_DNS_NAME_COMP.search(bucket_url.bucket_name)):
        raise InvalidUrlError('Invalid bucket name in URL "%s"' %
                              bucket_url.bucket_name)

      self.logger.info('Creating %s...', bucket_url)
      # Pass storage_class param only if this is a GCS bucket. (In S3 the
      # storage class is specified on the key object.)
      try:
        self.gsutil_api.CreateBucket(bucket_url.bucket_name,
                                     project_id=self.project_id,
                                     metadata=bucket_metadata,
                                     provider=bucket_url.scheme)
      except AccessDeniedException as e:
        message = e.reason
        if 'key' in message:
          # This will print the error reason and append the following as a
          # suggested next step:
          #
          # To authorize, run:
          #   gsutil kms authorize \
          #     -k <kms_key> \
          #     -p <project_id>
          message += ' To authorize, run:\n  gsutil kms authorize'
          message += ' \\\n    -k %s' % kms_key
          if (self.project_id):
            message += ' \\\n    -p %s' % self.project_id
          raise CommandException(message)
        else:
          raise

      except BadRequestException as e:
        if (e.status == 400 and e.reason == 'DotfulBucketNameNotUnderTld' and
            bucket_url.scheme == 'gs'):
          bucket_name = bucket_url.bucket_name
          final_comp = bucket_name[bucket_name.rfind('.') + 1:]
          raise CommandException('\n'.join(
              textwrap.wrap(
                  'Buckets with "." in the name must be valid DNS names. The bucket'
                  ' you are attempting to create (%s) is not a valid DNS name,'
                  ' because the final component (%s) is not currently a valid part'
                  ' of the top-level DNS tree.' % (bucket_name, final_comp))))
        else:
          raise

    return 0
