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
"""Utilities for generating help docs for GCE compute labels commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

_LIST_LABELS_DETAILED_HELP_TEMPLATE = """
    Labels can be used to identify the {resource} and to filter them. To find a
    {resource} labeled with key-value pair ``k1'', ``v2''

      $ {{parent_command}} list --filter='labels.k1:v2'

    To list only the labels when describing a resource, use --format

      $ {{parent_command}} describe {sample} --format='default(labels)'
"""

_ADD_LABELS_BRIEF_DOC_TEMPLATE = """\
    Add labels to Google Compute Engine {}.
"""
_ADD_LABELS_DESCRIPTION_TEMPLATE = """
    *{{command}}* adds labels to a Google Compute Engine {product}.
"""
_ADD_LABELS_EXAMPLE_TEMPLATE = """
    To add key-value pairs ``k0''=``v0'' and ``k1''=``v1'' to '{sample}'

      $ {{command}} {sample} --labels=k0=v0,k1=v1
"""

_REMOVE_LABELS_BRIEF_DOC_TEMPLATE = """\
    Remove labels from Google Compute Engine {}.
"""
_REMOVE_LABELS_DESCRIPTION_TEMPLATE = """
    *{{command}}* removes labels from a Google Compute Engine {product}.
"""
_REMOVE_LABELS_EXAMPLE_TEMPLATE = """
    To remove existing labels with key ``k0'' and ``k1'' from '{sample}'

      $ {{command}} {sample} --labels=k0,k1
"""


# Maps a resource name (e.g. 'instance' or 'image') to its product name.
# No trailing whitespace allowed.
_RESOURCE_NAME_TO_PRODUCT_NAME_MAP = {}
_RESOURCE_NAME_TO_PRODUCT_NAME_MAP['disk'] = 'persistent disk'
_RESOURCE_NAME_TO_PRODUCT_NAME_MAP['instance'] = 'virtual machine instance'
# Maps a product name to its plural form. Only include cases where
# the plural form is not simply appending a 's' at the end.
_PRODUCT_NAME_PLURAL_MAP = {}


def GenerateDetailedHelpForAddLabels(resource):
  """Generates the detailed help doc for add-labels command for a resource.

  Args:
    resource: The name of the resource. e.g "instance", "image" or "disk"
  Returns:
    The detailed help doc for the add-labels command.
  """
  return _GenerateDetailedHelpForCommand(resource,
                                         _ADD_LABELS_BRIEF_DOC_TEMPLATE,
                                         _ADD_LABELS_DESCRIPTION_TEMPLATE,
                                         _ADD_LABELS_EXAMPLE_TEMPLATE)


def GenerateDetailedHelpForRemoveLabels(resource):
  """Generates the detailed help doc for remove-labels command for a resource.

  Args:
    resource: The name of the resource. e.g "instance", "image" or "disk"
  Returns:
    The detailed help doc for the remove-labels command.
  """
  return _GenerateDetailedHelpForCommand(resource,
                                         _REMOVE_LABELS_BRIEF_DOC_TEMPLATE,
                                         _REMOVE_LABELS_DESCRIPTION_TEMPLATE,
                                         _REMOVE_LABELS_EXAMPLE_TEMPLATE)


def _GenerateDetailedHelpForCommand(resource, brief_doc_template,
                                    description_template, example_template):
  """Generates the detailed help doc for a command.

  Args:
    resource: The name of the resource. e.g "instance", "image" or "disk"
    brief_doc_template: The brief doc template to use.
    description_template: The command description template.
    example_template: The example template to use.
  Returns:
    The detailed help doc for a command. The returned value is a map with
    two attributes; 'brief' and 'description'.
  """
  product = _RESOURCE_NAME_TO_PRODUCT_NAME_MAP.get(resource, resource)
  product_plural = _PRODUCT_NAME_PLURAL_MAP.get(product, product + 's')
  sample = 'example-{0}'.format(resource)

  brief = brief_doc_template.format(product_plural)
  format_kwargs = {'product': product, 'sample': sample,
                   'resource': resource}
  description = description_template.format(**format_kwargs)
  examples = (
      example_template.format(**format_kwargs) +
      _LIST_LABELS_DETAILED_HELP_TEMPLATE.format(**format_kwargs))

  return {'brief': brief, 'DESCRIPTION': description, 'EXAMPLES': examples}
