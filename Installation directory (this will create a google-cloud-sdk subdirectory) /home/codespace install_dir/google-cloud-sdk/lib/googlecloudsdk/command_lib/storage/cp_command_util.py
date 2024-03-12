# -*- coding: utf-8 -*- #
# Copyright 2022 Google LLC. All Rights Reserved.
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
"""Generic logic for cp and mv command surfaces.

Uses command surface tests. Ex: cp_test.py, not cp_command_util_test.py.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import collections
import contextlib
import os

from googlecloudsdk.api_lib.storage import cloud_api
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.storage import encryption_util
from googlecloudsdk.command_lib.storage import errors
from googlecloudsdk.command_lib.storage import errors_util
from googlecloudsdk.command_lib.storage import flags
from googlecloudsdk.command_lib.storage import folder_util
from googlecloudsdk.command_lib.storage import name_expansion
from googlecloudsdk.command_lib.storage import plurality_checkable_iterator
from googlecloudsdk.command_lib.storage import rm_command_util
from googlecloudsdk.command_lib.storage import stdin_iterator
from googlecloudsdk.command_lib.storage import storage_url
from googlecloudsdk.command_lib.storage import user_request_args_factory
from googlecloudsdk.command_lib.storage.tasks import task_executor
from googlecloudsdk.command_lib.storage.tasks import task_graph_executor
from googlecloudsdk.command_lib.storage.tasks import task_status
from googlecloudsdk.command_lib.storage.tasks.cp import copy_task_iterator
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core.util import files
from googlecloudsdk.core.util import platforms


_ALL_VERSIONS_HELP_TEXT = """\
Copy all source versions from a source bucket or folder. If not set, only the
live version of each source object is copied.

Note: This option is only useful when the destination bucket has Object
Versioning enabled. Additionally, the generation numbers of copied versions do
not necessarily match the order of the original generation numbers.
"""
# TODO(b/223800321): Maybe offer ability to limit parallel encoding workers.
_GZIP_IN_FLIGHT_EXTENSIONS_HELP_TEXT = """\
Applies gzip transport encoding to any file upload whose
extension matches the input extension list. This is useful when
uploading files with compressible content such as .js, .css,
or .html files. This also saves network bandwidth while
leaving the data uncompressed in Cloud Storage.

When you specify the `--gzip-in-flight` option, files being
uploaded are compressed in-memory and on-the-wire only. Both the local
files and Cloud Storage objects remain uncompressed. The
uploaded objects retain the `Content-Type` and name of the
original files."""
_GZIP_IN_FLIGHT_ALL_HELP_TEXT = """\
Applies gzip transport encoding to file uploads. This option
works like the `--gzip-in-flight` option described above,
but it applies to all uploaded files, regardless of extension.

CAUTION: If some of the source files don't compress well, such
as binary data, using this option may result in longer uploads."""
_GZIP_LOCAL_EXTENSIONS_HELP_TEXT = """\
Applies gzip content encoding to any file upload whose
extension matches the input extension list. This is useful when
uploading files with compressible content such as .js, .css,
or .html files. This saves network bandwidth and space in Cloud Storage.

When you specify the `--gzip-local` option, the data from
files is compressed before it is uploaded, but the original files are left
uncompressed on the local disk. The uploaded objects retain the `Content-Type`
and name of the original files. However, the `Content-Encoding` metadata
is set to `gzip` and the `Cache-Control` metadata set to `no-transform`.
The data remains compressed on Cloud Storage servers and will not be
decompressed on download by gcloud storage because of the `no-transform`
field.

Since the local gzip option compresses data prior to upload, it is not subject
to the same compression buffer bottleneck of the in-flight gzip option."""
_GZIP_LOCAL_ALL_HELP_TEXT = """\
Applies gzip content encoding to file uploads. This option
works like the `--gzip-local` option described above,
but it applies to all uploaded files, regardless of extension.

CAUTION: If some of the source files don't compress well, such as binary data,
using this option may result in files taking up more space in the cloud than
they would if left uncompressed."""
_MANIFEST_HELP_TEXT = """\
Outputs a manifest log file with detailed information about each item that
was copied. This manifest contains the following information for each item:

