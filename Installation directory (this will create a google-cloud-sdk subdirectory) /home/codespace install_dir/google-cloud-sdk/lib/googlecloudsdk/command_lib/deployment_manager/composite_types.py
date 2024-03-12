# -*- coding: utf-8 -*- #
# Copyright 2016 Google LLC. All Rights Reserved.
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

"""composite-types command basics."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.deployment_manager import exceptions
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.command_lib.deployment_manager import importer
from googlecloudsdk.core import properties


def AddCompositeTypeNameFlag(parser):
  """Add the composite type name argument.

  Args:
    parser: An argparse parser that you can use to add arguments that go
        on the command line after this command. Positional arguments are
        allowed.
  """
  parser.add_argument('name', help='Composite type name.')


def AddDescriptionFlag(parser):
  """Add the description argument.

  Args:
    parser: An argparse parser that you can use to add arguments that go
        on the command line after this command. Positional arguments are
        allowed.
  """
  parser.add_argument('--description',
                      help='Optional description of the composite type.',
                      default='')


def AddStatusFlag(parser):
  """Add the status argument.

  Args:
    parser: An argparse parser that you can use to add arguments that go
        on the command line after this command. Positional arguments are
        allowed.
  """
  parser.add_argument('--status',
                      help='Optional status for a composite type.',
                      choices=['DEPRECATED', 'EXPERIMENTAL', 'SUPPORTED'],
                      default=None)


template_flag_arg_type = arg_parsers.RegexpValidator(
    r'.*\.(py|jinja)',
    'must be a python (".py") or jinja (".jinja") file')


def AddTemplateFlag(parser):
  """Add the template path argument.

  Args:
    parser: An argparse parser that you can use to add arguments that go
        on the command line after this command. Positional arguments are
        allowed.
  """
  parser.add_argument('--template',
                      help=('Path to a python or jinja file (local or via URL) '
                            'that defines the composite type. If you want to '
                            'provide a schema, that file must be in the same '
                            'location: e.g. "--template=./foobar.jinja" means '
                            '"./foobar.jinja.schema" should also exist. The '
                            'file must end in either ".jinja" or ".py" to be '
                            'interpreted correctly.'),
                      type=template_flag_arg_type,
                      required=True)


def TemplateContentsFor(messages, template_path):
  """Build a TemplateContents message from a local template or url.

  Args:
    messages: The API message to use.
    template_path: Path to the config yaml file, with an optional list of
      imports.

  Returns:
    The TemplateContents message from the template at template_path.

  Raises:
    Error if the provided file is not a template.
  """
  config_obj = importer.BuildConfig(template=template_path)

  if not config_obj.IsTemplate():
    raise exceptions.Error(
        'The provided file must be a template.')

  template_name = config_obj.GetBaseName()
  schema_name = template_name + '.schema'
  file_type = messages.TemplateContents.InterpreterValueValuesEnum.JINJA if template_name.endswith(
      '.jinja') else messages.TemplateContents.InterpreterValueValuesEnum.PYTHON

  imports = importer.CreateImports(messages, config_obj)

  template = ''
  schema = ''

  # Find schema and template from imports
  for item in imports:
    if item.name == template_name:
      template = item.content
    elif item.name == schema_name:
      schema = item.content

  # Remove schema and template from imports
  imports = [item for item in imports
             if item.name not in [template_name, schema_name]]

  return messages.TemplateContents(imports=imports,
                                   schema=schema,
                                   template=template,
                                   interpreter=file_type)


def GetReference(resources, name):
  return resources.Parse(
      name,
      params={'project': properties.VALUES.core.project.GetOrFail},
      collection='deploymentmanager.compositeTypes')
