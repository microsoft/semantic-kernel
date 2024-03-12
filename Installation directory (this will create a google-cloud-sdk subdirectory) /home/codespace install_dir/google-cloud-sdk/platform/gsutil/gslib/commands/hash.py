# -*- coding: utf-8 -*-
# Copyright 2014 Google Inc. All Rights Reserved.
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
"""Implementation of hash command for calculating hashes of local files."""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals

import logging
import os
import time

import crcmod
import six

from gslib.command import Command
from gslib.command_argument import CommandArgument
from gslib.cs_api_map import ApiSelector
from gslib.exception import CommandException
from gslib.progress_callback import FileProgressCallbackHandler
from gslib.progress_callback import ProgressCallbackWithTimeout
from gslib.storage_url import StorageUrlFromString
from gslib.thread_message import FileMessage
from gslib.thread_message import FinalMessage
from gslib.utils import boto_util
from gslib.utils import constants
from gslib.utils import hashing_helper
from gslib.utils import parallelism_framework_util
from gslib.utils.shim_util import GcloudStorageFlag
from gslib.utils.shim_util import GcloudStorageMap
from gslib.utils import shim_util

_PutToQueueWithTimeout = parallelism_framework_util.PutToQueueWithTimeout

_SYNOPSIS = """
  gsutil hash [-c] [-h] [-m] filename...
"""

_DETAILED_HELP_TEXT = ("""
<B>SYNOPSIS</B>
""" + _SYNOPSIS + """


<B>DESCRIPTION</B>
  Calculate hashes on local files, which can be used to compare with
  ``gsutil ls -L`` output. If a specific hash option is not provided, this
  command calculates all gsutil-supported hashes for the files.

  Note that gsutil automatically performs hash validation when uploading or
  downloading files, so this command is only needed if you want to write a
  script that separately checks the hash.

  If you calculate a CRC32c hash for files without a precompiled crcmod
  installation, hashing will be very slow. See "gsutil help crcmod" for details.

<B>OPTIONS</B>
  -c          Calculate a CRC32c hash for the specified files.

  -h          Output hashes in hex format. By default, gsutil uses base64.

  -m          Calculate a MD5 hash for the specified files.
""")

_GCLOUD_FORMAT_STRING = (
    '--format=' + 'value[separator="",terminator=""](' + 'digest_format.sub("' +
    shim_util.get_format_flag_caret() + '", "Hashes ["),' + 'url.sub("' +
    shim_util.get_format_flag_caret() + '", "] for ").sub("$", ":^\\^n"),' +
    'md5_hash.yesno(yes="\tHash (md5):\t\t", no=""),' +
    'md5_hash.yesno(no=""),' + 'md5_hash.yesno(yes="NEWLINE", no="")' +
    '.sub("NEWLINE", "' + shim_util.get_format_flag_newline() + '"),' +
    'crc32c_hash.yesno(yes="\tHash (crc32c):\t\t", no=""),' +
    'crc32c_hash.yesno(no=""),' + 'crc32c_hash.yesno(yes="NEWLINE", no="")' +
    '.sub("NEWLINE", "' + shim_util.get_format_flag_newline() + '")' + ')')


