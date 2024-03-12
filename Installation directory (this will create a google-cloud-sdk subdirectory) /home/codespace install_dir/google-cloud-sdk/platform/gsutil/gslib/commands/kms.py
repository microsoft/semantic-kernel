# -*- coding: utf-8 -*-
# Copyright 2018 Google Inc. All Rights Reserved.
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
"""This module provides the kms command to gsutil."""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals

import getopt
import textwrap

from gslib import metrics
from gslib.cloud_api import AccessDeniedException
from gslib.cloud_api import ServiceException
from gslib.command import Command
from gslib.command_argument import CommandArgument
from gslib.cs_api_map import ApiSelector
from gslib.exception import CommandException
from gslib.exception import NO_URLS_MATCHED_TARGET
from gslib.help_provider import CreateHelpText
from gslib.kms_api import KmsApi
from gslib.project_id import PopulateProjectId
from gslib.third_party.kms_apitools.cloudkms_v1_messages import Binding
from gslib.third_party.storage_apitools import storage_v1_messages as apitools_messages
from gslib.utils import text_util
from gslib.utils.constants import NO_MAX
from gslib.utils.encryption_helper import ValidateCMEK
from gslib.utils.retry_util import Retry
from gslib.utils.shim_util import GcloudStorageFlag
from gslib.utils.shim_util import GcloudStorageMap

_AUTHORIZE_SYNOPSIS = """
  gsutil kms authorize [-p <proj_id>] -k <kms_key>
"""

_ENCRYPTION_SYNOPSIS = """
  gsutil kms encryption [(-d|[-k <kms_key>])] [-w] gs://<bucket_name>...
"""

_SERVICEACCOUNT_SYNOPSIS = """
  gsutil kms serviceaccount [-p <proj_id>]
"""

_SYNOPSIS = (_AUTHORIZE_SYNOPSIS + _ENCRYPTION_SYNOPSIS.lstrip('\n') +
             _SERVICEACCOUNT_SYNOPSIS.lstrip('\n') + '\n')

# pylint: disable=line-too-long
_AUTHORIZE_DESCRIPTION = """
<B>AUTHORIZE</B>
  The authorize sub-command checks that the default (or supplied) project has a
  Cloud Storage service agent created for it, and if not, it creates one. It then
  adds appropriate encrypt/decrypt permissions to Cloud KMS resources such that the
  service agent can write and read Cloud KMS-encrypted objects in buckets associated
  with the service agent's project.

<B>AUTHORIZE EXAMPLES</B>
  Authorize "my-project" to use a Cloud KMS key:

    gsutil kms authorize -p my-project \\
        -k projects/key-project/locations/us-east1/keyRings/key-ring/cryptoKeys/my-key

<B>AUTHORIZE OPTIONS</B>
  -k <key>      The path to the KMS key to use. The path has
                the following form:
                ``projects/[project-id]/locations/[location]/keyRings/[key-ring]/cryptoKeys/[my-key]``

  -p <project>  The ID or number of the project being authorized to use the Cloud
                KMS key. If this flag is not included, your
                default project is authorized.

"""

_ENCRYPTION_DESCRIPTION = """
<B>ENCRYPTION</B>
  The encryption sub-command is used to set, display, or clear a bucket's
  default KMS key, which is used to encrypt newly-written objects if no other
  key is specified.

<B>ENCRYPTION EXAMPLES</B>
  Set the default KMS key for my-bucket:

    gsutil kms encryption \\
        -k projects/key-project/locations/us-east1/keyRings/key-ring/cryptoKeys/my-key \\
        gs://my-bucket

  Show the default KMS key for my-bucket, if one is set:

    gsutil kms encryption gs://my-bucket

  Clear the default KMS key so newly-written objects are not encrypted using it:

    gsutil kms encryption -d gs://my-bucket

  Once you clear the default KMS key, newly-written objects are encrypted with
  Google-managed encryption keys by default.

<B>ENCRYPTION OPTIONS</B>
  -k <key>      Set the default KMS key for my-bucket using the
                full path to the key, which has the following
                form:
                ``projects/[project-id]/locations/[location]/keyRings/[key-ring]/cryptoKeys/[my-key]``

  -w            (used with -k key) Display a warning rather than
                failing if gsutil is unable to verify that
                the specified key contains the correct IAM bindings
                for encryption/decryption. This is useful for
                users that do not have getIamPolicy permission
                but know that the key has the correct IAM policy
                for encryption in the user's project.

  -d            Clear the default KMS key.

"""
# pylint: enable=line-too-long

