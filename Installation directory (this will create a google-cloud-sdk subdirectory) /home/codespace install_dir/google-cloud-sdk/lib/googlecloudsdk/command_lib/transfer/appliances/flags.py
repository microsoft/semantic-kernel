# -*- coding: utf-8 -*- #
# Copyright 2023 Google LLC. All Rights Reserved.
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
"""Utils for transfer appliances commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.command_lib.transfer.appliances import regions


_MESSAGES = apis.GetMessagesModule('transferappliance', 'v1alpha1')
APPLIANCE_MODEL_ENUM = _MESSAGES.Appliance.ModelValueValuesEnum
_APPLIANCE_STATE_ENUM = _MESSAGES.Appliance.StateValueValuesEnum
_ORDER_STATE_ENUM = _MESSAGES.Order.StateValueValuesEnum
# We skip the first enum value, TYPE_UNSPECIFIED, in each case.
_APPLIANCE_MODELS = [e.name for e in APPLIANCE_MODEL_ENUM][1:]
_APPLIANCE_STATES = [e.name for e in _APPLIANCE_STATE_ENUM][1:]
_ORDER_STATES = [e.name for e in _ORDER_STATE_ENUM][1:]

_ADDRESS_HELP = """\
    Address where the appliance will be shipped. All fields (or list items)
    have a maximum of 80 characters. For more information see
    https://support.google.com/business/answer/6397478.

    *lines*::: Line of the postal address that doesn't fit in the other
    fields. For most countries/regions, the first line will include a street
    number and street name. You can have up to 5 address lines.

    *locality*::: Generally refers to the city/town portion of the address.

    *administrative_area*::: The state or province where the business is
    located. Enter the full name (e.g. "California"), common postal
    abbreviation (e.g. "CA"), or subdivision (ISO 3166-2) code
    (e.g. "US-CA").

    *postal_code*::: The postal code of the address.
    """
_CONTACT_HELP = """\
    *business*::: Name of the business, if applicable.

    *name*::: Name of the primary contact.

    *phone*::: The phone number of the primary contact. Should be given in E.164
    format consisting of the country calling code (1 to 3 digits) and the
    subscriber number, with no additional spaces or formatting, e.g.
    `15552220123`.

    *emails*::: The email of the primary contact along with any additional email
    addresses to include with all correspondence.
    """
_OFFLINE_EXPORT_HELP = """\
    Configuration for an offline export transfer, where data is downloaded onto
    the appliance at Google and copied from the appliance at the customer site.

    *source*::: The Cloud Storage bucket or folder where the data is located,
    in the form of `gs://my-bucket/path/to/folder/`.

    *manifest*::: Specifies the path to the manifest in Cloud Storage.
    An example path is `gs://bucket_name/path/manifest.csv`. The paths in
    the manifest file are relative to bucketname. For example, to export
    `SOURCE_PATH/object1.pdf`, manifest will have `object1.pdf` in the first
    column, followed by object version (optional). For more information see
    https://cloud.google.com/storage-transfer/docs/manifest#object_storage_transfers.
    """


def add_appliance_settings(parser, for_create_command=True):
  """Adds appliance flags for appliances orders create."""
  appliance_settings = parser.add_group(category='APPLIANCE')
  appliance_settings.add_argument(
      '--model',
      choices=_APPLIANCE_MODELS,
      required=for_create_command,
      type=str.upper,
      help='Model of the appliance to order.',
  )
  appliance_settings.add_argument(
      '--display-name',
      help='A mutable, user-settable name for both the appliance and the order.'
  )
  if for_create_command:
    appliance_settings.add_argument(
        '--internet-enabled',
        action='store_true',
        help=(
            'Gives the option to put the appliance into online mode,'
            ' allowing it to transfer data and/or remotely report progress to'
            ' the cloud over the network. When disabled only offline'
            ' transfers are possible.'
        ),
    )
  appliance_settings.add_argument(
      '--cmek',
      help=(
          'Customer-managed key which will add additional layer of security.'
          ' By default data is encrypted with a Google-managed key.'
      ),
  )
  appliance_settings.add_argument(
      '--online-import',
      help=(
          'Destination for a online import, where data is loaded onto the'
          ' appliance and automatically transferred to Cloud Storage whenever'
          ' it has an internet connection. Should be in the form of'
          ' `gs://my-bucket/path/to/folder/`.'
      ),
  )
  appliance_settings.add_argument(
      '--offline-import',
      help=(
          'Destination for a offline import, where data is loaded onto the'
          ' appliance at the customer site and ingested at Google. Should be in'
          ' the form of `gs://my-bucket/path/to/folder/`.'
      ),
  )
  appliance_settings.add_argument(
      '--offline-export',
      type=arg_parsers.ArgDict(spec={'source': str, 'manifest': str}),
      help=_OFFLINE_EXPORT_HELP,
  )


def add_delivery_information(parser, for_create_command=True):
  """Adds delivery flags for appliances orders create."""
  if for_create_command:
    parser.add_argument(
        '--country',
        choices=regions.APPROVED_COUNTRIES,
        required=True,
        help=(
            'Country where the appliance will be shipped. Note that this cannot'
            ' be changed. To ship the appliance to a different country, clone'
            ' the order instead and set a different country and delivery '
            ' address. To view a complete list of country codes and names see'
            ' https://support.google.com/business/answer/6270107.'
        ),
    )

  delivery_information = parser.add_group(category='DELIVERY')
  delivery_information.add_argument(
      '--address',
      type=arg_parsers.ArgDict(
          spec={
              'lines': arg_parsers.ArgList(max_length=5),
              'locality': str,
              'administrative-area': str,
              'postal-code': str,
          },
          allow_key_only=True,
          required_keys=['lines'],
      ),
      help=_ADDRESS_HELP,
  )
  delivery_information.add_argument(
      '--delivery-notes',
      help=(
          'Add any additional details about your order, such as site details'
          ' and a preference date when the appliance should be delivered.'
      ),
  )
  contact_arg_type = arg_parsers.ArgDict(
      spec={
          'business': str,
          'name': str,
          'phone': str,
          'emails': arg_parsers.ArgList(),
      },
      allow_key_only=True,
      required_keys=['name', 'phone', 'emails'],
  )
  delivery_information.add_argument(
      '--order-contact',
      type=contact_arg_type,
      help=_CONTACT_HELP,
  )
  delivery_information.add_argument(
      '--shipping-contact',
      type=contact_arg_type,
      help=_CONTACT_HELP,
  )
