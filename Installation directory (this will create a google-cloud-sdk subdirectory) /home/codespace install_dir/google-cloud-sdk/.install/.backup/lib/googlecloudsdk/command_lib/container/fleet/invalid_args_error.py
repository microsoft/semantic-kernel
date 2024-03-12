# -*- coding: utf-8 -*- #
# Copyright 2023 Google LLC. All Rights Reserved.
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
"""Invalid args error exception class used in creating errors for util files."""

from googlecloudsdk.core import exceptions

INVALID_ARGS_USER_MESSAGE = (
    'Please specify the --users in the correct format:'
    '"foo@example.com" or "principal://iam.googleapis.com/locations/global/'
    'workforcePools/pool/subject/user".'
)
INVALID_ARGS_GROUP_MESSAGE = (
    'Please specify the --groups in the correct format:'
    '"group@example.com" or "principalSet://iam.googleapis.com/locations/global'
    '/workforcePools/pool/group/group1".'
)


class InvalidArgsError(exceptions.Error):

  def __init__(self, error_message):
    message = '{}'.format(error_message)
    super(InvalidArgsError, self).__init__(message)
