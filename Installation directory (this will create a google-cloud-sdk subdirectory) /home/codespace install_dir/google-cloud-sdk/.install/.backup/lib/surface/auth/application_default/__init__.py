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

"""Auth for Application Default Credentials."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base


@base.ReleaseTracks(base.ReleaseTrack.GA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.ALPHA)
class ApplicationDefault(base.Group):
  """Manage your active Application Default Credentials.

  Application Default Credentials (ADC) provide a method to get credentials used
  in calling Google APIs. The {command} command group allows you to manage
  active credentials on your machine that are used for local application
  development.

  These credentials are only used by Google client libraries in your own
  application.

  For more information about ADC and how it works, see [Authenticating as a
  service account](https://cloud.google.com/docs/authentication/production).

  ## EXAMPLES

  To use your own user credentials for your application to access an API, run:

    $ {command} login

  This will take you through a web flow to acquire new user credentials.

  To create a service account and have your application use it for API access,
  run:

    $ gcloud iam service-accounts create my-account
    $ gcloud iam service-accounts keys create key.json
      --iam-account=my-account@my-project.iam.gserviceaccount.com
    $ export GOOGLE_APPLICATION_CREDENTIALS=key.json
    $ ./my_application.sh
  """
