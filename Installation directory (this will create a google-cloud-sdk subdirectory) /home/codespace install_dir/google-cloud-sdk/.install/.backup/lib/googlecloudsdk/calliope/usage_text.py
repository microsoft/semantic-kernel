# -*- coding: utf-8 -*- #
# Copyright 2013 Google LLC. All Rights Reserved.
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

"""Generate usage text for displaying to the user."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import argparse
import collections
import copy
import difflib
import enum
import io
import re
import sys
import textwrap

from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import arg_parsers_usage_text
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import parser_arguments
from googlecloudsdk.calliope.concepts import util as format_util
import six

LINE_WIDTH = 80
HELP_INDENT = 25
# Used to offset second-line indentation of arg choices in markdown.
_CHOICE_OFFSET = 3
_ARG_DETAILS_OFFSET = 1


class HelpInfo(object):
  """A class to hold some the information we need to generate help text."""

  def __init__(self, help_text, is_hidden, release_track):
    """Create a HelpInfo object.

    Args:
      help_text: str, The text of the help message.
      is_hidden: bool, True if this command or group has been marked as hidden.
      release_track: calliope.base.ReleaseTrack, The maturity level of this
        command.
    """
    self.help_text = help_text or ''
    self.is_hidden = is_hidden
    self.release_track = release_track


class TextChoiceSuggester(object):
  """Utility to suggest mistyped commands.

  """

  def __init__(self, choices=None):
    # A mapping of 'thing typed' to the suggestion that should be offered.
    # Often, these will be the same, but this allows for offering more currated
    # suggestions for more commonly misused things.
    self._choices = {}
    if choices:
      self.AddChoices(choices)

  def AddChoices(self, choices):
    """Add a set of valid things that can be suggested.

    Args:
      choices: [str], The valid choices.
    """
    for choice in choices:
      if choice not in self._choices:
        # Keep the first choice mapping that was added so later aliases don't
        # clobber real choices.
        self._choices[choice] = choice

  def AddAliases(self, aliases, suggestion):
    """Add an alias that is not actually a valid choice, but will suggest one.

    This should be called after AddChoices() so that aliases will not clobber
    any actual choices.

    Args:
      aliases: [str], The aliases for the valid choice.  This is something
        someone will commonly type when they actually mean something else.
      suggestion: str, The valid choice to suggest.
    """
    for alias in aliases:
      if alias not in self._choices:
        self._choices[alias] = suggestion

  def GetSuggestion(self, arg):
    """Find the item that is closest to what was attempted.

    Args:
      arg: str, The argument provided.

    Returns:
      str, The closest match.
    """
    if not self._choices:
      return None

    match = difflib.get_close_matches(
        arg.lower(), [six.text_type(c) for c in self._choices], 1)
    if match:
      choice = [c for c in self._choices if six.text_type(c) == match[0]][0]
      return self._choices[choice]
    return self._choices[match[0]] if match else None


class ArgumentWrapper(parser_arguments.Argument):
  pass


def _ApplyMarkdownItalic(msg):
  return re.sub(r'(\b[a-zA-Z][-a-zA-Z_0-9]*)',
                base.MARKDOWN_ITALIC + r'\1' + base.MARKDOWN_ITALIC, msg)


def GetPositionalUsage(arg, markdown=False):
  """Create the usage help string for a positional arg.

  Args:
    arg: parser_arguments.Argument, The argument object to be displayed.
    markdown: bool, If true add markdowns.

  Returns:
    str, The string representation for printing.
  """
  var = arg.metavar or arg.dest.upper()
  if markdown:
    var = _ApplyMarkdownItalic(var)
  if arg.nargs == '+':
    return '{var} [{var} ...]'.format(var=var)
  elif arg.nargs == '*':
    return '[{var} ...]'.format(var=var)
  elif arg.nargs == argparse.REMAINDER:
    return '[-- {var} ...]'.format(var=var)
  elif arg.nargs == '?':
    return '[{var}]'.format(var=var)
  else:
    return var


def _GetFlagMetavar(flag, metavar=None, name=None, markdown=False):
  """Returns a usage-separator + metavar for flag."""
  if metavar is None:
    metavar = flag.metavar or flag.dest.upper()
  separator = '=' if name and name.startswith('--') else ' '
  if isinstance(flag.type, arg_parsers_usage_text.ArgTypeUsage):
    metavar = flag.type.GetUsageMetavar(bool(flag.metavar), metavar) or metavar
  if metavar == ' ':
    return ''
  if markdown:
    metavar = _ApplyMarkdownItalic(metavar)
  if separator == '=':
    metavar = separator + metavar
    separator = ''
  if flag.nargs in ('?', '*'):
    metavar = '[' + metavar + ']'
    separator = ''
  return separator + metavar


def _QuoteValue(value):
  """Returns value quoted, with preference for "..."."""
  quoted = repr(value)
  if quoted.startswith('u'):
    quoted = quoted[1:]
  if quoted.startswith("'") and '"' not in value:
    quoted = '"' + quoted[1:-1] + '"'
  return quoted


def _FilterFlagNames(names):
  """Mockable flag name list filter."""
  return names


class InvertedValue(enum.Enum):
  NORMAL = 0
  INVERTED = 1
  BOTH = 2


def GetFlagUsage(arg, brief=False, markdown=False,
                 inverted=InvertedValue.NORMAL, value=True):
  """Returns the usage string for a flag arg.

  Args:
    arg: parser_arguments.Argument, The argument object to be displayed.
    brief: bool, If true, only display one version of a flag that has
        multiple versions, and do not display the default value.
    markdown: bool, If true add markdowns.
    inverted: InvertedValue, If INVERTED display the --no-* inverted name. If
        NORMAL display the normal name. If BOTH, display both.
    value: bool, If true display flag name=value for non-Boolean flags.

  Returns:
    str, The string representation for printing.
  """
  if inverted is InvertedValue.BOTH:
    names = [x.replace('--', '--[no-]', 1) for x in sorted(arg.option_strings)]
  elif inverted is InvertedValue.INVERTED:
    names = [x.replace('--', '--no-', 1) for x in sorted(arg.option_strings)]
  else:
    names = sorted(arg.option_strings)
  names = _FilterFlagNames(names)
  metavar = arg.metavar or arg.dest.upper()
  if not value or brief:
    try:
      long_string = names[0]
    except IndexError:
      long_string = ''
    if not value or arg.nargs == 0:
      return long_string
    flag_metavar = _GetFlagMetavar(arg, metavar, name=long_string)
    return '{flag}{metavar}'.format(
        flag=long_string,
        metavar=flag_metavar)
  if arg.nargs == 0:
    if markdown:
      usage = ', '.join([base.MARKDOWN_BOLD + x + base.MARKDOWN_BOLD
                         for x in names])
    else:
      usage = ', '.join(names)
  else:
    usage_list = []
    for name in names:
      flag_metavar = _GetFlagMetavar(arg, metavar, name=name, markdown=markdown)
      usage_list.append(
          '{bb}{flag}{be}{flag_metavar}'.format(
              bb=base.MARKDOWN_BOLD if markdown else '',
              flag=name,
              be=base.MARKDOWN_BOLD if markdown else '',
              flag_metavar=flag_metavar))
    usage = ', '.join(usage_list)
    if arg.default and not getattr(arg, 'is_required',
                                   getattr(arg, 'required', False)):
      if isinstance(arg.default, list):
        default = ','.join(arg.default)
      elif isinstance(arg.default, dict):
        default = ','.join(['{0}={1}'.format(k, v)
                            for k, v in sorted(six.iteritems(arg.default))])
      else:
        default = arg.default
      usage += '; default={0}'.format(_QuoteValue(default))
  return usage


def _GetInvertedFlagName(flag):
  """Returns the inverted flag name for flag."""
  return flag.option_strings[0].replace('--', '--no-', 1)


def GetArgDetails(arg, depth=0):
  """Returns the help message with autogenerated details for arg."""
  help_text = getattr(arg, 'hidden_help', arg.help)
  if callable(help_text):
    help_text = help_text()
  help_message = textwrap.dedent(help_text) if help_text else ''
  if arg.is_hidden:
    return help_message
  if arg.is_group or arg.is_positional:
    choices = None
  elif arg.choices:
    choices = getattr(arg, 'visible_choices', arg.choices)
  else:
    try:
      choices = getattr(arg.type, 'visible_choices', arg.type.choices)
    except AttributeError:
      choices = None
  extra_help = []
  if hasattr(arg, 'store_property'):
    prop, _, _ = arg.store_property
    # Don't add help if there's already explicit help.
    if six.text_type(prop) not in help_message:
      extra_help.append('Overrides the default *{0}* property value'
                        ' for this command invocation.'.format(prop))
      # '?' in Boolean flag check to cover legacy choices={'true', 'false'}
      # flags. They are the only flags with nargs='?'. This would have been
      # much easier if argparse had a first class Boolean flag attribute.
      if prop.default and arg.nargs in (0, '?'):
        extra_help.append('Use *{}* to disable.'.format(
            _GetInvertedFlagName(arg)))
  elif arg.is_group or arg.is_positional or arg.nargs:
    # Not a Boolean flag.
    pass
  elif arg.default is True:
    extra_help.append(
        'Enabled by default, use *{0}* to disable.'.format(
            _GetInvertedFlagName(arg)))
  elif isinstance(arg, arg_parsers.StoreTrueFalseAction):
    # This would be a "tri-valued" (True, False, None) command.
    extra_help.append(
        'Use *{0}* to enable and *{1}* to disable.'.format(
            arg.option_strings[0], _GetInvertedFlagName(arg)))
  if choices:
    metavar = arg.metavar or arg.dest.upper()
    if metavar != ' ':
      choices = getattr(arg, 'choices_help', choices)
      if len(choices) > 1:
        one_of = 'one of'
      else:
        # TBD I guess?
        one_of = '(only one value is supported)'
      if isinstance(choices, dict):
        choices_iteritems = six.iteritems(choices)
        if not isinstance(choices, collections.OrderedDict):
          choices_iteritems = sorted(choices_iteritems)
        choices = []
        for name, desc in choices_iteritems:
          dedented_desc = textwrap.dedent(desc)
          choice_help = '*{name}*{depth} {desc}'.format(
              name=name,
              desc=dedented_desc,
              depth=':' * (depth + _CHOICE_OFFSET))
          choices.append(choice_help)
        # Append marker to indicate end of list.
        choices.append(':' * (depth + _CHOICE_OFFSET))
        extra_help.append(
            '_{metavar}_ must be {one_of}:\n\n{choices}\n\n'.format(
                metavar=metavar,
                one_of=one_of,
                choices='\n'.join(choices)))
      else:
        extra_help.append('_{metavar}_ must be {one_of}: {choices}.'.format(
            metavar=metavar,
            one_of=one_of,
            choices=', '.join(['*{0}*'.format(x) for x in choices])))

  arg_type = getattr(arg, 'type', None)
  if isinstance(arg_type, arg_parsers_usage_text.ArgTypeUsage):
    arg_name = arg.option_strings[0] if arg.option_strings else None
    field_name = arg_name and format_util.NamespaceFormat(arg_name)
    type_help_text = arg.type.GetUsageHelpText(
        field_name=field_name,
        required=arg.is_required,
        flag_name=arg_name)
    if type_help_text:
      deduped_help_text = re.sub(
          f'^{re.escape(help_text)}', '', type_help_text)
      extra_help.append(
          arg_parsers_usage_text.IndentAsciiDoc(
              deduped_help_text, depth + _ARG_DETAILS_OFFSET)
      )

  if extra_help:
    help_message = help_message.rstrip()
    if help_message:
      extra_help_message = ' '.join(extra_help)
      newline_index = help_message.rfind('\n')
      if newline_index >= 0 and help_message[newline_index + 1] == ' ':
        # Preserve example markdown at end of help_message.
        help_message += '\n\n' + extra_help_message + '\n'
      else:
        if not help_message.endswith('.'):
          help_message += '.'
        if help_message.rfind('\n\n') > 0:
          # help_message has multiple paragraphs. Put extra_help in a new
          # paragraph.
          help_message += '\n\n'
        else:
          help_message += ' '
        help_message += extra_help_message
  return help_message.replace('\n\n', '\n+\n').strip()


def _IsPositional(arg):
  """Returns True if arg is a positional or group that contains a positional."""
  if arg.is_hidden:
    return False
  if arg.is_positional:
    return True
  if arg.is_group:
    for a in arg.arguments:
      if _IsPositional(a):
        return True
  return False


def _GetArgUsageSortKey(name):
  """Arg name usage string key function for sorted."""
  if not name:
    return 0, ''  # paranoid fail safe check -- should not happen
  elif name.startswith('--no-'):
    return 3, name[5:], 'x'  # --abc --no-abc
  elif name.startswith('--'):
    return 3, name[2:]
  elif name.startswith('-'):
    return 4, name[1:]
  elif name[0].isalpha():
    return 1, ''  # stable sort for positionals
  else:
    return 5, name


def GetSingleton(args):
  """Returns the single non-hidden arg in args.arguments or None."""
  singleton = None
  for arg in args.arguments:
    if arg.is_hidden:
      continue
    if arg.is_group:
      arg = GetSingleton(arg)
      if not arg:
        return None
    if singleton:
      return None
    singleton = arg

  if (singleton and not isinstance(args, ArgumentWrapper) and
      singleton.is_required != args.is_required):
    singleton = copy.copy(singleton)
    singleton.is_required = args.is_required

  return singleton


def GetArgSortKey(arg):
  """Arg key function for sorted."""
  name = re.sub(' +', ' ',
                re.sub('[](){}|[]', '',
                       GetArgUsage(arg, value=False, hidden=True) or ''))
  if arg.is_group:
    singleton = GetSingleton(arg)
    if singleton:
      arg = singleton
  if arg.is_group:
    if _IsPositional(arg):
      return 1, ''  # stable sort for positionals
    if arg.is_required:
      return 6, name
    return 7, name
  elif arg.nargs == argparse.REMAINDER:
    return 8, name
  if arg.is_positional:
    return 1, ''  # stable sort for positionals
  if arg.is_required:
    return 2, name
  return _GetArgUsageSortKey(name)


def _MarkOptional(usage):
  """Returns usage enclosed in [...] if it hasn't already been enclosed."""

  # If the leading bracket matches the trailing bracket its already marked.
  if re.match(r'^\[[^][]*(\[[^][]*\])*[^][]*\]$', usage):
    return usage
  return '[{}]'.format(usage)


