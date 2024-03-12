# -*- coding: utf-8 -*-
# Copyright 2014 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Contains classes related to argparse-based argument parsing."""
from __future__ import absolute_import
from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals

from .tab_complete import CompleterType


class CommandArgument(object):
  """Argparse style argument."""

  def __init__(self, *args, **kwargs):
    """Constructs an argparse argument with the given data.

    See add_argument in argparse for description of the options.
    The only deviation from the argparse arguments is the 'completer' parameter.
    If 'completer' is present, it's used as the argcomplete completer for the
    argument.

    Args:
      *args: Position args to pass to argparse add_argument
      **kwargs: Named args to pass to argparse add_argument
    """
    completer = None
    if 'completer' in kwargs:
      completer = kwargs['completer']
      del kwargs['completer']
    self.args = args
    self.kwargs = kwargs
    self.completer = completer

  @staticmethod
  def MakeZeroOrMoreCloudURLsArgument():
    """Constructs an argument that takes 0 or more Cloud URLs as parameters."""
    return CommandArgument('file',
                           nargs='*',
                           completer=CompleterType.CLOUD_OBJECT)

  @staticmethod
  def MakeZeroOrMoreCloudBucketURLsArgument():
    """Constructs an argument that takes 0+ Cloud bucket URLs as parameters."""
    return CommandArgument('file',
                           nargs='*',
                           completer=CompleterType.CLOUD_BUCKET)

  @staticmethod
  def MakeNCloudBucketURLsArgument(n):
    """Constructs an argument that takes N Cloud bucket URLs as parameters."""
    return CommandArgument('file',
                           nargs=n,
                           completer=CompleterType.CLOUD_BUCKET)

  @staticmethod
  def MakeNCloudURLsArgument(n):
    """Constructs an argument that takes N Cloud URLs as parameters."""
    return CommandArgument('file',
                           nargs=n,
                           completer=CompleterType.CLOUD_OBJECT)

  @staticmethod
  def MakeZeroOrMoreCloudOrFileURLsArgument():
    """Constructs an argument that takes 0 or more Cloud or File URLs."""
    return CommandArgument('file',
                           nargs='*',
                           completer=CompleterType.CLOUD_OR_LOCAL_OBJECT)

  @staticmethod
  def MakeNCloudOrFileURLsArgument(n):
    """Constructs an argument that takes N Cloud or File URLs as parameters."""
    return CommandArgument('file',
                           nargs=n,
                           completer=CompleterType.CLOUD_OR_LOCAL_OBJECT)

  @staticmethod
  def MakeZeroOrMoreFileURLsArgument():
    """Constructs an argument that takes 0 or more File URLs as parameters."""
    return CommandArgument('file',
                           nargs='*',
                           completer=CompleterType.LOCAL_OBJECT)

  @staticmethod
  def MakeNFileURLsArgument(n):
    """Constructs an argument that takes N File URLs as parameters."""
    return CommandArgument('file',
                           nargs=n,
                           completer=CompleterType.LOCAL_OBJECT)

  @staticmethod
  def MakeFileURLOrCannedACLArgument():
    """Constructs an argument that takes a File URL or a canned ACL."""
    return CommandArgument('file',
                           nargs=1,
                           completer=CompleterType.LOCAL_OBJECT_OR_CANNED_ACL)

  @staticmethod
  def MakeFreeTextArgument():
    """Constructs an argument that takes arbitrary text."""
    return CommandArgument('text', completer=CompleterType.NO_OP)

  @staticmethod
  def MakeOneOrMoreBindingsArgument():
    """Constructs an argument that takes multiple bindings."""
    return CommandArgument('binding', nargs='+', completer=CompleterType.NO_OP)
