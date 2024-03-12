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
"""Code that's shared between multiple security policies subcommands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import base64
import json

from googlecloudsdk.calliope import exceptions
from googlecloudsdk.core import yaml
from googlecloudsdk.core.resource import resource_printer
import six


def SecurityPolicyFromFile(input_file, messages, file_format):
  """Returns the security policy read from the given file.

  Args:
    input_file: file, A file with a security policy config.
    messages: messages, The set of available messages.
    file_format: string, the format of the file to read from

  Returns:
    A security policy resource.
  """

  if file_format == 'yaml':
    parsed_security_policy = yaml.load(input_file)
  else:
    try:
      parsed_security_policy = json.load(input_file)
    except ValueError as e:
      raise exceptions.BadFileException('Error parsing JSON: {0}'.format(
          six.text_type(e)))

  security_policy = messages.SecurityPolicy()
  if 'description' in parsed_security_policy:
    security_policy.description = parsed_security_policy['description']
  if 'fingerprint' in parsed_security_policy:
    security_policy.fingerprint = base64.urlsafe_b64decode(
        parsed_security_policy['fingerprint'].encode('ascii'))
  if 'type' in parsed_security_policy:
    security_policy.type = (
        messages.SecurityPolicy.TypeValueValuesEnum(
            parsed_security_policy['type']))
  if 'cloudArmorConfig' in parsed_security_policy:
    security_policy.cloudArmorConfig = messages.SecurityPolicyCloudArmorConfig(
        enableMl=parsed_security_policy['cloudArmorConfig']['enableMl'])
  if 'adaptiveProtectionConfig' in parsed_security_policy:
    security_policy.adaptiveProtectionConfig = (
        messages.SecurityPolicyAdaptiveProtectionConfig(
            layer7DdosDefenseConfig=messages
            .SecurityPolicyAdaptiveProtectionConfigLayer7DdosDefenseConfig(
                enable=parsed_security_policy['adaptiveProtectionConfig']
                ['layer7DdosDefenseConfig']['enable']),))
    if 'autoDeployConfig' in parsed_security_policy['adaptiveProtectionConfig']:
      security_policy.adaptiveProtectionConfig.autoDeployConfig = (
          messages.SecurityPolicyAdaptiveProtectionConfigAutoDeployConfig())
      if 'loadThreshold' in parsed_security_policy['adaptiveProtectionConfig'][
          'autoDeployConfig']:
        security_policy.adaptiveProtectionConfig.autoDeployConfig.loadThreshold = (
            parsed_security_policy['adaptiveProtectionConfig']
            ['autoDeployConfig']['loadThreshold'])
      if 'confidenceThreshold' in parsed_security_policy[
          'adaptiveProtectionConfig']['autoDeployConfig']:
        security_policy.adaptiveProtectionConfig.autoDeployConfig.confidenceThreshold = (
            parsed_security_policy['adaptiveProtectionConfig']
            ['autoDeployConfig']['confidenceThreshold'])
      if 'impactedBaselineThreshold' in parsed_security_policy[
          'adaptiveProtectionConfig']['autoDeployConfig']:
        security_policy.adaptiveProtectionConfig.autoDeployConfig.impactedBaselineThreshold = (
            parsed_security_policy['adaptiveProtectionConfig']
            ['autoDeployConfig']['impactedBaselineThreshold'])
      if 'expirationSec' in parsed_security_policy['adaptiveProtectionConfig'][
          'autoDeployConfig']:
        security_policy.adaptiveProtectionConfig.autoDeployConfig.expirationSec = (
            parsed_security_policy['adaptiveProtectionConfig']
            ['autoDeployConfig']['expirationSec'])
    if 'ruleVisibility' in parsed_security_policy['adaptiveProtectionConfig'][
        'layer7DdosDefenseConfig']:
      security_policy.adaptiveProtectionConfig.layer7DdosDefenseConfig.ruleVisibility = (
          messages.SecurityPolicyAdaptiveProtectionConfigLayer7DdosDefenseConfig
          .RuleVisibilityValueValuesEnum(
              parsed_security_policy['adaptiveProtectionConfig']
              ['layer7DdosDefenseConfig']['ruleVisibility']))
  if 'advancedOptionsConfig' in parsed_security_policy:
    advanced_options_config = parsed_security_policy['advancedOptionsConfig']
    security_policy.advancedOptionsConfig = (
        messages.SecurityPolicyAdvancedOptionsConfig())
    if 'jsonParsing' in advanced_options_config:
      security_policy.advancedOptionsConfig.jsonParsing = (
          messages.SecurityPolicyAdvancedOptionsConfig
          .JsonParsingValueValuesEnum(
              advanced_options_config['jsonParsing']))
    if 'jsonCustomConfig' in advanced_options_config:
      security_policy.advancedOptionsConfig.jsonCustomConfig = (
          messages.SecurityPolicyAdvancedOptionsConfigJsonCustomConfig(
              contentTypes=advanced_options_config
              ['jsonCustomConfig'].get('contentTypes', [])))
    if 'logLevel' in advanced_options_config:
      security_policy.advancedOptionsConfig.logLevel = (
          messages.SecurityPolicyAdvancedOptionsConfig.LogLevelValueValuesEnum(
              advanced_options_config['logLevel']))
    if 'userIpRequestHeaders' in advanced_options_config:
      security_policy.advancedOptionsConfig.userIpRequestHeaders = (
          advanced_options_config['userIpRequestHeaders'])
  if 'ddosProtectionConfig' in parsed_security_policy:
    security_policy.ddosProtectionConfig = (
        messages.SecurityPolicyDdosProtectionConfig(
            ddosProtection=messages.SecurityPolicyDdosProtectionConfig
            .DdosProtectionValueValuesEnum(
                parsed_security_policy['ddosProtectionConfig']
                ['ddosProtection'])))
  if 'recaptchaOptionsConfig' in parsed_security_policy:
    security_policy.recaptchaOptionsConfig = (
        messages.SecurityPolicyRecaptchaOptionsConfig())
    if 'redirectSiteKey' in parsed_security_policy['recaptchaOptionsConfig']:
      security_policy.recaptchaOptionsConfig.redirectSiteKey = (
          parsed_security_policy['recaptchaOptionsConfig']['redirectSiteKey'])

  if 'userDefinedFields' in parsed_security_policy:
    user_defined_fields = []
    for udf in parsed_security_policy['userDefinedFields']:
      user_defined_field = messages.SecurityPolicyUserDefinedField()
      user_defined_field.name = udf['name']
      user_defined_field.base = (
          messages.SecurityPolicyUserDefinedField.BaseValueValuesEnum(
              udf['base']
          )
      )
      user_defined_field.offset = udf['offset']
      user_defined_field.size = udf['size']
      if 'mask' in udf:
        user_defined_field.mask = udf['mask']
      user_defined_fields.append(user_defined_field)
    security_policy.userDefinedFields = user_defined_fields

  rules = []
  for rule in parsed_security_policy['rules']:
    security_policy_rule = messages.SecurityPolicyRule()
    security_policy_rule.action = rule['action']
    if 'description' in rule:
      security_policy_rule.description = rule['description']
    if 'match' in rule:
      match = messages.SecurityPolicyRuleMatcher()
      if 'versionedExpr' in rule['match']:
        match.versionedExpr = ConvertToEnum(
            rule['match']['versionedExpr'], messages
        )
      if 'expr' in rule['match']:
        match.expr = messages.Expr(
            expression=rule['match']['expr']['expression']
        )
      if 'exprOptions' in rule['match']:
        expr_options = messages.SecurityPolicyRuleMatcherExprOptions()
        if 'recaptchaOptions' in rule['match']['exprOptions']:
          expr_options.recaptchaOptions = (
              messages.SecurityPolicyRuleMatcherExprOptionsRecaptchaOptions(
                  actionTokenSiteKeys=rule['match']['exprOptions'][
                      'recaptchaOptions'
                  ].get('actionTokenSiteKeys', []),
                  sessionTokenSiteKeys=rule['match']['exprOptions'][
                      'recaptchaOptions'
                  ].get('sessionTokenSiteKeys', []),
              )
          )
        match.exprOptions = expr_options
      if 'config' in rule['match']:
        if 'srcIpRanges' in rule['match']['config']:
          match.config = messages.SecurityPolicyRuleMatcherConfig(
              srcIpRanges=rule['match']['config']['srcIpRanges']
          )
      security_policy_rule.match = match
    if 'networkMatch' in rule:
      network_match = messages.SecurityPolicyRuleNetworkMatcher()
      if 'userDefinedFields' in rule['networkMatch']:
        user_defined_fields = []
        for udf in rule['networkMatch']['userDefinedFields']:
          user_defined_field_match = (
              messages.SecurityPolicyRuleNetworkMatcherUserDefinedFieldMatch()
          )
          user_defined_field_match.name = udf['name']
          user_defined_field_match.values = udf['values']
          user_defined_fields.append(user_defined_field_match)
        network_match.userDefinedFields = user_defined_fields
      if 'srcIpRanges' in rule['networkMatch']:
        network_match.srcIpRanges = rule['networkMatch']['srcIpRanges']
      if 'destIpRanges' in rule['networkMatch']:
        network_match.destIpRanges = rule['networkMatch']['destIpRanges']
      if 'ipProtocols' in rule['networkMatch']:
        network_match.ipProtocols = rule['networkMatch']['ipProtocols']
      if 'srcPorts' in rule['networkMatch']:
        network_match.srcPorts = rule['networkMatch']['srcPorts']
      if 'destPorts' in rule['networkMatch']:
        network_match.destPorts = rule['networkMatch']['destPorts']
      if 'srcRegionCodes' in rule['networkMatch']:
        network_match.srcRegionCodes = rule['networkMatch']['srcRegionCodes']
      if 'srcAsns' in rule['networkMatch']:
        network_match.srcAsns = rule['networkMatch']['srcAsns']
      security_policy_rule.networkMatch = network_match
    security_policy_rule.priority = int(rule['priority'])
    if 'preview' in rule:
      security_policy_rule.preview = rule['preview']
    rules.append(security_policy_rule)
    if 'redirectTarget' in rule:
      security_policy_rule.redirectTarget = rule['redirectTarget']
    if 'ruleNumber' in rule:
      security_policy_rule.ruleNumber = int(rule['ruleNumber'])
    if 'redirectOptions' in rule:
      redirect_options = messages.SecurityPolicyRuleRedirectOptions()
      if 'type' in rule['redirectOptions']:
        redirect_options.type = (
            messages.SecurityPolicyRuleRedirectOptions.TypeValueValuesEnum(
                rule['redirectOptions']['type']))
      if 'target' in rule['redirectOptions']:
        redirect_options.target = rule['redirectOptions']['target']
      security_policy_rule.redirectOptions = redirect_options
    if 'headerAction' in rule:
      header_action = messages.SecurityPolicyRuleHttpHeaderAction()
      headers_in_rule = rule['headerAction'].get('requestHeadersToAdds', [])
      headers_to_add = []
      for header_to_add in headers_in_rule:
        headers_to_add.append(
            messages.SecurityPolicyRuleHttpHeaderActionHttpHeaderOption(
                headerName=header_to_add['headerName'],
                headerValue=header_to_add['headerValue']))
      if headers_to_add:
        header_action.requestHeadersToAdds = headers_to_add
      security_policy_rule.headerAction = header_action
    if 'rateLimitOptions' in rule:
      rate_limit_options = rule['rateLimitOptions']
      security_policy_rule.rateLimitOptions = (
          messages.SecurityPolicyRuleRateLimitOptions(
              rateLimitThreshold=messages
              .SecurityPolicyRuleRateLimitOptionsThreshold(
                  count=rate_limit_options['rateLimitThreshold']['count'],
                  intervalSec=rate_limit_options['rateLimitThreshold']
                  ['intervalSec']),
              conformAction=rate_limit_options['conformAction'],
              exceedAction=rate_limit_options['exceedAction']))
      if 'exceedActionRpcStatus' in rate_limit_options:
        exceed_action_rpc_status = (
            messages.SecurityPolicyRuleRateLimitOptionsRpcStatus()
        )
        if 'code' in rate_limit_options['exceedActionRpcStatus']:
          exceed_action_rpc_status.code = rate_limit_options[
              'exceedActionRpcStatus']['code']
        if 'message' in rate_limit_options['exceedActionRpcStatus']:
          exceed_action_rpc_status.message = rate_limit_options[
              'exceedActionRpcStatus']['message']
        security_policy_rule.rateLimitOptions.exceedActionRpcStatus = (
            exceed_action_rpc_status
        )
      if 'exceedRedirectOptions' in rate_limit_options:
        exceed_redirect_options = messages.SecurityPolicyRuleRedirectOptions()
        if 'type' in rate_limit_options['exceedRedirectOptions']:
          exceed_redirect_options.type = (
              messages.SecurityPolicyRuleRedirectOptions.TypeValueValuesEnum(
                  rate_limit_options['exceedRedirectOptions']['type']))
        if 'target' in rate_limit_options['exceedRedirectOptions']:
          exceed_redirect_options.target = rate_limit_options[
              'exceedRedirectOptions']['target']
        security_policy_rule.rateLimitOptions.exceedRedirectOptions = (
            exceed_redirect_options)
      if 'banThreshold' in rate_limit_options:
        security_policy_rule.rateLimitOptions.banThreshold = (
            messages.SecurityPolicyRuleRateLimitOptionsThreshold(
                count=rate_limit_options['banThreshold']['count'],
                intervalSec=rate_limit_options['banThreshold']['intervalSec']))
      if 'banDurationSec' in rate_limit_options:
        security_policy_rule.rateLimitOptions.banDurationSec = (
            rate_limit_options['banDurationSec'])
      if 'enforceOnKey' in rate_limit_options:
        security_policy_rule.rateLimitOptions.enforceOnKey = (
            messages.SecurityPolicyRuleRateLimitOptions
            .EnforceOnKeyValueValuesEnum(rate_limit_options['enforceOnKey']))
      if 'enforceOnKeyName' in rate_limit_options:
        security_policy_rule.rateLimitOptions.enforceOnKeyName = (
            rate_limit_options['enforceOnKeyName'])
      for config in rate_limit_options.get('enforceOnKeyConfigs', []):
        enforce_on_key_config = (
            messages.SecurityPolicyRuleRateLimitOptionsEnforceOnKeyConfig()
        )
        if 'enforceOnKeyType' in config:
          enforce_on_key_config.enforceOnKeyType = messages.SecurityPolicyRuleRateLimitOptionsEnforceOnKeyConfig.EnforceOnKeyTypeValueValuesEnum(
              config['enforceOnKeyType']
          )
        if 'enforceOnKeyName' in config:
          enforce_on_key_config.enforceOnKeyName = config['enforceOnKeyName']
        security_policy_rule.rateLimitOptions.enforceOnKeyConfigs.append(
            enforce_on_key_config
        )
    if 'preconfiguredWafConfig' in rule:
      preconfig_waf_config = messages.SecurityPolicyRulePreconfiguredWafConfig()
      for exclusion in rule['preconfiguredWafConfig'].get('exclusions', []):
        exclusion_to_add = (
            messages.SecurityPolicyRulePreconfiguredWafConfigExclusion())
        if 'targetRuleSet' in exclusion:
          exclusion_to_add.targetRuleSet = exclusion['targetRuleSet']
        for target_rule_id in exclusion.get('targetRuleIds', []):
          exclusion_to_add.targetRuleIds.append(target_rule_id)
        for request_header in exclusion.get('requestHeadersToExclude', []):
          exclusion_to_add.requestHeadersToExclude.append(
              ConvertPreconfigWafExclusionRequestField(request_header,
                                                       messages))
        for request_cookie in exclusion.get('requestCookiesToExclude', []):
          exclusion_to_add.requestCookiesToExclude.append(
              ConvertPreconfigWafExclusionRequestField(request_cookie,
                                                       messages))
        for request_query_param in exclusion.get('requestQueryParamsToExclude',
                                                 []):
          exclusion_to_add.requestQueryParamsToExclude.append(
              ConvertPreconfigWafExclusionRequestField(request_query_param,
                                                       messages))
        for request_uri in exclusion.get('requestUrisToExclude', []):
          exclusion_to_add.requestUrisToExclude.append(
              ConvertPreconfigWafExclusionRequestField(request_uri, messages))
        preconfig_waf_config.exclusions.append(exclusion_to_add)
      security_policy_rule.preconfiguredWafConfig = preconfig_waf_config

  security_policy.rules = rules

  return security_policy


def ConvertToEnum(versioned_expr, messages):
  """Converts a string version of a versioned expr to the enum representation.

  Args:
    versioned_expr: string, string version of versioned expr to convert.
    messages: messages, The set of available messages.

  Returns:
    A versioned expression enum.
  """
  return messages.SecurityPolicyRuleMatcher.VersionedExprValueValuesEnum(
      versioned_expr)


def ConvertPreconfigWafExclusionRequestField(request_field_in_rule, messages):
  """Converts the request field in preconfigured WAF exclusion configuration.

  Args:
    request_field_in_rule: a request field in preconfigured WAF exclusion
      configuration read from the security policy config file.
    messages: the set of available messages.

  Returns:
    The proto representation of the request field.
  """
  request_field = (
      messages.SecurityPolicyRulePreconfiguredWafConfigExclusionFieldParams())
  if 'op' in request_field_in_rule:
    request_field.op = (
        messages.SecurityPolicyRulePreconfiguredWafConfigExclusionFieldParams
        .OpValueValuesEnum(request_field_in_rule['op']))
  if 'val' in request_field_in_rule:
    request_field.val = request_field_in_rule['val']
  return request_field


def WriteToFile(output_file, security_policy, file_format):
  """Writes the given security policy in the given format to the given file.

  Args:
    output_file: file, File into which the security policy should be written.
    security_policy: resource, SecurityPolicy to be written out.
    file_format: string, the format of the file to write to.
  """
  resource_printer.Print(
      security_policy, print_format=file_format, out=output_file)


def CreateCloudArmorConfig(client, args):
  """Returns a SecurityPolicyCloudArmorConfig message."""

  messages = client.messages
  cloud_armor_config = None
  if args.enable_ml is not None:
    cloud_armor_config = messages.SecurityPolicyCloudArmorConfig(
        enableMl=args.enable_ml)
  return cloud_armor_config


def CreateAdaptiveProtectionConfig(client, args,
                                   existing_adaptive_protection_config):
  """Returns a SecurityPolicyAdaptiveProtectionConfig message."""

  messages = client.messages
  adaptive_protection_config = (
      existing_adaptive_protection_config if existing_adaptive_protection_config
      is not None else messages.SecurityPolicyAdaptiveProtectionConfig())

  if (args.IsSpecified('enable_layer7_ddos_defense') or
      args.IsSpecified('layer7_ddos_defense_rule_visibility')):
    layer7_ddos_defense_config = (
        (adaptive_protection_config.layer7DdosDefenseConfig)
        if adaptive_protection_config.layer7DdosDefenseConfig is not None
        else messages.SecurityPolicyAdaptiveProtectionConfigLayer7DdosDefenseConfig()
    )
    if args.IsSpecified('enable_layer7_ddos_defense'):
      layer7_ddos_defense_config.enable = args.enable_layer7_ddos_defense
    if args.IsSpecified('layer7_ddos_defense_rule_visibility'):
      layer7_ddos_defense_config.ruleVisibility = (
          messages.SecurityPolicyAdaptiveProtectionConfigLayer7DdosDefenseConfig
          .RuleVisibilityValueValuesEnum(
              args.layer7_ddos_defense_rule_visibility))
    adaptive_protection_config.layer7DdosDefenseConfig = (
        layer7_ddos_defense_config)

  return adaptive_protection_config


def CreateAdaptiveProtectionConfigWithAutoDeployConfig(
    client, args, existing_adaptive_protection_config):
  """Returns a SecurityPolicyAdaptiveProtectionConfig message with AutoDeployConfig."""

  messages = client.messages
  adaptive_protection_config = CreateAdaptiveProtectionConfig(
      client, args, existing_adaptive_protection_config)

  if args.IsSpecified(
      'layer7_ddos_defense_auto_deploy_load_threshold') or args.IsSpecified(
          'layer7_ddos_defense_auto_deploy_confidence_threshold'
      ) or args.IsSpecified(
          'layer7_ddos_defense_auto_deploy_impacted_baseline_threshold'
      ) or args.IsSpecified('layer7_ddos_defense_auto_deploy_expiration_sec'):
    auto_deploy_config = (
        adaptive_protection_config.autoDeployConfig
        if adaptive_protection_config.autoDeployConfig is not None else
        messages.SecurityPolicyAdaptiveProtectionConfigAutoDeployConfig())
    if args.IsSpecified('layer7_ddos_defense_auto_deploy_load_threshold'):
      auto_deploy_config.loadThreshold = (
          args.layer7_ddos_defense_auto_deploy_load_threshold)
    if args.IsSpecified('layer7_ddos_defense_auto_deploy_confidence_threshold'):
      auto_deploy_config.confidenceThreshold = (
          args.layer7_ddos_defense_auto_deploy_confidence_threshold)
    if args.IsSpecified(
        'layer7_ddos_defense_auto_deploy_impacted_baseline_threshold'):
      auto_deploy_config.impactedBaselineThreshold = (
          args.layer7_ddos_defense_auto_deploy_impacted_baseline_threshold)
    if args.IsSpecified('layer7_ddos_defense_auto_deploy_expiration_sec'):
      auto_deploy_config.expirationSec = (
          args.layer7_ddos_defense_auto_deploy_expiration_sec)

    adaptive_protection_config.autoDeployConfig = auto_deploy_config

  return adaptive_protection_config


def CreateAdvancedOptionsConfig(client, args, existing_advanced_options_config):
  """Returns a SecurityPolicyAdvancedOptionsConfig message."""

  messages = client.messages
  advanced_options_config = (
      existing_advanced_options_config if existing_advanced_options_config
      is not None else messages.SecurityPolicyAdvancedOptionsConfig())

  if args.IsSpecified('json_parsing'):
    advanced_options_config.jsonParsing = (
        messages.SecurityPolicyAdvancedOptionsConfig.JsonParsingValueValuesEnum(
            args.json_parsing))

  if args.IsSpecified('json_custom_content_types'):
    advanced_options_config.jsonCustomConfig = (
        messages.SecurityPolicyAdvancedOptionsConfigJsonCustomConfig(
            contentTypes=args.json_custom_content_types))

  if args.IsSpecified('log_level'):
    advanced_options_config.logLevel = (
        messages.SecurityPolicyAdvancedOptionsConfig.LogLevelValueValuesEnum(
            args.log_level))

  if args.IsSpecified('user_ip_request_headers'):
    advanced_options_config.userIpRequestHeaders = args.user_ip_request_headers

  return advanced_options_config


def CreateDdosProtectionConfig(client, args, existing_ddos_protection_config):
  """Returns a SecurityPolicyDdosProtectionConfig message."""

  messages = client.messages
  ddos_protection_config = (
      existing_ddos_protection_config if existing_ddos_protection_config
      is not None else messages.SecurityPolicyDdosProtectionConfig())

  if args.IsSpecified('network_ddos_protection'):
    ddos_protection_config.ddosProtection = (
        messages.SecurityPolicyDdosProtectionConfig
        .DdosProtectionValueValuesEnum(args.network_ddos_protection))

  return ddos_protection_config


def CreateDdosProtectionConfigOld(client, args,
                                  existing_ddos_protection_config):
  """Returns a SecurityPolicyDdosProtectionConfig message."""

  messages = client.messages
  ddos_protection_config = (
      existing_ddos_protection_config if existing_ddos_protection_config
      is not None else messages.SecurityPolicyDdosProtectionConfig())

  if args.IsSpecified('ddos_protection'):
    ddos_protection_config.ddosProtection = (
        messages.SecurityPolicyDdosProtectionConfig
        .DdosProtectionValueValuesEnum(args.ddos_protection))

  return ddos_protection_config


def CreateRecaptchaOptionsConfig(client, args,
                                 existing_recaptcha_options_config):
  """Returns a SecurityPolicyRecaptchaOptionsConfig message."""

  messages = client.messages
  recaptcha_options_config = (
      existing_recaptcha_options_config if existing_recaptcha_options_config
      is not None else messages.SecurityPolicyRecaptchaOptionsConfig())

  if args.IsSpecified('recaptcha_redirect_site_key'):
    recaptcha_options_config.redirectSiteKey = args.recaptcha_redirect_site_key

  return recaptcha_options_config


def CreateRateLimitOptions(
    client, args, support_fairshare, support_multiple_rate_limit_keys
):
  """Returns a SecurityPolicyRuleRateLimitOptions message."""

  messages = client.messages
  rate_limit_options = messages.SecurityPolicyRuleRateLimitOptions()
  is_updated = False

  if (args.IsSpecified('rate_limit_threshold_count') or
      args.IsSpecified('rate_limit_threshold_interval_sec')):
    rate_limit_threshold = (
        messages.SecurityPolicyRuleRateLimitOptionsThreshold())
    if args.IsSpecified('rate_limit_threshold_count'):
      rate_limit_threshold.count = args.rate_limit_threshold_count
    if args.IsSpecified('rate_limit_threshold_interval_sec'):
      rate_limit_threshold.intervalSec = args.rate_limit_threshold_interval_sec
    rate_limit_options.rateLimitThreshold = rate_limit_threshold
    is_updated = True

  if args.IsSpecified('conform_action'):
    rate_limit_options.conformAction = _ConvertConformAction(
        args.conform_action)
    is_updated = True
  if args.IsSpecified('exceed_action'):
    rate_limit_options.exceedAction = _ConvertExceedAction(args.exceed_action)
    is_updated = True
  if (args.IsSpecified('exceed_redirect_type') or
      args.IsSpecified('exceed_redirect_target')):
    exceed_redirect_options = messages.SecurityPolicyRuleRedirectOptions()
    if args.IsSpecified('exceed_redirect_type'):
      exceed_redirect_options.type = (
          messages.SecurityPolicyRuleRedirectOptions.TypeValueValuesEnum(
              _ConvertRedirectType(args.exceed_redirect_type)))
    if args.IsSpecified('exceed_redirect_target'):
      exceed_redirect_options.target = args.exceed_redirect_target
    rate_limit_options.exceedRedirectOptions = exceed_redirect_options
    is_updated = True
  if args.IsSpecified('enforce_on_key'):
    rate_limit_options.enforceOnKey = (
        messages.SecurityPolicyRuleRateLimitOptions.EnforceOnKeyValueValuesEnum(
            ConvertEnforceOnKey(args.enforce_on_key)))
    is_updated = True
  if args.IsSpecified('enforce_on_key_name'):
    rate_limit_options.enforceOnKeyName = args.enforce_on_key_name
    is_updated = True

  if support_multiple_rate_limit_keys and args.IsSpecified(
      'enforce_on_key_configs'
  ):
    enforce_on_key_configs = []
    for k, v in args.enforce_on_key_configs.items():
      enforce_on_key_configs.append(
          messages.SecurityPolicyRuleRateLimitOptionsEnforceOnKeyConfig(
              enforceOnKeyType=messages.SecurityPolicyRuleRateLimitOptionsEnforceOnKeyConfig.EnforceOnKeyTypeValueValuesEnum(
                  ConvertEnforceOnKey(k)
              ),
              enforceOnKeyName=v if v else None,
          )
      )
    rate_limit_options.enforceOnKeyConfigs = enforce_on_key_configs
    is_updated = True

  if (args.IsSpecified('ban_threshold_count') or
      args.IsSpecified('ban_threshold_interval_sec')):
    ban_threshold = messages.SecurityPolicyRuleRateLimitOptionsThreshold()
    if args.IsSpecified('ban_threshold_count'):
      ban_threshold.count = args.ban_threshold_count
    if args.IsSpecified('ban_threshold_interval_sec'):
      ban_threshold.intervalSec = args.ban_threshold_interval_sec
    rate_limit_options.banThreshold = ban_threshold
    is_updated = True

  if args.IsSpecified('ban_duration_sec'):
    rate_limit_options.banDurationSec = args.ban_duration_sec
    is_updated = True

  if support_fairshare and (
      args.IsSpecified('exceed_action_rpc_status_code') or
      args.IsSpecified('exceed_action_rpc_status_message')):
    exceed_action_rpc_status = (
        messages.SecurityPolicyRuleRateLimitOptionsRpcStatus()
    )
    if args.IsSpecified('exceed_action_rpc_status_code'):
      exceed_action_rpc_status.code = args.exceed_action_rpc_status_code
    if args.IsSpecified('exceed_action_rpc_status_message'):
      exceed_action_rpc_status.message = args.exceed_action_rpc_status_message
    rate_limit_options.exceedActionRpcStatus = exceed_action_rpc_status
    is_updated = True

  return rate_limit_options if is_updated else None


def _ConvertConformAction(action):
  return {'allow': 'allow'}.get(action, action)


def _ConvertExceedAction(action):
  return {
      'deny-403': 'deny(403)',
      'deny-404': 'deny(404)',
      'deny-429': 'deny(429)',
      'deny-502': 'deny(502)'
  }.get(action, action)


def ConvertEnforceOnKey(enforce_on_key):
  return {
      'ip': 'IP',
      'all-ips': 'ALL_IPS',
      'all': 'ALL',
      'http-header': 'HTTP_HEADER',
      'xff-ip': 'XFF_IP',
      'http-cookie': 'HTTP_COOKIE',
      'http-path': 'HTTP_PATH',
      'sni': 'SNI',
      'region-code': 'REGION_CODE',
      'tls-ja3-fingerprint': 'TLS_JA3_FINGERPRINT',
      'user-ip': 'USER_IP',
  }.get(enforce_on_key, enforce_on_key)


def CreateRedirectOptions(client, args):
  """Returns a SecurityPolicyRuleRedirectOptions message."""

  messages = client.messages
  redirect_options = messages.SecurityPolicyRuleRedirectOptions()
  is_updated = False

  if args.IsSpecified('redirect_type'):
    redirect_options.type = (
        messages.SecurityPolicyRuleRedirectOptions.TypeValueValuesEnum(
            _ConvertRedirectType(args.redirect_type)))
    is_updated = True

  # If --redirect-target is given while --redirect-type is unspecified, type
  # is implicitly set to be EXTERNAL_302.
  if args.IsSpecified('redirect_target'):
    redirect_options.target = args.redirect_target
    if redirect_options.type is None:
      redirect_options.type = (
          messages.SecurityPolicyRuleRedirectOptions.TypeValueValuesEnum
          .EXTERNAL_302)
    is_updated = True

  return redirect_options if is_updated else None


def _ConvertRedirectType(redirect_type):
  return {
      'google-recaptcha': 'GOOGLE_RECAPTCHA',
      'external-302': 'EXTERNAL_302'
  }.get(redirect_type, redirect_type)


def CreateExpressionOptions(client, args):
  """Returns a SecurityPolicyRuleMatcherExprOptions message."""
  if not args.IsSpecified(
      'recaptcha_action_site_keys'
  ) and not args.IsSpecified('recaptcha_session_site_keys'):
    return None

  messages = client.messages
  recaptcha_options = (
      messages.SecurityPolicyRuleMatcherExprOptionsRecaptchaOptions()
  )

  if args.IsSpecified('recaptcha_action_site_keys'):
    recaptcha_options.actionTokenSiteKeys = args.recaptcha_action_site_keys
  if args.IsSpecified('recaptcha_session_site_keys'):
    recaptcha_options.sessionTokenSiteKeys = args.recaptcha_session_site_keys

  return messages.SecurityPolicyRuleMatcherExprOptions(
      recaptchaOptions=recaptcha_options
  )


def CreateNetworkMatcher(client, args):
  """Returns a SecurityPolicyRuleNetworkMatcher message."""

  messages = client.messages
  network_matcher = messages.SecurityPolicyRuleNetworkMatcher()
  update_mask = []
  is_updated = False

  if getattr(args, 'network_user_defined_fields', None) is not None:
    user_defined_fields = []
    for user_defined_field in args.network_user_defined_fields:
      # user defined field match will be in the following format:
      # "name;value1:value2:value3"
      parsed = user_defined_field.split(';')
      name = parsed[0]
      values = parsed[1].split(':')
      user_defined_fields.append(
          messages.SecurityPolicyRuleNetworkMatcherUserDefinedFieldMatch(
              name=name, values=values
          )
      )
    network_matcher.userDefinedFields = user_defined_fields
    update_mask.append('network_match.user_defined_fields')
    is_updated = True
  if getattr(args, 'network_src_ip_ranges', None) is not None:
    network_matcher.srcIpRanges = args.network_src_ip_ranges
    update_mask.append('network_match.src_ip_ranges')
    is_updated = True
  if getattr(args, 'network_dest_ip_ranges', None) is not None:
    network_matcher.destIpRanges = args.network_dest_ip_ranges
    update_mask.append('network_match.dest_ip_ranges')
    is_updated = True
  if getattr(args, 'network_ip_protocols', None) is not None:
    network_matcher.ipProtocols = args.network_ip_protocols
    update_mask.append('network_match.ip_protocols')
    is_updated = True
  if getattr(args, 'network_src_ports', None) is not None:
    network_matcher.srcPorts = args.network_src_ports
    update_mask.append('network_match.src_ports')
    is_updated = True
  if getattr(args, 'network_dest_ports', None) is not None:
    network_matcher.destPorts = args.network_dest_ports
    update_mask.append('network_match.dest_ports')
    is_updated = True
  if getattr(args, 'network_src_region_codes', None) is not None:
    network_matcher.srcRegionCodes = args.network_src_region_codes
    update_mask.append('network_match.src_region_codes')
    is_updated = True
  if getattr(args, 'network_src_asns', None) is not None:
    network_matcher.srcAsns = [int(asn) for asn in args.network_src_asns]
    update_mask.append('network_match.src_asns')
    is_updated = True

  update_mask_str = ','.join(update_mask)

  return (network_matcher, update_mask_str) if is_updated else (None, None)


def CreateUserDefinedField(client, args):
  """Returns a SecurityPolicyUserDefinedField message."""

  messages = client.messages
  user_defined_field = messages.SecurityPolicyUserDefinedField()

  user_defined_field.name = args.user_defined_field_name
  user_defined_field.base = (
      messages.SecurityPolicyUserDefinedField.BaseValueValuesEnum(
          _ConvertUserDefinedFieldBase(args.base)
      )
  )
  user_defined_field.offset = args.offset
  user_defined_field.size = args.size

  if getattr(args, 'mask', None) is not None:
    user_defined_field.mask = args.mask

  return user_defined_field


def _ConvertUserDefinedFieldBase(base):
  return {'ipv4': 'IPV4', 'ipv6': 'IPV6', 'tcp': 'TCP', 'udp': 'UDP'}.get(
      base, base
  )


def CreateLayer7DdosDefenseThresholdConfig(
    client, args, support_granularity_config
):
  """Returns a SecurityPolicyAdaptiveProtectionConfigLayer7DdosDefenseConfigThresholdConfig message."""

  messages = client.messages
  threshold_config = (
      messages.SecurityPolicyAdaptiveProtectionConfigLayer7DdosDefenseConfigThresholdConfig()
  )

  threshold_config.name = args.threshold_config_name

  if args.IsSpecified('auto_deploy_load_threshold'):
    threshold_config.autoDeployLoadThreshold = args.auto_deploy_load_threshold
  if args.IsSpecified('auto_deploy_confidence_threshold'):
    threshold_config.autoDeployConfidenceThreshold = (
        args.auto_deploy_confidence_threshold
    )
  if args.IsSpecified('auto_deploy_impacted_baseline_threshold'):
    threshold_config.autoDeployImpactedBaselineThreshold = (
        args.auto_deploy_impacted_baseline_threshold
    )
  if args.IsSpecified('auto_deploy_expiration_sec'):
    threshold_config.autoDeployExpirationSec = args.auto_deploy_expiration_sec

  if support_granularity_config:
    if args.IsSpecified('detection_load_threshold'):
      threshold_config.detectionLoadThreshold = args.detection_load_threshold
    if args.IsSpecified('detection_absolute_qps'):
      threshold_config.detectionAbsoluteQps = args.detection_absolute_qps
    if args.IsSpecified('detection_relative_to_baseline_qps'):
      threshold_config.detectionRelativeToBaselineQps = (
          args.detection_relative_to_baseline_qps
      )
    if args.IsSpecified('traffic_granularity_configs'):
      traffic_granularity_configs = []
      for arg_traffic_granularity_config in args.traffic_granularity_configs:
        traffic_granularity_config = (
            messages.SecurityPolicyAdaptiveProtectionConfigLayer7DdosDefenseConfigThresholdConfigTrafficGranularityConfig()
        )
        if 'type' in arg_traffic_granularity_config:
          traffic_granularity_config.type = messages.SecurityPolicyAdaptiveProtectionConfigLayer7DdosDefenseConfigThresholdConfigTrafficGranularityConfig.TypeValueValuesEnum(
              arg_traffic_granularity_config['type']
          )
        if 'value' in arg_traffic_granularity_config:
          traffic_granularity_config.value = arg_traffic_granularity_config[
              'value'
          ]
        if 'enableEachUniqueValue' in arg_traffic_granularity_config:
          traffic_granularity_config.enableEachUniqueValue = (
              arg_traffic_granularity_config['enableEachUniqueValue']
          )
        traffic_granularity_configs.append(traffic_granularity_config)
      threshold_config.trafficGranularityConfigs = traffic_granularity_configs

  return threshold_config
