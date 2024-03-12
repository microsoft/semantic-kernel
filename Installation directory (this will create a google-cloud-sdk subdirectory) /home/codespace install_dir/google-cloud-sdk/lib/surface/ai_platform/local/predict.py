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
"""ai-platform local predict command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.ml_engine import flags
from googlecloudsdk.command_lib.ml_engine import local_utils
from googlecloudsdk.command_lib.ml_engine import predict_utilities
from googlecloudsdk.core import log


def _AddLocalPredictArgs(parser):
  """Add arguments for `gcloud ai-platform local predict` command."""
  parser.add_argument('--model-dir', required=True, help='Path to the model.')
  flags.FRAMEWORK_MAPPER.choice_arg.AddToParser(parser)
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
  flags.SIGNATURE_NAME.AddToParser(parser)


class Predict(base.Command):
  """Run prediction locally."""

  @staticmethod
  def Args(parser):
    _AddLocalPredictArgs(parser)

  def Run(self, args):
    framework = flags.FRAMEWORK_MAPPER.GetEnumForChoice(args.framework)
    framework_flag = framework.name.lower() if framework else 'tensorflow'
    if args.signature_name is None:
      log.status.Print('If the signature defined in the model is '
                       'not serving_default then you must specify it via '
                       '--signature-name flag, otherwise the command may fail.')
    results = local_utils.RunPredict(
        args.model_dir,
        json_request=args.json_request,
        json_instances=args.json_instances,
        text_instances=args.text_instances,
        framework=framework_flag,
        signature_name=args.signature_name)
    if not args.IsSpecified('format'):
      # default format is based on the response.
      if isinstance(results, list):
        predictions = results
      else:
        predictions = results.get('predictions')

      args.format = predict_utilities.GetDefaultFormat(predictions)

    return results


_DETAILED_HELP = {
    'DESCRIPTION':
        """\
*{command}* performs prediction locally with the given instances. It requires the
[TensorFlow SDK](https://www.tensorflow.org/install) be installed locally. The
output format mirrors `gcloud ai-platform predict` (online prediction).

You cannot use this command with custom prediction routines.
"""
}


Predict.detailed_help = _DETAILED_HELP
