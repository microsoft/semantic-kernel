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

"""Flags and helpers for the compute backend-buckets commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.command_lib.compute import completers as compute_completers
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.util.apis import arg_utils


_GCS_BUCKET_DETAILED_HELP = """\
The name of the Google Cloud Storage bucket to serve from. The storage
        bucket must be in the same project."""

DEFAULT_LIST_FORMAT = """\
    table(
      name,
      bucketName:label=GCS_BUCKET_NAME,
      enableCdn
    )"""


class BackendBucketsCompleter(compute_completers.ListCommandCompleter):

  def __init__(self, **kwargs):
    super(BackendBucketsCompleter, self).__init__(
        collection='compute.backendBuckets',
        list_command='compute backend-buckets list --uri',
        **kwargs)


def BackendBucketArgument(plural=False):
  return compute_flags.ResourceArgument(
      name='backend_bucket_name',
      resource_name='backend bucket',
      plural=plural,
      completer=BackendBucketsCompleter,
      global_collection='compute.backendBuckets')

GCS_BUCKET_ARG = compute_flags.ResourceArgument(
    resource_name='backend bucket',
    completer=BackendBucketsCompleter,
    name='--gcs-bucket-name',
    plural=False,
    required=False,
    global_collection='compute.backendBuckets',
    detailed_help=_GCS_BUCKET_DETAILED_HELP)

REQUIRED_GCS_BUCKET_ARG = compute_flags.ResourceArgument(
    resource_name='backend bucket',
    completer=BackendBucketsCompleter,
    name='--gcs-bucket-name',
    plural=False,
    global_collection='compute.backendBuckets',
    detailed_help=_GCS_BUCKET_DETAILED_HELP)


def BackendBucketArgumentForUrlMap(required=True):
  return compute_flags.ResourceArgument(
      resource_name='backend bucket',
      name='--default-backend-bucket',
      required=required,
      completer=BackendBucketsCompleter,
      global_collection='compute.backendBuckets')


def AddUpdatableArgs(cls, parser, operation_type):
  """Adds top-level backend bucket arguments that can be updated.

  Args:
    cls: type, Class to add backend bucket argument to.
    parser: The argparse parser.
    operation_type: str, operation_type forwarded to AddArgument(...)
  """
  cls.BACKEND_BUCKET_ARG = BackendBucketArgument()
  cls.BACKEND_BUCKET_ARG.AddArgument(parser, operation_type=operation_type)

  parser.add_argument(
      '--description',
      help='An optional, textual description for the backend bucket.')

  parser.add_argument(
      '--enable-cdn',
      action=arg_parsers.StoreTrueFalseAction,
      help="""\
      Enable Cloud CDN for the backend bucket. Cloud CDN can cache HTTP
      responses from a backend bucket at the edge of the network, close to
      users.""")


def AddCacheKeyExtendedCachingArgs(parser):
  """Adds cache key includeHttpHeader and includeNamedCookie flags to the argparse."""
  parser.add_argument(
      '--cache-key-include-http-header',
      type=arg_parsers.ArgList(),
      metavar='HEADER_FIELD_NAME',
      help="""\
      Specifies a comma-separated list of HTTP headers, by field name, to
      include in cache keys. Only the request URL is included in the cache
      key by default.
      """)

  parser.add_argument(
      '--cache-key-query-string-whitelist',
      type=arg_parsers.ArgList(),
      metavar='QUERY_STRING',
      help="""\
      Specifies a comma-separated list of query string parameters to include
      in cache keys. Default parameters are always included. '&' and '=' are
      percent encoded and not treated as delimiters.
      """)


def AddCompressionMode(parser):
  """Add support for --compression-mode flag."""
  return parser.add_argument(
      '--compression-mode',
      choices=['DISABLED', 'AUTOMATIC'],
      type=arg_utils.ChoiceToEnumName,
      help="""\
      Compress text responses using Brotli or gzip compression, based on
      the client's Accept-Encoding header. Two modes are supported:
      AUTOMATIC (recommended) - automatically uses the best compression based
      on the Accept-Encoding header sent by the client. In most cases, this
      will result in Brotli compression being favored.
      DISABLED - disables compression. Existing compressed responses cached
      by Cloud CDN will not be served to clients.
      """)
