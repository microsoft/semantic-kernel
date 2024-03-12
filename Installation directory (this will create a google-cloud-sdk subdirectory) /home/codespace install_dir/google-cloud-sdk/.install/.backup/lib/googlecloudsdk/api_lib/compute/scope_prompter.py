# -*- coding: utf-8 -*- #
# Copyright 2014 Google LLC. All Rights Reserved.
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
"""Facilities for user prompting for request context."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import abc
from googlecloudsdk.api_lib.compute import exceptions
from googlecloudsdk.api_lib.compute import lister
from googlecloudsdk.api_lib.compute import utils
from googlecloudsdk.command_lib.compute import exceptions as compute_exceptions
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources
from googlecloudsdk.core.console import console_io
from googlecloudsdk.core.credentials import gce as c_gce

import six
from six.moves import zip  # pylint: disable=redefined-builtin


def _GetGCERegion():
  if properties.VALUES.core.check_gce_metadata.GetBool():
    return c_gce.Metadata().Region()
  return None


def _GetGCEZone():
  if properties.VALUES.core.check_gce_metadata.GetBool():
    return c_gce.Metadata().Zone()
  return None


GCE_SUGGESTION_SOURCES = {
    'zone': _GetGCEZone,
    'region': _GetGCERegion
}


class Error(exceptions.Error):
  """Exceptions for the scope prompter."""
  pass


class _InvalidPromptInvocation(Error):
  """Exception for invoking prompt with invalid parameters."""
  pass


class ScopePrompter(six.with_metaclass(abc.ABCMeta, object)):
  """A mixin class prompting in the case of ambiguous resource context."""

  @abc.abstractproperty
  def resource_type(self):
    """Specifies the name of the collection that should be printed."""
    pass

  @abc.abstractproperty
  def http(self):
    """Specifies the http client to be used for requests."""
    pass

  @abc.abstractproperty
  def project(self):
    """Specifies the user's project."""
    pass

  @abc.abstractproperty
  def batch_url(self):
    """Specifies the API batch URL."""
    pass

  @abc.abstractproperty
  def compute(self):
    """Specifies the compute client."""
    pass

  @abc.abstractproperty
  def resources(self):
    """Specifies the resources parser for compute resources."""
    pass

  def FetchChoiceResources(self, attribute, service, flag_names,
                           prefix_filter=None):
    """Returns a list of choices used to prompt with."""
    if prefix_filter:
      filter_expr = 'name eq {0}.*'.format(prefix_filter)
    else:
      filter_expr = None

    errors = []
    global_resources = lister.GetGlobalResources(
        service=service,
        project=self.project,
        filter_expr=filter_expr,
        http=self.http,
        batch_url=self.batch_url,
        errors=errors)

    choices = [resource for resource in global_resources]
    if errors or not choices:
      punctuation = ':' if errors else '.'
      utils.RaiseToolException(
          errors,
          'Unable to fetch a list of {0}s. Specifying [{1}] may fix this '
          'issue{2}'.format(attribute, ', or '.join(flag_names), punctuation))

    return choices

  def _PromptForScope(self, ambiguous_names,
                      attributes, services, resource_type,
                      flag_names, prefix_filter):
    """Prompts user to specify a scope for ambiguous resources.

    Args:
      ambiguous_names: list(tuple(name, params, collection)),
        list of parameters which can be fed into resources.Parse.
      attributes: list(str), list of scopes to prompt over.
      services: list(apitool.base.py.base_api.BaseApiService), service for each
        attribute/scope.
      resource_type: str, collection name without api name.
      flag_names: list(str), flag names which can be used to specify scopes.
      prefix_filter: str, used to filter retrieved resources on backend.
    Returns:
      List of fully resolved names for provided ambiguous_names parameter.
    Raises:
      _InvalidPromptInvocation: if number of attributes does not match number of
        services.
    """

    def RaiseOnPromptFailure():
      """Call this to raise an exn when prompt cannot read from input stream."""
      phrases = ('one of ', 'flags') if len(flag_names) > 1 else ('', 'flag')
      raise compute_exceptions.FailedPromptError(
          'Unable to prompt. Specify {0}the [{1}] {2}.'.format(
              phrases[0], ', '.join(flag_names), phrases[1]))

    # one service per attribute
    if len(attributes) != len(services):
      raise _InvalidPromptInvocation()

    # Update selected_resource_name in response to user prompts
    selected_resource_name = None
    selected_attribute = None

    # Try first to give a precise suggestion based on current VM zone/region.
    if len(attributes) == 1:
      gce_suggestor = (
          GCE_SUGGESTION_SOURCES.get(attributes[0]) or (lambda: None))
      gce_suggested_resource = gce_suggestor()
      if gce_suggested_resource:
        selected_attribute = attributes[0]
        selected_resource_name = self._PromptDidYouMeanScope(
            ambiguous_names, attributes[0], resource_type,
            gce_suggested_resource, RaiseOnPromptFailure)

    # If the user said "no" fall back to a generic prompt.
    if selected_resource_name is None:
      choice_resources = {}
      for service, attribute in zip(services, attributes):
        choice_resources[attribute] = (
            self.FetchChoiceResources(
                attribute, service, flag_names, prefix_filter))
      selected_attribute, selected_resource_name = self._PromptForScopeList(
          ambiguous_names, attributes, resource_type, choice_resources,
          RaiseOnPromptFailure)

    # _PromptForScopeList ensures this.
    assert selected_resource_name is not None
    assert selected_attribute is not None
    result = []

    for ambigous_name, params, collection in ambiguous_names:
      new_params = params.copy()
      if selected_attribute in new_params:
        new_params[selected_attribute] = selected_resource_name
      try:
        resource_ref = self.resources.Parse(
            ambigous_name, params=new_params, collection=collection)
      except (resources.RequiredFieldOmittedException,
              properties.RequiredPropertyError):
        pass
      else:
        if hasattr(resource_ref, selected_attribute):
          result.append(resource_ref)

    return result

  def _PromptDidYouMeanScope(self, ambiguous_refs, attribute, resource_type,
                             suggested_resource, raise_on_prompt_failure):
    """Prompts "did you mean <scope>".  Returns str or None, or raises."""

    # targetInstances -> target instances
    resource_name = utils.CamelCaseToOutputFriendly(resource_type)
    names = [name for name, _, _ in ambiguous_refs]
    message = 'Did you mean {0} [{1}] for {2}: [{3}]?'.format(
        attribute, suggested_resource, resource_name, ', '.join(names))

    try:
      if console_io.PromptContinue(message=message, default=True,
                                   throw_if_unattended=True):
        return suggested_resource
      else:
        return None
    except console_io.UnattendedPromptError:
      raise_on_prompt_failure()

  def _PromptForScopeList(self, ambiguous_refs, attributes,
                          resource_type, choice_resources,
                          raise_on_prompt_failure):
    """Prompt to resolve abiguous resources.  Either returns str or throws."""
    # targetInstances -> target instances
    resource_name = utils.CamelCaseToOutputFriendly(resource_type)
    # Resource names should be surrounded by brackets while choices should not
    names = ['[{0}]'.format(name) for name, _, _ in ambiguous_refs]
    # Print deprecation state for choices.
    choice_names = []
    choice_mapping = []
    for attribute in attributes:
      for choice_resource in choice_resources[attribute]:
        deprecated = choice_resource.deprecated
        if deprecated:
          choice_name = '{0} ({1})'.format(
              choice_resource.name, deprecated.state)
        else:
          choice_name = choice_resource.name

        if len(attributes) > 1:
          choice_name = '{0}: {1}'.format(attribute, choice_name)

        choice_mapping.append((attribute, choice_resource.name))
        choice_names.append(choice_name)

    title = utils.ConstructList(
        'For the following {0}:'.format(resource_name), names)
    idx = console_io.PromptChoice(
        options=choice_names,
        message='{0}choose a {1}:'.format(title, ' or '.join(attributes)))
    if idx is None:
      raise_on_prompt_failure()
    else:
      return choice_mapping[idx]

  def PromptForMultiScopedReferences(
      self, resource_names, scope_names, scope_services, resource_types,
      flag_names):
    """Prompt for resources, which can be placed in several different scopes."""

    # one service and resource type per scope
    if len(scope_names) != len(scope_services) or (
        len(scope_names) != len(resource_types)):
      raise _InvalidPromptInvocation()

    resource_refs = []
    ambiguous_names = []
    for resource_name in resource_names:
      for resource_type in resource_types:
        collection = utils.GetApiCollection(resource_type)
        params = {
            'project': properties.VALUES.core.project.GetOrFail,
        }
        collection_info = self.resources.GetCollectionInfo(collection)
        if 'zone' in collection_info.params:
          params['zone'] = properties.VALUES.compute.zone.GetOrFail
        elif 'region' in collection_info.params:
          params['region'] = properties.VALUES.compute.region.GetOrFail
        try:
          resource_ref = self.resources.Parse(
              resource_name, params=params, collection=collection)
        except resources.WrongResourceCollectionException:
          pass
        except (resources.RequiredFieldOmittedException,
                properties.RequiredPropertyError):
          ambiguous_names.append((resource_name, params, collection))
        else:
          resource_refs.append(resource_ref)

    if ambiguous_names:
      resource_refs += self._PromptForScope(
          ambiguous_names=ambiguous_names,
          attributes=scope_names,
          services=scope_services,
          resource_type=resource_types[0],
          flag_names=flag_names,
          prefix_filter=None)

    return resource_refs

  def CreateScopedReferences(self, resource_names, scope_name, scope_arg,
                             scope_service, resource_type, flag_names,
                             prefix_filter=None):
    """Returns a list of resolved resource references for scoped resources."""
    resource_refs = []
    ambiguous_names = []
    resource_type = resource_type or self.resource_type
    collection = utils.GetApiCollection(resource_type)
    for resource_name in resource_names:
      params = {
          'project': properties.VALUES.core.project.GetOrFail,
          scope_name: (scope_arg or
                       getattr(properties.VALUES.compute, scope_name).GetOrFail)
      }
      try:
        resource_ref = self.resources.Parse(
            resource_name,
            collection=collection,
            params=params)
      except (resources.RequiredFieldOmittedException,
              properties.RequiredPropertyError):
        ambiguous_names.append((resource_name, params, collection))
      else:
        resource_refs.append(resource_ref)

    if ambiguous_names and not scope_arg:
      # We need to prompt.
      resource_refs += self._PromptForScope(
          ambiguous_names=ambiguous_names,
          attributes=[scope_name],
          services=[scope_service],
          resource_type=resource_type,
          flag_names=flag_names,
          prefix_filter=prefix_filter)

    return resource_refs

  def CreateZonalReferences(self, resource_names, zone_arg, resource_type=None,
                            flag_names=None, region_filter=None):
    """Returns a list of resolved zonal resource references."""
    if flag_names is None:
      flag_names = ['--zone']

    if zone_arg:
      zone_ref = self.resources.Parse(
          zone_arg,
          params={
              'project': properties.VALUES.core.project.GetOrFail,
          },
          collection='compute.zones')
      zone_name = zone_ref.Name()
    else:
      zone_name = None

    return self.CreateScopedReferences(
        resource_names,
        scope_name='zone',
        scope_arg=zone_name,
        scope_service=self.compute.zones,
        resource_type=resource_type,
        flag_names=flag_names,
        prefix_filter=region_filter)

  def CreateZonalReference(self, resource_name, zone_arg, resource_type=None,
                           flag_names=None, region_filter=None):
    return self.CreateZonalReferences(
        [resource_name], zone_arg, resource_type, flag_names, region_filter)[0]

  def CreateRegionalReferences(self, resource_names, region_arg,
                               flag_names=None, resource_type=None):
    """Returns a list of resolved regional resource references."""
    if flag_names is None:
      flag_names = ['--region']

    if region_arg:
      region_ref = self.resources.Parse(
          region_arg,
          params={
              'project': properties.VALUES.core.project.GetOrFail,
          },
          collection='compute.regions')
      region_name = region_ref.Name()
    else:
      region_name = None

    return self.CreateScopedReferences(
        resource_names,
        scope_name='region',
        scope_arg=region_name,
        scope_service=self.compute.regions,
        flag_names=flag_names,
        resource_type=resource_type)

  def CreateRegionalReference(self, resource_name, region_arg,
                              flag_names=None, resource_type=None):
    return self.CreateRegionalReferences(
        [resource_name], region_arg, flag_names, resource_type)[0]

  def CreateGlobalReferences(self, resource_names, resource_type=None):
    """Returns a list of resolved global resource references."""
    resource_refs = []
    for resource_name in resource_names:
      resource_refs.append(self.resources.Parse(
          resource_name,
          params={
              'project': properties.VALUES.core.project.GetOrFail,
          },
          collection=utils.GetApiCollection(
              resource_type or self.resource_type)))
    return resource_refs

  def CreateGlobalReference(self, resource_name, resource_type=None):
    return self.CreateGlobalReferences([resource_name], resource_type)[0]
