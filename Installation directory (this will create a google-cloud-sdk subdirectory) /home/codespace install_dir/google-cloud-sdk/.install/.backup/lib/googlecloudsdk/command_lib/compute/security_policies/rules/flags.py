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
"""Flags and helpers for the compute security policies rules commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.command_lib.compute import completers as compute_completers
from googlecloudsdk.command_lib.compute import flags as compute_flags

_WAF_EXCLUSION_REQUEST_FIELD_HELP_TEXT = """
You can specify an exact match or a partial match by using a field operator and
a field value. Available field operators are:
- ``EQUALS'': the operator matches if the field value equals the specified
              value.
- ``STARTS_WITH'': the operator matches if the field value starts with the
                   specified value.
- ``ENDS_WITH'': the operator matches if the field value ends with the specified
                 value.
- ``CONTAINS'': the operator matches if the field value contains the specified
                value.
- ``EQUALS_ANY'': the operator matches if the field value is any value.

A field value must be given if the field operator is not ``EQUALS_ANY'', and
cannot be given if the field operator is ``EQUALS_ANY''. For example,
`--request-header-to-exclude op=EQUALS,val=abc` or
`--request-header-to-exclude op=EQUALS_ANY`.

This flag can be repeated to specify multiple request headers to exclude. For
example,
`--request-header-to-exclude op=EQUALS,val=abc --request-header-to-exclude op=STARTS_WITH,val=xyz`.
"""

_WAF_EXCLUSION_TARGET_RULE_SET_HELP_TEXT_FOR_ADD = """
Target WAF rule set where the request field exclusions being added would apply.

This, together with the target rule IDs (if given), determines the target for
associating request field exclusions. See `--target-rule-ids`.
"""

_WAF_EXCLUSION_TARGET_RULE_SET_HELP_TEXT_FOR_REMOVE = """
Target WAF rule set from where to remove the request field exclusions.

This, together with the target rule IDs (if given), determines the target for
associating request field exclusions. See `--target-rule-ids`.

Note that the removal of request field exclusions is restricted to those
associated with a matching target. Set this flag to * if you want to remove
request field exclusions regardless of the target.
"""

_WAF_EXCLUSION_TARGET_RULE_IDS_HELP_TEXT_FOR_ADD = """
A comma-separated list of target rule IDs under the WAF rule set where the
request field exclusions being added would apply. If omitted, the added request
field exclusions will be associated with the rule set only, which would apply
to all the rule IDs under the rule set.
"""

_WAF_EXCLUSION_TARGET_RULE_IDS_HELP_TEXT_FOR_REMOVE = """
A comma-separated list of target rule IDs under the WAF rule set from where to
remove the request field exclusions. If omitted, the removal of request field
exclusions is restricted to those associated with the rule set only, without
specific rule IDs.
"""

_WAF_EXCLUSION_REQUEST_COOKIE_HELP_TEXT_FOR_ADD = """
Adds a request cookie to the request field exclusions associated with the rule
set and rule IDs (if given). This specifies a request cookie whose value will
be excluded from inspection during preconfigured WAF evaluation.
""" + _WAF_EXCLUSION_REQUEST_FIELD_HELP_TEXT

_WAF_EXCLUSION_REQUEST_COOKIE_HELP_TEXT_FOR_REMOVE = """
Removes a request cookie from the existing request field exclusions associated
with the rule set and rule IDs (if given).
""" + _WAF_EXCLUSION_REQUEST_FIELD_HELP_TEXT

_WAF_EXCLUSION_REQUEST_HEADER_HELP_TEXT_FOR_ADD = """
Adds a request header to the request field exclusions associated with the rule
set and rule IDs (if given). This specifies a request header whose value will be
excluded from inspection during preconfigured WAF evaluation.

Refer to the syntax under `--request-cookie-to-exclude`.

This flag can be repeated to specify multiple request headers.
"""

_WAF_EXCLUSION_REQUEST_HEADER_HELP_TEXT_FOR_REMOVE = """
Removes a request header from the existing request field exclusions associated
with the rule set and rule IDs (if given).

Refer to the syntax under `--request-cookie-to-exclude`.

