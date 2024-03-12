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

"""CLI trees supplementary help."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base


# NOTE: If the name of this topic is modified, please make sure to update all
# references to it in error messages and other help messages as there are no
# tests to catch such changes.
class CliTrees(base.TopicCommand):
  """CLI trees supplementary help.

  CLI trees are static nested dictionaries that describe all of the groups,
  commands, flags, positionals, help text, and completer module paths for a
  CLI. A CLI tree is often much faster to load and access than one generated
  at runtime from an active CLI. It is also a more compact representation.
  A properly formed CLI tree can be used to reproduce the help documentation
  for an entire CLI.

  ### CLI Tree Data Files

  A CLI tree is a dictionary in a JSON file. By convention, the file base name
  is the corresponding CLI name. For example, the CLI tree file name for
  *gcloud* is *gcloud.json*.

  CLI trees associated with Google Cloud CLI modules are installed in the
  *data/cli* subdirectory of the Google Cloud CLI installation root:

      $(gcloud info --format="value(installation.sdk_root)")/data/cli

  This includes tree data for *gcloud* (core component), *bq*, *gsutil*,
  and *kubectl*. Note that the tree data is installed with the component.
  If the component is not installed then neither is its CLI tree. An installed
  component does not require its CLI tree to run. Only the *gcloud* CLI
  tree is required by `$ gcloud alpha interactive`.

  By default, CLI trees for other commands are JSON files generated on demand
  from their *man*(1) or *man7.org* man pages. They are cached in the *cli*
  subdirectory of the global config directory:

    $(gcloud info --format="value(config.paths.global_config_dir)")/cli

  ### The gcloud CLI Tree

  The *gcloud* CLI tree is used for static TAB completion, the corpus for
  `$ gcloud alpha help-search`, and the data source for
  `$ gcloud alpha interactive` completions and help text generation.

  ### Other CLI Trees

  `$ gcloud alpha interactive` uses CLI tree data files for typeahead,
  command line completion and active help. A few CLI trees are installed
  with their respective Google Cloud CLI components: *gcloud* (core component),
  *bq*, *gsutil*, and *kubectl*.

  The generated trees are a close approximation. You can construct your own,
  especially for hierarchical CLIs like *git*(1) that are hard to extract
  from man pages.

  ### CLI Tree Schema

  TBD (`gcloud interactive` is still in ALPHA).
  """
