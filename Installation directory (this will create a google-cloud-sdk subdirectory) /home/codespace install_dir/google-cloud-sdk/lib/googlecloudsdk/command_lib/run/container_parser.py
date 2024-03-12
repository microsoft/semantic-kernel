# -*- coding: utf-8 -*- #
# Copyright 2023 Google LLC. All Rights Reserved.
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
"""Provides a parser for --container arguments."""

from __future__ import annotations

import collections
from collections.abc import Sequence
from typing import Any

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.calliope import cli
from googlecloudsdk.calliope import parser_arguments
from googlecloudsdk.calliope import parser_errors
from googlecloudsdk.calliope import parser_extensions
from googlecloudsdk.command_lib.run import flags


def AddContainerFlags(
    parser: parser_arguments.ArgumentInterceptor,
    container_arg_group: calliope_base.ArgumentGroup,
):
  """AddContainerFlags updates parser to add --container arg parsing.

  Args:
    parser: The parser to patch.
    container_arg_group: Arguments that can be specified per-container.
  """
  flags.ContainerFlag().AddToParser(parser)
  container_arg_group.AddToParser(parser)
  container_parser = ContainerParser(parser.parser, container_arg_group)
  parser.parser.parse_known_args = container_parser.ParseKnownArgs


class ContainerParser(object):
  """ContainerParser adds custom container parsing behavior to ArgumentParser."""

  _CONTAINER_FLAG_NAME = '--container'

  def __init__(
      self,
      parser: parser_extensions.ArgumentParser,
      container_arg_group: calliope_base.ArgumentGroup,
  ):
    """ContainerParser constructor.

    Args:
      parser: The original command's parser. Used to parse non-container args.
      container_arg_group: Arguments to add to per-container parsers.
    """
    self._parse_known_args = parser.parse_known_args
    self._prog = parser.prog
    self._calliope_command = parser._calliope_command
    self._container_arg_group = container_arg_group

  def _GetContainerFlags(self) -> frozenset[str]:
    """_GetContainerFlags returns the configured set of per-container flags."""
    args = [self._container_arg_group]
    flag_names = []
    while args:
      arg = args.pop()
      if isinstance(arg, calliope_base.ArgumentGroup):
        args.extend(arg.arguments)
      else:
        flag_names.append(arg.name)
    return frozenset(flag_names)

  def _NewContainerParser(self) -> parser_extensions.ArgumentParser:
    """_NewContainerParser creates a new parser for parsing container args."""
    parser = parser_extensions.ArgumentParser(
        add_help=False,
        prog=self._prog,
        calliope_command=self._calliope_command,
    )

    ai = parser_arguments.ArgumentInterceptor(
        parser=parser,
        is_global=False,
        cli_generator=None,
        allow_positional=True,
    )

    self._container_arg_group.AddToParser(ai)
    cli.FLAG_INTERNAL_FLAG_FILE_LINE.AddToParser(ai)
    return parser

  def _CheckForContainerFlags(self, namespace: parser_extensions.Namespace):
    """_CheckForContainerFlags checks that no container flags were specified.

    Args:
      namespace: The namespace to check.
    """
    container_flags = self._GetContainerFlags().intersection(
        namespace.GetSpecifiedArgNames()
    )
    if container_flags:
      raise parser_errors.ArgumentError(
          'When --container is specified {flags} must be specified after'
          ' --container.',
          flags=', '.join(container_flags),
      )

  def ParseKnownArgs(
      self,
      args: Sequence[Any],
      namespace: parser_extensions.Namespace,
  ) -> tuple[parser_extensions.Namespace, Sequence[Any]]:
    """Performs custom --container arg parsing.

    Groups arguments after each --container flag to be parsed into that
    container's namespace. For each container a new parser is used to parse that
    container's flags into fresh namespace and those namespaces are stored as a
    dict in namespace.containers. Remaining args are parsed by the orignal
    parser's parse_known_args method.

    Args:
      args: The arguments to parse.
      namespace: The namespace to store parsed args in.

    Returns:
      A tuple containing the updated namespace and a list of unknown args.
    """
    remaining = []
    containers = collections.defaultdict(list)
    current = remaining
    i = 0
    while i < len(args):
      value = args[i]
      i += 1
      if value == self._CONTAINER_FLAG_NAME:
        if i >= len(args):
          remaining.append(value)
        else:
          current = containers[args[i]]
          i += 1
      elif isinstance(value, str) and value.startswith(
          self._CONTAINER_FLAG_NAME + '='
      ):
        current = containers[value.split(sep='=', maxsplit=1)[1]]
      elif value == '--':
        remaining.append(value)
        remaining.extend(args[i:])
        break
      else:
        current.append(value)

    if not containers:
      return self._parse_known_args(args=remaining, namespace=namespace)

    namespace.containers = {}
    # pylint: disable=protected-access
    namespace._specified_args['containers'] = self._CONTAINER_FLAG_NAME
    for container_name, container_args in containers.items():
      container_namespace = parser_extensions.Namespace()
      container_namespace = self._NewContainerParser().parse_args(
          args=container_args, namespace=container_namespace
      )
      namespace.containers[container_name] = container_namespace

    namespace, unknown_args = self._parse_known_args(
        args=remaining, namespace=namespace
    )
    self._CheckForContainerFlags(namespace)
    return namespace, unknown_args
