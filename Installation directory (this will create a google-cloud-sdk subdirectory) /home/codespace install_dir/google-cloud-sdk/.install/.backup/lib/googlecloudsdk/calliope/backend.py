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

"""Backend stuff for the calliope.cli module.

Not to be used by mortals.

"""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import argparse
import collections
import re
import textwrap

from googlecloudsdk.calliope import actions
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import command_loading
from googlecloudsdk.calliope import display
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.calliope import parser_arguments
from googlecloudsdk.calliope import parser_errors
from googlecloudsdk.calliope import parser_extensions
from googlecloudsdk.calliope import usage_text
from googlecloudsdk.calliope.concepts import handlers
from googlecloudsdk.core import log
from googlecloudsdk.core import metrics
from googlecloudsdk.core.util import text
import six


class _Notes(object):
  """Auto-generated NOTES section helper."""

  def __init__(self, explicit_notes=None):
    self._notes = []
    if explicit_notes:
      self._notes.append(explicit_notes.rstrip())
      self._paragraph = True
    else:
      self._paragraph = False

  def AddLine(self, line):
    """Adds a note line with preceding separator if not empty."""
    if not line:
      if line is None:
        return
    elif self._paragraph:
      self._paragraph = False
      self._notes.append('')
    self._notes.append(line.rstrip())

  def GetContents(self):
    """Returns the notes contents as a single string."""
    return '\n'.join(self._notes) if self._notes else None