def GetArgUsage(arg, brief=False, definition=False, markdown=False,
                optional=True, top=False, remainder_usage=None, value=True,
                hidden=False):
  """Returns the argument usage string for arg or all nested groups in arg.

  Mutually exclusive args names are separated by ' | ', otherwise ' '.
  Required groups are enclosed in '(...)', otherwise '[...]'. Required args
  in a group are separated from the optional args by ' : '.

  Args:
    arg: The argument to get usage from.
    brief: bool, If True, only display one version of a flag that has
        multiple versions, and do not display the default value.
    definition: bool, Definition list usage if True.
    markdown: bool, Add markdown if True.
    optional: bool, Include optional flags if True.
    top: bool, True if args is the top level group.
    remainder_usage: [str], Append REMAINDER usage here instead of the return.
    value: bool, If true display flag name=value for non-Boolean flags.
    hidden: bool, Include hidden args if True.

  Returns:
    The argument usage string for arg or all nested groups in arg.
  """
  if arg.is_hidden and not hidden:
    return ''
  if arg.is_group:
    singleton = GetSingleton(arg)
    if singleton and (singleton.is_group or
                      singleton.nargs != argparse.REMAINDER):
      arg = singleton
  if not arg.is_group:
    # A single argument.
    if arg.is_positional:
      usage = GetPositionalUsage(arg, markdown=markdown)
    else:
      if isinstance(arg, arg_parsers.StoreTrueFalseAction):
        inverted = InvertedValue.BOTH
      else:
        if not definition and getattr(arg, 'inverted_synopsis', False):
          inverted = InvertedValue.INVERTED
        else:
          inverted = InvertedValue.NORMAL
      usage = GetFlagUsage(arg, brief=brief, markdown=markdown,
                           inverted=inverted, value=value)
    if usage and top and not arg.is_required:
      usage = _MarkOptional(usage)
    return usage

  # An argument group.
  sep = ' | ' if arg.is_mutex else ' '
  positional_args = []
  required_usage = []
  optional_usage = []
  if remainder_usage is None:
    include_remainder_usage = True
    remainder_usage = []
  else:
    include_remainder_usage = False
  arguments = (
      sorted(arg.arguments, key=GetArgSortKey)
      if arg.sort_args else arg.arguments)
  for a in arguments:
    if a.is_hidden and not hidden:
      continue
    if a.is_group:
      singleton = GetSingleton(a)
      if singleton:
        a = singleton
    if not a.is_group and a.nargs == argparse.REMAINDER:
      remainder_usage.append(
          GetArgUsage(a, markdown=markdown, value=value, hidden=hidden))
    elif _IsPositional(a):
      positional_args.append(a)
    else:
      usage = GetArgUsage(a, markdown=markdown, value=value, hidden=hidden)
      if not usage:
        continue
      if a.is_required:
        if usage not in required_usage:
          required_usage.append(usage)
      else:
        if top:
          usage = _MarkOptional(usage)
        if usage not in optional_usage:
          optional_usage.append(usage)
  positional_usage = []
  all_other_usage = []
  nesting = 0
  optional_positionals = False
  if positional_args:
    nesting = 0
    for a in positional_args:
      usage = GetArgUsage(a, markdown=markdown, hidden=hidden)
      if not usage:
        continue
      if not a.is_required:
        optional_positionals = True
        usage_orig = usage
        usage = _MarkOptional(usage)
        if usage != usage_orig:
          nesting += 1
      positional_usage.append(usage)
    if nesting:
      positional_usage[-1] = '{}{}'.format(positional_usage[-1], ']' * nesting)
  if required_usage:
    all_other_usage.append(sep.join(required_usage))
  if optional_usage:
    if optional:
      if not top and (positional_args and not optional_positionals
                      or required_usage):
        all_other_usage.append(':')
      all_other_usage.append(sep.join(optional_usage))
    elif brief and top:
      all_other_usage.append('[optional flags]')
  if brief:
    all_usage = positional_usage + sorted(all_other_usage,
                                          key=_GetArgUsageSortKey)
  else:
    all_usage = positional_usage + all_other_usage
  if remainder_usage and include_remainder_usage:
    all_usage.append(' '.join(remainder_usage))
  usage = ' '.join(all_usage)
  if arg.is_required:
    return '({})'.format(usage)
  if not top and len(all_usage) > 1:
    usage = _MarkOptional(usage)
  return usage


