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
"""The command group for Migrate to Virtual Machines service."""

from googlecloudsdk.calliope import base


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Vms(base.Group):
  """Provides Migrate to Virtual Machines (VM migration) service functionality.

  The gcloud alpha migration vms command group provides the CLI for
  the Migrate to Virtual Machines API.
  Google Cloud Migrate to Virtual Machines migrates VMs from on-premises data
  center and other cloud providers to Google Compute Engine virtual machine (VM)
  instances.
  VM Migration API must be enabled in your project.
  """
