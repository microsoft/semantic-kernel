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
"""Add tag command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from containerregistry.client import docker_name
from containerregistry.client.v2 import docker_image as v2_image
from containerregistry.client.v2 import docker_session as v2_session
from containerregistry.client.v2_2 import docker_http
from containerregistry.client.v2_2 import docker_image as v2_2_image
from containerregistry.client.v2_2 import docker_image_list
from containerregistry.client.v2_2 import docker_session as v2_2_session
from googlecloudsdk.api_lib.container.images import util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.container import flags
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core.console import console_io

import six


class Create(base.CreateCommand):
  """Adds tags to existing image."""

  detailed_help = {
      'DESCRIPTION':
          """\
          The container images add-tag command adds the tag(s) specified in
          the second (and following) tag parameter(s) to the image referenced
          in the first tag parameter. Repositories must be hosted by the
          Google Container Registry.
      """,
      'EXAMPLES':
          """\
          Add a tag to another tag:

            $ {command} gcr.io/myproject/myimage:mytag1
              gcr.io/myproject/myimage:mytag2

          Add a tag to a digest

            $ {command} gcr.io/myproject/myimage@sha256:digest
              gcr.io/myproject/myimage:mytag2

          Add a tag to latest

            $ {command} gcr.io/myproject/myimage
              gcr.io/myproject/myimage:mytag2

          Promote a tag to latest

            $ {command} gcr.io/myproject/myimage:mytag1
              gcr.io/myproject/myimage:latest

      """,
  }

  @staticmethod
  def Args(parser):
    flags.AddTagOrDigestPositional(
        parser, arg_name='src_image', verb='add tags for', repeated=False)
    flags.AddTagOrDigestPositional(
        parser,
        arg_name='dest_image',
        verb='be the new tags',
        repeated=True,
        tags_only=True)

  def Run(self, args):
    # pylint: disable=missing-docstring
    def Push(image, dest_names, creds, http_obj, session_push_type):
      for dest_name in dest_names:
        with session_push_type(dest_name, creds, http_obj) as push:
          push.upload(image)
          log.CreatedResource(dest_name)

    http_obj = util.Http()

    src_name = util.GetDockerImageFromTagOrDigest(args.src_image)

    dest_names = []
    for dest_image in args.dest_image:
      try:
        dest_name = docker_name.Tag(dest_image)
      except docker_name.BadNameException as e:
        raise util.InvalidImageNameError(six.text_type(e))

      if '/' not in dest_name.repository:
        raise exceptions.Error(
            'Pushing to project root-level images is disabled. '
            'Please designate an image within a project, '
            'e.g. gcr.io/project-id/my-image:tag')
      dest_names.append(dest_name)

    console_io.PromptContinue(
        'This will tag {} with:\n{}'.format(
            src_name,
            '\n'.join(six.text_type(dest_name) for dest_name in dest_names)),
        default=True,
        cancel_on_no=True)
    creds = util.CredentialProvider()
    with util.WrapExpectedDockerlessErrors():
      with docker_image_list.FromRegistry(src_name, creds,
                                          http_obj) as manifest_list:
        if manifest_list.exists():
          Push(manifest_list, dest_names, creds, http_obj, v2_2_session.Push)
          return

      with v2_2_image.FromRegistry(
          src_name,
          creds,
          http_obj,
          accepted_mimes=docker_http.SUPPORTED_MANIFEST_MIMES) as v2_2_img:
        if v2_2_img.exists():
          Push(v2_2_img, dest_names, creds, http_obj, v2_2_session.Push)
          return

      with v2_image.FromRegistry(src_name, creds, http_obj) as v2_img:
        Push(v2_img, dest_names, creds, http_obj, v2_session.Push)
