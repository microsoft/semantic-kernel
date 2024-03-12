# -*- coding: utf-8 -*- #
# Copyright 2021 Google Inc. All Rights Reserved.
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
"""Resource arguments for Backup for GKE commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope.concepts import concepts
from googlecloudsdk.calliope.concepts import deps
from googlecloudsdk.command_lib.util.concepts import concept_parsers
from googlecloudsdk.core import properties

LOCATION_RESOURCE_PARAMETER_ATTRIBUTE = concepts.ResourceParameterAttributeConfig(
    name='location',
    fallthroughs=[
        deps.PropertyFallthrough(
            properties.VALUES.gkebackup.Property('location')),
    ],
    help_text='Google Cloud location.')


def AddBackupArg(parser):
  concept_parsers.ConceptParser.ForResource(
      'backup',
      GetBackupResourceSpec(),
      """
      Name of the backup to create. Once the backup is created, this name can't
      be changed. This must be 63 or fewer characters long and must be unique
      within the project, location, and backup plan. The name may be provided
      either as a relative name, e.g.
      `projects/<project>/locations/<location>/backupPlans/<backupPlan>/backups/<backup>`
      or as a single ID name (with the parent resources provided via options or
      through properties), e.g.
      `BACKUP --project=<project> --location=<location> --backup_plan=<backupPlan>`.
      """,
      required=True).AddToParser(parser)


def GetBackupResourceSpec(resource_name='backup'):
  return concepts.ResourceSpec(
      'gkebackup.projects.locations.backupPlans.backups',
      resource_name=resource_name,
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
      locationsId=LOCATION_RESOURCE_PARAMETER_ATTRIBUTE,
      backupPlansId=concepts.ResourceParameterAttributeConfig(
          name='backup-plan',
          fallthroughs=[
              deps.PropertyFallthrough(
                  properties.VALUES.gkebackup.Property('backup_plan')),
          ],
          help_text='Backup Plan name.'))


def AddRestoreArg(parser):
  concept_parsers.ConceptParser.ForResource(
      'restore',
      GetRestoreResourceSpec(),
      """
      Name of the restore to create. Once the restore is created, this name
      can't be changed. This must be 63 or fewer characters long and must be
      unique within the project and location. The name may be provided either as
      a relative name, e.g.
      `projects/<project>/locations/<location>/restorePlans/<restorePlan>/restores/<restore>`
      or as a single ID name (with the parent resources provided via options or
      through properties), e.g.
      `<restore> --project=<project> --location=<location> --restore-plan=<restorePlan>`.
      """,
      required=True).AddToParser(parser)


def GetRestoreResourceSpec(resource_name='restore'):
  return concepts.ResourceSpec(
      'gkebackup.projects.locations.restorePlans.restores',
      api_version='v1',
      resource_name=resource_name,
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
      locationsId=LOCATION_RESOURCE_PARAMETER_ATTRIBUTE,
      restorePlansId=concepts.ResourceParameterAttributeConfig(
          name='restore-plan',
          fallthroughs=[
              deps.PropertyFallthrough(
                  properties.VALUES.gkebackup.Property('restore_plan')),
          ],
          help_text='Restore Plan name.'))
