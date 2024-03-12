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

"""Factory for AuthenticationConfig message."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals


class AuthenticationConfigFactory(object):
  """Factory for AuthenticationConfig message.

  Add arguments related to AuthenticationConfig to argument parser and create
  AuthenticationConfig message from parsed arguments.
  """

  def __init__(self, dataproc):
    """Factory for AuthenticationConfig message.

    Args:
      dataproc: An api_lib.dataproc.Dataproc instance.
    """
    self.dataproc = dataproc

  def GetMessage(self, args):
    """Builds an AuthenticationConfig message instance.

    Args:
      args: Parsed arguments.

    Returns:
      AuthenticationConfig: An AuthenticationConfig message instance. Returns
      none if all fields are None.
    """
    kwargs = {}

    if getattr(args, 'enable_credentials_injection', False):
      kwargs['authenticationType'] = (
          self.dataproc.messages.AuthenticationConfig.AuthenticationTypeValueValuesEnum(
              'CREDENTIALS_INJECTION'
          )
      )

    if not kwargs:
      return None

    return self.dataproc.messages.AuthenticationConfig(**kwargs)
