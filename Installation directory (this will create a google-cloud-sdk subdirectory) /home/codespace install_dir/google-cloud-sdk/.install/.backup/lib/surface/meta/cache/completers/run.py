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

"""The meta cache completers run command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import sys

from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import parser_extensions
from googlecloudsdk.command_lib.meta import cache_util
from googlecloudsdk.command_lib.util import parameter_info_lib
from googlecloudsdk.command_lib.util.concepts import concept_parsers
from googlecloudsdk.command_lib.util.concepts import presentation_specs
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core import module_util
from googlecloudsdk.core.console import console_io

import six


class _FunctionCompleter(object):
  """Convert an argparse function completer to a resource_cache completer."""

  def __init__(self, completer):
    self._completer = completer
    self.parameters = None

  def ParameterInfo(self, parsed_args, argument):
    del argument
    return parsed_args

  def Complete(self, prefix, parameter_info):
    return self._completer(prefix, parsed_args=parameter_info)


def _GetPresentationSpec(resource_spec_path, **kwargs):
  """Build a presentation spec."""
  resource_spec = module_util.ImportModule(resource_spec_path)
  if callable(resource_spec):
    resource_spec = resource_spec()
  flag_name_overrides = kwargs.pop('flag_name_overrides', '')
  flag_name_overrides = {
      o.split(':')[0]: o.split(':')[1] if ':' in o else ''
      for o in flag_name_overrides.split(';')
      if o}
  prefixes = kwargs.pop('prefixes', False)
  return presentation_specs.ResourcePresentationSpec(
      kwargs.pop('name', resource_spec.name),
      resource_spec,
      'help text',
      flag_name_overrides=flag_name_overrides,
      prefixes=prefixes,
      **kwargs)


def _GetCompleter(module_path, cache=None, qualify=None,
                  resource_spec=None, presentation_kwargs=None, attribute=None,
                  **kwargs):
  """Returns an instantiated completer for module_path."""
  presentation_kwargs = presentation_kwargs or {}
  if resource_spec:
    presentation_spec = _GetPresentationSpec(resource_spec,
                                             **presentation_kwargs)
    completer = module_util.ImportModule(module_path)(
        presentation_spec.concept_spec,
        attribute)

  else:
    completer = module_util.ImportModule(module_path)
    if not isinstance(completer, type):
      return _FunctionCompleter(completer)
  try:
    return completer(
        cache=cache,
        qualified_parameter_names=qualify,
        **kwargs)
  except TypeError:
    return _FunctionCompleter(completer())


class AddCompleterResourceFlags(parser_extensions.DynamicPositionalAction):
  """Adds resource argument flags based on the completer."""

  def __init__(self, *args, **kwargs):
    super(AddCompleterResourceFlags, self).__init__(*args, **kwargs)
    self.__argument = None
    self.__completer = None

  def GenerateArgs(self, namespace, module_path):
    args = []
    presentation_kwargs = namespace.resource_presentation_kwargs or {}
    # Add the args that correspond to the resource arg, but make them
    # non-required.
    if namespace.resource_spec_path:
      spec = _GetPresentationSpec(namespace.resource_spec_path,
                                  **presentation_kwargs)
      info = concept_parsers.ConceptParser([spec]).GetInfo(spec.name)
      for arg in info.GetAttributeArgs():
        if arg.name.startswith('--'):
          arg.kwargs['required'] = False
        else:
          arg.kwargs['nargs'] = '?' if not spec.plural else '*'
        args.append(arg)
    kwargs = namespace.kwargs or {}
    self.__completer = _GetCompleter(
        module_path, qualify=namespace.qualify,
        resource_spec=namespace.resource_spec_path,
        presentation_kwargs=presentation_kwargs,
        attribute=namespace.attribute,
        **kwargs)
    if self.__completer.parameters:
      for parameter in self.__completer.parameters:
        dest = parameter_info_lib.GetDestFromParam(parameter.name)
        if hasattr(namespace, dest):
          # Don't add if its already been added.
          continue
        flag = parameter_info_lib.GetFlagFromDest(dest)
        arg = base.Argument(
            flag,
            dest=dest,
            category='RESOURCE COMPLETER',
            help='{} `{}` parameter value.'.format(
                self.__completer.__class__.__name__, parameter.name))
        args.append(arg)
    self.__argument = base.Argument(
        'resource_to_complete',
        nargs='?',
        help=('The partial resource name to complete. Omit to enter an '
              'interactive loop that reads a partial resource name from the '
              'input and lists the possible prefix matches on the output '
              'or displays an ERROR message.'))
    args.append(self.__argument)
    return args

  def Completions(self, prefix, parsed_args, **kwargs):
    parameter_info = self.__completer.ParameterInfo(
        parsed_args, self.__argument)
    return self.__completer.Complete(prefix, parameter_info)


class Run(base.Command):
  """Cloud SDK completer module tester.

  *{command}* is an ideal way to debug completer modules without interference
  from the shell.  Shells typically ignore completer errors by disabling all
  standard output, standard error and exception messaging.  Specify
  `--verbosity=INFO` to enable completion and resource cache tracing.
  """

  @staticmethod
  def Args(parser):
    # Add a concept handler that will be stuffed dynamically with information.
    concept_parsers.ConceptParser([]).AddToParser(parser)
    parser.add_argument(
        '--resource-spec-path',
        help=('The resource spec path for a resource argument auto-generated '
              'completer.'))
    parser.add_argument(
        '--attribute',
        help=('The name of the resource attribute for a resource argument '
              'auto-generated completer.'))
    parser.add_argument(
        '--resource-presentation-kwargs',
        type=arg_parsers.ArgDict(
            spec={
                'name': str,
                'flag_name_overrides': str,
                'plural': bool,
                'prefixes': bool,
                'required': bool}),
        help=('Dict of kwargs to be passed to the presentation spec for the '
              'resource argument for which a completer is being tested, such '
              'as name, prefixes, plural, flag name overrides (format as a '
              'list of semicolon-separated key:value pairs). Prefixes is False '
              'by default. Name is the resource spec name by default.'))
    cache_util.AddCacheFlag(parser)
    parser.add_argument(
        '--qualify',
        metavar='NAME',
        type=arg_parsers.ArgList(),
        help=('A list of resource parameter names that must always be '
              'qualified. This is a manual setting for testing. The CLI sets '
              'this automatically.'))
    parser.add_argument(
        '--kwargs',
        metavar='NAME=VALUE',
        type=arg_parsers.ArgDict(),
        help=('Keyword arg dict passed to the completer constructor. For '
              'example, use this to set the resource collection and '
              'list command for `DeprecatedListCommandCompleter`:\n\n'
              '  --kwargs=collection=...,foo="..."'))
    parser.add_argument(
        '--stack-trace',
        action='store_true',
        default=True,
        help=('Enable all exception stack traces, including Cloud SDK core '
              'exceptions.'))
    parser.AddDynamicPositional(
        'module_path',
        action=AddCompleterResourceFlags,
        help=('The completer module path. Run $ gcloud meta completers list` '
              'to list the module paths of the available completers. A '
              'completer module may declare additional flags. Specify `--help` '
              'after _MODULE_PATH_ for details on the module specific flags.'
              '\n\nNOTE: To test resource argument completers, use the '
              'module path "googlecloudsdk.command_lib.util.completers:'
              'CompleterForAttribute". The flags `--resource-spec-path`, '
              '`--attribute`, and (if desired) `--resource-presentation-'
              'kwargs` must be provided BEFORE the positional. Unlike with '
              'most gcloud commands, the arguments are generated on the fly '
              'using the completer you provide, so all the information to '
              'create a resource completer needs to be provided up-front. For '
              'example:\n\n  $ {command} --resource-spec-path MODULE_PATH:'
              'SPEC_OBJECT --attribute ATTRIBUTE_NAME --resource-presentation-'
              'kwargs flag_name_overrides=ATTRIBUTE1:FLAG1;ATTRIBUTE2:FLAG2 '
              'googlecloudsdk.command_lib.util.completers:CompleterForAttribute'
             ))

  def Run(self, args):
    """Returns the results for one completion."""
    presentation_kwargs = args.resource_presentation_kwargs or {}
    with cache_util.GetCache(args.cache, create=True) as cache:
      log.info('cache name {}'.format(cache.name))
      if not args.kwargs:
        args.kwargs = {}
      # Create the ResourceInfo object that is used to hook up the parameter
      # info to the argparse namespace for resource argument completers.
      if args.resource_spec_path:
        spec = _GetPresentationSpec(
            args.resource_spec_path,
            **presentation_kwargs)
        spec.required = False
        resource_info = concept_parsers.ConceptParser([spec]).GetInfo(spec.name)
        # Since the argument being completed doesn't have the correct
        # dest, make sure the handler always gives the same ResourceInfo
        # object.
        def ResourceInfoMonkeyPatch(*args, **kwargs):
          del args, kwargs
          return resource_info
        args.CONCEPTS.ArgNameToConceptInfo = ResourceInfoMonkeyPatch

      completer = _GetCompleter(
          args.module_path, cache=cache, qualify=args.qualify,
          resource_spec=args.resource_spec_path,
          presentation_kwargs=presentation_kwargs,
          attribute=args.attribute,
          **args.kwargs)
      parameter_info = completer.ParameterInfo(
          args, args.GetPositionalArgument('resource_to_complete'))
      if args.resource_to_complete is not None:
        matches = completer.Complete(args.resource_to_complete, parameter_info)
        return [matches]
      while True:
        name = console_io.PromptResponse('COMPLETE> ')
        if name is None:
          break
        try:
          completions = completer.Complete(name, parameter_info)
        except (Exception, SystemExit) as e:  # pylint: disable=broad-except
          if args.stack_trace:
            exceptions.reraise(Exception(e))
          else:
            log.error(six.text_type(e))
          continue
        if completions:
          print('\n'.join(completions))
      sys.stderr.write('\n')
      return None
