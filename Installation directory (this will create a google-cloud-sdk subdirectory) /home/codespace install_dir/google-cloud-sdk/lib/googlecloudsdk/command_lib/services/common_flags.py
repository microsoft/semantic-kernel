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
"""Common flags for the consumers subcommand group."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import re

from googlecloudsdk.api_lib.services import services_util
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope.concepts import concepts
from googlecloudsdk.calliope.concepts import deps
from googlecloudsdk.command_lib.util import completers
from googlecloudsdk.command_lib.util.concepts import concept_parsers
from googlecloudsdk.command_lib.util.concepts import presentation_specs
from googlecloudsdk.core import properties

_SERVICES_LEGACY_LIST_COMMAND = ('services list --format=disable '
                                 '--flatten=serviceName')
_SERVICES_LIST_COMMAND = ('beta services list --format=disable '
                          '--flatten=config.name')

_OPERATION_NAME_RE = re.compile(r'operations/(?P<namespace>\w+)\.(?P<id>.*)')


class ConsumerServiceCompleter(completers.ListCommandCompleter):

  def __init__(self, **kwargs):
    super(ConsumerServiceCompleter, self).__init__(
        collection=services_util.SERVICES_COLLECTION,
        list_command=_SERVICES_LIST_COMMAND,
        flags=['enabled'],
        **kwargs)


class ConsumerServiceLegacyCompleter(completers.ListCommandCompleter):

  def __init__(self, **kwargs):
    super(ConsumerServiceLegacyCompleter, self).__init__(
        collection=services_util.SERVICES_COLLECTION,
        list_command=_SERVICES_LEGACY_LIST_COMMAND,
        flags=['enabled'],
        **kwargs)


def operation_flag(suffix='to act on'):
  return base.Argument(
      'operation', help='The name of the operation {0}.'.format(suffix))


def get_operation_namespace(op_name):
  match = _OPERATION_NAME_RE.match(op_name)
  if not match:
    raise arg_parsers.ArgumentTypeError("Invalid value '{0}': {1}".format(
        op_name, 'Operation format should be operations/namespace.id'))
  return match.group('namespace')


def consumer_service_flag(suffix='to act on', flag_name='service'):
  return base.Argument(
      flag_name,
      nargs='*',
      completer=ConsumerServiceCompleter,
      help='The name of the service(s) {0}.'.format(suffix))


def single_consumer_service_flag(suffix='to act on', flag_name='service'):
  return base.Argument(
      flag_name,
      completer=ConsumerServiceCompleter,
      help='The name of the service {0}.'.format(suffix))


def available_service_flag(suffix='to act on', flag_name='service'):
  # NOTE: Because listing available services often forces the tab completion
  #       code to timeout, this flag will not enable tab completion.
  return base.Argument(
      flag_name,
      nargs='*',
      help='The name of the service(s) {0}.'.format(suffix))


def _create_key_resource_arg(help_txt, api_version, required=True):
  return presentation_specs.ResourcePresentationSpec(
      'key', _get_key_resource_spec(api_version), help_txt, required=required
  )


def _get_key_resource_spec(api_version):
  """Return the resource specification for a key."""
  if api_version == 'v2':
    return concepts.ResourceSpec(
        'apikeys.projects.locations.keys',
        api_version=api_version,
        resource_name='key',
        disable_auto_completers=True,
        keysId=_key_attribute_config(),
        locationsId=_location_attribute_config(),
        projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG)
  else:
    return concepts.ResourceSpec(
        'apikeys.projects.keys',
        api_version=api_version,
        resource_name='key',
        disable_auto_completers=True,
        keysId=_key_attribute_config(),
        projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG)


def _key_attribute_config():
  return concepts.ResourceParameterAttributeConfig(
      name='key', help_text='Id of the key')


def _location_attribute_config():
  return concepts.ResourceParameterAttributeConfig(
      name='location',
      help_text='Location of the key.',
      fallthroughs=[
          deps.Fallthrough(
              function=lambda: 'global',
              hint='location will default to {}'.format('global'),
              active=True,
              plural=False)
      ])


def key_flag(parser, suffix='to act on', api_version='v2', required=True):
  return concept_parsers.ConceptParser(
      [
          _create_key_resource_arg(
              help_txt='The name of the key {0}.'.format(suffix),
              api_version=api_version,
              required=required,
          )
      ]
  ).AddToParser(parser)


def display_name_flag(parser, suffix='to act on'):
  base.Argument(
      '--display-name',
      help='Display name of the key {0}.'.format(suffix)).AddToParser(parser)


def key_id_flag(parser, suffix='to act on'):
  base.Argument(
      '--key-id', help='User-specified ID of the key {0}.'.format(suffix)
  ).AddToParser(parser)


def add_key_undelete_args(parser):
  """Adds args for api-keys undelete command."""
  undelete_set_group = parser.add_mutually_exclusive_group(required=True)
  key_flag(
      undelete_set_group, suffix='to undelete', api_version='v2', required=False
  )
  _key_string_flag(undelete_set_group)


def validate_only_args(parser):
  base.Argument(
      '--validate-only',
      action='store_true',
      help=(
          'If set, the action will be validated and result will be preview but'
          ' not exceuted.'
      ),
  ).AddToParser(parser)


def add_resource_args(parser):
  """Adds resource args for command."""
  resource_group = parser.add_mutually_exclusive_group(required=False)
  _project_id_flag(resource_group)
  _folder_id_flag(resource_group)
  _orgnaization_id_flag(resource_group)


def add_key_update_args(parser):
  """Adds args for api-keys update command."""
  update_set_restriction_group = parser.add_mutually_exclusive_group(
      required=False
  )
  _add_clear_restrictions_arg(update_set_restriction_group)
  restriction_group = update_set_restriction_group.add_argument_group()
  client_restriction_group = restriction_group.add_mutually_exclusive_group()
  _allowed_referrers_arg(client_restriction_group)
  _allowed_ips_arg(client_restriction_group)
  _allowed_bundle_ids(client_restriction_group)
  _allowed_application(client_restriction_group)
  _api_targets_arg(restriction_group)
  update_set_annotation_group = parser.add_mutually_exclusive_group(
      required=False
  )
  _annotations(update_set_annotation_group)
  _add_clear_annotations_arg(update_set_annotation_group)


def add_key_create_args(parser):
  """Add args for api-keys create command."""
  restriction_group = parser.add_argument_group()
  client_restriction_group = restriction_group.add_mutually_exclusive_group()
  _allowed_referrers_arg(client_restriction_group)
  _allowed_ips_arg(client_restriction_group)
  _allowed_bundle_ids(client_restriction_group)
  _allowed_application(client_restriction_group)
  _api_targets_arg(restriction_group)
  _annotations(parser)


def _add_clear_restrictions_arg(parser):
  base.Argument(
      '--clear-restrictions',
      action='store_true',
      help='If set, clear all restrictions on the key.').AddToParser(parser)


def _add_clear_annotations_arg(parser):
  base.Argument(
      '--clear-annotations',
      action='store_true',
      help='If set, clear all annotations on the key.').AddToParser(parser)


def _allowed_referrers_arg(parser):
  base.Argument(
      '--allowed-referrers',
      default=[],
      type=arg_parsers.ArgList(),
      metavar='ALLOWED_REFERRERS',
      help='A list of regular expressions for the referrer URLs that are '
      'allowed to make API calls with this key.').AddToParser(parser)


def _allowed_ips_arg(parser):
  base.Argument(
      '--allowed-ips',
      default=[],
      type=arg_parsers.ArgList(),
      metavar='ALLOWED_IPS',
      help='A list of the caller IP addresses that are allowed to make API '
      'calls with this key.').AddToParser(parser)


def _allowed_bundle_ids(parser):
  base.Argument(
      '--allowed-bundle-ids',
      default=[],
      metavar='ALLOWED_BUNDLE_IDS',
      type=arg_parsers.ArgList(),
      help='iOS app\'s bundle ids that are allowed to use the key.'
  ).AddToParser(parser)


def _allowed_application(parser):
  base.Argument(
      '--allowed-application',
      type=arg_parsers.ArgDict(
          spec={
              'sha1_fingerprint': str,
              'package_name': str
          },
          required_keys=['sha1_fingerprint', 'package_name'],
          max_length=2),
      metavar='sha1_fingerprint=SHA1_FINGERPRINT,package_name=PACKAGE_NAME',
      action='append',
      help=('Repeatable. Specify multiple allowed applications. '
            'The accepted keys are `sha1_fingerprint` and `package_name`.'
           )).AddToParser(parser)


def _annotations(parser):
  base.Argument(
      '--annotations',
      metavar='KEY=VALUE',
      type=arg_parsers.ArgDict(),
      required=False,
      help=("""Annotations are key resource. Specify annotations as
            a key-value dictionary for small amounts of arbitrary client data.
            """)).AddToParser(parser)


def _api_targets_arg(parser):
  base.Argument(
      '--api-target',
      type=arg_parsers.ArgDict(
          spec={
              'service': str,
              'methods': list
          },
          required_keys=['service'],
          min_length=1),
      metavar='service=SERVICE',
      action='append',
      help="""\
      Repeatable. Specify service and optionally one or multiple specific
      methods. Both fields are case insensitive.
      If you need to specify methods, it should be specified
      with the `--flags-file`. See $ gcloud topic flags-file for details.
      See the examples section for how to use `--api-target` in
      `--flags-file`.""").AddToParser(parser)


def _key_string_flag(parser):
  base.Argument('--key-string', help='Key String of the key.').AddToParser(
      parser
  )


def _project_id_flag(parser):
  base.Argument(
      '--project',
      metavar='PROJECT_ID',
      help="""\
The Google Cloud project ID to use for this invocation. If
omitted, then the current project is assumed; the current project can
be listed using `gcloud config list --format='text(core.project)'`
and can be set using `gcloud config set project PROJECTID`.

`--project` and its fallback `{core_project}` property play two roles
in the invocation. It specifies the project of the resource to
operate on. It also specifies the project for API enablement check,
quota, and billing. To specify a different project for quota and
billing, use `--billing-project` or `{billing_project}` property.
    """.format(
          core_project=properties.VALUES.core.project,
          billing_project=properties.VALUES.billing.quota_project,
      ),
  ).AddToParser(parser)


def _folder_id_flag(parser):
  base.Argument(
      '--folder',
      metavar='FOLDER_ID',
      help='The Google Cloud Platform folder ID to use for this invocation.',
  ).AddToParser(parser)


def _orgnaization_id_flag(parser):
  base.Argument(
      '--organization',
      metavar='ORGANIZATION_ID',
      help=(
          'The Google Cloud Platform organization ID to use for this'
          ' invocation.'
      ),
  ).AddToParser(parser)
