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
"""Utilities for the container analysis data model."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import collections

from googlecloudsdk.api_lib.container.images import container_data_util
from googlecloudsdk.api_lib.containeranalysis import requests
import six


_INDENT = '  '
_NULL_SEVERITY = 'UNKNOWN'


class SummaryResolver(object):
  """SummaryResolver is a base class for occurrence summary objects."""

  def resolve(self):
    """resolve is called after all records are added to the summary.

    In this function, aggregate data can be calculated for display.
    """
    pass


class PackageVulnerabilitiesSummary(SummaryResolver):
  """PackageVulnerabilitiesSummary has information about vulnerabilities."""

  def __init__(self):
    self.__messages = requests.GetMessages()
    self.vulnerabilities = collections.defaultdict(list)

  def add_record(self, occ):
    sev = six.text_type(occ.vulnerability.effectiveSeverity)
    self.vulnerabilities[sev].append(occ)

  def resolve(self):
    self.total_vulnerability_found = 0
    self.not_fixed_vulnerability_count = 0

    for occs in self.vulnerabilities.values():
      for occ in occs:
        self.total_vulnerability_found += 1
        for package_issue in occ.vulnerability.packageIssue:
          if (package_issue.fixedVersion.kind ==
              self.__messages.Version.KindValueValuesEnum.MAXIMUM):
            self.not_fixed_vulnerability_count += 1
            break
    # The gcloud encoder gets confused unless we turn this back into a dict.
    self.vulnerabilities = dict(self.vulnerabilities)


class ImageBasesSummary(SummaryResolver):
  """PackageVulnerabilitiesSummary has information about image basis."""

  def __init__(self):
    self.base_images = []

  def add_record(self, occ):
    self.base_images.append(occ)


class BuildsSummary(SummaryResolver):
  """BuildsSummary has information about builds."""

  def __init__(self):
    self.build_details = []

  def add_record(self, occ):
    self.build_details.append(occ)


class DeploymentsSummary(SummaryResolver):
  """DeploymentsSummary has information about deployments."""

  def __init__(self):
    self.deployments = []

  def add_record(self, occ):
    self.deployments.append(occ)


class DiscoverySummary(SummaryResolver):
  """DiscoveryResolver has information about vulnerability discovery."""

  def __init__(self):
    self.discovery = []

  def add_record(self, occ):
    self.discovery.append(occ)


class ContainerAndAnalysisData(container_data_util.ContainerData):
  """Class defining container and analysis data.

  ContainerAndAnalysisData subclasses ContainerData because we want it to
  contain a superset of the attributes, particularly when `--format=json`,
  `format=value(digest)`, etc. is used with `container images describe`.
  """

  def __init__(self, name):
    super(ContainerAndAnalysisData, self).__init__(
        registry=name.registry, repository=name.repository, digest=name.digest)
    self.package_vulnerability_summary = PackageVulnerabilitiesSummary()
    self.image_basis_summary = ImageBasesSummary()
    self.build_details_summary = BuildsSummary()
    self.deployment_summary = DeploymentsSummary()
    self.discovery_summary = DiscoverySummary()

  def add_record(self, occurrence):
    messages = requests.GetMessages()
    if (occurrence.kind == messages.Occurrence.KindValueValuesEnum.VULNERABILITY
       ):
      self.package_vulnerability_summary.add_record(occurrence)
    elif occurrence.kind == messages.Occurrence.KindValueValuesEnum.IMAGE:
      self.image_basis_summary.add_record(occurrence)
    elif occurrence.kind == messages.Occurrence.KindValueValuesEnum.BUILD:
      self.build_details_summary.add_record(occurrence)
    elif (
        occurrence.kind == messages.Occurrence.KindValueValuesEnum.DEPLOYMENT):
      self.deployment_summary.add_record(occurrence)
    elif (occurrence.kind ==
          messages.Occurrence.KindValueValuesEnum.DISCOVERY):
      self.discovery_summary.add_record(occurrence)

  def resolveSummaries(self):
    self.package_vulnerability_summary.resolve()
    self.image_basis_summary.resolve()
    self.build_details_summary.resolve()
    self.deployment_summary.resolve()
    self.discovery_summary.resolve()
