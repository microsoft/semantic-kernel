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
"""Flags for GCE Cloud CDN Signed URL support."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import arg_parsers


def AddCdnSignedUrlKeyName(parser, required=False):
  """Adds the Cloud CDN Signed URL key name argument to the argparse."""
  parser.add_argument(
      '--key-name',
      required=required,
      help='Name of the Cloud CDN Signed URL key.')


def AddCdnSignedUrlKeyFile(parser, required=False):
  """Adds the Cloud CDN Signed URL key file argument to the argparse."""
  parser.add_argument(
      '--key-file',
      required=required,
      metavar='LOCAL_FILE_PATH',
      help="""\
      The file containing the RFC 4648 Section 5 base64url encoded 128-bit
      secret key for Cloud CDN Signed URL. It is vital that the key is
      strongly random. One way to generate such a key is with the following
      command:

          head -c 16 /dev/random | base64 | tr +/ -_ > [KEY_FILE_NAME]

      """)


def AddSignedUrlCacheMaxAge(
    parser,
    required=False,
    unspecified_help=' If unspecified, the default value is 3600s.'):
  """Adds the Cloud CDN Signed URL cache max age argument to the argparse."""
  parser.add_argument(
      '--signed-url-cache-max-age',
      required=required,
      type=arg_parsers.Duration(),
      help="""\
      The amount of time up to which the response to a signed URL request
      will be cached in the CDN. After this time period, the Signed URL will
      be revalidated before being served. Cloud CDN will internally act as
      though all responses from this backend had a
      `Cache-Control: public, max-age=[TTL]` header, regardless of any
      existing Cache-Control header. The actual headers served in responses
      will not be altered.{}

      For example, specifying `12h` will cause the responses to signed URL
      requests to be cached in the CDN up to 12 hours.
      See $ gcloud topic datetimes for information on duration formats.

      This flag only affects signed URL requests.
      """.format(unspecified_help))
