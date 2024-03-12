# -*- coding: utf-8 -*-
# Copyright 2013 Google Inc. All Rights Reserved.
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
"""Additional help about the shim for running gcloud storage."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from gslib.help_provider import HelpProvider

_DETAILED_HELP_TEXT = ("""
<B>OVERVIEW</B>
  Cloud SDK includes a new CLI, gcloud storage, that can be considerably faster
  than gsutil when performing uploads and downloads with less parameter
  tweaking. This new CLI has a syntax and command structure that is familiar to
  gsutil users but is fundamentally different in many important ways. To ease
  transition to this new CLI, gsutil provides a shim that translates your gsutil
  commands to gcloud storage commands if an equivalent exists, and falls back to
  gsutil's usual behavior if an equivalent does not exist.


<B>TO ENABLE</B>
  Set ``use_gcloud_storage=True`` in the ``.boto`` config file under the
  ``[GSUtil]`` section:

    [GSUtil]
    use_gcloud_storage=True

  You can also set the flag for individual commands using the top-level ``-o``
  flag:

    gsutil -o "GSUtil:use_gcloud_storage=True" -m cp -p file gs://bucket/obj

<B>AVAILABLE COMMANDS</B>
  The gcloud storage CLI only supports a subset of gsutil commands. What follows
  is a list of commands supported by the shim with any differences in behavior
  noted.

  acl
  ------------------------

  - The ``ch`` subcommand is not supported.

  autoclass
  ------------------------

  - Works as expected.

  bucketpolicyonly
  ------------------------

  - Works as expected.

  cat
  ------------------------

  - Prints object data for a second object even if the first object is invalid.

  compose
  ------------------------

  - Works as expected.

  cors
  ------------------------

  - ``get`` subcommand prints "[]" instead of "gs://[bucket name] has no CORS
    configuration".

  cp
  ------------------------

  - Copies a second object even if the first object is invalid.
  - Does not support file to file copies.
  - Supports copying objects cloud-to-cloud with trailing slashes in the name.
  - The all-version flag (``-A``) silently enables sequential execution rather
    than raising an error.

  defacl
  ------------------------

  - The ``ch`` subcommand is not supported.

  defstorageclass
  ------------------------

  - Works as expected.

  hash
  ------------------------

  - In gsutil, the ``-m`` and ``-c`` flags that affect which hashes are displayed
    are ignored for cloud objects. This behavior is fixed for the shim and gcloud
    storage.

  iam
  ------------------------

  - The ``ch`` subcommand is not supported.
  - The ``-f`` flag will continue on any error, not just API errors.


  kms
  ------------------------

  - The authorize subcommand returns informational messages in a different
    format.
  - The encryption subcommand returns informational messages in a different
    format.

  labels
  ------------------------
  - ``get`` subcommand prints "[]" instead of "gs://[bucket name] has no labels
    configuration."

  lifecycle
  ------------------------

  - Works as expected.

  logging
  ------------------------

  - The get subcommand has different JSON spacing and doesn't print an
    informational message if no configuration is found.

  ls
  ------------------------

  - `ls -L` output uses spaces instead of tabs.

  mb
  ------------------------
  - Works as expected.

  mv
  ------------------------

  - See notes on cp.

  notification
  ------------------------

  - The list subcommand prints configuration information as YAML.
  - The delete subcommand offers progress tracking and parallelization.

  pap
  ------------------------

  - Works as expected.

  rb
  ------------------------

  - Works as expected.

  requesterpays
  ------------------------

  - Works as expected.

  rewrite
  ------------------------

  - The -k flag does not throw an error if called without a new key. In both the
    shim and unshimmed cases, the old key is maintained.

  rm
  ------------------------

  - ``$folder$`` delete markers are not supported.

  rpo
  ------------------------

  - Works as expected.

  setmeta
  ------------------------

  - Does not throw an error if no headers are changed.

  stat
  ------------------------

  - Includes a field "Storage class update time:" which may throw off tabbing.

  ubla
  ------------------------

  - Works as expected.

  versioning
  ------------------------

  - Works as expected.

  web
  ------------------------

  - The get subcommand has different JSON spacing and doesn't print an
    informational message if no configuration is found.



