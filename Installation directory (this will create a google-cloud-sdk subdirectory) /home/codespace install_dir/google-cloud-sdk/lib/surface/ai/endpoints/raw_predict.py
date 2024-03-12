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
"""Vertex AI endpoints raw-predict command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import json
import sys

from googlecloudsdk.api_lib.ai.endpoints import client
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.ai import constants
from googlecloudsdk.command_lib.ai import endpoint_util
from googlecloudsdk.command_lib.ai import flags
from googlecloudsdk.command_lib.ai import region_util
from googlecloudsdk.core import exceptions as core_exceptions
from googlecloudsdk.core.console import console_io

import six


def _AddArgs(parser):
  flags.AddEndpointResourceArg(
      parser,
      'to do online raw prediction',
      prompt_func=region_util.PromptForOpRegion)

  flags.GetRawPredictHeadersArg().AddToParser(parser)
  flags.GetRawPredictRequestArg().AddToParser(parser)


def _Run(args, version):
  """Run Vertex AI online prediction."""
  endpoint_ref = args.CONCEPTS.endpoint.Parse()
  args.region = endpoint_ref.AsDict()['locationsId']

  with endpoint_util.AiplatformEndpointOverrides(version, region=args.region):
    if args.request.startswith('@'):
      request = console_io.ReadFromFileOrStdin(args.request[1:], binary=True)
    else:
      request = args.request.encode('utf-8')

    endpoints_client = client.EndpointsClient(version=version)
    _, response = endpoints_client.RawPredict(endpoint_ref, args.http_headers,
                                              request)

    # Workaround since gcloud only supports protobufs as JSON objects. Since
    # raw predict can return anything, write raw bytes to stdout.
    if not args.IsSpecified('format'):
      sys.stdout.buffer.write(response)
      return None

    # If user asked for formatting, assume it's a JSON object.
    try:
      return json.loads(response.decode('utf-8'))
    except ValueError:
      raise core_exceptions.Error('No JSON object could be decoded from the '
                                  'HTTP response body:\n' +
                                  six.text_type(response))


@base.ReleaseTracks(base.ReleaseTrack.GA)
class RawPredict(base.Command):
  """Run Vertex AI online raw prediction.

  `{command}` sends a raw prediction request to a Vertex AI endpoint. The
  request can be given on the command line or read from a file or stdin.

  ## EXAMPLES

  To predict against an endpoint ``123'' under project ``example'' in region
  ``us-central1'', reading the request from the command line, run:

    $ {command} 123 --project=example --region=us-central1 --request='{
        "instances": [
          { "values": [1, 2, 3, 4], "key": 1 },
          { "values": [5, 6, 7, 8], "key": 2 }
        ]
      }'

  If the request body was in the file ``input.json'', run:

    $ {command} 123 --project=example --region=us-central1 --request=@input.json

  To send the image file ``image.jpeg'' and set the *content type*, run:

    $ {command} 123 --project=example --region=us-central1
    --http-headers=Content-Type=image/jpeg --request=@image.jpeg
  """

  @staticmethod
  def Args(parser):
    _AddArgs(parser)

  def Run(self, args):
    return _Run(args, constants.GA_VERSION)


@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.ALPHA)
class RawPredictBeta(RawPredict):
  """Run Vertex AI online raw prediction.

  `{command}` sends a raw prediction request to a Vertex AI endpoint. The
  request can be given on the command line or read from a file or stdin.

  ## EXAMPLES

  To predict against an endpoint ``123'' under project ``example'' in region
  ``us-central1'', reading the request from the command line, run:

    $ {command} 123 --project=example --region=us-central1 --request='{
        "instances": [
          { "values": [1, 2, 3, 4], "key": 1 },
          { "values": [5, 6, 7, 8], "key": 2 }
        ]
      }'

  If the request body was in the file ``input.json'', run:

    $ {command} 123 --project=example --region=us-central1 --request=@input.json

  To send the image file ``image.jpeg'' and set the *content type*, run:

    $ {command} 123 --project=example --region=us-central1
    --http-headers=Content-Type=image/jpeg --request=@image.jpeg
  """

  def Run(self, args):
    return _Run(args, constants.BETA_VERSION)
