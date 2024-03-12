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
"""Command line processing utilities for service perimeters."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import encoding
from googlecloudsdk.api_lib.accesscontextmanager import acm_printer
from googlecloudsdk.api_lib.accesscontextmanager import util
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope.concepts import concepts
from googlecloudsdk.command_lib.accesscontextmanager import common
from googlecloudsdk.command_lib.accesscontextmanager import levels
from googlecloudsdk.command_lib.accesscontextmanager import policies
from googlecloudsdk.command_lib.util.apis import arg_utils
from googlecloudsdk.command_lib.util.args import repeated
from googlecloudsdk.command_lib.util.concepts import concept_parsers
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import resources
from googlecloudsdk.core import yaml
import six

REGISTRY = resources.REGISTRY


class ParseError(exceptions.Error):

  def __init__(self, path, reason):
    super(ParseError,
          self).__init__('Issue parsing file [{}]: {}'.format(path, reason))


class InvalidMessageParseError(ParseError):

  def __init__(self, path, reason, message_class):
    valid_fields = [f.name for f in message_class.all_fields()]
    super(InvalidMessageParseError, self).__init__(
        path, ('The YAML-compliant file of messages provided contains errors: '
               '{}\n\n'
               'The objects in this file can contain the fields'
               ' [{}].').format(reason, ', '.join(valid_fields)))


class InvalidFormatError(ParseError):

  def __init__(self, path, reason, message_class):
    valid_fields = [f.name for f in message_class.all_fields()]
    super(InvalidFormatError, self).__init__(
        path, ('Invalid format: {}\n\n'
               'A service perimeter file is a YAML-formatted list of service '
               'perimeters, which are YAML objects with the fields [{}]. For '
               'example:\n\n'
               '- name: my_perimeter\n'
               '  title: My Perimeter\n'
               '  description: Perimeter for foo.\n'
               '  perimeterType: PERIMETER_TYPE_REGULAR\n'
               '  status:\n'
               '    resources:\n'
               '    - projects/0123456789\n'
               '    accessLevels:\n'
               '    - accessPolicies/my_policy/accessLevels/my_level\n'
               '    restrictedServices:\n'
               '    - storage.googleapis.com').format(reason,
                                                      ', '.join(valid_fields)))


def _GetConfig(perimeter_result, dry_run):
  """Returns the appropriate config for a Service Perimeter.

  Args:
    perimeter_result: The perimeter resource.
    dry_run: Whether the requested config is the dry-run config or the enforced
      config.

  Returns:
    Either the 'status' (enforced) or the 'spec' (dry-run) Perimeter config.
  """
  perimeter = perimeter_result.Get()
  if not dry_run:
    if perimeter.status is None:
      perimeter.status = type(perimeter).status.type()
    return perimeter.status
  else:
    if perimeter.spec is None:
      perimeter.spec = type(perimeter).spec.type()
    return perimeter.spec


def _ValidateAllFieldsRecognized(path, conditions):
  unrecognized_fields = set()
  for condition in conditions:
    if condition.all_unrecognized_fields():
      unrecognized_fields.update(condition.all_unrecognized_fields())
  if unrecognized_fields:
    raise InvalidFormatError(
        path,
        'Unrecognized fields: [{}]'.format(', '.join(unrecognized_fields)),
        type(conditions[0]))


def _AddVpcAccessibleServicesFilter(args, req, version):
  """Add the particular service filter message based on specified args."""
  service_restriction_config = None
  allowed_services = None
  enable_restriction = None
  restriction_modified = False
  service_perimeter_config = req.servicePerimeter.status
  if not service_perimeter_config:
    service_perimeter_config = (
        util.GetMessages(version=version).ServicePerimeterConfig)

  if args.IsSpecified('vpc_allowed_services'):
    allowed_services = getattr(args, 'vpc_allowed_services')
    restriction_modified = True

  if args.IsSpecified('enable_vpc_accessible_services'):
    enable_restriction = getattr(args, 'enable_vpc_accessible_services')
    restriction_modified = True

  if restriction_modified:
    service_restriction_config = getattr(service_perimeter_config,
                                         'vpcAccessibleServices')
    if not service_restriction_config:
      service_restriction_config = (
          getattr(util.GetMessages(version=version), 'VpcAccessibleServices'))
    service_restriction_config.allowedServices = allowed_services
    service_restriction_config.enableRestriction = enable_restriction

  setattr(service_perimeter_config, 'vpcAccessibleServices',
          service_restriction_config)
  req.servicePerimeter.status = service_perimeter_config

  return req


def AddVpcAccessibleServicesGA(ref, args, req):
  del ref  # Unused
  return AddVpcAccessibleServices(args, req, 'v1')


def AddVpcAccessibleServicesAlpha(ref, args, req):
  del ref  # Unused
  return AddVpcAccessibleServices(args, req, 'v1alpha')


def AddVpcAccessibleServices(args, req, version=None):
  """Hook to add the VpcAccessibleServices to request."""
  return _AddVpcAccessibleServicesFilter(args, req, version)


def AddAccessLevelsGA(ref, args, req):
  return AddAccessLevelsBase(ref, args, req, version='v1')


def AddAccessLevelsAlpha(ref, args, req):
  return AddAccessLevelsBase(ref, args, req, version='v1alpha')


def AddAccessLevelsBase(ref, args, req, version=None):
  """Hook to add access levels to request."""
  if args.IsSpecified('access_levels'):
    access_levels = []
    for access_level in args.access_levels:
      if access_level.startswith('accessPolicies'):
        access_levels.append(access_level)
      else:
        level_ref = resources.REGISTRY.Create(
            'accesscontextmanager.accessPolicies.accessLevels',
            accessLevelsId=access_level,
            **ref.Parent().AsDict())
        access_levels.append(level_ref.RelativeName())
    service_perimeter_config = req.servicePerimeter.status
    if not service_perimeter_config:
      service_perimeter_config = (
          util.GetMessages(version=version).ServicePerimeterConfig)
    service_perimeter_config.accessLevels = access_levels
    req.servicePerimeter.status = service_perimeter_config
  return req


def AddImplicitUnrestrictedServiceWildcard(ref, args, req):
  """Add wildcard for unrestricted services to message if type is regular.

  Args:
    ref: resources.Resource, the (unused) resource
    args: argparse namespace, the parse arguments
    req: AccesscontextmanagerAccessPoliciesAccessZonesCreateRequest

  Returns:
    The modified request.
  """
  del ref, args  # Unused in AddImplicitServiceWildcard

  m = util.GetMessages(version='v1beta')
  if req.servicePerimeter.perimeterType == (
      m.ServicePerimeter.PerimeterTypeValueValuesEnum.PERIMETER_TYPE_REGULAR):
    service_perimeter_config = req.servicePerimeter.status
    if not service_perimeter_config:
      service_perimeter_config = m.ServicePerimeterConfig
    service_perimeter_config.unrestrictedServices = ['*']
    req.servicePerimeter.status = service_perimeter_config
  return req


def _GetAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='perimeter', help_text='The ID of the service perimeter.')


def _GetResourceSpec():
  return concepts.ResourceSpec(
      'accesscontextmanager.accessPolicies.servicePerimeters',
      resource_name='perimeter',
      accessPoliciesId=policies.GetAttributeConfig(),
      servicePerimetersId=_GetAttributeConfig())


def AddResourceArg(parser, verb):
  """Add a resource argument for a service perimeter.

  NOTE: Must be used only if it's the only resource arg in the command.

  Args:
    parser: the parser for the command.
    verb: str, the verb to describe the resource, such as 'to update'.
  """
  concept_parsers.ConceptParser.ForResource(
      'perimeter',
      _GetResourceSpec(),
      'The service perimeter {}.'.format(verb),
      required=True).AddToParser(parser)


def GetTypeEnumMapper(version=None):
  return arg_utils.ChoiceEnumMapper(
      '--type',
      util.GetMessages(
          version=version).ServicePerimeter.PerimeterTypeValueValuesEnum,
      custom_mappings={
          'PERIMETER_TYPE_REGULAR': 'regular',
          'PERIMETER_TYPE_BRIDGE': 'bridge'
      },
      required=False,
      help_str="""\
          Type of the perimeter.

          A *regular* perimeter allows resources within this service perimeter
          to import and export data amongst themselves. A project may belong to
          at most one regular service perimeter.

          A *bridge* perimeter allows resources in different regular service
          perimeters to import and export data between each other. A project may
          belong to multiple bridge service perimeters (only if it also belongs to a
          regular service perimeter). Both restricted and unrestricted service lists,
          as well as access level lists, must be empty.
          """,
  )


def GetPerimeterTypeEnumForShortName(perimeter_type_short_name, api_version):
  """Returns the PerimeterTypeValueValuesEnum value for the given short name.

  Args:
    perimeter_type_short_name: Either 'regular' or 'bridge'.
    api_version: One of 'v1alpha', 'v1beta', or 'v1'.

  Returns:
    The appropriate value of type PerimeterTypeValueValuesEnum.
  """
  if perimeter_type_short_name is None:
    return None

  return GetTypeEnumMapper(
      version=api_version).GetEnumForChoice(perimeter_type_short_name)


def AddPerimeterUpdateArgs(parser, version=None):
  """Add args for perimeters update command."""
  args = [
      common.GetDescriptionArg('service perimeter'),
      common.GetTitleArg('service perimeter'),
      GetTypeEnumMapper(version=version).choice_arg
  ]
  for arg in args:
    arg.AddToParser(parser)
  _AddResources(parser)
  _AddRestrictedServices(parser)
  _AddLevelsUpdate(parser)
  _AddVpcRestrictionArgs(parser)
  AddUpdateDirectionalPoliciesGroupArgs(parser, version)


def AddUpdateDirectionalPoliciesGroupArgs(parser, version=None):
  _AddUpdateIngressPoliciesGroupArgs(parser, version)
  _AddUpdateEgressPoliciesGroupArgs(parser, version)


def AddPerimeterUpdateDryRunConfigArgs(parser):
  """Add args for perimeters update-dry-run-config command."""
  # The fields 'description', 'title', 'perimeter_type' are not editable through
  # the dry-run process.
  update_dry_run_group = parser.add_mutually_exclusive_group()
  _AddClearDryRunConfigArg(update_dry_run_group)
  config_group = update_dry_run_group.add_argument_group()
  _AddResources(config_group, include_set=False)
  _AddRestrictedServices(config_group, include_set=False)
  _AddLevelsUpdate(config_group, include_set=False)
  _AddVpcRestrictionArgs(config_group)


def _AddClearDryRunConfigArg(parser):
  arg = base.Argument(
      '--clear',
      action='store_true',
      help='If set, clear all dry run config values on the perimeter and set `dry_run` to `false`.',
  )
  arg.AddToParser(parser)


def _AddResources(parser, include_set=True):
  repeated.AddPrimitiveArgs(
      parser,
      'perimeter',
      'resources',
      'resources',
      additional_help=('Resources must be projects, in the form '
                       '`projects/<projectnumber>`.'),
      include_set=include_set)


def ParseResources(args, perimeter_result, dry_run=False):
  return repeated.ParsePrimitiveArgs(
      args, 'resources',
      lambda: _GetConfig(perimeter_result, dry_run).resources)


def _AddRestrictedServices(parser, include_set=True):
  repeated.AddPrimitiveArgs(
      parser,
      'perimeter',
      'restricted-services',
      'restricted services',
      metavar='SERVICE',
      additional_help=(
          'The perimeter boundary DOES apply to these services (for example, '
          '`storage.googleapis.com`).'),
      include_set=include_set)


def ParseRestrictedServices(args, perimeter_result, dry_run=False):
  return repeated.ParsePrimitiveArgs(
      args, 'restricted_services',
      lambda: _GetConfig(perimeter_result, dry_run).restrictedServices)


# Checks if the service filter  has an update argument specified in
# args.
def _IsServiceFilterUpdateSpecified(args):
  # We leave out the deprecated 'set' arg
  list_command_prefixes = ['remove_', 'add_', 'clear_']
  list_name = 'vpc_allowed_services'
  list_args = [command + list_name for command in list_command_prefixes]

  switch_name = 'enable_vpc_accessible_services'
  return any([args.IsSpecified(arg) for arg in list_args + [switch_name]])


def _AddVpcAccessibleServicesArgs(parser, list_help, enable_help):
  """Add to the parser arguments for this service restriction type."""
  group = parser.add_argument_group()
  repeated.AddPrimitiveArgs(
      group,
      'perimeter',
      'vpc-allowed-services',
      'vpc allowed services',
      metavar='VPC_SERVICE',
      include_set=False,
      additional_help=(list_help))
  group.add_argument(
      '--enable-vpc-accessible-services',
      default=None,
      action='store_true',
      help=enable_help)


def _AddUpdateIngressPoliciesGroupArgs(parser, api_version):
  """Add args for set/clear ingress-policies."""
  group_help = ('These flags modify the enforced IngressPolicies of this '
                'ServicePerimeter.')
  group = parser.add_mutually_exclusive_group(group_help)
  set_ingress_policies_help_text = (
      'Path to a file containing a list of Ingress Policies.\n\nThis file '
      'contains a list of YAML-compliant objects representing Ingress Policies'
      ' described in the API reference.\n\nFor more information about the '
      'alpha version, '
      'see:\nhttps://cloud.google.com/access-context-manager/docs/reference/rest/v1alpha/accessPolicies.servicePerimeters\nFor'
      ' more information about non-alpha versions, see: '
      '\nhttps://cloud.google.com/access-context-manager/docs/reference/rest/v1/accessPolicies.servicePerimeters'
  )
  set_ingress_policies_arg = base.Argument(
      '--set-ingress-policies',
      metavar='YAML_FILE',
      help=set_ingress_policies_help_text,
      type=ParseIngressPolicies(api_version))
  clear_ingress_policies_help_text = (
      'Empties existing enforced Ingress Policies.')
  clear_ingress_policies_arg = base.Argument(
      '--clear-ingress-policies',
      help=clear_ingress_policies_help_text,
      action='store_true')
  set_ingress_policies_arg.AddToParser(group)
  clear_ingress_policies_arg.AddToParser(group)


def _AddUpdateEgressPoliciesGroupArgs(parser, api_version):
  """Add args for set/clear egress policies."""
  group_help = ('These flags modify the enforced EgressPolicies of this '
                'ServicePerimeter.')
  group = parser.add_mutually_exclusive_group(group_help)
  set_egress_policies_help_text = (
      'Path to a file containing a list of Egress Policies.\n\nThis file '
      'contains a list of YAML-compliant objects representing Egress Policies '
      'described in the API reference.\n\nFor more information about the alpha'
      ' version, '
      'see:\nhttps://cloud.google.com/access-context-manager/docs/reference/rest/v1alpha/accessPolicies.servicePerimeters\nFor'
      ' more information about non-alpha versions, see: '
      '\nhttps://cloud.google.com/access-context-manager/docs/reference/rest/v1/accessPolicies.servicePerimeters'
  )
  set_egress_policies_arg = base.Argument(
      '--set-egress-policies',
      metavar='YAML_FILE',
      help=set_egress_policies_help_text,
      type=ParseEgressPolicies(api_version))
  clear_egress_policies_help_text = (
      'Empties existing enforced Egress Policies.')
  clear_egress_policies_arg = base.Argument(
      '--clear-egress-policies',
      help=clear_egress_policies_help_text,
      action='store_true')
  set_egress_policies_arg.AddToParser(group)
  clear_egress_policies_arg.AddToParser(group)


def ParseUpdateDirectionalPoliciesArgs(args, arg_name):
  """Return values for clear_/set_ ingress/egress-policies command line args."""
  underscored_name = arg_name.replace('-', '_')
  clear = getattr(args, 'clear_' + underscored_name)
  set_ = getattr(args, 'set_' + underscored_name, None)

  if clear:
    return []
  elif set_ is not None:
    return set_
  else:
    return None


def ParseVpcRestriction(args, perimeter_result, version, dry_run=False):
  """Parse service restriction related arguments."""
  if _IsServiceFilterUpdateSpecified(args):
    # If there is no service restriction message in the request, make an empty
    # one to populate.
    config = _GetConfig(perimeter_result, dry_run)
    if getattr(config, 'vpcAccessibleServices', None) is None:
      restriction_message = getattr(
          apis.GetMessagesModule('accesscontextmanager', version),
          'VpcAccessibleServices')()
      setattr(config, 'vpcAccessibleServices', restriction_message)

  def FetchAllowed():
    return getattr(
        _GetConfig(perimeter_result, dry_run),
        'vpcAccessibleServices').allowedServices

  return repeated.ParsePrimitiveArgs(args, 'vpc_allowed_services', FetchAllowed)


def _AddVpcRestrictionArgs(parser):
  """Add arguments related to the VPC Accessible Services to 'parser'."""
  _AddVpcAccessibleServicesArgs(
      parser=parser,
      list_help='Services allowed to be called within the Perimeter when '
      'VPC Accessible Services is enabled',
      enable_help=('When specified restrict API calls within the Service '
                   'Perimeter to the set of vpc allowed services. To disable '
                   'use \'--no-enable-vpc-accessible-services\'.'))


def _AddLevelsUpdate(parser, include_set=True):
  repeated.AddPrimitiveArgs(
      parser,
      'perimeter',
      'access-levels',
      'access levels',
      metavar='LEVEL',
      additional_help=(
          'An intra-perimeter request must satisfy these access levels (for '
          'example, `MY_LEVEL`; must be in the same access policy as this '
          'perimeter) to be allowed.'),
      include_set=include_set)


def _GetLevelIdFromLevelName(level_name):
  return REGISTRY.Parse(level_name, collection=levels.COLLECTION).accessLevelsId


def ExpandLevelNamesIfNecessary(level_ids, policy_id):
  """Returns the FULL Access Level names, prepending Policy ID if necessary."""
  if level_ids is None:
    return None
  final_level_ids = []
  for l in level_ids:
    if l.startswith('accessPolicies/'):
      final_level_ids.append(l)
    else:
      final_level_ids.append(
          REGISTRY.Create(
              levels.COLLECTION, accessPoliciesId=policy_id, accessLevelsId=l))
  return final_level_ids


def ParseLevels(args, perimeter_result, policy_id, dry_run=False):
  """Process repeated level changes."""

  def GetLevelIds():
    return [
        _GetLevelIdFromLevelName(l)
        for l in _GetConfig(perimeter_result, dry_run).accessLevels
    ]

  level_ids = repeated.ParsePrimitiveArgs(args, 'access_levels', GetLevelIds)
  return ExpandLevelNamesIfNecessary(level_ids, policy_id)


def ParseIngressPolicies(api_version):

  def ParseVersionedIngressPolicies(path):
    return ParseAccessContextManagerMessages(
        path,
        util.GetMessages(version=api_version).IngressPolicy)

  return ParseVersionedIngressPolicies


def ParseEgressPolicies(api_version):

  def ParseVersionedEgressPolicies(path):
    return ParseAccessContextManagerMessages(
        path,
        util.GetMessages(version=api_version).EgressPolicy)

  return ParseVersionedEgressPolicies


def ParseAccessContextManagerMessages(path, message_class):
  """Parse a YAML representation of a list of messages.

  Args:
    path: str, path to file containing Ingress/Egress Policies
    message_class: obj, message type to parse the contents of the yaml file to

  Returns:
    list of message objects.

  Raises:
    ParseError: if the file could not be read into the proper object
  """

  data = yaml.load_path(path)
  if not data:
    raise ParseError(path, 'File is empty')
  try:
    messages = [encoding.DictToMessage(c, message_class) for c in data]
  except Exception as err:
    raise InvalidMessageParseError(path, six.text_type(err), message_class)

  _ValidateAllFieldsRecognized(path, messages)
  return messages


def ParseServicePerimetersAlpha(path):
  return ParseServicePerimetersBase(path, version='v1alpha')


def ParseServicePerimetersGA(path):
  return ParseServicePerimetersBase(path, version='v1')


def ParseServicePerimetersBase(path, version=None):
  """Parse a YAML representation of a list of Service Perimeters.

  Args:
    path: str, path to file containing service perimeters
    version: str, api version of ACM to use for proto messages

  Returns:
    list of Service Perimeters objects.

  Raises:
    ParseError: if the file could not be read into the proper object
  """

  data = yaml.load_path(path)
  if not data:
    raise ParseError(path, 'File is empty')

  messages = util.GetMessages(version=version)
  message_class = messages.ServicePerimeter
  try:
    conditions = [encoding.DictToMessage(c, message_class) for c in data]
  except Exception as err:
    raise InvalidFormatError(path, six.text_type(err), message_class)

  _ValidateAllFieldsRecognized(path, conditions)
  return conditions


def ParseReplaceServicePerimetersResponseAlpha(lro, unused_args):
  return ParseReplaceServicePerimetersResponseBase(lro, version='v1alpha')


def ParseReplaceServicePerimetersResponseGA(lro, unused_args):
  return ParseReplaceServicePerimetersResponseBase(lro, version='v1')


def ParseReplaceServicePerimetersResponseBase(lro, version):
  """Parse the Long Running Operation response of the ReplaceServicePerimeters call.

  Args:
    lro: Long Running Operation response of ReplaceServicePerimeters.
    version: version of the API. e.g. 'v1beta', 'v1'.

  Returns:
    The replacement Service Perimeters created by the ReplaceServicePerimeters
    call.

  Raises:
    ParseResponseError: if the response could not be parsed into the proper
    object.
  """
  client = util.GetClient(version=version)
  operation_ref = resources.REGISTRY.Parse(
      lro.name, collection='accesscontextmanager.operations')
  poller = common.BulkAPIOperationPoller(
      client.accessPolicies_servicePerimeters, client.operations, operation_ref)

  return waiter.WaitFor(
      poller, operation_ref,
      'Waiting for Replace Service Perimeters operation [{}]'.format(
          operation_ref.Name()))


def GenerateDryRunConfigDiff(perimeter, api_version):
  """Generates a diff string by comparing status with spec."""
  if perimeter.spec is None and perimeter.useExplicitDryRunSpec:
    return 'This Service Perimeter has been marked for deletion dry-run mode.'
  if perimeter.status is None and perimeter.spec is None:
    return 'This Service Perimeter has no dry-run or enforcement mode config.'
  output = []
  status = perimeter.status
  if not perimeter.useExplicitDryRunSpec:
    spec = status
    output.append('This Service Perimeter does not have an explicit '
                  'dry-run mode configuration. The enforcement config '
                  'will be used as the dry-run mode configuration.')
  else:
    spec = perimeter.spec

  if status is None:
    messages = util.GetMessages(version=api_version)
    status = messages.ServicePerimeterConfig()

  perimeter.status = status
  perimeter.spec = spec

  output.append('  name: {}'.format(perimeter.name[perimeter.name.rfind('/') +
                                                   1:]))
  output.append('  title: {}'.format(perimeter.title))

  output.append('  type: {}'.format(perimeter.perimeterType or
                                    'PERIMETER_TYPE_REGULAR'))

  print('\n'.join(output))
  acm_printer.Print(perimeter, 'diff[format=yaml](status, spec)')
