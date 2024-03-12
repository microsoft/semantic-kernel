# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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

"""Flags for gcloud ml vision commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import arg_parsers


def AspectRatioType(value):
  """A type function to be used to parse aspect ratios."""
  try:
    return float(value)
  except ValueError:
    parts = value.split(':')
    if len(parts) == 2:
      try:
        return float(parts[0]) / float(parts[1])
      except ValueError:
        pass

    raise arg_parsers.ArgumentTypeError(
        'Each aspect ratio must either be specified as a decimal (ex. 1.333) '
        'or as a ratio of width to height (ex 4:3)')
