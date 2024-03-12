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
"""Code that's shared between multiple org firewall policies subcommands."""


def ConvertFirewallPolicy(policy, project):
  """Converts Firewall Policy to terraform script.

  Args:
    policy: Network Firewall Policy
    project: Project container of Firewall Policy

  Returns:
    Terraform script
  """

  return """resource "google_compute_network_firewall_policy" "auto_generated_firewall_policy" {
  name = "%s"
  project = "%s"
  description = "%s"
}
""" % (
      policy.name,
      project,
      policy.description,
  )


def ConvertFirewallPolicyRule(rule):
  """Converts Firewall Policy rule to terraform script.

  Args:
    rule: Firewall Policy rule

  Returns:
    Terraform script
  """

  return """resource "google_compute_network_firewall_policy_rule" "auto_generated_rule_{priority}" {{
  action                  = "{action}"
  description             = "{description}"
  direction               = "{direction}"
  disabled                = {disabled}
  enable_logging          = {enable_logging}
  firewall_policy         = google_compute_network_firewall_policy.auto_generated_firewall_policy.name
  priority                = {priority}
  rule_name               = "{rule_name}"

  match {{
    dest_ip_ranges = [{dest_ip_ranges}]
    src_ip_ranges = [{src_ip_ranges}]
{src_secure_tags}{layer4_configs}  }}
{target_secure_tags}}}
""".format(
      action=rule.action,
      description=rule.description,
      direction=rule.direction,
      disabled=_ConvertBoolean(rule.disabled),
      enable_logging=_ConvertBoolean(rule.enableLogging),
      priority=rule.priority,
      rule_name=rule.ruleName,
      dest_ip_ranges=_ConvertArray(rule.match.destIpRanges),
      src_ip_ranges=_ConvertArray(rule.match.srcIpRanges),
      src_secure_tags=_ConvertSrcTags(rule.match.srcSecureTags),
      target_secure_tags=_ConvertTargetTags(rule.targetSecureTags),
      layer4_configs=_ConvertLayer4Config(rule.match.layer4Configs),
  )


def _ConvertBoolean(value):
  return str(value).lower()


def _ConvertArray(arr):
  return ', '.join(map(lambda x: '"%s"' % x, arr))


def _ConvertSrcTags(secure_tags):
  template = '    src_secure_tags {{\n      name = "{name}"\n    }}\n'
  records = map(lambda x: template.format(name=x.name), secure_tags)
  return ''.join(records)


def _ConvertTargetTags(secure_tags):
  template = '  target_secure_tags {{\n    name = "{name}"\n  }}\n'
  records = map(lambda x: template.format(name=x.name), secure_tags)
  return ''.join(records)


def _ConvertLayer4Config(layer4_configs):
  """Converts Firewall Policy Layer4 configs to terraform script.

  Args:
    layer4_configs: Firewall Policy layer4 configs

  Returns:
    Terraform script
  """

  records = []
  template = """    layer4_configs {{
      ip_protocol = "{ip_protocol}"
      ports = [{ports}]
    }}
"""
  for config in layer4_configs:
    records.append(
        template.format(
            ip_protocol=config.ipProtocol, ports=(_ConvertArray(config.ports))
        )
    )
  return ''.join(records)