def GetFlags(arg, optional=False):
  """Returns the list of all flags in arg.

  Args:
    arg: The argument to get flags from.
    optional: Do not include required flags if True.

  Returns:
    The list of all/optional flags in arg.
  """
  flags = set()
  if optional:
    flags.add('--help')

  def _GetFlagsHelper(arg, level=0, required=True):
    """GetFlags() helper that adds to flags."""
    if arg.is_hidden:
      return
    if arg.is_group:
      if level and required:
        # level==0 is always required
        required = arg.is_required
      for arg in arg.arguments:
        _GetFlagsHelper(arg, level=level + 1, required=required)
    else:
      show_inverted = getattr(arg, 'show_inverted', None)
      if show_inverted:
        arg = show_inverted
      # A singleton optional flag in a required group is technically required
      # but is treated as optional here. We shouldn't see this in practice.
      if (arg.option_strings and
          not arg.is_positional and
          not arg.is_global and
          (not optional or not required or not arg.is_required)):
        flags.add(sorted(arg.option_strings)[0])

  _GetFlagsHelper(arg)
  return sorted(flags, key=_GetArgUsageSortKey)


class Section(object):
  """A positional/flag section.

  Attribute:
    heading: str, The section heading.
    args: [Argument], The sorted list of args in the section.
  """

  def __init__(self, heading, args):
    self.heading = heading
    self.args = args


