# -*- coding: utf-8 -*- #
# Copyright 2022 Google LLC. All Rights Reserved.
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
"""gcloud endpoint override supplementary help."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base


# NOTE: If the name of this topic is modified, please make sure to update all
# references to it in error messages and other help messages as there are no
# tests to catch such changes.
class EndpointOverride(base.TopicCommand):
  r"""gcloud endpoint override supplementary help.

  Use API endpoint overrides to override the API endpoints used by the `gcloud`
  CLI. Applications such as Private Google Access and Private Service Connect
  use API endpoint overrides.

  # Setting API endpoint overrides

  `gcloud` API endpoints are defined as `gcloud` CLI properties and can be
  overridden through `gcloud` CLI properties or environment variables. For
  example, to override the API endpoint for the `gcloud storage` command to use
  the private `storage-vialink1.p.googleapis.com` endpoint, you can use one of
  the following commands:

    # Override using a property:
    $ gcloud config set api_endpoint_overrides/storage
    storage-vialink1.p.googleapis.com

    # Override using an environment variable
    $ CLOUDSDK_API_ENDPOINT_OVERRIDES_STORAGE=storage-vialink1.p.googleapis.com
    gcloud storage objects list gs://my-bucket

  # Default API endpoints

  To get the default value for an API endpoint override, use `gcloud config get`
  to determine the correct format for your API endpoint override:

    $ gcloud config get api_endpoint_overrides/storage

  # Unsetting API endpoint overrides

  To unset an API endpoint override, use `gcloud config unset`:

    $ gcloud config unset api_endpoint_overrides/storage

  # Configured API endpoint overrides

  To see the APIs which have an endpoint override set, use `gcloud config list`:

    $ gcloud config list api_endpoint_overrides/

  To see all the set and unset API endpoint override properties, use the `--all`
  flag:

    $ gcloud config list api_endpoint_overrides/ --all
  """
