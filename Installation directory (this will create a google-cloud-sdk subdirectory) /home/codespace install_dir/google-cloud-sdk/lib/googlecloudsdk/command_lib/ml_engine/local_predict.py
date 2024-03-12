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
"""Utilities for running predictions locally.

This module will always be run within a subprocess, and therefore normal
conventions of Cloud SDK do not apply here.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import argparse
import json
import sys


def eprint(*args, **kwargs):
  """Print to stderr."""
  # Print is being over core.log because this is a special case as
  # this is a script called by gcloud.
  print(*args, file=sys.stderr, **kwargs)


VERIFY_TENSORFLOW_VERSION = ('Please verify the installed tensorflow version '
                             'with: "python -c \'import tensorflow; '
                             'print tensorflow.__version__\'".')

VERIFY_SCIKIT_LEARN_VERSION = ('Please verify the installed sklearn version '
                               'with: "python -c \'import sklearn; '
                               'print sklearn.__version__\'".')

VERIFY_XGBOOST_VERSION = ('Please verify the installed xgboost version '
                          'with: "python -c \'import xgboost; '
                          'print xgboost.__version__\'".')


def _verify_tensorflow(version):
  """Check whether TensorFlow is installed at an appropriate version."""
  # Check tensorflow with a recent version is installed.
  try:
    # pylint: disable=g-import-not-at-top
    import tensorflow.compat.v1 as tf
    # pylint: enable=g-import-not-at-top
  except ImportError:
    eprint('Cannot import Tensorflow. Please verify '
           '"python -c \'import tensorflow\'" works.')
    return False
  try:
    if tf.__version__ < version:
      eprint('Tensorflow version must be at least {} .'.format(version),
             VERIFY_TENSORFLOW_VERSION)
      return False
  except (NameError, AttributeError) as e:
    eprint('Error while getting the installed TensorFlow version: ', e,
           '\n', VERIFY_TENSORFLOW_VERSION)
    return False

  return True


def _verify_scikit_learn(version):
  """Check whether scikit-learn is installed at an appropriate version."""
  # Check scikit-learn with a recent version is installed.
  try:
    # pylint: disable=g-import-not-at-top
    import scipy  # pylint: disable=unused-variable
    # pylint: enable=g-import-not-at-top
  except ImportError:
    eprint('Cannot import scipy, which is needed for scikit-learn. Please '
           'verify "python -c \'import scipy\'" works.')
    return False
  try:
    # pylint: disable=g-import-not-at-top
    import sklearn
    # pylint: enable=g-import-not-at-top
  except ImportError:
    eprint('Cannot import sklearn. Please verify '
           '"python -c \'import sklearn\'" works.')
    return False
  try:
    if sklearn.__version__ < version:
      eprint('Scikit-learn version must be at least {} .'.format(version),
             VERIFY_SCIKIT_LEARN_VERSION)
      return False
  except (NameError, AttributeError) as e:
    eprint('Error while getting the installed scikit-learn version: ', e, '\n',
           VERIFY_SCIKIT_LEARN_VERSION)
    return False

  return True


def _verify_xgboost(version):
  """Check whether xgboost is installed at an appropriate version."""
  # Check xgboost with a recent version is installed.
  try:
    # pylint: disable=g-import-not-at-top
    import xgboost
    # pylint: enable=g-import-not-at-top
  except ImportError:
    eprint('Cannot import xgboost. Please verify '
           '"python -c \'import xgboost\'" works.')
    return False
  try:
    if xgboost.__version__ < version:
      eprint('Xgboost version must be at least {} .'.format(version),
             VERIFY_XGBOOST_VERSION)
      return False
  except (NameError, AttributeError) as e:
    eprint('Error while getting the installed xgboost version: ', e, '\n',
           VERIFY_XGBOOST_VERSION)
    return False

  return True


def _verify_ml_libs(framework):
  """Verifies the appropriate ML libs are installed per framework."""
  if framework == 'tensorflow' and not _verify_tensorflow('1.0.0'):
    sys.exit(-1)
  elif framework == 'scikit_learn' and not _verify_scikit_learn('0.18.1'):
    sys.exit(-1)
  elif framework == 'xgboost' and not _verify_xgboost('0.6a2'):
    sys.exit(-1)


def main():
  parser = argparse.ArgumentParser()
  parser.add_argument('--model-dir', required=True, help='Path of the model.')
  parser.add_argument(
      '--framework',
      required=False,
      default=None,
      help=('The ML framework used to train this version of the model. '
            'If not specified, the framework will be identified based on'
            ' the model file name stored in the specified model-dir'))
  parser.add_argument('--signature-name', required=False,
                      help='Tensorflow signature to select input/output map.')
  args, _ = parser.parse_known_args()

  if args.framework is None:
    from cloud.ml.prediction import prediction_utils  # pylint: disable=g-import-not-at-top
    framework = prediction_utils.detect_framework(args.model_dir)
  else:
    framework = args.framework

  if framework:
    _verify_ml_libs(framework)

  # We want to do this *after* we verify ml libs so the user gets a nicer
  # error message.
  # pylint: disable=g-import-not-at-top
  from cloud.ml.prediction import prediction_lib
  # pylint: enable=g-import-not-at-top

  instances = []
  for line in sys.stdin:
    instance = json.loads(line.rstrip('\n'))
    instances.append(instance)

  predictions = prediction_lib.local_predict(
      model_dir=args.model_dir,
      instances=instances,
      framework=framework,
      signature_name=args.signature_name)
  print(json.dumps(predictions))


if __name__ == '__main__':
  main()