- Source path.
- Destination path.
- Source size.
- Bytes transferred.
- MD5 hash.
- Transfer start time and date in UTC and ISO 8601 format.
- Transfer completion time and date in UTC and ISO 8601 format.
- Final result of the attempted transfer: OK, error, or skipped.
- Details, if any.

If the manifest file already exists, gcloud storage appends log items to the
existing file.

Objects that are marked as "OK" or "skipped" in the existing manifest file
are not retried by future commands. Objects marked as "error" are retried.
"""
_PRESERVE_POSIX_HELP_TEXT = """\
Causes POSIX attributes to be preserved when objects are copied. With this feature enabled,
gcloud storage will copy several fields provided by the stat command:
access time, modification time, owner UID, owner group GID, and the mode
(permissions) of the file.

For uploads, these attributes are read off of local files and stored in the
cloud as custom metadata. For downloads, custom cloud metadata is set as POSIX
attributes on files after they are downloaded.

On Windows, this flag will only set and restore access time and modification
time because Windows doesn't have a notion of POSIX UID, GID, and mode.
"""
_PRESERVE_SYMLINKS_HELP_TEST = """\
Preserve symlinks instead of copying what they point to. With this feature
enabled, uploaded symlinks will be represented as placeholders in the cloud
whose content consists of the linked path. Inversely, such placeholders will be
converted to symlinks when downloaded while this feature is enabled, as
described at https://cloud.google.com/storage-transfer/docs/metadata-preservation#posix_to.

Directory symlinks are only followed if this flag is specified.

CAUTION: No validation is applied to the symlink target paths. Once downloaded,
preserved symlinks will point to whatever path was specified by the placeholder,
regardless of the location or permissions of the path, or whether it actually
exists.

