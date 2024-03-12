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
"""List tags command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import heapq
import sys

from containerregistry.client.v2_2 import docker_image
from googlecloudsdk.api_lib.container.images import util
from googlecloudsdk.api_lib.containeranalysis import filter_util
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.container import flags
from googlecloudsdk.core import exceptions


# Add to this as we add columns.
_DEFAULT_KINDS = [
    'BUILD',
    'IMAGE',
    'DISCOVERY',
]
# How many images for which to report vulnerabilities, by default. These are
# always the most recent images, regardless of sorting.
_DEFAULT_SHOW_OCCURRENCES_FROM = 10
# By default return the most recent timestamps.
# (The --sort-by flag uses syntax `~X` to mean "sort descending on field X.")
_DEFAULT_SORT_BY = '~timestamp'

_TAGS_FORMAT = """
    table(
        digest.slice(7:19).join(''),
        tags.list(),
        timestamp.date():optional,
        BUILD.build.provenance.sourceProvenance.context.cloudRepo.revisionId.notnull().list().slice(:8).join(''):optional:label=GIT_SHA,
        vuln_counts.list():optional:label=VULNERABILITIES,
        IMAGE.image.sort(distance).map().extract(baseResourceUrl).slice(:1).map().list().list().split('//').slice(1:).list().split('@').slice(:1).list():optional:label=FROM,
        BUILD.build.provenance.id.notnull().list():optional:label=BUILD,
        DISCOVERY[0].discovered.analysisStatus:optional:label=VULNERABILITY_SCAN_STATUS
    )
"""


class ArgumentError(exceptions.Error):
  """For missing required mutually inclusive flags."""
  pass


@base.ReleaseTracks(base.ReleaseTrack.GA)
class ListTagsGA(base.ListCommand):
  """List tags and digests for the specified image."""

  detailed_help = {
      'DESCRIPTION':
          """\
          The container images list-tags command of gcloud lists metadata about
          tags and digests for the specified container image. Images must be
          hosted by the Google Container Registry.
      """,
      'EXAMPLES':
          """\
          List the tags in a specified image:

            $ {command} gcr.io/myproject/myimage

          To receive the full, JSON-formatted output (with untruncated digests):

            $ {command} gcr.io/myproject/myimage --format=json

          To list digests without corresponding tags:

            $ {command} gcr.io/myproject/myimage --filter="NOT tags:*"

          To list images that have a tag with the value '30e5504145':

            $ gcloud container images list-tags --filter="'tags:30e5504145'"

          The last example encloses the filter expression in single quotes
          because the value '30e5504145' could be interpreted as a number in
          scientific notation.

      """,
  }

  @staticmethod
  def Args(parser):
    """Register flags for this command.

    Args:
      parser: An argparse.ArgumentParser-like object. It is mocked out in order
        to capture some information, but behaves like an ArgumentParser.
    """
    flags.AddImagePositional(parser, verb='list tags for')
    base.SORT_BY_FLAG.SetDefault(parser, _DEFAULT_SORT_BY)

    # Does nothing for us, included in base.ListCommand
    base.URI_FLAG.RemoveFromParser(parser)
    parser.display_info.AddFormat(_TAGS_FORMAT)

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Raises:
      InvalidImageNameError: If the user specified an invalid image name.
    Returns:
      Some value that we want to have printed later.
    """
    repository = util.ValidateRepositoryPath(args.image_name)
    http_obj = util.Http()
    with util.WrapExpectedDockerlessErrors(repository):
      with docker_image.FromRegistry(
          basic_creds=util.CredentialProvider(),
          name=repository,
          transport=http_obj) as image:
        manifests = image.manifests()
        return util.TransformManifests(manifests, repository)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class ListTagsALPHAandBETA(ListTagsGA, base.ListCommand):
  """List tags and digests for the specified image."""

  @staticmethod
  def Args(parser):
    """Register flags for this command.

    Args:
      parser: An argparse.ArgumentParser-like object. It is mocked out in order
        to capture some information, but behaves like an ArgumentParser.
    """
    # Weird syntax, but this is how to call a static base method from the
    # derived method in Python.
    super(ListTagsALPHAandBETA, ListTagsALPHAandBETA).Args(parser)

    # TODO(b/116048537): Refactor these flags to comply with gcloud style.
    parser.add_argument(
        '--show-occurrences',
        action='store_true',
        default=True,
        help='Whether to show summaries of the various Occurrence types.')
    parser.add_argument(
        '--occurrence-filter',
        default=' OR '.join(
            ['kind = "{kind}"'.format(kind=x) for x in _DEFAULT_KINDS]),
        help='A filter for the Occurrences which will be summarized.')
    parser.add_argument(
        '--show-occurrences-from',
        type=arg_parsers.BoundedInt(1, sys.maxsize, unlimited=True),
        default=_DEFAULT_SHOW_OCCURRENCES_FROM,
        help=('How many of the most recent images for which to summarize '
              'Occurences.'))

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Raises:
      ArgumentError: If the user provided the flag --show-occurrences-from but
        --show-occurrences=False.
      InvalidImageNameError: If the user specified an invalid image name.
    Returns:
      Some value that we want to have printed later.
    """
    # Verify that --show-occurrences-from is set iff --show-occurrences=True.
    if args.IsSpecified('show_occurrences_from') and not args.show_occurrences:
      raise ArgumentError(
          '--show-occurrences-from may only be set if --show-occurrences=True')

    repository = util.ValidateRepositoryPath(args.image_name)
    http_obj = util.Http()
    with util.WrapExpectedDockerlessErrors(repository):
      with docker_image.FromRegistry(
          basic_creds=util.CredentialProvider(),
          name=repository,
          transport=http_obj) as image:
        manifests = image.manifests()
        # Only consider the top _DEFAULT_SHOW_OCCURRENCES_FROM images
        # to reduce computation time.
        most_recent_resource_urls = None
        occ_filter = filter_util.ContainerAnalysisFilter()
        occ_filter.WithCustomFilter(args.occurrence_filter)
        occ_filter.WithResourcePrefixes(['https://{}'.format(repository)])
        if args.show_occurrences_from:
          # This block is skipped when the user provided
          # --show-occurrences-from=unlimited on the CLI.
          most_recent_resource_urls = [
              'https://%s@%s' % (args.image_name, k) for k in heapq.nlargest(
                  args.show_occurrences_from,
                  manifests, key=lambda k: manifests[k]['timeCreatedMs'])
          ]
          occ_filter.WithResources(most_recent_resource_urls)
        return util.TransformManifests(
            manifests,
            repository,
            show_occurrences=args.show_occurrences,
            occurrence_filter=occ_filter)
