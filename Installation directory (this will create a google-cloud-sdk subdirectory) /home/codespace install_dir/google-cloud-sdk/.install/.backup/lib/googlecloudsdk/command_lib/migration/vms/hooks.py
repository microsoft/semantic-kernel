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
"""Argument processors for migration vms surface arguments."""

from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.core import properties


# Helper Functions
def _GetMessageClass(msg_type_name):
  """Gets API message object for given message type name."""
  msg = apis.GetMessagesModule('vmmigration', 'v1')
  return getattr(msg, msg_type_name)


# Argument Processors
def GetDataDiskImageImportTransform(value):
  """Returns empty DataDiskImageImport entry."""
  del value
  data_disk_image_import = _GetMessageClass('DataDiskImageImport')
  return data_disk_image_import()


def GetEncryptionTransform(value):
  """Returns empty Encryption entry."""
  del value
  encryption = _GetMessageClass('Encryption')
  return encryption()


def SetLocationAsGlobal():
  """Set default location to global."""
  return 'global'


# Modify Request Hook
def FixCreateImageImportRequest(ref, args, req):
  """Fixes the Create Image Import request."""
  if not (args.generalize or args.license_type):
    req.imageImport.diskImageTargetDefaults.osAdaptationParameters = None

  if not args.image_name:
    req.imageImport.diskImageTargetDefaults.imageName = ref.Name()

  if args.kms_key:
    req.imageImport.diskImageTargetDefaults.encryption = (
        GetEncryptionTransform(
            req.imageImport.diskImageTargetDefaults.encryption
            )
        )
    req.imageImport.diskImageTargetDefaults.encryption.kmsKey = args.kms_key

    req.imageImport.encryption = (
        GetEncryptionTransform(req.imageImport.encryption)
        )
    req.imageImport.encryption.kmsKey = args.kms_key

  if not args.target_project:
    # Handle default target project being the host project.
    target = args.project or properties.VALUES.core.project.Get(required=True)
    req.imageImport.diskImageTargetDefaults.targetProject = (
        ref.Parent().Parent().RelativeName() +
        '/locations/global/targetProjects/' + target
    )
  elif '/' not in args.target_project:
    # Handle prepending path to target project short-name.
    req.imageImport.diskImageTargetDefaults.targetProject = (
        ref.Parent().Parent().RelativeName() +
        '/locations/global/targetProjects/' + args.target_project
    )

  return req
