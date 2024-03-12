# -*- coding: utf-8 -*- #
# Copyright 2016 Google LLC. All Rights Reserved.
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

"""Console Prompter for compute scopes."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import operator

from googlecloudsdk.command_lib.compute import scope as compute_scope
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core.console import console_io
from googlecloudsdk.core.credentials import gce as c_gce
from googlecloudsdk.core.util import text


def PromptForScope(resource_name, underspecified_names,
                   scopes, default_scope, scope_lister):
  """Prompt user to specify a scope.

  Args:
    resource_name: str, human readable name of the resource.
    underspecified_names: list(str), names which lack scope context.
    scopes: list(compute_scope.ScopeEnum), scopes to query for.
    default_scope: compute_scope.ScopeEnum, force this scope to be used.
    scope_lister: func(scopes, underspecified_names)->[str->[str]], callback to
        provide possible values for each scope.
  Returns:
    tuple of chosen scope_enum and scope value.
  """
  implicit_scope = default_scope
  if len(scopes) == 1:
    implicit_scope = scopes[0]

  if implicit_scope:
    suggested_value = _GetSuggestedScopeValue(implicit_scope)
    if suggested_value is not None:
      if _PromptDidYouMeanScope(resource_name, underspecified_names,
                                implicit_scope, suggested_value):
        return implicit_scope, suggested_value

  if not scope_lister:
    return None, None

  scope_value_choices = scope_lister(
      # Sort to make it deterministic.
      sorted(scopes, key=operator.attrgetter('name')),
      underspecified_names)

  choice_names, choice_mapping = _FormatScopeValueChoices(scope_value_choices)

  if len(choice_mapping) == 1:
    suggested_resource_scope_enum = choice_mapping[0][0]
    suggested_resource = choice_mapping[0][1]
    _PromptSuggestedScopeChoice(resource_name, underspecified_names,
                                suggested_resource_scope_enum,
                                suggested_resource)
    return suggested_resource_scope_enum, suggested_resource

  resource_scope_enum, scope_value = _PromptWithScopeChoices(
      resource_name, underspecified_names, scope_value_choices, choice_names,
      choice_mapping)

  return resource_scope_enum, scope_value


def _PromptDidYouMeanScope(resource_name, underspecified_names, scope_enum,
                           suggested_resource):
  """Prompts "did you mean <scope>".  Returns str or None."""
  if scope_enum == compute_scope.ScopeEnum.GLOBAL:
    message = 'Did you mean [{0}] for {1}: [{2}]'.format(
        scope_enum.flag_name, resource_name, ', '.join(underspecified_names))
  else:
    message = 'Did you mean {0} [{1}] for {2}: [{3}]'.format(
        scope_enum.flag_name, suggested_resource,
        resource_name, ', '.join(underspecified_names))
  return console_io.PromptContinue(prompt_string=message, default=True,
                                   throw_if_unattended=True)


def _PromptSuggestedScopeChoice(resource_name, underspecified_names, scope_enum,
                                suggested_resource):
  if scope_enum == compute_scope.ScopeEnum.GLOBAL:
    log.status.Print('No scope specified. Using [{0}] for {1}: [{2}].'.format(
        scope_enum.flag_name,
        text.Pluralize(len(underspecified_names), resource_name),
        ', '.join(underspecified_names)))
  else:
    log.status.Print('No {0} specified. Using {0} [{1}] for {2}: [{3}].'.format(
        scope_enum.flag_name, suggested_resource,
        text.Pluralize(len(underspecified_names), resource_name),
        ', '.join(underspecified_names)))


def _FormatScopeValueChoices(scope_value_choices):
  """Formats scope value choices for prompting and adds deprecation states."""
  choice_names, choice_mapping = [], []
  for scope in sorted(list(scope_value_choices.keys()),
                      key=operator.attrgetter('flag_name')):
    for choice_resource in sorted(scope_value_choices[scope],
                                  key=operator.attrgetter('name')):
      deprecated = getattr(choice_resource, 'deprecated', None)
      if deprecated is not None:
        choice_name = '{0} ({1})'.format(
            choice_resource.name, deprecated.state)
      else:
        choice_name = choice_resource.name

      if len(scope_value_choices) > 1:
        if choice_name:
          choice_name = '{0}: {1}'.format(scope.flag_name, choice_name)
        else:
          choice_name = scope.flag_name

      choice_mapping.append((scope, choice_resource.name))
      choice_names.append(choice_name)

  return choice_names, choice_mapping


def _PromptWithScopeChoices(resource_name, underspecified_names,
                            scope_value_choices, choice_names, choice_mapping):
  """Queries user to choose scope and its value."""
  title = ('For the following {0}:\n {1}\n'
           .format(text.Pluralize(len(underspecified_names), resource_name),
                   '\n '.join('- [{0}]'.format(n)
                              for n in sorted(underspecified_names))))
  flags = ' or '.join(
      sorted([s.prefix + s.flag_name for s in scope_value_choices.keys()]))

  idx = console_io.PromptChoice(
      options=choice_names, message='{0}choose {1}:'.format(title, flags))
  if idx is None:
    return None, None
  else:
    return choice_mapping[idx]


def _GetSuggestedScopeValue(scope):
  if scope == compute_scope.ScopeEnum.ZONE:
    return _GetGCEZone()
  if scope == compute_scope.ScopeEnum.REGION:
    return _GetGCERegion()
  return True


def _GetGCERegion():
  if properties.VALUES.core.check_gce_metadata.GetBool():
    return c_gce.Metadata().Region()
  return None


def _GetGCEZone():
  if properties.VALUES.core.check_gce_metadata.GetBool():
    return c_gce.Metadata().Zone()
  return None
