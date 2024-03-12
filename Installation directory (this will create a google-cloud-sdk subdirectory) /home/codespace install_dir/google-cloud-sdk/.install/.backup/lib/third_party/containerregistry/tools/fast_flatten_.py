# Copyright 2017 Google Inc. All Rights Reserved.
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
"""This package flattens image metadata into a single tarball."""

from __future__ import absolute_import

from __future__ import print_function

import argparse
import logging
import tarfile

from containerregistry.client.v2_2 import docker_image as v2_2_image
from containerregistry.tools import logging_setup
from six.moves import zip  # pylint: disable=redefined-builtin

parser = argparse.ArgumentParser(description='Flatten container images.')

# The name of this flag was chosen for compatibility with docker_pusher.py
parser.add_argument(
    '--tarball', action='store', help='An optional legacy base image tarball.')

parser.add_argument(
    '--config',
    action='store',
    help='The path to the file storing the image config.')

parser.add_argument(
    '--digest',
    action='append',
    help='The list of layer digest filenames in order.')

parser.add_argument(
    '--layer',
    action='append',
    help='The list of compressed layer filenames in order.')

parser.add_argument(
    '--uncompressed_layer',
    action='append',
    help='The list of uncompressed layer filenames in order.')

parser.add_argument(
    '--diff_id', action='append', help='The list of diff_ids in order.')

# Output arguments.
parser.add_argument(
    '--filesystem',
    action='store',
    help='The name of where to write the filesystem tarball.')

parser.add_argument(
    '--metadata',
    action='store',
    help=('The name of where to write the container '
          'startup metadata.'))


def main():
  logging_setup.DefineCommandLineArgs(parser)
  args = parser.parse_args()
  logging_setup.Init(args=args)

  # If config is specified, use that.  Otherwise, fall back on reading
  # the config from the tarball.
  if args.config:
    logging.info('Reading config from %r', args.config)
    with open(args.config, 'r') as reader:
      config = reader.read()
  elif args.tarball:
    logging.info('Reading config from tarball %r', args.tarball)
    with v2_2_image.FromTarball(args.tarball) as base:
      config = base.config_file()
  else:
    config = args.config

  layers = list(zip(args.digest or [], args.layer or []))
  uncompressed_layers = list(
      zip(args.diff_id or [], args.uncompressed_layer or []))
  logging.info('Loading v2.2 image From Disk ...')
  with v2_2_image.FromDisk(
      config_file=config,
      layers=layers,
      uncompressed_layers=uncompressed_layers,
      legacy_base=args.tarball) as v2_2_img:
    with tarfile.open(args.filesystem, 'w:', encoding='utf-8') as tar:
      v2_2_image.extract(v2_2_img, tar)

    with open(args.metadata, 'w') as f:
      f.write(v2_2_img.config_file())


if __name__ == '__main__':
  main()
