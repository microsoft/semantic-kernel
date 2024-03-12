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

"""A command that regenerates existing or new gcloud API."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import fnmatch
import os
import re
import shutil

import googlecloudsdk
from googlecloudsdk import third_party
from googlecloudsdk.api_lib.regen import generate
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import parser_errors
from googlecloudsdk.command_lib.meta import regen as regen_utils
from googlecloudsdk.core import log
from googlecloudsdk.core.util import encoding
from googlecloudsdk.core.util import files

import ruamel.yaml
import six
from six.moves import map

_API_REGEX = '([a-z0-9_]+)/([a-z0-9_]+)'


class Regen(base.Command):
  """Regenerate given API(s) in gcloud."""

  @staticmethod
  def Args(parser):
    parser.add_argument(
        'api',
        type=arg_parsers.ArgList(),
        help='The APIs to regenerate in api_name/api_version format. '
             'These can be filename glob expressions to regenerate multiple '
             'apis. For example */* to regegenerate all apis and versions, '
             'or */*beta* to only regenerate existing beta apis. '
             'Note that if discovery doc is supplied this cannot '
             'contain any wildcards.')

    parser.add_argument(
        '--api-discovery-doc',
        help='Path to json file describing the api. If not specified, '
             'an existing discovery doc will be used.')

    parser.add_argument('--config',
                        help='Regeneration config yaml filename. '
                             'If not specified canonical config will be used.')

    parser.add_argument(
        '--base-dir',
        help='Directory where generated code will be written. '
        'By default googlecloudsdk/generated_clients/apis.')

  def Run(self, args):
    config = _LoadConfig(args.config)
    root_dir = config['root_dir']
    changed_config = False

    if args.api_discovery_doc:
      if not os.path.isfile(args.api_discovery_doc):
        raise regen_utils.DiscoveryDocError(
            'File not found {}'.format(args.api_discovery_doc))
      if len(args.api) != 1:
        raise parser_errors.ArgumentError(
            'Can only specify one api when discovery doc is provided.')

      match = re.match(_API_REGEX, args.api[0])
      if not match:
        raise regen_utils.DiscoveryDocError(
            'Api name must match {} pattern when discovery doc '
            'is specified'.format(_API_REGEX))

      api_name, api_version = match.group(1), match.group(2)
      if api_name not in config['apis']:
        log.warning('No such api %s in config, adding...', api_name)
        config['apis'][api_name] = {api_version: {'discovery_doc': ''}}
        changed_config = True
      elif api_version not in config['apis'][api_name]:
        log.warning('No such api version %s in config, adding...', api_version)
        config['apis'][api_name][api_version] = {'discovery_doc': ''}
        changed_config = True

      api_version_config = config['apis'].get(api_name).get(api_version, {})
      discovery_doc = api_name + '_' + api_version + '.json'
      new_discovery_doc = os.path.realpath(args.api_discovery_doc)
      old_discovery_doc = os.path.realpath(
          os.path.join(args.base_dir, root_dir, discovery_doc))

      if new_discovery_doc != old_discovery_doc:
        log.status.Print('Copying in {}'.format(new_discovery_doc))
        shutil.copyfile(new_discovery_doc, old_discovery_doc)

      if api_version_config['discovery_doc'] != discovery_doc:
        changed_config = True
        api_version_config['discovery_doc'] = discovery_doc

      regenerate_list = [
          (match.group(1), match.group(2), api_version_config)
      ]
    else:
      regex_patern = '|'.join(map(fnmatch.translate, args.api))
      regenerate_list = [
          (api_name, api_version, api_config)
          for api_name, api_version_config in six.iteritems(config['apis'])
          for api_version, api_config in six.iteritems(api_version_config)
          if re.match(regex_patern, api_name + '/' + api_version)
      ]

    if not regenerate_list:
      raise regen_utils.UnknownApi(
          'api [{api_name}] not found in "apis" section of '
          '{config_file}. Use [gcloud meta apis list] to see available apis.'
          .format(api_name=','.join(args.api),
                  config_file=args.config))

    base_dir = args.base_dir or os.path.dirname(
        os.path.dirname(googlecloudsdk.__file__))
    for api_name, api_version, api_config in sorted(regenerate_list):
      log.status.Print(
          'Generating {} {} from {}'
          .format(api_name,
                  api_version,
                  os.path.join(root_dir, api_config['discovery_doc'])))
      generate.GenerateApitoolsApi(base_dir, root_dir,
                                   api_name, api_version, api_config)
      generate.GenerateApitoolsResourceModule(base_dir, root_dir,
                                              api_name, api_version,
                                              api_config['discovery_doc'],
                                              api_config.get('resources', {}))

    generate.GenerateApiMap(base_dir, root_dir, config['apis'])

    # Now that everything passed, config can be updated if needed.
    if changed_config:
      log.warning('Updated %s', args.config)
      with files.FileWriter(args.config) as stream:
        ruamel.yaml.round_trip_dump(config, stream)


def _LoadConfig(config_file_name=None):
  """Loads regen config from given filename."""
  config_file_name = config_file_name or os.path.join(
      os.path.dirname(encoding.Decode(third_party.__file__)),
      'regen_apis_config.yaml')

  if not os.path.isfile(config_file_name):
    raise regen_utils.ConfigFileError('{} Not found'.format(config_file_name))
  with files.FileReader(config_file_name) as stream:
    config = ruamel.yaml.round_trip_load(stream)
  if not config or 'root_dir' not in config:
    raise regen_utils.ConfigFileError(
        '{} does not have format of gcloud api config file'
        .format(config_file_name))
  return config
