# Copyright 2016 Google Inc. All Rights Reserved.
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
"""Script for reporting metrics."""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals

import logging
import os
import pickle
import random
import string
import sys

_LOG_FILE_BASENAME = 'metrics.log'
# pylint:disable=g-import-not-at-top
try:
  from gslib.utils.boto_util import ConfigureCertsFile
  from gslib.utils.boto_util import GetGsutilStateDir
  from gslib.utils.boto_util import GetNewHttp
  from gslib.utils.system_util import CreateDirIfNeeded
  _LOG_FILE_PARENT_DIR = GetGsutilStateDir()
except:  # pylint: disable=bare-except
  # Some environments import their own version of standard Python libraries
  # which might cause the import of some of our gslib.utils modules to fail
  # (e.g. if httplib2 is missing, etc). Try these alternative definitions in
  # such cases.

  _LOG_FILE_PARENT_DIR = os.path.expanduser(os.path.join('~', '.gsutil'))

  # Some environments don't have the httplib2 functionality we need.
  try:
    import errno
    # Fall back to httplib (no proxy) if we can't import libraries normally.
    from six.moves import http_client

    def GetNewHttp():
      """Returns an httplib-based metrics reporter."""

      class HttplibReporter(object):

        def __init__(self):
          pass

        # pylint: disable=invalid-name
        def request(self, endpoint, method=None, body=None, headers=None):
          # Strip 'https://'
          https_con = http_client.HTTPSConnection(endpoint[8:].split('/')[0])
          https_con.request(method, endpoint, body=body, headers=headers)
          response = https_con.getresponse()
          # Return status like an httplib2 response.
          return ({'status': response.status},)

        # pylint: enable=invalid-name

      return HttplibReporter()

    def ConfigureCertsFile():
      pass

    def CreateDirIfNeeded(dir_path, mode=0o777):
      """See the same-named method in gslib.utils.system_util."""
      if not os.path.exists(dir_path):
        try:
          os.makedirs(dir_path, mode)
        except OSError as e:
          if e.errno != errno.EEXIST:
            raise
  except:  # pylint: disable=bare-except
    sys.exit(0)

LOG_FILE_PATH = os.path.join(_LOG_FILE_PARENT_DIR, _LOG_FILE_BASENAME)


def ReportMetrics(metrics_file_path, log_level, log_file_path=None):
  """Sends the specified anonymous usage event to the given analytics endpoint.

  Args:
      metrics_file_path: str, File with pickled metrics (list of tuples).
      log_level: int, The logging level of gsutil's root logger.
      log_file_path: str, The file that this module should write its logs to.
        This parameter is intended for use by tests that need to evaluate the
        contents of the file at this path.

  """
  logger = logging.getLogger()
  if log_file_path is not None:
    # Use a separate logger so that we don't add another handler to the default
    # module-level logger. This is intended to prevent multiple calls from tests
    # running in parallel from writing output to the same file.
    new_name = '%s.%s' % (logger.name, ''.join(
        random.choice(string.ascii_lowercase) for _ in range(8)))
    logger = logging.getLogger(new_name)

  log_file_path = log_file_path or LOG_FILE_PATH
  log_file_parent_dir = os.path.dirname(log_file_path)
  CreateDirIfNeeded(log_file_parent_dir)
  handler = logging.FileHandler(log_file_path, mode='w')
  logger.addHandler(handler)
  logger.setLevel(log_level)

  with open(metrics_file_path, 'rb') as metrics_file:
    metrics = pickle.load(metrics_file)
  os.remove(metrics_file_path)

  ConfigureCertsFile()
  http = GetNewHttp()

  for metric in metrics:
    try:
      headers = {'User-Agent': metric.user_agent}
      response = http.request(metric.endpoint,
                              method=metric.method,
                              body=metric.body,
                              headers=headers)
      logger.debug(metric)
      logger.debug('RESPONSE: %s', response[0]['status'])
    except Exception as e:  # pylint: disable=broad-except
      logger.debug(e)
