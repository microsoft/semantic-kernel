# -*- coding: utf-8 -*-
# Copyright 2015 Google Inc. All Rights Reserved.
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
"""Implementation of rewrite command (in-place cloud object transformation)."""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals

import sys
import textwrap
import time

from apitools.base.py import encoding
from boto import config

from gslib.cloud_api import EncryptionException
from gslib.command import Command
from gslib.command_argument import CommandArgument
from gslib.cs_api_map import ApiSelector
from gslib.exception import CommandException
from gslib.name_expansion import NameExpansionIterator
from gslib.name_expansion import SeekAheadNameExpansionIterator
from gslib.progress_callback import FileProgressCallbackHandler
from gslib.storage_url import StorageUrlFromString
from gslib.third_party.storage_apitools import storage_v1_messages as apitools_messages
from gslib.thread_message import FileMessage
from gslib.utils.cloud_api_helper import GetCloudApiInstance
from gslib.utils.constants import NO_MAX
from gslib.utils.constants import UTF8
from gslib.utils.encryption_helper import CryptoKeyType
from gslib.utils.encryption_helper import CryptoKeyWrapperFromKey
from gslib.utils.encryption_helper import GetEncryptionKeyWrapper
from gslib.utils.encryption_helper import MAX_DECRYPTION_KEYS
from gslib.utils.shim_util import GcloudStorageFlag
from gslib.utils.shim_util import GcloudStorageMap
from gslib.utils.system_util import StdinIterator
from gslib.utils.text_util import ConvertRecursiveToFlatWildcard
from gslib.utils.text_util import NormalizeStorageClass
from gslib.utils import text_util
from gslib.utils.translation_helper import PreconditionsFromHeaders

MAX_PROGRESS_INDICATOR_COLUMNS = 65

_SYNOPSIS = """
  gsutil rewrite -k [-O] [-f] [-r] [-s] url...
  gsutil rewrite -k [-O] [-f] [-r] [-s] -I
  gsutil rewrite -s [-k] [-O] [-f] [-r] url...
  gsutil rewrite -s [-k] [-O] [-f] [-r] -I
"""

