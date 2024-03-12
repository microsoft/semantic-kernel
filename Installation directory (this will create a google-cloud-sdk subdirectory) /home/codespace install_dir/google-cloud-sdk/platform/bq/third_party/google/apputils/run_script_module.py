#!/usr/bin/env python
# Copyright 2010 Google Inc. All Rights Reserved.
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

"""Script for running Google-style applications.

Unlike normal scripts run through setuptools console_script entry points,
Google-style applications must be run as top-level scripts.

Given an already-imported module, users can use the RunScriptModule function to
set up the appropriate executable environment to spawn a new Python process to
run the module as a script.

To use this technique in your project, first create a module called e.g.
stubs.py with contents like:

  from google.apputils import run_script_module

  def RunMyScript():
    import my.script
    run_script_module.RunScriptModule(my.script)

  def RunMyOtherScript():
    import my.other_script
    run_script_module.RunScriptModule(my.other_script)

Then, set up entry points in your setup.py that point to the functions in your
stubs module:

  setup(
      ...
      entry_points = {
          'console_scripts': [
              'my_script = my.stubs:RunMyScript',
              'my_other_script = my.stubs.RunMyOtherScript',
              ],
          },
      )

When your project is installed, setuptools will generate minimal wrapper scripts
to call your stub functions, which in turn execv your script modules. That's it!
"""

from __future__ import print_function
__author__ = 'dborowitz@google.com (Dave Borowitz)'

import os
import re
import sys


def FindEnv(progname):
  """Find the program in the system path.

  Args:
    progname: The name of the program.

  Returns:
    The full pathname of the program.

  Raises:
    AssertionError: if the program was not found.
  """
  for path in os.environ['PATH'].split(':'):
    fullname = os.path.join(path, progname)
    if os.access(fullname, os.X_OK):
      return fullname
  raise AssertionError(
      "Could not find an executable named '%s' in the system path" % progname)


def GetPdbArgs(python):
  """Try to get the path to pdb.py and return it in a list.

  Args:
    python: The full path to a Python executable.

  Returns:
    A list of strings. If a relevant pdb.py was found, this will be
    ['/path/to/pdb.py']; if not, return ['-m', 'pdb'] and hope for the best.
    (This latter technique will fail for Python 2.2.)
  """
  # Usually, python is /usr/bin/pythonxx and pdb is /usr/lib/pythonxx/pdb.py
  components = python.split('/')
  if len(components) >= 2:
    pdb_path = '/'.join(components[0:-2] + ['lib'] +
                        components[-1:] + ['pdb.py'])
    if os.access(pdb_path, os.R_OK):
      return [pdb_path]

  # No pdb module found in the python path, default to -m pdb
  return ['-m', 'pdb']


def StripDelimiters(s, beg, end):
  if s[0] == beg:
    assert s[-1] == end
    return (s[1:-1], True)
  else:
    return (s, False)


def StripQuotes(s):
  (s, stripped) = StripDelimiters(s, '"', '"')
  if not stripped:
    (s, stripped) = StripDelimiters(s, "'", "'")
  return s


def PrintOurUsage():
  """Print usage for the stub script."""
  print('Stub script %s (auto-generated). Options:' % sys.argv[0])
  print ('--helpstub               '
         'Show help for stub script.')
  print ('--debug_binary           '
         'Run python under debugger specified by --debugger.')
  print ('--debugger=<debugger>    '
         "Debugger for --debug_binary. Default: 'gdb --args'.")
  print ('--debug_script           '
         'Run wrapped script with python debugger module (pdb).')
  print ('--show_command_and_exit  '
         'Print command which would be executed and exit.')
  print ('These options must appear first in the command line, all others will '
         'be passed to the wrapped script.')


def RunScriptModule(module):
  """Run a module as a script.

  Locates the module's file and runs it in the current interpreter, or
  optionally a debugger.

  Args:
    module: The module object to run.
  """
  args = sys.argv[1:]

  debug_binary = False
  debugger = 'gdb --args'
  debug_script = False
  show_command_and_exit = False

  while args:
    if args[0] == '--helpstub':
      PrintOurUsage()
      sys.exit(0)
    if args[0] == '--debug_binary':
      debug_binary = True
      args = args[1:]
      continue
    if args[0] == '--debug_script':
      debug_script = True
      args = args[1:]
      continue
    if args[0] == '--show_command_and_exit':
      show_command_and_exit = True
      args = args[1:]
      continue
    matchobj = re.match('--debugger=(.+)', args[0])
    if matchobj is not None:
      debugger = StripQuotes(matchobj.group(1))
      args = args[1:]
      continue
    break

  # Now look for my main python source file
  # TODO(user): This will fail if the module was zipimported, which means
  # no egg depending on this script runner can be zip_safe.
  main_filename = module.__file__
  assert os.path.exists(main_filename), ('Cannot exec() %r: file not found.' %
                                         main_filename)
  assert os.access(main_filename, os.R_OK), ('Cannot exec() %r: file not'
                                             ' readable.' % main_filename)

  args = [main_filename] + args

  if debug_binary:
    debugger_args = debugger.split()
    program = debugger_args[0]
    # If pathname is not absolute, determine full path using PATH
    if not os.path.isabs(program):
      program = FindEnv(program)
    python_path = sys.executable
    command_vec = [python_path]
    if debug_script:
      command_vec.extend(GetPdbArgs(python_path))
    args = [program] + debugger_args[1:] + command_vec + args

  elif debug_script:
    args = [sys.executable] + GetPdbArgs(program) + args

  else:
    program = sys.executable
    args = [sys.executable] + args

  if show_command_and_exit:
    print('program: "%s"' % program)
    print('args:', args)
    sys.exit(0)

  try:
    sys.stdout.flush()
    os.execv(program, args)
  except EnvironmentError as e:
    if not getattr(e, 'filename', None):
      e.filename = program  # Add info to error message
    raise
