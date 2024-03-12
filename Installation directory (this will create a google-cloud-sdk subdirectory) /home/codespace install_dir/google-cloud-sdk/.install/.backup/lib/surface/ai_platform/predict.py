# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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
"""ai-platform predict command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.ml_engine import predict
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.ml_engine import endpoint_util
from googlecloudsdk.command_lib.ml_engine import flags
from googlecloudsdk.command_lib.ml_engine import predict_utilities
from googlecloudsdk.command_lib.ml_engine import region_util
from googlecloudsdk.core import log

INPUT_INSTANCES_LIMIT = 100


def _AddPredictArgs(parser):
  """Register flags for this command."""
  parser.add_argument('--model', required=True, help='Name of the model.')
  parser.add_argument(
      '--version',
      help="""\
Model version to be used.

If unspecified, the default version of the model will be used. To list model
versions run

  $ {parent_command} versions list
""")
  group = parser.add_mutually_exclusive_group(required=True)
  group.add_argument(
      '--json-request',
      help="""\
      Path to a local file containing the body of JSON request.

      An example of a JSON request:

          {
            "instances": [
              {"x": [1, 2], "y": [3, 4]},
              {"x": [-1, -2], "y": [-3, -4]}
            ]
          }

      This flag accepts "-" for stdin.
      """)
  group.add_argument(
      '--json-instances',
      help="""\
      Path to a local file from which instances are read.
      Instances are in JSON format; newline delimited.

      An example of the JSON instances file:

          {"images": [0.0, ..., 0.1], "key": 3}
          {"images": [0.0, ..., 0.1], "key": 2}
          ...

      This flag accepts "-" for stdin.
      """)
  group.add_argument(
      '--text-instances',
      help="""\
      Path to a local file from which instances are read.
      Instances are in UTF-8 encoded text format; newline delimited.

      An example of the text instances file:

          107,4.9,2.5,4.5,1.7
          100,5.7,2.8,4.1,1.3
          ...

      This flag accepts "-" for stdin.
      """)

  flags.GetRegionArg(include_global=True).AddToParser(parser)
  flags.SIGNATURE_NAME.AddToParser(parser)


def _Run(args):
  """This is what gets called when the user runs this command.

  Args:
    args: an argparse namespace. All the arguments that were provided to this
      command invocation.

  Returns:
    A json object that contains predictions.
  """
  instances = predict_utilities.ReadInstancesFromArgs(
      args.json_request,
      args.json_instances,
      args.text_instances,
      limit=INPUT_INSTANCES_LIMIT)

  region = region_util.GetRegion(args)
  with endpoint_util.MlEndpointOverrides(region=region):
    model_or_version_ref = predict_utilities.ParseModelOrVersionRef(
        args.model, args.version)
    if (args.signature_name is None and
        predict_utilities.CheckRuntimeVersion(args.model, args.version)):
      log.status.Print(
          'You are running on a runtime version >= 1.8. '
          'If the signature defined in the model is '
          'not serving_default then you must specify it via '
          '--signature-name flag, otherwise the command may fail.')
    results = predict.Predict(
        model_or_version_ref, instances, signature_name=args.signature_name)

  if not args.IsSpecified('format'):
    # default format is based on the response.
    args.format = predict_utilities.GetDefaultFormat(
        results.get('predictions'))

  return results


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Predict(base.Command):
  """Run AI Platform online prediction.

     `{command}` sends a prediction request to AI Platform for the given
     instances. This command will read up to 100 instances, though the service
     itself will accept instances up to the payload limit size (currently,
     1.5MB). If you are predicting on more instances, you should use batch
     prediction via

         $ {parent_command} jobs submit prediction.
  """

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    _AddPredictArgs(parser)

  def Run(self, args):
    return _Run(args)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class PredictBeta(base.Command):
  """Run AI Platform online prediction.

     `{command}` sends a prediction request to AI Platform for the given
     instances. This command will read up to 100 instances, though the service
     itself will accept instances up to the payload limit size (currently,
     1.5MB). If you are predicting on more instances, you should use batch
     prediction via

         $ {parent_command} jobs submit prediction.
  """

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    _AddPredictArgs(parser)

  def Run(self, args):
    return _Run(args)
