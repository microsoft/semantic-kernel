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
"""This package pushes images to a Docker Registry.

The format this tool *expects* to deal with is (unlike docker_pusher)
proprietary, however, unlike {fast,docker}_puller the signature of this tool is
compatible with docker_pusher.
"""

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
from six.moves import zip  # pylint: disable=redefined-builtin


parser = argparse.ArgumentParser(
    description='Push images to a Docker Registry, faaaaaast.')

parser.add_argument(
    '--name', action='store', help='The name of the docker image to push.',
    required=True)

# The name of this flag was chosen for compatibility with docker_pusher.py
parser.add_argument(
    '--tarball', action='store', help='An optional legacy base image tarball.')

parser.add_argument(
    '--config',
    action='store',
    help='The path to the file storing the image config.')

parser.add_argument(
    '--manifest',
    action='store',
    required=False,
    help='The path to the file storing the image manifest.')

parser.add_argument(
    '--digest',
    action='append',
    help='The list of layer digest filenames in order.')

parser.add_argument(
    '--layer', action='append', help='The list of layer filenames in order.')

parser.add_argument(
    '--stamp-info-file',
    action='append',
    required=False,
    help=('A list of files from which to read substitutions '
          'to make in the provided --name, e.g. {BUILD_USER}'))

parser.add_argument(
    '--oci', action='store_true', help='Push the image with an OCI Manifest.')

parser.add_argument(
    '--client-config-dir',
    action='store',
    help='The path to the directory where the client configuration files are '
    'located. Overiddes the value from DOCKER_CONFIG')

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

  if files:
    print(('{name} was resolved to {fname}'.format(
        name=name, fname=formatted_name)))

  return docker_name.Tag(formatted_name)


def main():
  logging_setup.DefineCommandLineArgs(parser)
  args = parser.parse_args()
  logging_setup.Init(args=args)

  # This library can support push-by-digest, but the likelihood of a user
  # correctly providing us with the digest without using this library
  # directly is essentially nil.
  name = Tag(args.name, args.stamp_info_file)

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

  # If the user provided a client config directory, instruct the keychain
  # resolver to use it to look for the docker client config
  if args.client_config_dir is not None:
    docker_creds.DefaultKeychain.setCustomConfigDir(args.client_config_dir)

  retry_factory = retry.Factory()
  retry_factory = retry_factory.WithSourceTransportCallable(httplib2.Http)
  transport = transport_pool.Http(retry_factory.Build, size=_THREADS)

  logging.info('Loading v2.2 image from disk ...')
  with v2_2_image.FromDisk(
      config,
      list(zip(args.digest or [], args.layer or [])),
      legacy_base=args.tarball,
      foreign_layers_manifest=manifest) as v2_2_img:
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