class CommandCommon(object):
  """A base class for CommandGroup and Command.

  It is responsible for extracting arguments from the modules and does argument
  validation, since this is always the same for groups and commands.
  """

  def __init__(self, common_type, path, release_track, cli_generator,
               parser_group, allow_positional_args, parent_group):
    """Create a new CommandCommon.

    Args:
      common_type: base._Common, The actual loaded user written command or
        group class.
      path: [str], A list of group names that got us down to this command group
        with respect to the CLI itself.  This path should be used for things
        like error reporting when a specific element in the tree needs to be
        referenced.
      release_track: base.ReleaseTrack, The release track (ga, beta, alpha,
        preview) that this command group is in.  This will apply to all commands
        under it.
      cli_generator: cli.CLILoader, The builder used to generate this CLI.
      parser_group: argparse.Parser, The parser that this command or group will
        live in.
      allow_positional_args: bool, True if this command can have positional
        arguments.
      parent_group: CommandGroup, The parent of this command or group. None if
        at the root.
    """
    self.category = common_type.category
    self._parent_group = parent_group

    self.name = path[-1]
    # For the purposes of argparse and the help, we should use dashes.
    self.cli_name = self.name.replace('_', '-')
    log.debug('Loaded Command Group: %s', path)
    path[-1] = self.cli_name
    self._path = path
    self.dotted_name = '.'.join(path)
    self._cli_generator = cli_generator

    # pylint: disable=protected-access
    self._common_type = common_type
    self._common_type._cli_generator = cli_generator
    self._common_type._release_track = release_track

    self.is_group = any([t == base.Group for t in common_type.__mro__])

    if parent_group:
      # Propagate down the hidden attribute.
      if parent_group.IsHidden():
        self._common_type._is_hidden = True
      # Propagate down the universe compatible attribute.
      if (parent_group.IsUniverseCompatible() and
          self._common_type._universe_compatible is None):
        self._common_type._universe_compatible = True
      # Propagate down the unicode supported attribute.
      if parent_group.IsUnicodeSupported():
        self._common_type._is_unicode_supported = True
      # Propagate down notices from the deprecation decorator.
      if parent_group.Notices():
        for tag, msg in six.iteritems(parent_group.Notices()):
          self._common_type.AddNotice(tag, msg, preserve_existing=True)

    self.detailed_help = getattr(self._common_type, 'detailed_help', {})
    self._ExtractHelpStrings(self._common_type.__doc__)

    self._AssignParser(
        parser_group=parser_group,
        allow_positional_args=allow_positional_args)

  def Notices(self):
    """Gets the notices of this command or group."""
    return self._common_type.Notices()

  def ReleaseTrack(self):
    """Gets the release track of this command or group."""
    return self._common_type.ReleaseTrack()

  def IsHidden(self):
    """Gets the hidden status of this command or group."""
    return self._common_type.IsHidden()

  def IsUniverseCompatible(self):
    """Gets the universe compatible status of this command or group."""
    return self._common_type.IsUniverseCompatible()

  def IsUnicodeSupported(self):
    """Gets the unicode supported status of this command or group."""
    return self._common_type.IsUnicodeSupported()

  def IsRoot(self):
    """Returns True if this is the root element in the CLI tree."""
    return not self._parent_group

  def _TopCLIElement(self):
    """Gets the top group of this CLI."""
    if self.IsRoot():
      return self
    # pylint: disable=protected-access
    return self._parent_group._TopCLIElement()

  def _ExtractHelpStrings(self, docstring):
    """Extracts short help, long help and man page index from a docstring.

    Sets self.short_help, self.long_help and self.index_help and adds release
    track tags if needed.

    Args:
      docstring: The docstring from which short and long help are to be taken
    """
    self.short_help, self.long_help = usage_text.ExtractHelpStrings(docstring)

    if 'brief' in self.detailed_help:
      self.short_help = re.sub(r'\s', ' ', self.detailed_help['brief']).strip()
    if self.short_help and not self.short_help.endswith('.'):
      self.short_help += '.'

    # Append any notice messages to command description and long_help
    if self.Notices():
      all_notices = ('\n\n' +
                     '\n\n'.join(sorted(self.Notices().values())) +
                     '\n\n')
      description = self.detailed_help.get('DESCRIPTION')
      if description:
        self.detailed_help = dict(self.detailed_help)  # make a shallow copy
        self.detailed_help['DESCRIPTION'] = (all_notices +
                                             textwrap.dedent(description))
      if self.short_help == self.long_help:
        self.long_help += all_notices
      else:
        self.long_help = self.short_help + all_notices + self.long_help

    self.index_help = self.short_help
    if len(self.index_help) > 1:
      if self.index_help[0].isupper() and not self.index_help[1].isupper():
        self.index_help = self.index_help[0].lower() + self.index_help[1:]
      if self.index_help[-1] == '.':
        self.index_help = self.index_help[:-1]

    tags = []
    tag = self.ReleaseTrack().help_tag
    if tag:
      tags.append(tag)
    if self.Notices():
      tags.extend(sorted(self.Notices().keys()))
    if tags:
      tag = ' '.join(tags) + ' '

      def _InsertTag(txt):
        return re.sub(r'^(\s*)', r'\1' + tag, txt)

      self.short_help = _InsertTag(self.short_help)
      # If long_help starts with section markdown then it's not the implicit
      # DESCRIPTION section and shouldn't have a tag inserted.
      if not self.long_help.startswith('#'):
        self.long_help = _InsertTag(self.long_help)

      # No need to tag DESCRIPTION if it starts with {description} or {index}
      # because they are already tagged.
      description = self.detailed_help.get('DESCRIPTION')
      if description and not re.match(r'^[ \n]*\{(description|index)\}',
                                      description):
        self.detailed_help = dict(self.detailed_help)  # make a shallow copy
        self.detailed_help['DESCRIPTION'] = _InsertTag(
            textwrap.dedent(description))

  def GetNotesHelpSection(self, contents=None):
    """Returns the NOTES section with explicit and generated help."""
    if not contents:
      contents = self.detailed_help.get('NOTES')
    notes = _Notes(contents)
    if self.IsHidden():
      notes.AddLine('This command is an internal implementation detail and may '
                    'change or disappear without notice.')
    notes.AddLine(self.ReleaseTrack().help_note)
    alternates = self.GetExistingAlternativeReleaseTracks()
    if alternates:
      notes.AddLine('{} also available:'.format(
          text.Pluralize(
              len(alternates), 'This variant is', 'These variants are')))
      notes.AddLine('')
      for alternate in alternates:
        notes.AddLine('  $ ' + alternate)
        notes.AddLine('')
    return notes.GetContents()

  def _AssignParser(self, parser_group, allow_positional_args):
    """Assign a parser group to model this Command or CommandGroup.

    Args:
      parser_group: argparse._ArgumentGroup, the group that will model this
          command or group's arguments.
      allow_positional_args: bool, Whether to allow positional args for this
          group or not.

    """
    if not parser_group:
      # This is the root of the command tree, so we create the first parser.
      self._parser = parser_extensions.ArgumentParser(
          description=self.long_help,
          add_help=False,
          prog=self.dotted_name,
          calliope_command=self)
    else:
      # This is a normal sub group, so just add a new subparser to the existing
      # one.
      self._parser = parser_group.add_parser(
          self.cli_name,
          help=self.short_help,
          description=self.long_help,
          add_help=False,
          prog=self.dotted_name,
          calliope_command=self)

    self._sub_parser = None

    self.ai = parser_arguments.ArgumentInterceptor(
        parser=self._parser,
        is_global=not parser_group,
        cli_generator=self._cli_generator,
        allow_positional=allow_positional_args)

    self.ai.add_argument(
        '-h', action=actions.ShortHelpAction(self),
        is_replicated=True,
        category=base.COMMONLY_USED_FLAGS,
        help='Print a summary help and exit.')
    self.ai.add_argument(
        '--help', action=actions.RenderDocumentAction(self, '--help'),
        is_replicated=True,
        category=base.COMMONLY_USED_FLAGS,
        help='Display detailed help.')
    self.ai.add_argument(
        '--document', action=actions.RenderDocumentAction(self),
        is_replicated=True,
        nargs=1,
        metavar='ATTRIBUTES',
        type=arg_parsers.ArgDict(),
        hidden=True,
        help='THIS TEXT SHOULD BE HIDDEN')

    self._AcquireArgs()

  def IsValidSubPath(self, command_path):
    """Determines if the given sub command path is valid from this node.

    Args:
      command_path: [str], The pieces of the command path.

    Returns:
      True, if the given path parts exist under this command or group node.
      False, if the sub path does not lead to a valid command or group.
    """
    current = self
    for part in command_path:
      current = current.LoadSubElement(part)
      if not current:
        return False
    return True

  def AllSubElements(self):
    """Gets all the sub elements of this group.

    Returns:
      set(str), The names of all sub groups or commands under this group.
    """
    return []

  # pylint: disable=unused-argument
  def LoadAllSubElements(self, recursive=False, ignore_load_errors=False):
    """Load all the sub groups and commands of this group.

    Args:
      recursive: bool, True to continue loading all sub groups, False, to just
        load the elements under the group.
      ignore_load_errors: bool, True to ignore command load failures. This
        should only be used when it is not critical that all data is returned,
        like for optimizations like static tab completion.

    Returns:
      int, The total number of elements loaded.
    """
    return 0

  def LoadSubElement(self, name, allow_empty=False,
                     release_track_override=None):
    """Load a specific sub group or command.

    Args:
      name: str, The name of the element to load.
      allow_empty: bool, True to allow creating this group as empty to start
        with.
      release_track_override: base.ReleaseTrack, Load the given sub-element
        under the given track instead of that of the parent. This should only
        be used when specifically creating the top level release track groups.

    Returns:
      _CommandCommon, The loaded sub element, or None if it did not exist.
    """
    pass

  def LoadSubElementByPath(self, path):
    """Load a specific sub group or command by path.

    If path is empty, returns the current element.

    Args:
      path: list of str, The names of the elements to load down the hierarchy.

    Returns:
      _CommandCommon, The loaded sub element, or None if it did not exist.
    """
    curr = self
    for part in path:
      curr = curr.LoadSubElement(part)
      if curr is None:
        return None
    return curr

  def GetPath(self):
    return self._path

  def GetUsage(self):
    return usage_text.GetUsage(self, self.ai)

  def GetSubCommandHelps(self):
    return {}

  def GetSubGroupHelps(self):
    return {}

  def _AcquireArgs(self):
    """Calls the functions to register the arguments for this module."""
    # A Command subclass can define a _Flags() method.
    self._common_type._Flags(self.ai)  # pylint: disable=protected-access
    # A command implementation can optionally define an Args() method.
    self._common_type.Args(self.ai)

    if self._parent_group:
      # Add parent arguments to the list of all arguments.
      for arg in self._parent_group.ai.arguments:
        self.ai.arguments.append(arg)
      # Add parent concepts to children, if they aren't represented already
      if self._parent_group.ai.concept_handler:
        if not self.ai.concept_handler:
          self.ai.add_concepts(handlers.RuntimeHandler())
        # pylint: disable=protected-access
        for concept_details in self._parent_group.ai.concept_handler._all_concepts:
          try:
            self.ai.concept_handler.AddConcept(**concept_details)
          except handlers.RepeatedConceptName:
            raise parser_errors.ArgumentException(
                'repeated concept in {command}: {concept_name}'.format(
                    command=self.dotted_name,
                    concept_name=concept_details['name']))
      # Add parent flags to children, if they aren't represented already
      for flag in self._parent_group.GetAllAvailableFlags():
        if flag.is_replicated:
          # Each command or group gets its own unique help flags.
          continue
        if flag.do_not_propagate:
          # Don't propagate down flags that only apply to the group but not to
          # subcommands.
          continue
        if flag.is_required:
          # It is not easy to replicate required flags to subgroups and
          # subcommands, since then there would be two+ identical required
          # flags, and we'd want only one of them to be necessary.
          continue
        try:
          self.ai.AddFlagActionFromAncestors(flag)
        except argparse.ArgumentError:
          raise parser_errors.ArgumentException(
              'repeated flag in {command}: {flag}'.format(
                  command=self.dotted_name,
                  flag=flag.option_strings))
      # Update parent display_info in children, children take precedence.
      self.ai.display_info.AddLowerDisplayInfo(
          self._parent_group.ai.display_info)

  def GetAllAvailableFlags(self, include_global=True, include_hidden=True):
    flags = self.ai.flag_args + self.ai.ancestor_flag_args
    # TODO(b/35983142): Use mutant disable decorator when its available.
    # This if statement triggers a mutant. Currently there are no Python comment
    # decorators to disable individual mutants. This statement is a semantic
    # mutant space/time optimization (if the list in hand is OK then use it),
    # and the mutant scanner can't detect those in a reasonable amount of time.
    if include_global and include_hidden:
      return flags
    return [f for f in flags if
            (include_global or not f.is_global) and
            (include_hidden or not f.is_hidden)]

  def GetSpecificFlags(self, include_hidden=True):
    flags = self.ai.flag_args
    if include_hidden:
      return flags
    return [f for f in flags if not f.hidden]

  def GetExistingAlternativeReleaseTracks(self, value=None):
    """Gets the names for the command in other release tracks.

    Args:
      value: str, Optional value being parsed after the command.

    Returns:
      [str]: The names for the command in other release tracks.
    """
    existing_alternatives = []
    # Get possible alternatives.
    path = self.GetPath()
    if value:
      path.append(value)
    alternates = self._cli_generator.ReplicateCommandPathForAllOtherTracks(path)
    # See if the command is actually enabled in any of those alternative tracks.
    if alternates:
      top_element = self._TopCLIElement()
      # Pre-sort by the release track prefix so GA commands always list first.
      for _, command_path in sorted(six.iteritems(alternates),
                                    key=lambda x: x[0].prefix or ''):
        alternative_cmd = top_element.LoadSubElementByPath(command_path[1:])
        if alternative_cmd and not alternative_cmd.IsHidden():
          existing_alternatives.append(' '.join(command_path))
    return existing_alternatives


