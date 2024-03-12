# -*- coding: utf-8 -*- #
# Copyright 2015 Google LLC. All Rights Reserved.
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

"""Script for reporting gcloud metrics."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os
import pickle
import sys

# This file is unique because it is executed as a separate process on metrics
# teardown. Because of this, googlecloudsdk.core is on the Python Path (because
# the directory of the main script is always first on the Path). This happens
# not to matter on Python2, but on Python3, there is a module named http.client
# that is used by httplib2. When core is on the path, our http.py shadows this
# module and the import fails. On Python2, this module doesn't exist so we just
# hadn't hit this issue. Here, we remove the script's directory from the Path
# because we never want to import anything from here as an absolute import (on
# either Python2 or Python3).
sys.path.pop(0)

# pylint: disable=g-import-not-at-top
from googlecloudsdk.core import argv_utils
from googlecloudsdk.core.util import files

try:
  from googlecloudsdk.core import requests
except ImportError:
  # Do nothing if we can't import the lib.
  sys.exit(0)

# If outgoing packets are getting dropped, httplib2 will not respond
# indefinitely while waiting for a response.
TIMEOUT_IN_SEC = 10


def ReportMetrics(metrics_file_path):
  """Sends the specified anonymous usage event to the given analytics endpoint.

  Args:
      metrics_file_path: str, File with pickled metrics (list of tuples).
  """
  with files.BinaryFileReader(metrics_file_path) as metrics_file:
    metrics = pickle.load(metrics_file)
  os.remove(metrics_file_path)

  session = requests.Session()

  for metric in metrics:
    session.request(metric[1], metric[0], data=metric[2], headers=metric[3],
                    timeout=TIMEOUT_IN_SEC)

if __name__ == '__main__':
  try:
    ReportMetrics(argv_utils.GetDecodedArgv()[1])
  # pylint: disable=bare-except, Never fail or output a stacktrace here.
  except:
    pass
