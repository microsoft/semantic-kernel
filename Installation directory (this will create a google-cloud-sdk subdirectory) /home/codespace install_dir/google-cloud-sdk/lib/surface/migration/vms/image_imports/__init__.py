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
"""The command group for Image Imports."""

from googlecloudsdk.calliope import base


# We could have multiple tracks here, e.g.
#   @base.ReleaseTracks(base.ReleaseTrack.GA, base.ReleaseTrack.ALPHA)
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class ImageImports(base.Group):
  r"""Imports images to Google Compute Engine from Google Cloud Storage.

  gcloud alpha migration vms image-imports provides a more robust and better
  supported method for importing images to Google Compute Engine.
  Other image-related operations (for example, list) can be done using
  gcloud compute images, as usual.

  The commands use VM Migartion API which supports importing of an image from
  a Google Cloud Storage file (gs://...) to a target project.
  VM Migration API must be enabled in your project.

  gcloud alpha migration vms image-imports create creates an Image Import resource
  with a nested Image Import Job resource. The Image Import Job resource tracks
  the image import progress. After the Image Import Job completes, successfully
  or otherwise, there's no further use for the Image Import resource.

  The image is imported to a Google Cloud Project, desginated by the
  Target Project resource. To get a list of Target Projects, run the
  gcloud alpha migration vms target-projects list command.
  Use the Google Cloud console to add target project resources.
  For information on adding target projects, see
  https://cloud.google.com/migrate/virtual-machines/docs/5.0/how-to/target-project.

  A project can support a maximum of 1000 Image Import resources per project.
  Hence it's recommended to delete an Image Import resource after the Image
  Import Job is complete to avoid reaching the Image Import resources limit.
  Deletion of Image Import resource does not affect the imported image.

  ## Import Image
  $ gcloud alpha migration vms image-imports create IMAGE_IMPORT_NAME \
    --source-file=GCS_FILE_NAME \
    --image-name=IMPORTED_IMAGE_NAME \
    --location=REGION \
    --target-project=TARGET_PROJECT_RESOURCE_PATH

  ## Delete Image Import resource
  $ gcloud alpha migration vms image-imports delete IMAGE_IMPORT_NAME \
    --location=REGION
  """
