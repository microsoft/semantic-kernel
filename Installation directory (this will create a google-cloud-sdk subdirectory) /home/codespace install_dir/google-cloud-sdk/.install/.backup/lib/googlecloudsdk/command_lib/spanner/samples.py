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
"""Spanner samples API helper."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import collections
import os
from googlecloudsdk.api_lib.spanner import databases
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import execution_utils
from googlecloudsdk.core import log
from googlecloudsdk.core.util import files

# TODO(b/230344467): Better default samples dir
_SAMPLES_DEFAULT_DIR_NAME = '.gcloud-spanner-samples'
_SAMPLES_DEFAULT_DIR_PATH = os.path.join(
    os.path.expanduser('~'), _SAMPLES_DEFAULT_DIR_NAME)
SAMPLES_DIR_PATH = os.getenv('GCLOUD_SPANNER_SAMPLES_HOME',
                             _SAMPLES_DEFAULT_DIR_PATH)

_BIN_RELPATH = 'bin'
SAMPLES_BIN_PATH = os.path.join(SAMPLES_DIR_PATH, _BIN_RELPATH)
_LOG_RELPATH = 'log'
SAMPLES_LOG_PATH = os.path.join(SAMPLES_DIR_PATH, _LOG_RELPATH)
_ETC_RELPATH = 'etc'
SAMPLES_ETC_PATH = os.path.join(SAMPLES_DIR_PATH, _ETC_RELPATH)

# TODO(b/228633873): Replace with prod bucket
GCS_BUCKET = 'gs://cloud-spanner-samples'

FINANCE_APP_NAME = 'finance'
FINANCE_PG_APP_NAME = 'finance-pg'

AppAttrs = collections.namedtuple('AppAttrs', [
    'db_id',  # Name of the sample app DB
    'bin_path',  # Relative path for sample app bin files
    'etc_path',  # Relative path for schema, data, and other files
    'gcs_prefix',  # Prefix for sample app files in GCS_BUCKET
    'schema_file',  # Schema filename (in GCS and locally)
    'backend_bin',  # Backend/server bin filename
    'workload_bin',  # Workload bin filename
    'database_dialect'  # The database dialect used in this sample
])

APPS = {
    FINANCE_APP_NAME:
        AppAttrs(
            db_id='finance-db',
            bin_path='finance',
            etc_path='finance',
            schema_file='finance-schema.sdl',
            gcs_prefix='finance',
            backend_bin='server-1.0-SNAPSHOT-jar-with-dependencies.jar',
            workload_bin='workload-1.0-SNAPSHOT-jar-with-dependencies.jar',
            database_dialect=databases.DATABASE_DIALECT_GOOGLESQL,
        ),
    FINANCE_PG_APP_NAME:
        AppAttrs(
            db_id='finance-pg-db',
            bin_path='finance-pg',
            etc_path='finance-pg',
            schema_file='finance-schema-pg.sdl',
            gcs_prefix='finance',
            backend_bin='server-1.0-SNAPSHOT-jar-with-dependencies.jar',
            workload_bin='workload-1.0-SNAPSHOT-jar-with-dependencies.jar',
            database_dialect=databases.DATABASE_DIALECT_POSTGRESQL,
        )
}

_GCS_BIN_PREFIX = 'bin'
_GCS_SCHEMA_PREFIX = 'schema'


class SpannerSamplesError(exceptions.Error):
  """User error running Cloud Spanner sample app commands."""


def check_appname(appname):
  """Raise if the given sample app doesn't exist.

  Args:
    appname: str, Name of the sample app.

  Raises:
    ValueError: if the given sample app doesn't exist.
  """
  if appname not in APPS:
    raise ValueError("Unknown sample app '{}'".format(appname))


def get_db_id_for_app(appname):
  """Get the database ID for the given sample app.

  Args:
    appname: str, Name of the sample app.

  Returns:
    str, The database ID, e.g. "finance-db".

  Raises:
    ValueError: if the given sample app doesn't exist.
  """
  check_appname(appname)
  return APPS[appname].db_id


def get_local_schema_path(appname):
  """Get the local path of the schema file for the given sample app.

  Note that the file and parent dirs may not exist.

  Args:
    appname: str, Name of the sample app.

  Returns:
    str, The local path of the schema file.

  Raises:
    ValueError: if the given sample app doesn't exist.
  """
  check_appname(appname)
  app_attrs = APPS[appname]
  return os.path.join(SAMPLES_ETC_PATH, app_attrs.etc_path,
                      app_attrs.schema_file)


def get_local_bin_path(appname):
  """Get the local path to binaries for the given sample app.

  This typically includes server and workload binaries and any required
  dependencies. Note that the path may not exist.

  Args:
    appname: str, Name of the sample app.

  Returns:
    str, The local path of the sample app binaries.

  Raises:
    ValueError: if the given sample app doesn't exist.
  """
  check_appname(appname)
  return os.path.join(SAMPLES_BIN_PATH, APPS[appname].bin_path)


def get_gcs_schema_name(appname):
  """Get the GCS file path for the schema for the given sample app.

  Doesn't include the bucket name. Use to download the sample app schema file
  from GCS.

  Args:
    appname: str, Name of the sample app.

  Returns:
    str, The sample app schema GCS file path.

  Raises:
    ValueError: if the given sample app doesn't exist.
  """
  check_appname(appname)
  app_attrs = APPS[appname]
  return '/'.join(
      [app_attrs.gcs_prefix, _GCS_SCHEMA_PREFIX, app_attrs.schema_file])


def get_gcs_bin_prefix(appname):
  """Get the GCS prefix for binaries for the given sample app.

  Doesn't include the bucket name. Different sample apps have different
  numbers and types of binaries, list the bucket contents before downloading.

  Args:
    appname: str, Name of the sample app.

  Returns:
    str, The sample app binaries GCS prefix.

  Raises:
    ValueError: if the given sample app doesn't exist.
  """
  check_appname(appname)
  return '/'.join([APPS[appname].gcs_prefix, _GCS_BIN_PREFIX, ''])


def get_database_dialect(appname):
  """Get the database dialect for the given sample app.

  Args:
    appname: str, Name of the sample app.

  Returns:
    str, The database dialect.

  Raises:
    ValueError: if the given sample app doesn't exist.
  """
  check_appname(appname)
  return APPS[appname].database_dialect


def run_proc(args, capture_logs_fn=None):
  """Wrapper for execution_utils.Subprocess that optionally captures logs.

  Args:
    args: [str], The arguments to execute.  The first argument is the command.
    capture_logs_fn: str, If set, save logs to the specified filename.

  Returns:
    subprocess.Popen or execution_utils.SubprocessTimeoutWrapper, The running
      subprocess.
  """
  if capture_logs_fn:
    logfile = files.FileWriter(capture_logs_fn, append=True, create_path=True)
    log.status.Print('Writing logs to {}'.format(capture_logs_fn))
    popen_args = dict(stdout=logfile, stderr=logfile)
  else:
    popen_args = {}
  return execution_utils.Subprocess(args, **popen_args)

