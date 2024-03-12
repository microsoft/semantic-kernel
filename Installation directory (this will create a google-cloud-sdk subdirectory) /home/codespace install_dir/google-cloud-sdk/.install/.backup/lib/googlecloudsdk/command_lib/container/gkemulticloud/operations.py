# -*- coding: utf-8 -*- #
# Copyright 2021 Google LLC. All Rights Reserved.
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
"""Utilities for operations command groups."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

_OPERATION_TABLE_FORMAT = """\
    table(
        name.basename():label=OPERATION_NAME,
        name.segment(3):label=LOCATION,
        metadata.target.basename(),
        metadata.verb,
        done.yesno(yes='DONE', no='RUNNING'):label=STATUS,
        metadata.createTime.date():sort=1,
        duration(start=metadata.createTime,end=metadata.endTime,precision=0,calendar=false).slice(2:).join("").yesno(no="<1S"):label=DURATION
    )"""


def AddFilter(args, noun):
  predicate = 'metadata.target ~ projects/\\d+/locations/.+/{}*'.format(noun)
  if args.filter:
    args.filter = predicate + ' AND ' + args.filter
  else:
    args.filter = predicate


def AddFormat(parser):
  parser.display_info.AddFormat(_OPERATION_TABLE_FORMAT)
