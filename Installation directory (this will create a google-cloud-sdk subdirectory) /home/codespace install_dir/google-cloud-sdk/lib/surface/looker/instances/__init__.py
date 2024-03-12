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
"""Command group for Looker instances."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.GA)
class Instances(base.Group):
  """Manage Looker instances.

  ## EXAMPLES

  To create an instance with the name `my-looker-instance`, with an edition of
  "LOOKER_CORE_STANDARD", run:

    $ {command} create my-looker-instance --oauth-client-id='looker'
    --oauth-client-secret='looker' --edition="core-standard" --async

  Note: It is *recommended* that the *--async* argument is provided when
  creating a Looker instance.

  To delete an instance with the name `my-looker-instance`, run:

    $ {command} delete my-looker-instance --async

  To display the details for an instance with name `my-looker-instance`, run:

    $ {command} describe my-looker-instance

  To restart an instance with the name `my-looker-instance`, run:

    $ {command} restart my-looker-instance --async

  To update an instance with the name `my-looker-instance`, run:

    $ {command} update my-looker-instance --async

  To export an instance with the name `my-looker-instance`, run:

    $ {command} export my-looker-instance
    --target-gcs-uri='gs://bucketName/folderName'
    --kms-key='projects/my-project/locations/us-central1/keyRings/my-key-ring/cryptoKeys/my-key'

  To import an instance with the name `my-looker-instance`, run:

    $ {command} import my-looker-instance
    --source-gcs-uri='gs://bucketName/folderName'

  To list all the instances, run:

    $ {command} list
  """

  pass
