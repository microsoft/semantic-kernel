# Copyright 2018 Google Inc. All Rights Reserved.
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
"""This package defines a few functions to add and parse platforms arguments.

These arguments are used to select the image to pull when given a Docker
manifest list.
"""



import argparse

from containerregistry.client.v2_2 import docker_image_list


def AddArguments(parser):
  """Adds command-line arguments for platform fields.

  Args:
    parser: argparser.ArgumentParser object.
  """
  parser.add_argument(
      '--os',
      help=('For multi-platform manifest lists, specifies the operating '
            'system.'))

  parser.add_argument(
      '--os-version',
      help=('For multi-platform manifest lists, specifies the operating system '
            'version.'))

  parser.add_argument(
      '--os-features',
      nargs='*',
      help=('For multi-platform manifest lists, specifies operating system '
            'features.'))

  parser.add_argument(
      '--architecture',
      help=('For multi-platform manifest lists, specifies the CPU '
            'architecture.'))

  parser.add_argument(
      '--variant',
      help='For multi-platform manifest lists, specifies the CPU variant.')

  parser.add_argument(
      '--features',
      nargs='*',
      help='For multi-platform manifest lists, specifies CPU features.')


def FromArgs(args):
  """Populates a docker_image_list.Platform object from the provided args."""
  p = {}

  def _SetField(k, v):
    if v is not None:
      p[k] = v

  _SetField('os', args.os)
  _SetField('os.version', args.os_version)
  _SetField('os.features', args.os_features)
  _SetField('architecture', args.architecture)
  _SetField('variant', args.variant)
  _SetField('features', args.features)

  return docker_image_list.Platform(p)
