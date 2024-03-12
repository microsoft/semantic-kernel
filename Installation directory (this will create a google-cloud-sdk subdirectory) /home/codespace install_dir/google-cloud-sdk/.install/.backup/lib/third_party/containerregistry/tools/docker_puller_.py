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
"""This package pulls images from a Docker Registry."""



import argparse
import logging
import sys
import tarfile

from containerregistry.client import docker_creds
from containerregistry.client import docker_name
from containerregistry.client.v2 import docker_image as v2_image
from containerregistry.client.v2_2 import docker_http
from containerregistry.client.v2_2 import docker_image as v2_2_image
from containerregistry.client.v2_2 import docker_image_list as image_list
from containerregistry.client.v2_2 import save
from containerregistry.client.v2_2 import v2_compat
from containerregistry.tools import logging_setup
from containerregistry.tools import patched
from containerregistry.tools import platform_args
from containerregistry.transport import retry
from containerregistry.transport import transport_pool

import httplib2


parser = argparse.ArgumentParser(
    description='Pull images from a Docker Registry.')

parser.add_argument(
    '--name',
    action='store',
    help=('The name of the docker image to pull and save. '
          'Supports fully-qualified tag or digest references.'),
    required=True)

parser.add_argument(
    '--tarball', action='store', help='Where to save the image tarball.',
    required=True)

platform_args.AddArguments(parser)

_DEFAULT_TAG = 'i-was-a-digest'


# Today save.tarball expects a tag, which is emitted into one or more files
# in the resulting tarball.  If we don't translate the digest into a tag then
# the tarball format leaves us no good way to represent this information and
# folks are left having to tag the resulting image ID (yuck).  As a datapoint
# `docker save -o /tmp/foo.tar bar@sha256:deadbeef` omits the v1 "repositories"
# file and emits `null` for the `RepoTags` key in "manifest.json".  By doing
# this we leave a trivial breadcrumb of what the image was named (and the digest
# is recoverable once the image is loaded), which is a strictly better UX IMO.
# We do not need to worry about collisions by doing this here because this tool
# only packages a single image, so this is preferable to doing something similar
# in save.py itself.
def _make_tag_if_digest(
    name):
  if isinstance(name, docker_name.Tag):
    return name
  return docker_name.Tag('{repo}:{tag}'.format(
      repo=str(name.as_repository()), tag=_DEFAULT_TAG))


def main():
  logging_setup.DefineCommandLineArgs(parser)
  args = parser.parse_args()
  logging_setup.Init(args=args)

  retry_factory = retry.Factory()
  retry_factory = retry_factory.WithSourceTransportCallable(httplib2.Http)
  transport = transport_pool.Http(retry_factory.Build, size=8)

  if '@' in args.name:
    name = docker_name.Digest(args.name)
  else:
    name = docker_name.Tag(args.name)

  # OCI Image Manifest is compatible with Docker Image Manifest Version 2,
  # Schema 2. We indicate support for both formats by passing both media types
  # as 'Accept' headers.
  #
  # For reference:
  #   OCI: https://github.com/opencontainers/image-spec
  #   Docker: https://docs.docker.com/registry/spec/manifest-v2-2/
  accept = docker_http.SUPPORTED_MANIFEST_MIMES

  # Resolve the appropriate credential to use based on the standard Docker
  # client logic.
  try:
    creds = docker_creds.DefaultKeychain.Resolve(name)
  # pylint: disable=broad-except
  except Exception as e:
    logging.fatal('Error resolving credentials for %s: %s', name, e)
    sys.exit(1)

  try:
    with tarfile.open(name=args.tarball, mode='w:') as tar:
      logging.info('Pulling manifest list from %r ...', name)
      with image_list.FromRegistry(name, creds, transport) as img_list:
        if img_list.exists():
          platform = platform_args.FromArgs(args)
          # pytype: disable=wrong-arg-types
          with img_list.resolve(platform) as default_child:
            save.tarball(_make_tag_if_digest(name), default_child, tar)
            return
          # pytype: enable=wrong-arg-types

      logging.info('Pulling v2.2 image from %r ...', name)
      with v2_2_image.FromRegistry(name, creds, transport, accept) as v2_2_img:
        if v2_2_img.exists():
          save.tarball(_make_tag_if_digest(name), v2_2_img, tar)
          return

      logging.info('Pulling v2 image from %r ...', name)
      with v2_image.FromRegistry(name, creds, transport) as v2_img:
        with v2_compat.V22FromV2(v2_img) as v2_2_img:
          save.tarball(_make_tag_if_digest(name), v2_2_img, tar)
          return
  # pylint: disable=broad-except
  except Exception as e:
    logging.fatal('Error pulling and saving image %s: %s', name, e)
    sys.exit(1)


if __name__ == '__main__':
  with patched.Httplib2():
    main()