This feature is not supported on Windows.
"""


def add_gzip_in_flight_flags(parser):
  """Adds flags for gzip parsing in flight."""
  parser.add_argument(
      '-J',
      '--gzip-in-flight-all',
      action='store_true',
      help=_GZIP_IN_FLIGHT_ALL_HELP_TEXT,
  )
  parser.add_argument(
      '-j',
      '--gzip-in-flight',
      metavar='FILE_EXTENSIONS',
      type=arg_parsers.ArgList(),
      help=_GZIP_IN_FLIGHT_EXTENSIONS_HELP_TEXT,
  )


def add_include_managed_folders_flag(parser):
  parser.add_argument(
      '--include-managed-folders',
      action='store_true',
      default=False,
      help=(
          'Includes managed folders in command operations. For'
          ' transfers, gcloud storage will set up managed folders in the'
          ' destination with the same IAM policy bindings as the source.'
          ' Managed folders are only included with recursive cloud-to-cloud'
          ' transfers.'
      ),
  )


def add_ignore_symlinks_flag(parser_or_group, default=False):
  """Adds flag for skipping copying symlinks."""
  parser_or_group.add_argument(
      '--ignore-symlinks',
      action='store_true',
      default=default,
      help=(
          'Ignore file symlinks instead of copying what they point to.'
      ),
  )


def add_preserve_symlinks_flag(parser_or_group, default=False):
  """Adds flag for preserving symlinks."""
  parser_or_group.add_argument(
      '--preserve-symlinks',
      action='store_true',
      default=default,
      help=_PRESERVE_SYMLINKS_HELP_TEST,
  )


def add_cp_mv_rsync_flags(parser):
  """Adds flags shared by cp, mv, and rsync."""
  flags.add_additional_headers_flag(parser)
  flags.add_continue_on_error_flag(parser)
  flags.add_object_metadata_flags(parser)
  flags.add_precondition_flags(parser)
  parser.add_argument(
      '--content-md5',
      metavar='MD5_DIGEST',
      help=('Manually specified MD5 hash digest for the contents of an uploaded'
            ' file. This flag cannot be used when uploading multiple files. The'
            ' custom digest is used by the cloud provider for validation.'))
  parser.add_argument(
      '-n',
      '--no-clobber',
      action='store_true',
      help=(
          'Do not overwrite existing files or objects at the destination.'
          ' Skipped items will be printed. This option may perform an'
          ' additional GET request for cloud objects before attempting an'
          ' upload.'
      ),
  )
  parser.add_argument(
      '-P',
      '--preserve-posix',
      action='store_true',
      help=_PRESERVE_POSIX_HELP_TEXT,
  )
  parser.add_argument(
      '-U',
      '--skip-unsupported',
      action='store_true',
      help='Skip objects with unsupported object types.',
  )


def add_cp_and_mv_flags(parser, release_track):
  """Adds flags to cp, mv, or other cp-based commands."""
  parser.add_argument('source', nargs='*', help='The source path(s) to copy.')
  parser.add_argument('destination', help='The destination path.')
  add_cp_mv_rsync_flags(parser)
  parser.add_argument(
      '-A', '--all-versions', action='store_true', help=_ALL_VERSIONS_HELP_TEXT)
  parser.add_argument(
      '--do-not-decompress',
      action='store_true',
      help='Do not automatically decompress downloaded gzip files.')
  parser.add_argument(
      '-D',
      '--daisy-chain',
      action='store_true',
      help='Copy in "daisy chain" mode, which means copying an object by'
      ' first downloading it to the machine where the command is run, then'
      ' uploading it to the destination bucket. The default mode is a "copy'
      ' in the cloud," where data is copied without uploading or downloading.'
      ' During a copy in the cloud, a source composite object remains'
      ' composite at its destination. However, you can use daisy chain mode'
      ' to change a composite object into a non-composite object.'
      ' Note: Daisy chain mode is automatically used when copying between'
      ' providers.')
  # TODO(b/304524534): Remove this condition.
  if release_track is base.ReleaseTrack.ALPHA:
    add_include_managed_folders_flag(parser)
  symlinks_group = parser.add_group(
      mutex=True,
      help=(
          'Flags to influence behavior when handling symlinks. Only one value'
          ' may be set.'
      ),
  )
  add_ignore_symlinks_flag(symlinks_group)
  add_preserve_symlinks_flag(symlinks_group)
  parser.add_argument('-L', '--manifest-path', help=_MANIFEST_HELP_TEXT)
  parser.add_argument(
      '-v',
      '--print-created-message',
      action='store_true',
      help='Prints the version-specific URL for each copied object.')
  parser.add_argument(
      '-s',
      '--storage-class',
      help='Specify the storage class of the destination object. If not'
      ' specified, the default storage class of the destination bucket is'
      ' used. This option is not valid for copying to non-cloud destinations.')

  gzip_flags_group = parser.add_group(mutex=True)
  add_gzip_in_flight_flags(gzip_flags_group)
  gzip_flags_group.add_argument(
      '-Z',
      '--gzip-local-all',
      action='store_true',
      help=_GZIP_LOCAL_ALL_HELP_TEXT,
  )
  gzip_flags_group.add_argument(
      '-z',
      '--gzip-local',
      metavar='FILE_EXTENSIONS',
      type=arg_parsers.ArgList(),
      help=_GZIP_LOCAL_EXTENSIONS_HELP_TEXT,
  )

  acl_flags_group = parser.add_group()
  flags.add_predefined_acl_flag(acl_flags_group)
  flags.add_preserve_acl_flag(acl_flags_group)
  flags.add_encryption_flags(parser)
  flags.add_read_paths_from_stdin_flag(
      parser,
      help_text=(
          'Read the list of resources to copy from stdin. No need to enter'
          ' a source argument if this flag is present.\nExample:'
          ' "storage cp -I gs://bucket/destination"\n'
          ' Note: To copy the contents of one file directly from stdin, use "-"'
          ' as the source argument without the "-I" flag.'
      ),
  )


def add_recursion_flag(parser):
  """Adds flag for copying with recursion.

  Not used by mv.

  Args:
    parser (parser_arguments.ArgumentInterceptor): Parser passed to surface.
  """
  parser.add_argument(
      '-R',
      '-r',
      '--recursive',
      action='store_true',
      help=(
          'Recursively copy the contents of any directories that match the'
          ' source path expression.'
      ),
  )


def validate_include_managed_folders(
    args, raw_source_urls, raw_destination_url
):
  """Validates that arguments are consistent with managed folder operations."""
  # TODO(b/304524534): Replace with args.include_managed_folders.
  if not getattr(args, 'include_managed_folders', False):
    return

  if isinstance(raw_destination_url, storage_url.FileUrl):
    raise errors.Error(
        'Cannot include managed folders with a non-cloud destination: {}'
        .format(raw_destination_url)
    )

  if getattr(args, 'read_paths_from_stdin', None):
    raise errors.Error(
        'Cannot include managed folders when reading paths from stdin, as this'
        ' would require storing all paths passed to gcloud storage in memory.'
    )

  for url_string in raw_source_urls:
    url = storage_url.storage_url_from_string(url_string)
    if isinstance(url, storage_url.FileUrl):
      raise errors.Error(
          'Cannot include managed folders with a non-cloud source: {}'.format(
              url
          )
      )

  if not args.recursive:
    raise errors.Error(
        'Cannot include managed folders unless recursion is enabled.'
    )

  errors_util.raise_error_if_not_gcs(args.command_path, raw_destination_url)


def _validate_args(args, raw_destination_url):
  """Raises errors if invalid flags are passed."""
  if args.no_clobber and args.if_generation_match:
    raise errors.Error(
        'Cannot specify both generation precondition and no-clobber.'
    )

  if args.preserve_symlinks and platforms.OperatingSystem.IsWindows():
    raise errors.Error('Symlink preservation is not supported for Windows.')

  if (isinstance(raw_destination_url, storage_url.FileUrl) and
      args.storage_class):
    raise errors.Error(
        'Cannot specify storage class for a non-cloud destination: {}'.format(
            raw_destination_url
        )
    )
  validate_include_managed_folders(args, args.source, raw_destination_url)


@contextlib.contextmanager
def _get_shared_stream(args, raw_destination_url):
  """Context manager for streams used in streaming downloads.

  Warns the user when downloading to a named pipe.

  Args:
    args (parser_extensions.Namespace): Flags passed by the user.
    raw_destination_url (storage_url.StorageUrl): The destination of the
      transfer. May contain unexpanded wildcards.

  Yields:
    A stream used for downloads, or None if the transfer is not a streaming
    download. The stream is closed by the context manager if it is not stdout.
  """
  if raw_destination_url.is_stdio:
    yield os.fdopen(1, 'wb')
  elif raw_destination_url.is_stream:
    log.warning('Downloading to a pipe.'
                ' This command may stall until the pipe is read.')
    with files.BinaryFileWriter(args.destination) as stream:
      yield stream
  else:
    yield None


def _is_parallelizable(args, raw_destination_url, first_source_url):
  """Determines whether a a `cp` workload is parallelizable.

  Logs warnings if gcloud storage is configured to parallelize workloads, but
  doing so is not possible.

  Args:
    args (parser_extensions.Namespace): Flags passed by the user.
    raw_destination_url (storage_url.StorageUrl): The destination of the
      transfer. May contain unexpanded wildcards.
    first_source_url (storage_url.StorageUrl): The first source URL passed by
      the user. May contain unexpanded wildcards.

  Returns:
    True if the transfer is parallelizable, False otherwise.
  """
  configured_for_parallelism = (
      properties.VALUES.storage.process_count.GetInt() != 1 or
      properties.VALUES.storage.thread_count.GetInt() != 1)

  if args.all_versions:
    if configured_for_parallelism:
      log.warning(
          'Using sequential instead of parallel task execution. This will'
          ' maintain version ordering when copying all versions of an object.')
    return False

  if raw_destination_url.is_stream:
    if configured_for_parallelism:
      log.warning(
          'Using sequential instead of parallel task execution to write to a'
          ' stream.')
    return False

  # Only the first url needs to be checked since multiple sources aren't
  # allowed with stdin.
  if first_source_url.is_stdio:
    if configured_for_parallelism:
      log.warning('Using sequential instead of parallel task execution to'
                  ' transfer from stdin.')
    return False

  return True


def _execute_copy_tasks(
    args,
    delete_source,
    parallelizable,
    raw_destination_url,
    source_expansion_iterator,
):
  """Returns appropriate exit code after creating and executing copy tasks."""
  if raw_destination_url.is_stdio:
    task_status_queue = None
  else:
    task_status_queue = task_graph_executor.multiprocessing_context.Queue()

  user_request_args = (
      user_request_args_factory.get_user_request_args_from_command_args(
          args, metadata_type=user_request_args_factory.MetadataType.OBJECT))

  with _get_shared_stream(args, raw_destination_url) as shared_stream:
    task_iterator = copy_task_iterator.CopyTaskIterator(
        source_expansion_iterator,
        args.destination,
        custom_md5_digest=args.content_md5,
        delete_source=delete_source,
        do_not_decompress=args.do_not_decompress,
        force_daisy_chain=args.daisy_chain,
        print_created_message=args.print_created_message,
        shared_stream=shared_stream,
        skip_unsupported=args.skip_unsupported,
        task_status_queue=task_status_queue,
        user_request_args=user_request_args,
    )

    return task_executor.execute_tasks(
        task_iterator,
        parallelizable=parallelizable,
        task_status_queue=task_status_queue,
        progress_manager_args=task_status.ProgressManagerArgs(
            task_status.IncrementType.FILES_AND_BYTES,
            manifest_path=user_request_args.manifest_path,
        ),
        continue_on_error=args.continue_on_error,
    )


def _get_managed_folder_iterator(args, url_found_match_tracker):
  return name_expansion.NameExpansionIterator(
      args.source,
      managed_folder_setting=(
          folder_util.ManagedFolderSetting.LIST_WITHOUT_OBJECTS
      ),
      raise_error_for_unmatched_urls=False,
      recursion_requested=name_expansion.RecursionSetting.YES,
      url_found_match_tracker=url_found_match_tracker,
  )


def run_cp(args, delete_source=False):
  """Runs implementation of cp surface with tweaks for similar commands."""
  raw_destination_url = storage_url.storage_url_from_string(args.destination)
  _validate_args(args, raw_destination_url)
  encryption_util.initialize_key_store(args)

  url_found_match_tracker = collections.OrderedDict()

  # TODO(b/304524534): Replace with args.include_managed_folders.
  if getattr(args, 'include_managed_folders', False):
    source_expansion_iterator = _get_managed_folder_iterator(
        args, url_found_match_tracker
    )
    exit_code = _execute_copy_tasks(
        args=args,
        delete_source=False,
        parallelizable=False,
        raw_destination_url=raw_destination_url,
        source_expansion_iterator=source_expansion_iterator,
    )
    if exit_code:
      # An error occurred setting up managed folders in the destination, so we
      # exit out early, as managed folders regulate permissions and we do not
      # want to copy to a location that is incorrectly configured.
      return exit_code

  raw_source_string_iterator = (
      plurality_checkable_iterator.PluralityCheckableIterator(
          stdin_iterator.get_urls_iterable(
              args.source, args.read_paths_from_stdin
          )
      )
  )
  first_source_url = storage_url.storage_url_from_string(
      raw_source_string_iterator.peek()
  )
  parallelizable = _is_parallelizable(
      args, raw_destination_url, first_source_url
  )

  if args.preserve_acl:
    fields_scope = cloud_api.FieldsScope.FULL
  else:
    fields_scope = cloud_api.FieldsScope.NO_ACL

  source_expansion_iterator = name_expansion.NameExpansionIterator(
      raw_source_string_iterator,
      fields_scope=fields_scope,
      ignore_symlinks=args.ignore_symlinks,
      managed_folder_setting=folder_util.ManagedFolderSetting.DO_NOT_LIST,
      object_state=flags.get_object_state_from_flags(args),
      preserve_symlinks=args.preserve_symlinks,
      recursion_requested=name_expansion.RecursionSetting.YES
      if args.recursive
      else name_expansion.RecursionSetting.NO_WITH_WARNING,
      url_found_match_tracker=url_found_match_tracker,
  )
  exit_code = _execute_copy_tasks(
      args=args,
      delete_source=delete_source,
      parallelizable=parallelizable,
      raw_destination_url=raw_destination_url,
      source_expansion_iterator=source_expansion_iterator,
  )

  if (
      delete_source
      # TODO(b/304524534): Replace with args.include_managed_folders.
      and getattr(args, 'include_managed_folders', False)
  ):
    managed_folder_expansion_iterator = name_expansion.NameExpansionIterator(
        args.source,
        managed_folder_setting=folder_util.ManagedFolderSetting.LIST_WITHOUT_OBJECTS,
        raise_error_for_unmatched_urls=False,
        recursion_requested=name_expansion.RecursionSetting.YES,
        url_found_match_tracker=url_found_match_tracker,
    )
    exit_code = rm_command_util.remove_managed_folders(
        args,
        managed_folder_expansion_iterator,
        task_graph_executor.multiprocessing_context.Queue(),
    )

  return exit_code
