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
"""Useful commands for interacting with the Looker Instances API."""


from googlecloudsdk.api_lib.looker import utils


def GetService(release_track):
  """Returns the service for interacting with the Intances service."""
  client = utils.LookerClient(release_track)
  looker_client = client.looker_client
  return looker_client.projects_locations_instances


def ExportInstance(instance_ref, args, release_track):
  """Exports a Looker Instance."""
  messages_module = utils.GetMessagesModule(release_track)
  service = GetService(release_track)

  encryption_config = messages_module.ExportEncryptionConfig(
      kmsKeyName=args.kms_key
  )
  export_instance_request = messages_module.ExportInstanceRequest(
      gcsUri=args.target_gcs_uri, encryptionConfig=encryption_config
  )

  return service.Export(
      messages_module.LookerProjectsLocationsInstancesExportRequest(
          name=instance_ref.RelativeName(),
          exportInstanceRequest=export_instance_request,
      )
  )


def ImportInstance(instance_ref, args, release_track):
  """Imports a Looker Instance."""
  messages_module = utils.GetMessagesModule(release_track)
  service = GetService(release_track)

  import_instance_request = messages_module.ImportInstanceRequest(
      gcsUri=args.source_gcs_uri
  )

  return service.Import(
      messages_module.LookerProjectsLocationsInstancesImportRequest(
          name=instance_ref.RelativeName(),
          importInstanceRequest=import_instance_request,
      )
  )
