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
"""This package calculates the digest of an image.

The format this tool *expects* to deal with is proprietary.
Image digests aren't stable upon gzip implementation/configuration.
This tool is expected to be only self-consistent.
"""

from __future__ import absolute_import
from __future__ import print_function

import argparse
import logging
import sys

from containerregistry.client.v2_2 import docker_image as v2_2_image
from containerregistry.client.v2_2 import oci_compat
from containerregistry.tools import logging_setup

from six.moves import zip  # pylint: disable=redefined-builtin

parser = argparse.ArgumentParser(
    description='Calculate digest for a container image.')

parser.add_argument(
    '--tarball', action='store', help='An optional legacy base image tarball.')

parser.add_argument(
    '--output-digest',
    required=True,
    action='store',
    help='Filename to store digest in.')

parser.add_argument(
    '--config',
    action='store',
    help='The path to the file storing the image config.')

parser.add_argument(
    '--manifest',
    action='store',
    help='The path to the file storing the image manifest.')

parser.add_argument(
    '--digest',
    action='append',
    help='The list of layer digest filenames in order.')

parser.add_argument(
    '--layer', action='append', help='The list of layer filenames in order.')

parser.add_argument(
    '--oci', action='store_true', help='Image has an OCI Manifest.')


def main():
  logging_setup.DefineCommandLineArgs(parser)
  args = parser.parse_args()
  logging_setup.Init(args=args)

  if not args.config and (args.layer or args.digest):
    logging.fatal(
        'Using --layer or --digest requires --config to be specified.')
    sys.exit(1)

  if not args.config and not args.tarball:
    logging.fatal('Either --config or --tarball must be specified.')
    sys.exit(1)

  # If config is specified, use that.  Otherwise, fallback on reading
  # the config from the tarball.
  config = args.config
  manifest = args.manifest
  if args.config:
    logging.info('Reading config from %r', args.config)
    with open(args.config, 'r') as reader:
      config = reader.read()
  elif args.tarball:
    logging.info('Reading config from tarball %r', args.tarball)
    with v2_2_image.FromTarball(args.tarball) as base:
      config = base.config_file()

  if args.manifest:
    with open(args.manifest, 'r') as reader:
      manifest = reader.read()

  if len(args.digest or []) != len(args.layer or []):
    logging.fatal('--digest and --layer must have matching lengths.')
    sys.exit(1)

  logging.info('Loading v2.2 image from disk ...')
  with v2_2_image.FromDisk(
      config,
      list(zip(args.digest or [], args.layer or [])),
      legacy_base=args.tarball,
      foreign_layers_manifest=manifest) as v2_2_img:

    try:
      if args.oci:
        with oci_compat.OCIFromV22(v2_2_img) as oci_img:
          digest = oci_img.digest()
      else:
        digest = v2_2_img.digest()

      with open(args.output_digest, 'w+') as digest_file:
        digest_file.write(digest)
    # pylint: disable=broad-except
    except Exception as e:
      logging.fatal('Error getting digest: %s', e)
      sys.exit(1)


if __name__ == '__main__':
  main()
