#!/usr/bin/env python
#
# Copyright 2003 Google Inc. All Rights Reserved.

"""Utility functions for dealing with command interpreters."""



import os

# Running windows?
win32 = (os.name == 'nt')


def ShellEscapeList(words):
  """Turn a list of words into a shell-safe string.

  Args:
    words: A list of words, e.g. for a command.

  Returns:
    A string of shell-quoted and space-separated words.
  """

  if win32:
    return ' '.join(words)

  s = ''
  for word in words:
    # Single quote word, and replace each ' in word with '"'"'
    s += "'" + word.replace("'", "'\"'\"'") + "' "

  return s[:-1]


def ShellifyStatus(status):
  """Translate from a wait() exit status to a command shell exit status."""

  if not win32:
    if os.WIFEXITED(status):
      # decode and return exit status
      status = os.WEXITSTATUS(status)
    else:
      # On Unix, the wait() produces a 16 bit return code.  Unix shells
      # lossily compress this to an 8 bit value, using the formula below.
      # Shell status code < 128 means the process exited normally, status
      # code >= 128 means the process died because of a signal.
      status = 128 + os.WTERMSIG(status)
  return status