def GetArgSections(arguments, is_root, is_group, sort_top_level_args):
  """Returns the positional/flag sections in document order.

  Args:
    arguments: [Flag|Positional], The list of arguments for this command or
      group.
    is_root: bool, True if arguments are for the CLI root command.
    is_group: bool, True if arguments are for a command group.
    sort_top_level_args: bool, True if top level arguments should be sorted.

  Returns:
    ([Section] global_flags)
      global_flags - The sorted list of global flags if command is not the root.
  """
  categories = collections.OrderedDict()
  dests = set()
  global_flags = set()
  if not is_root and is_group:
    global_flags = {'--help'}
  for arg in arguments:
    if arg.is_hidden:
      continue
    if _IsPositional(arg):
      category = 'POSITIONAL ARGUMENTS'
      if category not in categories:
        categories[category] = []
      categories[category].append(arg)
      continue
    if arg.is_global and not is_root:
      for a in arg.arguments if arg.is_group else [arg]:
        if a.option_strings and not a.is_hidden:
          flag = a.option_strings[0]
          if not is_group and flag.startswith('--'):
            global_flags.add(flag)
      continue
    if arg.is_required:
      category = 'REQUIRED'
    else:
      category = getattr(arg, 'category', None) or 'OTHER'
    if hasattr(arg, 'dest'):
      if arg.dest in dests:
        continue
      dests.add(arg.dest)
    if category not in categories:
      categories[category] = []
    categories[category].append(arg)

  # Collect the priority sections first in order:
  #   POSITIONAL ARGUMENTS, REQUIRED, COMMON
  # Followed by uncategorized / categorized:
  # * If the top level args are sorted, just put uncategorized first followed by
  #   the remaining categories in alphabetical order.
  # * If the top level args shouldn't be sorted, then use the insertion order of
  #   categories so as to mirror the top level args order.
  sections = []
  if is_root:
    common = 'GLOBAL'
  else:
    common = base.COMMONLY_USED_FLAGS
  if sort_top_level_args:
    initial_categories = ['POSITIONAL ARGUMENTS', 'REQUIRED', common, 'OTHER']
    remaining_categories = sorted([
        c for c in categories if c not in initial_categories])
  else:
    initial_categories = ['POSITIONAL ARGUMENTS', 'REQUIRED', common]
    remaining_categories = [
        c for c in categories if c not in initial_categories]

  def _GetArgHeading(category):
    """Returns the arg section heading for an arg category."""
    if category == 'OTHER':
      # We can be more descriptive with the OTHER flags heading, depending on
      # what other categories are present.
      if set(remaining_categories) - set(['OTHER']):  # Additional categorized.
        other_flags_heading = 'FLAGS'
      elif common in categories:
        other_flags_heading = 'OTHER FLAGS'
      elif 'REQUIRED' in categories:
        other_flags_heading = 'OPTIONAL FLAGS'
      else:
        other_flags_heading = 'FLAGS'
      return other_flags_heading
    if 'ARGUMENTS' in category or 'FLAGS' in category:
      return category
    return category + ' FLAGS'

  for category in initial_categories + remaining_categories:
    if category not in categories:
      continue
    sections.append(Section(_GetArgHeading(category),
                            ArgumentWrapper(
                                arguments=categories[category],
                                sort_args=sort_top_level_args)))

  return sections, global_flags


