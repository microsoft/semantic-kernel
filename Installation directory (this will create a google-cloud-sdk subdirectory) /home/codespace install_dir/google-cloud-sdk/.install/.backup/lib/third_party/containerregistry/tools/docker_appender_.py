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
"""This package appends a tarball to an image in a Docker Registry."""

from __future__ import absolute_import

from __future__ import print_function

import argparse
import logging

from containerregistry.client import docker_creds
from containerregistry.client import docker_name
from containerregistry.client.v2_2 import append
from containerregistry.client.v2_2 import docker_image as v2_2_image
from containerregistry.client.v2_2 import docker_session
from containerregistry.tools import logging_setup
from containerregistry.tools import patched
from containerregistry.transport import transport_pool

import httplib2

parser = argparse.ArgumentParser(
    description='Append tarballs to an image in a Docker Registry.')

parser.add_argument(
    '--src-image',
    action='store',
    help='The name of the docker image to append to.',
    required=True)

parser.add_argument('--tarball', action='store', help='The tarball to append.',
                    required=True)

parser.add_argument(
    '--dst-image', action='store', help='The name of the new image.',
    required=True)

_THREADS = 8


def main():
  logging_setup.DefineCommandLineArgs(parser)
  args = parser.parse_args()
  logging_setup.Init(args=args)

  transport = transport_pool.Http(httplib2.Http, size=_THREADS)

  # This library can support push-by-digest, but the likelihood of a user
  # correctly providing us with the digest without using this library
  # directly is essentially nil.
  src = docker_name.Tag(args.src_image)
  dst = docker_name.Tag(args.dst_image)

  # Resolve the appropriate credential to use based on the standard Docker
  # client logic.
  creds = docker_creds.DefaultKeychain.Resolve(src)
  logging.info('Pulling v2.2 image from %r ...', src)
  with v2_2_image.FromRegistry(src, creds, transport) as src_image:
    with open(args.tarball, 'rb') as f:
      new_img = append.Layer(src_image, f.read())

  creds = docker_creds.DefaultKeychain.Resolve(dst)
  with docker_session.Push(dst, creds, transport, threads=_THREADS,
                           mount=[src.as_repository()]) as session:
    logging.info('Starting upload ...')
    session.upload(new_img)
    digest = new_img.digest()

    print(('{name} was published with digest: {digest}'.format(
        name=dst, digest=digest)))


if __name__ == '__main__':
  with patched.Httplib2():
    main()
