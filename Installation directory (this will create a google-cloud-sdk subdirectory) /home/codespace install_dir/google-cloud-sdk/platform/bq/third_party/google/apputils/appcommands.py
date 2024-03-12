#!/usr/bin/env python
# Copyright 2007 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS-IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""This module is the base for programs that provide multiple commands.

This provides command line tools that have a few shared global flags,
followed by a command name, followed by command specific flags,
then by arguments. That is:
  tool [--global_flags] command [--command_flags] [args]

The module is built on top of app.py and 'overrides' a bit of it. However
the interface is mostly the same. The main difference is that your main
is supposed to register commands and return without further execution
of the commands; pre checking is of course welcome! Also your
global initialization should call appcommands.Run() rather than app.run().

To register commands use AddCmd() or AddCmdFunc().  AddCmd() is used
for commands that derive from class Cmd and the AddCmdFunc() is used
to wrap simple functions.

This module itself registers the command 'help' that allows users
to retrieve help for all or specific commands.

Example:

<code>
from mx import DateTime


class CmdDate(appcommands.Cmd):
  \"\"\"This docstring contains the help for the date command.\"\"\"

  def Run(self, argv):
    print DateTime.now()


def main(argv):
  appcommands.AddCmd('date', CmdDate, command_aliases=['data_now'])


if __name__ == '__main__':
  appcommands.Run()
</code>

In the above example the name of the registered command on the command line is
'date'. Thus, to get the date you would execute:
  tool date
The above example also added the command alias 'data_now' which allows to
replace 'tool date' with 'tool data_now'.

To get a list of available commands run:
  tool help
For help with a specific command, you would execute:
  tool help date
For help on flags run one of the following:
  tool --help
Note that 'tool --help' gives you information on global flags, just like for
applications that do not use appcommand. Likewise 'tool --helpshort' and the
other help-flags from app.py are also available.

The above example also demonstrates that you only have to call
  appcommands.Run()
and register your commands in main() to initialize your program with appcommands
(and app).

Handling of flags:
  Flags can be registered just as with any other google tool using flags.py.
  In addition you can also provide command specific flags. To do so simply add
  flags registering code into the __init__ function of your Cmd classes passing
  parameter flag_values to any flags registering calls. These flags will get
  copied to the global flag list, so that once the command is detected they
  behave just like any other flag. That means these flags won't be available
  for other commands. Note that it is possible to register flags with more
  than one command.

Getting help:
  This module activates formatting and wrapping to help output. That is
  the main difference to help created from app.py. So just as with app.py,
  appcommands.py will create help from the main modules main __doc__.
  But it adds the new 'help' command that allows you to get a list of
  all available commands.  Each command's help will be followed by the
  registered command specific flags along with their defaults and help.
  After help for all commands there will also be a list of all registered
  global flags with their defaults and help.

  The text for the command's help can best be supplied by overwriting the
  __doc__ property of the Cmd classes for commands registered with AddCmd() or
  the __doc__ property of command functions registered AddCmdFunc().

Inner working:
  This module interacts with app.py by replacing its inner start dispatcher.
  The replacement version basically does the same, registering help flags,
  checking whether help flags were present, and calling the main module's main
  function. However unlike app.py, this module epxpects main() to only register
  commands and then to return. After having all commands registered
  appcommands.py will then parse the remaining arguments for any registered
  command. If one is found it will get executed. Otherwise a short usage info
  will be displayed.

  Each provided command must be an instance of Cmd. If commands get registered
  from global functions using AddCmdFunc() then the helper class _FunctionalCmd
  will be used in the registering process.
