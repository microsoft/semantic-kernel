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

"""Some utilities intended for use around apis."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import enum

from googlecloudsdk.core import exceptions


class UnknownAPIError(exceptions.Error):
  """Unable to find API in APIs map."""

  def __init__(self, api_name):
    super(UnknownAPIError, self).__init__(
        'API named [{0}] does not exist in the APIs map'.format(api_name))


class UnknownVersionError(exceptions.Error):
  """Unable to find API version in APIs map."""

  def __init__(self, api_name, api_version):
    super(UnknownVersionError, self).__init__(
        'The [{0}] API does not have version [{1}] in the APIs map'.format(
            api_name, api_version))


class GapicTransport(enum.Enum):
  """Enum options for Gapic Clients."""
  GRPC = 1
  GRPC_ASYNCIO = 2
  REST = 3


# This is the map of API name aliases to actual API names.
# Do not add to this map unless the api definition uses different names for api
# name, endpoint and/or collection names.
# The apis_map keys are aliases and values are actual API names.
# The rest of the Cloud SDK, including
# property sections, and command surfaces should use the API name alias.

# The general rule for this module is: all apis_map lookups should use the real
# API name, and all property lookups should use the alias. Any api_name argument
# expects to receive the name alias (if one exists). The _GetApiNameAndAlias
# helper method can be used to convert it into a (name, alias) tuple.
_API_NAME_ALIASES = {
    'sql': 'sqladmin',
    'transfer': 'storagetransfer',
}
