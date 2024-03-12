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
"""Base formatter for Cloud Run Integrations."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import abc

from typing import Optional
from googlecloudsdk.api_lib.run.integrations import types_utils
from googlecloudsdk.command_lib.run.integrations.formatters import states
from googlecloudsdk.core import properties
from googlecloudsdk.core.console import console_attr
from googlecloudsdk.core.resource import custom_printer_base as cp
from googlecloudsdk.generated_clients.apis.runapps.v1alpha1 import runapps_v1alpha1_messages as runapps


# Constants used to pick the symbol displayed to the console.
SUCCESS = 'SUCCESS'
UPDATING = 'UPDATING'
FAILED = 'FAILED'
MISSING = 'MISSING'
DEFAULT = 'DEFAULT'

# Constants used to pick the encoding
ASCII = 'ascii'
UTF8 = 'utf8'


class Record(object):
  """Record holds data that is passed around to printers for formatting.

  Attributes:
    name: str, name of the integration
    region: str, GCP region for the integration.
    metadata: the type metadata for the integration.
    resource: the resource of the integration.
    status: dict, application status for the given integration.
    latest_deployment: str, canonical deployment name for the latest deployment
      for the given integration.
  """

  def __init__(
      self,
      name: Optional[str],
      region: Optional[str],
      metadata: Optional[types_utils.TypeMetadata] = None,
      resource: Optional[runapps.Resource] = None,
      status: Optional[runapps.ResourceStatus] = None,
      latest_deployment: runapps.Deployment = None,
  ):
    self.name = name
    self.region = region
    self.metadata = metadata
    self.resource = resource if resource else runapps.Resource()
    self.status = status if status else runapps.ResourceStatus()
    self.latest_deployment = latest_deployment


class BaseFormatter(abc.ABC):
  """Prints the run Integration in a custom human-readable format."""

  @abc.abstractmethod
  def TransformConfig(self, record: Record) -> cp._Marker:
    """Override to describe the format of the config of the integration."""

  @abc.abstractmethod
  def TransformComponentStatus(self, record: Record) -> cp._Marker:
    """Override to describe the format of the components and status of the integration."""

  def CallToAction(self, record: Record) -> Optional[str]:
    """Override to return call to action message.

    Args:
      record: dict, the integration.

    Returns:
      A formatted string of the call to action message,
      or None if no call to action is required.
    """
    del record  # Unused
    return None

  def PrintType(self, ctype):
    """Return the type in a user friendly format.

    Args:
      ctype: the type name to be formatted.

    Returns:
      A formatted string.
    """
    return (ctype
            .replace('google_', '')
            .replace('compute_', '')
            .replace('_', ' ')
            .title())

  def GetResourceState(self, resource):
    """Return the state of the top level resource in the integration.

    Args:
      resource: dict, resource status of the integration resource.

    Returns:
      The state string.
    """
    return resource.get('state', states.UNKNOWN)

  def PrintStatus(self, status):
    """Print the status with symbol and color.

    Args:
      status: string, the status.

    Returns:
      The formatted string.
    """
    return '{} {}'.format(self.StatusSymbolAndColor(status), status)

  def StatusSymbolAndColor(self, status: str) -> str:
    """Return the color symbol for the status.

    Args:
      status: string, the status.

    Returns:
      The symbol string.
    """
    if status == states.DEPLOYED or status == states.ACTIVE:
      return GetSymbol(SUCCESS)
    if status in (states.PROVISIONING, states.UPDATING, states.NOT_READY):
      return GetSymbol(UPDATING)
    if status == states.MISSING:
      return GetSymbol(MISSING)
    if status == states.FAILED:
      return GetSymbol(FAILED)
    return GetSymbol(DEFAULT)


def GetSymbol(status, encoding=None) -> str:
  """Chooses a symbol to be displayed to the console based on the status.

  Args:
    status: str, defined as a constant in this file.  CloudSDK must
      support Python 2 at the moment so we cannot use the actual enum class.
      If the value is not valid or supported then it will return a default
      symbol.

    encoding: str, defined as a constant in this file.  If not provided, the
      encoding will be fetched from the user's console.

  Returns:
    Symbol (str) to be displayed to the console.
  """
  con = console_attr.GetConsoleAttr()
  if encoding is None:
    encoding = _GetEncoding()

  default_symbol = con.Colorize('~', 'blue')
  status_to_symbol = {
      SUCCESS: con.Colorize(
          _PickSymbol('\N{HEAVY CHECK MARK}', '+', encoding), 'green'
      ),
      UPDATING: con.Colorize(
          _PickSymbol('\N{HORIZONTAL ELLIPSIS}', '.', encoding), 'yellow'
      ),
      FAILED: con.Colorize('X', 'red'),
      MISSING: con.Colorize('?', 'yellow'),
      DEFAULT: default_symbol,
  }

  return status_to_symbol.get(status, default_symbol)


def _GetEncoding():
  """Returns the encoding used by the user's console.

  If the user has color disabled, then we will default to ascii.
  """
  if properties.VALUES.core.disable_color.GetBool():
    return ASCII

  return console_attr.GetConsoleAttr().GetEncoding()


def _PickSymbol(best, alt, encoding):
  """Chooses the best symbol (if it's in this encoding) or an alternate.

  Args:
    best: str, the symbol to return if the encoding allows.
    alt: str, alternative to return if best cannot be encoded.
    encoding:  str, possible values are utf8, ascii, and win.

  Returns:
    The symbol string if the encoding allows, otherwise an alternative string.
  """
  try:
    best.encode(encoding)
    return best
  except UnicodeError:
    return alt
