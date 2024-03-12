# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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
"""Untag images command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from containerregistry.client import docker_name
from containerregistry.client.v2_2 import docker_session
from googlecloudsdk.api_lib.container.images import util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.container import flags
from googlecloudsdk.core import log
from googlecloudsdk.core.console import console_io
import six


class Untag(base.DeleteCommand):
  """Remove existing image tags.

  The container images untag command of gcloud deletes a specified
  tag on a specified image. Repositories must be hosted by the
  Google Container Registry.
  """

  detailed_help = {
      'DESCRIPTION':
          """\
          The container images untag command removes the specified tag
          from the image.
      """,
      'EXAMPLES':
          """\
          Removes the tag from the input IMAGE_NAME:

            $ {command} <IMAGE_NAME>

      """,
  }

  @staticmethod
  def Args(parser):
    """Register flags for this command.

    Args:
      parser: An argparse.ArgumentParser-like object. It is mocked out in order
        to capture some information, but behaves like an ArgumentParser.
    """
    flags.AddTagOrDigestPositional(parser, verb='untag', tags_only=True)

  def Run(self, args):
    """This is what is called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Raises:
      util.InvalidImageNameError: If the user specified an invalid
      (or non-existent) image name.
    Returns:
      A list of the deleted docker_name.Tag objects
    """
    # IMAGE_NAME: The fully-qualified image name to delete (with a tag).
    # Removes the tag from the image. Ex. gcr.io/google-appengine/java:TAG.

    http_obj = util.Http()
    # collect input/validate
    tags = self._ParseArgs(args.image_names)

    digests = dict()
    with util.WrapExpectedDockerlessErrors():
      for tag in tags:
        try:
          # Resolve tags to digests. Throws InvalidImageNameError on 404.
          digests[tag] = util.GetDigestFromName(six.text_type(tag))
        except util.InvalidImageNameError:
          # We already validated the image string in _ParseArgs, this is a 404
          raise util.InvalidImageNameError(
              'Image could not be found: [{}]'.format(six.text_type(tag)))

      if not tags:
        log.warning('No tags found matching image names [%s].',
                    ', '.join(args.image_names))
        return
      for tag, digest in six.iteritems(digests):
        log.status.Print('Tag: [{}]'.format(six.text_type(tag)))
        log.status.Print('- referencing digest: [{}]'.format(
            six.text_type(digest)))
        log.status.Print('')

      console_io.PromptContinue(
          'This operation will remove the above tags. '
          'Tag removals only delete the tags; '
          'The underlying image layers (referenced by the above digests) will '
          'continue to exist.',
          cancel_on_no=True)

      # delete and collect output
      result = []
      for tag in tags:
        self._DeleteDockerTag(tag, digests, http_obj)
        result.append({'name': six.text_type(tag)})
      return result

  def _ParseArgs(self, image_names):
    tags = set()
    for image_name in image_names:
      docker_obj = util.GetDockerImageFromTagOrDigest(image_name)
      if (isinstance(docker_obj, docker_name.Tag) and
          util.IsFullySpecified(image_name)):
        # Only accept explicitly named tags for removal.
        tags.add(docker_obj)
      else:
        raise util.InvalidImageNameError(
            'IMAGE_NAME must be of the form [*.gcr.io/repository:<tag>]: '
            '[{}]'.format(image_name))
    return tags

  def _DeleteDockerTag(self, tag, digests, http_obj):
    # calling Delete on an image referenced by tag only deletes the tag
    docker_session.Delete(
        creds=util.CredentialProvider(), name=tag, transport=http_obj)
    log.DeletedResource('[{tag}] (referencing [{digest}])'.format(
        tag=tag, digest=digests[tag]))
