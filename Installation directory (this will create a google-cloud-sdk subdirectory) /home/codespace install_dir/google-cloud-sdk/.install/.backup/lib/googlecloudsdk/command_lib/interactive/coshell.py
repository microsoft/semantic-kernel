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

"""The local coshell module.

A coshell is an interactive non-login /bin/bash running as a coprocess. It has
the same stdin, stdout and stderr as the caller and reads command lines from a
pipe. Only one command runs at a time. ctrl-c interrupts and kills the currently
running command but does not kill the coshell. The coshell process exits when
the shell 'exit' command is executed. State is maintained by the coshell across
commands, including the current working directory and local and environment
variables. ~/.bashrc, if it exists, is sourced into the coshell at startup.
This gives the caller the opportunity to set up aliases and default
'set -o ...' shell modes.

Usage:
  cosh = coshell.Coshell()
  while True:
    command = <the next command line to run>
    try:
      command_exit_status = cosh.Run(command)
    except coshell.CoshellExitError:
      break
  coshell_exit_status = cosh.Close()

This module contains three Coshell implementations:
  * _UnixCoshell using /bin/bash
  * _MinGWCoshell using MinGW bash or git bash
  * _WindowsCoshell using cmd.exe, does not support state across commands
On the first instantiation Coshell.__init__() determines what implementation to
use. All subsequent instantiations will use the same implementation.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import abc
import locale
import os
import re
import signal
import subprocess
from googlecloudsdk.core.util import encoding
import six

COSHELL_ENV = 'COSHELL'
COSHELL_VERSION = '1.1'


_GET_COMPLETIONS_INIT = r"""
# Defines functions to support completion requests to the coshell.
#
# The only coshell specific shell globals are functions prefixed by __coshell_.
# All other globals are part of the bash completion api.