<B>BOTO CONFIGURATION</B>
  Configuration found in the boto file is mapped 1:1 to gcloud environment
  variables where appropriate.

  [Credentials]
  ------------------------

  - aws_access_key_id: AWS_ACCESS_KEY_ID
  - aws_secret_access_key: AWS_SECRET_ACCESS_KEY
  - use_client_certificate: CLOUDSDK_CONTEXT_AWARE_USE_CLIENT_CERTIFICATE

  [Boto]
  ------------------------

  - proxy: CLOUDSDK_PROXY_ADDRESS
  - proxy_type: CLOUDSDK_PROXY_TYPE
  - proxy_port: CLOUDSDK_PROXY_PORT
  - proxy_user: CLOUDSDK_PROXY_USERNAME
  - proxy_pass: CLOUDSDK_PROXY_PASSWORD
  - proxy_rdns: CLOUDSDK_PROXY_RDNS
  - http_socket_timeout: CLOUDSDK_CORE_HTTP_TIMEOUT
  - ca_certificates_file: CLOUDSDK_CORE_CUSTOM_CA_CERTS_FILE
  - max_retry_delay: CLOUDSDK_STORAGE_BASE_RETRY_DELAY
  - num_retries: CLOUDSDK_STORAGE_MAX_RETRIES

  [GSUtil]
  ------------------------

  - check_hashes: CLOUDSDK_STORAGE_CHECK_HASHES
  - default_project_id: CLOUDSDK_CORE_PROJECT
  - disable_analytics_prompt: CLOUDSDK_CORE_DISABLE_USAGE_REPORTING
  - use_magicfile: CLOUDSDK_STORAGE_USE_MAGICFILE
  - parallel_composite_upload_threshold: CLOUDSDK_STORAGE_PARALLEL_COMPOSITE_UPLOAD_THRESHOLD
  - resumable_threshold: CLOUDSDK_STORAGE_RESUMABLE_THRESHOLD

  [OAuth2]
  ------------------------

  - client_id: CLOUDSDK_AUTH_CLIENT_ID
  - client_secret: CLOUDSDK_AUTH_CLIENT_SECRET
  - provider_authorization_uri: CLOUDSDK_AUTH_AUTH_HOST
  - provider_token_uri: CLOUDSDK_AUTH_TOKEN_HOST

<B>GENERAL COMPATIBILITY NOTES</B>

  - Due to its compatibility across all major platforms, multiprocessing is
    enabled for all commands by default (equivalent to the -m option always
    being included in gsutil).
  - A sequence of asterisks greater than 2 (i.e. ``***``) are always treated as
    a single asterisk.
  - Unlike gsutil, gcloud is not designed to be used in parallel invocations,
    and doing so (i.e. running the shim from 2 terminals at once) can lead to
    unpredictable behavior.
  - Assuming a bucket contains an object ``gs://bucket/nested/foo.txt``,
    gsutil's wildcard iterator will match ``foo.txt`` given a URL like
    ``gs://bucket/*/nested/*``. The shim will not match ``foo.txt`` given the
    same URL.
  - This will be updated as new commands are supported by both gcloud storage
    and the shim.
  - If Unicode is having issues, try setting the environment variable
    ``PYTHONUTF8`` to ``1``. Specifically, this may help on the Windows
    command-line (CMD).

""")


class CommandOptions(HelpProvider):
  """Additional help about the shim for running gcloud storage."""

  # Help specification. See help_provider.py for documentation.
  help_spec = HelpProvider.HelpSpec(
      help_name='shim',
      help_name_aliases=['gcloudstorage', 'gcloud storage'],
      help_type='additional_help',
      help_one_line_summary='Shim for Running gcloud storage',
      help_text=_DETAILED_HELP_TEXT,
      subcommand_help_text={},
  )