_SERVICEACCOUNT_DESCRIPTION = """
<B>SERVICEACCOUNT</B>
  The serviceaccount sub-command displays the Cloud Storage service agent
  that is used to perform Cloud KMS operations against your default project
  (or a supplied project).

<B>SERVICEACCOUNT EXAMPLES</B>
  Show the service account for my-project:

    gsutil kms serviceaccount -p my-project

<B>SERVICEACCOUNT OPTIONS</B>
  -p <project>  The ID or number of the project whose Cloud Storage service
                agent is being requested. If this flag is not
                included, your default project is used.

"""

_DESCRIPTION = """
  The kms command is used to configure Google Cloud Storage and Cloud KMS
  resources to support encryption of Cloud Storage objects with
  `Cloud KMS keys
  <https://cloud.google.com/storage/docs/encryption/customer-managed-keys>`_.

  The kms command has three sub-commands that deal with configuring Cloud
  Storage's integration with Cloud KMS: ``authorize``, ``encryption``,
  and ``serviceaccount``.

  Before using this command, read the `prerequisites
  <https://cloud.google.com/storage/docs/encryption/using-customer-managed-keys#prereqs>`_.
  for using Cloud KMS with Cloud Storage.
""" + (_AUTHORIZE_DESCRIPTION + _ENCRYPTION_DESCRIPTION +
       _SERVICEACCOUNT_DESCRIPTION)

_DETAILED_HELP_TEXT = CreateHelpText(_SYNOPSIS, _DESCRIPTION)

_authorize_help_text = CreateHelpText(_AUTHORIZE_SYNOPSIS,
                                      _AUTHORIZE_DESCRIPTION)
_encryption_help_text = CreateHelpText(_ENCRYPTION_SYNOPSIS,
                                       _ENCRYPTION_DESCRIPTION)
_serviceaccount_help_text = CreateHelpText(_SERVICEACCOUNT_SYNOPSIS,
                                           _SERVICEACCOUNT_DESCRIPTION)

_AUTHORIZE_COMMAND = GcloudStorageMap(
    gcloud_command=['storage', 'service-agent'],
    flag_map={
        '-p': GcloudStorageFlag('--project'),
        '-k': GcloudStorageFlag('--authorize-cmek'),
    })

_SERVICEACCOUNT_COMMAND = GcloudStorageMap(
    gcloud_command=['storage', 'service-agent'],
    flag_map={
        '-p': GcloudStorageFlag('--project'),
    })


