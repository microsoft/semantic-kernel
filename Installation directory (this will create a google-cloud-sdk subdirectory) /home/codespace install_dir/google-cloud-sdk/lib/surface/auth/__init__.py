# -*- coding: utf-8 -*- #
# Copyright 2013 Google LLC. All Rights Reserved.
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

"""Auth for the Google Cloud SDK."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base


@base.ReleaseTracks(base.ReleaseTrack.GA,
                    base.ReleaseTrack.BETA,
                    base.ReleaseTrack.ALPHA)
class Auth(base.Group):
  # pylint: disable=line-too-long
  """Manage oauth2 credentials for the Google Cloud CLI.

  The `gcloud auth` command group lets you grant and revoke authorization to
  Google Cloud CLI (`gcloud` CLI) to access Google Cloud. Typically, when
  scripting Google Cloud CLI tools for use on multiple machines, using
  `gcloud auth activate-service-account` is recommended.

  For information about authorization and credential types, see
  [Authorizing the gcloud CLI](https://cloud.google.com/sdk/docs/authorizing).
  For information about authorizing a service account, see
  [Authorizing with a service account](https://cloud.google.com/sdk/docs/authorizing#service-account).

  After running `gcloud auth` commands, you can run other commands with
  `--account`=``ACCOUNT'' to authenticate the command with the credentials
  of the specified account. For information about `--account` and other `gcloud`
  CLI global flags, see the
  [gcloud CLI overview](https://cloud.google.com/sdk/gcloud/reference).

  See `$ gcloud topic client-certificate` to learn how to use Mutual TLS when using gcloud.
  Mutual TLS can be used for [certificate based access](https://cloud.google.com/beyondcorp-enterprise/docs/securing-resources-with-certificate-based-access) with gcloud.

  ## EXAMPLES

  To authenticate a user account with `gcloud` and minimal user output, run:

    $ gcloud auth login --brief

  To list all credentialed accounts and identify the current active account,
  run:

    $ gcloud auth list

  To revoke credentials for a user account (like logging out), run:

    $ gcloud auth revoke test@gmail.com
  """
  # pylint: enable=line-too-long

  category = base.IDENTITY_AND_SECURITY_CATEGORY

  def Filter(self, context, args):
    del context, args
    base.DisableUserProjectQuota()
