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
"""This package pushes images to a Docker Registry."""

from __future__ import absolute_import

from __future__ import print_function

import argparse
import logging
import sys

from containerregistry.client import docker_creds
from containerregistry.client import docker_name
from containerregistry.client.v2_2 import docker_image as v2_2_image
from containerregistry.client.v2_2 import docker_session
from containerregistry.client.v2_2 import oci_compat
from containerregistry.tools import logging_setup
from containerregistry.tools import patched
from containerregistry.transport import retry
from containerregistry.transport import transport_pool

import httplib2


parser = argparse.ArgumentParser(
    description='Push images to a Docker Registry.')

parser.add_argument(
    '--name', action='store', help='The name of the docker image to push.',
    required=True)

parser.add_argument(
    '--tarball', action='store', help='Where to load the image tarball.',
    required=True)

parser.add_argument(
    '--stamp-info-file',
    action='append',
    required=False,
    help=('A list of files from which to read substitutions '
          'to make in the provided --name, e.g. {BUILD_USER}'))

parser.add_argument(
    '--oci', action='store_true', help='Push the image with an OCI Manifest.')

_THREADS = 8


def Tag(name, files):
  """Perform substitutions in the provided tag name."""
  format_args = {}
  for infofile in files or []:
    with open(infofile) as info:
      for line in info:
        line = line.strip('\n')
        key, value = line.split(' ', 1)
        if key in format_args:
          print(('WARNING: Duplicate value for key "%s": '
                 'using "%s"' % (key, value)))
        format_args[key] = value

  formatted_name = name.format(**format_args)

  return docker_name.Tag(formatted_name)


def main():
  logging_setup.DefineCommandLineArgs(parser)
  args = parser.parse_args()
  logging_setup.Init(args=args)

  retry_factory = retry.Factory()
  retry_factory = retry_factory.WithSourceTransportCallable(httplib2.Http)
  transport = transport_pool.Http(retry_factory.Build, size=_THREADS)

  # This library can support push-by-digest, but the likelihood of a user
  # correctly providing us with the digest without using this library
  # directly is essentially nil.
  name = Tag(args.name, args.stamp_info_file)

  logging.info('Reading v2.2 image from tarball %r', args.tarball)
  with v2_2_image.FromTarball(args.tarball) as v2_2_img:
    # Resolve the appropriate credential to use based on the standard Docker
    # client logic.
    try:
      creds = docker_creds.DefaultKeychain.Resolve(name)
    # pylint: disable=broad-except
    except Exception as e:
      logging.fatal('Error resolving credentials for %s: %s', name, e)
      sys.exit(1)

    try:
      with docker_session.Push(
          name, creds, transport, threads=_THREADS) as session:
        logging.info('Starting upload ...')
        if args.oci:
          with oci_compat.OCIFromV22(v2_2_img) as oci_img:
            session.upload(oci_img)
            digest = oci_img.digest()
        else:
          session.upload(v2_2_img)
          digest = v2_2_img.digest()

        print(('{name} was published with digest: {digest}'.format(
            name=name, digest=digest)))
    # pylint: disable=broad-except
    except Exception as e:
      logging.fatal('Error publishing %s: %s', name, e)
      sys.exit(1)


if __name__ == '__main__':
  with patched.Httplib2():
    main()
