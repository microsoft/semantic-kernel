# -*- coding: utf-8 -*- #
# Copyright 2021 Google LLC. All Rights Reserved.
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
"""Create a new external account key."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.publicca import base as publicca_base
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core.util import files


def _ExportExternalAccountKey(external_account_key, key_output_file):
  try:
    files.WriteFileContents(key_output_file, external_account_key)
  except (files.Error, OSError, IOError):
    raise exceptions.BadFileException(
        "Could not write external account key to '{}'.".format(key_output_file))


class Create(base.CreateCommand):
  r"""Create a new external account key.

  ## EXAMPLES

  To create an external account key:

      $ {command}

  To create an external account key and save it to a file:

      $ {command} --key-output-file=./external_account_key.txt
  """

  @staticmethod
  def Args(parser):
    parser.add_argument(
        '--key-output-file',
        help='The path where the generated external account key is written.')

  def Run(self, args):
    api_version = publicca_base.GetVersion(self.ReleaseTrack())
    self.client = publicca_base.GetClientInstance(api_version)
    self.messages = publicca_base.GetMessagesModule(api_version)
    project = properties.VALUES.core.project.Get(required=True)
    request = self.messages.PubliccaProjectsLocationsExternalAccountKeysCreateRequest(
        parent='projects/{}/locations/global'.format(project))

    external_account_key = self.client.projects_locations_externalAccountKeys.Create(
        request)
    key_and_id = ('b64MacKey: {key}\nkeyId: {id}'.format(
        key=external_account_key.b64MacKey.decode('utf-8', 'backslashreplace'),
        id=external_account_key.keyId))
    status_message = 'Created an external account key'
    if args.IsSpecified('key_output_file'):
      status_message += ' and saved it to [{}]'.format(args.key_output_file)
      _ExportExternalAccountKey(key_and_id, args.key_output_file)
    else:
      status_message += '\n[{}]\n'.format(key_and_id)
    log.status.Print(status_message)
    return {
        'b64MacKey':
            external_account_key.b64MacKey.decode('utf-8', 'backslashreplace'),
        'keyId':
            external_account_key.keyId,
    }
