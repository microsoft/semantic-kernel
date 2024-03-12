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

"""The gcloud interactive shell completion."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import io
import os
import sys
import threading
import time

from googlecloudsdk.calliope import parser_completer
from googlecloudsdk.command_lib.interactive import parser
from googlecloudsdk.command_lib.meta import generate_cli_trees
from googlecloudsdk.core import module_util
from googlecloudsdk.core.console import console_attr
from prompt_toolkit import completion

import six


_INVALID_COMMAND_COUNT = -1
_INVALID_ARG_COMMAND_COUNT = _INVALID_COMMAND_COUNT - 1
_URI_SEP = '://'


# TODO(b/115505558): add a visual element test framework
def _GenerateCompletions(event):
  """completion.generate_completions override that auto selects singletons."""

  b = event.current_buffer
  if not b.complete_state:
    # First TAB -- display the completions in a menu.
    event.cli.start_completion(insert_common_part=True, select_first=False)
  elif len(b.complete_state.current_completions) == 1:
    # Second TAB with only one completion -- select it dadgummit.
    b.apply_completion(b.complete_state.current_completions[0])
  else:
    # Second and subsequent TABs -- rotate through the menu.
    b.complete_next()


completion.generate_completions = _GenerateCompletions  # MONKEYPATCH!


def _PrettyArgs(args):
  """Pretty prints args into a string and returns it."""
  buf = io.StringIO()
  buf.write('[')
  for arg in args:
    buf.write('({},{})'.format(arg.value or '""', arg.token_type.name))
  buf.write(']')
  return buf.getvalue()


def _Split(path):
  """Returns the list of component names in path, treating foo:// as a dir."""
  urisep = _URI_SEP
  uri_index = path.find(urisep)
  if uri_index >= 0:
    n = uri_index + len(_URI_SEP)
    return [path[:n-1]] + path[n:].split('/')
  return path.split('/')


def _Dirname(path):
  """Returns the dirname of path, '' if it's '.'."""
  return '/'.join(_Split(path)[:-1])


class CacheArg(object):
  """A completion cache arg."""

  def __init__(self, prefix, completions):
    self.prefix = prefix
    self.completions = completions
    self.dirs = {}

  def IsValid(self):
    return self.completions is not None

  def Invalidate(self):
    self.command_count = _INVALID_ARG_COMMAND_COUNT
    self.completions = None
    self.dirs = {}


