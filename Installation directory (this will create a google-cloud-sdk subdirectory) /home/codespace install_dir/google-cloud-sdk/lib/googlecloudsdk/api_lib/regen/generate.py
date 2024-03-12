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
"""Utility wrappers around apitools generator."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import logging
import os

from apitools.gen import gen_client
from googlecloudsdk.api_lib.regen import api_def
from googlecloudsdk.api_lib.regen import resource_generator
from googlecloudsdk.core.util import files
from mako import runtime
from mako import template
import six


_INIT_FILE_CONTENT = """\
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

"""


class NoDefaultApiError(Exception):
  """Multiple apis versions are specified but no default is set."""


class WrongDiscoveryDocError(Exception):
  """Unexpected discovery doc."""


def GenerateApitoolsApi(base_dir, root_dir, api_name, api_version, api_config):
  """Invokes apitools generator for given api."""
  discovery_doc = api_config['discovery_doc']

  args = [gen_client.__file__]

  unelidable_request_methods = api_config.get('unelidable_request_methods')
  if unelidable_request_methods:
    args.append('--unelidable_request_methods={0}'.format(
        ','.join(api_config['unelidable_request_methods'])))

  args.extend([
      '--init-file=empty',
      '--nogenerate_cli',
      '--infile={0}'.format(os.path.join(base_dir, root_dir, discovery_doc)),
      '--outdir={0}'.format(os.path.join(base_dir, root_dir, api_name,
                                         api_version)),
      '--overwrite',
      '--apitools_version=CloudSDK',
      '--user_agent=google-cloud-sdk',
      '--root_package',
      '{0}.{1}.{2}'.format(
          root_dir.replace('/', '.'), api_name, api_version),
      'client',
  ])
  logging.debug('Apitools gen %s', args)
  gen_client.main(args)

  package_dir = base_dir
  for subdir in [root_dir, api_name, api_version]:
    package_dir = os.path.join(package_dir, subdir)
    init_file = os.path.join(package_dir, '__init__.py')
    if not os.path.isfile(init_file):
      logging.warning('%s does not have __init__.py file, generating ...',
                      package_dir)
      files.WriteFileContents(init_file, _INIT_FILE_CONTENT)


def _CamelCase(snake_case):
  return ''.join(x.capitalize() for x in snake_case.split('_'))


def _MakeApitoolsClientDef(root_package, api_name, api_version):
  """Makes an ApitoolsClientDef."""
  class_path = '.'.join([root_package, api_name, api_version])
  # TODO(b/142448542) Roll back the hack
  if api_name == 'admin' and api_version == 'v1':
    client_classpath = 'admin_v1_client.AdminDirectoryV1'
  else:
    client_classpath = '.'.join([
        '_'.join([api_name, api_version, 'client']),
        _CamelCase(api_name) + _CamelCase(api_version)])

  messages_modulepath = '_'.join([api_name, api_version, 'messages'])
  base_url = ''
  client_full_classpath = class_path + '.' + client_classpath
  try:
    client_classpath_def = _GetClientClassFromDef(client_full_classpath)
    base_url = client_classpath_def.BASE_URL
  except Exception:   # pylint: disable=broad-except
    # unreleased api or test not in "googlecloudsdk.generated_clients.apis"
    pass

  apitools_def = api_def.ApitoolsClientDef(
      class_path=class_path,
      client_classpath=client_classpath,
      messages_modulepath=messages_modulepath,
      base_url=base_url)
  return apitools_def


def _GetClientClassFromDef(client_full_classpath):
  """Returns the client class for the API definition specified in the args."""
  module_path, client_class_name = client_full_classpath.rsplit('.', 1)
  module_obj = __import__(module_path, fromlist=[client_class_name])
  return getattr(module_obj, client_class_name)


def _MakeGapicClientDef(root_package, api_name, api_version):
  """Makes a GapicClientDef."""
  gapic_root_package = '.'.join(root_package.split('.')[:-1])
  class_path = '.'.join(
      [gapic_root_package, 'gapic_wrappers', api_name, api_version])
  return api_def.GapicClientDef(
      class_path=class_path)


def _MakeApiMap(root_package, api_config):
  """Converts a map of api_config into ApiDef.

  Args:
    root_package: str, root path of where generate api will reside.
    api_config: {api_name->api_version->{discovery,default,version,...}},
                description of each api.
  Returns:
    {api_name->api_version->ApiDef()}.

  Raises:
    NoDefaultApiError: if for some api with multiple versions
        default was not specified.
  """
  apis_map = {}
  apis_with_default = set()
  for api_name, api_version_config in six.iteritems(api_config):
    api_versions_map = apis_map.setdefault(api_name, {})
    has_default = False
    for api_version, api_config in six.iteritems(api_version_config):
      if api_config.get('discovery_doc'):
        apitools_client = _MakeApitoolsClientDef(
            root_package, api_name, api_version
        )
      else:
        apitools_client = None
      if api_config.get('gcloud_gapic_library'):
        gapic_client = _MakeGapicClientDef(root_package, api_name, api_version)
      else:
        gapic_client = None

      default = api_config.get('default', len(api_version_config) == 1)
      if has_default and default:
        raise NoDefaultApiError(
            'Multiple default client versions found for [{}]!'
            .format(api_name))
      has_default = has_default or default

      enable_mtls = api_config.get('enable_mtls', True)
      mtls_endpoint_override = api_config.get('mtls_endpoint_override', '')
      api_versions_map[api_version] = api_def.APIDef(
          apitools_client,
          gapic_client,
          default, enable_mtls, mtls_endpoint_override)
    if has_default:
      apis_with_default.add(api_name)

  apis_without_default = set(apis_map.keys()).difference(apis_with_default)
  if apis_without_default:
    raise NoDefaultApiError('No default client versions found for [{0}]!'
                            .format(', '.join(sorted(apis_without_default))))
  return apis_map


def GenerateApiMap(base_dir, root_dir, api_config):
  """Create an apis_map.py file in the given root_dir with for given api_config.

  Args:
      base_dir: str, Path of directory for the project.
      root_dir: str, Path of the map file location within the project.
      api_config: regeneration config for all apis.
  """

  api_def_filename, _ = os.path.splitext(api_def.__file__)
  api_def_source = files.ReadFileContents(api_def_filename + '.py')

  tpl = template.Template(
      filename=os.path.join(os.path.dirname(__file__), 'template.tpl')
  )
  api_map_file = os.path.join(base_dir, root_dir, 'apis_map.py')
  logging.debug('Generating api map at %s', api_map_file)

  api_map = _MakeApiMap(root_dir.replace('/', '.'), api_config)
  logging.debug('Creating following api map %s', api_map)
  with files.FileWriter(api_map_file) as apis_map_file:
    ctx = runtime.Context(
        apis_map_file, api_def_source=api_def_source, apis_map=api_map
    )
    tpl.render_context(ctx)


def GenerateApitoolsResourceModule(
    base_dir,
    root_dir,
    api_name,
    api_version,
    discovery_doc_path,
    custom_resources,
):
  """Create resource.py file for given api and its discovery doc.

  Args:
      base_dir: str, Path of directory for the project.
      root_dir: str, Path of the resource file location within the project.
      api_name: str, name of the api.
      api_version: str, the version for the api.
      discovery_doc_path: str, file path to discovery doc.
      custom_resources: dict, dictionary of custom resource collections.
  Raises:
    WrongDiscoveryDocError: if discovery doc api name/version does not match.
  """

  discovery_doc = resource_generator.DiscoveryDoc.FromJson(
      os.path.join(base_dir, root_dir, discovery_doc_path))
  if discovery_doc.api_version != api_version:
    logging.warning(
        'Discovery api version %s does not match %s, '
        'this client will be accessible via new alias.',
        discovery_doc.api_version, api_version)
  if discovery_doc.api_name != api_name:
    raise WrongDiscoveryDocError('api name {0}, expected {1}'.format(
        discovery_doc.api_name, api_name))
  resource_collections = discovery_doc.GetResourceCollections(
      custom_resources, api_version)
  if custom_resources:
    # Check if this is redefining one of the existing collections.
    matched_resources = set([])
    for collection in resource_collections:
      if collection.name in custom_resources:
        apitools_compatible = custom_resources[collection.name].get(
            'apitools_compatible', True
        )
        if not apitools_compatible:
          continue
        matched_resources.add(collection.name)
        custom_path = custom_resources[collection.name]['path']
        if isinstance(custom_path, dict):
          collection.flat_paths.update(custom_path)
        elif isinstance(custom_path, six.string_types):
          collection.flat_paths[
              resource_generator.DEFAULT_PATH_NAME] = custom_path
    # Remaining must be new custom resources.
    for collection_name in set(custom_resources.keys()) - matched_resources:
      collection_def = custom_resources[collection_name]
      collection_path = collection_def['path']
      apitools_compatible = collection_def.get(
          'apitools_compatible', True
      )
      if not apitools_compatible:
        continue
      enable_uri_parsing = collection_def.get('enable_uri_parsing', True)
      collection_info = discovery_doc.MakeResourceCollection(
          collection_name, collection_path, enable_uri_parsing, api_version)
      resource_collections.append(collection_info)

  api_dir = os.path.join(base_dir, root_dir, api_name, api_version)
  if not os.path.exists(api_dir):
    os.makedirs(api_dir)
  resource_file_name = os.path.join(api_dir, 'resources.py')

  if resource_collections:
    logging.debug('Generating resource module at %s', resource_file_name)
    tpl = template.Template(filename=os.path.join(os.path.dirname(__file__),
                                                  'resources.tpl'))
    with files.FileWriter(resource_file_name) as output_file:
      ctx = runtime.Context(output_file,
                            collections=sorted(resource_collections),
                            base_url=resource_collections[0].base_url,
                            docs_url=discovery_doc.docs_url)
      tpl.render_context(ctx)
  elif os.path.isfile(resource_file_name):
    logging.debug('Removing existing resource module at %s', resource_file_name)
    os.remove(resource_file_name)
