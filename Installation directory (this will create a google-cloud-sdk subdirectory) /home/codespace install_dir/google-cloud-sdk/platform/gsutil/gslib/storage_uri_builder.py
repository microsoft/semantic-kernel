# -*- coding: utf-8 -*-
# Copyright 2012 Google Inc. All Rights Reserved.
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
"""Class that holds state for instantiating StorageUri objects.

The StorageUri func defined in this class uses that state
(bucket_storage_uri_class and debug) needed plus gsutil default flag values to
instantiate this frequently constructed object with just one param for most
cases.
"""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals

import boto


class StorageUriBuilder(object):
  """Class for instantiating StorageUri objects."""

  def __init__(self, debug, bucket_storage_uri_class):
    """Initializes the builder.

    Args:
      debug: Debug level to pass in to boto connection (range 0..3).
      bucket_storage_uri_class: Class to instantiate for cloud StorageUris.
                                Settable for testing/mocking.
    """
    self.bucket_storage_uri_class = bucket_storage_uri_class
    self.debug = debug

  def StorageUri(self, uri_str):
    """Instantiates StorageUri using class state and gsutil default flag values.

    Args:
      uri_str: StorageUri naming bucket or object.

    Returns:
      boto.StorageUri for given uri_str.

    Raises:
      InvalidUriError: if uri_str not valid.
    """
    return boto.storage_uri(
        uri_str,
        'file',
        debug=self.debug,
        validate=False,
        bucket_storage_uri_class=self.bucket_storage_uri_class,
        suppress_consec_slashes=False)