def WrapWithPrefix(prefix, message, indent, length, spacing, writer=sys.stdout):
  """Helper function that does two-column writing.

  If the first column is too long, the second column begins on the next line.

  Args:
    prefix: str, Text for the first column.
    message: str, Text for the second column.
    indent: int, Width of the first column.
    length: int, Width of both columns, added together.
    spacing: str, Space to put on the front of prefix.
    writer: file-like, Receiver of the written output.
  """
  def W(s):
    writer.write(s)
  def Wln(s):
    W(s + '\n')

  # Reformat the message to be of rows of the correct width, which is what's
  # left-over from length when you subtract indent. The first line also needs
  # to begin with the indent, but that will be taken care of conditionally.
  message = ('\n%%%ds' % indent % ' ').join(
      textwrap.TextWrapper(break_on_hyphens=False, width=length - indent).wrap(
          message.replace(' | ', '&| '))).replace('&|', ' |')
  if len(prefix) > indent - len(spacing) - 2:
    # If the prefix is too long to fit in the indent width, start the message
    # on a new line after writing the prefix by itself.
    Wln('%s%s' % (spacing, prefix))
    # The message needs to have the first line indented properly.
    W('%%%ds' % indent % ' ')
    Wln(message)
  else:
    # If the prefix fits comfortably within the indent (2 spaces left-over),
    # print it out and start the message after adding enough whitespace to make
    # up the rest of the indent.
    W('%s%s' % (spacing, prefix))
    Wln('%%%ds %%s'
        % (indent - len(prefix) - len(spacing) - 1)
        % (' ', message))


