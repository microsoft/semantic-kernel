# -*- coding: utf-8 -*- #
# Copyright 2022 Google LLC. All Rights Reserved.
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
"""Utilities for "gcloud metastore federations" commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import re

from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.metastore import validators as validator

import six


def GenerateCreateBackends(job_ref, args, create_federation_req):
  """Construct the backend names for create requests of Dataproc Metastore federations.

  Args:
    job_ref: A resource ref to the parsed Federation resource.
    args: The parsed args namespace from CLI.
    create_federation_req: Create federation request for the API call.

  Returns:
    Modified request for the API call.
  """

  return validator.ParseBackendsIntoRequest(job_ref, create_federation_req)


def GenerateUpdateBackends(job_ref, args, update_federation_req):
  """Construct the long name for backends and updateMask for update requests of Dataproc Metastore federations.

  Args:
    job_ref: A resource ref to the parsed Federation resource.
    args: The parsed args namespace from CLI.
    update_federation_req: Update federation request for the API call.

  Returns:
    Modified request for the API call.
  """
  args_set = set(args.GetSpecifiedArgNames())
  if '--remove-backends' in args_set and '--update-backends' not in args_set:
    update_federation_req.federation.backendMetastores = {}

  if '--update-backends' in args_set:
    validator.ParseBackendsIntoRequest(job_ref, update_federation_req)
  update_federation_req.updateMask = _GenerateUpdateMask(args)
  return update_federation_req


def _AppendKeysToUpdateMask(prefix, key):
  return prefix + '.' + key


def _GenerateUpdateMask(args):
  """Constructs updateMask for federation patch requests.

  Args:
    args: The parsed args namespace from CLI.

  Returns:
    String containing update mask for patch request.
  """

  arg_name_to_field = {
      '--clear-backends': 'backend_metastores',
      '--clear-labels': 'labels'
  }

  update_mask = set()
  input_args = set(args.GetSpecifiedArgNames())
  for arg_name in input_args.intersection(arg_name_to_field):
    update_mask.add(arg_name_to_field[arg_name])

  for arg in input_args:
    if 'backend_metastores' not in update_mask:
      if '--update-backends' == arg:
        update_backends_value = args.update_backends
        backends_list = update_backends_value.split(',')
        for backend in backends_list:
          update_mask.add(
              _AppendKeysToUpdateMask('backend_metastores',
                                      backend.split('=')[0]))
      if '--remove-backends' == arg:
        remove_backends_value = args.remove_backends
        backend_keys_list = remove_backends_value.split(',')
        for backend in backend_keys_list:
          update_mask.add(
              _AppendKeysToUpdateMask('backend_metastores', backend))

    if 'labels' not in update_mask:
      if '--update-labels' == arg:
        for key in args.update_labels:
          update_mask.add(_AppendKeysToUpdateMask('labels', key))
      if '--remove-labels' == arg:
        for key in args.remove_labels:
          update_mask.add(_AppendKeysToUpdateMask('labels', key))

  return ','.join(sorted(update_mask))
