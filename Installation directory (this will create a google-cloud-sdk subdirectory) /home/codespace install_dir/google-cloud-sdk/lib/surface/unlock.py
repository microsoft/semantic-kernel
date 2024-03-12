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

"""Unlock secrets and surprises coming soon to Google Cloud."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os
import shutil
import sys

from googlecloudsdk.calliope import base
from googlecloudsdk.core.util import encoding
import requests

_UNLOCK_URL = "https://gcloud-unlock-api-gsaaz6raqa-uc.a.run.app/api/unlock/"


class SurpriseError(Exception):
  pass


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.GA)
class EnableAlpha(base.SilentCommand):
  """Unlock secrets and surprises coming soon to Google Cloud."""

  @staticmethod
  def Args(parser):
    parser.add_argument("SURPRISE", help="ID of the surprise to be unlocked.")

  def Run(self, args):
    istty = sys.stdout.isatty()

    size = shutil.get_terminal_size(fallback=(80, 25))
    width, height = size.columns, size.lines
    terminal_type = encoding.GetEncodedValue(os.environ, "TERM", "unknown")

    unlock_request = {
        "args": [args.SURPRISE],  # No command arguments to pass
        "options": {},  # No command options to pass
        "terminfo": {
            "istty": istty,
            "width": width,
            "height": height,
            "term": terminal_type,
        },
    }

    try:
      response = requests.post(_UNLOCK_URL, json=unlock_request)
      response.raise_for_status()

      # Assuming the response's content is JSON and has a 'content' field
      response_content = response.json().get("content", "")
      print(response_content)

    except requests.exceptions.HTTPError as http_err:
      raise SurpriseError("{http_err}".format(http_err=http_err))
