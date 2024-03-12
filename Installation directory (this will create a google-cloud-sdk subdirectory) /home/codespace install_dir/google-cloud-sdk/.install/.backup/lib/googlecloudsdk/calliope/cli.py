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

"""The calliope CLI/API is a framework for building library interfaces."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import argparse
import collections
import os
import re
import sys
import types
import uuid

import argcomplete
from googlecloudsdk.calliope import actions
from googlecloudsdk.calliope import backend
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.calliope import command_loading
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.calliope import parser_errors
from googlecloudsdk.calliope import parser_extensions
from googlecloudsdk.core import argv_utils
from googlecloudsdk.core import config
from googlecloudsdk.core import log
from googlecloudsdk.core import metrics
from googlecloudsdk.core import properties
from googlecloudsdk.core import yaml
from googlecloudsdk.core.configurations import named_configs
from googlecloudsdk.core.console import console_attr
from googlecloudsdk.core.util import encoding
from googlecloudsdk.core.util import files
from googlecloudsdk.core.util import pkg_resources

import six


_COMMAND_SUFFIX = '.py'
_FLAG_FILE_LINE_NAME = '---flag-file-line-'


class _FlagLocation(object):
  """--flags-file (file,line_col) location."""

  def __init__(self, file_name, line_col):
    self.file_name = file_name
    self.line = line_col.line + 1  # ruamel does 0-offset line numbers?

  def __str__(self):
    return '{}:{}'.format(self.file_name, self.line)


class _ArgLocations(object):
  """--flags-file (arg,locations) info."""

  def __init__(self, arg, file_name, line_col, locations=None):
    self.arg = arg
    self.locations = locations.locations[:] if locations else []
    self.locations.append(_FlagLocation(file_name, line_col))

  def __str__(self):
    return ';'.join([six.text_type(location) for location in self.locations])

  def FileInStack(self, file_name):
    """Returns True if file_name is in the locations stack."""
    return any([file_name == x.file_name for x in self.locations])


def _AddFlagsFileFlags(inject, flags_file, parent_locations=None):
  """Recursively append the flags file flags to inject."""

  flag = calliope_base.FLAGS_FILE_FLAG.name

  if parent_locations and parent_locations.FileInStack(flags_file):
    raise parser_errors.ArgumentError(
        '{} recursive reference ({}).'.format(flag, parent_locations))

  # Load the YAML flag:value dict or list of dicts. List of dicts allows
  # flags to be specified more than once.

  if flags_file == '-':
    contents = sys.stdin.read()
  elif not os.path.exists(flags_file):
    raise parser_errors.ArgumentError(
        '{} [{}] not found.'.format(flag, flags_file))
  else:
    contents = files.ReadFileContents(flags_file)
  if not contents:
    raise parser_errors.ArgumentError(
        '{} [{}] is empty.'.format(flag, flags_file))
  data = yaml.load(contents, location_value=True)
  group = data if isinstance(data, list) else [data]

  # Generate the list of args to inject.

  for member in group:

    if not isinstance(member.value, dict):
      raise parser_errors.ArgumentError(
          '{}:{}: {} file must contain a dictionary or list of dictionaries '
          'of flags.'.format(flags_file, member.lc.line + 1, flag))

    for arg, obj in six.iteritems(member.value):

      line_col = obj.lc
      value = yaml.strip_locations(obj)

      if arg == flag:
        # The flags-file YAML arg value can be a path or list of paths.
        file_list = obj.value if isinstance(obj.value, list) else [obj.value]
        for path in file_list:
          locations = _ArgLocations(arg, flags_file, line_col, parent_locations)
          _AddFlagsFileFlags(inject, path, locations)
        continue
      if isinstance(value, (type(None), bool)):
        separate_value_arg = False
      elif isinstance(value, (list, dict)):
        separate_value_arg = True
      else:
        separate_value_arg = False
        arg = '{}={}'.format(arg, value)
      inject.append(_FLAG_FILE_LINE_NAME)
      inject.append(_ArgLocations(arg, flags_file, line_col, parent_locations))
      inject.append(arg)
      if separate_value_arg:
        # Add the already lexed arg and with one swoop we sidestep all flag
        # value and command line interpreter quoting issues. The ArgList and
        # ArgDict arg parsers have been adjusted to handle this.
        inject.append(value)


def _ApplyFlagsFile(args):
  """Applies FLAGS_FILE_FLAG in args and returns the new args.

  The basic algorithm is arg list manipulation, done before ArgParse is called.
  This function reaps all FLAGS_FILE_FLAG args from the command line, and
  recursively from the flags files, and inserts them into a new args list by
  replacing the --flags-file=YAML-FILE flag by its constituent flags. This
  preserves the left-to-right precedence of the argument parser. Internal
  _FLAG_FILE_LINE_NAME flags are also inserted into args. This specifies the
  flags source file and line number for each flags file flag, and is used to
  construct actionable error messages.

  Args:
    args: The original args list.

  Returns:
    A new args list with all FLAGS_FILE_FLAG args replaced by their constituent
    flags.
  """
  flag = calliope_base.FLAGS_FILE_FLAG.name
  flag_eq = flag + '='
  if not any([arg == flag or arg.startswith(flag_eq) for arg in args]):
    return args

  # Find and replace all file flags by their constituent flags

  peek = False
  new_args = []
  for arg in args:
    if peek:
      peek = False
      _AddFlagsFileFlags(new_args, arg)
    elif arg == flag:
      peek = True
    elif arg.startswith(flag_eq):
      _AddFlagsFileFlags(new_args, arg[len(flag_eq):])
    else:
      new_args.append(arg)

  return new_args


class RunHook(object):
  """Encapsulates a function to be run before or after command execution.

  The function should take **kwargs so that more things can be passed to the
  functions in the future.
  """

  def __init__(self, func, include_commands=None, exclude_commands=None):
    """Constructs the hook.

    Args:
      func: function, The function to run.
      include_commands: str, A regex for the command paths to run.  If not
        provided, the hook will be run for all commands.
      exclude_commands: str, A regex for the command paths to exclude.  If not
        provided, nothing will be excluded.
    """
    self.__func = func
    self.__include_commands = include_commands if include_commands else '.*'
    self.__exclude_commands = exclude_commands

  def Run(self, command_path):
    """Runs this hook if the filters match the given command.

    Args:
      command_path: str, The calliope command path for the command that was run.

    Returns:
      bool, True if the hook was run, False if it did not match.
    """
    if not re.match(self.__include_commands, command_path):
      return False
    if self.__exclude_commands and re.match(self.__exclude_commands,
                                            command_path):
      return False
    self.__func(command_path=command_path)
    return True


class _SetFlagsFileLine(argparse.Action):
  """FLAG_INTERNAL_FLAG_FILE_LINE action."""

  def __call__(self, parser, namespace, values, option_string=None):
    if not hasattr(parser, 'flags_locations'):
      setattr(parser, 'flags_locations', collections.defaultdict(set))
    parser.flags_locations[values.arg].add(six.text_type(values))


FLAG_INTERNAL_FLAG_FILE_LINE = calliope_base.Argument(
    _FLAG_FILE_LINE_NAME,
    default=None,
    action=_SetFlagsFileLine,
    hidden=True,
    help='Internal *--flags-file* flag, line number, and source file.')


class CLILoader(object):
  """A class to encapsulate loading the CLI and bootstrapping the REPL."""

  # Splits a path like foo.bar.baz into 2 groups: foo.bar, and baz.  Group 1 is
  # optional.
  PATH_RE = re.compile(r'(?:([\w\.]+)\.)?([^\.]+)')

  def __init__(self, name, command_root_directory,
               allow_non_existing_modules=False, logs_dir=None,
               version_func=None, known_error_handler=None,
               yaml_command_translator=None):
    """Initialize Calliope.

    Args:
      name: str, The name of the top level command, used for nice error
        reporting.
      command_root_directory: str, The path to the directory containing the main
        CLI module.
      allow_non_existing_modules: True to allow extra module directories to not
        exist, False to raise an exception if a module does not exist.
      logs_dir: str, The path to the root directory to store logs in, or None
        for no log files.
      version_func: func, A function to call for a top-level -v and
        --version flag. If None, no flags will be available.
      known_error_handler: f(x)->None, A function to call when an known error is
        handled. It takes a single argument that is the exception.
      yaml_command_translator: YamlCommandTranslator, An instance of a
        translator that will be used to load commands written as a yaml spec.

    Raises:
      backend.LayoutException: If no command root directory is given.
    """
    self.__name = name
    self.__command_root_directory = command_root_directory
    if not self.__command_root_directory:
      raise command_loading.LayoutException(
          'You must specify a command root directory.')

    self.__allow_non_existing_modules = allow_non_existing_modules

    self.__logs_dir = logs_dir or config.Paths().logs_dir
    self.__version_func = version_func
    self.__known_error_handler = known_error_handler
    self.__yaml_command_translator = yaml_command_translator

    self.__pre_run_hooks = []
    self.__post_run_hooks = []

    self.__modules = []
    self.__missing_components = {}
    self.__release_tracks = {}

  @property
  def yaml_command_translator(self):
    return self.__yaml_command_translator

  def AddReleaseTrack(self, release_track, path, component=None):
    """Adds a release track to this CLI tool.

    A release track (like alpha, beta...) will appear as a subgroup under the
    main entry point of the tool.  All groups and commands will be replicated
    under each registered release track.  You can implement your commands to
    behave differently based on how they are called.

    Args:
      release_track: base.ReleaseTrack, The release track you are adding.
      path: str, The full path the directory containing the root of this group.
      component: str, The name of the component this release track is in, if
        you want calliope to auto install it for users.

    Raises:
      ValueError: If an invalid track is registered.
    """
    if not release_track.prefix:
      raise ValueError('You may only register alternate release tracks that '
                       'have a different prefix.')
    self.__release_tracks[release_track] = (path, component)

  def AddModule(self, name, path, component=None):
    """Adds a module to this CLI tool.

    If you are making a CLI that has subgroups, use this to add in more
    directories of commands.

    Args:
      name: str, The name of the group to create under the main CLI.  If this is
        to be placed under another group, a dotted name can be used.
      path: str, The full path the directory containing the commands for this
        group.
      component: str, The name of the component this command module is in, if
        you want calliope to auto install it for users.
    """
    self.__modules.append((name, path, component))

  def RegisterPreRunHook(self, func,
                         include_commands=None, exclude_commands=None):
    """Register a function to be run before command execution.

    Args:
      func: function, The function to run.  See RunHook for more details.
      include_commands: str, A regex for the command paths to run.  If not
        provided, the hook will be run for all commands.
      exclude_commands: str, A regex for the command paths to exclude.  If not
        provided, nothing will be excluded.
    """
    hook = RunHook(func, include_commands, exclude_commands)
    self.__pre_run_hooks.append(hook)

  def RegisterPostRunHook(self, func,
                          include_commands=None, exclude_commands=None):
    """Register a function to be run after command execution.

    Args:
      func: function, The function to run.  See RunHook for more details.
      include_commands: str, A regex for the command paths to run.  If not
        provided, the hook will be run for all commands.
      exclude_commands: str, A regex for the command paths to exclude.  If not
        provided, nothing will be excluded.
    """
    hook = RunHook(func, include_commands, exclude_commands)
    self.__post_run_hooks.append(hook)

  def ComponentsForMissingCommand(self, command_path):
    """Gets the components that need to be installed to run the given command.

    Args:
      command_path: [str], The path of the command being run.

    Returns:
      [str], The component names of the components that should be installed.
    """
    path_string = '.'.join(command_path)
    return [component
            for path, component in six.iteritems(self.__missing_components)
            if path_string.startswith(self.__name + '.' + path)]

  def ReplicateCommandPathForAllOtherTracks(self, command_path):
    """Finds other release tracks this command could be in.

    The returned values are not necessarily guaranteed to exist because the
    commands could be disabled for that particular release track.  It is up to
    the caller to determine if the commands actually exist before attempting
    use.

    Args:
      command_path: [str], The path of the command being run.

    Returns:
      {ReleaseTrack: [str]}, A mapping of release track to command path of other
      places this command could be found.
    """
    # Only a single element, it's just the root of the tree.
    if len(command_path) < 2:
      return []

    # Determine if the first token is a release track name.
    track = calliope_base.ReleaseTrack.FromPrefix(command_path[1])
    if track and track not in self.__release_tracks:
      # Make sure it's actually a track that we are using in this CLI.
      track = None

    # Remove the track from the path to get back to the GA version of the
    # command, or  keep the existing path if it is not in a track (already GA).
    root = command_path[0]
    sub_path = command_path[2:] if track else command_path[1:]

    if not sub_path:
      # There are no parts to the path other than the track.
      return []

    results = dict()
    # Calculate how this command looks under each alternate release track.
    for t in self.__release_tracks:
      results[t] = [root] + [t.prefix] + sub_path

    if track:
      # If the incoming command had a release track, remove that one from
      # alternate suggestions but add GA.
      del results[track]
      results[calliope_base.ReleaseTrack.GA] = [root] + sub_path

    return results

  def Generate(self):
    """Uses the registered information to generate the CLI tool.

    Returns:
      CLI, The generated CLI tool.
    """
    # The root group of the CLI.
    impl_path = self.__ValidateCommandOrGroupInfo(
        self.__command_root_directory, allow_non_existing_modules=False)
    top_group = backend.CommandGroup(
        [impl_path], [self.__name], calliope_base.ReleaseTrack.GA,
        uuid.uuid4().hex, self, None)
    self.__AddBuiltinGlobalFlags(top_group)

    # Sub groups for each alternate release track.
    loaded_release_tracks = dict([(calliope_base.ReleaseTrack.GA, top_group)])
    track_names = set(track.prefix for track in self.__release_tracks.keys())
    for track, (module_dir, component) in six.iteritems(self.__release_tracks):
      impl_path = self.__ValidateCommandOrGroupInfo(
          module_dir,
          allow_non_existing_modules=self.__allow_non_existing_modules)
      if impl_path:
        # Add the release track sub group into the top group.
        # pylint: disable=protected-access
        top_group._groups_to_load[track.prefix] = [impl_path]
        # Override the release track because this is specifically a top level
        # release track group.
        track_group = top_group.LoadSubElement(
            track.prefix, allow_empty=True, release_track_override=track)
        # Copy all the root elements of the top group into the release group.
        top_group.CopyAllSubElementsTo(track_group, ignore=track_names)
        loaded_release_tracks[track] = track_group
      elif component:
        self.__missing_components[track.prefix] = component

    # Load the normal set of registered sub groups.
    for module_dot_path, module_dir_path, component in self.__modules:
      is_command = module_dir_path.endswith(_COMMAND_SUFFIX)
      if is_command:
        module_dir_path = module_dir_path[:-len(_COMMAND_SUFFIX)]
      match = CLILoader.PATH_RE.match(module_dot_path)
      root, name = match.group(1, 2)
      try:
        # Mount each registered sub group under each release track that exists.
        for track, track_root_group in six.iteritems(loaded_release_tracks):
          # pylint: disable=line-too-long
          parent_group = self.__FindParentGroup(track_root_group, root)
          # pylint: enable=line-too-long
          exception_if_present = None
          if not parent_group:
            if track != calliope_base.ReleaseTrack.GA:
              # Don't error mounting sub groups if the parent group can't be
              # found unless this is for the GA group.  The GA should always be
              # there, but for alternate release channels, the parent group
              # might not be enabled for that particular release channel, so it
              # is valid to not exist.
              continue
            exception_if_present = command_loading.LayoutException(
                'Root [{root}] for command group [{group}] does not exist.'
                .format(root=root, group=name))

          cmd_or_grp_name = module_dot_path.split('.')[-1]
          impl_path = self.__ValidateCommandOrGroupInfo(
              module_dir_path,
              allow_non_existing_modules=self.__allow_non_existing_modules,
              exception_if_present=exception_if_present)

          if impl_path:
            # pylint: disable=protected-access
            if is_command:
              parent_group._commands_to_load[cmd_or_grp_name] = [impl_path]
            else:
              parent_group._groups_to_load[cmd_or_grp_name] = [impl_path]
          elif component:
            prefix = track.prefix + '.' if track.prefix else ''
            self.__missing_components[prefix + module_dot_path] = component
      except command_loading.CommandLoadFailure as e:
        log.exception(e)

    cli = self.__MakeCLI(top_group)

    return cli

  def __FindParentGroup(self, top_group, root):
    """Find the group that should be the parent of this command.

    Args:
      top_group: _CommandCommon, The top group in this CLI hierarchy.
      root: str, The dotted path of where this command or group should appear
        in the command tree.

    Returns:
      _CommandCommon, The group that should be parent of this new command tree
        or None if it could not be found.
    """
    if not root:
      return top_group
    root_path = root.split('.')
    group = top_group
    for part in root_path:
      group = group.LoadSubElement(part)
      if not group:
        return None
    return group

  def __ValidateCommandOrGroupInfo(
      self, impl_path, allow_non_existing_modules=False,
      exception_if_present=None):
    """Generates the information necessary to be able to load a command group.

    The group might actually be loaded now if it is the root of the SDK, or the
    information might be saved for later if it is to be lazy loaded.

    Args:
      impl_path: str, The file path to the command implementation for this
        command or group.
      allow_non_existing_modules: True to allow this module directory to not
        exist, False to raise an exception if this module does not exist.
      exception_if_present: Exception, An exception to throw if the module
        actually exists, or None.

    Raises:
      LayoutException: If the module directory does not exist and
      allow_non_existing is False.

    Returns:
      impl_path or None if the module directory does not exist and
      allow_non_existing is True.
    """
    module_root, module = os.path.split(impl_path)
    if not pkg_resources.IsImportable(module, module_root):
      if allow_non_existing_modules:
        return None
      raise command_loading.LayoutException(
          'The given module directory does not exist: {0}'.format(
              impl_path))
    elif exception_if_present:
      # pylint: disable=raising-bad-type, This will be an actual exception.
      raise exception_if_present
    return impl_path

  def __AddBuiltinGlobalFlags(self, top_element):
    """Adds in calliope builtin global flags.

    This needs to happen immediately after the top group is loaded and before
    any other groups are loaded.  The flags must be present so when sub groups
    are loaded, the flags propagate down.

    Args:
      top_element: backend._CommandCommon, The root of the command tree.
    """
    calliope_base.FLAGS_FILE_FLAG.AddToParser(top_element.ai)
    calliope_base.FLATTEN_FLAG.AddToParser(top_element.ai)
    calliope_base.FORMAT_FLAG.AddToParser(top_element.ai)

    if self.__version_func is not None:
      top_element.ai.add_argument(
          '-v', '--version',
          do_not_propagate=True,
          category=calliope_base.COMMONLY_USED_FLAGS,
          action=actions.FunctionExitAction(self.__version_func),
          help='Print version information and exit. This flag is only available'
          ' at the global level.')

    top_element.ai.add_argument(
        '--configuration',
        metavar='CONFIGURATION',
        category=calliope_base.COMMONLY_USED_FLAGS,
        help="""\
        The configuration to use for this command invocation. For more
        information on how to use configurations, run:
        `gcloud topic configurations`.  You can also use the {0} environment
        variable to set the equivalent of this flag for a terminal
        session.""".format(config.CLOUDSDK_ACTIVE_CONFIG_NAME))

    top_element.ai.add_argument(
        '--verbosity',
        choices=log.OrderedVerbosityNames(),
        default=log.DEFAULT_VERBOSITY_STRING,
        category=calliope_base.COMMONLY_USED_FLAGS,
        help='Override the default verbosity for this command.',
        action=actions.StoreProperty(properties.VALUES.core.verbosity))

    # This should be a pure Boolean flag, but the alternate true/false explicit
    # value form is preserved for backwards compatibility. This flag and
    # is the only Cloud SDK outlier.
    # TODO(b/24095744): Add true/false deprecation message.
    top_element.ai.add_argument(
        '--user-output-enabled',
        metavar=' ',  # Help text will look like the flag does not have a value.
        nargs='?',
        default=None,  # Tri-valued, None => don't override the property.
        const='true',
        choices=('true', 'false'),
        action=actions.DeprecationAction(
            '--user-output-enabled',
            warn=(
                'The `{flag_name}` flag will no longer support the explicit use'
                ' of the `true/false` optional value in an upcoming release.'
            ),
            removed=False,
            show_message=lambda _: False,
            action=actions.StoreBooleanProperty(
                properties.VALUES.core.user_output_enabled
            ),
        ),
        help='Print user intended output to the console.',
    )

    top_element.ai.add_argument(
        '--log-http',
        default=None,  # Tri-valued, None => don't override the property.
        action=actions.StoreBooleanProperty(properties.VALUES.core.log_http),
        help='Log all HTTP server requests and responses to stderr.')

    top_element.ai.add_argument(
        '--authority-selector',
        default=None,
        action=actions.StoreProperty(properties.VALUES.auth.authority_selector),
        hidden=True,
        help='THIS ARGUMENT NEEDS HELP TEXT.')

    top_element.ai.add_argument(
        '--authorization-token-file',
        default=None,
        action=actions.StoreProperty(
            properties.VALUES.auth.authorization_token_file),
        hidden=True,
        help='THIS ARGUMENT NEEDS HELP TEXT.')

    top_element.ai.add_argument(
        '--credential-file-override',
        action=actions.StoreProperty(
            properties.VALUES.auth.credential_file_override),
        hidden=True,
        help='THIS ARGUMENT NEEDS HELP TEXT.')

    # Timeout value for HTTP requests.
    top_element.ai.add_argument(
        '--http-timeout',
        default=None,
        action=actions.StoreProperty(properties.VALUES.core.http_timeout),
        hidden=True,
        help='THIS ARGUMENT NEEDS HELP TEXT.')

    # --flags-file source line number hook.
    FLAG_INTERNAL_FLAG_FILE_LINE.AddToParser(top_element.ai)

  def __MakeCLI(self, top_element):
    """Generate a CLI object from the given data.

    Args:
      top_element: The top element of the command tree
        (that extends backend.CommandCommon).

    Returns:
      CLI, The generated CLI tool.
    """
    # Don't bother setting up logging if we are just doing a completion.
    if '_ARGCOMPLETE' not in os.environ or '_ARGCOMPLETE_TRACE' in os.environ:
      log.AddFileLogging(self.__logs_dir)
      verbosity_string = encoding.GetEncodedValue(os.environ,
                                                  '_ARGCOMPLETE_TRACE')
      if verbosity_string:
        verbosity = log.VALID_VERBOSITY_STRINGS.get(verbosity_string)
        log.SetVerbosity(verbosity)

    # Pre-load all commands if lazy loading is disabled.
    if properties.VALUES.core.disable_command_lazy_loading.GetBool():
      top_element.LoadAllSubElements(recursive=True)

    cli = CLI(self.__name, top_element, self.__pre_run_hooks,
              self.__post_run_hooks, self.__known_error_handler)
    return cli


class _CompletionFinder(argcomplete.CompletionFinder):
  """Calliope overrides for argcomplete.CompletionFinder.

  This makes calliope ArgumentInterceptor and actions objects visible to the
  argcomplete monkeypatcher.
  """

  def _patch_argument_parser(self):
    ai = self._parser
    self._parser = ai.parser
    active_parsers = super(_CompletionFinder, self)._patch_argument_parser()
    if ai:
      self._parser = ai
    return active_parsers

  def _get_completions(self, comp_words, cword_prefix, cword_prequote,
                       last_wordbreak_pos):
    active_parsers = self._patch_argument_parser()

    parsed_args = parser_extensions.Namespace()
    self.completing = True

    try:
      self._parser.parse_known_args(comp_words[1:], namespace=parsed_args)
    except BaseException:  # pylint: disable=broad-except
      pass

    self.completing = False

    completions = self.collect_completions(
        active_parsers, parsed_args, cword_prefix, lambda *_: None)
    completions = self.filter_completions(completions)
    return self.quote_completions(
        completions, cword_prequote, last_wordbreak_pos)

  def quote_completions(self, completions, cword_prequote, last_wordbreak_pos):
    """Returns the completion (less aggressively) quoted for the shell.

    If the word under the cursor started with a quote (as indicated by a
    nonempty ``cword_prequote``), escapes occurrences of that quote character
    in the completions, and adds the quote to the beginning of each completion.
    Otherwise, escapes *most* characters that bash splits words on
    (``COMP_WORDBREAKS``), and removes portions of completions before the first
    colon if (``COMP_WORDBREAKS``) contains a colon.

    If there is only one completion, and it doesn't end with a
    **continuation character** (``/``, ``:``, or ``=``), adds a space after
    the completion.

    Args:
      completions: The current completion strings.
      cword_prequote: The current quote character in progress, '' if none.
      last_wordbreak_pos: The index of the last wordbreak.

    Returns:
      The completions quoted for the shell.
    """
    # The *_special character sets are the only non-cosmetic changes from the
    # argcomplete original. We drop { '!', ' ', '\n' } from _NO_QUOTE_SPECIAL
    # and { '!' } from _DOUBLE_QUOTE_SPECIAL. argcomplete should make these
    # settable properties.
    no_quote_special = '\\();<>|&$* \t\n`"\''
    double_quote_special = '\\`"$'
    single_quote_special = '\\'
    continuation_special = '=/:'
    no_escaping_shells = ('tcsh', 'fish', 'zsh')

    # If the word under the cursor was quoted, escape the quote char.
    # Otherwise, escape most special characters and specially handle most
    # COMP_WORDBREAKS chars.
    if not cword_prequote:
      # Bash mangles completions which contain characters in COMP_WORDBREAKS.
      # This workaround has the same effect as __ltrim_colon_completions in
      # bash_completion (extended to characters other than the colon).
      if last_wordbreak_pos:
        completions = [c[last_wordbreak_pos + 1:] for c in completions]
      special_chars = no_quote_special
    elif cword_prequote == '"':
      special_chars = double_quote_special
    else:
      special_chars = single_quote_special

    if encoding.GetEncodedValue(os.environ,
                                '_ARGCOMPLETE_SHELL') in no_escaping_shells:
      # these shells escape special characters themselves.
      special_chars = ''
    elif cword_prequote == "'":
      # Nothing can be escaped in single quotes, so we need to close
      # the string, escape the single quote, then open a new string.
      special_chars = ''
      completions = [c.replace("'", r"'\''") for c in completions]

    for char in special_chars:
      completions = [c.replace(char, '\\' + char) for c in completions]

    if getattr(self, 'append_space', False):
      # Similar functionality in bash was previously turned off by supplying
      # the "-o nospace" option to complete. Now it is conditionally disabled
      # using "compopt -o nospace" if the match ends in a continuation
      # character. This code is retained for environments where this isn't
      # done natively.
      continuation_chars = continuation_special
      if len(completions) == 1 and completions[0][-1] not in continuation_chars:
        if not cword_prequote:
          completions[0] += ' '

    return completions


def _ArgComplete(ai, **kwargs):
  """Runs argcomplete.autocomplete on a calliope argument interceptor."""
  if '_ARGCOMPLETE' not in os.environ:
    return
  mute_stderr = None
  namespace = None
  try:
    # Monkeypatch argcomplete argparse Namespace to be the Calliope extended
    # Namespace so the parsed_args passed to the completers is an extended
    # Namespace object.
    namespace = argcomplete.argparse.Namespace
    argcomplete.argparse.Namespace = parser_extensions.Namespace
    # Monkeypatch disable argcomplete.mute_stderr if the caller wants to see
    # error output. This is indispensible for debugging Cloud SDK completers.
    # It's much less verbose than the argcomplete _ARC_DEBUG output.
    if '_ARGCOMPLETE_TRACE' in os.environ:
      mute_stderr = argcomplete.mute_stderr

      def _DisableMuteStderr():
        pass

      argcomplete.mute_stderr = _DisableMuteStderr

    completer = _CompletionFinder()
    # pylint: disable=not-callable
    completer(
        ai,
        always_complete_options=False,
        **kwargs)
  finally:
    if namespace:
      argcomplete.argparse.Namespace = namespace
    if mute_stderr:
      argcomplete.mute_stderr = mute_stderr


def _SubParsersActionCall(self, parser, namespace, values, option_string=None):
  """argparse._SubParsersAction.__call__ version 1.2.1 MonkeyPatch."""
  del option_string

  # pylint: disable=protected-access

  parser_name = values[0]
  arg_strings = values[1:]

  # set the parser name if requested
  if self.dest is not argparse.SUPPRESS:
    setattr(namespace, self.dest, parser_name)

  # select the parser
  try:
    parser = self._name_parser_map[parser_name]
  except KeyError:
    tup = parser_name, ', '.join(self._name_parser_map)
    msg = argparse._('unknown parser %r (choices: %s)' % tup)
    raise argparse.ArgumentError(self, msg)

  # parse all the remaining options into the namespace
  # store any unrecognized options on the object, so that the top
  # level parser can decide what to do with them
  namespace, arg_strings = parser.parse_known_args(arg_strings, namespace)
  if arg_strings:
    vars(namespace).setdefault(argparse._UNRECOGNIZED_ARGS_ATTR, [])
    getattr(namespace, argparse._UNRECOGNIZED_ARGS_ATTR).extend(arg_strings)

  # pylint: enable=protected-access


class CLI(object):
  """A generated command line tool."""

  def __init__(self, name, top_element, pre_run_hooks, post_run_hooks,
               known_error_handler):
    # pylint: disable=protected-access
    self.__name = name
    self.__parser = top_element._parser
    self.__top_element = top_element
    self.__pre_run_hooks = pre_run_hooks
    self.__post_run_hooks = post_run_hooks
    self.__known_error_handler = known_error_handler

  def _TopElement(self):
    return self.__top_element

  @property
  def name(self):
    return self.__name

  @property
  def top_element(self):
    return self.__top_element

  def IsValidCommand(self, cmd):
    """Checks if given command exists.

    Args:
      cmd: [str], The command path not including any arguments.

    Returns:
      True, if the given command exist, False otherwise.
    """
    return self.__top_element.IsValidSubPath(cmd)

  def Execute(self, args=None, call_arg_complete=True):
    """Execute the CLI tool with the given arguments.

    Args:
      args: [str], The arguments from the command line or None to use sys.argv
      call_arg_complete: Call the _ArgComplete function if True

    Returns:
      The result of executing the command determined by the command
      implementation.

    Raises:
      ValueError: for ill-typed arguments.
    """
    if isinstance(args, six.string_types):
      raise ValueError('Execute expects an iterable of strings, not a string.')

    # The argparse module does not handle unicode args when run in Python 2
    # because it uses str(x) even when type(x) is unicode. This sets itself up
    # for failure because it converts unicode strings back to byte strings which
    # will trigger ASCII codec exceptions. It works in Python 3 because str() is
    # equivalent to unicode() in Python 3. The next Pythonically magic and dirty
    # statement coaxes the Python 3 behavior out of argparse running in
    # Python 2. Doing it here ensures that the workaround is in place for
    # calliope argparse use cases.
    argparse.str = six.text_type
    # We need the argparse 1.2.1 patch in _SubParsersActionCall.
    if argparse.__version__ == '1.1':
      argparse._SubParsersAction.__call__ = _SubParsersActionCall  # pylint: disable=protected-access

    if call_arg_complete:
      _ArgComplete(self.__top_element.ai)

    if not args:
      args = argv_utils.GetDecodedArgv()[1:]

    # Look for a --configuration flag and update property state based on
    # that before proceeding to the main argparse parse step.
    named_configs.FLAG_OVERRIDE_STACK.PushFromArgs(args)
    properties.VALUES.PushInvocationValues()

    # Set the command name in case an exception happens before the command name
    # is finished parsing.
    command_path_string = self.__name
    specified_arg_names = None

    # Convert py2 args to text.
    argv = [console_attr.Decode(arg) for arg in args] if six.PY2 else args
    old_user_output_enabled = None
    old_verbosity = None
    try:
      args = self.__parser.parse_args(_ApplyFlagsFile(argv))
      if args.CONCEPT_ARGS is not None:
        args.CONCEPT_ARGS.ParseConcepts()
      calliope_command = args._GetCommand()  # pylint: disable=protected-access
      command_path_string = '.'.join(calliope_command.GetPath())
      specified_arg_names = args.GetSpecifiedArgNames()
      # If the CLI has not been reloaded since the last command execution (e.g.
      # in test runs), args.CONCEPTS may contain cached values.
      if args.CONCEPTS is not None:
        args.CONCEPTS.Reset()

      # -h|--help|--document are dispatched by parse_args and never get here.

      # Now that we have parsed the args, reload the settings so the flags will
      # take effect.  These will use the values from the properties.
      old_user_output_enabled = log.SetUserOutputEnabled(None)
      old_verbosity = log.SetVerbosity(None)

      # Set the command_name property so it is persisted until the process ends.
      # Only do this for the top level command that can be detected by looking
      # at the stack. It will have one initial level, and another level added by
      # the PushInvocationValues earlier in this method.
      if len(properties.VALUES.GetInvocationStack()) == 2:
        properties.VALUES.metrics.command_name.Set(command_path_string)
      # Set the invocation value for all commands, this is lost when popped
      properties.VALUES.SetInvocationValue(
          properties.VALUES.metrics.command_name, command_path_string, None)

      for hook in self.__pre_run_hooks:
        hook.Run(command_path_string)

      resources = calliope_command.Run(cli=self, args=args)

      for hook in self.__post_run_hooks:
        hook.Run(command_path_string)

      # Preserve generator or static list resources.

      if isinstance(resources, types.GeneratorType):

        def _Yield():
          """Activates generator exceptions."""
          try:
            for resource in resources:
              yield resource
          except Exception as exc:  # pylint: disable=broad-except
            self._HandleAllErrors(exc, command_path_string, specified_arg_names)

        return _Yield()

      # Do this last. If there is an error, the error handler will log the
      # command execution along with the error.
      metrics.Commands(
          command_path_string, config.CLOUD_SDK_VERSION, specified_arg_names)
      return resources

    except Exception as exc:  # pylint: disable=broad-except
      self._HandleAllErrors(exc, command_path_string, specified_arg_names)

    finally:
      properties.VALUES.PopInvocationValues()
      named_configs.FLAG_OVERRIDE_STACK.Pop()
      # Reset these values to their previous state now that we popped the flag
      # values.
      if old_user_output_enabled is not None:
        log.SetUserOutputEnabled(old_user_output_enabled)
      if old_verbosity is not None:
        log.SetVerbosity(old_verbosity)

  def _HandleAllErrors(self, exc, command_path_string, specified_arg_names):
    """Handle all errors.

    Args:
      exc: Exception, The exception that was raised.
      command_path_string: str, The '.' separated command path.
      specified_arg_names: [str], The specified arg named scrubbed for metrics.

    Raises:
      exc or a core.exceptions variant that does not produce a stack trace.
    """
    error_extra_info = {'error_code': getattr(exc, 'exit_code', 1)}

    # Returns exc.payload.status if available. Otherwise, None.
    http_status_code = getattr(getattr(exc, 'payload', None),
                               'status_code', None)
    if http_status_code is not None:
      error_extra_info['http_status_code'] = http_status_code

    metrics.Commands(
        command_path_string, config.CLOUD_SDK_VERSION, specified_arg_names,
        error=exc.__class__, error_extra_info=error_extra_info)
    metrics.Error(command_path_string, exc.__class__, specified_arg_names,
                  error_extra_info=error_extra_info)

    exceptions.HandleError(exc, command_path_string, self.__known_error_handler)
