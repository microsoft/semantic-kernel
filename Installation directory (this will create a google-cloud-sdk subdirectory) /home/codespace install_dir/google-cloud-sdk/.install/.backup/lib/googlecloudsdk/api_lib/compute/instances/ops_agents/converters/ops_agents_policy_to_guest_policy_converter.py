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
"""Converter related function for Ops Agents Policy."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import collections
import textwrap

from googlecloudsdk.api_lib.compute.instances.ops_agents import ops_agents_policy as agent_policy


class _PackageTemplates(
    collections.namedtuple(
        '_PackageTemplates',
        ('repo', 'clear_prev_repo'))):
  pass


class _AgentRuleTemplates(
    collections.namedtuple(
        '_AgentRuleTemplates',
        ('install_with_version', 'yum_package', 'apt_package',
         'zypper_package', 'goo_package', 'run_agent', 'win_run_agent',
         'repo_id', 'display_name', 'recipe_name', 'current_major_version'))):
  pass

_EMPTY_SOFTWARE_RECIPE_SCRIPT = textwrap.dedent("""\
    #!/bin/bash
    echo 'Skipping as the package state is [removed].'""")
_AGENT_RULE_TEMPLATES = {
    'logging':
        _AgentRuleTemplates(
            install_with_version=(
                'curl -sSO https://dl.google.com/cloudagents/add-logging-agent-repo.sh && '
                'sudo bash add-logging-agent-repo.sh --also-install --version=%s'
                ),
            yum_package=_PackageTemplates(
                repo='google-cloud-logging-el%s-x86_64-%s',
                clear_prev_repo=(
                    'sudo rm /etc/yum.repos.d/google-cloud-logging.repo || '
                    "true; find /var/cache/{yum,dnf} -name '*google-cloud-logging*' "
                    '| xargs sudo rm -rf || true'),
            ),
            zypper_package=_PackageTemplates(
                repo='google-cloud-logging-sles%s-x86_64-%s',
                clear_prev_repo=(
                    'sudo rm /etc/zypp/repos.d/google-cloud-logging.repo || '
                    "true; find /var/cache/zypp -name '*google-cloud-logging*' "
                    '| xargs sudo rm -rf || true'),
            ),
            apt_package=_PackageTemplates(
                repo='google-cloud-logging-%s-%s',
                clear_prev_repo=(
                    'sudo rm /etc/apt/sources.list.d/google-cloud-logging.list '
                    '|| true; find /var/cache/apt -name '
                    "'*google-fluentd*' | xargs sudo rm -rf || true"),
            ),
            goo_package=None,
            repo_id='google-cloud-logging',
            display_name='Google Cloud Logging Agent Repository',
            run_agent=textwrap.dedent("""\
                    #!/bin/bash -e
                    %(clear_prev_repo)s
                    for i in {1..5}; do
                      if (%(install)s); then
                        sudo service google-fluentd start
                        break
                      fi
                      sleep 1m
                    done"""),
            win_run_agent=None,
            recipe_name='set-google-fluentd-version',
            current_major_version='1.*.*',
        ),
    'metrics':
        _AgentRuleTemplates(
            install_with_version=(
                'curl -sSO https://dl.google.com/cloudagents/add-monitoring-agent-repo.sh && '
                'sudo bash add-monitoring-agent-repo.sh --also-install --version=%s'
                ),
            yum_package=_PackageTemplates(
                repo='google-cloud-monitoring-el%s-x86_64-%s',
                clear_prev_repo=(
                    'sudo rm /etc/yum.repos.d/google-cloud-monitoring.repo || '
                    'true; find /var/cache/{yum,dnf} -name '
                    "'*google-cloud-monitoring*' | xargs sudo rm -rf || true"),
            ),
            zypper_package=_PackageTemplates(
                repo='google-cloud-monitoring-sles%s-x86_64-%s',
                clear_prev_repo=(
                    'sudo rm /etc/zypp/repos.d/google-cloud-monitoring.repo || '
                    'true; find /var/cache/zypp -name '
                    "'*google-cloud-monitoring*' | xargs sudo rm -rf || true"),
            ),
            apt_package=_PackageTemplates(
                repo='google-cloud-monitoring-%s-%s',
                clear_prev_repo=(
                    'sudo rm '
                    '/etc/apt/sources.list.d/google-cloud-monitoring.list || '
                    'true; find /var/cache/apt -name '
                    "'*stackdriver-agent*' | xargs sudo rm -rf || true"),
            ),
            goo_package=None,
            repo_id='google-cloud-monitoring',
            display_name='Google Cloud Monitoring Agent Repository',
            run_agent=textwrap.dedent("""\
                    #!/bin/bash -e
                    %(clear_prev_repo)s
                    for i in {1..5}; do
                      if (%(install)s); then
                        sudo service stackdriver-agent start
                        break
                      fi
                      sleep 1m
                    done"""),
            win_run_agent=None,
            recipe_name='set-stackdriver-agent-version',
            current_major_version='6.*.*',
        ),
    'ops-agent':
        _AgentRuleTemplates(
            install_with_version=(
                'curl -sSO https://dl.google.com/cloudagents/add-google-cloud-ops-agent-repo.sh && '
                'sudo bash add-google-cloud-ops-agent-repo.sh --also-install --version=%s'
                ),
            yum_package=_PackageTemplates(
                repo='google-cloud-ops-agent-el%s-x86_64-%s',
                clear_prev_repo=(
                    'sudo rm /etc/yum.repos.d/google-cloud-ops-agent.repo || '
                    'true; find /var/cache/{yum,dnf} -name '
                    "'*google-cloud-ops-agent*' | xargs sudo rm -rf || true"),
            ),
            zypper_package=_PackageTemplates(
                repo='google-cloud-ops-agent-sles%s-x86_64-%s',
                clear_prev_repo=(
                    'sudo rm /etc/zypp/repos.d/google-cloud-ops-agent.repo || '
                    'true; find /var/cache/zypp -name '
                    "'*google-cloud-ops-agent*' | xargs sudo rm -rf || true"),
            ),
            apt_package=_PackageTemplates(
                repo='google-cloud-ops-agent-%s-%s',
                clear_prev_repo=(
                    'sudo rm '
                    '/etc/apt/sources.list.d/google-cloud-ops-agent.list || '
                    'true; find /var/cache/apt -name '
                    "'*google-cloud-ops-agent*' | xargs sudo rm -rf || true"),
            ),
            goo_package=_PackageTemplates(
                repo='google-cloud-ops-agent-%s-%s',
                clear_prev_repo=None,
            ),
            repo_id='google-cloud-ops-agent',
            display_name='Google Cloud Ops Agent Repository',
            run_agent=textwrap.dedent("""\
                    #!/bin/bash -e
                    %(clear_prev_repo)s
                    for i in {1..5}; do
                      if (%(install)s); then
                        sudo systemctl start google-cloud-ops-agent.target || sudo service google-cloud-ops-agent restart
                        break
                      fi
                      sleep 1m
                    done"""),
            win_run_agent=textwrap.dedent("""\
            $Stoploop = $false
            [int]$Retrycount = "0"

            do {
                googet --noconfirm remove google-cloud-ops-agent
                Start-Sleep -Seconds 10
                googet --noconfirm install google-cloud-ops-agent%s
                if ( $? ) {
                    $Stoploop = $true
                }
                else {
                    Write-Output "Installing ops-agent failes, retrying..."
                    if ($Retrycount -gt 3) {
                        Write-Output "Retried 3 times already, failing..."
                        $Stoploop = $true
                    }
                    else {
                        Start-Sleep -Seconds 3
                        $Retrycount = $Retrycount + 1
                    }
                }
            }
            while ($Stoploop -eq $false)"""),
            recipe_name='set-ops-agent-version',
            current_major_version='2.*.*',
        ),
}

_APT_CODENAMES = {
    '8': 'jessie',
    '9': 'stretch',
    '10': 'buster',
    '11': 'bullseye',
    '12': 'bookworm',
    '16.04': 'xenial',
    '18.04': 'bionic',
    '19.10': 'eoan',
    '20.04': 'focal',
    '21.04': 'hirsute',
    '21.10': 'impish',
    '22.04': 'jammy',
    '23.04': 'lunar',
    '23.10': 'mantic',
}

_SUSE_OS = ('sles-sap', 'sles')

_YUM_OS = ('centos', 'rhel', 'rocky')

_APT_OS = ('debian', 'ubuntu')

_WINDOWS_OS = ('windows')


def _CreatePackages(messages, agent_rules, os_type):
  """Create OS Agent guest policy packages from Ops Agent policy agent field."""
  packages = []
  for agent_rule in agent_rules or []:
    if agent_rule.type is agent_policy.OpsAgentPolicy.AgentRule.Type.LOGGING:
      packages.append(
          _CreatePackage(messages, 'google-fluentd', agent_rule.package_state,
                         agent_rule.enable_autoupgrade))
      packages.append(
          _CreatePackage(messages, 'google-fluentd-catch-all-config',
                         agent_rule.package_state,
                         agent_rule.enable_autoupgrade))
      # apt os will start the service automatically without the start-service.
      if os_type.short_name not in _APT_OS:
        packages.append(
            _CreatePackage(messages, 'google-fluentd-start-service',
                           agent_rule.package_state,
                           agent_rule.enable_autoupgrade))

    if agent_rule.type is agent_policy.OpsAgentPolicy.AgentRule.Type.METRICS:
      packages.append(
          _CreatePackage(messages, 'stackdriver-agent',
                         agent_rule.package_state,
                         agent_rule.enable_autoupgrade))
      # apt os will start the service automatically without the start-service.
      if os_type.short_name not in _APT_OS:
        packages.append(
            _CreatePackage(messages, 'stackdriver-agent-start-service',
                           agent_rule.package_state,
                           agent_rule.enable_autoupgrade))

    if agent_rule.type is agent_policy.OpsAgentPolicy.AgentRule.Type.OPS_AGENT:
      packages.append(
          _CreatePackage(messages, 'google-cloud-ops-agent',
                         agent_rule.package_state,
                         agent_rule.enable_autoupgrade))
  return packages


def _CreatePackage(messages, package_name, package_state, enable_autoupgrade):
  """Creates package in guest policy.

  Args:
    messages: os config guest policy API messages.
    package_name: package name.
    package_state: package states.
    enable_autoupgrade: True or False.

  Returns:
    package in guest policy.
  """
  states = messages.Package.DesiredStateValueValuesEnum
  desired_state = None
  if (package_state
      is agent_policy.OpsAgentPolicy.AgentRule.PackageState.INSTALLED):
    if enable_autoupgrade:
      desired_state = states.UPDATED
    else:
      desired_state = states.INSTALLED
  elif (package_state
        is agent_policy.OpsAgentPolicy.AgentRule.PackageState.REMOVED):
    desired_state = states.REMOVED
  return messages.Package(name=package_name, desiredState=desired_state)


def _CreatePackageRepositories(messages, os_type, agent_rules):
  """Create package repositories in guest policy.

  Args:
    messages: os config guest policy api messages.
    os_type: it contains os_version, os_shortname.
    agent_rules: list of agent rules which contains version, package_state, type
      of {logging,metrics}.

  Returns:
    package repos in guest policy.
  """
  package_repos = None
  if os_type.short_name in _APT_OS:
    package_repos = _CreateAptPkgRepos(
        messages, _APT_CODENAMES.get(os_type.version), agent_rules)
  elif os_type.short_name in _YUM_OS:
    version = os_type.version.split('.')[0]
    version = version.split('*')[0]
    package_repos = _CreateYumPkgRepos(messages, version, agent_rules)
  elif os_type.short_name in _SUSE_OS:
    version = os_type.version.split('.')[0]
    version = version.split('*')[0]
    package_repos = _CreateZypperPkgRepos(messages, version, agent_rules)
  elif os_type.short_name in _WINDOWS_OS:
    package_repos = _CreateGooPkgRepos(messages, 'windows', agent_rules)
  return package_repos


def _GetRepoSuffix(version):
  return version.replace('.*.*', '') if '.*.*' in version else 'all'


def _CreateGooPkgRepos(messages, repo_distro, agent_rules):
  goo_pkg_repos = []
  for agent_rule in agent_rules:
    template = _AGENT_RULE_TEMPLATES[agent_rule.type]
    repo_name = template.goo_package.repo % (repo_distro,
                                             _GetRepoSuffix(agent_rule.version))
    goo_pkg_repos.append(_CreateGooPkgRepo(messages, repo_name))
  return goo_pkg_repos


def _CreateGooPkgRepo(messages, repo_id):
  """Create a goo repo in guest policy.

  Args:
    messages: os config guest policy api messages.
    repo_id: 'google-cloud-ops-agent-windows-[all|1]'.

  Returns:
    zoo repos in guest policy.
  """
  return messages.PackageRepository(
      goo=messages.GooRepository(
          name=repo_id,
          url='https://packages.cloud.google.com/yuck/repos/%s' % repo_id))


def _CreateZypperPkgRepos(messages, repo_distro, agent_rules):
  zypper_pkg_repos = []
  for agent_rule in agent_rules:
    template = _AGENT_RULE_TEMPLATES[agent_rule.type]
    repo_name = template.zypper_package.repo % (
        repo_distro, _GetRepoSuffix(agent_rule.version))
    zypper_pkg_repos.append(
        _CreateZypperPkgRepo(messages, template.repo_id, template.display_name,
                             repo_name))
  return zypper_pkg_repos


def _CreateZypperPkgRepo(messages, repo_id, display_name, repo_name):
  """Create a zypper repo in guest policy.

  Args:
    messages: os config guest policy api messages.
    repo_id: 'google-cloud-logging' or 'google-cloud-monitoring'.
    display_name: 'Google Cloud Logging Agent Repository' or 'Google Cloud
      Monitoring Agent Repository'.
    repo_name: repository name.

  Returns:
    zypper repos in guest policy.
  """
  return messages.PackageRepository(
      zypper=messages.ZypperRepository(
          id=repo_id,
          displayName=display_name,
          baseUrl='https://packages.cloud.google.com/yum/repos/%s' % repo_name,
          gpgKeys=[
              'https://packages.cloud.google.com/yum/doc/yum-key.gpg',
              'https://packages.cloud.google.com/yum/doc/rpm-package-key.gpg'
          ]))


def _CreateYumPkgRepos(messages, repo_distro, agent_rules):
  yum_pkg_repos = []
  for agent_rule in agent_rules:
    template = _AGENT_RULE_TEMPLATES[agent_rule.type]
    repo_name = template.yum_package.repo % (
        repo_distro, _GetRepoSuffix(agent_rule.version))
    yum_pkg_repos.append(
        _CreateYumPkgRepo(messages, template.repo_id, template.display_name,
                          repo_name))
  return yum_pkg_repos


def _CreateYumPkgRepo(messages, repo_id, display_name, repo_name):
  """Create a yum repo in guest policy.

  Args:
    messages: os config guest policy api messages.
    repo_id: 'google-cloud-logging' or 'google-cloud-monitoring'.
    display_name: 'Google Cloud Logging Agent Repository' or 'Google Cloud
      Monitoring Agent Repository'.
    repo_name: repository name.

  Returns:
    yum repos in guest policy.
  """
  return messages.PackageRepository(
      yum=messages.YumRepository(
          id=repo_id,
          displayName=display_name,
          baseUrl='https://packages.cloud.google.com/yum/repos/%s' % repo_name,
          gpgKeys=[
              'https://packages.cloud.google.com/yum/doc/yum-key.gpg',
              'https://packages.cloud.google.com/yum/doc/rpm-package-key.gpg'
          ]))


def _CreateAptPkgRepos(messages, repo_distro, agent_rules):
  apt_pkg_repos = []
  for agent_rule in agent_rules or []:
    template = _AGENT_RULE_TEMPLATES[agent_rule.type]
    repo_name = template.apt_package.repo % (
        repo_distro, _GetRepoSuffix(agent_rule.version))
    apt_pkg_repos.append(_CreateAptPkgRepo(messages, repo_name))
  return apt_pkg_repos


def _CreateAptPkgRepo(messages, repo_name):
  """Create an apt repo in guest policy.

  Args:
    messages: os config guest policy api messages.
    repo_name: repository name.

  Returns:
    An apt repo in guest policy.
  """
  return messages.PackageRepository(
      apt=messages.AptRepository(
          uri='http://packages.cloud.google.com/apt',
          distribution=repo_name,
          components=['main'],
          gpgKey='https://packages.cloud.google.com/apt/doc/apt-key.gpg'))


def _CreateOstypes(messages, assignment_os_types):
  os_types = []
  for assignment_os_type in assignment_os_types or []:
    os_type = messages.AssignmentOsType(
        osShortName=assignment_os_type.short_name,
        osVersion=assignment_os_type.version)
    os_types.append(os_type)
  return os_types


def _CreateGroupLabel(messages, assignment_group_labels):
  """Create guest policy group labels.

  Args:
    messages: os config guest policy api messages.
    assignment_group_labels: List of dict of key: value pair.

  Returns:
    group_labels in guest policy.
  """
  group_labels = []
  for group_label in assignment_group_labels or []:
    pairs = [
        messages.AssignmentGroupLabel.LabelsValue.AdditionalProperty(
            key=key, value=value) for key, value in group_label.items()
    ]
    group_labels.append(
        messages.AssignmentGroupLabel(
            labels=messages.AssignmentGroupLabel.LabelsValue(
                additionalProperties=pairs)))
  return group_labels


def _CreateAssignment(messages, assignment_group_labels, assignment_os_types,
                      assignment_zones, assignment_instances):
  """Creates a Assignment message from its components."""
  return messages.Assignment(
      groupLabels=_CreateGroupLabel(messages, assignment_group_labels),
      zones=assignment_zones or [],
      instances=assignment_instances or [],
      osTypes=_CreateOstypes(messages, assignment_os_types))


def _GetRecipeVersion(prev_recipes, recipe_name):
  for recipe in prev_recipes or []:
    if recipe.name.startswith(recipe_name):
      return str(int(recipe.version)+1)
  return '0'


def _CreateRecipes(messages, agent_rules, os_type, prev_recipes):
  """Create recipes in guest policy.

  Args:
    messages: os config guest policy api messages.
    agent_rules: ops agent policy agent rules.
    os_type: ops agent policy os_type.
    prev_recipes: a list of original SoftwareRecipe.

  Returns:
    Recipes in guest policy
  """
  recipes = []
  for agent_rule in agent_rules or []:
    recipes.append(_CreateRecipe(messages, agent_rule, os_type, prev_recipes))
  return recipes


def _CreateRecipe(messages, agent_rule, os_type, prev_recipes):
  """Create a recipe for one agent rule in guest policy.

  Args:
    messages: os config guest policy api messages.
    agent_rule: ops agent policy agent rule.
    os_type: ops agent policy os type.
    prev_recipes: a list of original SoftwareRecipe.


  Returns:
    One software recipe in guest policy. If the package state is "removed", this
    software recipe has an empty run script. We still keep the software recipe
    to maintain versioning of the software recipe as the policy gets updated.
  """
  version = _GetRecipeVersion(
      prev_recipes, _AGENT_RULE_TEMPLATES[agent_rule.type].recipe_name)
  return messages.SoftwareRecipe(
      desiredState=messages.SoftwareRecipe.DesiredStateValueValuesEnum.UPDATED,
      installSteps=[_CreateStepInScript(messages, agent_rule, os_type)],
      name='%s-%s' % (
          _AGENT_RULE_TEMPLATES[agent_rule.type].recipe_name, version),
      version=version)


def _CreateStepInScript(messages, agent_rule, os_type):
  """Create scriptRun step in guest policy recipe section.

  Args:
    messages: os config guest policy api messages.
    agent_rule: logging or metrics agent rule.
    os_type: it contains os_version, os_short_name.

  Returns:
    Step of script to be run in Recipe section. If the package state is
    "removed", this run script is empty. We still keep the software recipe to
    maintain versioning of the software recipe as the policy gets updated.
  """
  step = messages.SoftwareRecipeStep()
  step.scriptRun = messages.SoftwareRecipeStepRunScript()
  agent_version = '' if agent_rule.version == 'latest' else agent_rule.version
  if os_type.short_name in _YUM_OS:
    clear_prev_repo = _AGENT_RULE_TEMPLATES[
        agent_rule.type].yum_package.clear_prev_repo
    install_with_version = _AGENT_RULE_TEMPLATES[
        agent_rule.type].install_with_version % agent_version
  if os_type.short_name in _APT_OS:

    clear_prev_repo = _AGENT_RULE_TEMPLATES[
        agent_rule.type].apt_package.clear_prev_repo
    install_with_version = _AGENT_RULE_TEMPLATES[
        agent_rule.type].install_with_version % agent_version
  if os_type.short_name in _SUSE_OS:
    clear_prev_repo = _AGENT_RULE_TEMPLATES[
        agent_rule.type].zypper_package.clear_prev_repo
    install_with_version = _AGENT_RULE_TEMPLATES[
        agent_rule.type].install_with_version % agent_version
  if os_type.short_name in _WINDOWS_OS:
    if agent_rule.version == 'latest' or '*.*' in agent_rule.version:
      agent_version = ''
    else:
      agent_version = '.x86_64.%s@1' % agent_rule.version

  # PackageState is REMOVED.
  if (agent_rule.package_state
      == agent_policy.OpsAgentPolicy.AgentRule.PackageState.REMOVED):
    step.scriptRun.script = _EMPTY_SOFTWARE_RECIPE_SCRIPT
  # PackageState is INSTALLED or UPDATED for Windows.
  elif os_type.short_name in _WINDOWS_OS:
    step.scriptRun.interpreter = messages.SoftwareRecipeStepRunScript.InterpreterValueValuesEnum.POWERSHELL
    step.scriptRun.script = _AGENT_RULE_TEMPLATES[
        agent_rule.type].win_run_agent % agent_version
  # PackageState is INSTALLED or UPDATED for Linux.
  else:
    step.scriptRun.script = _AGENT_RULE_TEMPLATES[agent_rule.type].run_agent % {
        'install': install_with_version,
        'clear_prev_repo': clear_prev_repo
    }
  return step


def _CreateDescription(agent_rules, description):
  """Create description in guest policy.

  Args:
    agent_rules: agent rules in ops agent policy.
    description: description in ops agent policy.

  Returns:
    description in guest policy.
  """
  description_template = ('{"type": "ops-agents", "description": "%s", '
                          '"agentRules": [%s]}')

  agent_contents = [agent_rule.ToJson() for agent_rule in agent_rules or []]

  return description_template % (description, ','.join(agent_contents))


def _SetAgentVersion(agent_rules):
  for agent_rule in agent_rules or []:
    if agent_rule.version in {'current-major', None, ''}:
      agent_rule.version = _AGENT_RULE_TEMPLATES[
          agent_rule.type].current_major_version


def ConvertOpsAgentPolicyToGuestPolicy(messages, ops_agents_policy,
                                       prev_recipes=None):
  """Converts Ops Agent policy to OS Config guest policy."""
  ops_agents_policy_assignment = ops_agents_policy.assignment
  _SetAgentVersion(ops_agents_policy.agent_rules)
  # TODO(b/159365920): once os config supports multi repos, remove indexing [0].
  guest_policy = messages.GuestPolicy(
      description=_CreateDescription(ops_agents_policy.agent_rules,
                                     ops_agents_policy.description),
      etag=ops_agents_policy.etag,
      assignment=_CreateAssignment(messages,
                                   ops_agents_policy_assignment.group_labels,
                                   ops_agents_policy_assignment.os_types,
                                   ops_agents_policy_assignment.zones,
                                   ops_agents_policy_assignment.instances),
      packages=_CreatePackages(messages, ops_agents_policy.agent_rules,
                               ops_agents_policy_assignment.os_types[0]),
      packageRepositories=_CreatePackageRepositories(
          messages, ops_agents_policy_assignment.os_types[0],
          ops_agents_policy.agent_rules),
      recipes=_CreateRecipes(messages, ops_agents_policy.agent_rules,
                             ops_agents_policy.assignment.os_types[0],
                             prev_recipes))

  return guest_policy
