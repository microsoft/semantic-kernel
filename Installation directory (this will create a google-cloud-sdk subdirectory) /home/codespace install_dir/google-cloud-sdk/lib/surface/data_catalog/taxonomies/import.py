# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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

"""List command for gcloud debug logpoints command group."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.data_catalog import flags
from googlecloudsdk.command_lib.data_catalog.taxonomies import taxonomies
from googlecloudsdk.command_lib.data_catalog.taxonomies import util
from googlecloudsdk.core import properties


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.GA)
class Import(base.Command):
  """Export a file with serialized taxonomies to a certain project."""

  detailed_help = {
      'DESCRIPTION': """
          Export a file with serialized taxonomies to a certain project.
      """,
      'EXAMPLES': """
          To parse and import the taxonomies contained in '/tmp/taxonomies.json'
          to your project within location LOCATION:

            $ {command} "/tmp/taxonomies.json" --location="LOCATION"
      """,
  }

  @staticmethod
  def Args(parser):
    flags.AddLocationResourceArg(parser, 'Location to import taxonomies to.')
    parser.add_argument(
        'taxonomies',
        type=arg_parsers.YAMLFileContents(),
        metavar='TAXONOMIES',
        help="""\
            File containing serialized taxonomy.
        """)

  def Run(self, args):
    """Run the import command."""
    version_label = flags.GetVersionLabel(self.ReleaseTrack())
    args.project_val = properties.VALUES.core.project.Get()
    args.taxonomies = util.ProcessTaxonomiesFromYAML(args.taxonomies,
                                                     version_label)
    return taxonomies.Import(args, version_label)