_DETAILED_HELP_TEXT = ("""
<B>SYNOPSIS</B>
""" + _SYNOPSIS + """


<B>DESCRIPTION</B>
  The gsutil rewrite command rewrites cloud objects, applying the specified
  transformations to them. The transformation(s) are atomic for each affected
  object and applied based on the input transformation flags. Object metadata
  values are preserved unless altered by a transformation. At least one
  transformation flag, -k or -s, must be included in the command.

  The -k flag is supported to add, rotate, or remove encryption keys on
  objects.  For example, the command:

    gsutil rewrite -k -r gs://bucket

  updates all objects in gs://bucket with the current encryption key
  from your boto config file, which may either be a base64-encoded CSEK or the
  fully-qualified name of a Cloud KMS key.

  The rewrite command acts only on live object versions, so specifying a
  URL with a generation number fails. If you want to rewrite a noncurrent
  version, first copy it to the live version, then rewrite it, for example:

    gsutil cp gs://bucket/object#123 gs://bucket/object
    gsutil rewrite -k gs://bucket/object

  You can use the -s option to specify a new storage class for objects.  For
  example, the command:

    gsutil rewrite -s nearline gs://bucket/foo

  rewrites the object, changing its storage class to nearline.

  If you specify the -k option and you have an encryption key set in your boto
  configuration file, the rewrite command skips objects that are already
  encrypted with the specified key.  For example, if you run:

    gsutil rewrite -k -r gs://bucket

  and gs://bucket contains objects encrypted with the key specified in your boto
  configuration file, gsutil skips rewriting those objects and only rewrites
  objects that are not encrypted with the specified key. This avoids the cost of
  performing redundant rewrite operations.

  If you specify the -k option and you do not have an encryption key set in your
  boto configuration file, gsutil always rewrites each object, without
  explicitly specifying an encryption key. This results in rewritten objects
  being encrypted with either the bucket's default KMS key (if one is set) or
  Google-managed encryption (no CSEK or CMEK). Gsutil does not attempt to
  determine whether the operation is redundant (and thus skippable) because
  gsutil cannot be sure how the object is encrypted after the rewrite. Note that
  if your goal is to encrypt objects with a bucket's default KMS key, you can
  avoid redundant rewrite costs by specifying the bucket's default KMS key in
  your boto configuration file; this allows gsutil to perform an accurate
  comparison of the objects' current and desired encryption configurations and
  skip rewrites for objects already encrypted with that key.

  If have an encryption key set in your boto configuration file and specify
  multiple transformations, gsutil only skips those that would not change
  the object's state. For example, if you run:

    gsutil rewrite -s nearline -k -r gs://bucket

  and gs://bucket contains objects that already match the encryption
  configuration but have a storage class of standard, the only transformation
  applied to those objects would be the change in storage class.

  You can pass a list of URLs (one per line) to rewrite on stdin instead of as
  command line arguments by using the -I option. This allows you to use gsutil
  in a pipeline to rewrite objects identified by a program, such as:

    some_program | gsutil -m rewrite -k -I

  The contents of stdin can name cloud URLs and wildcards of cloud URLs.

  The rewrite command requires OWNER permissions on each object to preserve
  object ACLs. You can bypass this by using the -O flag, which causes
  gsutil not to read the object's ACL and instead apply the default object ACL
  to the rewritten object:

    gsutil rewrite -k -O -r gs://bucket


<B>OPTIONS</B>
  -f            Continues silently (without printing error messages) despite
                errors when rewriting multiple objects. If some of the objects
                could not be rewritten, gsutil's exit status is non-zero even
                if this flag is set. This option is implicitly set when running
                "gsutil -m rewrite ...".

  -I            Causes gsutil to read the list of objects to rewrite from stdin.
                This allows you to run a program that generates the list of
                objects to rewrite.

  -k            Rewrite objects with the current encryption key specified in
                your boto configuration file. The value for encryption_key may
                be either a base64-encoded CSEK or a fully-qualified KMS key
                name. If no value is specified for encryption_key, gsutil
                ignores this flag. Instead, rewritten objects are encrypted with
                the bucket's default KMS key, if one is set, or Google-managed
                encryption, if no default KMS key is set.

  -O            When a bucket has uniform bucket-level access (UBLA) enabled,
                the -O flag is required and skips all ACL checks. When a
                bucket has UBLA disabled, the -O flag rewrites objects with the
                bucket's default object ACL instead of the existing object ACL.
                This is needed if you do not have OWNER permission on the
                object.

  -R, -r        The -R and -r options are synonymous. Causes bucket or bucket
                subdirectory contents to be rewritten recursively.

  -s <class>    Rewrite objects using the specified storage class.
""")


def _RewriteExceptionHandler(cls, e):
  """Simple exception handler to allow post-completion status."""
  if not cls.continue_on_error:
    cls.logger.error(str(e))
  cls.op_failure_count += 1


def _RewriteFuncWrapper(cls, name_expansion_result, thread_state=None):
  cls.RewriteFunc(name_expansion_result, thread_state=thread_state)


def GenerationCheckGenerator(url_strs):
  """Generator function that ensures generation-less (live) arguments."""
  for url_str in url_strs:
    if StorageUrlFromString(url_str).generation is not None:
      raise CommandException('"rewrite" called on URL with generation (%s).' %
                             url_str)
    yield url_str


class _TransformTypes(object):
  """Enum class for valid transforms."""
  CRYPTO_KEY = 'crypto_key'
  STORAGE_CLASS = 'storage_class'


