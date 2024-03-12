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

"""Utilities for making requests using a given client and handling errors.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import io

from googlecloudsdk.core.resource import resource_printer


def ExtractErrorMessage(error_details):
  """Extracts error details from an apitools_exceptions.HttpError.

  Args:
    error_details: a python dictionary returned from decoding an error that
        was serialized to json.

  Returns:
    Multiline string containing a detailed error message suitable to show to a
    user.
  """
  error_message = io.StringIO()
  error_message.write('Error Response: [{code}] {message}'.format(
      code=error_details.get('code', 'UNKNOWN'),  # error_details.code is an int
      message=error_details.get('message', '')))

  if 'url' in error_details:
    error_message.write('\n' + error_details['url'])

  if 'details' in error_details:
    error_message.write('\n\nDetails: ')
    resource_printer.Print(
        resources=[error_details['details']],
        print_format='json',
        out=error_message)
  return error_message.getvalue()


