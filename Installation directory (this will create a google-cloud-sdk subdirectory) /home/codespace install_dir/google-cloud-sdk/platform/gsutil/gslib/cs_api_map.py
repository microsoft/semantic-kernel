# -*- coding: utf-8 -*-
# Copyright 2013 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""API map classes used with the CloudApiDelegator class."""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals

from gslib.boto_translation import BotoTranslation
from gslib.gcs_json_api import GcsJsonApi


class ApiSelector(object):
  """Enum class for API."""
  XML = 'XML'
  JSON = 'JSON'


class ApiMapConstants(object):
  """Enum class for API map entries."""
  API_MAP = 'apiclass'
  SUPPORT_MAP = 'supported'
  DEFAULT_MAP = 'default'


class GsutilApiClassMapFactory(object):
  """Factory for generating gsutil API class maps.

  A valid class map is defined as:
    {
      (key) Provider prefix used in URI strings.
      (value) {
        (key) ApiSelector describing the API format.
        (value) CloudApi child class that implements this API.
      }
    }
  """

  @classmethod
  def GetClassMap(cls):
    """Returns the default gsutil class map."""
    gs_class_map = {
        ApiSelector.XML: BotoTranslation,
        ApiSelector.JSON: GcsJsonApi
    }
    s3_class_map = {
        ApiSelector.XML: BotoTranslation,
    }
    class_map = {
        'gs': gs_class_map,
        's3': s3_class_map,
    }
    return class_map


class GsutilApiMapFactory(object):
  """Factory the generates the default gsutil API map.

    The API map determines which Cloud API implementation is used for a given
    command.  A valid API map is defined as:
    {
      (key) ApiMapConstants.API_MAP : (value) Gsutil API class map (as
          described in GsutilApiClassMapFactory comments).
      (key) ApiMapConstants.SUPPORT_MAP : (value) {
        (key) Provider prefix used in URI strings.
        (value) list of ApiSelectors supported by the command for this provider.
      }
      (key) ApiMapConstants.DEFAULT_MAP : (value) {
        (key) Provider prefix used in URI strings.
        (value) Default ApiSelector for this command and provider.
      }
    }
  """

  @classmethod
  def GetApiMap(cls, gsutil_api_class_map_factory, support_map, default_map):
    """Creates a GsutilApiMap for use by the command from the inputs.

    Args:
      gsutil_api_class_map_factory: Factory defining a GetClassMap() function
                                    adhering to GsutilApiClassMapFactory
                                    semantics.
      support_map: Entries for ApiMapConstants.SUPPORT_MAP as described above.
      default_map: Entries for ApiMapConstants.DEFAULT_MAP as described above.

    Returns:
      GsutilApiMap generated from the inputs.
    """
    return {
        ApiMapConstants.API_MAP: gsutil_api_class_map_factory.GetClassMap(),
        ApiMapConstants.SUPPORT_MAP: support_map,
        ApiMapConstants.DEFAULT_MAP: default_map
    }