class RewriteCommand(Command):
  """Implementation of gsutil rewrite command."""

  # Command specification. See base class for documentation.
  command_spec = Command.CreateCommandSpec(
      'rewrite',
      command_name_aliases=[],
      usage_synopsis=_SYNOPSIS,
      min_args=0,
      max_args=NO_MAX,
      supported_sub_args='fkIrROs:',
      file_url_ok=False,
      provider_url_ok=False,
      urls_start_arg=0,
      gs_api_support=[ApiSelector.JSON],
      gs_default_api=ApiSelector.JSON,
      argparse_arguments=[CommandArgument.MakeZeroOrMoreCloudURLsArgument()])
  # Help specification. See help_provider.py for documentation.
  help_spec = Command.HelpSpec(
      help_name='rewrite',
      help_name_aliases=['rekey', 'rotate'],
      help_type='command_help',
      help_one_line_summary='Rewrite objects',
      help_text=_DETAILED_HELP_TEXT,
      subcommand_help_text={},
  )

  gcloud_storage_map = GcloudStorageMap(
      gcloud_command=['storage', 'objects', 'update'],
      flag_map={
          '-I':
              GcloudStorageFlag('-I'),
          '-f':
              GcloudStorageFlag('--continue-on-error'),
          # Adding encryptions handled in shim_util.py.
          '-k':
              None if config.get('GSUtil', 'encryption_key', None) else
              GcloudStorageFlag('--clear-encryption-key'),
          '-O':
              GcloudStorageFlag('--no-preserve-acl'),
          '-r':
              GcloudStorageFlag('-r'),
          '-R':
              GcloudStorageFlag('-r'),
          '-s':
              GcloudStorageFlag('-s'),
      },
  )

  def CheckProvider(self, url):
    if url.scheme != 'gs':
      raise CommandException(
          '"rewrite" called on URL with unsupported provider: %s' % str(url))

  def RunCommand(self):
    """Command entry point for the rewrite command."""
    self.continue_on_error = self.parallel_operations
    self.csek_hash_to_keywrapper = {}
    self.dest_storage_class = None
    self.no_preserve_acl = False
    self.read_args_from_stdin = False
    self.supported_transformation_flags = ['-k', '-s']
    self.transform_types = set()

    self.op_failure_count = 0
    self.boto_file_encryption_keywrapper = GetEncryptionKeyWrapper(config)
    self.boto_file_encryption_sha256 = (
        self.boto_file_encryption_keywrapper.crypto_key_sha256
        if self.boto_file_encryption_keywrapper else None)

    if self.sub_opts:
      for o, a in self.sub_opts:
        if o == '-f':
          self.continue_on_error = True
        elif o == '-k':
          self.transform_types.add(_TransformTypes.CRYPTO_KEY)
        elif o == '-I':
          self.read_args_from_stdin = True
        elif o == '-O':
          self.no_preserve_acl = True
        elif o == '-r' or o == '-R':
          self.recursion_requested = True
          self.all_versions = True
        elif o == '-s':
          self.transform_types.add(_TransformTypes.STORAGE_CLASS)
          self.dest_storage_class = NormalizeStorageClass(a)

    if self.read_args_from_stdin:
      if self.args:
        raise CommandException('No arguments allowed with the -I flag.')
      url_strs = StdinIterator()
    else:
      if not self.args:
        raise CommandException('The rewrite command (without -I) expects at '
                               'least one URL.')
      url_strs = self.args

    if not self.transform_types:
      raise CommandException(
          'rewrite command requires at least one transformation flag. '
          'Currently supported transformation flags: %s' %
          self.supported_transformation_flags)

    self.preconditions = PreconditionsFromHeaders(self.headers or {})

    url_strs_generator = GenerationCheckGenerator(url_strs)

    # Convert recursive flag to flat wildcard to avoid performing multiple
    # listings.
    if self.recursion_requested:
      url_strs_generator = ConvertRecursiveToFlatWildcard(url_strs_generator)

    # Expand the source argument(s).
    name_expansion_iterator = NameExpansionIterator(
        self.command_name,
        self.debug,
        self.logger,
        self.gsutil_api,
        url_strs_generator,
        self.recursion_requested,
        project_id=self.project_id,
        continue_on_error=self.continue_on_error or self.parallel_operations,
        bucket_listing_fields=['name', 'size'])

    seek_ahead_iterator = None
    # Cannot seek ahead with stdin args, since we can only iterate them
    # once without buffering in memory.
    if not self.read_args_from_stdin:
      # Perform the same recursive-to-flat conversion on original url_strs so
      # that it is as true to the original iterator as possible.
      seek_ahead_url_strs = ConvertRecursiveToFlatWildcard(url_strs)
      seek_ahead_iterator = SeekAheadNameExpansionIterator(
          self.command_name,
          self.debug,
          self.GetSeekAheadGsutilApi(),
          seek_ahead_url_strs,
          self.recursion_requested,
          all_versions=self.all_versions,
          project_id=self.project_id)

    # Rather than have each worker repeatedly calculate the sha256 hash for each
    # decryption_key in the boto config, do this once now and cache the results.
    for i in range(0, MAX_DECRYPTION_KEYS):
      key_number = i + 1
      keywrapper = CryptoKeyWrapperFromKey(
          config.get('GSUtil', 'decryption_key%s' % str(key_number), None))
      if keywrapper is None:
        # Stop at first attribute absence in lexicographical iteration.
        break
      if keywrapper.crypto_type == CryptoKeyType.CSEK:
        self.csek_hash_to_keywrapper[keywrapper.crypto_key_sha256] = keywrapper
    # Also include the encryption_key, since it should be used to decrypt and
    # then encrypt if the object's CSEK should remain the same.
    if self.boto_file_encryption_sha256 is not None:
      self.csek_hash_to_keywrapper[self.boto_file_encryption_sha256] = (
          self.boto_file_encryption_keywrapper)

    if self.boto_file_encryption_keywrapper is None:
      msg = '\n'.join(
          textwrap.wrap(
              'NOTE: No encryption_key was specified in the boto configuration '
              'file, so gsutil will not provide an encryption key in its rewrite '
              'API requests. This will decrypt the objects unless they are in '
              'buckets with a default KMS key set, in which case the service '
              'will automatically encrypt the rewritten objects with that key.')
      )
      print('%s\n' % msg, file=sys.stderr)

    # Perform rewrite requests in parallel (-m) mode, if requested.
    self.Apply(_RewriteFuncWrapper,
               name_expansion_iterator,
               _RewriteExceptionHandler,
               fail_on_error=(not self.continue_on_error),
               shared_attrs=['op_failure_count'],
               seek_ahead_iterator=seek_ahead_iterator)

    if self.op_failure_count:
      plural_str = 's' if self.op_failure_count else ''
      raise CommandException('%d file%s/object%s could not be rewritten.' %
                             (self.op_failure_count, plural_str, plural_str))

    return 0

  def RewriteFunc(self, name_expansion_result, thread_state=None):
    gsutil_api = GetCloudApiInstance(self, thread_state=thread_state)
    transform_url = name_expansion_result.expanded_storage_url

    self.CheckProvider(transform_url)

    # Get all fields so that we can ensure that the target metadata is
    # specified correctly.
    src_metadata = gsutil_api.GetObjectMetadata(
        transform_url.bucket_name,
        transform_url.object_name,
        generation=transform_url.generation,
        provider=transform_url.scheme)

    if self.no_preserve_acl:
      # Leave ACL unchanged.
      src_metadata.acl = []
    elif not src_metadata.acl:
      raise CommandException(
          'No OWNER permission found for object %s. If your bucket has uniform '
          'bucket-level access (UBLA) enabled, include the -O option in your '
          'command to avoid this error. If your bucket does not use UBLA, you '
          'can use the -O option to apply the bucket\'s default object ACL '
          'when rewriting.' % transform_url)

    # Note: If other transform types are added, they must ensure that the
    # encryption key configuration matches the boto configuration, because
    # gsutil maintains an invariant that all objects it writes use the
    # encryption_key value (including decrypting if no key is present).

    # Store metadata about src encryption to make logic below easier to read.
    src_encryption_kms_key = (src_metadata.kmsKeyName
                              if src_metadata.kmsKeyName else None)

    src_encryption_sha256 = None
    if (src_metadata.customerEncryption and
        src_metadata.customerEncryption.keySha256):
      src_encryption_sha256 = src_metadata.customerEncryption.keySha256
      # In python3, hashes are bytes, use ascii since it should be ascii
      src_encryption_sha256 = src_encryption_sha256.encode('ascii')

    src_was_encrypted = (src_encryption_sha256 is not None or
                         src_encryption_kms_key is not None)

    # Also store metadata about dest encryption.
    dest_encryption_kms_key = None
    if (self.boto_file_encryption_keywrapper is not None and
        self.boto_file_encryption_keywrapper.crypto_type == CryptoKeyType.CMEK):
      dest_encryption_kms_key = self.boto_file_encryption_keywrapper.crypto_key

    dest_encryption_sha256 = None
    if (self.boto_file_encryption_keywrapper is not None and
        self.boto_file_encryption_keywrapper.crypto_type == CryptoKeyType.CSEK):
      dest_encryption_sha256 = (
          self.boto_file_encryption_keywrapper.crypto_key_sha256)

    should_encrypt_dest = self.boto_file_encryption_keywrapper is not None

    encryption_unchanged = (src_encryption_sha256 == dest_encryption_sha256 and
                            src_encryption_kms_key == dest_encryption_kms_key)

    # Prevent accidental key rotation.
    if (_TransformTypes.CRYPTO_KEY not in self.transform_types and
        not encryption_unchanged):
      raise EncryptionException(
          'The "-k" flag was not passed to the rewrite command, but the '
          'encryption_key value in your boto config file did not match the key '
          'used to encrypt the object "%s" (hash: %s). To encrypt the object '
          'using a different key, you must specify the "-k" flag.' %
          (transform_url, src_encryption_sha256))

    # Determine if we can skip this rewrite operation (this should only be done
    # when ALL of the specified transformations are redundant).
    redundant_transforms = []

    # STORAGE_CLASS transform is redundant if the target storage class matches
    # the existing storage class.
    if (_TransformTypes.STORAGE_CLASS in self.transform_types and
        self.dest_storage_class == NormalizeStorageClass(
            src_metadata.storageClass)):
      redundant_transforms.append('storage class')

    # CRYPTO_KEY transform is redundant if we're using the same encryption
    # key that was used to encrypt the source. However, if no encryption key was
    # specified, we should still perform the rewrite. This results in the
    # rewritten object either being encrypted with its bucket's default KMS key
    # or having no CSEK/CMEK encryption applied. While we could attempt fetching
    # the bucket's metadata and checking its default KMS key before performing
    # the rewrite (in the case where we appear to be transitioning from
    # no key to no key), that is vulnerable to the race condition where the
    # default KMS key is changed between when we check it and when we rewrite
    # the object.
    if (_TransformTypes.CRYPTO_KEY in self.transform_types and
        should_encrypt_dest and encryption_unchanged):
      redundant_transforms.append('encryption key')

    if len(redundant_transforms) == len(self.transform_types):
      self.logger.info('Skipping %s, all transformations were redundant: %s' %
                       (transform_url, redundant_transforms))
      return

    # First make a deep copy of the source metadata, then overwrite any
    # requested attributes (e.g. if a storage class change was specified).
    dest_metadata = encoding.PyValueToMessage(
        apitools_messages.Object, encoding.MessageToPyValue(src_metadata))

    # Remove some unnecessary/invalid fields.
    dest_metadata.generation = None
    # Service has problems if we supply an ID, but it is responsible for
    # generating one, so it is not necessary to include it here.
    dest_metadata.id = None
    # Ensure we don't copy over the KMS key name or CSEK key info from the
    # source object; those should only come from the boto config's
    # encryption_key value.
    dest_metadata.customerEncryption = None
    dest_metadata.kmsKeyName = None

    # Both a storage class change and CMEK encryption should be set as part of
    # the dest object's metadata. CSEK encryption, if specified, is added to the
    # request later via headers obtained from the keywrapper value passed to
    # encryption_tuple.
    if _TransformTypes.STORAGE_CLASS in self.transform_types:
      dest_metadata.storageClass = self.dest_storage_class
    if dest_encryption_kms_key is not None:
      dest_metadata.kmsKeyName = dest_encryption_kms_key

    # Make sure we have the CSEK key necessary to decrypt.
    decryption_keywrapper = None
    if src_encryption_sha256 is not None:
      if src_encryption_sha256 in self.csek_hash_to_keywrapper:
        decryption_keywrapper = (
            self.csek_hash_to_keywrapper[src_encryption_sha256])
      else:
        raise EncryptionException(
            'Missing decryption key with SHA256 hash %s. No decryption key '
            'matches object %s' % (src_encryption_sha256, transform_url))

    operation_name = 'Rewriting'
    if _TransformTypes.CRYPTO_KEY in self.transform_types:
      if src_was_encrypted and should_encrypt_dest:
        if not encryption_unchanged:
          operation_name = 'Rotating'
        # Else, keep "Rewriting". This might occur when -k was specified and was
        # redundant, but we're performing the operation anyway because some
        # other transformation was not redundant.
      elif src_was_encrypted and not should_encrypt_dest:
        operation_name = 'Decrypting'
      elif not src_was_encrypted and should_encrypt_dest:
        operation_name = 'Encrypting'

    # TODO: Remove this call (used to verify tests) and make it processed by
    # the UIThread.
    sys.stderr.write(
        _ConstructAnnounceText(operation_name, transform_url.url_string))
    sys.stderr.flush()

    # Message indicating beginning of operation.
    gsutil_api.status_queue.put(
        FileMessage(transform_url,
                    None,
                    time.time(),
                    finished=False,
                    size=src_metadata.size,
                    message_type=FileMessage.FILE_REWRITE))

    progress_callback = FileProgressCallbackHandler(
        gsutil_api.status_queue,
        src_url=transform_url,
        operation_name=operation_name).call

    gsutil_api.CopyObject(src_metadata,
                          dest_metadata,
                          src_generation=transform_url.generation,
                          preconditions=self.preconditions,
                          progress_callback=progress_callback,
                          decryption_tuple=decryption_keywrapper,
                          encryption_tuple=self.boto_file_encryption_keywrapper,
                          provider=transform_url.scheme,
                          fields=[])

    # Message indicating end of operation.
    gsutil_api.status_queue.put(
        FileMessage(transform_url,
                    None,
                    time.time(),
                    finished=True,
                    size=src_metadata.size,
                    message_type=FileMessage.FILE_REWRITE))