class CommandGroup(CommandCommon):
  """A class to encapsulate a group of commands."""

  def __init__(self, impl_paths, path, release_track, construction_id,
               cli_generator, parser_group, parent_group=None,
               allow_empty=False):
    """Create a new command group.

    Args:
      impl_paths: [str], A list of file paths to the command implementation for
        this group.
      path: [str], A list of group names that got us down to this command group
        with respect to the CLI itself.  This path should be used for things
        like error reporting when a specific element in the tree needs to be
        referenced.
      release_track: base.ReleaseTrack, The release track (ga, beta, alpha) that
        this command group is in.  This will apply to all commands under it.
      construction_id: str, A unique identifier for the CLILoader that is
        being constructed.
      cli_generator: cli.CLILoader, The builder used to generate this CLI.
      parser_group: the current argparse parser, or None if this is the root
        command group.  The root command group will allocate the initial
        top level argparse parser.
      parent_group: CommandGroup, The parent of this group. None if at the
        root.
      allow_empty: bool, True to allow creating this group as empty to start
        with.

    Raises:
      LayoutException: if the module has no sub groups or commands
    """
    common_type = command_loading.LoadCommonType(
        impl_paths, path, release_track, construction_id, is_command=False)
    super(CommandGroup, self).__init__(
        common_type,
        path=path,
        release_track=release_track,
        cli_generator=cli_generator,
        allow_positional_args=False,
        parser_group=parser_group,
        parent_group=parent_group)

    self._construction_id = construction_id

    # find sub groups and commands
    self.groups = {}
    self.commands = {}
    self._groups_to_load = {}
    self._commands_to_load = {}
    self._unloadable_elements = set()

    group_infos, command_infos = command_loading.FindSubElements(impl_paths,
                                                                 path)
    self._groups_to_load.update(group_infos)
    self._commands_to_load.update(command_infos)

    if (not allow_empty and
        not self._groups_to_load and not self._commands_to_load):
      raise command_loading.LayoutException(
          'Group {0} has no subgroups or commands'.format(self.dotted_name))
    # Initialize the sub-parser so sub groups can be found.
    self.SubParser()

  def CopyAllSubElementsTo(self, other_group, ignore):
    """Copies all the sub groups and commands from this group to the other.

    Args:
      other_group: CommandGroup, The other group to populate.
      ignore: set(str), Names of elements not to copy.
    """
    # pylint: disable=protected-access, This is the same class.
    other_group._groups_to_load.update(
        {name: impl_paths
         for name, impl_paths in six.iteritems(self._groups_to_load)
         if name not in ignore})
    other_group._commands_to_load.update(
        {name: impl_paths
         for name, impl_paths in six.iteritems(self._commands_to_load)
         if name not in ignore})

  def SubParser(self):
    """Gets or creates the argparse sub parser for this group.

    Returns:
      The argparse subparser that children of this group should register with.
          If a sub parser has not been allocated, it is created now.
    """
    if not self._sub_parser:
      # pylint: disable=protected-access
      self._sub_parser = self._parser.add_subparsers(
          action=parser_extensions.CommandGroupAction,
          calliope_command=self)
    return self._sub_parser

  def AllSubElements(self):
    """Gets all the sub elements of this group.

    Returns:
      set(str), The names of all sub groups or commands under this group.
    """
    return (set(self._groups_to_load.keys()) |
            set(self._commands_to_load.keys()))

  def IsValidSubElement(self, name):
    """Determines if the given name is a valid sub group or command.

    Args:
      name: str, The name of the possible sub element.

    Returns:
      bool, True if the name is a valid sub element of this group.
    """
    return bool(self.LoadSubElement(name))

  def LoadAllSubElements(self, recursive=False, ignore_load_errors=False):
    """Load all the sub groups and commands of this group.

    Args:
      recursive: bool, True to continue loading all sub groups, False, to just
        load the elements under the group.
      ignore_load_errors: bool, True to ignore command load failures. This
        should only be used when it is not critical that all data is returned,
        like for optimizations like static tab completion.

    Returns:
      int, The total number of elements loaded.
    """
    total = 0
    for name in self.AllSubElements():
      try:
        element = self.LoadSubElement(name)
        total += 1
      # pylint:disable=bare-except, We are in a mode where accuracy doesn't
      # matter. Just ignore any errors in loading a command.
      except:
        element = None
        if not ignore_load_errors:
          raise
      if element and recursive:
        total += element.LoadAllSubElements(
            recursive=recursive, ignore_load_errors=ignore_load_errors)
    return total

  def LoadSubElement(self, name, allow_empty=False,
                     release_track_override=None):
    """Load a specific sub group or command.

    Args:
      name: str, The name of the element to load.
      allow_empty: bool, True to allow creating this group as empty to start
        with.
      release_track_override: base.ReleaseTrack, Load the given sub-element
        under the given track instead of that of the parent. This should only
        be used when specifically creating the top level release track groups.

    Returns:
      _CommandCommon, The loaded sub element, or None if it did not exist.
    """
    name = name.replace('-', '_')

    # See if this element has already been loaded.
    existing = self.groups.get(name, None)
    if not existing:
      existing = self.commands.get(name, None)
    if existing:
      return existing
    if name in self._unloadable_elements:
      return None

    element = None
    try:
      if name in self._groups_to_load:
        element = CommandGroup(
            self._groups_to_load[name], self._path + [name],
            release_track_override or self.ReleaseTrack(),
            self._construction_id, self._cli_generator, self.SubParser(),
            parent_group=self, allow_empty=allow_empty)
        self.groups[element.name] = element
      elif name in self._commands_to_load:
        element = Command(
            self._commands_to_load[name], self._path + [name],
            release_track_override or self.ReleaseTrack(),
            self._construction_id, self._cli_generator, self.SubParser(),
            parent_group=self)
        self.commands[element.name] = element
    except command_loading.ReleaseTrackNotImplementedException as e:
      self._unloadable_elements.add(name)
      log.debug(e)
    return element

  def GetSubCommandHelps(self):
    return dict(
        (item.cli_name,
         usage_text.HelpInfo(help_text=item.short_help,
                             is_hidden=item.IsHidden(),
                             release_track=item.ReleaseTrack))
        for item in self.commands.values())

  def GetSubGroupHelps(self):
    return dict(
        (item.cli_name,
         usage_text.HelpInfo(help_text=item.short_help,
                             is_hidden=item.IsHidden(),
                             release_track=item.ReleaseTrack()))
        for item in self.groups.values())

  def RunGroupFilter(self, context, args):
    """Constructs and runs the Filter() method of all parent groups.

    This recurses up to the root group and then constructs each group and runs
    its Filter() method down the tree.

    Args:
      context: {}, The context dictionary that Filter() can modify.
      args: The argparse namespace.
    """
    if self._parent_group:
      self._parent_group.RunGroupFilter(context, args)
    self._common_type().Filter(context, args)

  def GetCategoricalUsage(self):
    return usage_text.GetCategoricalUsage(
        self, self._GroupSubElementsByCategory())

  def GetUncategorizedUsage(self):
    return usage_text.GetUncategorizedUsage(self)

  def GetHelpHint(self):
    return usage_text.GetHelpHint(self)

  def _GroupSubElementsByCategory(self):
    """Returns dictionary mapping each category to its set of subelements."""

    def _GroupSubElementsOfSameTypeByCategory(elements):
      """Returns dictionary mapping specific to element type."""
      categorized_dict = collections.defaultdict(set)
      for element in elements.values():
        if not element.IsHidden():
          if element.category:
            categorized_dict[element.category].add(element)
          else:
            categorized_dict[base.UNCATEGORIZED_CATEGORY].add(element)
      return categorized_dict

    self.LoadAllSubElements()
    categories = {}
    categories['command'] = (
        _GroupSubElementsOfSameTypeByCategory(self.commands))
    categories['command_group'] = (
        _GroupSubElementsOfSameTypeByCategory(self.groups))

    return categories


