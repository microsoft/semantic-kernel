# Copyright 2017 Stripe Inc. All Rights Reserved.
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
"""This package sets up the Python logging system."""



import logging
import sys


# Based on glog.
FORMAT = ('%(shortlevel)s%(asctime)s.%(time_millis)06d %(process_str)s '
          '%(filename)s:%(lineno)d] %(message)s')

# Based on glog.
TIMESTAMP_FORMAT = '%m%d %H:%M:%S'


def DefineCommandLineArgs(argparser):
  argparser.add_argument(
      '--stderrthreshold',
      action='store',
      help=('Write log events at or above this level to stderr.'))


def Init(args=None):
  handler = logging.StreamHandler(stream=sys.stderr)
  handler.setFormatter(Formatter())
  logging.root.addHandler(handler)
  if args is not None:
    if args.stderrthreshold is not None:
      logging.root.setLevel(args.stderrthreshold)


class Formatter(logging.Formatter):

  def __init__(self):
    super(Formatter, self).__init__(fmt=FORMAT, datefmt=TIMESTAMP_FORMAT)

  def format(self, record):
    # Injecting fields into the record seems to be fine, it's how the upstream
    # logging.Formatter adds timestamps and such.
    if record.levelname == 'CRITICAL':
      record.shortlevel = 'F'  # FATAL
    else:
      record.shortlevel = record.levelname[0]
    record.time_millis = (record.created - int(record.created)) * 1000000
    if record.process is None:
      record.process_str = '???????'
    else:
      record.process_str = '% 7d' % (record.process,)
    return super(Formatter, self).format(record)
