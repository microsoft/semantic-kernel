# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""Hooks for Certificate Manager declarative commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.core.util import times

DNS_AUTHORIZATIONS_TEMPLATE = "{}/dnsAuthorizations/{}"
ISSUANCE_CONFIG_TEMPLATE = "{}/certificateIssuanceConfigs/{}"
CA_POOL_TEMPLATE = "{}/caPools/{}"


def GetLocation():
  return "global"


def SetAuthorizationURL(ref, args, request):
  """Converts the dns-authorization argument into a relative URL with project name and location.

  Args:
    ref: Reference to the membership object.
    args: Command line arguments.
    request: API request to be issued

  Returns:
    Modified request
  """

  del ref
  if not args:
    return request

  if args.dns_authorizations:
    authorizations = []

    for field in args.dns_authorizations:
      if not field.startswith("projects/"):
        authorizations.append(
            DNS_AUTHORIZATIONS_TEMPLATE.format(request.parent, field))
      else:
        authorizations.append(field)

    request.certificate.managed.dnsAuthorizations = authorizations

  return request


def SetIssuanceConfigURL(ref, args, request):
  """Converts the issuance-config argument into a relative URL with project name and location.

  Args:
    ref: Reference to the membership object.
    args: Command line arguments.
    request: API request to be issued.

  Returns:
    Modified request
  """

  del ref
  if not args:
    return request

  # TODO(b/228342902): Remove once enabled in GA.
  if hasattr(args, "issuance_config"
            ) and args.issuance_config and not args.issuance_config.startswith(
                "projects/"):
    request.certificate.managed.issuanceConfig = ISSUANCE_CONFIG_TEMPLATE.format(
        request.parent, args.issuance_config)

  return request


def SetCAPoolURL(ref, args, request):
  """Converts the ca-pool argument into a relative URL with project name and location.

  Args:
    ref: reference to the membership object.
    args: command line arguments.
    request: API request to be issued

  Returns:
    modified request
  """

  del ref
  if not args:
    return request

  if args.ca_pool:
    if not args.ca_pool.startswith("projects/"):
      request.certificateIssuanceConfig.certificateAuthorityConfig.certificateAuthorityServiceConfig.caPool = CA_POOL_TEMPLATE.format(
          request.parent, args.ca_pool)

  return request


def ParseIso8601LifetimeFlag(value):
  """Parses the ISO 8601 lifetime argument.

  Args:
    value: An ISO 8601 valid value.

  Returns:
    modified value as expected by the API
  """

  return times.FormatDurationForJson(times.ParseDuration(value))