class CompletionCache(object):
  """A per-arg cache of completions for the command line under construction.

  Since we have no details on the compeleted values this cache is only for the
  current command line. This means that async activities by other commands
  (creating files, instances, resources) may not be seen until the current
  command under construction is executed.

  Attributes:
    args: The list of CacheArg args holding the completion state for each arg.
    completer: The completer object.
    command_count: The completer.cli.command_count value for the current cache.
  """

  def __init__(self, completer):
    self.args = []
    self.completer = completer
    self.command_count = _INVALID_COMMAND_COUNT

  def IsValid(self):
    return self.command_count == self.completer.cli.command_count

  def ArgMatch(self, args, index):
    """Returns True if args[index] matches the cache prefix for index."""
    if not self.args[index].IsValid():
      # Only concerned with cached args.
      return True
    return args[index].value.startswith(self.args[index].prefix)

  def Lookup(self, args):
    """Returns the cached completions for the last arg in args or None."""

    # No joy if it's not cached or if the command has already executed.

    if not args or not self.IsValid():
      return None
    if len(args) > len(self.args):
      return None

    # Args before the last must match the cached arg value.

    last_arg_index = len(args) - 1
    for i in range(last_arg_index):
      if not self.ArgMatch(args, i):
        return None

    # The last arg must have completions and match the completion prefix.

    if not self.args[last_arg_index].IsValid():
      return None

    # Check directory boundaries.

    a = args[last_arg_index].value
    if a.endswith('/'):
      # Entering a subdir, maybe it's already cached.
      parent = a[:-1]
      self.completer.debug.dir.text(parent)
      prefix, completions = self.args[last_arg_index].dirs.get(parent,
                                                               (None, None))
      if not completions:
        return None
      self.args[last_arg_index].prefix = prefix
      self.args[last_arg_index].completions = completions
    elif a in self.args[last_arg_index].dirs:
      # Backing up into a parent dir.
      self.completer.debug.dir.text(_Dirname(a))
      prefix, completions = self.args[last_arg_index].dirs.get(_Dirname(a),
                                                               (None, None))
      if completions:
        self.args[last_arg_index].prefix = prefix
        self.args[last_arg_index].completions = completions

    # The last arg must match the completion prefix.

    if not self.ArgMatch(args, last_arg_index):
      return None

    # Found valid matching completions in the cache.

    return [c for c in self.args[last_arg_index].completions if c.startswith(a)]

  def Update(self, args, completions):
    """Updates completions for the last arg in args."""
    self.command_count = self.completer.cli.command_count
    last_arg_index = len(args) - 1
    for i in range(last_arg_index):
      if i >= len(self.args):
        # Grow the cache.
        self.args.append(CacheArg(args[i].value, None))
      elif not self.ArgMatch(args, i):
        self.args[i].Invalidate()
    a = args[last_arg_index].value

    # Extend the cache if necessary.

    if last_arg_index == len(self.args):
      self.args.append(CacheArg(a, completions))

    # Update the last arg.

    if (not self.args[last_arg_index].IsValid() or
        not a.startswith(self.args[last_arg_index].prefix) or
        a.endswith('/')):
      if a.endswith('/'):
        # Subdir completions.
        if not self.args[last_arg_index].dirs:
          # Default completions belong to ".".
          self.args[last_arg_index].dirs[''] = (
              self.args[last_arg_index].prefix,
              self.args[last_arg_index].completions)
        self.args[last_arg_index].dirs[a[:-1]] = (a, completions)

    # Check for dir completions trying to slip by.

    if completions and '/' in completions[0][:-1] and '/' not in a:
      dirs = {}
      for comp in completions:
        if comp.endswith('/'):
          comp = comp[:-1]
          mark = '/'
        else:
          mark = ''
        parts = _Split(comp)
        if mark:
          parts[-1] += mark
        for i in range(len(parts)):
          d = '/'.join(parts[:i])
          if d not in dirs:
            dirs[d] = []
          comp = '/'.join(parts[:i + 1])
          if comp.endswith(':/'):
            comp += '/'
          if comp not in dirs[d]:
            dirs[d].append(comp)
      for d, c in six.iteritems(dirs):
        marked = d
        if marked.endswith(':/'):
          marked += '/'
        self.args[last_arg_index].dirs[d] = marked, c
    else:
      self.args[last_arg_index].prefix = a
      self.args[last_arg_index].completions = completions

    # Invalidate the rest of the cache.

    for i in range(last_arg_index + 1, len(self.args)):
      self.args[i].Invalidate()


