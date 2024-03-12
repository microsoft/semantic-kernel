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

from googlecloudsdk.command_lib.storage import storage_url
from googlecloudsdk.command_lib.transfer.appliances import flags


def apply_args_to_appliance(appliance_resource, args):
  """Maps command arguments to appliance resource values.

  Args:
    appliance_resource (messages.Appliance): The target appliance resource.
    args (parser_extensions.Namespace): The args from the command.

  Returns:
    List[str] A list of strings representing the update mask.
  """
  update_mask = []
  if args.model is not None:
    appliance_resource.model = getattr(flags.APPLIANCE_MODEL_ENUM, args.model)
    update_mask.append('model')

  # Using IsSpecified here ensures we can clear these fields with an empty
  # string.
  if args.IsSpecified('display_name'):
    appliance_resource.displayName = args.display_name
    update_mask.append('displayName')

  if args.IsSpecified('cmek'):
    appliance_resource.customerManagedKey = args.cmek
    update_mask.append('customerManagedKey')

  # We use hasattr() because the --internet-enabled flag is only available to
  # the create command.
  if hasattr(args, 'internet_enabled'):
    appliance_resource.internetEnabled = args.internet_enabled

  if args.offline_import is not None:
    destination = _get_gcs_destination_from_url_string(args.offline_import)
    appliance_resource.offlineImportFeature = destination
    update_mask.append('offlineImportFeature')

  if args.online_import is not None:
    destination = _get_gcs_destination_from_url_string(args.online_import)
    appliance_resource.onlineImportFeature = destination
    update_mask.append('onlineImportFeature')

  if args.offline_export is not None:
    offline_export = {'source': []}
    source = args.offline_export.get('source', None)
    manifest = args.offline_export.get('manifest', None)
    if source is not None:
      bucket, path = _get_bucket_folder_from_url_string(source)
      offline_export['source'].append({'bucket': '{}/{}'.format(bucket, path)})
    if manifest is not None:
      offline_export['transferManifest'] = {'location': manifest}
    appliance_resource.offlineExportFeature = offline_export
    update_mask.append('offlineExportFeature')

  return ','.join(update_mask)


def _apply_args_to_order_contact(contact_field):
  """Maps command arguments to order contact values."""
  emails = contact_field.get('emails', [])
  return {
      'email': emails.pop(0),
      'additionalEmails': emails,
      'business': contact_field.get('business', None),
      'contactName': contact_field.get('name', None),
      'phone': contact_field.get('phone', None)
  }


def apply_args_to_order(order_resource, args, appliance_name=None):
  """Maps command arguments to appliance resource values.

  Args:
    order_resource (messages.Order): The target order resource.
    args (parser_extensions.Namespace): The args from the command.
    appliance_name (str): The name of the appliance associated with the order.

  Returns:
    List['field1', 'field2']
  """
  update_mask = []
  # Using IsSpecified here ensures we can clear these fields.
  if args.IsSpecified('delivery_notes'):
    order_resource.deliveryNotes = args.delivery_notes
    update_mask.append('deliveryNotes')

  if args.IsSpecified('display_name'):
    order_resource.displayName = args.display_name
    update_mask.append('displayName')

  if appliance_name is not None:
    order_resource.appliances = [appliance_name]

  if args.address is not None:
    order_resource.address = {
        'addressLines': args.address.get('lines', None),
        'locality': args.address.get('locality', None),
        'administrativeArea': args.address.get('administrative-area', None),
        'postalCode': args.address.get('postal-code', None),
        'regionCode': _get_region_code(order_resource, args),
    }
    update_mask.append('address')

  if args.order_contact is not None:
    order_resource.orderContact = _apply_args_to_order_contact(
        args.order_contact)
    update_mask.append('orderContact')

  if args.shipping_contact is not None:
    order_resource.shippingContact = _apply_args_to_order_contact(
        args.shipping_contact)
    update_mask.append('shippingContact')

  return ','.join(update_mask)


def _get_region_code(order_resource, args):
  """Get region code either from the country arg or the previous value."""
  # The create command requires country, but its immutable and therefore isn't
  # available on the update command.
  if hasattr(args, 'country'):
    return args.country
  # The update command will be able to use the code from the previous address.
  return order_resource.address.regionCode


def _get_bucket_folder_from_url_string(url_string):
  """Takes a storage_url string and returns a tuple of bucket and folder."""
  url = storage_url.storage_url_from_string(url_string)
  bucket = url.bucket_name
  folder = url.object_name
  if folder is not None and not folder.endswith('/'):
    folder += '/'
  return bucket, folder


def _get_gcs_destination_from_url_string(url_string):
  """Takes a storage_url string and returns a GcsDestination."""
  bucket, folder = _get_bucket_folder_from_url_string(url_string)
  return {
      'destination': {
          'outputBucket': bucket,
          'outputPath': folder,
      }
  }
