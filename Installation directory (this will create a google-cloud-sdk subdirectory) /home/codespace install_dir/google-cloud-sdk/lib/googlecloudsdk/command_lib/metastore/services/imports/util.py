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
"""Utilities for "gcloud metastore services imports" commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.util import apis


def Messages(api_version):
  return apis.GetMessagesModule('metastore', api_version)


def UpdateDescription(unused_ref, args, update_import_req):
  """Constructs updateMask for update requests of Dataproc Metastore services.

  Args:
    unused_ref: A resource ref to the parsed Service resource.
    args: The parsed args namespace from CLI.
    update_import_req: Created Update request for the API call.

  Returns:
    Modified request for the API call.
  """
  update_import_req.metadataImport.description = args.description
  return update_import_req