"""



import os
import pdb
import sys
import traceback

from google.apputils import app
import gflags as flags

FLAGS = flags.FLAGS


# module exceptions:
class AppCommandsError(Exception):
  """The base class for all flags errors."""
  pass


_cmd_argv = None        # remaining arguments with index 0 = sys.argv[0]
_cmd_list = {}          # list of commands index by name (_Cmd instances)
_cmd_alias_list = {}    # list of command_names index by command_alias


def GetAppBasename():
  """Returns the friendly basename of this application."""
  base = os.path.basename(sys.argv[0]).split('.')
  return base[0]


def ShortHelpAndExit(message=None):
  """Display optional message, followed by a note on how to get help, then exit.

  Args:
    message: optional message to display
  """
  sys.stdout.flush()
  if message is not None:
    sys.stderr.write('%s\n' % message)
  sys.stderr.write("Run '%s help' to get help\n" % GetAppBasename())
  sys.exit(1)


def GetCommandList():
  """Return list of registered commands."""
  # pylint: disable-msg=W0602
  global _cmd_list
  return _cmd_list


def GetCommandAliasList():
  """Return list of registered command aliases."""
  # pylint: disable-msg=W0602
  global _cmd_alias_list
  return _cmd_alias_list


def GetFullCommandList():
  """Return list of registered commands, including aliases."""
  all_cmds = dict(GetCommandList())
  for cmd_alias, cmd_name in GetCommandAliasList().iteritems():
    all_cmds[cmd_alias] = all_cmds.get(cmd_name)
  return all_cmds


def GetCommandByName(name):
  """Get the command or None if name is not a registered command.

  Args:
    name:  name of command to look for

  Returns:
    Cmd instance holding the command or None
  """
  return GetCommandList().get(GetCommandAliasList().get(name))


def GetCommandArgv():
  """Return list of remaining args."""
  return _cmd_argv


def GetMaxCommandLength():
  """Returns the length of the longest registered command."""
  return max([len(cmd_name) for cmd_name in GetCommandList()])


class Cmd(object):
  """Abstract class describing and implementing a command.

  When creating code for a command, at least you have to derive this class
  and override method Run(). The other methods of this class might be
  overridden as well. Check their documentation for details. If the command
  needs any specific flags, use __init__ for registration.
  """

  def __init__(self, name, flag_values, command_aliases=None):
    """Initialize and check whether self is actually a Cmd instance.

    This can be used to register command specific flags. If you do so
    remember that you have to provide the 'flag_values=flag_values'
    parameter to any flags.DEFINE_*() call.

    Args:
      name:            Name of the command
      flag_values:     FlagValues() instance that needs to be passed as
                       flag_values parameter to any flags registering call.
      command_aliases: A list of command aliases that the command can be run as.
    Raises:
      AppCommandsError: if self is Cmd (Cmd is abstract)
    """
    self._command_name = name
    self._command_aliases = command_aliases
    self._command_flags = flag_values
    self._all_commands_help = None
    if type(self) is Cmd:
      raise AppCommandsError('Cmd is abstract and cannot be instantiated')

  def Run(self, argv):
    """Execute the command. Must be provided by the implementing class.

    Args:
      argv: Remaining command line arguments after parsing flags and command
            (that is a copy of sys.argv at the time of the function call with
            all parsed flags removed).

    Returns:
      0 for success, anything else for failure (must return with integer).
      Alternatively you may return None (or not use a return statement at all).

    Raises:
      AppCommandsError: Always as in must be overwritten
    """
    raise AppCommandsError('%s.%s.Run() is not implemented' % (
        type(self).__module__, type(self).__name__))

  def CommandRun(self, argv):
    """Execute the command with given arguments.

    First register and parse additional flags. Then run the command.

    Returns:
      Command return value.

    Args:
      argv: Remaining command line arguments after parsing command and flags
            (that is a copy of sys.argv at the time of the function call with
            all parsed flags removed).
    """
    # Register flags global when run normally
    FLAGS.AppendFlagValues(self._command_flags)
    # Prepare flags parsing, to redirect help, to show help for command
    orig_app_usage = app.usage

    def ReplacementAppUsage(shorthelp=0, writeto_stdout=1, detailed_error=None,
                            exitcode=None):
      AppcommandsUsage(shorthelp, writeto_stdout, detailed_error, exitcode=1,
                       show_cmd=self._command_name, show_global_flags=True)
    app.usage = ReplacementAppUsage
    # Parse flags and restore app.usage afterwards
    try:
      try:
        argv = ParseFlagsWithUsage(argv)
        # Run command
        if FLAGS.run_with_pdb:
          ret = pdb.runcall(self.Run, argv)
        else:
          ret = self.Run(argv)
        if ret is None:
          ret = 0
        else:
          assert isinstance(ret, int)
        return ret
      except app.UsageError as error:
        app.usage(shorthelp=1, detailed_error=error, exitcode=error.exitcode)
    finally:
      # Restore app.usage and remove this command's flags from the global flags.
      app.usage = orig_app_usage
      for flag_name in self._command_flags.FlagDict():
        delattr(FLAGS, flag_name)

  def CommandGetHelp(self, unused_argv, cmd_names=None):
    """Get help string for command.

    Args:
      unused_argv: Remaining command line flags and arguments after parsing
                   command (that is a copy of sys.argv at the time of the
                   function call with all parsed flags removed); unused in this
                   default implementation, but may be used in subclasses.
      cmd_names:   Complete list of commands for which help is being shown at
                   the same time. This is used to determine whether to return
                   _all_commands_help, or the command's docstring.
                   (_all_commands_help is used, if not None, when help is being
                   shown for more than one command, otherwise the command's
                   docstring is used.)

    Returns:
      Help string, one of the following (by order):
        - Result of the registered 'help' function (if any)
        - Doc string of the Cmd class (if any)
        - Default fallback string
    """
    if (type(cmd_names) is list and len(cmd_names) > 1 and
        self._all_commands_help is not None):
      return flags.DocToHelp(self._all_commands_help)
    elif self.__doc__:
      return flags.DocToHelp(self.__doc__)
    else:
      return 'No help available'

  def CommandGetAliases(self):
    """Get aliases for command.

    Returns:
      aliases: list of aliases for the command.
    """
    return self._command_aliases


class _FunctionalCmd(Cmd):
  """Class to wrap functions as CMD instances.

  Args:
    cmd_func:   command function
  """

  def __init__(self, name, flag_values, cmd_func, all_commands_help=None,
               **kargs):
    """Create a functional command.

    Args:
      name:        Name of command
      flag_values: FlagValues() instance that needs to be passed as flag_values
                   parameter to any flags registering call.
      cmd_func:    Function to call when command is to be executed.
    """
    Cmd.__init__(self, name, flag_values, **kargs)
    self._all_commands_help = all_commands_help
    self._cmd_func = cmd_func

  def CommandGetHelp(self, unused_argv, cmd_names=None):
    """Get help for command.

    Args:
      unused_argv: Remaining command line flags and arguments after parsing
                   command (that is a copy of sys.argv at the time of the
                   function call with all parsed flags removed); unused in this
                   implementation.
      cmd_names:   By default, if help is being shown for more than one command,
                   and this command defines _all_commands_help, then
                   _all_commands_help will be displayed instead of the class
                   doc. cmd_names is used to determine the number of commands
                   being displayed and if only a single command is display then
                   the class doc is returned.

    Returns:
      __doc__ property for command function or a message stating there is no
      help.
    """
    if (type(cmd_names) is list and len(cmd_names) > 1 and
        self._all_commands_help is not None):
      return flags.DocToHelp(self._all_commands_help)
    if self._cmd_func.__doc__ is not None:
      return flags.DocToHelp(self._cmd_func.__doc__)
    else:
      return 'No help available'

  def Run(self, argv):
    """Execute the command with given arguments.

    Args:
      argv: Remaining command line flags and arguments after parsing command
            (that is a copy of sys.argv at the time of the function call with
            all parsed flags removed).

    Returns:
      Command return value.
    """
    return self._cmd_func(argv)


def _AddCmdInstance(command_name, cmd, command_aliases=None):
  """Add a command from a Cmd instance.

  Args:
    command_name:    name of the command which will be used in argument parsing
    cmd:             Cmd instance to register
    command_aliases: A list of command aliases that the command can be run as.

  Raises:
    AppCommandsError: is command is already registered OR cmd is not a subclass
                      of Cmd
    AppCommandsError: if name is already registered OR name is not a string OR
                      name is too short OR name does not start with a letter OR
                      name contains any non alphanumeric characters besides
                      '_', '-', or ':'.
  """
  # Update global command list.
  # pylint: disable-msg=W0602
  global _cmd_list
  global _cmd_alias_list
  if not issubclass(cmd.__class__, Cmd):
    raise AppCommandsError('Command must be an instance of commands.Cmd')

  for name in [command_name] + (command_aliases or []):
    _CheckCmdName(name)
    _cmd_alias_list[name] = command_name

  _cmd_list[command_name] = cmd


def _CheckCmdName(name_or_alias):
  """Only allow strings for command names and aliases (reject unicode as well).

  Args:
    name_or_alias: properly formatted string name or alias.

  Raises:
    AppCommandsError: is command is already registered OR cmd is not a subclass
                      of Cmd
    AppCommandsError: if name is already registered OR name is not a string OR
                      name is too short OR name does not start with a letter OR
                      name contains any non alphanumeric characters besides
                      '_', '-', or ':'.
  """
  if name_or_alias in GetCommandAliasList():
    raise AppCommandsError("Command or Alias '%s' already defined" %
                           name_or_alias)
  if not isinstance(name_or_alias, str) or len(name_or_alias) <= 1:
    raise AppCommandsError("Command '%s' not a string or too short"
                           % str(name_or_alias))
  if not name_or_alias[0].isalpha():
    raise AppCommandsError("Command '%s' does not start with a letter"
                           % name_or_alias)
  if [c for c in name_or_alias if not (c.isalnum() or c in ('_', '-', ':'))]:
    raise AppCommandsError("Command '%s' contains non alphanumeric characters"
                           % name_or_alias)


def AddCmd(command_name, cmd_factory, **kargs):
  """Add a command from a Cmd subclass or factory.

  Args:
    command_name:    name of the command which will be used in argument parsing
    cmd_factory:     A callable whose arguments match those of Cmd.__init__ and
                     returns a Cmd. In the simplest case this is just a subclass
                     of Cmd.
    command_aliases: A list of command aliases that the command can be run as.

  Raises:
    AppCommandsError: if calling cmd_factory does not return an instance of Cmd.
  """
  cmd = cmd_factory(command_name, flags.FlagValues(), **kargs)

  if not isinstance(cmd, Cmd):
    raise AppCommandsError('Command must be an instance of commands.Cmd')

  _AddCmdInstance(command_name, cmd, **kargs)


def AddCmdFunc(command_name, cmd_func, command_aliases=None,
               all_commands_help=None):
  """Add a new command to the list of registered commands.

  Args:
    command_name:      name of the command which will be used in argument
                       parsing
    cmd_func:          command function, this function received the remaining
                       arguments as its only parameter. It is supposed to do the
                       command work and then return with the command result that
                       is being used as the shell exit code.
    command_aliases:   A list of command aliases that the command can be run as.
    all_commands_help: Help message to be displayed in place of func.__doc__
                       when all commands are displayed.
  """
  _AddCmdInstance(command_name,
                  _FunctionalCmd(command_name, flags.FlagValues(), cmd_func,
                                 command_aliases=command_aliases,
                                 all_commands_help=all_commands_help),
                  command_aliases)


class _CmdHelp(Cmd):
  """Standard help command.

  Allows to provide help for all or specific commands.
  """

  def Run(self, argv):
    """Execute help command.

    If an argument is given and that argument is a registered command
    name, then help specific to that command is being displayed.
    If the command is unknown then a fatal error will be displayed. If
    no argument is present then help for all commands will be presented.

    If a specific command help is being generated, the list of commands is
    temporarily replaced with one containing only that command. Thus the call
    to usage() will only show help for that command. Otherwise call usage()
    will show help for all registered commands as it sees all commands.

    Args:
      argv: Remaining command line flags and arguments after parsing command
            (that is a copy of sys.argv at the time of the function call with
            all parsed flags removed).
            So argv[0] is the program and argv[1] will be the first argument to
            the call. For instance 'tool.py help command' will result in argv
            containing ('tool.py', 'command'). In this case the list of
            commands is searched for 'command'.

    Returns:
      1 for failure
    """
    if len(argv) > 1 and argv[1] in GetFullCommandList():
      show_cmd = argv[1]
    else:
      show_cmd = None
    AppcommandsUsage(shorthelp=0, writeto_stdout=1, detailed_error=None,
                     exitcode=1, show_cmd=show_cmd, show_global_flags=False)

  def CommandGetHelp(self, unused_argv, cmd_names=None):
    """Returns: Help for command."""
    cmd_help = ('Help for all or selected command:\n'
                '\t%(prog)s help [<command>]\n\n'
                'To retrieve help with global flags:\n'
                '\t%(prog)s --help\n\n'
                'To retrieve help with flags only from the main module:\n'
                '\t%(prog)s --helpshort [<command>]\n\n'
                % {'prog': GetAppBasename()})
    return flags.DocToHelp(cmd_help)


def GetSynopsis():
  """Get synopsis for program.

  Returns:
    Synopsis including program basename.
  """
  return '%s [--global_flags] <command> [--command_flags] [args]' % (
      GetAppBasename())


def _UsageFooter(detailed_error, cmd_names):
  """Output a footer at the end of usage or help output.

  Args:
    detailed_error: additional detail about why usage info was presented.
    cmd_names:      list of command names for which help was shown or None.
  Returns:
    Generated footer that contains 'Run..' messages if appropriate.
  """
  footer = []
  if not cmd_names or len(cmd_names) == 1:
    footer.append("Run '%s help' to see the list of available commands."
                  % GetAppBasename())
  if not cmd_names or len(cmd_names) == len(GetCommandList()):
    footer.append("Run '%s help <command>' to get help for <command>."
                  % GetAppBasename())
  if detailed_error is not None:
    if footer:
      footer.append('')
    footer.append('%s' % detailed_error)
  return '\n'.join(footer)


def AppcommandsUsage(shorthelp=0, writeto_stdout=0, detailed_error=None,
                     exitcode=None, show_cmd=None, show_global_flags=False):
  """Output usage or help information.

  Extracts the __doc__ string from the __main__ module and writes it to
  stderr. If that string contains a '%s' then that is replaced by the command
  pathname. Otherwise a default usage string is being generated.

  The output varies depending on the following:
  - FLAGS.help
  - FLAGS.helpshort
  - show_cmd
  - show_global_flags

  Args:
    shorthelp:      print only command and main module flags, rather than all.
    writeto_stdout: write help message to stdout, rather than to stderr.
    detailed_error: additional details about why usage info was presented.
    exitcode:       if set, exit with this status code after writing help.
    show_cmd:       show help for this command only (name of command).
    show_global_flags: show help for global flags.
  """
  if writeto_stdout:
    stdfile = sys.stdout
  else:
    stdfile = sys.stderr

  prefix = ''.rjust(GetMaxCommandLength() + 2)
  # Deal with header, containing general tool documentation
  doc = sys.modules['__main__'].__doc__
  if doc:
    help_msg = flags.DocToHelp(doc.replace('%s', sys.argv[0]))
    stdfile.write(flags.TextWrap(help_msg, flags.GetHelpWidth()))
    stdfile.write('\n\n\n')
  if not doc or doc.find('%s') == -1:
    synopsis = 'USAGE: ' + GetSynopsis()
    stdfile.write(flags.TextWrap(synopsis, flags.GetHelpWidth(), '       ',
                                 ''))
    stdfile.write('\n\n\n')
  # Special case just 'help' registered, that means run as 'tool --help'.
  if len(GetCommandList()) == 1:
    cmd_names = []
  else:
    # Show list of commands
    if show_cmd is None or show_cmd == 'help':
      cmd_names = GetCommandList().keys()
      cmd_names.sort()
      stdfile.write('Any of the following commands:\n')
      doc = ', '.join(cmd_names)
      stdfile.write(flags.TextWrap(doc, flags.GetHelpWidth(), '  '))
      stdfile.write('\n\n\n')
    # Prepare list of commands to show help for
    if show_cmd is not None:
      cmd_names = [show_cmd]  # show only one command
    elif FLAGS.help or FLAGS.helpshort or shorthelp:
      cmd_names = []
    else:
      cmd_names = GetCommandList().keys()  # show all commands
      cmd_names.sort()
  # Show the command help (none, one specific, or all)
  for name in cmd_names:
    command = GetCommandByName(name)
    cmd_help = command.CommandGetHelp(GetCommandArgv(), cmd_names=cmd_names)
    cmd_help = cmd_help.strip()
    all_names = ', '.join([name] + (command.CommandGetAliases() or []))
    if len(all_names) + 1 >= len(prefix) or not cmd_help:
      # If command/alias list would reach over help block-indent
      # start the help block on a new line.
      stdfile.write(flags.TextWrap(all_names, flags.GetHelpWidth()))
      stdfile.write('\n')
      prefix1 = prefix
    else:
      prefix1 = all_names.ljust(GetMaxCommandLength() + 2)
    if cmd_help:
      stdfile.write(flags.TextWrap(cmd_help, flags.GetHelpWidth(), prefix,
                                   prefix1))
      stdfile.write('\n\n')
    else:
      stdfile.write('\n')
    # When showing help for exactly one command we show its flags
    if len(cmd_names) == 1:
      # Need to register flags for command prior to be able to use them.
      # We do not register them globally so that they do not reappear.
      # pylint: disable-msg=W0212
      cmd_flags = command._command_flags
      if cmd_flags.RegisteredFlags():
        stdfile.write('%sFlags for %s:\n' % (prefix, name))
        stdfile.write(cmd_flags.GetHelp(prefix+'  '))
        stdfile.write('\n\n')
  stdfile.write('\n')
  # Now show global flags as asked for
  if show_global_flags:
    stdfile.write('Global flags:\n')
    if shorthelp:
      stdfile.write(FLAGS.MainModuleHelp())
    else:
      stdfile.write(FLAGS.GetHelp())
    stdfile.write('\n')
  else:
    stdfile.write("Run '%s --help' to get help for global flags."
                  % GetAppBasename())
  stdfile.write('\n%s\n' % _UsageFooter(detailed_error, cmd_names))
  if exitcode is not None:
    sys.exit(exitcode)


def ParseFlagsWithUsage(argv):
  """Parse the flags, exiting (after printing usage) if they are unparseable.

  Args:
    argv: command line arguments

  Returns:
    remaining command line arguments after parsing flags
  """
  # Update the global commands.
  # pylint: disable-msg=W0603
  global _cmd_argv
  try:
    _cmd_argv = FLAGS(argv)
    return _cmd_argv
  except flags.FlagsError as error:
    ShortHelpAndExit('FATAL Flags parsing error: %s' % error)


def GetCommand(command_required):
  """Get the command or return None (or issue an error) if there is none.

  Args:
    command_required: whether to issue an error if no command is present

  Returns:
    command or None, if command_required is True then return value is a valid
    command or the program will exit. The program also exits if a command was
    specified but that command does not exist.
  """
  # Update the global commands.
  # pylint: disable-msg=W0603
  global _cmd_argv
  _cmd_argv = ParseFlagsWithUsage(_cmd_argv)
  if len(_cmd_argv) < 2:
    if command_required:
      ShortHelpAndExit('FATAL Command expected but none given')
    return None
  command = GetCommandByName(_cmd_argv[1])
  if command is None:
    ShortHelpAndExit("FATAL Command '%s' unknown" % _cmd_argv[1])
  del _cmd_argv[1]
  return command


def _CommandsStart():
  """Main initialization.

  This initializes flag values, and calls __main__.main().  Only non-flag
  arguments are passed to main().  The return value of main() is used as the
  exit status.

  """
  app.RegisterAndParseFlagsWithUsage()
  # The following is supposed to return after registering additional commands
  try:
    sys.modules['__main__'].main(GetCommandArgv())
  # If sys.exit was called, return with error code.
  except SystemExit as e:
    sys.exit(e.code)
  except Exception as error:
    traceback.print_exc()  # Print a backtrace to stderr.
    ShortHelpAndExit('\nFATAL error in main: %s' % error)

  if len(GetCommandArgv()) > 1:
    command = GetCommand(command_required=True)
  else:
    command = GetCommandByName('help')
  sys.exit(command.CommandRun(GetCommandArgv()))


def Run():
  """This must be called from __main__ modules main, instead of app.run().

  app.run will base its actions on its stacktrace.

  Returns:
    app.run()
  """
  app.parse_flags_with_usage = ParseFlagsWithUsage
  app.really_start = _CommandsStart
  app.usage = _ReplacementAppUsage
  return app.run()


# Always register 'help' command
AddCmd('help', _CmdHelp)


def _ReplacementAppUsage(shorthelp=0, writeto_stdout=0, detailed_error=None,
                         exitcode=None):
  AppcommandsUsage(shorthelp, writeto_stdout, detailed_error, exitcode=exitcode,
                   show_cmd=None, show_global_flags=True)


if __name__ == '__main__':
  Run()
