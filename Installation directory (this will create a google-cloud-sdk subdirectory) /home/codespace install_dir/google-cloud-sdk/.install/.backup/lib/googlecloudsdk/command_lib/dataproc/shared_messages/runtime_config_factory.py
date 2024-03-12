# -*- coding: utf-8 -*- #
# Copyright 2021 Google LLC. All Rights Reserved.
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
"""Factory for RuntimeConfig message."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import collections

from apitools.base.py import encoding
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.command_lib.dataproc.shared_messages import autotuning_config_factory as standard_autotuning_config_factory


class RuntimeConfigFactory(object):
  """Factory for RuntimeConfig message.

  Factory to add RuntimeConfig message arguments to argument parser and create
  RuntimeConfig message from parsed arguments.
  """

  def __init__(
      self,
      dataproc,
      use_config_property=False,
      include_autotuning=False,
      include_cohort=False,
      autotuning_config_factory=None,
  ):
    """Factory for RuntimeConfig message.

    Args:
      dataproc: Api_lib.dataproc.Dataproc instance.
      use_config_property: Use --property instead of --properties
      include_autotuning: Add support for autotuning arguments.
      include_cohort: Add support for cohort argument.
      autotuning_config_factory: Override the standard AutotuningConfigFactory
        instance.
    """
    self.dataproc = dataproc
    self.use_config_property = use_config_property
    self.include_autotuning = include_autotuning
    self.include_cohort = include_cohort

    self.autotuning_config_factory = (
        autotuning_config_factory
        or standard_autotuning_config_factory.AutotuningConfigFactory(
            self.dataproc
        )
    )

  def GetMessage(self, args):
    """Builds a RuntimeConfig message.

    Build a RuntimeConfig message instance according to user settings. Returns
    None if all fields are None.

    Args:
      args: Parsed arguments.

    Returns:
      RuntimeConfig: A RuntimeConfig message instance. This function returns
      None if all fields are None.
    """
    kwargs = {}

    if args.container_image:
      kwargs['containerImage'] = args.container_image

    flat_property = collections.OrderedDict()
    if self.use_config_property:
      if args.property:
        for entry in args.property:
          for k, v in entry.items():
            flat_property[k] = v
    elif args.properties:
      flat_property = args.properties
    if flat_property:
      kwargs['properties'] = encoding.DictToAdditionalPropertyMessage(
          flat_property,
          self.dataproc.messages.RuntimeConfig.PropertiesValue,
          sort_items=True,
      )

    if args.version:
      kwargs['version'] = args.version

    if self.include_autotuning:
      autotuning_config = self.autotuning_config_factory.GetMessage(args)
      if autotuning_config:
        kwargs['autotuningConfig'] = autotuning_config

    if self.include_cohort:
      cohort_id = args.cohort or args.autotuning_cohort
      if cohort_id:
        kwargs['cohort'] = cohort_id
        # Here we also set AutotuningConfig
        if 'autotuningConfig' not in kwargs:
          kwargs['autotuningConfig'] = self.dataproc.messages.AutotuningConfig(
              cohort=cohort_id
          )
        else:
          kwargs['autotuningConfig'].cohort = cohort_id

    if not kwargs:
      return None

    return self.dataproc.messages.RuntimeConfig(**kwargs)


def AddArguments(
    parser,
    use_config_property=False,
    include_autotuning=False,
    include_cohort=False,
):
  """Adds arguments related to RuntimeConfig message to the given parser."""
  parser.add_argument(
      '--container-image',
      help=(
          'Optional custom container image to use for the batch/session '
          'runtime environment. If not specified, a default container image '
          'will be used. The value should follow the container image naming '
          'format: {registry}/{repository}/{name}:{tag}, for example, '
          'gcr.io/my-project/my-image:1.2.3'
      ),
  )
  if use_config_property:
    parser.add_argument(
        '--property',
        type=arg_parsers.ArgDict(),
        action='append',
        metavar='PROPERTY=VALUE',
        help='Specifies configuration properties.',
    )
  else:
    parser.add_argument(
        '--properties',
        type=arg_parsers.ArgDict(),
        metavar='PROPERTY=VALUE',
        help="""\
        Specifies configuration properties for the workload. See
        [Dataproc Serverless for Spark documentation](https://cloud.google.com/dataproc-serverless/docs/concepts/properties)
        for the list of supported properties.""",
    )

  parser.add_argument(
      '--version',
      help=(
          'Optional runtime version.  If not specified, a default '
          'version will be used.'
      ),
  )

  if include_cohort:
    cohort_group = parser.add_mutually_exclusive_group(hidden=True)
    cohort_group.add_argument(
        '--cohort',
        help=(
            'Cohort identifier. Identifies families of the workloads having the'
            ' similar structure and inputs, e.g. daily ETL jobs.'
        ),
        hidden=True,
    )
    cohort_group.add_argument(
        '--autotuning-cohort',
        help=(
            'Autotuning cohort identifier. Identifies families of the workloads'
            ' having the similar structure and inputs, e.g. daily ETL jobs.'
        ),
        hidden=True,
    )

  _AddDependency(parser, include_autotuning)


def _AddDependency(parser, include_autotuning):
  if include_autotuning:
    standard_autotuning_config_factory.AddArguments(parser)
