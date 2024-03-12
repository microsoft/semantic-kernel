# -*- coding: utf-8 -*- #
# Copyright 2014 Google LLC. All Rights Reserved.
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
"""Common utility functions for ReplicaPool template processing.

These utility functions enable easy replacement of parameters into
ReplicaPool template files.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.command_lib.compute import exceptions
from googlecloudsdk.core import yaml
from googlecloudsdk.core.util import files

import six


def AddTemplateParamArgs(parser):
  """Adds --param and --param-from-file flags."""
  parser.add_argument(
      '--param',
      type=arg_parsers.ArgDict(min_length=1),
      help=('A list of key=value parameters to substitute in the template '
            'before the template is submitted to the replica pool. This does '
            'not change the actual template file.'),
      metavar='PARAM=VALUE')
  parser.add_argument(
      '--param-from-file',
      type=arg_parsers.ArgDict(min_length=1),
      help=('A list of files each containing a key=value parameter to '
            'substitute in the template before the template is submitted '
            'to the replica pool. This does not change the actual template '
            'file.'),
      metavar='PARAM=FILE_PATH')


def ParseTemplate(template_file, params=None, params_from_file=None):
  """Parse and apply params into a template file.

  Args:
    template_file: The path to the file to open and parse.
    params: a dict of param-name -> param-value
    params_from_file: a dict of param-name -> param-file

  Returns:
    The parsed template dict

  Raises:
    yaml.Error: When the template file cannot be read or parsed.
    ArgumentError: If any params are not provided.
    ValidationError: if the YAML file is invalid.
  """
  params = params or {}
  params_from_file = params_from_file or {}

  joined_params = dict(params)
  for key, file_path in six.iteritems(params_from_file):
    if key in joined_params:
      raise exceptions.DuplicateError('Duplicate param key: ' + key)
    try:
      joined_params[key] = files.ReadFileContents(file_path)
    except files.Error as e:
      raise exceptions.ArgumentError(
          'Could not load param key "{0}" from file "{1}": {2}'.format(
              key, file_path, e.strerror))

  template = yaml.load_path(template_file)

  if not isinstance(template, dict) or 'template' not in template:
    raise exceptions.ValidationError(
        'Invalid template format.  Root must be a mapping with single '
        '"template" value')

  (template, missing_params, used_params) = ReplaceTemplateParams(
      template, joined_params)
  if missing_params:
    raise exceptions.ArgumentError(
        'Some parameters were present in the template but not provided on '
        'the command line: ' + ', '.join(sorted(missing_params)))
  unused_params = set(joined_params.keys()) - used_params
  if unused_params:
    raise exceptions.ArgumentError(
        'Some parameters were specified on the command line but not referenced '
        'in the template: ' + ', '.join(sorted(unused_params)))
  return template


def ReplaceTemplateParams(node, params):
  """Apply the params provided into the template.

  Args:
    node: A node in the parsed template
    params: a dict of params of param-name -> param-value

  Returns:
    A tuple of (new_node, missing_params, used_params) where new_node is the
    node with all params replaced, missing_params is set of param
    references found in the node that were not provided and used_params were
    the params that we actually used.
  """
  if isinstance(node, six.string_types):
    if node.startswith('{{') and node.endswith('}}'):
      param = node[2:-2].strip()
      if param in params:
        return (params[param], set(), set([param]))
      else:
        return (node, set([param]), set())

  if isinstance(node, dict):
    missing_params = set()
    used_params = set()
    for k in node.keys():
      (new_subnode, new_missing, new_used) = ReplaceTemplateParams(
          node[k], params)
      node[k] = new_subnode
      missing_params.update(new_missing)
      used_params.update(new_used)
    return (node, missing_params, used_params)

  if isinstance(node, list):
    missing_params = set()
    used_params = set()
    new_node = []
    for subnode in node:
      (new_subnode, new_missing, new_used) = ReplaceTemplateParams(
          subnode, params)
      new_node.append(new_subnode)
      missing_params.update(new_missing)
      used_params.update(new_used)
    return (new_node, missing_params, used_params)

  return (node, set(), set())
