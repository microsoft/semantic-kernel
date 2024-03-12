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
"""Command group for Looker backups."""


from googlecloudsdk.calliope import base

@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Backups(base.Group):
  """Manage Looker instances.

  ## EXAMPLES

  To create a backup of an instance with the name `my-looker-instance`, run:

    $ {command} create --instance='my-looker-instance'

  To delete a backup with the name `looker-backup` that is a backup of an
  instance instance with the name `my-looker-instance`, run:

    $ {command} delete looker-backup --instance=my-looker-instance

  To display the details for a backup with the name `looker-backup` that is a
  backup of an instance instance with the name `my-looker-instance`, run:

    $ {command} describe looker-backup --instance=my-looker-instance

  To list all backups of an instance instance with the name
  `my-looker-instance`, run:

    $ {command} list --instance=my-looker-instance

  """
  pass
