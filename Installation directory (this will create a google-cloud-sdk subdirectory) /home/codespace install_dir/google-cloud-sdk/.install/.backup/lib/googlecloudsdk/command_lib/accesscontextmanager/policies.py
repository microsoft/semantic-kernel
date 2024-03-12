# -*- coding: utf-8 -*- #
# Copyright 2018 Google LLC. All Rights Reserved.
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
"""Command line processing utilities for access policies."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.accesscontextmanager import policies as policies_api
from googlecloudsdk.api_lib.cloudresourcemanager import organizations
from googlecloudsdk.calliope.concepts import concepts
from googlecloudsdk.calliope.concepts import deps
from googlecloudsdk.command_lib.meta import cache_util as meta_cache_util
from googlecloudsdk.command_lib.util import cache_util
from googlecloudsdk.command_lib.util.concepts import concept_parsers
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources


class DefaultPolicyResolutionError(exceptions.Error):
  pass


def ValidateAccessPolicyArg(ref, args, req=None):
  """Add the particular service filter message based on specified args."""
  del ref  # unused
  if args.IsSpecified('policy'):
    properties.AccessPolicyValidator(args.policy)

  return req


def GetAttributeConfig():
  property_ = properties.VALUES.access_context_manager.policy
  return concepts.ResourceParameterAttributeConfig(
      name='policy',
      help_text='The ID of the access policy.',
      fallthroughs=[deps.PropertyFallthrough(property_)])


def GetResourceSpec():
  return concepts.ResourceSpec(
      'accesscontextmanager.accessPolicies',
      resource_name='policy',
      accessPoliciesId=GetAttributeConfig())


def AddResourceArg(parser, verb):
  """Add a resource argument for an access policy.

  NOTE: Must be used only if it's the only resource arg in the command.

  Args:
    parser: the parser for the command.
    verb: str, the verb to describe the resource, such as 'to update'.
  """
  concept_parsers.ConceptParser.ForResource(
      'policy',
      GetResourceSpec(),
      'The access policy {}.'.format(verb),
      required=True).AddToParser(parser)


@cache_util.CacheResource('organizations-by-domain', 10)
def _GetOrganization(domain):
  """Get the organization for the given domain.

  The current user must have permission to list the organization.

  Args:
    domain: str, the domain (e.g. 'example.com') to look up the organization of,
      or None to just list the organizations for the current account.

  Returns:
    resources.Resource, a reference to a cloudresourcemanager.organizations
      resource

  Raises:
    DefaultPolicyResolutionError: if the number of organizations matching the
      given domain is not exactly 1, or searching organizations fails.
  """
  filter_ = 'domain:' + domain
  try:
    orgs = list(organizations.Client().List(filter_=filter_, limit=2))
  except Exception as err:
    raise DefaultPolicyResolutionError(
        'Unable to resolve organization for domain [{}]: {}'.format(
            domain, err))

  if not orgs:
    raise DefaultPolicyResolutionError(
        'No matching organizations found for domain [{}].'.format(domain))
  elif len(orgs) > 1:
    raise DefaultPolicyResolutionError(
        'Found more than one organization for domain [{}].\n{}'.format(
            domain, orgs))

  return resources.REGISTRY.Parse(
      orgs[0].name, collection='cloudresourcemanager.organizations')


@cache_util.CacheResource('policies-by-organization', 10)
def _GetPolicy(organization_ref):
  """Get the access policy for the given organization.

  The current user must have permission to list the policies for the
  organization.

  Args:
    organization_ref: resources.Resource, a reference to a
      cloudresourcemanager.organizations resource to look up the policy for.

  Returns:
    resources.Resource, a reference to an accesscontextmanager.accessPolicies
      resource

  Raises:
    DefaultPolicyResolutionError: if the number of policies matching the
      given organization is not exactly 1, or listing policies fails.
  """
  try:
    policies = list(policies_api.Client().List(organization_ref, limit=2))
  except Exception as err:
    raise DefaultPolicyResolutionError(
        'Unable to resolve policy for organization [{}]: {}'.format(
            organization_ref.Name(), err))

  if not policies:
    raise DefaultPolicyResolutionError(
        'No matching policies found for organization [{}]'.format(
            organization_ref.Name()))
  elif len(policies) > 1:
    raise DefaultPolicyResolutionError(
        'Found more than one access policy for organization [{}]:\n{}'.format(
            organization_ref.Name(), policies))
  policy_ref = resources.REGISTRY.Parse(
      policies[0].name, collection='accesscontextmanager.accessPolicies')
  return policy_ref


_IAM_SUFFIX = '.iam.gserviceaccount.com'
_DEVELOPER_DOMAIN = 'developer.gserviceaccount.com'


def _GetDomain(account):
  _, _, host = account.partition('@')
  if host.endswith(_IAM_SUFFIX) or host == _DEVELOPER_DOMAIN:
    return None
  return host


def GetDefaultPolicy():
  """Gets the ID of the default policy for the current account."""
  account = properties.VALUES.core.account.Get()
  if not account:
    log.info('Unable to automatically resolve policy since account property '
             'is not set.')
    return None

  domain = _GetDomain(account)
  if not domain:
    log.info('Unable to resolve domain for account [%s]', account)
    return None

  with meta_cache_util.GetCache('resource://', create=True) as cache:
    try:
      # pylint: disable=too-many-function-args
      organization_ref = _GetOrganization(cache, domain)
      policy_ref = _GetPolicy(cache, organization_ref.RelativeName(),
                              (organization_ref,))
    except DefaultPolicyResolutionError as err:
      log.info('Unable to automatically resolve policy: %s', err)
      return None

  return policy_ref.Name()
