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

"""Calliope argparse intercepts and extensions.

Calliope uses the argparse module for command line argument definition and
parsing. It intercepts some argparse methods to provide enhanced runtime help
document generation, command line usage help, error handling and argument group
conflict analysis.

The parser and intercepts are in these modules:

  parser_extensions (this module)

    Extends and intercepts argparse.ArgumentParser and the parser args
    namespace to support Command.Run() method access to info added in the
    Command.Args() method.

  parser_arguments

    Intercepts the basic argument objects and collects data for command flag
    metrics reporting.

  parser_errors

    Error/exception classes for all Calliope arg parse errors. Errors derived
    from ArgumentError have a payload used for metrics reporting.

Intercepted argument definitions for a command and all its ancestor command
groups are kept in a tree of ArgumentInterceptor nodes. Inner nodes have
is_group==True and an arguments list of child nodes. Leaf nodes have
is_group==False. ArgumentInterceptor keeps track of the arguments and flags
specified on the command line in a set that is queried to verify the specified
arguments against their definitions. For example, that a required argument has
been specified, or that at most one flag in a mutually exclusive group has been
specified.

The collected info is also used to generate help markdown documents. The
markdown is annotated with extra text that collates and describes argument
attributes and groupings. For example, mutually exclusive, required, and nested
groups.

The intercepted args namespace object passed to the Command.Run() method adds
methods to access/modify info collected during the parse.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import abc
import argparse
import collections
import io
import itertools
import os
import re
import sys

from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base  # pylint: disable=unused-import
from googlecloudsdk.calliope import parser_arguments
from googlecloudsdk.calliope import parser_errors
from googlecloudsdk.calliope import suggest_commands
from googlecloudsdk.calliope import usage_text
from googlecloudsdk.core import argv_utils
from googlecloudsdk.core import config
from googlecloudsdk.core import log
from googlecloudsdk.core import metrics
from googlecloudsdk.core.console import console_attr
from googlecloudsdk.core.console import console_io
from googlecloudsdk.core.document_renderers import render_document
from googlecloudsdk.core.updater import update_manager
import six


_HELP_SEARCH_HINT = """\
To search the help text of gcloud commands, run:
  gcloud help -- SEARCH_TERMS"""


class Namespace(argparse.Namespace):
  """A custom subclass for parsed args.

  Attributes:
    _deepest_parser: ArgumentParser, The deepest parser for the last command
      part.
    _parsers: ArgumentParser, The list of all parsers for the command.
    _specified_args: {dest: arg-name}, A map of dest names for known args
      specified on the command line to arg names that have been scrubbed for
      metrics. This dict accumulate across all subparsers.
  """

  def __init__(self, **kwargs):
    self._deepest_parser = None
    self._parsers = []
    self._specified_args = {}
    super(Namespace, self).__init__(**kwargs)

  def _SetParser(self, parser):
    """Sets the parser for the first part of the command."""
    self._deepest_parser = parser

  def _GetParser(self):
    """Returns the deepest parser for the command."""
    return self._deepest_parser

  def _GetCommand(self):
    """Returns the command for the deepest parser."""
    # pylint: disable=protected-access
    return self._GetParser()._calliope_command

  def _Execute(self, command, call_arg_complete=False):
    """Executes command in the current CLI.

    Args:
      command: A list of command args to execute.
      call_arg_complete: Enable arg completion if True.

    Returns:
      Returns the list of resources from the command.
    """
    call_arg_complete = False
    # pylint: disable=protected-access
    return self._GetCommand()._cli_generator.Generate().Execute(
        command, call_arg_complete=call_arg_complete)

  def GetDisplayInfo(self):
    """Returns the parser display_info."""
    # pylint: disable=protected-access
    return self._GetCommand().ai.display_info

  @property
  def CONCEPTS(self):  # pylint: disable=invalid-name
    """The holder for concepts v1 arguments."""
    handler = self._GetCommand().ai.concept_handler
    if handler is None:
      return handler
    handler.parsed_args = self
    return handler

  @property
  def CONCEPT_ARGS(self):  # pylint: disable=invalid-name
    """The holder for concepts v2 arguments."""
    handler = self._GetCommand().ai.concepts
    if handler is None:
      return handler
    handler.parsed_args = self
    return handler

  def GetSpecifiedArgNames(self):
    """Returns the scrubbed names for args specified on the command line.

    For example,

      `$ {command} positional_value --foo=bar, --lorem-ipsum=hello`

    returns ['POSITIONAL_NAME', '--foo', '--lorem-ipsum'].
    """
    return sorted(self._specified_args.values())

  def GetSpecifiedArgs(self):
    """Gets the argument names and values that were actually specified.

    For example,

      `$ {command} positional_value --foo=bar, --lorem-ipsum=1,2,3`

    returns
      {
        'POSITIONAL_NAME': 'positional_value'
        '--foo': 'bar',
        '--lorem-ipsum': [1,2,3],
      }

    In the returned dictionary, the keys are the specified arguments, including
    positional argument names and flag names, in string type; the corresponding
    values are the user-specified flag values, converted according to the type
    defined by each flag.

    Returns:
      {str: any}, A mapping of argument name to value.
    """
    return {
        name: getattr(self, dest, 'UNKNOWN')
        for dest, name in six.iteritems(self._specified_args)
    }

  def GetSpecifiedArgsDict(self):
    """Returns the _specified_args dictionary.

    For example,

      $ {command} positional_value --foo=bar, --lorem-ipsum=hello --async,

    returns
      {
        'positional_name', 'POSITIONAL_NAME'
        'foo': '--foo',
        'lorem_ipsum': '--lorem-ipsum',
        'async_': '--async',
      }.

    In the returned dictionary, the keys are destinations in the argparse
    namespace object.

    In the above example, the destination of `--async` is set to 'async_' in its
    flag definition, other flags use underscore separated flag names as their
    default destinations.
    """
    return self._specified_args

  def IsSpecified(self, dest):
    """Returns True if args.dest was specified on the command line.

    Args:
      dest: str, The dest name for the arg to check.

    Raises:
      UnknownDestinationException: If there is no registered arg for dest.

    Returns:
      True if args.dest was specified on the command line.
    """
    if not hasattr(self, dest):
      raise parser_errors.UnknownDestinationException(
          'No registered arg for destination [{}].'.format(dest))
    return dest in self._specified_args

  def IsKnownAndSpecified(self, dest):
    """Returns True if dest is a known and args.dest was specified.

    Args:
      dest: str, The dest name for the arg to check.

    Returns:
      True if args.dest is a known argument was specified on the command line.
    """
    return hasattr(self, dest) and (dest in self._specified_args)

  def GetFlagArgument(self, name):
    """Returns the flag argument object for name.

    Args:
      name: The flag name or Namespace destination.

    Raises:
      UnknownDestinationException: If there is no registered flag arg for name.

    Returns:
      The flag argument object for name.
    """
    if name.startswith('--'):
      dest = name[2:].replace('-', '_')
      flag = name
    else:
      dest = name
      flag = '--' + name.replace('_', '-')
    ai = self._GetCommand().ai
    for arg in ai.flag_args + ai.ancestor_flag_args:
      if (dest == arg.dest or
          arg.option_strings and flag == arg.option_strings[0]):
        return arg
    raise parser_errors.UnknownDestinationException(
        'No registered flag arg for [{}].'.format(name))

  def GetPositionalArgument(self, name):
    """Returns the positional argument object for name.

    Args:
      name: The Namespace metavar or destination.

    Raises:
      UnknownDestinationException: If there is no registered positional arg
        for name.

    Returns:
      The positional argument object for name.
    """
    dest = name.replace('-', '_').lower()
    meta = name.replace('-', '_').upper()
    for arg in self._GetCommand().ai.positional_args:
      if isinstance(arg, type):
        continue
      if dest == arg.dest or meta == arg.metavar:
        return arg
    raise parser_errors.UnknownDestinationException(
        'No registered positional arg for [{}].'.format(name))

  def GetFlag(self, dest):
    """Returns the flag name registered to dest or None is dest is a positional.

    Args:
      dest: The dest of a registered argument.

    Raises:
      UnknownDestinationException: If no arg is registered for dest.

    Returns:
      The flag name registered to dest or None if dest is a positional.
    """
    arg = self.GetFlagArgument(dest)
    return arg.option_strings[0] if arg.option_strings else None

  def GetValue(self, dest):
    """Returns the value of the argument registered for dest.

    Args:
      dest: The dest of a registered argument.

    Raises:
      UnknownDestinationException: If no arg is registered for dest.

    Returns:
      The value of the argument registered for dest.
    """
    try:
      return getattr(self, dest)
    except AttributeError:
      raise parser_errors.UnknownDestinationException(
          'No registered arg for destination [{}].'.format(dest))

  def MakeGetOrRaise(self, flag_name):
    """Returns a function to get given flag value or raise if it is not set.

    This is useful when given flag becomes required when another flag
    is present.

    Args:
      flag_name: str, The flag_name name for the arg to check.

    Raises:
      parser_errors.RequiredError: if flag is not specified.
      UnknownDestinationException: If there is no registered arg for flag_name.

    Returns:
      Function for accessing given flag value.
    """
    def _Func():
      flag = flag_name[2:] if flag_name.startswith('--') else flag_name
      flag_value = getattr(self, flag)
      if flag_value is None and not self.IsSpecified(flag):
        raise parser_errors.RequiredError(argument=flag_name)
      return flag_value

    return _Func


class _ErrorContext(object):
  """Context from the most recent ArgumentParser.error() call.

  The context can be saved and used to reproduce the error() method call later
  in the execution.  Used to probe argparse errors for different argument
  combinations.

  Attributes:
    message: The error message string.
    parser: The parser where the error occurred.
    error: The exception error value.
  """

  def __init__(self, message, parser, error):
    self.message = re.sub(r"\bu'", "'", message)
    self.parser = parser
    self.error = error
    self.flags_locations = parser.flags_locations

  def AddLocations(self, arg):
    """Adds locaton info from context for arg if specified."""
    locations = self.flags_locations.get(arg)
    if locations:
      arg = '{} ({})'.format(arg, ','.join(sorted(locations)))
    return arg


class _HandleLaterError(Exception):
  """Error to be handled in a subsequent call to self.error.

  This error exists to provide a way to break out of self.error so that we can
  deduce a better error later; it will always be caught in parser_extensions and
  never surfaced as a user-facing error (at least in theory; if that does happen
  then it's a bug.)
  """
  pass


class ArgumentParser(argparse.ArgumentParser):
  """A custom subclass for arg parsing behavior.

  This overrides the default argparse parser.

  Attributes:
    _args: Original argv passed to argparse.
    _calliope_command: base._Command, The Calliope command or group for this
      parser.
    _error_context: The most recent self.error() method _ErrorContext.
    _is_group: bool, True if _calliope_command is a group.
    _probe_error: bool, True when parse_known_args() is probing argparse errors
      captured in the self.error() method.
    _remainder_action: action, The argument action for a -- ... remainder
      argument, added by AddRemainderArgument.
    _specified_args: {dest: arg-name}, A map of dest names for known args
      specified on the command line to arg names that have been scrubbed for
      metrics. This value is initialized and propagated to the deepest parser
      namespace in parse_known_args() from specified args collected in
      _get_values().
      raise_error: This is set to true if we want to raise an exception for
      errors.
  """

  _args = None

  def __init__(self, *args, **kwargs):
    self._calliope_command = kwargs.pop('calliope_command')
    # Would rather isinstance(self._calliope_command, CommandGroup) here but
    # that would introduce a circular dependency on calliope.backend.
    self._is_group = hasattr(self._calliope_command, 'commands')
    self._remainder_action = None
    self._specified_args = {}
    self._error_context = None
    self._probe_error = False
    self.flags_locations = collections.defaultdict(set)
    self.raise_error = False
    super(ArgumentParser, self).__init__(*args, **kwargs)

  def _Error(self, error):
    # self.error() wraps the standard argparse error() method.
    self.error(context=_ErrorContext(console_attr.SafeText(error), self, error))

  def AddRemainderArgument(self, *args, **kwargs):
    """Add an argument representing '--' followed by anything.

    This argument is bound to the parser, so the parser can use its helper
    methods to parse.

    Args:
      *args: The arguments for the action.
      **kwargs: They keyword arguments for the action.

    Raises:
      ArgumentException: If there already is a Remainder Action bound to this
      parser.

    Returns:
      The created action.
    """
    if self._remainder_action:
      self._Error(parser_errors.ArgumentException(
          'There can only be one pass through argument.'))
    kwargs['action'] = arg_parsers.RemainderAction
    # pylint:disable=protected-access
    self._remainder_action = self.add_argument(*args, **kwargs)
    return self._remainder_action

  def GetSpecifiedArgNames(self):
    """Returns the scrubbed names for args specified on the command line."""
    return sorted(self._specified_args.values())

  def _AddLocations(self, arg, value=None):
    """Adds file and line info from context for arg if specified."""
    if value and '=' not in arg:
      argval = '{}={}'.format(arg, value)
    else:
      argval = arg
    locations = self.flags_locations.get(argval)
    if locations:
      arg = '{} ({})'.format(argval, ','.join(sorted(locations)))
    return arg

  def _Suggest(self, unknown_args):
    """Error out with a suggestion based on text distance for each unknown."""
    messages = []
    suggester = usage_text.TextChoiceSuggester()
    # pylint:disable=protected-access, This is an instance of this class.
    for flag in self._calliope_command.GetAllAvailableFlags(
        include_hidden=False):
      options = flag.option_strings
      if options:
        # This is a flag, add all its names as choices.
        suggester.AddChoices(options)
        # Add any aliases as choices as well, but suggest the primary name.
        aliases = getattr(flag, 'suggestion_aliases', None)
        if aliases:
          suggester.AddAliases(aliases, options[0])

    suggestions = {}
    for arg in unknown_args:
      # Only do this for flag names.
      if not isinstance(arg, six.string_types):
        continue
      # Strip the flag value if any from the suggestion.
      flag = arg.split('=')[0]
      value = arg.split('=')[1] if len(arg.split('=')) > 1 else None
      if flag.startswith('--') or value:
        suggestion = suggester.GetSuggestion(flag)
        arg = self._AddLocations(arg)
      else:
        suggestion = None
      if arg in messages:
        continue
      if self._ExistingFlagAlternativeReleaseTracks(flag):
        existing_alternatives = self._ExistingFlagAlternativeReleaseTracks(flag)
        messages.append('\n {} flag is available in one or more alternate '
                        'release tracks. Try:\n'.format(flag))
        messages.append('\n  '.join(existing_alternatives) +'\n')
      if suggestion:
        suggestions[arg] = suggestion
        messages.append(arg + " (did you mean '{0}'?)".format(suggestion))
      else:
        messages.append(arg)

    # If there is a single arg, put it on the same line.  If there are multiple
    # add each on its own line for better clarity.
    if len(messages) > 1:
      separator, prefix = '\n  ', ''
    else:
      separator, prefix = ' ', '\n\n'
    # Always add a final message suggesting gcloud help. Set off with new line
    # if this will be the only new line.
    messages.append('{}{}'.format(prefix, _HELP_SEARCH_HINT))
    self._Error(parser_errors.UnrecognizedArgumentsError(
        'unrecognized arguments:{0}{1}'.format(
            separator, separator.join(messages)),
        parser=self,
        total_unrecognized=len(unknown_args),
        total_suggestions=len(suggestions),
        suggestions=suggestions))

  def _SetErrorContext(self, context):
    """Sets the current error context to context -- called by self.error()."""
    self._error_context = context

  def _ParseKnownArgs(self, args, namespace, wrapper=True):
    """Calls parse_known_args() and adds error_context to the return.

    Args:
      args: The list of command line args.
      namespace: The parsed args namespace.
      wrapper: Calls the parse_known_args() wrapper if True, otherwise the
        wrapped argparse parse_known_args().

    Returns:
      namespace: The parsed arg namespace.
      unknown_args: The list of unknown args.
      error_context: The _ErrorContext if there was an error, None otherwise.
    """
    self._error_context = None
    parser = self if wrapper else super(ArgumentParser, self)
    try:
      namespace, unknown_args = parser.parse_known_args(args, namespace)
    except _HandleLaterError:
      unknown_args = []
    error_context = self._error_context
    self._error_context = None
    if not unknown_args and hasattr(parser, 'flags_locations'):
      parser.flags_locations = collections.defaultdict(set)
    return namespace, unknown_args, error_context

  def _DeduceBetterError(self, context, args, namespace):
    """There is an argparse error in context, see if we can do better.

    We are committed to an argparse error. See if we can do better than the
    observed error in context by isolating each flag arg to determine if the
    argparse error complained about a flag arg value instead of a positional.

    Args:
      context: The _ErrorContext containing the error to improve.
      args: The subset of the command lines args that triggered the argparse
        error in context.
      namespace: The namespace for the current parser.
    """
    self._probe_error = True
    for arg in args:
      try:
        if not arg.startswith('-'):
          break
      except AttributeError:
        break
      _, _, error_context = self._ParseKnownArgs([arg], namespace)
      if not error_context:
        continue
      context = error_context
      break
    self._probe_error = False
    context.error.argument = context.AddLocations(context.error.argument)
    context.parser.error(context=context, reproduce=True)

  @staticmethod
  def GetDestinations(args):
    """Returns the set of 'dest' attributes (or the arg if no dest)."""
    return set([getattr(a, 'dest', a) for a in args])

  # pylint: disable=invalid-name, argparse style
  def validate_specified_args(self, ai, specified_args, namespace,
                              is_required=True, top=True):
    """Validate specified args against the arg group constraints.

    Each group may be mutually exclusive and/or required. Each argument may be
    required.

    Args:
      ai: ArgumentInterceptor, The argument interceptor containing the
        ai.arguments argument group.
      specified_args: set, The dests of the specified args.
      namespace: object, The parsed args namespace.
      is_required: bool, True if all containing groups are required.
      top: bool, True if ai.arguments is the top level group.

    Raises:
      ModalGroupError: If modal arg not specified.
      OptionalMutexError: On optional mutex group conflict.
      RequiredError: If required arg not specified.
      RequiredMutexError: On required mutex group conflict.

    Returns:
      True if the subgroup was specified.
    """
    # TODO(b/120132521) Replace and eliminate argparse extensions
    also_optional = []  # The optional args in group that were not specified.
    have_optional = []  # The specified optional (not required) args.
    have_required = []  # The specified required args.
    need_required = []  # The required args in group that must be specified.
    arguments = (
        sorted(ai.arguments, key=usage_text.GetArgSortKey)
        if ai.sort_args else ai.arguments)
    for arg in arguments:
      if arg.is_group:
        arg_was_specified = self.validate_specified_args(
            arg,
            specified_args,
            namespace,
            is_required=is_required and arg.is_required,
            top=False)
      else:
        arg_was_specified = arg.dest in specified_args
      if arg_was_specified:
        if arg.is_required:
          have_required.append(arg)
        else:
          have_optional.append(arg)
      elif arg.is_required:
        if not isinstance(arg, DynamicPositionalAction):
          need_required.append(arg)
      else:
        also_optional.append(arg)

    if need_required:
      if top or have_required and not (have_optional or also_optional):
        need_args = usage_text.ArgumentWrapper(
            arguments=need_required, is_group=True, sort_args=ai.sort_args)
        self._Error(parser_errors.RequiredError(
            parser=self,
            argument=usage_text.GetArgUsage(
                need_args, value=False, hidden=True, top=top)))
      if have_optional or have_required:
        have_args = usage_text.ArgumentWrapper(
            arguments=have_optional + have_required, is_group=True,
            sort_args=ai.sort_args)
        need_args = usage_text.ArgumentWrapper(
            arguments=need_required, is_group=True,
            sort_args=ai.sort_args)
        self._Error(parser_errors.ModalGroupError(
            parser=self,
            argument=usage_text.GetArgUsage(
                have_args, value=False, hidden=True, top=top),
            conflict=usage_text.GetArgUsage(
                need_args, value=False, hidden=True, top=top)))

    # Multiple args with the same dest are counted as 1 arg.
    count = (len(self.GetDestinations(have_required)) +
             len(self.GetDestinations(have_optional)))

    if ai.is_mutex:
      conflict = usage_text.GetArgUsage(ai, value=False, hidden=True, top=top)
      if is_required and ai.is_required:
        if count != 1:
          if count:
            argument = usage_text.GetArgUsage(
                sorted(have_required + have_optional,
                       key=usage_text.GetArgSortKey)[0],
                value=False, hidden=True, top=top)
            try:
              flag = namespace.GetFlagArgument(argument)
            except parser_errors.UnknownDestinationException:
              flag = None
            if flag:
              value = namespace.GetValue(flag.dest)
              if not isinstance(value, (bool, dict, list)):
                argument = self._AddLocations(argument, value)
          else:
            argument = None
          self._Error(parser_errors.RequiredMutexError(
              parser=self, argument=argument, conflict=conflict))
      elif count > 1:
        argument = usage_text.GetArgUsage(
            sorted(have_required + have_optional,
                   key=usage_text.GetArgSortKey)[0],
            value=False, hidden=True, top=top)
        self._Error(parser_errors.OptionalMutexError(
            parser=self, argument=argument, conflict=conflict))

    return bool(count)

  def parse_known_args(self, args=None, namespace=None):
    """Overrides argparse.ArgumentParser's .parse_known_args method."""
    if args is None:
      args = argv_utils.GetDecodedArgv()[1:]
    if namespace is None:
      namespace = Namespace()
    namespace._SetParser(self)  # pylint: disable=protected-access
    try:
      if self._remainder_action:
        # Remove remainder_action if still there so it is not parsed regularly.
        try:
          self._actions.remove(self._remainder_action)
        except ValueError:
          pass
        # Split on first -- if it exists
        namespace, args = self._remainder_action.ParseKnownArgs(args, namespace)
      # _get_values() updates self._specified_args.
      self._specified_args = namespace._specified_args  # pylint: disable=protected-access
      namespace, unknown_args, error_context = self._ParseKnownArgs(
          args, namespace, wrapper=False)
      # Propagate _specified_args.
      namespace._specified_args.update(self._specified_args)  # pylint: disable=protected-access
      if unknown_args:
        self._Suggest(unknown_args)
      elif error_context:
        if self._probe_error:
          raise _HandleLaterError()
        error_context.parser._DeduceBetterError(  # pylint: disable=protected-access
            error_context, args, namespace)
      namespace._parsers.append(self)  # pylint: disable=protected-access
    finally:
      # Replace action for help message and ArgumentErrors.
      if self._remainder_action:
        self._actions.append(self._remainder_action)
    return (namespace, unknown_args)

  @classmethod
  def _SaveOriginalArgs(cls, original_args):
    if original_args:
      cls._args = original_args[:]
    else:
      cls._args = None

  @classmethod
  def _ClearOriginalArgs(cls):
    cls._args = None

  @classmethod
  def _GetOriginalArgs(cls):
    return cls._args

  def parse_args(self, args=None, namespace=None, raise_error=False):
    """Overrides argparse.ArgumentParser's .parse_args method."""
    self._SaveOriginalArgs(args)
    self.raise_error = raise_error
    namespace, unknown_args, _ = self._ParseKnownArgs(args, namespace)

    # pylint:disable=protected-access
    deepest_parser = namespace._GetParser()
    deepest_parser._specified_args = namespace._specified_args

    if not unknown_args:
      # All of the specified args from all of the subparsers are now known.
      # Check for argument/group conflicts and error out from the deepest
      # parser so the resulting error message has the correct command context.
      for parser in namespace._parsers:
        try:
          # pylint: disable=protected-access
          parser.validate_specified_args(
              parser.ai, namespace._specified_args, namespace)
        except argparse.ArgumentError as e:
          deepest_parser._Error(e)
      if namespace._GetCommand().is_group:
        deepest_parser.error('Command name argument expected.')

      # No argument/group conflicts.
      return namespace

    if deepest_parser._remainder_action:
      # Assume the user wanted to pass all arguments after last recognized
      # arguments into _remainder_action. Either do this with a warning or
      # fail depending on strictness.
      # pylint:disable=protected-access
      try:
        namespace, unknown_args = (
            deepest_parser._remainder_action.ParseRemainingArgs(
                unknown_args, namespace, args))
        # There still may be unknown_args that came before the last known arg.
        if not unknown_args:
          return namespace
      except parser_errors.UnrecognizedArgumentsError:
        # In the case of UnrecognizedArgumentsError, we want to just let it
        # continue so that we can get the nicer error handling.
        pass

    deepest_parser._Suggest(unknown_args)

  def _check_value(self, action, value):
    """Overrides argparse.ArgumentParser's ._check_value(action, value) method.

    Args:
      action: argparse.Action, The action being checked against this value.
      value: The parsed command line argument provided that needs to correspond
          to this action.

    Raises:
      argparse.ArgumentError: If the action and value don't work together.
    """
    is_subparser = isinstance(action, CloudSDKSubParsersAction)

    # When using tab completion, argcomplete monkey patches various parts of
    # argparse and interferes with the normal argument parsing flow.  Here, we
    # need to set self._orig_class because argcomplete compares this
    # directly to argparse._SubParsersAction to see if it should recursively
    # patch this parser.  It should really check to see if it is a subclass
    # but alas, it does not.  If we don't set this, argcomplete will not patch,
    # our subparser and completions below this point won't work.  Normally we
    # would just set this in action.IsValidChoice() but sometimes this
    # sub-element has already been loaded and is already in action.choices.  In
    # either case, we still need argcomplete to patch this subparser so it
    # can compute completions below this point.
    if is_subparser and '_ARGCOMPLETE' in os.environ:
      # pylint:disable=protected-access, Required by argcomplete.
      action._orig_class = argparse._SubParsersAction
    # This is copied from this method in argparse's version of this method.
    if action.choices is None or value in action.choices:
      return
    if isinstance(value, six.string_types):
      arg = value
    else:
      arg = six.text_type(value)

    # We add this to check if we can lazy load the element.
    if is_subparser and action.IsValidChoice(arg):
      return

    # Not something we know, raise an error.
    # pylint:disable=protected-access
    cli_generator = self._calliope_command._cli_generator
    missing_components = cli_generator.ComponentsForMissingCommand(
        self._calliope_command.GetPath() + [arg])
    if missing_components:
      msg = ('You do not currently have this command group installed.  Using '
             'it requires the installation of components: '
             '[{missing_components}]'.format(
                 missing_components=', '.join(missing_components)))
      update_manager.UpdateManager.EnsureInstalledAndRestart(
          missing_components, msg=msg)

    if is_subparser:
      # We are going to show the usage anyway, which requires loading
      # everything.  Do this here so that choices gets populated.
      action.LoadAllChoices()

    # Command is not valid, see what we can suggest as a fix...
    message = "Invalid choice: '{0}'.".format(value)

    # Determine if the requested command is available in another release track.
    existing_alternatives = self._ExistingCommandAlternativeReleaseTracks(arg)
    if existing_alternatives:
      message += ('\nThis command is available in one or more alternate '
                  'release tracks.  Try:\n  ')
      message += '\n  '.join(existing_alternatives)

      # Log to analytics the attempt to execute a command.
      # We know the user entered 'value' is a valid command in a different
      # release track. It's safe to include it.
      self._Error(parser_errors.WrongTrackError(
          message,
          parser=self,
          extra_path_arg=arg,
          suggestions=existing_alternatives))

    # If we are dealing with flags, see if the spelling was close to something
    # else that exists here.
    suggestion = None
    choices = sorted(action.choices)
    if not is_subparser:
      suggester = usage_text.TextChoiceSuggester(choices)
      suggestion = suggester.GetSuggestion(arg)
      if suggestion:
        message += " Did you mean '{0}'?".format(suggestion)
      else:
        # Command group choices will be displayed in the usage message.
        message += '\n\nValid choices are [{0}].'.format(
            ', '.join([six.text_type(c) for c in choices]))

    # Log to analytics the attempt to execute a command.
    # We don't know if the user entered 'value' is a mistyped command or
    # some resource name that the user entered and we incorrectly thought it's
    # a command. We can't include it since it might be PII.

    self._Error(parser_errors.UnknownCommandError(
        message,
        argument=action.option_strings[0] if action.option_strings else None,
        total_unrecognized=1,
        total_suggestions=1 if suggestion else 0,
        suggestions=[suggestion] if suggestion else choices))

  def _CommandAlternativeReleaseTracks(self, value=None):
    """Gets alternatives for the command in other release tracks.

    Args:
      value: str, The value being parsed.

    Returns:
      [CommandCommon]: The alternatives for the command in other release tracks.
    """
    existing_alternatives = []
    # pylint:disable=protected-access
    cli_generator = self._calliope_command._cli_generator
    alternates = cli_generator.ReplicateCommandPathForAllOtherTracks(
        self._calliope_command.GetPath() + ([value] if value else []))
    if alternates:
      top_element = self._calliope_command._TopCLIElement()
      for _, command_path in sorted(six.iteritems(alternates),
                                    key=lambda x: x[0].prefix or ''):
        alternative_cmd = top_element.LoadSubElementByPath(command_path[1:])
        if alternative_cmd and not alternative_cmd.IsHidden():
          existing_alternatives.append(alternative_cmd)
    return existing_alternatives

  def _ExistingFlagAlternativeReleaseTracks(self, arg):
    """Checks whether the arg exists in other tracks of the command.

    Args:
      arg: str, The argument being parsed.

    Returns:
      [str]: The names of alternate commands that the user may use.
    """
    res = []
    for alternate in self._CommandAlternativeReleaseTracks():
      if arg in [f.option_strings[0] for f in alternate.GetAllAvailableFlags(
          include_hidden=False)]:
        res.append(' '.join(alternate.GetPath()) + ' ' + arg)
    return res

  def _ExistingCommandAlternativeReleaseTracks(self, value):
    """Gets the path of alternatives for the command in other release tracks.

    Args:
      value: str, The value being parsed.

    Returns:
      [str]:  The names of alternate commands that the user may use.
    """
    return [' '.join(alternate.GetPath()) for alternate in
            self._CommandAlternativeReleaseTracks(value=value)]

  def _ReportErrorMetricsHelper(self, dotted_command_path, error,
                                error_extra_info=None):
    """Logs `Commands` and `Error` Google Analytics events for an error.

    Args:
      dotted_command_path: str, The dotted path to as much of the command as we
          can identify before an error. Example: gcloud.projects
      error: class, The class (not the instance) of the Exception for an error.
      error_extra_info: {str: json-serializable}, A json serializable dict of
        extra info that we want to log with the error. This enables us to write
        queries that can understand the keys and values in this dict.
    """
    specified_args = self.GetSpecifiedArgNames()
    metrics.Commands(
        dotted_command_path,
        config.CLOUD_SDK_VERSION,
        specified_args,
        error=error,
        error_extra_info=error_extra_info)
    metrics.Error(
        dotted_command_path,
        error,
        specified_args,
        error_extra_info=error_extra_info)

  def ReportErrorMetrics(self, error, message):
    """Reports Command and Error metrics in case of argparse errors.

    Args:
      error: Exception, The Exception object.
      message: str, The exception error message.
    """
    dotted_command_path = '.'.join(self._calliope_command.GetPath())

    # Check for parser_errors.ArgumentError with metrics payload.
    if isinstance(error, parser_errors.ArgumentError):
      if error.extra_path_arg:
        dotted_command_path = '.'.join([dotted_command_path,
                                        error.extra_path_arg])
      self._ReportErrorMetricsHelper(dotted_command_path,
                                     error.__class__,
                                     error.error_extra_info)
      return

    # No specific exception with metrics, try to detect error from message.
    if 'too few arguments' in message:
      self._ReportErrorMetricsHelper(dotted_command_path,
                                     parser_errors.TooFewArgumentsError)
      return

    # Catchall for any error we didn't explicitly detect.
    self._ReportErrorMetricsHelper(dotted_command_path,
                                   parser_errors.OtherParsingError)

  def error(self, message='', context=None, reproduce=False):
    """Overrides argparse.ArgumentParser's .error(message) method.

    Specifically, it avoids reprinting the program name and the string
    "error:".

    Args:
      message: str, The error message to print.
      context: _ErrorContext, An error context with affected parser.
      reproduce: bool, Reproduce a previous call to this method from context.

    Raises:
      _HandleLaterError: if the error should be handled in a subsequent call to
        this method.
    """
    # Ignore errors better handled by validate_specified_args().
    if '_ARGCOMPLETE' not in os.environ:
      if re.search('too few arguments', message):
        return
      if (re.search('arguments? .* required', message) and
          not re.search('in dict arg but not provided', message) and
          not re.search(r'\[.*\brequired\b.*\]', message)):
        return

    if reproduce and context:
      # Reproduce a previous call to this method from the info in context.
      message = context.message
      parser = context.parser
      error = context.error
      if not error:
        error = parser_errors.ArgumentError(message, parser=self)
    else:
      if context:
        message = context.message
        parser = context.parser
        error = context.error
      else:
        if 'Invalid choice:' in message:
          exc = parser_errors.UnrecognizedArgumentsError
        else:
          exc = parser_errors.ArgumentError
        if message:
          message = re.sub(r"\bu'", "'", message)
        error = exc(message, parser=self)
        parser = self
      if ('_ARGCOMPLETE' not in os.environ and
          not isinstance(error, parser_errors.DetailedArgumentError) and
          (
              self._probe_error or
              'Invalid choice' in message
          )
         ):
        if self._probe_error and 'expected one argument' in message:
          raise _HandleLaterError()
        # Save this context for later. We may be able to deduce a better error
        # message. For instance, argparse might complain about an invalid
        # command choice 'flag-value' for '--unknown-flag flag-value', but
        # with a little finagling in parse_known_args() we can verify that
        # '--unknown-flag' is in fact an unknown flag and error out on that.
        self._SetErrorContext(context or _ErrorContext(message, parser, error))
        raise _HandleLaterError()

    # Add file/line info if specified.

    prefix = 'argument '
    if context and message.startswith(prefix):
      parts = message.split(':', 1)
      arg = context.AddLocations(parts[0][len(prefix):])
      message = '{}{}:{}'.format(prefix, arg, parts[1])

    # No need to output help/usage text if we are in completion mode. However,
    # we do need to populate group/command level choices. These choices are not
    # loaded when there is a parser error since we do lazy loading.
    if '_ARGCOMPLETE' in os.environ:
      # pylint:disable=protected-access
      if self._calliope_command._sub_parser:
        self._calliope_command.LoadAllSubElements()
    elif not self.raise_error:
      message = console_attr.SafeText(message)
      log.error('({prog}) {message}'.format(prog=self.prog, message=message))
      # multi-line message means hints already added, no need for usage.
      # pylint: disable=protected-access
      if '\n' not in message:
        # Provide "Maybe you meant" suggestions if we are dealing with an
        # invalid command.
        suggestions = None
        if 'Invalid choice' in message:
          suggestions = suggest_commands.GetCommandSuggestions(
              self._GetOriginalArgs())
          self._ClearOriginalArgs()
        if suggestions:
          argparse._sys.stderr.write(
              '\n  '.join(['Maybe you meant:'] + suggestions) + '\n')
          argparse._sys.stderr.write('\n' + _HELP_SEARCH_HINT + '\n')
          error.error_extra_info = {
              'suggestions': suggestions,
              'total_suggestions': len(suggestions),
              'total_unrecognized': 1,
          }
        # Otherwise print out usage string.
        elif 'Command name argument expected.' == message:
          usage_string = self._calliope_command.GetCategoricalUsage()
          # The next if clause is executed if there were no categories to
          # display.
          uncategorized_usage = False
          if not usage_string:
            uncategorized_usage = True
            usage_string = self._calliope_command.GetUncategorizedUsage()
          interactive = False
          if not uncategorized_usage:
            interactive = console_io.IsInteractive(error=True)
          if interactive:
            out = io.StringIO()
            out.write('{message}\n'.format(message=message))
          else:
            out = argparse._sys.stderr
          out.write('\n')
          render_document.RenderDocument(
              fin=io.StringIO(usage_string), out=out)
          if uncategorized_usage:
            out.write(self._calliope_command.GetHelpHint())
          if interactive:
            console_io.More(out.getvalue(), out=argparse._sys.stderr)
        else:
          usage_string = self._calliope_command.GetUsage()
          argparse._sys.stderr.write(usage_string)

    parser.ReportErrorMetrics(error, message)
    self.exit(2, exception=error)

  def exit(self, status=0, message=None, exception=None):
    """Overrides argparse.ArgumentParser's .exit() method.

    Args:
      status: int, The exit status.
      message: str, The error message to print.
      exception: Exception, The exception that caused the exit, if any.
    """
    del message  # self.error() handles all messaging
    if self.raise_error:
      raise exception

    sys.exit(status)

  def _parse_optional(self, arg_string):
    """Overrides argparse.ArgumentParser's ._parse_optional method.

    This allows the parser to have leading flags included in the grabbed
    arguments and stored in the namespace.

    Args:
      arg_string: str, The argument string.

    Returns:
      The normal return value of argparse.ArgumentParser._parse_optional.
    """
    if not isinstance(arg_string, six.string_types):
      # Flag value injected by --flags-file.
      return None
    positional_actions = self._get_positional_actions()
    option_tuple = super(ArgumentParser, self)._parse_optional(arg_string)
    # If parse_optional finds an action for this arg_string, use that option.
    # Note: option_tuple = (action, option_string, explicit_arg) or None
    known_option = option_tuple and option_tuple[0]
    if (len(positional_actions) == 1 and
        positional_actions[0].nargs == argparse.REMAINDER and
        not known_option):
      return None
    return option_tuple

  def _get_values(self, action, arg_strings):
    """Intercepts argparse.ArgumentParser's ._get_values method.

    This intercept does not actually change any behavior.  We use this hook to
    grab the flags and arguments that are actually seen at parse time.  The
    resulting namespace has entries for every argument (some with defaults) so
    we can't know which the user actually typed.

    Args:
      action: Action, the action that is being processed.
      arg_strings: [str], The values provided for this action.

    Returns:
      Whatever the parent method returns.
    """
    if action.dest != argparse.SUPPRESS:  # argparse SUPPRESS usage
      # Don't look at the action unless it is a real argument or flag. The
      # suppressed destination indicates that it is a SubParsers action.
      name = None
      if action.option_strings:
        # This is a flag, save the first declared name of the flag.
        name = action.option_strings[0]
      elif arg_strings:
        # This is a positional and there are arguments to consume.  Optional
        # positionals will always get to this method, so we need to ignore the
        # ones for which a value was not actually provided.  If it is provided,
        # save the metavar name or the destination name.
        name = action.metavar if action.metavar else action.dest
        if action.nargs and action.nargs != '?':
          # This arg takes in multiple values, record how many were provided.
          # (? means 0 or 1, so treat that as an arg that takes a single value.
          name += ':' + six.text_type(len(arg_strings))
      if name:
        self._specified_args[action.dest] = name
    return super(ArgumentParser, self)._get_values(action, arg_strings)

  def _get_option_tuples(self, option_string):
    """Intercepts argparse.ArgumentParser's ._get_option_tuples method.

    Cloud SDK no longer supports flag abbreviations, so it always returns []
    for the non-arg-completion case to indicate no abbreviated flag matches.

    Args:
      option_string: The option string to match.

    Returns:
      A list of matching flag tuples.
    """
    if '_ARGCOMPLETE' in os.environ:
      return super(ArgumentParser, self)._get_option_tuples(option_string)
    return []  # This effectively disables abbreviations.


# pylint:disable=protected-access
class CloudSDKSubParsersAction(six.with_metaclass(abc.ABCMeta,
                                                  argparse._SubParsersAction)):
  """A custom subclass for arg parsing behavior.

  While the above ArgumentParser overrides behavior for parsing the flags
  associated with a specific group or command, this class overrides behavior
  for loading those sub parsers.
  """

  @abc.abstractmethod
  def IsValidChoice(self, choice):
    """Determines if the given arg is a valid sub group or command.

    Args:
      choice: str, The name of the sub element to check.

    Returns:
      bool, True if the given item is a valid sub element, False otherwise.
    """
    pass

  @abc.abstractmethod
  def LoadAllChoices(self):
    """Load all the choices because we need to know the full set."""
    pass


class CommandGroupAction(CloudSDKSubParsersAction):
  """A subparser for loading calliope command groups on demand.

  We use this to intercept the parsing right before it needs to start parsing
  args for sub groups and we then load the specific sub group it needs.
  """

  def __init__(self, *args, **kwargs):
    self._calliope_command = kwargs.pop('calliope_command')
    super(CommandGroupAction, self).__init__(*args, **kwargs)

  def IsValidChoice(self, choice):
    # When using tab completion, argcomplete monkey patches various parts of
    # argparse and interferes with the normal argument parsing flow.  Usually
    # it is sufficient to check if the given choice is valid here, but delay
    # the loading until __call__ is invoked later during the parsing process.
    # During completion time, argcomplete tries to patch the subparser before
    # __call__ is called, so nothing has been loaded yet.  We need to force
    # load things here so that there will be something loaded for it to patch.
    if '_ARGCOMPLETE' in os.environ:
      self._calliope_command.LoadSubElement(choice)
    return self._calliope_command.IsValidSubElement(choice)

  def LoadAllChoices(self):
    self._calliope_command.LoadAllSubElements()

  def __call__(self, parser, namespace, values, option_string=None):
    # This is the name of the arg that is the sub element that needs to be
    # loaded.
    parser_name = values[0]
    # Load that element if it's there.  If it's not valid, nothing will be
    # loaded and normal error handling will take over.
    if self._calliope_command:
      self._calliope_command.LoadSubElement(parser_name)
    super(CommandGroupAction, self).__call__(
        parser, namespace, values, option_string=option_string)


class DynamicPositionalAction(six.with_metaclass(abc.ABCMeta,
                                                 CloudSDKSubParsersAction)):
  """An argparse action that adds new flags to the parser when it is called.

  We need to use a subparser for this because for a given parser, argparse
  collects all the arg information before it starts parsing. Adding in new flags
  on the fly doesn't work. With a subparser, it is independent so we can load
  flags into here on the fly before argparse loads this particular parser.
  """

  def __init__(self, *args, **kwargs):
    self.hidden = kwargs.pop('hidden', False)
    self._parent_ai = kwargs.pop('parent_ai')
    super(DynamicPositionalAction, self).__init__(*args, **kwargs)

  def IsValidChoice(self, choice):
    # We need to actually create the parser or else check_value will fail if the
    # given choice is not present. We just add it no matter what it is because
    # we don't have access to the namespace to be able to figure out if the
    # choice is actually valid. Invalid choices will raise exceptions once
    # called. We also don't actually care what the values are in here because we
    # register an explicit completer to use for completions, so the list of
    # parsers is not actually used other than to bypass the check_value
    # validation.
    self._AddParser(choice)
    # By default, don't do any checking of the argument. If it is bad, raise
    # an exception when it is called. We don't need to do any on-demand loading
    # here because there are no subparsers of this one, so the above argcomplete
    # issue doesn't matter.
    return True

  def LoadAllChoices(self):
    # We don't need to do this because we will use an explicit completer to
    # complete the names of the options rather than relying on correctly
    # populating the choices.
    pass

  def _AddParser(self, choice):
    # Create a new parser and pass in the calliope_command of the original so
    # that things like help and error reporting continue to work.
    return self.add_parser(
        choice, add_help=False, prog=self._parent_ai.parser.prog,
        calliope_command=self._parent_ai.parser._calliope_command)

  @abc.abstractmethod
  def GenerateArgs(self, namespace, choice):
    pass

  @abc.abstractmethod
  def Completions(self, prefix, parsed_args, **kwargs):
    pass

  def __call__(self, parser, namespace, values, option_string=None):
    choice = values[0]
    args = self.GenerateArgs(namespace, choice)
    sub_parser = self._name_parser_map[choice]

    # This is tricky. When we create a new parser above, that parser does not
    # have any of the flags from the parent command. We need to propagate them
    # all down to this parser like we do in calliope. We also want to add new
    # flags. In order for those to show up in the help, they need to be
    # registered with an ArgumentInterceptor. Here, we create one and seed it
    # with the data of the parent. This actually means that every flag we add
    # to our new parser will show up in the help of the parent parser, even
    # though those flags are not actually on that parser. This is ok because
    # help is always run on the parent ArgumentInterceptor and we want it to
    # show the full set of args.
    ai = parser_arguments.ArgumentInterceptor(
        sub_parser, is_global=False, cli_generator=None,
        allow_positional=True, data=self._parent_ai.data)

    for flag in itertools.chain(self._parent_ai.flag_args,
                                self._parent_ai.ancestor_flag_args):
      # Propagate the flags down except the ones we are not supposed to. Note
      # that we *do* copy the help action unlike we usually do because this
      # subparser is going to share the help action of the parent.
      if flag.do_not_propagate or flag.is_required:
        continue
      # We add the flags directly to the parser instead of the
      # ArgumentInterceptor because if we didn't the flags would be duplicated
      # in the help, since we reused the data object from the parent.
      sub_parser._add_action(flag)
    # Update parent display_info in children, children take precedence.
    ai.display_info.AddLowerDisplayInfo(self._parent_ai.display_info)

    # Add args to the parser and remove any collisions if arguments are
    # already registered with the same name.
    for arg in args:
      arg.RemoveFromParser(ai)
      added_arg = arg.AddToParser(ai)
      # Argcomplete patches parsers and actions before call() is called. Since
      # we generate these args at call() time, they have not been patched and
      # causes completion to fail. Since we know that we are not going to be
      # adding any subparsers (the only thing that actually needs to be patched)
      # we fake it here to make argcomplete think it did the patching so it
      # doesn't crash.
      if '_ARGCOMPLETE' in os.environ and not hasattr(added_arg, '_orig_class'):
        added_arg._orig_class = added_arg.__class__

    super(DynamicPositionalAction, self).__call__(
        parser, namespace, values, option_string=option_string)

    # Running two dynamic commands in a row using the same CLI object is a
    # problem because the argparse parsers are saved in between invocations.
    # This is usually fine because everything is static, but in this case two
    # invocations could actually have different dynamic args generated. We
    # have to do two things to get this to work. First we need to clear the
    # parser from the map. If we don't do this, this class doesn't even get
    # called again because the choices are already defined. Second, we need
    # to remove the arguments we added from the ArgumentInterceptor. The
    # parser itself is thrown out, but because we are sharing an
    # ArgumentInterceptor with our parent, it remembers the args that we
    # added. Later, they are propagated back down to us even though they no
    # longer actually exist. When completing, we know we will only be running
    # a single invocation and we need to leave the choices around so that the
    # completer can read them after the command fails to run.
    if '_ARGCOMPLETE' not in os.environ:
      self._name_parser_map.clear()
      # Detaching the argument interceptors here makes the help text work by
      # preventing the accumlation of duplicate entries with each command
      # execution on this CLI.  However, it also foils the ability to map arg
      # dest names back to the original argument, needed for the flag completion
      # style.  It's commented out here just in case help text wins out over
      # argument lookup down the road.
      # for _, arg in args.iteritems():
      #   arg.RemoveFromParser(ai)