def _ConstructAnnounceText(operation_name, url_string):
  """Constructs announce text for ongoing operations on url_string.

  This truncates the text to a maximum of MAX_PROGRESS_INDICATOR_COLUMNS, and
  informs the rewrite-related operation ('Encrypting', 'Rotating', or
  'Decrypting').

  Args:
    operation_name: String describing the operation, i.e.
        'Rotating' or 'Encrypting'.
    url_string: String describing the file/object being processed.

  Returns:
    Formatted announce text for outputting operation progress.
  """
  # Operation name occupies 10 characters (enough for 'Encrypting'), plus a
  # space. The rest is used for url_string. If a longer operation name is
  # used, it will be truncated. We can revisit this size if we need to support
  # a longer operation, but want to make sure the terminal output is meaningful.
  justified_op_string = operation_name[:10].ljust(11)
  start_len = len(justified_op_string)
  end_len = len(': ')
  if (start_len + len(url_string) + end_len > MAX_PROGRESS_INDICATOR_COLUMNS):
    ellipsis_len = len('...')
    url_string = '...%s' % url_string[-(MAX_PROGRESS_INDICATOR_COLUMNS -
                                        start_len - end_len - ellipsis_len):]
  base_announce_text = '%s%s:' % (justified_op_string, url_string)
  format_str = '{0:%ds}' % MAX_PROGRESS_INDICATOR_COLUMNS
  return format_str.format(base_announce_text)