class HashCommand(Command):
  """Implementation of gsutil hash command."""

  # Command specification. See base class for documentation.
  command_spec = Command.CreateCommandSpec(
      'hash',
      command_name_aliases=[],
      usage_synopsis=_SYNOPSIS,
      min_args=1,
      max_args=constants.NO_MAX,
      supported_sub_args='chm',
      file_url_ok=True,
      provider_url_ok=False,
      urls_start_arg=0,
      gs_api_support=[ApiSelector.JSON],
      gs_default_api=ApiSelector.JSON,
      argparse_arguments=[CommandArgument.MakeZeroOrMoreFileURLsArgument()])
  # Help specification. See help_provider.py for documentation.
  help_spec = Command.HelpSpec(
      help_name='hash',
      help_name_aliases=['checksum'],
      help_type='command_help',
      help_one_line_summary='Calculate file hashes',
      help_text=_DETAILED_HELP_TEXT,
      subcommand_help_text={},
  )

  def get_gcloud_storage_args(self):
    gcloud_storage_map = GcloudStorageMap(
        gcloud_command=[
            'storage',
            'hash',
            _GCLOUD_FORMAT_STRING,
        ],
        flag_map={
            '-h': GcloudStorageFlag('--hex'),
            '-c': None,
            '-m': None,
        },
    )
    args_set = set(self.args + [flag for flag, _ in self.sub_opts])
    if '-c' in args_set and '-m' not in args_set:
      gcloud_storage_map.gcloud_command += ['--skip-md5']
    elif '-m' in args_set and '-c' not in args_set:
      gcloud_storage_map.gcloud_command += ['--skip-crc32c']

    return super().get_gcloud_storage_args(gcloud_storage_map)

  @classmethod
  def _ParseOpts(cls, sub_opts, logger):
    """Returns behavior variables based on input options.

    Args:
      sub_opts: getopt sub-arguments for the command.
      logger: logging.Logger for the command.

    Returns:
      Tuple of
      calc_crc32c: Boolean, if True, command should calculate a CRC32c checksum.
      calc_md5: Boolean, if True, command should calculate an MD5 hash.
      format_func: Function used for formatting the hash in the desired format.
      cloud_format_func: Function used for formatting the hash in the desired
                         format.
      output_format: String describing the hash output format.
    """
    calc_crc32c = False
    calc_md5 = False
    format_func = (
        lambda digest: hashing_helper.Base64EncodeHash(digest.hexdigest()))
    cloud_format_func = lambda digest: digest
    found_hash_option = False
    output_format = 'base64'

    if sub_opts:
      for o, unused_a in sub_opts:
        if o == '-c':
          calc_crc32c = True
          found_hash_option = True
        elif o == '-h':
          output_format = 'hex'
          format_func = lambda digest: digest.hexdigest()
          cloud_format_func = lambda digest: (
              hashing_helper.Base64ToHexHash(digest).decode('ascii')
          )  # yapf: disable
        elif o == '-m':
          calc_md5 = True
          found_hash_option = True

    if not found_hash_option:
      calc_crc32c = True
      calc_md5 = True

    if calc_crc32c and not boto_util.UsingCrcmodExtension():
      logger.warn(hashing_helper.SLOW_CRCMOD_WARNING)

    return calc_crc32c, calc_md5, format_func, cloud_format_func, output_format

  def _GetHashClassesFromArgs(self, calc_crc32c, calc_md5):
    """Constructs the dictionary of hashes to compute based on the arguments.

    Args:
      calc_crc32c: If True, CRC32c should be included.
      calc_md5: If True, MD5 should be included.

    Returns:
      Dictionary of {string: hash digester}, where string the name of the
          digester algorithm.
    """
    hash_dict = {}
    if calc_crc32c:
      hash_dict['crc32c'] = crcmod.predefined.Crc('crc-32c')
    if calc_md5:
      hash_dict['md5'] = hashing_helper.GetMd5()
    return hash_dict

  def RunCommand(self):
    """Command entry point for the hash command."""
    (calc_crc32c, calc_md5, format_func, cloud_format_func,
     output_format) = (self._ParseOpts(self.sub_opts, self.logger))

    matched_one = False
    for url_str in self.args:
      for file_ref in self.WildcardIterator(url_str).IterObjects(
          bucket_listing_fields=[
              'crc32c',
              'customerEncryption',
              'md5Hash',
              'size',
          ]):
        matched_one = True
        url = StorageUrlFromString(url_str)
        file_name = file_ref.storage_url.object_name
        if StorageUrlFromString(url_str).IsFileUrl():
          file_size = os.path.getsize(file_name)
          self.gsutil_api.status_queue.put(
              FileMessage(url,
                          None,
                          time.time(),
                          size=file_size,
                          finished=False,
                          message_type=FileMessage.FILE_HASH))
          callback_processor = ProgressCallbackWithTimeout(
              file_size,
              FileProgressCallbackHandler(self.gsutil_api.status_queue,
                                          src_url=StorageUrlFromString(url_str),
                                          operation_name='Hashing').call)
          hash_dict = self._GetHashClassesFromArgs(calc_crc32c, calc_md5)
          with open(file_name, 'rb') as fp:
            hashing_helper.CalculateHashesFromContents(
                fp, hash_dict, callback_processor=callback_processor)
          self.gsutil_api.status_queue.put(
              FileMessage(url,
                          None,
                          time.time(),
                          size=file_size,
                          finished=True,
                          message_type=FileMessage.FILE_HASH))
        else:
          hash_dict = {}
          obj_metadata = file_ref.root_object
          file_size = obj_metadata.size
          md5_present = obj_metadata.md5Hash is not None
          crc32c_present = obj_metadata.crc32c is not None
          if not md5_present and not crc32c_present:
            logging.getLogger().warn('No hashes present for %s', url_str)
            continue
          if md5_present:
            hash_dict['md5'] = obj_metadata.md5Hash
          if crc32c_present:
            hash_dict['crc32c'] = obj_metadata.crc32c
        print('Hashes [%s] for %s:' % (output_format, file_name))
        for name, digest in six.iteritems(hash_dict):
          print('\tHash (%s):\t\t%s' % (name,
                                        (format_func(digest) if url.IsFileUrl()
                                         else cloud_format_func(digest))))

    if not matched_one:
      raise CommandException('No files matched')
    _PutToQueueWithTimeout(self.gsutil_api.status_queue,
                           FinalMessage(time.time()))
    return 0
