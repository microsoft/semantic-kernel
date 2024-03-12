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
"""Conversions to translate between legacy YAML and OnePlatform protos."""

from __future__ import absolute_import
import re

# pylint:disable=g-import-not-at-top
try:
  from googlecloudsdk.third_party.appengine.api import dispatchinfo
except ImportError:
  from google.appengine.api import dispatchinfo
try:
  from googlecloudsdk.third_party.appengine.api import appinfo
except ImportError:
  from google.appengine.api import appinfo
# pylint:enable=g-import-not-at-top

_SECONDS_PER_MINUTE = 60
_MILLISECONDS_PER_SECOND = 1000
_NANOSECONDS_PER_SECOND = 1000000000

_COMMON_HANDLER_FIELDS = (
    'urlRegex',
    'login',
    'authFailAction',
    'securityLevel',
    'redirectHttpResponseCode',
)

_SCRIPT_FIELDS = (
    'scriptPath',
)

_HANDLER_FIELDS = {
    'staticFiles': (
        'path',
        'uploadPathRegex',
        'httpHeaders',
        'expiration',
        'applicationReadable',
        'mimeType',
        'requireMatchingFile',
    ),
    'script': _SCRIPT_FIELDS,
    'apiEndpoint': _SCRIPT_FIELDS,
}

_REQUEST_UTILIZATION_SCALING_FIELDS = (
    'targetRequestCountPerSec',
    'targetConcurrentRequests',
    'targetRequestCountPerSecond',
)

_DISK_UTILIZATION_SCALING_FIELDS = (
    'targetWriteBytesPerSec',
    'targetWriteOpsPerSec',
    'targetReadBytesPerSec',
    'targetReadOpsPerSec',
    'targetWriteBytesPerSecond',
    'targetWriteOpsPerSecond',
    'targetReadBytesPerSecond',
    'targetReadOpsPerSecond',
)

_NETWORK_UTILIZATION_SCALING_FIELDS = (
    'targetSentBytesPerSec',
    'targetSentPacketsPerSec',
    'targetReceivedBytesPerSec',
    'targetReceivedPacketsPerSec',
    'targetSentBytesPerSecond',
    'targetSentPacketsPerSecond',
    'targetReceivedBytesPerSecond',
    'targetReceivedPacketsPerSecond',
)

_ENDPOINTS_ROLLOUT_STRATEGY_VALUES = (
    'fixed',
    'managed',
)
(_ENDPOINTS_UNSPECIFIED_ROLLOUT_STRATEGY_ENUM_VALUE
) = 'UNSPECIFIED_ROLLOUT_STRATEGY'

_STANDARD_SCHEDULER_SETTINGS = (
    'maxInstances',
    'minInstances',
    'targetCpuUtilization',
    'targetThroughputUtilization',
)

# Maps VPC egress setting as specified in app.yaml to their proto enum values.
_VPC_EGRESS_SETTING_MAP = {
    'all-traffic': 'ALL_TRAFFIC',
    'private-ranges-only': 'PRIVATE_IP_RANGES'
}

def ToVpcEgressSettingEnum(value):
  """Converts a string to a VPC egress setting."""
  if str(value) not in _VPC_EGRESS_SETTING_MAP:
    raise ValueError('egress_setting must be one of: [%s]' %
                     ','.join(_VPC_EGRESS_SETTING_MAP.keys()))
  return _VPC_EGRESS_SETTING_MAP[str(value)]


def EnumConverter(prefix):
  """Create conversion function which translates from string to enum value.

  Args:
    prefix: Prefix for enum value. Expected to be an upper-cased value.

  Returns:
    A conversion function which translates from string to enum value.

  Raises:
    ValueError: If an invalid prefix (empty, non-upper-cased, etc.) prefix was
    provided.
  """
  if not prefix:
    raise ValueError('A prefix must be provided')
  if prefix != prefix.upper():
    raise ValueError('Upper-cased prefix must be provided')
  if prefix.endswith('_'):
    raise ValueError(
        'Prefix should not contain a trailing underscore: "%s"' % prefix)

  return lambda value: '_'.join([prefix, str(value).upper()])


def Not(value):
  """Convert the given boolean value to the opposite value."""
  if not isinstance(value, bool):
    raise ValueError('Expected a boolean value. Got "%s"' % value)
  return not value


def ToJsonString(value):
  """Coerces a primitive value into a JSON-compatible string.

  Special handling for boolean values, since the Python version (True/False) is
  incompatible with the JSON version (true/false).

  Args:
    value: value to convert.

  Returns:
    Value as a string.

  Raises:
    ValueError: when a non-primitive value is provided.
  """
  if isinstance(value, (list, dict)):
    raise ValueError('Expected a primitive value. Got "%s"' % value)
  if isinstance(value, bool):
    return str(value).lower()
  return str(value)