This flag can be repeated to specify multiple request headers.
"""

_WAF_EXCLUSION_REQUEST_QUERY_PARAM_HELP_TEXT_FOR_ADD = """
Adds a request query parameter to the request field exclusions associated with
the rule set and rule IDs (if given). This specifies a request query parameter
in the query string or in the POST body whose value will be excluded from
inspection during preconfigured WAF evaluation.

Refer to the syntax under `--request-cookie-to-exclude`.

This flag can be repeated to specify multiple request query parameters.
"""

_WAF_EXCLUSION_REQUEST_QUERY_PARAM_HELP_TEXT_FOR_REMOVE = """
Removes a request query parameter from the existing request field exclusions
associated with the rule set and rule IDs (if given).

Refer to the syntax under `--request-cookie-to-exclude`.

This flag can be repeated to specify multiple request query parameters.
"""

_WAF_EXCLUSION_REQUEST_URI_HELP_TEXT_FOR_ADD = """
Adds a request URI to the request field exclusions associated with the rule set
and rule IDs (if given). This specifies a request URI from the request line to
be excluded from inspection during preconfigured WAF evaluation.

Refer to the syntax under `--request-cookie-to-exclude`.

This flag can be repeated to specify multiple request URIs.
"""

_WAF_EXCLUSION_REQUEST_URI_HELP_TEXT_FOR_REMOVE = """
Removes a request URI from the existing request field exclusions associated with
the rule set and rule IDs (if given).

Refer to the syntax under `--request-cookie-to-exclude`.

This flag can be repeated to specify multiple request URIs.
"""

_RATE_LIMIT_ENFORCE_ON_KEY_TYPES_DESCRIPTION = """
      - ``ip'': each client IP address has this limit enforced separately
      - ``all'': a single limit is applied to all requests matching this rule
      - ``http-header'': key type takes the value of the HTTP header configured
                         in enforce-on-key-name as the key value
      - ``xff-ip'': takes the original IP address specified in the X-Forwarded-For
                    header as the key
      - ``http-cookie'': key type takes the value of the HTTP cookie configured
                         in enforce-on-key-name as the key value
      - ``http-path'': key type takes the value of the URL path in the request
      - ``sni'': key type takes the value of the server name indication from the
                  TLS session of the HTTPS request
      - ``region-code'': key type takes the value of the region code from which
                         the request originates
      - ``tls-ja3-fingerprint'': key type takes the value of JA3 TLS/SSL
                                 fingerprint if the client connects using HTTPS,
                                 HTTP/2 or HTTP/3
      - ``user-ip'': key type takes the IP address of the originating client,
                     which is resolved based on user-ip-request-headers
                     configured with the security policy