def GetUsage(command, argument_interceptor):
  """Return the command Usage string.

  Args:
    command: calliope._CommandCommon, The command object that we're helping.
    argument_interceptor: parser_arguments.ArgumentInterceptor, the object that
      tracks all of the flags for this command or group.

  Returns:
    str, The command usage string.
  """
  command.LoadAllSubElements()
  command_path = ' '.join(command.GetPath())
  topic = len(command.GetPath()) >= 2 and command.GetPath()[1] == 'topic'
  command_id = 'topic' if topic else 'command'

  buf = io.StringIO()

  buf.write('Usage: ')

  usage_parts = []

  if not topic:
    usage_parts.append(GetArgUsage(argument_interceptor, brief=True,
                                   optional=False, top=True))

  group_helps = command.GetSubGroupHelps()
  command_helps = command.GetSubCommandHelps()

  groups = sorted(name for (name, help_info) in six.iteritems(group_helps)
                  if command.IsHidden() or not help_info.is_hidden)
  commands = sorted(name for (name, help_info) in six.iteritems(command_helps)
                    if command.IsHidden() or not help_info.is_hidden)

  all_subtypes = []
  if groups:
    all_subtypes.append('group')
  if commands:
    all_subtypes.append(command_id)
  if groups or commands:
    usage_parts.append('<%s>' % ' | '.join(all_subtypes))
    optional_flags = None
  else:
    optional_flags = GetFlags(argument_interceptor, optional=True)

  usage_msg = ' '.join(usage_parts)

  non_option = '{command} '.format(command=command_path)

  buf.write(non_option + usage_msg + '\n')

  if groups:
    WrapWithPrefix('group may be', ' | '.join(
        groups), HELP_INDENT, LINE_WIDTH, spacing='  ', writer=buf)
  if commands:
    WrapWithPrefix('%s may be' % command_id, ' | '.join(
        commands), HELP_INDENT, LINE_WIDTH, spacing='  ', writer=buf)
  if optional_flags:
    WrapWithPrefix('optional flags may be', ' | '.join(optional_flags),
                   HELP_INDENT, LINE_WIDTH, spacing='  ', writer=buf)

  buf.write('\n' + GetHelpHint(command))

  return buf.getvalue()