class KmsCommand(Command):
  """Implements of gsutil kms command."""

  command_spec = Command.CreateCommandSpec(
      'kms',
      usage_synopsis=_SYNOPSIS,
      min_args=1,
      max_args=NO_MAX,
      supported_sub_args='dk:p:w',
      file_url_ok=False,
      provider_url_ok=False,
      urls_start_arg=1,
      gs_api_support=[ApiSelector.JSON],
      gs_default_api=ApiSelector.JSON,
      argparse_arguments={
          'authorize': [],
          'encryption': [CommandArgument.MakeNCloudBucketURLsArgument(1)],
          'serviceaccount': [],
      })
  # Help specification. See help_provider.py for documentation.
  help_spec = Command.HelpSpec(
      help_name='kms',
      help_name_aliases=[],
      help_type='command_help',
      help_one_line_summary='Configure Cloud KMS encryption',
      help_text=_DETAILED_HELP_TEXT,
      subcommand_help_text={
          'authorize': _authorize_help_text,
          'encryption': _encryption_help_text,
          'serviceaccount': _serviceaccount_help_text
      },
  )

  gcloud_storage_map = GcloudStorageMap(
      gcloud_command={
          'authorize': _AUTHORIZE_COMMAND,
          'serviceaccount': _SERVICEACCOUNT_COMMAND,
          # "encryption" subcommand handled in get_gcloud_storage_args.
      },
      flag_map={})

  def get_gcloud_storage_args(self):
    if self.args[0] == 'encryption':
      gcloud_storage_map = GcloudStorageMap(gcloud_command={
          'encryption':
              GcloudStorageMap(
                  gcloud_command=['storage', 'buckets'],
                  flag_map={
                      '-d': GcloudStorageFlag('--clear-default-encryption-key'),
                      '-k': GcloudStorageFlag('--default-encryption-key'),
                      '-w': GcloudStorageFlag(''),
                  }),
      },
                                            flag_map={})
      if '-d' in self.args or '-k' in self.args:
        gcloud_storage_map.gcloud_command['encryption'].gcloud_command += [
            'update'
        ]
      else:
        gcloud_storage_map.gcloud_command['encryption'].gcloud_command += [
            'describe',
            ('--format=value[separator=\": \"](name, encryption'
             '.defaultKmsKeyName.yesno(no="No default encryption key."))'),
            '--raw'
        ]
    else:
      gcloud_storage_map = KmsCommand.gcloud_storage_map

    return super().get_gcloud_storage_args(gcloud_storage_map)

  def _GatherSubOptions(self, subcommand_name):
    self.CheckArguments()
    self.clear_kms_key = False
    self.kms_key = None
    self.warn_on_key_authorize_failure = False

    if self.sub_opts:
      for o, a in self.sub_opts:
        if o == '-p':
          self.project_id = a
        elif o == '-k':
          self.kms_key = a
          ValidateCMEK(self.kms_key)
        elif o == '-d':
          self.clear_kms_key = True
        elif o == '-w':
          self.warn_on_key_authorize_failure = True

    if self.warn_on_key_authorize_failure and (
        self.subcommand_name != 'encryption' or not self.kms_key):
      raise CommandException('\n'.join(
          textwrap.wrap(
              'The "-w" option should only be specified for the "encryption" '
              'subcommand and must be used with the "-k" option.')))
    # Determine the project (used in the serviceaccount and authorize
    # subcommands), either from the "-p" option's value or the default specified
    # in the user's Boto config file.
    if not self.project_id:
      self.project_id = PopulateProjectId(None)

  @Retry(ServiceException, tries=3, timeout_secs=1)
  def _AuthorizeProject(self, project_id, kms_key):
    """Authorizes a project's service account to be used with a KMS key.

    Authorizes the Cloud Storage-owned service account for project_id to be used
    with kms_key.

    Args:
      project_id: (str) Project id string (not number).
      kms_key: (str) Fully qualified resource name for the KMS key.

    Returns:
      (str, bool) A 2-tuple consisting of:
      1) The email address for the service account associated with the project,
         which is authorized to encrypt/decrypt with the specified key.
      2) A bool value - True if we had to grant the service account permission
         to encrypt/decrypt with the given key; False if the required permission
         was already present.
    """
    # Request the Cloud Storage-owned service account for project_id, creating
    # it if it does not exist.
    service_account = self.gsutil_api.GetProjectServiceAccount(
        project_id, provider='gs').email_address

    kms_api = KmsApi(logger=self.logger)
    self.logger.debug('Getting IAM policy for %s', kms_key)
    try:
      policy = kms_api.GetKeyIamPolicy(kms_key)
      self.logger.debug('Current policy is %s', policy)

      # Check if the required binding is already present; if not, add it and
      # update the key's IAM policy.
      added_new_binding = False
      binding = Binding(role='roles/cloudkms.cryptoKeyEncrypterDecrypter',
                        members=['serviceAccount:%s' % service_account])
      if binding not in policy.bindings:
        policy.bindings.append(binding)
        kms_api.SetKeyIamPolicy(kms_key, policy)
        added_new_binding = True
      return (service_account, added_new_binding)
    except AccessDeniedException:
      if self.warn_on_key_authorize_failure:
        text_util.print_to_fd('\n'.join(
            textwrap.wrap(
                'Warning: Check that your Cloud Platform project\'s service '
                'account has the "cloudkms.cryptoKeyEncrypterDecrypter" role '
                'for the specified key. Without this role, you may not be '
                'able to encrypt or decrypt objects using the key which will '
                'prevent you from uploading or downloading objects.')))
        return (service_account, False)
      else:
        raise

  def _Authorize(self):
    self._GatherSubOptions('authorize')
    if not self.kms_key:
      raise CommandException('%s %s requires a key to be specified with -k' %
                             (self.command_name, self.subcommand_name))

    _, newly_authorized = self._AuthorizeProject(self.project_id, self.kms_key)
    if newly_authorized:
      print('Authorized project %s to encrypt and decrypt with key:\n%s' %
            (self.project_id, self.kms_key))
    else:
      print('Project %s was already authorized to encrypt and decrypt with '
            'key:\n%s.' % (self.project_id, self.kms_key))
    return 0

  def _EncryptionClearKey(self, bucket_metadata, bucket_url):
    """Clears the defaultKmsKeyName on a Cloud Storage bucket.

    Args:
      bucket_metadata: (apitools_messages.Bucket) Metadata for the given bucket.
      bucket_url: (gslib.storage_url.StorageUrl) StorageUrl of the given bucket.
    """
    bucket_metadata.encryption = apitools_messages.Bucket.EncryptionValue()
    print('Clearing default encryption key for %s...' %
          str(bucket_url).rstrip('/'))
    self.gsutil_api.PatchBucket(bucket_url.bucket_name,
                                bucket_metadata,
                                fields=['encryption'],
                                provider=bucket_url.scheme)

  def _EncryptionSetKey(self, bucket_metadata, bucket_url,
                        svc_acct_for_project_num):
    """Sets defaultKmsKeyName on a Cloud Storage bucket.

    Args:
      bucket_metadata: (apitools_messages.Bucket) Metadata for the given bucket.
      bucket_url: (gslib.storage_url.StorageUrl) StorageUrl of the given bucket.
      svc_acct_for_project_num: (Dict[int, str]) Mapping of project numbers to
          their corresponding service account.
    """
    bucket_project_number = bucket_metadata.projectNumber
    try:
      # newly_authorized will always be False if the project number is in our
      # cache dict, since we've already called _AuthorizeProject on it.
      service_account, newly_authorized = (
          svc_acct_for_project_num[bucket_project_number], False)
    except KeyError:
      service_account, newly_authorized = self._AuthorizeProject(
          bucket_project_number, self.kms_key)
      svc_acct_for_project_num[bucket_project_number] = service_account
    if newly_authorized:
      text_util.print_to_fd('Authorized service account %s to use key:\n%s' %
                            (service_account, self.kms_key))

    bucket_metadata.encryption = apitools_messages.Bucket.EncryptionValue(
        defaultKmsKeyName=self.kms_key)
    print('Setting default KMS key for bucket %s...' %
          str(bucket_url).rstrip('/'))
    self.gsutil_api.PatchBucket(bucket_url.bucket_name,
                                bucket_metadata,
                                fields=['encryption'],
                                provider=bucket_url.scheme)

  def _Encryption(self):
    self._GatherSubOptions('encryption')
    # For each project, we should only make one API call to look up its
    # associated Cloud Storage-owned service account; subsequent lookups can be
    # pulled from this cache dict.
    svc_acct_for_project_num = {}

    def _EncryptionForBucket(blr):
      """Set, clear, or get the defaultKmsKeyName for a bucket."""
      bucket_url = blr.storage_url

      if bucket_url.scheme != 'gs':
        raise CommandException(
            'The %s command can only be used with gs:// bucket URLs.' %
            self.command_name)

      # Determine the project from the provided bucket.
      bucket_metadata = self.gsutil_api.GetBucket(
          bucket_url.bucket_name,
          fields=['encryption', 'projectNumber'],
          provider=bucket_url.scheme)

      # "-d" flag was specified, so clear the default KMS key and return.
      if self.clear_kms_key:
        self._EncryptionClearKey(bucket_metadata, bucket_url)
        return 0
      # "-k" flag was specified, so set the default KMS key and return.
      if self.kms_key:
        self._EncryptionSetKey(bucket_metadata, bucket_url,
                               svc_acct_for_project_num)
        return 0
      # Neither "-d" nor "-k" was specified, so emit the default KMS key and
      # return.
      bucket_url_string = str(bucket_url).rstrip('/')
      if (bucket_metadata.encryption and
          bucket_metadata.encryption.defaultKmsKeyName):
        print('Default encryption key for %s:\n%s' %
              (bucket_url_string, bucket_metadata.encryption.defaultKmsKeyName))
      else:
        print('Bucket %s has no default encryption key' % bucket_url_string)
      return 0

    # Iterate over bucket args, performing the specified encryption operation
    # for each.
    some_matched = False
    url_args = self.args
    if not url_args:
      self.RaiseWrongNumberOfArgumentsException()
    for url_str in url_args:
      # Throws a CommandException if the argument is not a bucket.
      bucket_iter = self.GetBucketUrlIterFromArg(url_str)
      for bucket_listing_ref in bucket_iter:
        some_matched = True
        _EncryptionForBucket(bucket_listing_ref)

    if not some_matched:
      raise CommandException(NO_URLS_MATCHED_TARGET % list(url_args))
    return 0

  def _ServiceAccount(self):
    self.CheckArguments()
    if not self.args:
      self.args = ['gs://']
    if self.sub_opts:
      for o, a in self.sub_opts:
        if o == '-p':
          self.project_id = a

    if not self.project_id:
      self.project_id = PopulateProjectId(None)

    # Request the service account for that project; this might create the
    # service account if it doesn't already exist.
    self.logger.debug('Checking service account for project %s',
                      self.project_id)

    service_account = self.gsutil_api.GetProjectServiceAccount(
        self.project_id, provider='gs').email_address

    print(service_account)

    return 0

  def _RunSubCommand(self, func):
    try:
      self.sub_opts, self.args = getopt.getopt(
          self.args, self.command_spec.supported_sub_args)
      # Commands with both suboptions and subcommands need to reparse for
      # suboptions, so we log again.
      metrics.LogCommandParams(sub_opts=self.sub_opts)
      return func(self)
    except getopt.GetoptError:
      self.RaiseInvalidArgumentException()

  def RunCommand(self):
    """Command entry point for the kms command."""
    # If the only credential type the user supplies in their boto file is hmac,
    # GetApiSelector logic will force us to use the XML API. As the XML API does
    # not support all the operations needed for kms subcommands, fail early.
    if self.gsutil_api.GetApiSelector(provider='gs') != ApiSelector.JSON:
      raise CommandException('\n'.join(
          textwrap.wrap(
              'The "%s" command can only be used with the GCS JSON API. If you '
              'have only supplied hmac credentials in your boto file, please '
              'instead supply a credential type that can be used with the JSON '
              'API.' % self.command_name)))

  def RunCommand(self):
    """Command entry point for the kms command."""
    # If the only credential type the user supplies in their boto file is hmac,
    # GetApiSelector logic will force us to use the XML API. As the XML API does
    # not support all the operations needed for kms subcommands, fail early.
    if self.gsutil_api.GetApiSelector(provider='gs') != ApiSelector.JSON:
      raise CommandException('\n'.join(
          textwrap.wrap(
              'The "%s" command can only be used with the GCS JSON API, which '
              'cannot use HMAC credentials. Please supply a credential '
              'type that is compatible with the JSON API (e.g. OAuth2) in your '
              'boto config file.' % self.command_name)))

    method_for_subcommand = {
        'authorize': KmsCommand._Authorize,
        'encryption': KmsCommand._Encryption,
        'serviceaccount': KmsCommand._ServiceAccount
    }
    self.subcommand_name = self.args.pop(0)
    if self.subcommand_name in method_for_subcommand:
      metrics.LogCommandParams(subcommands=[self.subcommand_name])
      return self._RunSubCommand(method_for_subcommand[self.subcommand_name])
    else:
      raise CommandException('Invalid subcommand "%s" for the %s command.' %
                             (self.subcommand_name, self.command_name))