class Command(CommandCommon):
  """A class that encapsulates the configuration for a single command."""

  def __init__(self, impl_paths, path, release_track, construction_id,
               cli_generator, parser_group, parent_group=None):
    """Create a new command.

    Args:
      impl_paths: [str], A list of file paths to the command implementation for
        this command.
      path: [str], A list of group names that got us down to this command
        with respect to the CLI itself.  This path should be used for things
        like error reporting when a specific element in the tree needs to be
        referenced.
      release_track: base.ReleaseTrack, The release track (ga, beta, alpha) that
        this command group is in.  This will apply to all commands under it.
      construction_id: str, A unique identifier for the CLILoader that is
        being constructed.
      cli_generator: cli.CLILoader, The builder used to generate this CLI.
      parser_group: argparse.Parser, The parser to be used for this command.
      parent_group: CommandGroup, The parent of this command.
    """
    common_type = command_loading.LoadCommonType(
        impl_paths, path, release_track, construction_id, is_command=True,
        yaml_command_translator=cli_generator.yaml_command_translator)
    super(Command, self).__init__(
        common_type,
        path=path,
        release_track=release_track,
        cli_generator=cli_generator,
        allow_positional_args=True,
        parser_group=parser_group,
        parent_group=parent_group)

    self._parser.set_defaults(calliope_command=self, command_path=self._path)

  def Run(self, cli, args):
    """Run this command with the given arguments.

    Args:
      cli: The cli.CLI object for this command line tool.
      args: The arguments for this command as a namespace.

    Returns:
      The object returned by the module's Run() function.

    Raises:
      exceptions.Error: if thrown by the Run() function.
      exceptions.ExitCodeNoError: if the command is returning with a non-zero
        exit code.
    """
    metrics.Loaded()

    tool_context = {}
    if self._parent_group:
      self._parent_group.RunGroupFilter(tool_context, args)

    command_instance = self._common_type(cli=cli, context=tool_context)

    base.LogCommand(self.dotted_name, args)
    resources = command_instance.Run(args)
    resources = display.Displayer(command_instance, args, resources,
                                  display_info=self.ai.display_info).Display()
    metrics.Ran()

    if command_instance.exit_code != 0:
      raise exceptions.ExitCodeNoError(exit_code=command_instance.exit_code)

    return resources
