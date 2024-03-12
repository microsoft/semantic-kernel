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
"""This package imports images from a 'docker save' tarball.

Unlike 'docker save' the format this uses is proprietary.
"""



import argparse
import logging

from containerregistry.client.v2_2 import docker_image as v2_2_image
from containerregistry.client.v2_2 import save
from containerregistry.tools import logging_setup
from containerregistry.tools import patched

parser = argparse.ArgumentParser(
    description='Import images from a tarball into our faaaaaast format.')

parser.add_argument(
    '--tarball',
    action='store',
    help=('The tarball containing the docker image to rewrite '
          'into our fast on-disk format.'),
    required=True)

parser.add_argument(
    '--format',
    action='store',
    default='tar',
    choices=['tar', 'tar.gz'],
    help='The form in which to save layers.')

parser.add_argument(
    '--directory', action='store', help='Where to save the image\'s files.',
    required=True)

_THREADS = 32


def main():
  logging_setup.DefineCommandLineArgs(parser)
  args = parser.parse_args()
  logging_setup.Init(args=args)

  method = save.uncompressed
  if args.format == 'tar.gz':
    method = save.fast

  logging.info('Reading v2.2 image from tarball %r', args.tarball)
  with v2_2_image.FromTarball(args.tarball) as v2_2_img:
    method(v2_2_img, args.directory, threads=_THREADS)


if __name__ == '__main__':
  with patched.Httplib2():
    main()