__coshell_get_completions__() {
  # Prints the completions for the (partial) command line "$@" terminated by
  # a blank line sentinel. The first arg is either 'prefix' for command
  # executable completeions or 'default' for default completions.

  local command completion_function last_word next_to_last_word
  local COMP_CWORD COMP_LINE COMP_POINT COMP_WORDS COMPREPLY=()

  (( $# )) || {
    printf '\n'
    return
  }

  command=$1
  COMP_WORDS=( "$@" )

  # Get the command specific completion function.
  set -- $(complete -p "$command" 2>/dev/null)
  if (( ! $# )); then
    # Load the completion function for the command.
    _completion_loader "$command"
    set -- $(complete -p "$command" 2>/dev/null)
  fi
  # Check if it was loaded.
  if (( $# )); then
    # There is an explicit completer.
    shift $(( $# - 2 ))
    completion_function=$1
  else
    # Use the coshell default completer.
    __coshell_get_file_completions__ "${COMP_WORDS[${#COMP_WORDS[*]}-1]}"
    return
  fi

  # Set up the completion call stack -- really, this is the api?
  COMP_LINE=${COMP_WORDS[@]}
  COMP_POINT=${#COMP_LINE}

  # Index and value of the last word.
  COMP_CWORD=$(( ${#COMP_WORDS[@]} - 1 ))
  last_word=${COMP_WORDS[$COMP_CWORD]}

  # Value of the next to last word.
  if (( COMP_CWORD >= 2 )); then
    next_to_last_word=${COMP_WORDS[$((${COMP_CWORD}-1))]}
  else
    next_to_last_word=''
  fi

  # Execute the completion function. Some completers, like _python_argcomplete,
  # require $1, $2 and $3.
  if $completion_function "${command}" "${last_word}" "${next_to_last_word}" 2>/dev/null; then
    # Print the completions to stdout.
    printf '%s\n' "${COMPREPLY[@]}" ''
  else
    # Fall back to the coshell default completer on error.
    __coshell_get_file_completions__ "${COMP_WORDS[${#COMP_WORDS[@]}-1]}"
  fi
}

__coshell_get_executable_completions__() {
  # Prints the executable completions for $1 one per line, terminated by a
  # blank line sentinel.
  compgen -A command -- "$1"
  printf '\n'
}

__coshell_get_file_completions__() {
  # Prints the file completions for $1, with trailing / for dirs, one per line,
  # terminated by a blank line sentinel. We could almost use_filedir_xspec, but
  #   * it's not installed/sourced by default on some systems (like macos)
  #   * it's part of a ~2K line rc file with no clear way of slicing it out
  #   * ~ and $... are expanded in the completions
  if __coshell_var_brace_expand "$1"; then
    # ...$AB
    compgen -A variable -P "${1%\$*}\${" -S "}" -- "${1##*\$\{}"
  elif __coshell_var_plain_expand "$1"; then
    # ...${AB
    compgen -A variable -P "${1%\$*}\$" -- "${1##*\$}"
  else
    local word_raw word_exp word words=() x IFS=$'\n'
    word_raw=$1
    eval word_exp=\"$word_raw\"
    if [[ $word_exp == "$word_raw" ]]; then
      # No $... expansions, just add trailing / for dirs.
      words=( $(compgen -A file -- "$word_exp") )
      for word in ${words[@]}; do
        if [[ $word != */ ]]; then
          if [[ $word == \~* ]]; then
            eval x="$word"
          else
            x=$word
          fi
          [[ -d $x ]] && word+=/
        fi
        printf '%s\n' "$word"
      done
    else
      # $... expansions: expand for -d tests, return unexpanded completions with
      # trailing / for dirs. compgen -A file handles ~ but does not expand it,
      # too bad it doesn't do the same for $... expansions.
      local prefix_exp suffix_raw
      __coshell_suffix_raw "$word_raw"  # Sets suffix_raw.
      prefix_raw=${word_raw%"$suffix_raw"}
      prefix_exp=${word_exp%"$suffix_raw"}
      words=( $(compgen -A file "$word_exp") )
      for word in ${words[@]}; do
        [[ $word != */ && -d $word ]] && word+=/
        printf '%s\n' "${prefix_raw}${word#"$prefix_exp"}"
      done
    fi
  fi
  printf '\n'
}

__coshell_get_directory_completions__() {
  # Prints the directory completions for $1, with trailing /, one per line,
  # terminated by a blank line sentinel.
  if __coshell_var_brace_expand "$1"; then
    # ...$AB
    compgen -A variable -P "${1%\$*}\${" -S "}" -- "${1##*\$\{}"
  elif __coshell_var_plain_expand "$1"; then
    # ...${AB
    compgen -A variable -P "${1%\$*}\$" -- "${1##*\$}"
  else
    local word_raw word_exp word words=() x IFS=$'\n'
    word_raw=$1
    eval word_exp=\"$word_raw\"
    if [[ $word_exp == "$word_raw" ]]; then
      # No $... expansions, just add trailing / for dirs.
      words=( $(compgen -A directory -S/ -- "$word_exp") )
      printf '%s\n' "${words[@]}"
    else
      # $... expansions: return unexpanded completions with trailing /.
      local prefix_exp suffix_raw
      __coshell_suffix_raw "$word_raw"  # Sets suffix_raw.
      prefix_raw=${word_raw%"$suffix_raw"}
      prefix_exp=${word_exp%"$suffix_raw"}
      words=( $(compgen -A file -S/ -- "$word_exp") )
      for word in ${words[@]}; do
        printf '%s\n' "${prefix_raw}${word#"$prefix_exp"}"
      done
    fi
  fi
  printf '\n'
}

__coshell_default_completer__() {
  # The default interactive completer. Handles ~ and embedded $... expansion.
  local IFS=$'\n' completer=__coshell_get_file_completions__
  for o in "$@"; do
    case $o in
    -c) completer=__coshell_get_executable_completions__ ;;
    -d) completer=__coshell_get_directory_completions__ ;;
    esac
  done
  COMPREPLY=( $($completer "$cur") )
}

__coshell_init_completions__() {
  # Loads bash-completion if necessary.

  declare -F _completion_loader &>/dev/null || {
    source /usr/share/bash-completion/bash_completion 2>/dev/null || {
      _completion_loader() {
        return 1
      }
    }
  }

  # Defines bash version dependent functions.

  local x y

  x='${HOME}/tmp'
  y=${x##*\$?(\{)+([a-zA-Z0-90-9_])?(\})}
  if [[ $x != $y ]]; then
    # Modern bash.
    eval '
      __coshell_suffix_raw() {
        coshell_suffix_raw=${1##*\$?(\{)+([a-zA-Z0-90-9_])?(\})}
      }
    '
  else
    __coshell_suffix_raw() {
      suffix_raw=$(sed 's/.*\${*[a-zA-Z0-9_]*}*//' <<<"$1")
    }
  fi

  if eval '[[ x == *\$\{*([a-zA-Z0-90-9_]) ]]' 2>/dev/null; then
    # Modern bash.
    eval '
      __coshell_var_brace_expand() {
        [[ $1 == *\$\{*([a-zA-Z0-90-9_]) ]]
      }
      __coshell_var_plain_expand() {
        [[ $1 == *\$+([a-zA-Z0-90-9_]) ]]
      }
    '
  else
    __coshell_var_brace_expand() {
      __coshell_partial_expand=$(sed 's/.*\$\({*\)[a-zA-Z0-9_]*$/\1/' <<<"$1")
      [[ $1 && $__coshell_partial_expand == "{" ]]
    }
    __coshell_var_plain_expand() {
      __coshell_partial_expand=$(sed 's/.*\$\({*\)[a-zA-Z0-9_]*$/\1/' <<<"$1")
      [[ $1 && $__coshell_partial_expand == "" ]]
    }
  fi

  _filedir() {
    # Overrides the bash_completion function that completes internal $cur.
    __coshell_default_completer__ "$@"
  }

  _minimal() {
    # Overrides the bash_completion function that completes external COMP_WORDS.
    cur=${COMP_WORDS[$COMP_CWORD]}
    __coshell_default_completer__ "$@"
  }

  compopt() {
    # $completion_function is called by __coshell_get_file_completions__
    # outside a completion context. Any of those functions calling compopt will
    # get an annoying error and completely break completions. This override
    # ignores the errors -- the other coshell completer overrides should wash
    # them out.
    command compopt "$@" 2>/dev/null
    return 0
  }

}

__coshell_init_completions__
"""


class CoshellExitError(Exception):
  """The coshell exited."""

  def __init__(self, message, status=None):
    super(CoshellExitError, self).__init__(message)
    self.status = status


class _CoshellBase(six.with_metaclass(abc.ABCMeta, object)):
  """The local coshell base class.

  Attributes:
    _edit_mode: The coshell edit mode, one of {'emacs', 'vi'}.
    _ignore_eof: True if the coshell should ignore EOF on stdin and not exit.
    _set_modes_callback: Called when SetModesCallback() is called or when
      mutable shell modes may have changed.
    _state_is_preserved: True if shell process state is preserved across Run().
  """

  def __init__(self, state_is_preserved=True):
    self._set_modes_callback = None
    # Immutable coshell object properties.
    self._encoding = locale.getpreferredencoding()
    self._state_is_preserved = state_is_preserved
    # Mutable shell modes controlled by `set -o ...` and `set +o ...`.
    self._edit_mode = 'emacs'
    self._ignore_eof = False

  @property
  def edit_mode(self):
    return self._edit_mode

  @property
  def ignore_eof(self):
    return self._ignore_eof

  @property
  def state_is_preserved(self):
    return self._state_is_preserved

  @staticmethod
  def _ShellStatus(status):
    """Returns the shell $? status given a python Popen returncode."""
    if status is None:
      status = 0
    elif status < 0:
      status = 256 - status
    return status

  def _Decode(self, data):
    """Decodes external data if needed and returns internal string."""
    try:
      return data.decode(self._encoding)
    except (AttributeError, UnicodeError):
      return data

  def _Encode(self, string):
    """Encodes internal string if needed and returns external data."""
    try:
      return string.encode(self._encoding)
    except UnicodeError:
      return string

  def Close(self):
    """Closes the coshell connection and release any resources."""
    pass

  def SetModesCallback(self, callback):
    """Sets the callback function to be called when any mutable mode changed.

    If callback is not None then it is called immediately to initialize the
    caller.

    Args:
      callback: func() called when any mutable mode changed, None to disable.
    """
    self._set_modes_callback = callback
    if callback:
      callback()

  @abc.abstractmethod
  def Run(self, command, check_modes=True):
    """Runs command in the coshell and waits for it to complete.

    Args:
      command: The command line string to run. Must be a sytactically complete
        shell statement. Nothing is executed if there is a syntax error.
      check_modes: If True runs self._GetModes() after command has executed if
        command contains `set -o ...` or `set +o ...`.
    """
    pass

  @abc.abstractmethod
  def Interrupt(self, sig):
    """Sends the interrupt signal to the coshell."""
    pass

  def GetCompletions(self, args, prefix=False):
    """Returns the list of completion choices for args.

    Args:
      args: The list of command line argument strings to complete.
      prefix: Complete the last arg as a command prefix.
    """
    del args
    return None

  def Communicate(self, args, quote=True):
    """Runs args and returns the list of output lines, up to first empty one.

    Args:
      args: The list of command line arguments.
      quote: Shell quote args if True.

    Returns:
      The list of output lines from command args up to the first empty line.
    """
    del args
    return []


class _UnixCoshellBase(six.with_metaclass(abc.ABCMeta, _CoshellBase)):
  """The unix local coshell base class.

  Attributes:
    _shell: The coshell subprocess object.
  """

  SHELL_STATUS_EXIT = 'x'
  SHELL_STATUS_FD = 9
  SHELL_STDIN_FD = 8

  def __init__(self):
    super(_UnixCoshellBase, self).__init__()
    self.status = None
    self._status_fd = None
    self._shell = None

  @staticmethod
  def _Quote(command):
    """Quotes command in single quotes so it can be eval'd in coshell."""
    return "'{}'".format(command.replace("'", r"'\''"))

  def _Exited(self):
    """Raises the coshell exit exception."""
    try:
      self._WriteLine(':')
    except (IOError, OSError, ValueError):
      # Yeah, ValueError for IO on a closed file.
      pass
    status = self._ShellStatus(self._shell.returncode)
    raise CoshellExitError(
        'The coshell exited [status={}].'.format(status),
        status=status)

  def _ReadLine(self):
    """Reads and returns a decoded stripped line from the coshell."""
    return self._Decode(self._shell.stdout.readline()).strip()

  def _ReadStatusChar(self):
    """Reads and returns one encoded character from the coshell status fd."""
    return os.read(self._status_fd, 1)

  def _WriteLine(self, line):
    """Writes an encoded line to the coshell."""
    self._shell.communicate(self._Encode(line + '\n'))

  def _SendCommand(self, command):
    """Sends command to the coshell for execution."""
    try:
      self._shell.stdin.write(self._Encode(command + '\n'))
      self._shell.stdin.flush()
    except (IOError, OSError, ValueError):
      # Yeah, ValueError for IO on a closed file.
      self._Exited()

  def _GetStatus(self):
    """Gets the status of the last command sent to the coshell."""
    line = []
    shell_status_exit = self.SHELL_STATUS_EXIT.encode('ascii')
    while True:
      c = self._ReadStatusChar()
      if c in (None, b'\n', shell_status_exit):
        break
      line.append(c)
    status_string = self._Decode(b''.join(line))
    if not status_string.isdigit() or c == shell_status_exit:
      self._Exited()
    return int(status_string)

  def _GetModes(self):
    """Syncs the user settable modes of interest to the Coshell.

    Calls self._set_modes_callback if it was specified and any mode changed.
    """

    changed = False

    # Get the caller emacs/vi mode.
    if self.Run('set -o | grep -q "^vi.*on"', check_modes=False) == 0:
      if self._edit_mode != 'vi':
        changed = True
        self._edit_mode = 'vi'
    else:
      if self._edit_mode != 'emacs':
        changed = True
        self._edit_mode = 'emacs'

    # Get the caller ignoreeof setting.
    ignore_eof = self._ignore_eof
    self._ignore_eof = self.Run(
        'set -o | grep -q "^ignoreeof.*on"', check_modes=False) == 0
    if self._ignore_eof != ignore_eof:
      changed = True

    if changed and self._set_modes_callback:
      self._set_modes_callback()

  def GetPwd(self):
    """Gets the coshell pwd, sets local pwd, returns the pwd, None on error."""
    pwd = self.Communicate([r'printf "$PWD\n\n"'], quote=False)
    if len(pwd) == 1:
      try:
        os.chdir(pwd[0])
        return pwd[0]
      except OSError:
        pass
    return None

  def _GetUserConfigDefaults(self):
    """Consults the user shell config for defaults."""

    self._SendCommand(
        # For rc file tests.
        'COSHELL_VERSION={coshell_version};'
        # Set $? to $1.
        '_status() {{ return $1; }};'
        # .bashrc configures aliases and set -o modes. Must be done explicitly
        # because the input pipe makes bash think it's not interactive.
        '[[ -f $HOME/.bashrc ]] && source $HOME/.bashrc;'
        # The exit command hits this trap, reaped by _GetStatus() in Run().
        "trap 'echo $?{exit} >&{fdstatus}' 0;"
        # This catches interrupts so commands die while the coshell stays alive.
        'trap ":" 2;{get_completions_init}'
        .format(coshell_version=COSHELL_VERSION,
                exit=self.SHELL_STATUS_EXIT,
                fdstatus=self.SHELL_STATUS_FD,
                get_completions_init=_GET_COMPLETIONS_INIT))

    # Enable job control if supported.
    self._SendCommand('set -o monitor 2>/dev/null')

    # Enable alias expansion if supported.
    self._SendCommand('shopt -s expand_aliases 2>/dev/null')

    # Sync the user settable modes to the coshell.
    self._GetModes()

    # Set $? to 0.
    self._SendCommand('true')

  @abc.abstractmethod
  def _Run(self, command, check_modes=True):
    """Runs command in the coshell and waits for it to complete."""
    pass

  def Run(self, command, check_modes=True):
    """Runs command in the coshell and waits for it to complete."""
    status = 130  # assume the worst: 128 (had signal) + 2 (it was SIGINT)
    sigint = signal.signal(signal.SIGINT, signal.SIG_IGN)
    try:
      status = self._Run(command, check_modes=check_modes)
    except KeyboardInterrupt:
      pass
    finally:
      signal.signal(signal.SIGINT, sigint)
    return status

  def GetCompletions(self, args, prefix=False):
    """Returns the list of completion choices for args.

    Args:
      args: The list of command line argument strings to complete.
      prefix: Complete the last arg as a command prefix.

    Returns:
      The list of completions for args.
    """
    if prefix:
      completions = self.Communicate(['__coshell_get_executable_completions__',
                                      args[-1]])
    else:
      completions = self.Communicate(['__coshell_get_completions__'] + args)
    # Some shell completers return unsorted with dups -- that stops here.
    return sorted(set(completions))

  def Interrupt(self):
    """Sends the interrupt signal to the coshell."""
    self._shell.send_signal(signal.SIGINT)


class _UnixCoshell(_UnixCoshellBase):
  """The unix local coshell implementation.

  This implementation preserves coshell process state across Run().

  Attributes:
    _status_fd: The read side of the pipe where the coshell write 1 char status
      lines. The status line is used to mark the exit of the currently running
      command.
  """

  SHELL_PATH = '/bin/bash'

  def __init__(self, stdout=1, stderr=2):
    super(_UnixCoshell, self).__init__()

    # The dup/close/dup dance preserves caller fds that collide with SHELL_*_FD.

    try:
      caller_shell_status_fd = os.dup(self.SHELL_STATUS_FD)
    except OSError:
      caller_shell_status_fd = -1
    os.dup2(1, self.SHELL_STATUS_FD)

    try:
      caller_shell_stdin_fd = os.dup(self.SHELL_STDIN_FD)
    except OSError:
      caller_shell_stdin_fd = -1
    os.dup2(0, self.SHELL_STDIN_FD)

    self._status_fd, w = os.pipe()
    os.dup2(w, self.SHELL_STATUS_FD)
    os.close(w)

    # Check for an alternate coshell command.

    coshell_command_line = encoding.GetEncodedValue(os.environ, COSHELL_ENV)
    if coshell_command_line:
      shell_command = coshell_command_line.split(' ')
    else:
      shell_command = [self.SHELL_PATH]

    # Python 3 adds a restore_signals kwarg to subprocess.Popen that defaults to
    # True, and has the effect of restoring the subprocess's SIGPIPE handler to
    # the default action. Python 2, on the other hand, keeps the modified
    # SIGPIPE handler for the subprocess. The coshell relies on the latter
    # behavior.
    additional_kwargs = {} if six.PY2 else {'restore_signals': False}
    self._shell = subprocess.Popen(
        shell_command,
        env=os.environ,  # NOTE: Needed to pass mocked environ to children.
        stdin=subprocess.PIPE,
        stdout=stdout,
        stderr=stderr,
        close_fds=False,
        **additional_kwargs)

    if caller_shell_status_fd >= 0:
      os.dup2(caller_shell_status_fd, self.SHELL_STATUS_FD)
      os.close(caller_shell_status_fd)
    else:
      os.close(self.SHELL_STATUS_FD)

    if caller_shell_stdin_fd >= 0:
      os.dup2(caller_shell_stdin_fd, self.SHELL_STDIN_FD)
      os.close(caller_shell_stdin_fd)
    else:
      os.close(self.SHELL_STDIN_FD)

    self._GetUserConfigDefaults()

  def Close(self):
    """Closes the coshell connection and release any resources."""
    if self._status_fd >= 0:
      os.close(self._status_fd)
      self._status_fd = -1
    try:
      self._WriteLine('exit')  # This closes internal fds.
    except (IOError, ValueError):
      # Yeah, ValueError for IO on a closed file.
      pass
    return self._ShellStatus(self._shell.returncode)

  def _Run(self, command, check_modes=True):
    """Runs command in the coshell and waits for it to complete."""
    self._SendCommand(
        'command eval {command} <&{fdin} && echo 0 >&{fdstatus} || '
        '{{ status=$?; echo $status 1>&{fdstatus}; _status $status; }}'.format(
            command=self._Quote(command),
            fdstatus=self.SHELL_STATUS_FD,
            fdin=self.SHELL_STDIN_FD))
    status = self._GetStatus()

    # Re-check shell shared state and modes.
    if check_modes:
      if re.search(r'\bset\s+[-+]o\s+\w', command):
        self._GetModes()
      if re.search(r'\bcd\b', command):
        self.GetPwd()

    return status

  def Communicate(self, args, quote=True):
    """Runs args and returns the list of output lines, up to first empty one.

    Args:
      args: The list of command line arguments.
      quote: Shell quote args if True.

    Returns:
      The list of output lines from command args up to the first empty line.
    """
    if quote:
      command = ' '.join([self._Quote(arg) for arg in args])
    else:
      command = ' '.join(args)
    self._SendCommand('{command} >&{fdstatus}\n'.format(
        command=command, fdstatus=self.SHELL_STATUS_FD))
    lines = []
    line = []
    while True:
      try:
        c = self._ReadStatusChar()
      except (IOError, OSError, ValueError):
        # Yeah, ValueError for IO on a closed file.
        self._Exited()
      if c in (None, b'\n'):
        if not line:
          break
        lines.append(self._Decode(b''.join(line).rstrip()))
        line = []
      else:
        line.append(c)
    return lines


class _MinGWCoshell(_UnixCoshellBase):
  """The MinGW local coshell implementation.

  This implementation preserves coshell process state across Run().

  NOTE: The Windows subprocess module passes fds 0,1,2 to the child process and
  no others. It is possble to pass handles that can be converted to/from fds,
  but the child process needs to know what handles to convert back to fds. Until
  we figure out how to reconstitute handles as fds >= 3 we are stuck with
  restricting fds 0,1,2 to be /dev/tty, via shell redirection, for Run(). For
  internal communication fds 0,1 are pipes. Luckily this works for the shell
  interactive prompt. Unfortunately this fails for the test environment.
  """

  SHELL_PATH = None  # Determined by the Coshell dynamic class below.
  STDIN_PATH = '/dev/tty'
  STDOUT_PATH = '/dev/tty'

  def __init__(self):
    super(_MinGWCoshell, self).__init__()
    self._shell = self._Popen()
    self._GetUserConfigDefaults()

  def _Popen(self):
    """Mockable popen+startupinfo so we can test on Unix."""
    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dWflags = subprocess.CREATE_NEW_PROCESS_GROUP
    return subprocess.Popen([self.SHELL_PATH],
                            stdin=subprocess.PIPE,
                            stdout=subprocess.PIPE,
                            startupinfo=startupinfo)

  def Close(self):
    """Closes the coshell connection and release any resources."""
    try:
      self._WriteLine('exit')  # This closes internal fds.
    except (IOError, ValueError):
      # Yeah, ValueError for IO on a closed file.
      pass
    return self._ShellStatus(self._shell.returncode)

  def _GetStatus(self):
    """Gets the status of the last command sent to the coshell."""
    status_string = self._ReadLine()
    if status_string.endswith(self.SHELL_STATUS_EXIT):
      c = self.SHELL_STATUS_EXIT
      status_string = status_string[:-1]
    else:
      c = ''
    if not status_string.isdigit() or c == self.SHELL_STATUS_EXIT:
      self._Exited()
    return int(status_string)

  def _Run(self, command, check_modes=True):
    """Runs command in the coshell and waits for it to complete."""
    self._SendCommand(
        "command eval {command} <'{stdin}' >>'{stdout}' && echo 0 || "
        "{{ status=$?; echo 1; (exit $status); }}".format(
            command=self._Quote(command),
            stdin=self.STDIN_PATH,
            stdout=self.STDOUT_PATH,
        ))
    status = self._GetStatus()

    # Re-check shell shared state and modes.
    if check_modes:
      if re.search(r'\bset\s+[-+]o\s+\w', command):
        self._GetModes()
      if re.search(r'\bcd\b', command):
        self.GetPwd()

    return status

  def Communicate(self, args, quote=True):
    """Runs args and returns the list of output lines, up to first empty one.

    Args:
      args: The list of command line arguments.
      quote: Shell quote args if True.

    Returns:
      The list of output lines from command args up to the first empty line.
    """
    if quote:
      command = ' '.join([self._Quote(arg) for arg in args])
    else:
      command = ' '.join(args)
    self._SendCommand(command + '\n')
    lines = []
    while True:
      try:
        line = self._ReadLine()
      except (IOError, OSError, ValueError):
        # Yeah, ValueError for IO on a closed file.
        self._Exited()
      if not line:
        break
      lines.append(line)
    return lines

  def Interrupt(self):
    """Sends the interrupt signal to the coshell."""
    self._shell.send_signal(signal.CTRL_C_EVENT)


class _WindowsCoshell(_CoshellBase):
  """The windows local coshell implementation.

  This implementation does not preserve shell coprocess state across Run().
  """

  def __init__(self):
    super(_WindowsCoshell, self).__init__(state_is_preserved=False)

  def Run(self, command, check_modes=False):
    """Runs command in the coshell and waits for it to complete."""
    del check_modes
    return subprocess.call(command, shell=True)

  def Interrupt(self):
    """Sends the interrupt signal to the coshell."""
    pass


def _RunningOnWindows():
  """Lightweight mockable Windows check."""
  try:
    return bool(WindowsError)
  except NameError:
    return False


class Coshell(object):
  """The local coshell implementation shim.

  This shim class delays os specific checks until the first instantiation. The
  checks are memoized in the shim class for subsequent instantiations.
  """

  _IMPLEMENTATION = None

  def __new__(cls, *args, **kwargs):
    if not cls._IMPLEMENTATION:
      if _RunningOnWindows():
        cls._IMPLEMENTATION = _WindowsCoshell
        # We do an explicit search rather than PATH lookup because:
        # (1) It's not clear that a git or MinGW installation automatically
        #     sets up PATH to point to sh.exe.
        # (2) Picking up any old sh.exe on PATH on a Windows system is dicey.
        for shell in [r'C:\MinGW\bin\sh.exe',
                      r'C:\Program Files\Git\bin\sh.exe']:
          if os.path.isfile(shell):
            cls._IMPLEMENTATION = _MinGWCoshell
            cls._IMPLEMENTATION.SHELL_PATH = shell
            break
      else:
        cls._IMPLEMENTATION = _UnixCoshell
    obj = cls._IMPLEMENTATION.__new__(cls._IMPLEMENTATION, *args, **kwargs)
    obj.__init__()  # The docs say this is unnecessary.
    return obj