def GetCategoricalUsage(command, categories):
  """Constructs an alternative Usage markdown string organized into categories.

  The string is formatted as a series of tables; first, there's a table for
  each category of subgroups, next, there's a table for each category of
  subcommands. Each table element is printed under the category defined in the
  surface definition of the command or group with a short summary describing its
  functionality. In either set of tables (groups or commands), if there are no
  categories to display, there will be only be one table listing elements
  lexicographically. If both the sets of tables (groups and commands) have no
  categories to display, then an empty string is returned.

  Args:
    command: calliope._CommandCommon, The command object that we're helping.
    categories: A dictionary mapping category name to the set of elements
      belonging to that category.

  Returns:
    str, The command usage markdown string organized into categories.
  """

  command_key = 'command'
  command_group_key = 'command_group'

  def _WriteTypeUsageTextToBuffer(buf, categories, key_name):
    """Writes the markdown string to the buffer passed by reference."""
    single_category_is_other = False
    if len(categories[key_name]
          ) == 1 and base.UNCATEGORIZED_CATEGORY in categories[key_name]:
      single_category_is_other = True
    buf.write('\n\n')
    buf.write('# Available {type}s for {group}:\n'.format(
        type=' '.join(key_name.split('_')), group=' '.join(command.GetPath())))
    for category, elements in sorted(six.iteritems(categories[key_name])):
      if not single_category_is_other:
        buf.write('\n### {category}\n\n'.format(category=category))
      buf.write('---------------------- | ---\n')
      for element in sorted(elements, key=lambda e: e.name):
        short_help = None
        if element.name == 'alpha':
          short_help = element.short_help[10:]
        elif element.name == 'beta':
          short_help = element.short_help[9:]
        else:
          short_help = element.short_help
        buf.write('{name} | {description}\n'.format(
            name=element.name.replace('_', '-'), description=short_help))

  def _ShouldCategorize(categories):
    """Ensures the categorization has real categories and is not just all Uncategorized."""
    if not categories[command_key].keys(
    ) and not categories[command_group_key].keys():
      return False
    if set(
        list(categories[command_key].keys()) +
        list(categories[command_group_key].keys())) == set(
            [base.UNCATEGORIZED_CATEGORY]):
      return False
    return True

  if not _ShouldCategorize(categories):
    return ''

  buf = io.StringIO()
  if command_group_key in categories:
    _WriteTypeUsageTextToBuffer(buf, categories, command_group_key)
  if command_key in categories:
    _WriteTypeUsageTextToBuffer(buf, categories, command_key)
  return buf.getvalue()


