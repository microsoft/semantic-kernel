# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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

"""A library containing resource args used by Transcoder commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import exceptions as calliope_exceptions
from googlecloudsdk.core.util import files


def GetContent(file_path, content):
  """Get job or template data."""

  if content is not None:
    return content

  if file_path is not None:
    try:
      return files.ReadFileContents(file_path)
    except files.Error as e:
      raise calliope_exceptions.BadFileException('Failed to read {}, {}'
                                                 .format(file_path, e))

  return None


def ValidateCreateJobArguments(args):
  """Valid parameters for create job command."""

  missing = None
  # when using (default)template to create job, input/output uri are required
  if args.file is None and args.json is None:
    input_uri = args.input_uri
    output_uri = args.output_uri

    if input_uri is None:
      missing = 'input-uri'
    elif output_uri is None:
      missing = 'output-uri'

  if missing is not None:
    raise calliope_exceptions.RequiredArgumentException(
        '--{}'.format(missing),
        '{} is required when using template to create job'.format(missing))