def ToUpperCaseJsonString(value):
  """Coerces a primitive value into a upper-case JSON-compatible string.

  Special handling for  values whose JSON version is in upper-case.

  Args:
    value: value to convert.

  Returns:
    Value as a string.

  Raises:
    ValueError: when a non-primitive value is provided.
  """
  return str(value).upper()


def StringToInt(handle_automatic=False):
  """Create conversion function which converts from a string to an integer.

  Args:
    handle_automatic: Boolean indicating whether a value of "automatic" should
      be converted to 0.

  Returns:
    A conversion function which converts a string to an integer.
  """
  def Convert(value):
    if value == 'automatic' and handle_automatic:
      return 0
    return int(value)

  return Convert


def SecondsToDuration(value):
  """Convert seconds expressed as integer to a Duration value."""
  return '%ss' % int(value)


def LatencyToDuration(value):
  """Convert valid pending latency argument to a Duration value of seconds.

  Args:
    value: A string in the form X.Xs or XXms.

  Returns:
    Duration value of the given argument.

  Raises:
    ValueError: if the given value isn't parseable.
  """
  if not re.compile(appinfo._PENDING_LATENCY_REGEX).match(value):  # pylint: disable=protected-access
    raise ValueError('Unrecognized latency: %s' % value)
  if value == 'automatic':
    return None
  if value.endswith('ms'):
    return '%ss' % (float(value[:-2]) / _MILLISECONDS_PER_SECOND)
  else:
    return value


def IdleTimeoutToDuration(value):
  """Convert valid idle timeout argument to a Duration value of seconds.

  Args:
    value: A string in the form Xm or Xs

  Returns:
    Duration value of the given argument.

  Raises:
    ValueError: if the given value isn't parseable.
  """
  if not re.compile(appinfo._IDLE_TIMEOUT_REGEX).match(value):  # pylint: disable=protected-access
    raise ValueError('Unrecognized idle timeout: %s' % value)
  if value.endswith('m'):
    return '%ss' % (int(value[:-1]) * _SECONDS_PER_MINUTE)
  else:
    return value


def ExpirationToDuration(value):
  """Convert valid expiration argument to a Duration value of seconds.

  Args:
    value: String that matches _DELTA_REGEX.

  Returns:
    Time delta expressed as a Duration.

  Raises:
    ValueError: if the given value isn't parseable.
  """
  if not re.compile(appinfo._EXPIRATION_REGEX).match(value):  # pylint: disable=protected-access
    raise ValueError('Unrecognized expiration: %s' % value)
  delta = appinfo.ParseExpiration(value)
  return '%ss' % delta


def ConvertAutomaticScaling(automatic_scaling):
  """Moves several VM-specific automatic scaling parameters to submessages.

  For example:
  Input {
    "targetSentPacketsPerSec": 10,
    "targetReadOpsPerSec": 2,
    "targetRequestCountPerSec": 3
  }
  Output {
    "networkUtilization": {
      "targetSentPacketsPerSec": 10
    },
    "diskUtilization": {
      "targetReadOpsPerSec": 2
    },
    "requestUtilization": {
      "targetRequestCountPerSec": 3
    }
  }

  Args:
    automatic_scaling: Result of converting automatic_scaling according to
      schema.
  Returns:
    AutomaticScaling which has moved network/disk utilization related fields to
    submessage.
  """
  def MoveFieldsTo(field_names, target_field_name):
    target = {}
    for field_name in field_names:
      if field_name in automatic_scaling:
        target[field_name] = automatic_scaling[field_name]
        del automatic_scaling[field_name]
    if target:
      automatic_scaling[target_field_name] = target
  MoveFieldsTo(_REQUEST_UTILIZATION_SCALING_FIELDS, 'requestUtilization')
  MoveFieldsTo(_DISK_UTILIZATION_SCALING_FIELDS, 'diskUtilization')
  MoveFieldsTo(_NETWORK_UTILIZATION_SCALING_FIELDS, 'networkUtilization')
  MoveFieldsTo(_STANDARD_SCHEDULER_SETTINGS, 'standardSchedulerSettings')
  return automatic_scaling