def _WriteUncategorizedTable(command, elements, element_type, writer):
  """Helper method to GetUncategorizedUsage().

  The elements are written to a markdown table with a special heading. Element
  names are printed in the first column, and help snippet text is printed in the
  second. No categorization is performed.

  Args:
    command: calliope._CommandCommon, The command object that we're helping.
    elements: an iterable over backend.CommandCommon, The sub-elements that
      we're printing to the table.
    element_type: str, The type of elements we are dealing with. Usually
      'groups' or 'commands'.
    writer: file-like, Receiver of the written output.
  """
  writer.write('# Available {element_type} for {group}:\n'.format(
      element_type=element_type, group=' '.join(command.GetPath())))
  writer.write('---------------------- | ---\n')
  for element in sorted(elements, key=lambda e: e.name):
    if element.IsHidden():
      continue
    writer.write('{name} | {description}\n'.format(
        name=element.name.replace('_', '-'), description=element.short_help))


def GetUncategorizedUsage(command):
  """Constructs a Usage markdown string for uncategorized command groups.

  The string is formatted as two tables, one for the subgroups and one for the
  subcommands. Each sub-element is printed in its corresponding table together
  with a short summary describing its functionality.

  Args:
    command: calliope._CommandCommon, the command object that we're helping.

  Returns:
    str, The command Usage markdown string as described above.
  """
  buf = io.StringIO()
  if command.groups:
    _WriteUncategorizedTable(command, command.groups.values(), 'groups', buf)

  if command.commands:
    buf.write('\n')
    _WriteUncategorizedTable(
        command, command.commands.values(), 'commands', buf)

  return buf.getvalue()


def GetHelpHint(command):
  return """\
For detailed information on this command and its flags, run:
  {command_path} --help
""".format(command_path=' '.join(command.GetPath()))


def ExtractHelpStrings(docstring):
  """Extracts short help and long help from a docstring.

  If the docstring contains a blank line (i.e., a line consisting of zero or
  more spaces), everything before the first blank line is taken as the short
  help string and everything after it is taken as the long help string. The
  short help is flowing text with no line breaks, while the long help may
  consist of multiple lines, each line beginning with an amount of whitespace
  determined by dedenting the docstring.

  If the docstring does not contain a blank line, the sequence of words in the
  docstring is used as both the short help and the long help.

  Corner cases: If the first line of the docstring is empty, everything
  following it forms the long help, and the sequence of words of in the long
  help (without line breaks) is used as the short help. If the short help
  consists of zero or more spaces, None is used instead. If the long help
  consists of zero or more spaces, the short help (which might or might not be
  None) is used instead.

  Args:
    docstring: The docstring from which short and long help are to be taken

  Returns:
    a tuple consisting of a short help string and a long help string

  """
  if docstring:
    unstripped_doc_lines = docstring.splitlines()
    stripped_doc_lines = [s.strip() for s in unstripped_doc_lines]
    try:
      empty_line_index = stripped_doc_lines.index('')
      short_help = ' '.join(stripped_doc_lines[:empty_line_index])
      raw_long_help = '\n'.join(unstripped_doc_lines[empty_line_index + 1:])
      long_help = textwrap.dedent(raw_long_help).strip()
    except ValueError:  # no empty line in stripped_doc_lines
      short_help = ' '.join(stripped_doc_lines).strip()
      long_help = ''
    if not short_help:  # docstring started with a blank line
      short_help = ' '.join(stripped_doc_lines[empty_line_index + 1:]).strip()
      # words of long help as flowing text
    return (short_help, long_help or short_help)
  else:
    return ('', '')
