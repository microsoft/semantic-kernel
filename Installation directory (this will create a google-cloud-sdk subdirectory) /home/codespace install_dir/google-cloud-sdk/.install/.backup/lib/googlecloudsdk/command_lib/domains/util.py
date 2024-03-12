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
"""General utilties for Cloud Domains commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import re

from apitools.base.py import encoding

from googlecloudsdk.api_lib.domains import operations
from googlecloudsdk.api_lib.domains import registrations
from googlecloudsdk.command_lib.domains import flags
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources
from googlecloudsdk.core import yaml
from googlecloudsdk.core.console import console_io
from googlecloudsdk.core.util import files

LOCATIONS_COLLECTION = 'domains.projects.locations'
OPERATIONS_COLLECTION = 'domains.projects.locations.operations'
REGISTRATIONS_COLLECTION = 'domains.projects.locations.registrations'
_PROJECT = lambda: properties.VALUES.core.project.Get(required=True)
_MAX_LIST_BATCH_SIZE = 200


def RegistrationsUriFunc(api_version):
  def UriFunc(resource):
    return ParseRegistration(api_version, resource.name).SelfLink()
  return UriFunc


def AssertRegistrationOperational(api_version, registration):
  messages = registrations.GetMessagesModule(api_version)

  if registration.state not in [
      messages.Registration.StateValueValuesEnum.ACTIVE,
      messages.Registration.StateValueValuesEnum.SUSPENDED
  ]:
    raise exceptions.Error(
        'The registration resource must be in state ACTIVE or SUSPENDED, '
        'not \'{}\'.'.format(registration.state))


def ParseMessageFromYamlFile(path, message_type, error_message):
  """Parse a Yaml file.

  Args:
    path: Yaml file path. If path is None returns None.
    message_type: Message type to parse YAML into.
    error_message: Error message to print in case of parsing error.

  Returns:
    parsed message of type message_type.
  """
  if path is None:
    return None
  raw_message = yaml.load_path(path)
  try:
    parsed_message = encoding.PyValueToMessage(message_type, raw_message)
  except Exception as e:
    # This error may be slightly different in Py2 and Py3.
    raise exceptions.Error('{}: {}'.format(error_message, e))

  unknown_fields = []
  for message in encoding.UnrecognizedFieldIter(parsed_message):
    outer_message = ''.join([edge.field + '.' for edge in message[0]])
    unknown_fields += [outer_message + field for field in message[1]]
  unknown_fields.sort()
  if unknown_fields:
    raise exceptions.Error(
        ('{}.\nProblematic fields: \'{}\'').format(error_message,
                                                   ', '.join(unknown_fields)))

  return parsed_message


def NormalizeResourceName(domain):
  """Normalizes domain name in resource name."""
  parts = domain.split('/')
  parts[-1] = NormalizeDomainName(parts[-1])
  return '/'.join(parts)


def NormalizeDomainName(domain):
  """Normalizes domain name (including punycoding)."""
  if not domain:
    raise exceptions.Error('Empty domain name')
  try:
    normalized = domain.encode('idna').decode()  # To Punycode
    normalized = normalized.lower().rstrip('.')
  except UnicodeError as e:
    raise exceptions.Error('Invalid domain name \'{}\': {}.'.format(domain, e))
  return normalized


def PunycodeToUnicode(domain):
  return domain.encode('utf-8').decode('idna')


def ValidateDomainName(domain):
  if not domain:
    return False
  # Replace with some library function for FQDN validation.
  pattern = r'^[a-z0-9-]+(\.[a-z0-9-]+)+\.{0,1}$'
  if not re.match(pattern, domain) or '..' in domain:
    return False
  return True


def ValidateNonEmpty(s):
  return s is not None and bool(s.strip())


def ValidateRegionCode(rc):
  return rc is not None and len(rc) == 2 and rc.isalpha() and rc.isupper()


def ValidateEmail(email):
  if not email:
    return False
  # Replace with some library function for email validation.
  pattern = r'^[^@\s]+@[^@\s]+\.[^@\s]+$'
  return bool(re.match(pattern, email))


def Prompt(prompt_string, message=None):
  """Prompt for user input.

  Args:
    prompt_string: Message to print in the line with prompt.
    message: Optional message to print before prompt.

  Returns:
    User provided value.
  """
  if message:
    log.status.Print(message)
  return console_io.PromptResponse(prompt_string)


def PromptWithValidator(prompt_string,
                        validator,
                        error_message,
                        message=None,
                        default=None):
  """Prompt for user input and validate output.

  Args:
    prompt_string: Message to print in the line with prompt.
    validator: Validation function (str) -> bool.
    error_message: Message to print if provided value is not correct.
    message: Optional message to print before prompt.
    default: Optional default value.

  Returns:
    Valid user provided value or default if not None and user chose it.
  """
  if message:
    log.status.Print(message)
  while True:
    if default is not None:
      answer = console_io.PromptWithDefault(
          message=prompt_string, default=default)
      if not answer:
        return default
    else:
      answer = console_io.PromptResponse(prompt_string)
    if validator(answer):
      return answer
    else:
      log.status.Print(error_message)


def GetRegistry(api_version):
  registry = resources.REGISTRY.Clone()
  registry.RegisterApiByName('domains', api_version)
  return registry


def ParseRegistration(api_version, registration):
  return GetRegistry(api_version).Parse(
      registration,
      params={
          'projectsId': _PROJECT,
          'locationsId': 'global'
      },
      collection=REGISTRATIONS_COLLECTION)


def ParseOperation(api_version, operation):
  return GetRegistry(api_version).Parse(
      operation,
      params={
          'projectsId': _PROJECT,
          'locationsId': 'global'
      },
      collection=OPERATIONS_COLLECTION)


def DomainNamespace(domain):
  # Return everything after the first encountered dot.
  # This is needed to accommodate two-level domains like .co.uk.
  return domain[domain.find('.'):]


def ParseTransferLockState(api_version, transfer_lock_state):
  messages = registrations.GetMessagesModule(api_version)
  if transfer_lock_state is None:
    return None
  return flags.TransferLockEnumMapper(messages).GetEnumForChoice(
      transfer_lock_state)


def PromptForEnum(enum_mapper, enum_type, current_value):
  """Prompts the user for the new enum_type value.

  Args:
    enum_mapper: Instance of the EnumMapper.
    enum_type: A string with enum type name to print.
    current_value: Current value of the enum.

  Returns:
    The new enum choice or None if the enum shouldn't be updated.
  """
  options = list(enum_mapper.choices)
  update = console_io.PromptContinue(
      f'Your current {enum_type} is: {current_value}.',
      'Do you want to change it',
      default=False,
  )
  if not update:
    return None

  current_choice = 0
  for i, enum in enumerate(options):
    if enum == enum_mapper.GetChoiceForEnum(current_value):
      current_choice = i
  index = console_io.PromptChoice(
      options=options,
      default=current_choice,
      message=f'Specify new {enum_type}',
  )
  return options[index]


def PromptForTransferLockState(api_version, transfer_lock):
  """Prompts the user for new transfer lock state."""
  messages = registrations.GetMessagesModule(api_version)
  enum_mapper = flags.TransferLockEnumMapper(messages)
  result = PromptForEnum(enum_mapper, 'Transfer Lock state', transfer_lock)
  if result is None:
    return None
  return ParseTransferLockState(api_version, result)


def ParseRenewalMethod(api_version, renewal_method):
  messages = registrations.GetMessagesModule(api_version)
  if renewal_method is None:
    return None
  return flags.RenewalMethodEnumMapper(messages).GetEnumForChoice(
      renewal_method
  )


def PromptForRenewalMethod(api_version, preferred_renewal_method):
  """Prompts the user for new renewal method."""
  messages = registrations.GetMessagesModule(api_version)
  enum_mapper = flags.RenewalMethodEnumMapper(messages)
  result = PromptForEnum(
      enum_mapper, 'preferred Renewal Method', preferred_renewal_method
  )
  if result is None:
    return None
  return ParseRenewalMethod(api_version, result)


def PromptForAuthCode():
  """Prompts the user to enter the auth code."""
  message = ('Please provide the authorization code from the domain\'s current '
             'registrar to transfer the domain.')

  log.status.Print(message)
  auth_code = console_io.PromptPassword(
      prompt='Authorization code:  ',
      error_message=' Authorization code must not be empty.',
      validation_callable=ValidateNonEmpty)
  return auth_code


def TransformMoneyType(r):
  if r is None:
    return None
  dr = r
  if not isinstance(dr, dict):
    dr = encoding.MessageToDict(r)
  return '{}.{:02d} {}'.format(dr['units'], int(dr.get('nanos', 0) / (10**7)),
                               dr.get('currencyCode', ''))


def _ParseMoney(money):
  """Parses money string as tuple (units, cents, currency)."""
  match = re.match(r'^(\d+|\d+\.\d{2})\s*([A-Z]{3})$', money)
  if match:
    number, s = match.groups()
  else:
    raise ValueError('Value could not be parsed as number + currency code')
  if '.' in number:
    index = number.find('.')
    return int(number[:index]), int(number[index + 1:]), s
  else:
    return int(number), 0, s


def ParseYearlyPrice(api_version, price_string):
  """Parses money string as type Money."""
  if not price_string:
    return None
  try:
    units, cents, currency = _ParseMoney(price_string)
  except ValueError:
    raise exceptions.Error(
        (
            f"Yearly price '{price_string}' is invalid. Please specify the"
            ' amount followed by the currency code.'
        )
    )

  if currency == '$':
    currency = 'USD'

  messages = registrations.GetMessagesModule(api_version)
  return messages.Money(
      units=int(units), nanos=cents * 10**7, currencyCode=currency)


def EqualPrice(x, y):
  if x.nanos is None:
    x.nanos = 0
  if y.nanos is None:
    y.nanos = 0
  return x == y


def PromptForYearlyPriceAck(price):
  """Asks the user to accept the yearly price."""
  ack = console_io.PromptContinue(
      'Yearly price: {}\n'.format(TransformMoneyType(price)),
      prompt_string='Do you agree to pay this yearly price for your domain',
      throw_if_unattended=True,
      cancel_on_no=True,
      default=False)
  if ack:
    return price
  else:
    return None


def ParseRegisterNotices(notices):
  """Parses registration notices.

  Args:
    notices: list of notices (lowercase-strings).

  Returns:
    Pair (public privacy ack: bool, hsts ack: bool).
  """
  if not notices:
    return False, False
  return 'public-contact-data-acknowledgement' in notices, 'hsts-preloaded' in notices


def PromptForHSTSAck(domain):
  ack = console_io.PromptContinue(
      ('{} is a secure namespace. You may purchase {} now but it will '
       'require an SSL certificate for website connection.').format(
           DomainNamespace(domain), domain),
      throw_if_unattended=True,
      cancel_on_no=True,
      default=False)
  return ack


def WaitForOperation(api_version, response, asynchronous):
  """Handles waiting for the operation and printing information about it.

  Args:
    api_version: Cloud Domains API version to call.
    response: Response from the API call
    asynchronous: If true, do not wait for the operation

  Returns:
    The last information about the operation.
  """
  operation_ref = ParseOperation(api_version, response.name)
  if asynchronous:
    log.status.Print('Started \'{}\''.format(operation_ref.Name()))
  else:
    message = 'Waiting for \'{}\' to complete'
    operations_client = operations.Client.FromApiVersion(api_version)
    response = operations_client.WaitForOperation(
        operation_ref, message.format(operation_ref.Name()))
  return response


def ReadFileContents(path):
  """Reads the text contents from the given path.

  Args:
    path: str, The file path to read.

  Raises:
    Error: If the file cannot be read.

  Returns:
    str, The text string read from the file.
  """
  if not path:
    return None
  return files.ReadFileContents(path)


def GetListBatchSize(args):
  """Returns the batch size for listing resources."""
  if args.page_size:
    return args.page_size
  elif args.limit:
    return min(args.limit, _MAX_LIST_BATCH_SIZE)
  else:
    return None
