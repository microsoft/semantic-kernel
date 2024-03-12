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

"""Common resource topic text."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import pkgutil
import textwrap

from googlecloudsdk import api_lib
from googlecloudsdk.core.resource import resource_printer
from googlecloudsdk.core.resource import resource_transform

import six
from six.moves import range  # pylint: disable=redefined-builtin


def ResourceDescription(name):
  """Generates resource help DESCRIPTION help text for name.

  This puts common text for the key, formats and projections topics in one
  place.

  Args:
    name: One of ['filter', 'format', 'key', 'projection'].

  Raises:
    ValueError: If name is not one of the expected topic names.

  Returns:
    A detailed_help DESCRIPTION markdown string.
  """
  description = """\
  Most *gcloud* commands return a list of resources on success. By default they
  are pretty-printed on the standard output. The
  *--format=*_NAME_[_ATTRIBUTES_]*(*_PROJECTION_*)* and
  *--filter=*_EXPRESSION_ flags along with projections can be used to format and
  change the default output to a more meaningful result.

  Use the `--format` flag to change the default output format of a command. \
  {see_format}

  Use the `--filter` flag to select resources to be listed. {see_filter}

  Use resource-keys to reach resource items through a unique path of names from the root. {see_key}

  Use projections to list a subset of resource keys in a resource. \
  {see_projection}

  Note: To refer to a list of fields you can sort, filter, and format by for
  each resource, you can run a list command with the format set to `text` or
  `json`. For
  example, $ gcloud compute instances list --limit=1 --format=text.

  To work through an interactive tutorial about using the filter and format
  flags instead, see: https://console.cloud.google.com/cloudshell/open?git_repo=https://github.com/GoogleCloudPlatform/cloud-shell-tutorials&page=editor&tutorial=cloudsdk/tutorial.md
  """
  # topic <name> => gcloud topic <command>
  topics = {
      'filter': 'filters',
      'format': 'formats',
      'key': 'resource-keys',
      'projection': 'projections',
  }
  if name not in topics:
    raise ValueError('Expected one of [{topics}], got [{name}].'.format(
        topics=','.join(sorted(topics)), name=name))
  see = {}
  for topic, command in six.iteritems(topics):
    if topic == name:
      see[topic] = 'Resource {topic}s are described in detail below.'.format(
          topic=topic)
    else:
      see[topic] = 'For details run $ gcloud topic {command}.'.format(
          command=command)
  return textwrap.dedent(description).format(see_filter=see['filter'],
                                             see_format=see['format'],
                                             see_key=see['key'],
                                             see_projection=see['projection'])


_DOC_MAIN, _DOC_ARGS, _DOC_ATTRIBUTES, _DOC_EXAMPLE, _DOC_SKIP = range(5)


def _AppendParagraph(lines):
  """Appends paragraph markdown to lines.

  Paragraph markdown is used to add paragraphs in nested lists at the list
  prevaling indent. _AppendParagraph does not append the markdown if the last
  line in lines is already a paragraph markdown.

  A line containing only the + character is a paragraph markdown. It renders
  a blank line and starts the next paragraph of lines using the prevailing
  indent. A blank line would also start a new paragraph but would decrease the
  prevailing indent.

  Args:
    lines: The lines to append to.
  """
  if lines and not lines[-1].endswith('\n+\n'):
    # The last line in lines is not a paragrpah markdown.
    if lines[-1].endswith('\n'):
      # Don't append a blank line -- that would decrease the indentation.
      lines.append('+\n')
    else:
      lines.append('\n+\n')


def _AppendLine(lines, line, paragraph):
  """Appends line to lines handling list markdown.

  Args:
    lines: The lines to append to.
    line: The line to append.
    paragraph: Start a new paragraph if True.

  Returns:
    The new paragraph value. This will always be False.
  """
  if paragraph:
    paragraph = False
    _AppendParagraph(lines)
  elif lines and not lines[-1].endswith('\n'):
    lines.append(' ')
  if line.startswith('* ') or line.endswith('::'):
    if lines and not lines[-1].endswith('\n'):
      lines.append('\n')
    lines.append(line)
    lines.append('\n')
  else:
    lines.append(line)
  return paragraph


def _ParseFormatDocString(printer):
  """Parses the doc string for printer.

  Args:
    printer: The doc string will be parsed from this resource format printer.

  Returns:
    A (description, attributes) tuple:
      description - The format description.
      attributes - A list of (name, description) tuples, one tuple for each
        format-specific attribute.

  Example resource printer docstring parsed by this method:
    '''This line is skipped. Printer attributes and Example sections optional.

    These lines describe the format.
    Another description line.

    Printer attributes:
      attribute-1-name: The description for attribute-1-name.
      attribute-N-name: The description for attribute-N-name.

    Example:
      One or more example lines for the 'For example:' section.
    '''
  """
  descriptions = []
  attributes = []
  example = []
  if not printer.__doc__:
    return '', '', ''
  _, _, doc = printer.__doc__.partition('\n')
  collect = _DOC_MAIN
  attribute = None
  attribute_description = []
  paragraph = False
  for line in textwrap.dedent(doc).split('\n'):
    if not line.startswith(' ') and line.endswith(':'):
      # The start of a new section.
      paragraph = False
      if attribute:
        # The current attribute description is done.
        attributes.append((attribute, ''.join(attribute_description)))
        attribute = None
      if line == 'Printer attributes:':
        # Now collecting Printer attributes: section lines.
        collect = _DOC_ATTRIBUTES
      elif line == 'Example:':
        # Now collecting Example: section lines.
        collect = _DOC_EXAMPLE
      else:
        collect = _DOC_SKIP
    elif collect == _DOC_SKIP:
      # Only interested in the description body and the Printer args: section.
      continue
    elif not line:
      # Blank line for new paragraph at current indendataion.
      paragraph = True
    elif collect == _DOC_MAIN:
      # The main description line.
      paragraph = _AppendLine(descriptions, line, paragraph)
    elif line.startswith('    '):
      if collect == _DOC_ATTRIBUTES:
        # An attribute description line.
        paragraph = _AppendLine(attribute_description, line.strip(), paragraph)
    elif collect == _DOC_EXAMPLE and line.startswith('  '):
      # An example section line.
      paragraph = _AppendLine(example, line, paragraph)
    else:
      # The current attribute description is done.
      if attribute:
        attributes.append((attribute, ''.join(attribute_description)))
      # A new attribute description.
      attribute, _, text = line.partition(':')
      attribute = attribute.strip()
      attribute = attribute.lstrip('*')
      attribute_description = [text.strip()]
  if attribute:
    attributes.append((attribute, ''.join(attribute_description)))
  return ''.join(descriptions), attributes, example


def FormatRegistryDescriptions():
  """Returns help markdown for all registered resource printer formats."""
  # Generate the printer markdown.
  descriptions = ['The formats and format specific attributes are:\n']
  for name, printer in sorted(
      six.iteritems(resource_printer.GetFormatRegistry())):
    description, attributes, example = _ParseFormatDocString(printer)
    descriptions.append('\n*{name}*::\n{description}\n'.format(
        name=name, description=description))
    if attributes:
      _AppendParagraph(descriptions)
      descriptions.append('The format attributes are:\n\n')
      for attribute, description in attributes:
        descriptions.append('*{attribute}*:::\n{description}\n'.format(
            attribute=attribute, description=description))
      descriptions.append(':::\n')
    if example:
      _AppendParagraph(descriptions)
      descriptions.append('For example:\n+\n{example}\n'.format(
          example=''.join(example)))
  descriptions.append('::\n')

  # Generate the "attributes for all printers" markdown.
  description, attributes, example = _ParseFormatDocString(
      resource_printer.PrinterAttributes)
  if attributes:
    descriptions.append('\n{description}:\n+\n'.format(
        description=description[:-1]))
    for attribute, description in attributes:
      descriptions.append('*{attribute}*::\n{description}\n'.format(
          attribute=attribute, description=description))
  if example:
    _AppendParagraph(descriptions)
    descriptions.append('For example:\n+\n{example}\n'.format(
        example=''.join(example)))
  descriptions.append('\n')
  return ''.join(descriptions)


def _StripUnusedNotation(string):
  """Returns string with Pythonic unused notation stripped."""
  if string.startswith('_'):
    return string.lstrip('_')
  unused = 'unused_'
  if string.startswith(unused):
    return string[len(unused):]
  return string


def _ParseTransformDocString(func):
  """Parses the doc string for func.

  Args:
    func: The doc string will be parsed from this function.

  Returns:
    A (description, prototype, args) tuple:
      description - The function description.
      prototype - The function prototype string.
      args - A list of (name, description) tuples, one tuple for each arg.

  Example transform function docstring parsed by this method:
    '''Transform description. Example sections optional.

    These lines are skipped.
    Another skipped line.

    Args:
      r: The resource arg is always sepcified but omitted from the docs.
      arg-2-name[=default-2]: The description for arg-2-name.
      arg-N-name[=default-N]: The description for arg-N-name.
      kwargs: Omitted from the description.

    Example:
      One or more example lines for the 'For example:' section.
    '''
  """
  hidden_args = ('kwargs', 'projection', 'r')
  if not func.__doc__:
    return '', '', '', ''
  description, _, doc = func.__doc__.partition('\n')
  collect = _DOC_MAIN
  arg = None
  descriptions = [description]
  example = []
  args = []
  arg_description = []
  paragraph = False
  for line in textwrap.dedent(doc).split('\n'):
    if not line:
      paragraph = True
    elif line == 'Args:':
      # Now collecting Args: section lines.
      collect = _DOC_ARGS
      paragraph = False
    elif line == 'Example:':
      # Now collecting Example: section lines.
      collect = _DOC_EXAMPLE
      paragraph = False
    elif collect == _DOC_SKIP:
      # Not interested in this line.
      continue
    elif collect == _DOC_MAIN:
      # The main description line.
      paragraph = _AppendLine(descriptions, line, paragraph)
    elif collect == _DOC_ARGS and line.startswith('    '):
      # An arg description line.
      paragraph = _AppendLine(arg_description, line, paragraph)
    elif collect == _DOC_EXAMPLE and line.startswith('  '):
      # An example description line.
      paragraph = _AppendLine(example, line[2:], paragraph)
    else:
      # The current arg description is done.
      if arg:
        arg = _StripUnusedNotation(arg)
      if arg and arg not in hidden_args:
        args.append((arg, ' '.join(arg_description)))
      if not line.startswith(' ') and line.endswith(':'):
        # The start of a new section.
        collect = _DOC_SKIP
        continue
      # A new arg description.
      arg, _, text = line.partition(':')
      arg = arg.strip()
      arg = arg.lstrip('*')
      arg_description = [text.strip()]

  # Collect the formal arg list with defaults for the function prototype.
  import inspect  # pylint: disable=g-import-not-at-top, For startup efficiency.
  # getfullargspec() may fail in the future if the "func" method passed in has
  # kwargs-only arguments, in which case refactoring will be needed. See
  # b/287663703 for more details.
  argspec = inspect.getfullargspec(func)
  default_index_start = len(argspec.args) - len(argspec.defaults or [])
  formals = []
  for formal_index, formal in enumerate(argspec.args):
    if formal:
      formal = _StripUnusedNotation(formal)
    if formal in hidden_args:
      continue
    default_index = formal_index - default_index_start
    default = argspec.defaults[default_index] if default_index >= 0 else None
    if default is not None:
      default_display = repr(default).replace("'", '"')
      # Trim off the unicode 'u'.
      if default_display.startswith('u"'):
        default_display = default_display[1:]
      if default_display == 'False':
        default_display = 'false'
      elif default_display == 'True':
        default_display = 'true'
      formals.append('{formal}={default_display}'.format(
          formal=formal, default_display=default_display))
    else:
      formals.append(formal)
  if argspec.varargs:
    formals.append(argspec.varargs)
  prototype = '({formals})'.format(formals=', '.join(formals))

  return ''.join(descriptions), prototype, args, example


def TransformsDescriptions(transforms):
  """Generates resource transform help text markdown for transforms.

  Args:
    transforms: The transform name=>method symbol table.

  Returns:
    The resource transform help text markdown for transforms.
  """
  descriptions = []
  for name, transform in sorted(six.iteritems(transforms)):
    description, prototype, args, example = _ParseTransformDocString(transform)
    if not description:
      continue
    descriptions.append('\n\n*{name}*{prototype}::\n{description}'.format(
        name=name, prototype=prototype, description=description))
    if args:
      _AppendParagraph(descriptions)
      descriptions.append('The arguments are:\n+\n')
      for arg, description in args:
        descriptions.append('*```{arg}```*:::\n{description}\n'.format(
            arg=arg, description=description))
        descriptions.append(':::\n')
    if example:
      _AppendParagraph(descriptions)
      descriptions.append('For example:\n+\n{example}\n'.format(
          example=''.join(example)))
    descriptions.append('::\n')
  return ''.join(descriptions)


def _GetApiTransforms(api):
  """Returns the transforms for api if it has a transforms module."""
  if api == 'builtin':
    return resource_transform.GetTransforms()
  # Include all api_lib.*.transforms modules that have GetTransforms().
  method_name = 'GetTransforms'
  module_path = 'googlecloudsdk.api_lib.{api}.transforms'.format(api=api)
  try:
    module = __import__(module_path, fromlist=[method_name])
    method = getattr(module, method_name)
    return method()
  except ImportError:
    return None


def TransformRegistryDescriptions():
  """Returns help markdown for all registered resource transforms."""
  descriptions = []
  apis = set(
      [name for _, name, _ in pkgutil.iter_modules(api_lib.__path__) if name])
  for api in ['builtin'] + sorted(apis):
    transforms = _GetApiTransforms(api)
    if transforms:
      descriptions.append(
          '\nThe {api} transform functions are:\n{desc}\n'.format(
              api=api, desc=TransformsDescriptions(transforms)))
  return ''.join(descriptions)
