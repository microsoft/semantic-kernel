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
"""Flags and helpers for the compute interconnects commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import collections

from googlecloudsdk.calliope import actions as calliope_actions
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.command_lib.compute import completers as compute_completers
from googlecloudsdk.command_lib.compute import flags as compute_flags


_INTERCONNECT_TYPE_CHOICES_GA = {
    'DEDICATED': 'Dedicated private interconnect.',
    'PARTNER': 'Partner interconnect. Only available to approved partners.',
}

_INTERCONNECT_TYPE_CHOICES_BETA_AND_ALPHA = {
    'IT_PRIVATE':
        'Dedicated private interconnect. (Warning: IT_PRIVATE is deprecated, '
        'use DEDICATED instead.)',
    'DEDICATED':
        'Dedicated private interconnect.',
    'PARTNER':
        'Partner interconnect. Only available to approved partners.',
}

_LINK_TYPE_CHOICES = {
    'LINK_TYPE_ETHERNET_10G_LR': '10Gbps Ethernet, LR Optics.',
    'LINK_TYPE_ETHERNET_100G_LR': '100Gbps Ethernet, LR Optics.'
}

_REQUESTED_FEATURES_CHOICES = {
    'MACSEC':
        'If specified then the interconnect is created on MACsec capable '
        'hardware ports. If not specified, the interconnect is created on '
        'non-MACsec capable ports first, if available. This parameter can only '
        'be provided during interconnect INSERT and cannot be changed using '
        'interconnect PATCH.'
}


class InterconnectsCompleter(compute_completers.ListCommandCompleter):

  def __init__(self, **kwargs):
    super(InterconnectsCompleter, self).__init__(
        collection='compute.interconnects',
        list_command='compute interconnects list --uri',
        **kwargs)


def InterconnectArgument(required=True, plural=False):
  return compute_flags.ResourceArgument(
      resource_name='interconnect',
      completer=InterconnectsCompleter,
      plural=plural,
      required=required,
      global_collection='compute.interconnects')


def InterconnectArgumentForOtherResource(short_help,
                                         required=True,
                                         detailed_help=None):
  return compute_flags.ResourceArgument(
      name='--interconnect',
      resource_name='interconnect',
      completer=InterconnectsCompleter,
      plural=False,
      required=required,
      global_collection='compute.interconnects',
      short_help=short_help,
      detailed_help=detailed_help)


def GetInterconnectType(messages, interconnect_type_arg):
  """Converts the interconnect type flag to a message enum.

  Args:
    messages: The API messages holder.
    interconnect_type_arg: The interconnect type flag value.

  Returns:
    An InterconnectTypeValueValuesEnum of the flag value, or None if absent.
  """
  if interconnect_type_arg is None:
    return None
  else:
    return messages.Interconnect.InterconnectTypeValueValuesEnum(
        interconnect_type_arg)


def GetLinkType(messages, link_type_arg):
  """Converts the link type flag to a message enum.

  Args:
    messages: The API messages holder.
    link_type_arg: The link type flag value.
  Returns:
    An LinkTypeValueValuesEnum of the flag value, or None if absent.
  """
  if link_type_arg is None:
    return None
  else:
    return messages.Interconnect.LinkTypeValueValuesEnum(link_type_arg)


def GetRequestedFeatures(messages, requested_features_arg):
  """Converts the requested-features flag to a list of message enums.

  Args:
    messages: The API messages holder.
    requested_features_arg: A list of the interconnect feature type flag values.

  Returns:
    A list of RequestedFeaturesValueListEntryValuesEnum values, or None if
    absent.
  """
  if not requested_features_arg:
    return []
  features = list(
      filter(
          None,
          [
              GetRequestedFeature(messages, f)
              for f in requested_features_arg
          ],
      )
  )
  return list(collections.OrderedDict.fromkeys(features))  # Remove duplicates.


def GetRequestedFeature(messages, feature_arg):
  """Converts interconnect feature type flag to a message enum.

  Args:
    messages: The API messages holder.
    feature_arg: The feature type flag value.

  Returns:
    A RequestedFeaturesValueListEntryValuesEnum of the flag value.
  """
  if feature_arg == 'MACSEC':
    return messages.Interconnect.RequestedFeaturesValueListEntryValuesEnum(
        'IF_MACSEC'
    )
  return None


def AddCreateCommonArgs(parser):
  """Adds shared flags for create command to the argparse.ArgumentParser."""
  AddAdminEnabled(parser)
  AddDescription(parser)
  AddCustomerName(parser)
  AddLinkType(parser)
  AddNocContactEmail(parser)
  AddRequestedLinkCount(parser)
  AddRequestedFeatures(parser)


def AddCreateGaArgs(parser):
  """Adds GA flags for create command to the argparse.ArgumentParser."""
  AddCreateCommonArgs(parser)
  AddInterconnectTypeGA(parser)


def AddCreateAlphaBetaArgs(parser):
  """Adds alpha / beta flags for create command to the argparse.ArgumentParser."""
  AddCreateCommonArgs(parser)
  AddInterconnectTypeBetaAndAlpha(parser)


def AddDescription(parser):
  """Adds description flag to the argparse.ArgumentParser."""
  parser.add_argument(
      '--description',
      help='An optional, textual description for the interconnect.')


def AddInterconnectTypeGA(parser):
  """Adds interconnect-type flag to the argparse.ArgumentParser."""
  parser.add_argument(
      '--interconnect-type',
      choices=_INTERCONNECT_TYPE_CHOICES_GA,
      required=True,
      help="""\
      Type of the interconnect.
      """)


def _ShouldShowDeprecatedWarning(value):
  return value and value.upper() == 'IT_PRIVATE'


def AddInterconnectTypeBetaAndAlpha(parser):
  """Adds interconnect-type flag to the argparse.ArgumentParser."""
  parser.add_argument(
      '--interconnect-type',
      choices=_INTERCONNECT_TYPE_CHOICES_BETA_AND_ALPHA,
      action=calliope_actions.DeprecationAction(
          'interconnect-type',
          removed=False,
          show_add_help=False,
          show_message=_ShouldShowDeprecatedWarning,
          warn=('IT_PRIVATE will be deprecated '
                'for {flag_name}. '
                'Please use DEDICATED instead.'),
          error='Value IT_PRIVATE for {flag_name} has been removed. '
                'Please use DEDICATED instead.'),
      required=True,
      help="""\
      Type of the interconnect.
      """)


def AddRequestedFeatures(parser):
  """Adds requested-features flag to the argparse.ArgumentParser."""
  parser.add_argument(
      '--requested-features',
      type=arg_parsers.ArgList(choices=_REQUESTED_FEATURES_CHOICES),
      metavar='FEATURES',
      help="""\
      List of features requested for this interconnect.
      """)


def AddLinkType(parser):
  """Adds link-type flag to the argparse.ArgumentParser."""
  link_types = _LINK_TYPE_CHOICES
  parser.add_argument(
      '--link-type',
      choices=link_types,
      required=True,
      help="""\
      Type of the link for the interconnect.
      """)


def AddRequestedLinkCount(parser):
  """Adds requestedLinkCount flag to the argparse.ArgumentParser."""
  parser.add_argument(
      '--requested-link-count',
      required=True,
      type=int,
      help="""\
      Target number of physical links in the link bundle.
      """)


def AddRequestedLinkCountForUpdate(parser):
  """Adds requestedLinkCount flag to the argparse.ArgumentParser."""
  parser.add_argument(
      '--requested-link-count',
      type=int,
      help="""\
      Target number of physical links in the link bundle.
      """)


def AddNocContactEmail(parser):
  """Adds nocContactEmail flag to the argparse.ArgumentParser."""
  parser.add_argument(
      '--noc-contact-email',
      help="""\
      Email address to contact the customer NOC for operations and maintenance
      notifications regarding this interconnect.
      """)


def AddCustomerName(parser):
  """Adds customerName flag to the argparse.ArgumentParser."""
  parser.add_argument(
      '--customer-name',
      help="""\
    Customer name to put in the Letter of Authorization as the party
    authorized to request an interconnect. This field is required for most
    interconnects, however it is prohibited when creating a Cross-Cloud Interconnect.
    """,
  )


def AddAdminEnabled(parser):
  """Adds adminEnabled flag to the argparse.ArgumentParser."""
  admin_enabled_args = parser.add_mutually_exclusive_group()
  admin_enabled_args.add_argument(
      '--admin-enabled',
      action='store_true',
      default=None,
      help="""\
      Administrative status of the interconnect. If not provided on creation,
      defaults to enabled.
      When this is enabled, the interconnect is operational and will carry
      traffic across any functioning linked interconnect attachments. Use
      --no-admin-enabled to disable it.
      """)


def AddAdminEnabledForUpdate(parser):
  """Adds adminEnabled flag to the argparse.ArgumentParser."""
  admin_enabled_args = parser.add_mutually_exclusive_group()
  admin_enabled_args.add_argument(
      '--admin-enabled',
      action='store_true',
      default=None,
      help="""\
      Administrative status of the interconnect.
      When this is enabled, the interconnect is operational and will carry
      traffic across any functioning linked interconnect attachments. Use
      --no-admin-enabled to disable it.
      """)


def AddMacsecEnabledForUpdate(parser):
  """Adds macsecEnabled flag to the argparse.ArgumentParser."""
  parser.add_argument(
      '--enabled',
      action='store_true',
      default=None,
      help="""\
      Enable or disable MACsec on this Interconnect. MACsec enablement will fail
      if the MACsec configuration is not specified. Use --no-enabled to disable
      it.
      """)


def AddFailOpenForUpdate(parser):
  """Adds failOpen flag to the argparse.ArgumentParser."""
  parser.add_argument(
      '--fail-open',
      action='store_true',
      default=None,
      help="""\
      If enabled, the Interconnect will be configured with a should-secure
      MACsec security policy, that allows the Google router to fallback to
      cleartext traffic if the MKA session cannot be established. By default,
      the Interconnect will be configured with a must-secure security policy
      that drops all traffic if the MKA session cannot be established with your
      router. Use --no-fail-open to disable it.
      """)


def AddMacsecPreSharedKeyNameForAddOrUpdateKey(parser):
  """Adds keyName flag to the argparse.ArgumentParser."""
  parser.add_argument(
      '--key-name',
      required=True,
      help="""\
      A name of pre-shared key being added to MACsec configuration of the
      interconnect. The name must be 1-63 characters long, and comply with
      RFC1035.
      """)


def AddMacsecPreSharedKeyStartTimeForAddOrUpdateKey(parser):
  """Adds keyName flag to the argparse.ArgumentParser."""
  parser.add_argument(
      '--start-time',
      required=False,
      default=None,
      help="""\
      A RFC3339 timestamp on or after which the key is valid. startTime can be
      in the future. If the keychain has a single key, --start-time can be
      omitted. If the keychain has multiple keys, --start-time is mandatory for
      each key. The start times of two consecutive keys must be at least 6 hours
      apart.
      """)


def AddMacsecPreSharedKeyNameForRomoveKey(parser):
  """Adds keyName flag to the argparse.ArgumentParser."""
  parser.add_argument(
      '--key-name',
      required=True,
      help="""\
      The name of pre-shared key being removed from MACsec configuration of the
      interconnect.
      """)