"""


class SecurityPolicyRulesCompleter(compute_completers.ListCommandCompleter):

  def __init__(self, **kwargs):
    super(SecurityPolicyRulesCompleter, self).__init__(
        collection='compute.securityPolicyRules', **kwargs)


def AddPriority(parser, operation, is_plural=False):
  """Adds the priority argument to the argparse."""
  parser.add_argument(
      'name' + ('s' if is_plural else ''),
      metavar='PRIORITY',
      nargs='*' if is_plural else None,
      completer=SecurityPolicyRulesCompleter,
      help=('The priority of the rule{0} to {1}. Rules are evaluated in order '
            'from highest priority to lowest priority where 0 is the highest '
            'priority and 2147483647 is the lowest priority.'.format(
                's' if is_plural else '', operation)))


def PriorityArgument(operation, is_plural=False):
  return compute_flags.ResourceArgument(
      'name' + ('s' if is_plural else ''),
      completer=SecurityPolicyRulesCompleter,
      global_collection='compute.securityPolicyRules',
      regional_collection='compute.regionSecurityPolicyRules',
      region_hidden=False,
      scope_flags_usage=compute_flags.ScopeFlagsUsage.DONT_USE_SCOPE_FLAGS,
      plural=is_plural,
      required=(False if is_plural else True),
      detailed_help=(
          'The priority of the rule{0} to {1}. Rules are evaluated in order '
          'from highest priority to lowest priority where 0 is the highest '
          'priority and 2147483647 is the lowest priority.'.format(
              's' if is_plural else '', operation)))


def AddRegionFlag(parser, operation):
  """Adds the region argument to the argparse to specify the security policy region."""
  return compute_flags.AddRegionFlag(
      parser,
      'security policy',
      operation,
      explanation=compute_flags.REGION_PROPERTY_EXPLANATION_NO_DEFAULT)


def AddMatcher(parser, required=True):
  """Adds the matcher arguments to the argparse."""
  matcher = parser.add_group(
      mutex=True, required=required, help='Security policy rule matcher.')
  matcher.add_argument(
      '--src-ip-ranges',
      type=arg_parsers.ArgList(),
      metavar='SRC_IP_RANGE',
      help=('The source IPs/IP ranges to match for this rule. '
            'To match all IPs specify *.'))
  matcher.add_argument(
      '--expression',
      help='The Cloud Armor rules language expression to match for this rule.')


def AddMatcherAndNetworkMatcher(parser, required=True):
  """Adds the matcher arguments to the argparse."""
  matcher = parser.add_group(
      required=required, help='Security policy rule matcher.')
  matcher.add_argument(
      '--src-ip-ranges',
      type=arg_parsers.ArgList(),
      metavar='SRC_IP_RANGE',
      help=('The source IPs/IP ranges to match for this rule. '
            'To match all IPs specify *.'))
  matcher.add_argument(
      '--expression',
      help='The Cloud Armor rules language expression to match for this rule.')
  matcher.add_argument(
      '--network-user-defined-fields',
      type=arg_parsers.ArgList(),
      metavar='NAME;VALUE:VALUE:...',
      help=('Each element names a defined field and lists the matching values '
            'for that field.'))
  matcher.add_argument(
      '--network-src-ip-ranges',
      type=arg_parsers.ArgList(),
      metavar='SRC_IP_RANGE',
      help=('The source IPs/IP ranges to match for this rule. '
            'To match all IPs specify *.'))
  matcher.add_argument(
      '--network-dest-ip-ranges',
      type=arg_parsers.ArgList(),
      metavar='DEST_IP_RANGE',
      help=('The destination IPs/IP ranges to match for this rule. '
            'To match all IPs specify *.'))
  matcher.add_argument(
      '--network-ip-protocols',
      type=arg_parsers.ArgList(),
      metavar='IP_PROTOCOL',
      help=('The IP protocols to match for this rule. Each element can be an '
            '8-bit unsigned decimal number (e.g. "6"), range (e.g."253-254"), '
            'or one of the following protocol names: "tcp", "udp", "icmp", '
            '"esp", "ah", "ipip", or "sctp". To match all protocols specify '
            '*.'))
  matcher.add_argument(
      '--network-src-ports',
      type=arg_parsers.ArgList(),
      metavar='SRC_PORT',
      help=('The source ports to match for this rule. Each element can be an '
            '16-bit unsigned decimal number (e.g. "80") or range '
            '(e.g."0-1023"), To match all source ports specify *.'))
  matcher.add_argument(
      '--network-dest-ports',
      type=arg_parsers.ArgList(),
      metavar='DEST_PORT',
      help=('The destination ports to match for this rule. Each element can be '
            'an 16-bit unsigned decimal number (e.g. "80") or range '
            '(e.g."0-1023"), To match all destination ports specify *.'))
  matcher.add_argument(
      '--network-src-region-codes',
      type=arg_parsers.ArgList(),
      metavar='SRC_REGION_CODE',
      help=('The two letter ISO 3166-1 alpha-2 country code associated with '
            'the source IP address to match for this rule. To match all region '
            'codes specify *.'))
  matcher.add_argument(
      '--network-src-asns',
      type=arg_parsers.ArgList(),
      metavar='SRC_ASN',
      help=('BGP Autonomous System Number associated with the source IP '
            'address to match for this rule.'))


def AddAction(parser,
              required=True,
              support_redirect=False,
              support_rate_limit=False,
              support_fairshare=False):
  """Adds the action argument to the argparse."""
  actions = {
      'allow': 'Allows the request from HTTP(S) Load Balancing.',
      'deny': (
          'Denies the request from TCP/SSL Proxy and Network Load Balancing.'
      ),
      'deny-403': (
          'Denies the request from HTTP(S) Load Balancing, with an HTTP '
          'response status code of 403.'
      ),
      'deny-404': (
          'Denies the request from HTTP(S) Load Balancing, with an HTTP '
          'response status code of 404.'
      ),
      'deny-502': (
          'Denies the request from HTTP(S) Load Balancing, with an HTTP '
          'response status code of 502.'
      ),
      'redirect-to-recaptcha': (
          '(DEPRECATED) Redirects the request from HTTP(S) Load Balancing, for'
          ' reCAPTCHA Enterprise assessment. This flag choice is deprecated. '
          'Use --action=redirect and --redirect-type=google-recaptcha instead.'
      ),
  }
  if support_fairshare:
    actions.update({
        'fairshare':
            'When traffic reaches the threshold limit, requests from the '
            'clients matching this rule begin to be rate-limited using the '
            'Fair Share algorithm.'
    })
  if support_redirect:
    actions.update({
        'redirect':
            'Redirects the request from HTTP(S) Load Balancing, based on '
            'redirect options.'
    })
  if support_rate_limit:
    actions.update({
        'rate-based-ban':
            'Enforces rate-based ban action from HTTP(S) Load Balancing, '
            'based on rate limit options.',
        'throttle':
            'Enforces throttle action from HTTP(S) Load Balancing, based on '
            'rate limit options.'
    })
  parser.add_argument(
      '--action',
      choices=actions,
      type=lambda x: x.lower(),
      required=required,
      help='The action to take if the request matches the match condition.')


def AddDescription(parser):
  """Adds the preview argument to the argparse."""
  parser.add_argument(
      '--description', help='An optional, textual description for the rule.')


def AddPreview(parser, default):
  """Adds the preview argument to the argparse."""
  parser.add_argument(
      '--preview',
      action='store_true',
      default=default,
      help='If specified, the action will not be enforced.')


def AddRedirectOptions(parser):
  """Adds redirect action related argument to the argparse."""
  redirect_type = ['google-recaptcha', 'external-302']
  parser.add_argument(
      '--redirect-type',
      choices=redirect_type,
      type=lambda x: x.lower(),
      help="""\
      Type for the redirect action. Default to ``external-302'' if unspecified
      while --redirect-target is given.
      """)

  parser.add_argument(
      '--redirect-target',
      help="""\
      URL target for the redirect action. Must be specified if the redirect
      type is ``external-302''. Cannot be specified if the redirect type is
      ``google-recaptcha''.
      """)


def AddRateLimitOptions(
    parser,
    support_exceed_redirect=True,
    support_fairshare=False,
    support_multiple_rate_limit_keys=False,
):
  """Adds rate limiting related arguments to the argparse."""
  parser.add_argument(
      '--rate-limit-threshold-count',
      type=int,
      help=('Number of HTTP(S) requests for calculating the threshold for rate '
            'limiting requests.'))

  parser.add_argument(
      '--rate-limit-threshold-interval-sec',
      type=int,
      help=('Interval over which the threshold for rate limiting requests is '
            'computed.'))

  conform_actions = ['allow']
  parser.add_argument(
      '--conform-action',
      choices=conform_actions,
      type=lambda x: x.lower(),
      help=('Action to take when requests are under the given threshold. When '
            'requests are throttled, this is also the action for all requests '
            'which are not dropped.'))

  exceed_actions = ['deny-403', 'deny-404', 'deny-429', 'deny-502', 'deny']
  if support_exceed_redirect:
    exceed_actions.append('redirect')
  parser.add_argument(
      '--exceed-action',
      choices=exceed_actions,
      type=lambda x: x.lower(),
      help="""\
      Action to take when requests are above the given threshold. When a request
      is denied, return the specified HTTP response code. When a request is
      redirected, use the redirect options based on --exceed-redirect-type and
      --exceed-redirect-target below.
      """)

  if support_exceed_redirect:
    exceed_redirect_types = ['google-recaptcha', 'external-302']
    parser.add_argument(
        '--exceed-redirect-type',
        choices=exceed_redirect_types,
        type=lambda x: x.lower(),
        help="""\
        Type for the redirect action that is configured as the exceed action.
        """)
    parser.add_argument(
        '--exceed-redirect-target',
        help="""\
        URL target for the redirect action that is configured as the exceed
        action when the redirect type is ``external-302''.
        """)

  enforce_on_key = [
      'ip',
      'all',
      'http-header',
      'xff-ip',
      'http-cookie',
      'http-path',
      'sni',
      'region-code',
      'tls-ja3-fingerprint',
      'user-ip',
  ]
  parser.add_argument(
      '--enforce-on-key',
      choices=enforce_on_key,
      type=lambda x: x.lower(),
      help="""\
      Different key types available to enforce the rate limit threshold limit on:"""
      + _RATE_LIMIT_ENFORCE_ON_KEY_TYPES_DESCRIPTION,
  )

  parser.add_argument(
      '--enforce-on-key-name',
      help="""\
      Determines the key name for the rate limit key. Applicable only for the
      following rate limit key types:
      - http-header: The name of the HTTP header whose value is taken as the key
      value.
      - http-cookie: The name of the HTTP cookie whose value is taken as the key
      value.
      """)

  if support_multiple_rate_limit_keys:
    parser.add_argument(
        '--enforce-on-key-configs',
        type=arg_parsers.ArgDict(
            spec={key: str for key in enforce_on_key},
            min_length=1,
            max_length=3,
            allow_key_only=True,
        ),
        # The default renders as follows:
        # [all=ALL],[http-cookie=HTTP-COOKIE],
        # [http-header=HTTP-HEADER],[http-path=HTTP-PATH],
        # [ip=IP],[region-code=REGION-CODE],[sni=SNI],
        # [tls-ja3-fingerprint=TLS-JA3-FINGERPRINT],[user-ip=USER-IP],
        # [xff-ip=XFF-IP]]
        metavar='[[all],[ip],[xff-ip],[http-cookie=HTTP_COOKIE],[http-header=HTTP_HEADER],[http-path],[sni],[region-code],[tls-ja3-fingerprint],[user-ip]]',
        help="""\
        Specify up to 3 key type/name pairs to rate limit.
        Valid key types are:
        """
        + _RATE_LIMIT_ENFORCE_ON_KEY_TYPES_DESCRIPTION
        + """
      Key names are only applicable to the following key types:
      - http-header: The name of the HTTP header whose value is taken as the key value.
      - http-cookie: The name of the HTTP cookie whose value is taken as the key value.
      """,
    )

  parser.add_argument(
      '--ban-threshold-count',
      type=int,
      help="""\
      Number of HTTP(S) requests for calculating the threshold for
      banning requests. Can only be specified if the action for the
      rule is ``rate-based-ban''. If specified, the key will be banned
      for the configured ``BAN_DURATION_SEC'' when the number of requests
      that exceed the ``RATE_LIMIT_THRESHOLD_COUNT'' also exceed this
      ``BAN_THRESHOLD_COUNT''.
      """)

  parser.add_argument(
      '--ban-threshold-interval-sec',
      type=int,
      help="""\
      Interval over which the threshold for banning requests is
      computed. Can only be specified if the action for the rule is
      ``rate-based-ban''. If specified, the key will be banned for the
      configured ``BAN_DURATION_SEC'' when the number of requests that
      exceed the ``RATE_LIMIT_THRESHOLD_COUNT'' also exceed this
      ``BAN_THRESHOLD_COUNT''.
      """)

  parser.add_argument(
      '--ban-duration-sec',
      type=int,
      help="""\
      Can only be specified if the action for the rule is
      ``rate-based-ban''. If specified, determines the time (in seconds)
      the traffic will continue to be banned by the rate limit after
      the rate falls below the threshold.
      """)
  if support_fairshare:
    parser.add_argument(
        '--exceed-action-rpc-status-code',
        type=int,
        help=(
            'Status code, which should be an enum value of [google.rpc.Code]'))

    parser.add_argument(
        '--exceed-action-rpc-status-message',
        help=('Developer-facing error message, should be in English.'))


def AddRequestHeadersToAdd(parser):
  """Adds request-headers-to-add argument to the argparse."""
  parser.add_argument(
      '--request-headers-to-add',
      metavar='REQUEST_HEADERS_TO_ADD',
      type=arg_parsers.ArgDict(),
      help="""\
      A comma-separated list of header names and header values to add to
      requests that match this rule.
      """)


def AddTargetRuleSet(parser, is_add):
  """Adds target-rule-set argument to the argparse."""
  parser.add_argument(
      '--target-rule-set',
      required=True,
      help=_WAF_EXCLUSION_TARGET_RULE_SET_HELP_TEXT_FOR_ADD
      if is_add else _WAF_EXCLUSION_TARGET_RULE_SET_HELP_TEXT_FOR_REMOVE)


def AddTargetRuleIds(parser, is_add):
  """Adds target-rule-ids argument to the argparse."""
  parser.add_argument(
      '--target-rule-ids',
      type=arg_parsers.ArgList(),
      metavar='RULE_ID',
      help=_WAF_EXCLUSION_TARGET_RULE_IDS_HELP_TEXT_FOR_ADD
      if is_add else _WAF_EXCLUSION_TARGET_RULE_IDS_HELP_TEXT_FOR_REMOVE)


def AddRequestCookie(parser, is_add):
  """Adds request-cookie-to-exclude argument to the argparse."""
  parser.add_argument(
      '--request-cookie-to-exclude',
      type=arg_parsers.ArgDict(
          spec={
              'op': str,
              'val': str,
          }, required_keys=['op']),
      action='append',
      help=_WAF_EXCLUSION_REQUEST_COOKIE_HELP_TEXT_FOR_ADD
      if is_add else _WAF_EXCLUSION_REQUEST_COOKIE_HELP_TEXT_FOR_REMOVE)


def AddRequestHeader(parser, is_add):
  """Adds request-header-to-exclude argument to the argparse."""
  parser.add_argument(
      '--request-header-to-exclude',
      type=arg_parsers.ArgDict(
          spec={
              'op': str,
              'val': str,
          }, required_keys=['op']),
      action='append',
      help=_WAF_EXCLUSION_REQUEST_HEADER_HELP_TEXT_FOR_ADD
      if is_add else _WAF_EXCLUSION_REQUEST_HEADER_HELP_TEXT_FOR_REMOVE)


def AddRequestQueryParam(parser, is_add):
  """Adds request-query-param-to-exclude argument to the argparse."""
  parser.add_argument(
      '--request-query-param-to-exclude',
      type=arg_parsers.ArgDict(
          spec={
              'op': str,
              'val': str,
          }, required_keys=['op']),
      action='append',
      help=_WAF_EXCLUSION_REQUEST_QUERY_PARAM_HELP_TEXT_FOR_ADD
      if is_add else _WAF_EXCLUSION_REQUEST_QUERY_PARAM_HELP_TEXT_FOR_REMOVE)


def AddRequestUri(parser, is_add):
  """Adds request-uri-to-exclude argument to the argparse."""
  parser.add_argument(
      '--request-uri-to-exclude',
      type=arg_parsers.ArgDict(
          spec={
              'op': str,
              'val': str,
          }, required_keys=['op']),
      action='append',
      help=_WAF_EXCLUSION_REQUEST_URI_HELP_TEXT_FOR_ADD
      if is_add else _WAF_EXCLUSION_REQUEST_URI_HELP_TEXT_FOR_REMOVE)


def AddRecaptchaOptions(parser):
  """Adds reCAPTCHA token evaluation related arguments to the argparse."""
  parser.add_argument(
      '--recaptcha-action-site-keys',
      type=arg_parsers.ArgList(),
      metavar='SITE_KEY',
      help="""\
      A comma-separated list of site keys to be used during the validation of
      reCAPTCHA action-tokens. The provided site keys need to be created from
      the reCAPTCHA API under the same project where the security policy is created.
      """,
  )

  parser.add_argument(
      '--recaptcha-session-site-keys',
      type=arg_parsers.ArgList(),
      metavar='SITE_KEY',
      help="""\
      A comma-separated list of site keys to be used during the validation of
      reCAPTCHA session-tokens. The provided site keys need to be created from
      the reCAPTCHA API under the same project where the security policy is created.
      """,
  )
