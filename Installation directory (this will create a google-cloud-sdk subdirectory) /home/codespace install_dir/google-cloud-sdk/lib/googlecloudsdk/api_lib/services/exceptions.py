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
"""Wrapper for user-visible error exceptions to raise in the CLI."""
from googlecloudsdk.api_lib.util import exceptions as api_lib_exceptions
from googlecloudsdk.core import exceptions as core_exceptions


class Error(core_exceptions.Error):
  """Exceptions for Services errors."""


class EnableServicePermissionDeniedException(Error):
  """Permission denied exception for enable service command."""


class ListServicesPermissionDeniedException(Error):
  """Permission denied exception for list services command."""


class GetServicePermissionDeniedException(Error):
  """Permission denied exception for get service command."""


class CreateQuotaOverridePermissionDeniedException(Error):
  """Permission denied exception for create quota override command."""


class UpdateQuotaOverridePermissionDeniedException(Error):
  """Permission denied exception for update quota override command."""


class DeleteQuotaOverridePermissionDeniedException(Error):
  """Permission denied exception for delete quota override command."""


class CreateConnectionsPermissionDeniedException(Error):
  """Permission denied exception for create connection command."""


class DeleteConnectionsPermissionDeniedException(Error):
  """Permission denied exception for create connection command."""


class UpdateConnectionsPermissionDeniedException(Error):
  """Permission denied exception for list connections command."""


class ListConnectionsPermissionDeniedException(Error):
  """Permission denied exception for list connections command."""


class EnableVpcServiceControlsPermissionDeniedException(Error):
  """Permission denied exception for enable vpc service controls command."""


class GetVpcServiceControlsPermissionDeniedException(Error):
  """Permission denied exception for get vpc service controls command."""


class DisableVpcServiceControlsPermissionDeniedException(Error):
  """Permission denied exception for disable vpc service controls command."""


class CreatePeeredDnsDomainPermissionDeniedException(Error):
  """Permission denied exception for create peered dns domain command."""


class DeletePeeredDnsDomainPermissionDeniedException(Error):
  """Permission denied exception for delete peered dns domain command."""


class ListPeeredDnsDomainsPermissionDeniedException(Error):
  """Permission denied exception for list peered dns domains command."""


class GenerateServiceIdentityPermissionDeniedException(Error):
  """Permission denied exception for generate service identitiy command."""


class GetConsumerPolicyPermissionDeniedException(Error):
  """Permission denied exception for get consumer policy."""


class UpdateConsumerPolicyPermissionDeniedException(Error):
  """Permission denied exception for update consumer policy."""


class GetReverseDependencyClosurePermissionDeniedException(Error):
  """Permission denied exception for get reverse dependency closure."""


class ListFlattenedMembersPermissionDeniedException(Error):
  """Permission denied exception for list flattened members."""


class ListGroupMembersPermissionDeniedException(Error):
  """Permission denied exception for list group members."""


class FetchValueInfoPermissionDeniedException(Error):
  """Permission denied exception for fetch value info group members."""


class GetEffectiverPolicyPermissionDeniedException(Error):
  """Permission denied exception for get effective policy."""


class FetchPublicValueInfoPermissionDeniedException(Error):
  """Permission denied exception for fetch public value info group members."""


class TestEnabledPermissionDeniedException(Error):
  """Permission denied exception for test enabled."""


class ListDescendantServicesPermissionDeniedException(Error):
  """Permission denied exception for list descendant services."""


class ListAncestorGroupsPermissionDeniedException(Error):
  """Permission denied exception for list ancestor groups."""


class BatchGetServicePermissionDeniedException(Error):
  """Permission denied exception for batch get service."""

  pass


class ListCategoryServicespermissionDeniedException(Error):
  """Permission denied exception for list category service."""

  pass


class OperationErrorException(Error):
  """Exception for operation error."""


class TimeoutError(Error):
  """Exception for timeout error."""


def ReraiseError(err, klass):
  """Transform and re-raise error helper."""
  core_exceptions.reraise(klass(api_lib_exceptions.HttpException(err)))


class ConfigError(Error):
  """Raised when unable to parse a config file."""

  def __init__(self, message=None, **kwargs):
    message = message or 'Config Error.'
    super(ConfigError, self).__init__(message, **kwargs)