def ConvertUrlHandler(handler):
  """Rejiggers the structure of the url handler based on its type.

  An extra level of message nesting occurs here, based on the handler type.
  Fields common to all handler types occur at the top-level, while
  handler-specific fields will go into a submessage based on handler type.

  For example, a static files handler is transformed as follows:
  Input {
    "urlRegex": "foo/bar.html",
    "path": "static_files/foo/bar.html"
  }
  Output {
    "urlRegex": "foo/bar.html",
    "staticFiles": {
      "path": "static_files/foo/bar.html"
    }
  }

  Args:
    handler: Result of converting handler according to schema.

  Returns:
    Handler which has moved fields specific to the handler's type to a
    submessage.
  """

  def AppendRegexToPath(path, regex):
    """Equivalent to os.path.join(), except uses forward slashes always."""
    return path.rstrip('/') + '/' + regex

  handler_type = _GetHandlerType(handler)

  # static_dir is syntactic sugar for static_files, so we "demote" any
  # static_dir directives we see to a static_files directive before
  # continuing.
  if handler_type == 'staticDirectory':
    # Groups are disallowed in URLs for static directory handlers.
    # We check for them using the Python re module. App Engine uses Posix
    # extended regular expressions, but it's overkill to start packaging a
    # library that officially supports Posix extended regular expressions for
    # this simple validation. We just let compile errors slide; Python regular
    # expressions are mostly a superset.
    try:
      compiled = re.compile(handler['urlRegex'])
    except re.error:
      pass  # We'll let the API handle this.
    else:
      if compiled.groups:  # `groups` is the number of groups in the RE
        raise ValueError(
            'Groups are not allowed in URLs for static directory handlers: ' +
            handler['urlRegex'])
    tmp = {
        'path': AppendRegexToPath(handler['staticDir'], r'\1'),
        'uploadPathRegex': AppendRegexToPath(handler['staticDir'], '.*'),
        'urlRegex': AppendRegexToPath(handler['urlRegex'], '(.*)'),
    }
    del handler['staticDir']
    handler.update(tmp)
    handler_type = 'staticFiles'

  new_handler = {}
  new_handler[handler_type] = {}

  for field in _HANDLER_FIELDS[handler_type]:
    if field in handler:
      new_handler[handler_type][field] = handler[field]

  # Copy the common fields
  for common_field in _COMMON_HANDLER_FIELDS:
    if common_field in handler:
      new_handler[common_field] = handler[common_field]

  return new_handler


def ConvertDispatchHandler(handler):
  """Create conversion function which handles dispatch rules.

  Extract domain and path from dispatch url,
  set service value from service or module info.

  Args:
    handler: Result of converting handler according to schema.

  Returns:
    Handler which has 'domain', 'path' and 'service' fields.
  """
  dispatch_url = dispatchinfo.ParsedURL(handler['url'])
  dispatch_service = handler['service']

  dispatch_domain = dispatch_url.host
  if not dispatch_url.host_exact:
    dispatch_domain = '*' + dispatch_domain

  dispatch_path = dispatch_url.path
  if not dispatch_url.path_exact:
    dispatch_path = dispatch_path.rstrip('/') + '/*'

  new_handler = {}
  new_handler['domain'] = dispatch_domain
  new_handler['path'] = dispatch_path
  new_handler['service'] = dispatch_service

  return new_handler


def _GetHandlerType(handler):
  """Get handler type of mapping.

  Args:
    handler: Original handler.

  Returns:
    Handler type determined by which handler id attribute is set.

  Raises:
    ValueError: when none of the handler id attributes are set.
  """
  if 'apiEndpoint' in handler:
    return 'apiEndpoint'
  elif 'staticDir' in handler:
    return 'staticDirectory'
  elif 'path' in handler:
    return 'staticFiles'
  elif 'scriptPath' in handler:
    return 'script'

  raise ValueError('Unrecognized handler type: %s' % handler)


def ConvertEndpointsRolloutStrategyToEnum(value):
  """Converts the rollout strategy to an enum.

  In the YAML file, the user does not use the enum values directly. Therefore we
  must convert these to their corresponding enum values in version.proto.

  Args:
    value: A string that is a valid rollout strategy ("fixed" or "managed")

  Returns:
    Value converted to the proper enum value. Defaults to
    "UNSPECIFIED_ROLLOUT_STRATEGY"

  Raises:
    ValueError: When the value is set and is not one of "fixed" or "managed".
  """
  if value is None:
    return _ENDPOINTS_UNSPECIFIED_ROLLOUT_STRATEGY_ENUM_VALUE
  if value in _ENDPOINTS_ROLLOUT_STRATEGY_VALUES:
    return value.upper()

  raise ValueError('Unrecognized rollout strategy: %s' % value)


def ConvertEntrypoint(entrypoint):
  """Converts the raw entrypoint to a nested shell value.

  In the YAML file, the user specifies an entrypoint value. However, the version
  resource expects it to be nested under a 'shell' key. In addition, Zeus
  always prepends 'exec' to the value provided, so we remove it here as it is
  sometimes added client-side by the validation library.

  Args:
    entrypoint: string, entrypoint value.

  Returns:
    Dict containing entrypoint.
  """
  if entrypoint is None:
    entrypoint = ''
  if entrypoint.startswith('exec '):
    entrypoint = entrypoint[len('exec '):]
  return {'shell': entrypoint}