class Spinner(object):
  """A Spinner to show when completer takes too long to respond.

  Some completer calls take too long, specially those that fetch remote
  resources. An instance of this class can be used as a context manager wrapping
  slow completers to get spinmarks while the completer fetches.

  Attributes:
    _done_loading: Boolean flag indicating whether ticker thread is working.
    _set_spinner: Function reference to InteractiveCliCompleter's spinner
      setter.
    _spin_marks: List of unicode spinmarks to be cycled while loading.
    _ticker: Thread instance that handles displaying the spinner.
    _ticker_index: Integer specifying the last iteration index in _spin_marks.
    _TICKER_INTERVAL: Float specifying time between ticker rotation in
      milliseconds.
    _ticker_length: Integer spcifying length of _spin_marks.
    _TICKER_WAIT: Float specifying the wait time before ticking in milliseconds.
    _TICKER_WAIT_CHECK_INTERVAL: Float specifying interval time to break wait
      in milliseconds.
  """

  _TICKER_INTERVAL = 100
  _TICKER_WAIT = 200
  _TICKER_WAIT_CHECK_INTERVAL = 10

  def __init__(self, set_spinner):
    self._done_loading = False
    self._spin_marks = console_attr.GetConsoleAttr()\
        .GetProgressTrackerSymbols().spin_marks
    self._ticker = None
    self._ticker_index = 0
    self._ticker_length = len(self._spin_marks)
    self._set_spinner = set_spinner

  def _Mark(self, spin_mark):
    """Marks spin_mark on stdout and moves cursor back."""
    sys.stdout.write(spin_mark + '\b')
    sys.stdout.flush()

  def Stop(self):
    """Erases last spin_mark and joins the ticker thread."""
    self._Mark(' ')
    self._done_loading = True
    if self._ticker:
      self._ticker.join()

  def _Ticker(self):
    """Waits for _TICKER_WAIT and then starts printing the spinner."""
    for _ in range(Spinner._TICKER_WAIT // Spinner._TICKER_WAIT_CHECK_INTERVAL):
      time.sleep(Spinner._TICKER_WAIT_CHECK_INTERVAL/1000.0)
      if self._done_loading:
        break
    while not self._done_loading:
      spin_mark = self._spin_marks[self._ticker_index]
      self._Mark(spin_mark)
      self._ticker_index = (self._ticker_index + 1) % self._ticker_length
      time.sleep(Spinner._TICKER_INTERVAL/1000.0)

  def __enter__(self):
    self._set_spinner(self)
    self._ticker = threading.Thread(target=self._Ticker)
    self._ticker.start()
    return self

  def __exit__(self, *args):
    self.Stop()
    self._set_spinner(None)


def _NameSpaceDict(args):
  """Returns a namespace dict given parsed CLI tree args."""
  namespace = {}
  name = None
  for arg in args:
    if arg.token_type == parser.ArgTokenType.POSITIONAL:
      name = arg.tree.get(parser.LOOKUP_NAME)
      value = arg.value
    elif arg.token_type == parser.ArgTokenType.FLAG:
      name = arg.tree.get(parser.LOOKUP_NAME)
      if name:
        if name.startswith('--'):
          name = name[2:]
        name = name.replace('-', '_')
      continue
    elif not name:
      continue
    elif arg.token_type == parser.ArgTokenType.FLAG_ARG:
      value = arg.value
    else:
      continue
    namespace[name] = value
  return namespace


class ModuleCache(object):
  """A local completer module cache item to minimize intra-command latency.

  Some CLI tree positionals and flag values have completers that are specified
  by module paths. These path strings point to a completer method or class that
  can be imported at run-time. The ModuleCache keeps track of modules that have
  already been imported, the most recent completeion result, and a timeout for
  the data. This saves on import lookup, and more importantly, repeated
  completion requests within a short window. Users really love that TAB key.

  Attributes:
    _TIMEOUT: Newly updated choices stale after this many seconds.
    completer_class: The completer class.
    coshell: The coshell object.
    choices: The cached choices.
    stale: choices stale after this time.
  """

  _TIMEOUT = 60

  def __init__(self, completer_class):
    self.completer_class = completer_class
    self.choices = None
    self.stale = 0
    self.timeout = ModuleCache._TIMEOUT


class InteractiveCliCompleter(completion.Completer):
  """A prompt_toolkit interactive CLI completer.

  This is the wrapper class for the get_completions() callback that is
  called when characters are added to the default input buffer. It's a bit
  hairy because it maintains state between calls to avoid duplicate work,
  especially for completer calls of unknown cost.

  cli.command_count is a serial number that marks the current command line in
  progress. Some of the cached state is reset when get_completions() detects
  that it has changed.

  Attributes:
    cli: The interactive CLI object.
    coshell: The interactive coshell object.
    debug: The debug object.
    empty: Completion request is on an empty arg if True.
    hidden: Complete hidden commands and flags if True.
    last: The last character before the cursor in the completion request.
    manpage_generator: The unknown command man page generator object.
    module_cache: The completer module path cache object.
    parsed_args: The parsed args namespace passed to completer modules.
    parser: The interactive parser object.
    prefix_completer_command_count: If this is equal to cli.command_count then
      command PREFIX TAB completion is enabled. This completion searches PATH
      for executables matching the current PREFIX token. It's fairly expensive
      and volumninous, so we don't want to do it for every completion event.
    _spinner: Private instance of Spinner used for loading during
      ArgCompleter.
  """

  def __init__(self, cli=None, coshell=None, debug=None,
               interactive_parser=None, args=None, hidden=False,
               manpage_generator=True):
    self.arg_cache = CompletionCache(self)
    self.cli = cli
    self.coshell = coshell
    self.debug = debug
    self.hidden = hidden
    self.manpage_generator = manpage_generator
    self.module_cache = {}
    self.parser = interactive_parser
    self.parsed_args = args
    self.empty = False
    self._spinner = None
    self.last = ''
    generate_cli_trees.CliTreeGenerator.MemoizeFailures(True)
    self.reset()

  def reset(self):
    """Resets any cached state for the current command being composed."""
    self.DisableExecutableCompletions()
    if self._spinner:
      self._spinner.Stop()
      self._spinner = None

  def SetSpinner(self, spinner):
    """Sets and Unsets current spinner object."""
    self._spinner = spinner

  def DoExecutableCompletions(self):
    """Returns True if command prefix args should use executable completion."""
    return self.prefix_completer_command_count == self.cli.command_count

  def DisableExecutableCompletions(self):
    """Disables command prefix arg executable completion."""
    self.prefix_completer_command_count = _INVALID_COMMAND_COUNT

  def EnableExecutableCompletions(self):
    """Enables command prefix arg executable completion."""
    self.prefix_completer_command_count = self.cli.command_count

  def IsPrefixArg(self, args):
    """Returns True if the input buffer cursor is in a command prefix arg."""
    return not self.empty and args[-1].token_type == parser.ArgTokenType.PREFIX

  def IsSuppressed(self, info):
    """Returns True if the info for a command, group or flag is hidden."""
    if self.hidden:
      return info.get(parser.LOOKUP_NAME, '').startswith('--no-')
    return info.get(parser.LOOKUP_IS_HIDDEN)

  def get_completions(self, doc, event):
    """Yields the completions for doc.

    Args:
      doc: A Document instance containing the interactive command line to
           complete.
      event: The CompleteEvent that triggered this completion.

    Yields:
      Completion instances for doc.
    """

    self.debug.tabs.count().text('@{}:{}'.format(
        self.cli.command_count,
        'explicit' if event.completion_requested else 'implicit'))

    # TAB on empty line toggles command PREFIX executable completions.

    if not doc.text_before_cursor and event.completion_requested:
      if self.DoExecutableCompletions():
        self.DisableExecutableCompletions()
      else:
        self.EnableExecutableCompletions()
      return

    # Parse the arg types from the input buffer.

    args = self.parser.ParseCommand(doc.text_before_cursor)
    if not args:
      return

    # The default completer order.

    completers = (
        self.CommandCompleter,
        self.FlagCompleter,
        self.PositionalCompleter,
        self.InteractiveCompleter,
    )

    # Command PREFIX token may need a different order.

    if self.IsPrefixArg(args) and (
        self.DoExecutableCompletions() or event.completion_requested):
      completers = (self.InteractiveCompleter,)

    self.last = doc.text_before_cursor[-1] if doc.text_before_cursor else ''
    self.empty = self.last.isspace()
    self.event = event

    self.debug.last.text(self.last)
    self.debug.tokens.text(_PrettyArgs(args))

    # Apply the completers in order stopping at the first one that does not
    # return None.

    for completer in completers:
      choices, offset = completer(args)
      if choices is None:
        continue
      self.debug.tag(completer.__name__).count().text(len(list(choices)))
      if offset is None:
        # The choices are already completion.Completion objects.
        for choice in choices:
          yield choice
      else:
        for choice in sorted(choices):
          yield completion.Completion(choice, start_position=offset)
      return

  def CommandCompleter(self, args):
    """Returns the command/group completion choices for args or None.

    Args:
      args: The CLI tree parsed command args.

    Returns:
      (choices, offset):
        choices - The list of completion strings or None.
        offset - The completion prefix offset.
    """
    arg = args[-1]

    if arg.value.startswith('-'):
      # A flag, not a command.
      return None, 0

    elif self.IsPrefixArg(args):
      # The root command name arg ("argv[0]"), the first token at the beginning
      # of the command line or the next token after a shell statement separator.
      node = self.parser.root
      prefix = arg.value

    elif arg.token_type in (parser.ArgTokenType.COMMAND,
                            parser.ArgTokenType.GROUP) and not self.empty:
      # A command/group with an exact CLI tree match. It could also be a prefix
      # of other command/groups, so fallthrough to default choices logic.
      node = args[-2].tree if len(args) > 1 else self.parser.root
      prefix = arg.value

    elif arg.token_type == parser.ArgTokenType.GROUP:
      # A command group with an exact CLI tree match.
      if not self.empty:
        return [], 0
      node = arg.tree
      prefix = ''

    elif arg.token_type == parser.ArgTokenType.UNKNOWN:
      # Unknown command arg type.
      prefix = arg.value
      if (self.manpage_generator and not prefix and
          len(args) == 2 and args[0].value):
        node = generate_cli_trees.LoadOrGenerate(args[0].value)
        if not node:
          return None, 0
        self.parser.root[parser.LOOKUP_COMMANDS][args[0].value] = node
      elif len(args) > 1 and args[-2].token_type == parser.ArgTokenType.GROUP:
        node = args[-2].tree
      else:
        return None, 0

    else:
      # Don't know how to complete this arg.
      return None, 0

    choices = [k for k, v in six.iteritems(node[parser.LOOKUP_COMMANDS])
               if k.startswith(prefix) and not self.IsSuppressed(v)]
    if choices:
      return choices, -len(prefix)

    return None, 0

  def ArgCompleter(self, args, arg, value):
    """Returns the flag or positional completion choices for arg or [].

    Args:
      args: The CLI tree parsed command args.
      arg: The flag or positional argument.
      value: The (partial) arg value.

    Returns:
      (choices, offset):
        choices - The list of completion strings or None.
        offset - The completion prefix offset.
    """
    choices = arg.get(parser.LOOKUP_CHOICES)
    if choices:
      # static choices
      return [v for v in choices if v.startswith(value)], -len(value)

    if not value and not self.event.completion_requested:
      return [], 0

    module_path = arg.get(parser.LOOKUP_COMPLETER)
    if not module_path:
      return [], 0

    # arg with a completer
    cache = self.module_cache.get(module_path)
    if not cache:
      cache = ModuleCache(module_util.ImportModule(module_path))
      self.module_cache[module_path] = cache
    prefix = value
    if not isinstance(cache.completer_class, type):
      cache.choices = cache.completer_class(prefix=prefix)
    elif cache.stale < time.time():
      old_dict = self.parsed_args.__dict__
      self.parsed_args.__dict__ = {}
      self.parsed_args.__dict__.update(old_dict)
      self.parsed_args.__dict__.update(_NameSpaceDict(args))
      completer = parser_completer.ArgumentCompleter(
          cache.completer_class,
          parsed_args=self.parsed_args)
      with Spinner(self.SetSpinner):
        cache.choices = completer(prefix='')
      self.parsed_args.__dict__ = old_dict
      cache.stale = time.time() + cache.timeout
    if arg.get(parser.LOOKUP_TYPE) == 'list':
      parts = value.split(',')
      prefix = parts[-1]
    if not cache.choices:
      return [], 0
    return [v for v in cache.choices if v.startswith(prefix)], -len(prefix)

  def FlagCompleter(self, args):
    """Returns the flag completion choices for args or None.

    Args:
      args: The CLI tree parsed command args.

    Returns:
      (choices, offset):
        choices - The list of completion strings or None.
        offset - The completion prefix offset.
    """
    arg = args[-1]

    if (arg.token_type == parser.ArgTokenType.FLAG_ARG and
        args[-2].token_type == parser.ArgTokenType.FLAG and
        (not arg.value and self.last in (' ', '=') or
         arg.value and not self.empty)):
      # A flag value arg with the cursor in the value so it's OK to complete.
      flag = args[-2].tree
      return self.ArgCompleter(args, flag, arg.value)

    elif arg.token_type == parser.ArgTokenType.FLAG:
      # A flag arg with an exact CLI tree match.
      if not self.empty:
        # The cursor is in the flag arg. See if it's a prefix of other flags.
        # Search backwards in args to find the rightmost command node.
        flags = {}
        for a in reversed(args):
          if a.tree and parser.LOOKUP_FLAGS in a.tree:
            flags = a.tree[parser.LOOKUP_FLAGS]
            break
        completions = [k for k, v in six.iteritems(flags)
                       if k != arg.value and
                       k.startswith(arg.value) and
                       not self.IsSuppressed(v)]
        if completions:
          completions.append(arg.value)
          return completions, -len(arg.value)

      # Flag completed as it.
      flag = arg.tree
      if flag.get(parser.LOOKUP_TYPE) != 'bool':
        completions, offset = self.ArgCompleter(args, flag, '')
        # Massage the completions to insert space between flag and it's value.
        if not self.empty and self.last != '=':
          completions = [' ' + c for c in completions]
        return completions, offset

    elif arg.value.startswith('-'):
      # The arg is a flag prefix. Return the matching completions.
      return [k for k, v in six.iteritems(arg.tree[parser.LOOKUP_FLAGS])
              if k.startswith(arg.value) and
              not self.IsSuppressed(v)], -len(arg.value)

    return None, 0

  def PositionalCompleter(self, args):
    """Returns the positional completion choices for args or None.

    Args:
      args: The CLI tree parsed command args.

    Returns:
      (choices, offset):
        choices - The list of completion strings or None.
        offset - The completion prefix offset.
    """
    arg = args[-1]

    if arg.token_type == parser.ArgTokenType.POSITIONAL:
      return self.ArgCompleter(args, arg.tree, arg.value)

    return None, 0

  def InteractiveCompleter(self, args):
    """Returns the interactive completion choices for args or None.

    Args:
      args: The CLI tree parsed command args.

    Returns:
      (choices, offset):
        choices - The list of completion strings or None.
        offset - The completion prefix offset.
    """
    # If the input command line ended with a space then the split command line
    # must end with an empty string if it doesn't already. This instructs the
    # completer to complete the next arg.

    if self.empty and args[-1].value:
      args = args[:]
      args.append(parser.ArgToken('', parser.ArgTokenType.UNKNOWN, None))

    # First check the cache.

    completions = self.arg_cache.Lookup(args)
    if not completions:

      # Only call the coshell completer on an explicit TAB request.

      prefix = self.DoExecutableCompletions() and self.IsPrefixArg(args)
      if not self.event.completion_requested and not prefix:
        return None, None

      # Call the coshell completer and update the cache.

      command = [arg.value for arg in args]
      with Spinner(self.SetSpinner):
        completions = self.coshell.GetCompletions(command, prefix=prefix)
      self.debug.get.count()
      if not completions:
        return None, None
      self.arg_cache.Update(args, completions)
    else:
      self.debug.hit.count()

    last = args[-1].value
    offset = -len(last)

    # No dropdown for singletons so just return the original completion.

    if False and len(completions) == 1 and completions[0].startswith(last):
      return completions, offset

    # Make path completions play nice with dropdowns. Add trailing '/' for dirs
    # in the dropdown but not the completion. User types '/' to select a dir
    # and ' ' to select a path.
    #
    # NOTE: '/' instead of os.path.sep since the coshell is bash even on Windows

    chop = len(os.path.dirname(last))
    uri_sep = _URI_SEP
    uri_sep_index = completions[0].find(uri_sep)
    if uri_sep_index > 0:
      # Treat the completions as URI paths.
      if not last:
        chop = uri_sep_index + len(uri_sep)

    # Construct the completion result list. No list comprehension here because
    # MakePathCompletion() could return None.
    result = []
    strip_trailing_slash = len(completions) != 1
    for c in completions:
      path_completion = self.MakePathCompletion(
          c, offset, chop, strip_trailing_slash)
      if path_completion:
        result.append(path_completion)
    return result, None

  @classmethod
  def MakePathCompletion(cls, value, offset, chop, strip_trailing_slash=True):
    """Returns the Completion object for a file/uri path completion value.

    Args:
      value: The file/path completion value string.
      offset: The Completion object offset used for dropdown display.
      chop: The minimum number of chars to chop from the dropdown items.
      strip_trailing_slash: Strip trailing '/' if True.

    Returns:
      The Completion object for a file path completion value or None if the
      chopped/stripped value is empty.
    """

    display = value
    if chop:
      display = display[chop:].lstrip('/')
    if not display:
      return None
    if strip_trailing_slash and not value.endswith(_URI_SEP):
      value = value.rstrip('/')
    if not value:
      return None
    return completion.Completion(value, display=display, start_position=offset)
