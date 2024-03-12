#!/usr/bin/env python
# Copyright 2004 Google Inc. All Rights Reserved.
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

"""Import this module to add a hook to call pdb on uncaught exceptions.

To enable this, do the following in your top-level application:

import google.apputils.debug

and then in your main():

google.apputils.debug.Init()

Then run your program with --pdb.
"""



import sys

import gflags as flags

flags.DEFINE_boolean('pdb', 0, 'Drop into pdb on uncaught exceptions')

old_excepthook = None


def _DebugHandler(exc_class, value, tb):
  if not flags.FLAGS.pdb or hasattr(sys, 'ps1') or not sys.stderr.isatty():
    # we aren't in interactive mode or we don't have a tty-like
    # device, so we call the default hook
    old_excepthook(exc_class, value, tb)
  else:
    # Don't impose import overhead on apps that never raise an exception.
    import traceback
    import pdb
    # we are in interactive mode, print the exception...
    traceback.print_exception(exc_class, value, tb)
    print
    # ...then start the debugger in post-mortem mode.
    pdb.pm()


def Init():
  # Must back up old excepthook.
  global old_excepthook  # pylint: disable-msg=W0603
  old_excepthook = sys.excepthook
  sys.excepthook = _DebugHandler
