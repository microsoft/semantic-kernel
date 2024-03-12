# Copyright 2007 Google LLC. All Rights Reserved.
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

"""AppInfo tools.

This library allows you to work with AppInfo records in memory, as well as store
and load from configuration files.
"""


# WARNING: This file is externally viewable by our users.  All comments from
# this file will be stripped.  The docstrings will NOT.  Do not put sensitive
# information in docstrings.  If you must communicate internal information in
# this source file, please place them in comments only.

# Parts of the code in this file are duplicated in
# //java/com/google/apphosting/admin/legacy/...
# This is part of an ongoing effort to replace the deployment API.
# Until we can delete this code, please check to see if your changes need
# to be reflected in the java code. For questions, talk to clouser@ or

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
import logging
import os
import re
import string
import sys
import wsgiref.util

# pylint: disable=g-import-not-at-top
if os.environ.get('APPENGINE_RUNTIME') == 'python27':
  from google.appengine.api import validation
  from google.appengine.api import yaml_builder
  from google.appengine.api import yaml_listener
  from google.appengine.api import yaml_object
else:
  # This case covers both Python 2.5 and unittests, which are 2.5 only.
  from googlecloudsdk.third_party.appengine.api import validation
  from googlecloudsdk.third_party.appengine.api import yaml_builder
  from googlecloudsdk.third_party.appengine.api import yaml_listener
  from googlecloudsdk.third_party.appengine.api import yaml_object

from googlecloudsdk.third_party.appengine.api import appinfo_errors
from googlecloudsdk.third_party.appengine.api import backendinfo
from googlecloudsdk.third_party.appengine._internal import six_subset


# pylint: enable=g-import-not-at-top

# Regular expression for matching URL, file, URL root regular expressions.
# `url_root` is identical to url except it additionally imposes not ending with
# *.
# TODO(user): `url_root` should generally allow a URL but not a regex or
# glob.
_URL_REGEX = r'(?!\^)/.*|\..*|(\(.).*(?!\$).'
_FILES_REGEX = r'.+'
_URL_ROOT_REGEX = r'/.*'

# Regular expression for matching cache expiration deltas.
_DELTA_REGEX = r'([0-9]+)([DdHhMm]|[sS]?)'
_EXPIRATION_REGEX = r'\s*(%s)(\s+%s)*\s*' % (_DELTA_REGEX, _DELTA_REGEX)
_START_PATH = '/_ah/start'

_NON_WHITE_SPACE_REGEX = r'^\S+$'

# Regular expression for matching service names.
# TODO(user): this may need altering so as to not leak unreleased service names
# TODO(user): Re-add sms to list of services.
_ALLOWED_SERVICES = ['mail', 'mail_bounce', 'xmpp_message', 'xmpp_subscribe',
                     'xmpp_presence', 'xmpp_error', 'channel_presence', 'rest',
                     'warmup']
_SERVICE_RE_STRING = '(' + '|'.join(_ALLOWED_SERVICES) + ')'

# Regular expression for matching page names.
_PAGE_NAME_REGEX = r'^.+$'

# Constants for interpreting expiration deltas.
_EXPIRATION_CONVERSIONS = {
    'd': 60 * 60 * 24,
    'h': 60 * 60,
    'm': 60,
    's': 1,
}

# Constant values from `apphosting/base/constants.h`
# TODO(user): Maybe a python constants file.
APP_ID_MAX_LEN = 100
MODULE_ID_MAX_LEN = 63
# See b/5485871 for why this is 100 and not 63.
# NOTE(user): See b/5485871 for why this is different from the
# `apphosting/base/constants.h` value.
MODULE_VERSION_ID_MAX_LEN = 63
MAX_URL_MAPS = 100

# The character separating the partition from the domain.
PARTITION_SEPARATOR = '~'

# The character separating the domain from the display-app-id.
DOMAIN_SEPARATOR = ':'

# The character separating major and minor versions.
VERSION_SEPARATOR = '.'

# The character separating module from module version.
MODULE_SEPARATOR = ':'

# The name of the default module
DEFAULT_MODULE = 'default'

# Regular expression for ID types. Defined in apphosting/base/id_util.cc.
PARTITION_RE_STRING_WITHOUT_SEPARATOR = (r'[a-z\d\-]{1,%d}' % APP_ID_MAX_LEN)
PARTITION_RE_STRING = (r'%s\%s' %
                       (PARTITION_RE_STRING_WITHOUT_SEPARATOR,
                        PARTITION_SEPARATOR))
DOMAIN_RE_STRING_WITHOUT_SEPARATOR = (r'(?!\-)[a-z\d\-\.]{1,%d}' %
                                      APP_ID_MAX_LEN)
DOMAIN_RE_STRING = (r'%s%s' %
                    (DOMAIN_RE_STRING_WITHOUT_SEPARATOR, DOMAIN_SEPARATOR))
DISPLAY_APP_ID_RE_STRING = r'(?!-)[a-z\d\-]{0,%d}[a-z\d]' % (APP_ID_MAX_LEN - 1)
APPLICATION_RE_STRING = (r'(?:%s)?(?:%s)?%s' %
                         (PARTITION_RE_STRING,
                          DOMAIN_RE_STRING,
                          DISPLAY_APP_ID_RE_STRING))

# NOTE(user,user): These regexes have been copied to multiple other
# locations in google.apphosting so we don't have to pull this file into
# python_lib for other modules to work in production.
# Other known locations as of 2016-08-15:
# - java/com/google/apphosting/admin/legacy/LegacyAppInfo.java
# - apphosting/client/app_config_old.cc
# - apphosting/api/app_config/app_config_server2.cc
MODULE_ID_RE_STRING = r'^(?!-)[a-z\d\-]{0,%d}[a-z\d]$' % (MODULE_ID_MAX_LEN - 1)
MODULE_VERSION_ID_RE_STRING = (r'^(?!-)[a-z\d\-]{0,%d}[a-z\d]$' %
                               (MODULE_VERSION_ID_MAX_LEN - 1))

_IDLE_INSTANCES_REGEX = r'^([\d]+|automatic)$'
# Note that this regex will not allow zero-prefixed numbers, e.g. 0001.
_INSTANCES_REGEX = r'^[1-9][\d]*$'

_CONCURRENT_REQUESTS_REGEX = r'^([1-9]\d*)$'

# This enforces that we will only accept a single decimal point of accuracy at
# the granularity of seconds and no decimal point with a granularity of
# milliseconds.
_PENDING_LATENCY_REGEX = r'^(\d+((\.\d{1,3})?s|ms)|automatic)$'

_IDLE_TIMEOUT_REGEX = r'^[\d]+(s|m)$'

GCE_RESOURCE_PATH_REGEX = r'^[a-z\d-]+(/[a-z\d-]+)*$'

GCE_RESOURCE_NAME_REGEX = r'^[a-z]([a-z\d-]{0,61}[a-z\d])?$'

FLEX_INSTANCE_IP_MODE_REGEX = r'^(EXTERNAL|external|INTERNAL|internal)$'

VPC_ACCESS_CONNECTOR_NAME_REGEX = r'^[a-z\d-]+(/.+)*$'

ALTERNATE_HOSTNAME_SEPARATOR = '-dot-'

# Note(user): This must match api/app_config.py
BUILTIN_NAME_PREFIX = 'ah-builtin'

# Here we expect either normal runtimes (such as 'nodejs' or 'java') or
# pinned runtime builders, which take the form of the path to a cloudbuild.yaml
# manifest file in GCS (written as gs://bucket/path/to/build.yaml).
RUNTIME_RE_STRING = r'((gs://[a-z0-9\-\._/]+)|([a-z][a-z0-9\-\.]{0,29}))'

API_VERSION_RE_STRING = r'[\w.]{1,32}'
ENV_RE_STRING = r'(1|2|standard|flex|flexible)'

SOURCE_LANGUAGE_RE_STRING = r'[\w.\-]{1,32}'

HANDLER_STATIC_FILES = 'static_files'
HANDLER_STATIC_DIR = 'static_dir'
HANDLER_SCRIPT = 'script'
HANDLER_API_ENDPOINT = 'api_endpoint'

LOGIN_OPTIONAL = 'optional'
LOGIN_REQUIRED = 'required'
LOGIN_ADMIN = 'admin'

AUTH_FAIL_ACTION_REDIRECT = 'redirect'
AUTH_FAIL_ACTION_UNAUTHORIZED = 'unauthorized'

DATASTORE_ID_POLICY_LEGACY = 'legacy'
DATASTORE_ID_POLICY_DEFAULT = 'default'

SECURE_HTTP = 'never'
SECURE_HTTPS = 'always'
SECURE_HTTP_OR_HTTPS = 'optional'
# Used for missing values; see http://b/issue?id=2073962.
SECURE_DEFAULT = 'default'

REQUIRE_MATCHING_FILE = 'require_matching_file'

DEFAULT_SKIP_FILES = (r'^(.*/)?('
                      r'(#.*#)|'
                      r'(.*~)|'
                      r'(.*\.py[co])|'
                      r'(.*/RCS/.*)|'
                      r'(\..*)|'
                      r')$')
# Expression meaning to skip no files, which is the default for AppInclude.
SKIP_NO_FILES = r'(?!)'

DEFAULT_NOBUILD_FILES = (r'^$')

# Attributes for `URLMap`
LOGIN = 'login'
AUTH_FAIL_ACTION = 'auth_fail_action'
SECURE = 'secure'
URL = 'url'
POSITION = 'position'
POSITION_HEAD = 'head'
POSITION_TAIL = 'tail'
STATIC_FILES = 'static_files'
UPLOAD = 'upload'
STATIC_DIR = 'static_dir'
MIME_TYPE = 'mime_type'
SCRIPT = 'script'
EXPIRATION = 'expiration'
API_ENDPOINT = 'api_endpoint'
HTTP_HEADERS = 'http_headers'
APPLICATION_READABLE = 'application_readable'
REDIRECT_HTTP_RESPONSE_CODE = 'redirect_http_response_code'

# Attributes for `AppInfoExternal`
APPLICATION = 'application'
PROJECT = 'project'  # An alias for 'application'
MODULE = 'module'
SERVICE = 'service'
AUTOMATIC_SCALING = 'automatic_scaling'
MANUAL_SCALING = 'manual_scaling'
BASIC_SCALING = 'basic_scaling'
VM = 'vm'
VM_SETTINGS = 'vm_settings'
ZONES = 'zones'
BETA_SETTINGS = 'beta_settings'
FLEXIBLE_RUNTIME_SETTINGS = 'flexible_runtime_settings'
VM_HEALTH_CHECK = 'vm_health_check'
HEALTH_CHECK = 'health_check'
RESOURCES = 'resources'
LIVENESS_CHECK = 'liveness_check'
READINESS_CHECK = 'readiness_check'
NETWORK = 'network'
VPC_ACCESS_CONNECTOR = 'vpc_access_connector'
VERSION = 'version'
MAJOR_VERSION = 'major_version'
MINOR_VERSION = 'minor_version'
RUNTIME = 'runtime'
RUNTIME_CHANNEL = 'runtime_channel'
API_VERSION = 'api_version'
MAIN = 'main'
ENDPOINTS_API_SERVICE = 'endpoints_api_service'
ENV = 'env'
ENTRYPOINT = 'entrypoint'
RUNTIME_CONFIG = 'runtime_config'
SOURCE_LANGUAGE = 'source_language'
BUILTINS = 'builtins'
INCLUDES = 'includes'
HANDLERS = 'handlers'
LIBRARIES = 'libraries'
DEFAULT_EXPIRATION = 'default_expiration'
SKIP_FILES = 'skip_files'
NOBUILD_FILES = 'nobuild_files'
SERVICES = 'inbound_services'
DERIVED_FILE_TYPE = 'derived_file_type'
JAVA_PRECOMPILED = 'java_precompiled'
PYTHON_PRECOMPILED = 'python_precompiled'
ADMIN_CONSOLE = 'admin_console'
ERROR_HANDLERS = 'error_handlers'
BACKENDS = 'backends'
THREADSAFE = 'threadsafe'
SERVICEACCOUNT = 'service_account'
DATASTORE_AUTO_ID_POLICY = 'auto_id_policy'
API_CONFIG = 'api_config'
CODE_LOCK = 'code_lock'
ENV_VARIABLES = 'env_variables'
BUILD_ENV_VARIABLES = 'build_env_variables'
STANDARD_WEBSOCKET = 'standard_websocket'
APP_ENGINE_APIS = 'app_engine_apis'

SOURCE_REPO_RE_STRING = r'^[a-z][a-z0-9\-\+\.]*:[^#]*$'
SOURCE_REVISION_RE_STRING = r'^[0-9a-fA-F]+$'

# Maximum size of all source references (in bytes) for a deployment.
SOURCE_REFERENCES_MAX_SIZE = 2048

INSTANCE_CLASS = 'instance_class'

# Attributes for Standard App Engine (only) AutomaticScaling.
MINIMUM_PENDING_LATENCY = 'min_pending_latency'
MAXIMUM_PENDING_LATENCY = 'max_pending_latency'
MINIMUM_IDLE_INSTANCES = 'min_idle_instances'
MAXIMUM_IDLE_INSTANCES = 'max_idle_instances'
MAXIMUM_CONCURRENT_REQUEST = 'max_concurrent_requests'

# Attributes for Managed VMs (only) AutomaticScaling. These are very
# different than Standard App Engine because scaling settings are
# mapped to Cloud Autoscaler (as opposed to the clone scheduler). See
MIN_NUM_INSTANCES = 'min_num_instances'
MAX_NUM_INSTANCES = 'max_num_instances'
COOL_DOWN_PERIOD_SEC = 'cool_down_period_sec'
CPU_UTILIZATION = 'cpu_utilization'
CPU_UTILIZATION_UTILIZATION = 'target_utilization'
CPU_UTILIZATION_AGGREGATION_WINDOW_LENGTH_SEC = 'aggregation_window_length_sec'
# Managed VMs Richer Autoscaling. These (MVMs only) scaling settings
# are supported for both vm:true and env:2|flex, but are not yet
# publicly documented.
TARGET_NETWORK_SENT_BYTES_PER_SEC = 'target_network_sent_bytes_per_sec'
TARGET_NETWORK_SENT_PACKETS_PER_SEC = 'target_network_sent_packets_per_sec'
TARGET_NETWORK_RECEIVED_BYTES_PER_SEC = 'target_network_received_bytes_per_sec'
TARGET_NETWORK_RECEIVED_PACKETS_PER_SEC = (
    'target_network_received_packets_per_sec')
TARGET_DISK_WRITE_BYTES_PER_SEC = 'target_disk_write_bytes_per_sec'
TARGET_DISK_WRITE_OPS_PER_SEC = 'target_disk_write_ops_per_sec'
TARGET_DISK_READ_BYTES_PER_SEC = 'target_disk_read_bytes_per_sec'
TARGET_DISK_READ_OPS_PER_SEC = 'target_disk_read_ops_per_sec'
TARGET_REQUEST_COUNT_PER_SEC = 'target_request_count_per_sec'
TARGET_CONCURRENT_REQUESTS = 'target_concurrent_requests'
# Custom Metric autoscaling. These are supported for Flex only.
CUSTOM_METRICS = 'custom_metrics'
METRIC_NAME = 'metric_name'
TARGET_TYPE = 'target_type'
TARGET_TYPE_REGEX = r'^(GAUGE|DELTA_PER_SECOND|DELTA_PER_MINUTE)$'
CUSTOM_METRIC_UTILIZATION = 'target_utilization'
SINGLE_INSTANCE_ASSIGNMENT = 'single_instance_assignment'
FILTER = 'filter'


# Attributes for ManualScaling
INSTANCES = 'instances'

# Attributes for BasicScaling
MAX_INSTANCES = 'max_instances'
IDLE_TIMEOUT = 'idle_timeout'

# Attributes for AdminConsole
PAGES = 'pages'
NAME = 'name'

# Attributes for EndpointsApiService
ENDPOINTS_NAME = 'name'
CONFIG_ID = 'config_id'
ROLLOUT_STRATEGY = 'rollout_strategy'
ROLLOUT_STRATEGY_FIXED = 'fixed'
ROLLOUT_STRATEGY_MANAGED = 'managed'
TRACE_SAMPLING = 'trace_sampling'

# Attributes for ErrorHandlers
ERROR_CODE = 'error_code'
FILE = 'file'
_ERROR_CODE_REGEX = r'(default|over_quota|dos_api_denial|timeout)'

# Attributes for BuiltinHandler
ON = 'on'
ON_ALIASES = ['yes', 'y', 'True', 't', '1', 'true']
OFF = 'off'
OFF_ALIASES = ['no', 'n', 'False', 'f', '0', 'false']

# Attributes for `VmHealthCheck`. Please refer to message `VmHealthCheck` in
# `request_path` and `port` are not configurable yet.
ENABLE_HEALTH_CHECK = 'enable_health_check'
CHECK_INTERVAL_SEC = 'check_interval_sec'
TIMEOUT_SEC = 'timeout_sec'
APP_START_TIMEOUT_SEC = 'app_start_timeout_sec'
UNHEALTHY_THRESHOLD = 'unhealthy_threshold'
HEALTHY_THRESHOLD = 'healthy_threshold'
FAILURE_THRESHOLD = 'failure_threshold'
SUCCESS_THRESHOLD = 'success_threshold'
RESTART_THRESHOLD = 'restart_threshold'
INITIAL_DELAY_SEC = 'initial_delay_sec'
HOST = 'host'
PATH = 'path'

# Attributes for Resources.
CPU = 'cpu'
MEMORY_GB = 'memory_gb'
DISK_SIZE_GB = 'disk_size_gb'

# Attributes for Resources:Volumes.
VOLUMES = 'volumes'
VOLUME_NAME = 'name'
VOLUME_TYPE = 'volume_type'
SIZE_GB = 'size_gb'

# Attributes for Network.
FORWARDED_PORTS = 'forwarded_ports'
INSTANCE_TAG = 'instance_tag'
NETWORK_NAME = 'name'
SUBNETWORK_NAME = 'subnetwork_name'
SESSION_AFFINITY = 'session_affinity'
INSTANCE_IP_MODE = 'instance_ip_mode'

# Attributes for Scheduler Settings
STANDARD_MIN_INSTANCES = 'min_instances'
STANDARD_MAX_INSTANCES = 'max_instances'
STANDARD_TARGET_CPU_UTILIZATION = 'target_cpu_utilization'
STANDARD_TARGET_THROUGHPUT_UTILIZATION = 'target_throughput_utilization'

# Attributes for `VpcAccessConnector`.
VPC_ACCESS_CONNECTOR_NAME = 'name'
VPC_ACCESS_CONNECTOR_EGRESS_SETTING = 'egress_setting'
VPC_ACCESS_CONNECTOR_EGRESS_SETTING_ALL_TRAFFIC = 'all-traffic'
VPC_ACCESS_CONNECTOR_EGRESS_SETTING_PRIVATE_RANGES_ONLY = 'private-ranges-only'

# Attributes for FlexibleRuntimeSettings.
OPERATING_SYSTEM = 'operating_system'
RUNTIME_VERSION = 'runtime_version'

class _VersionedLibrary(object):
  """A versioned library supported by App Engine."""

  def __init__(self,
               name,
               url,
               description,
               supported_versions,
               latest_version,
               default_version=None,
               deprecated_versions=None,
               experimental_versions=None,
               hidden_versions=None):
    """Initializer for `_VersionedLibrary`.

    Args:
      name: The name of the library; for example, `django`.
      url: The URL for the library's project page; for example,
          `http://www.djangoproject.com/`.
      description: A short description of the library; for example,
          `A framework...`.
      supported_versions: A list of supported version names, ordered by release
          date; for example, `["v1", "v2", "v3"]`.
      latest_version: The version of the library that will be used when you
          specify `latest.` The rule of thumb is that this value should be the
          newest version that is neither deprecated nor experimental; however
          this value might be an experimental version if all of the supported
          versions are either deprecated or experimental.
      default_version: The version of the library that is enabled by default
          in the Python 2.7 runtime, or `None` if the library is not available
          by default; for example, `v1`.
      deprecated_versions: A list of the versions of the library that have been
          deprecated; for example, `["v1", "v2"]`. Order by release version.
      experimental_versions: A list of the versions of the library that are
          currently experimental; for example, `["v1"]`. Order by release
          version.
      hidden_versions: A list of versions that will not show up in public
          documentation for release purposes.  If, as a result, the library
          has no publicly documented versions, the entire library won't show
          up in the docs. Order by release version.
    """
    self.name = name
    self.url = url
    self.description = description
    self.supported_versions = supported_versions
    self.latest_version = latest_version
    self.default_version = default_version
    self.deprecated_versions = deprecated_versions or []
    self.experimental_versions = experimental_versions or []
    self.hidden_versions = hidden_versions or []

  @property
  def hidden(self):
    """Determines if the entire library should be hidden from public docs.

    Returns:
      True if there is every supported version is hidden.
    """
    return sorted(self.supported_versions) == sorted(self.hidden_versions)

  @property
  def non_deprecated_versions(self):
    """Retrieves the versions of the library that are not deprecated.

    Returns:
      A list of the versions of the library that are not deprecated.
    """
    return [version for version in self.supported_versions
            if version not in self.deprecated_versions]


_SUPPORTED_LIBRARIES = [
    _VersionedLibrary(
        'clearsilver',
        'http://www.clearsilver.net/',
        'A fast, powerful, and language-neutral HTML template system.',
        ['0.10.5'],
        latest_version='0.10.5',
        hidden_versions=['0.10.5'],
        ),
    _VersionedLibrary(
        'click',
        'http://click.pocoo.org/',
        'A command line library for Python.',
        ['6.6'],
        latest_version='6.6',
        hidden_versions=['6.6'],
        ),
    _VersionedLibrary(
        'django',
        'http://www.djangoproject.com/',
        'A full-featured web application framework for Python.',
        ['1.2', '1.3', '1.4', '1.5', '1.9', '1.11'],
        latest_version='1.4',
        deprecated_versions=['1.2', '1.3', '1.5', '1.9'],
        # TODO(b/78247136) Deprecate 1.4 and update latest_version to 1.11
        ),
    _VersionedLibrary(
        'enum',
        'https://pypi.python.org/pypi/enum34',
        'A backport of the enum module introduced in python 3.4',
        ['0.9.23'],
        latest_version='0.9.23',
        ),
    _VersionedLibrary(
        'endpoints',
        'https://cloud.google.com/appengine/docs/standard/python/endpoints/',
        'Libraries for building APIs in an App Engine application.',
        ['1.0'],
        latest_version='1.0',
        ),
    _VersionedLibrary(
        'flask',
        'http://flask.pocoo.org/',
        'Flask is a microframework for Python based on Werkzeug, Jinja 2 '
        'and good intentions.',
        ['0.12'],
        latest_version='0.12',
        ),
    _VersionedLibrary(
        'futures',
        'https://docs.python.org/3/library/concurrent.futures.html',
        'Backport of Python 3.2 Futures.',
        ['3.0.5'],
        latest_version='3.0.5',
        ),
    _VersionedLibrary(
        'grpcio',
        'http://www.grpc.io/',
        'A high performance general RPC framework',
        # Note: For documentation this is overridden to display 1.1.0dev0
        ['1.0.0'],
        latest_version='1.0.0',
        experimental_versions=['1.0.0'],
        ),
    _VersionedLibrary(
        'itsdangerous',
        'http://pythonhosted.org/itsdangerous/',
        'HMAC and SHA1 signing for Python.',
        ['0.24'],
        latest_version='0.24',
        hidden_versions=['0.24'],
        ),
    _VersionedLibrary(
        'jinja2',
        'http://jinja.pocoo.org/docs/',
        'A modern and designer friendly templating language for Python.',
        ['2.6'],
        latest_version='2.6',
        ),
    _VersionedLibrary(
        'lxml',
        'http://lxml.de/',
        'A Pythonic binding for the C libraries libxml2 and libxslt.',
        ['2.3', '2.3.5', '3.7.3'],
        latest_version='3.7.3',
        deprecated_versions=['2.3', '2.3.5'],
        ),
    _VersionedLibrary(
        'markupsafe',
        'http://pypi.python.org/pypi/MarkupSafe',
        'A XML/HTML/XHTML markup safe string for Python.',
        ['0.15', '0.23'],
        latest_version='0.15',
        ),
    _VersionedLibrary(
        'matplotlib',
        'http://matplotlib.org/',
        'A 2D plotting library which produces publication-quality figures.',
        ['1.2.0'],
        latest_version='1.2.0',
        ),
    _VersionedLibrary(
        'MySQLdb',
        'http://mysql-python.sourceforge.net/',
        'A Python DB API v2.0 compatible interface to MySQL.',
        ['1.2.4b4', '1.2.4', '1.2.5'],
        latest_version='1.2.5',
        deprecated_versions=['1.2.4b4', '1.2.4'],
        ),
    _VersionedLibrary(
        'mysqlclient',
        'http://mysql-python.sourceforge.net/',
        'A Python DB API v2.0 compatible interface to MySQL.',
        ['1.4.4'],
        latest_version='1.4.4',
        ),
    _VersionedLibrary(
        'numpy',
        'http://numpy.scipy.org/',
        'A general-purpose library for array-processing.',
        ['1.6.1'],
        latest_version='1.6.1',
        ),
    _VersionedLibrary(
        'PIL',
        'http://www.pythonware.com/library/pil/handbook/',
        'A library for creating and transforming images.',
        ['1.1.7'],
        latest_version='1.1.7',
        ),
    _VersionedLibrary(
        'protorpc',
        'https://github.com/google/protorpc',
        'A framework for implementing HTTP-based remote procedure call (RPC) '
        'services.',
        ['1.0'],
        latest_version='1.0',
        default_version='1.0',
        ),
    _VersionedLibrary(
        'pytz',
        'https://pypi.python.org/pypi/pytz?',
        'A library for cross-platform timezone calculations',
        ['2016.4', '2017.2', '2017.3'],
        latest_version='2017.3',
        default_version='2017.3',
        deprecated_versions=['2016.4', '2017.2'],
        ),
    _VersionedLibrary(
        'crcmod',
        'http://crcmod.sourceforge.net/',
        'A library for generating Cyclic Redundancy Checks (CRC).',
        ['1.7'],
        latest_version='1.7',
        ),
    _VersionedLibrary(
        'protobuf',
        'https://developers.google.com/protocol-buffers/',
        'A library for serializing structured data',
        ['3.0.0'],
        latest_version='3.0.0',
        experimental_versions=['3.0.0'],
        ),
    _VersionedLibrary(
        'psycopg2',
        'http://initd.org/psycopg/',
        'A Python DB API v2.0 compatible interface to PostgreSQL.',
        ['2.8.3'],
        latest_version='2.8.3',
        ),
    _VersionedLibrary(
        'PyAMF',
        'https://pypi.python.org/pypi/PyAMF',
        'A library that provides (AMF) Action Message Format functionality.',
        ['0.6.1', '0.7.2'],
        latest_version='0.6.1',
        experimental_versions=['0.7.2'],
        ),
    _VersionedLibrary(
        'pycrypto',
        'https://www.dlitz.net/software/pycrypto/',
        'A library of cryptography functions such as random number generation.',
        ['2.3', '2.6', '2.6.1'],
        latest_version='2.6',
        deprecated_versions=['2.3'],
        # TODO(b/78247136) Deprecate 2.6 and update latest_version to 2.6.1
        ),
    _VersionedLibrary(
        'setuptools',
        'http://pypi.python.org/pypi/setuptools',
        'A library that provides package and module discovery capabilities.',
        ['0.6c11', '36.6.0'],
        latest_version='36.6.0',
        deprecated_versions=['0.6c11'],
        ),
    _VersionedLibrary(
        'six',
        'https://pypi.python.org/pypi/six',
        'Abstract differences between py2.x and py3',
        ['1.9.0', '1.12.0'],
        latest_version='1.12.0',
        default_version='1.12.0',
        ),
    _VersionedLibrary(
        'ssl',
        'http://docs.python.org/dev/library/ssl.html',
        'The SSL socket wrapper built-in module.',
        ['2.7', '2.7.11', '2.7.16', '2.7.current'],
        latest_version='2.7.11',
        deprecated_versions=['2.7', '2.7.16']
        ),
    _VersionedLibrary(
        'ujson',
        'https://pypi.python.org/pypi/ujson',
        'UltraJSON is an ultra fast JSON encoder and decoder written in pure C',
        ['1.35'],
        latest_version='1.35',
        ),
    _VersionedLibrary(
        'webapp2',
        'http://webapp-improved.appspot.com/',
        'A lightweight Python web framework.',
        ['2.3', '2.5.1', '2.5.2'],
        latest_version='2.5.2',
        # Keep default version at 2.3 because apps in production depend on it.
        default_version='2.3',
        deprecated_versions=['2.5.1']
        ),
    _VersionedLibrary(
        'webob',
        'http://www.webob.org/',
        'A library that provides wrappers around the WSGI request environment.',
        ['1.1.1', '1.2.3'],
        latest_version='1.2.3',
        # Keep default version at 1.1.1 because apps in production depend on it.
        default_version='1.1.1',
        ),
    _VersionedLibrary(
        'werkzeug',
        'http://www.werkzeug.pocoo.org/',
        'A WSGI utility library.',
        ['0.11.10'],
        latest_version='0.11.10',
        default_version='0.11.10',
        ),
    _VersionedLibrary(
        'yaml',
        'http://www.yaml.org/',
        'A library for YAML serialization and deserialization.',
        ['3.10'],
        latest_version='3.10',
        default_version='3.10'
        ),
    ]

_NAME_TO_SUPPORTED_LIBRARY = dict((library.name, library)
                                  for library in _SUPPORTED_LIBRARIES)

# A mapping from third-party name/version to a list of that library's
# dependencies.
REQUIRED_LIBRARIES = {
    ('django', '1.11'): [('pytz', '2017.2')],
    ('flask', '0.12'): [('click', '6.6'), ('itsdangerous', '0.24'),
                        ('jinja2', '2.6'), ('werkzeug', '0.11.10')],
    ('jinja2', '2.6'): [('markupsafe', '0.15'), ('setuptools', '0.6c11')],
    ('jinja2', 'latest'): [('markupsafe', 'latest'), ('setuptools', 'latest')],
    ('matplotlib', '1.2.0'): [('numpy', '1.6.1')],
    ('matplotlib', 'latest'): [('numpy', 'latest')],
    ('protobuf', '3.0.0'): [('six', 'latest')],
    ('protobuf', 'latest'): [('six', 'latest')],
    ('grpcio', '1.0.0'): [('protobuf', '3.0.0'), ('enum', '0.9.23'),
                          ('futures', '3.0.5'), ('six', 'latest'),
                          ('setuptools', '36.6.0')],
    ('grpcio', 'latest'): [('protobuf', 'latest'), ('enum', 'latest'),
                           ('futures', 'latest'), ('six', 'latest'),
                           ('setuptools', 'latest')]
}

_USE_VERSION_FORMAT = ('use one of: "%s"')


# See RFC 2616 section 2.2.
_HTTP_SEPARATOR_CHARS = frozenset('()<>@,;:\\"/[]?={} \t')
_HTTP_TOKEN_CHARS = frozenset(string.printable[:-5]) - _HTTP_SEPARATOR_CHARS
_HTTP_TOKEN_RE = re.compile('[%s]+$' % re.escape(''.join(_HTTP_TOKEN_CHARS)))

# Source: http://www.cs.tut.fi/~jkorpela/http.html
_HTTP_REQUEST_HEADERS = frozenset([
    'accept',
    'accept-charset',
    'accept-encoding',
    'accept-language',
    'authorization',
    'expect',
    'from',
    'host',
    'if-match',
    'if-modified-since',
    'if-none-match',
    'if-range',
    'if-unmodified-since',
    'max-forwards',
    'proxy-authorization',
    'range',
    'referer',
    'te',
    'user-agent',
])

# The minimum cookie length (i.e. number of bytes) that HTTP clients should
# support, per RFCs 2109 and 2965.
_MAX_COOKIE_LENGTH = 4096

# trailing NULL character, which is why this is not 2048.
_MAX_URL_LENGTH = 2047

# We allow certain headers to be larger than the normal limit of 8192 bytes.
_MAX_HEADER_SIZE_FOR_EXEMPTED_HEADERS = 10240

_CANNED_RUNTIMES = ('contrib-dart', 'dart', 'go', 'php', 'php55', 'php72',
                    'python', 'python27', 'python-compat', 'java', 'java7',
                    'java8', 'vm', 'custom', 'nodejs', 'ruby', 'go111',
                    'go112')
_all_runtimes = _CANNED_RUNTIMES


def GetAllRuntimes():
  """Returns the list of all valid runtimes.

  This list can include third-party runtimes as well as canned runtimes.

  Returns:
    Tuple of strings.
  """
  return _all_runtimes


def EnsureAsciiBytes(s, err):
  """Ensure s contains only ASCII-safe characters; return it as bytes-type.

  Arguments:
    s: the string or bytes to check
    err: the error to raise if not good.
  Raises:
    err if it's not ASCII-safe.
  Returns:
    s as a byte string
  """
  try:
    return s.encode('ascii')
  except UnicodeEncodeError:
    raise err
  except UnicodeDecodeError:
    # Python 2 hilariously raises UnicodeDecodeError on trying to
    # ascii-_en_code a byte string invalidly.
    raise err
  except AttributeError:
    try:
      return s.decode('ascii').encode('ascii')
    except UnicodeDecodeError:
      raise err


class HandlerBase(validation.Validated):
  """Base class for URLMap and ApiConfigHandler."""
  ATTRIBUTES = {
      # Common fields.
      URL: validation.Optional(_URL_REGEX),
      LOGIN: validation.Options(LOGIN_OPTIONAL,
                                LOGIN_REQUIRED,
                                LOGIN_ADMIN,
                                default=LOGIN_OPTIONAL),

      AUTH_FAIL_ACTION: validation.Options(AUTH_FAIL_ACTION_REDIRECT,
                                           AUTH_FAIL_ACTION_UNAUTHORIZED,
                                           default=AUTH_FAIL_ACTION_REDIRECT),

      SECURE: validation.Options(SECURE_HTTP,
                                 SECURE_HTTPS,
                                 SECURE_HTTP_OR_HTTPS,
                                 SECURE_DEFAULT,
                                 default=SECURE_DEFAULT),

      # Python/CGI fields.
      HANDLER_SCRIPT: validation.Optional(_FILES_REGEX)
  }


class HttpHeadersDict(validation.ValidatedDict):
  """A dict that limits keys and values to what `http_headers` allows.

  `http_headers` is an static handler key; it applies to handlers with
  `static_dir` or `static_files` keys. The following code is an example of how
  `http_headers` is used::

      handlers:
      - url: /static
        static_dir: static
        http_headers:
          X-Foo-Header: foo value
          X-Bar-Header: bar value

  """

  DISALLOWED_HEADERS = frozenset([
      # TODO(user): I don't think there's any reason to disallow users
      # from setting Content-Encoding, but other parts of the system prevent
      # this; therefore, we disallow it here. See the following discussion:
      'content-encoding',
      'content-length',
      'date',
      'server'
  ])

  MAX_HEADER_LENGTH = 500
  MAX_HEADER_VALUE_LENGTHS = {
      'content-security-policy': _MAX_HEADER_SIZE_FOR_EXEMPTED_HEADERS,
      'x-content-security-policy': _MAX_HEADER_SIZE_FOR_EXEMPTED_HEADERS,
      'x-webkit-csp': _MAX_HEADER_SIZE_FOR_EXEMPTED_HEADERS,
      'content-security-policy-report-only':
          _MAX_HEADER_SIZE_FOR_EXEMPTED_HEADERS,
      'set-cookie': _MAX_COOKIE_LENGTH,
      'set-cookie2': _MAX_COOKIE_LENGTH,
      'location': _MAX_URL_LENGTH}
  MAX_LEN = 500

  class KeyValidator(validation.Validator):
    """Ensures that keys in `HttpHeadersDict` are valid.

    `HttpHeadersDict` contains a list of headers. An instance is used as
    `HttpHeadersDict`'s `KEY_VALIDATOR`.
    """

    def Validate(self, name, unused_key=None):
      """Returns an argument, or raises an exception if the argument is invalid.

      HTTP header names are defined by `RFC 2616, section 4.2`_.

      Args:
        name: HTTP header field value.
        unused_key: Unused.

      Returns:
        name argument, unchanged.

      Raises:
        appinfo_errors.InvalidHttpHeaderName: An argument cannot be used as an
            HTTP header name.

      .. _RFC 2616, section 4.2:
         https://www.ietf.org/rfc/rfc2616.txt
      """
      original_name = name

      # Make sure only ASCII data is used.
      if isinstance(name, six_subset.string_types):
        name = EnsureAsciiBytes(name, appinfo_errors.InvalidHttpHeaderName(
            'HTTP header values must not contain non-ASCII data'))

      # HTTP headers are case-insensitive.
      name = name.lower().decode('ascii')

      if not _HTTP_TOKEN_RE.match(name):
        raise appinfo_errors.InvalidHttpHeaderName(
            'An HTTP header must be a non-empty RFC 2616 token.')

      # Request headers shouldn't be used in responses.
      if name in _HTTP_REQUEST_HEADERS:
        raise appinfo_errors.InvalidHttpHeaderName(
            '%r can only be used in HTTP requests, not responses.'
            % original_name)

      # Make sure that none of the reserved prefixes is used.
      if name.startswith('x-appengine'):
        raise appinfo_errors.InvalidHttpHeaderName(
            'HTTP header names that begin with X-Appengine are reserved.')

      if wsgiref.util.is_hop_by_hop(name):
        raise appinfo_errors.InvalidHttpHeaderName(
            'Only use end-to-end headers may be used. See RFC 2616 section'
            ' 13.5.1.')

      if name in HttpHeadersDict.DISALLOWED_HEADERS:
        raise appinfo_errors.InvalidHttpHeaderName(
            '%s is a disallowed header.' % name)

      return original_name

  class ValueValidator(validation.Validator):
    """Ensures that values in `HttpHeadersDict` are valid.

    An instance is used as `HttpHeadersDict`'s `VALUE_VALIDATOR`.
    """

    def Validate(self, value, key=None):
      """Returns a value, or raises an exception if the value is invalid.

      According to `RFC 2616 section 4.2`_ header field values must consist "of
      either *TEXT or combinations of token, separators, and quoted-string"::

          TEXT = <any OCTET except CTLs, but including LWS>

      Args:
        value: HTTP header field value.
        key: HTTP header field name.

      Returns:
        A value argument.

      Raises:
        appinfo_errors.InvalidHttpHeaderValue: An argument cannot be used as an
            HTTP header value.

      .. _RFC 2616, section 4.2:
         https://www.ietf.org/rfc/rfc2616.txt
      """
      # Make sure only ASCII data is used.
      error = appinfo_errors.InvalidHttpHeaderValue(
          'HTTP header values must not contain non-ASCII data')
      if isinstance(value, six_subset.string_types):
        b_value = EnsureAsciiBytes(value, error)
      else:
        b_value = EnsureAsciiBytes(('%s' % value), error)

      # HTTP headers are case-insensitive.
      key = key.lower()

      # TODO(user): This is the same check that appserver performs, but it
      # could be stronger. e.g. `"foo` should not be considered valid, because
      # HTTP does not allow unclosed double quote marks in header values, per
      # RFC 2616 section 4.2.
      printable = set(string.printable[:-5].encode('ascii'))
      if not all(b in printable for b in b_value):
        raise appinfo_errors.InvalidHttpHeaderValue(
            'HTTP header field values must consist of printable characters.')

      HttpHeadersDict.ValueValidator.AssertHeaderNotTooLong(key, value)

      return value

    @staticmethod
    def AssertHeaderNotTooLong(name, value):
      header_length = len(('%s: %s\r\n' % (name, value)).encode('ascii'))

      # The `>=` operator here is a little counter-intuitive. The reason for it
      # is that I'm trying to follow the
      # `HTTPProto::IsValidHeader` implementation.
      if header_length >= HttpHeadersDict.MAX_HEADER_LENGTH:
        # If execution reaches this point, it generally means the header is too
        # long, but there are a few exceptions, which are listed in the next
        # dict.
        try:
          max_len = HttpHeadersDict.MAX_HEADER_VALUE_LENGTHS[name]
        except KeyError:
          raise appinfo_errors.InvalidHttpHeaderValue(
              'HTTP header (name + value) is too long.')

        # We are dealing with one of the exceptional headers with larger maximum
        # value lengths.
        if len(value) > max_len:
          insert = name, len(value), max_len
          raise appinfo_errors.InvalidHttpHeaderValue(
              '%r header value has length %d, which exceed the maximum allowed,'
              ' %d.' % insert)

  KEY_VALIDATOR = KeyValidator()
  VALUE_VALIDATOR = ValueValidator()

  def Get(self, header_name):
    """Gets a header value.

    Args:
      header_name: HTTP header name to look for.

    Returns:
      A header value that corresponds to `header_name`. If more than one such
      value is in `self`, one of the values is selected arbitrarily and
      returned. The selection is not deterministic.
    """
    for name in self:
      if name.lower() == header_name.lower():
        return self[name]

  # TODO(user): Perhaps, this functionality should be part of
  # `validation.ValidatedDict`.
  def __setitem__(self, key, value):
    is_addition = self.Get(key) is None
    if is_addition and len(self) >= self.MAX_LEN:
      raise appinfo_errors.TooManyHttpHeaders(
          'Tried to add another header when the current set of HTTP headers'
          ' already has the maximum allowed number of headers, %d.'
          % HttpHeadersDict.MAX_LEN)
    super(HttpHeadersDict, self).__setitem__(key, value)


class URLMap(HandlerBase):
  r"""Maps from URLs to handlers.

  This class acts similar to a union type. Its purpose is to describe a mapping
  between a set of URLs and their handlers. The handler type of a given instance
  is determined by which `handler-id` attribute is used.

  Every mapping can have one and only one handler type. Attempting to use more
  than one `handler-id` attribute will cause an `UnknownHandlerType` to be
  raised during validation. Failure to provide any `handler-id` attributes will
  cause `MissingHandlerType` to be raised during validation.

  The regular expression used by the `url` field will be used to match against
  the entire URL path and query string of the request; therefore, partial maps
  will not be matched. Specifying a `url`, such as `/admin`, is the same as
  matching against the regular expression `^/admin$`. Don't start your matching
  `url` with `^` or end them with `$`. These regular expressions won't be
  accepted and will raise `ValueError`.

  Attributes:
    login: Specifies whether a user should be logged in to access a URL.
        The default value of this argument is `optional`.
    secure: Sets the restriction on the protocol that can be used to serve this
        URL or handler. This value can be set to `HTTP`, `HTTPS` or `either`.
    url: Specifies a regular expression that is used to fully match against the
        request URLs path. See the "Special cases" section of this document to
        learn more.
    static_files: Specifies the handler ID attribute that maps `url` to the
        appropriate file. You can specify regular expression backreferences to
        the string matched to `url`.
    upload: Specifies the regular expression that is used by the application
        configuration program to determine which files are uploaded as blobs.
        Because it is difficult to determine this information using just the
        `url` and `static_files` arguments, this attribute must be included.
        This attribute is required when you define a `static_files` mapping. A
        matching file name must fully match against the `upload` regular
        expression, similar to how `url` is matched against the request path. Do
        not begin the `upload` argument with the `^` character or end it with
        the `$` character.
    static_dir: Specifies the handler ID that maps the provided `url` to a
        sub-directory within the application directory. See "Special cases."
    mime_type: When used with `static_files` and `static_dir`, this argument
        specifies that the MIME type of the files that are served from those
        directories must be overridden with this value.
    script: Specifies the handler ID that maps URLs to a script handler within
        the application directory that will run using CGI.
    position: Used in `AppInclude` objects to specify whether a handler should
        be inserted at the beginning of the primary handler list or at the end.
        If `tail` is specified, the handler is inserted at the end; otherwise,
        the handler is inserted at the beginning. This behavior implies that
        `head` is the effective default.
    expiration: When used with static files and directories, this argument
        specifies the time delta to use for cache expiration. This argument
        should use the following format: `4d 5h 30m 15s`, where each letter
        signifies days, hours, minutes, and seconds, respectively. The `s` for
        "seconds" can be omitted. Only one amount must be specified, though
        combining multiple amounts is optional. The following list contains
        examples of values that are acceptable: `10`, `1d 6h`, `1h 30m`,
        `7d 7d 7d`, `5m 30`.
    api_endpoint: Specifies the handler ID that identifies an endpoint as an API
        endpoint. Calls that terminate here will be handled by the API serving
        framework.

  Special cases:
    When defining a `static_dir` handler, do not use a regular expression in the
    `url` attribute. Both the `url` and `static_dir` attributes are
    automatically mapped to these equivalents::

        <url>/(.*)
        <static_dir>/\1

    For example, this declaration...::

        url: /images
        static_dir: images_folder

    ...is equivalent to this `static_files` declaration::

        url: /images/(.*)
        static_files: images_folder/\1
        upload: images_folder/(.*)

  """
  ATTRIBUTES = {
      # Static file fields.
      # File mappings are allowed to have regex back references.
      HANDLER_STATIC_FILES: validation.Optional(_FILES_REGEX),
      UPLOAD: validation.Optional(_FILES_REGEX),
      APPLICATION_READABLE: validation.Optional(bool),

      # Static directory fields.
      HANDLER_STATIC_DIR: validation.Optional(_FILES_REGEX),

      # Used in both static mappings.
      MIME_TYPE: validation.Optional(str),
      EXPIRATION: validation.Optional(_EXPIRATION_REGEX),
      REQUIRE_MATCHING_FILE: validation.Optional(bool),
      HTTP_HEADERS: validation.Optional(HttpHeadersDict),

      # Python/CGI fields.
      POSITION: validation.Optional(validation.Options(POSITION_HEAD,
                                                       POSITION_TAIL)),

      HANDLER_API_ENDPOINT: validation.Optional(validation.Options(
          (ON, ON_ALIASES),
          (OFF, OFF_ALIASES))),

      REDIRECT_HTTP_RESPONSE_CODE: validation.Optional(validation.Options(
          '301', '302', '303', '307')),
  }
  ATTRIBUTES.update(HandlerBase.ATTRIBUTES)

  COMMON_FIELDS = set([
      URL, LOGIN, AUTH_FAIL_ACTION, SECURE, REDIRECT_HTTP_RESPONSE_CODE])

  # The keys of this map are attributes which can be used to identify each
  # mapping type in addition to the handler identifying attribute itself.
  ALLOWED_FIELDS = {
      HANDLER_STATIC_FILES: (MIME_TYPE, UPLOAD, EXPIRATION,
                             REQUIRE_MATCHING_FILE, HTTP_HEADERS,
                             APPLICATION_READABLE),
      HANDLER_STATIC_DIR: (MIME_TYPE, EXPIRATION, REQUIRE_MATCHING_FILE,
                           HTTP_HEADERS, APPLICATION_READABLE),
      HANDLER_SCRIPT: (POSITION),
      HANDLER_API_ENDPOINT: (POSITION, SCRIPT),
  }

  def GetHandler(self):
    """Gets the handler for a mapping.

    Returns:
      The value of the handler, as determined by the handler ID attribute.
    """
    return getattr(self, self.GetHandlerType())

  def GetHandlerType(self):
    """Gets the handler type of a mapping.

    Returns:
      The handler type as determined by which handler ID attribute is set.

    Raises:
      UnknownHandlerType: If none of the handler ID attributes are set.
      UnexpectedHandlerAttribute: If an unexpected attribute is set for the
          discovered handler type.
      HandlerTypeMissingAttribute: If the handler is missing a required
          attribute for its handler type.
      MissingHandlerAttribute: If a URL handler is missing an attribute.
    """
    # Special case for the `api_endpoint` handler as it may have a `script`
    # attribute as well.
    if getattr(self, HANDLER_API_ENDPOINT) is not None:
      # Matched id attribute, break out of loop.
      mapping_type = HANDLER_API_ENDPOINT
    else:
      for id_field in URLMap.ALLOWED_FIELDS:
        # Attributes always exist as defined by ATTRIBUTES.
        if getattr(self, id_field) is not None:
          # Matched id attribute, break out of loop.
          mapping_type = id_field
          break
      else:
        # If no mapping type is found raise exception.
        raise appinfo_errors.UnknownHandlerType(
            'Unknown url handler type.\n%s' % str(self))

    allowed_fields = URLMap.ALLOWED_FIELDS[mapping_type]

    # Make sure that none of the set attributes on this handler
    # are not allowed for the discovered handler type.
    for attribute in self.ATTRIBUTES:
      if (getattr(self, attribute) is not None and
          not (attribute in allowed_fields or
               attribute in URLMap.COMMON_FIELDS or
               attribute == mapping_type)):
        raise appinfo_errors.UnexpectedHandlerAttribute(
            'Unexpected attribute "%s" for mapping type %s.' %
            (attribute, mapping_type))

    # Also check that static file map has 'upload'.
    # NOTE: Add REQUIRED_FIELDS along with ALLOWED_FIELDS if any more
    # exceptional cases arise.
    if mapping_type == HANDLER_STATIC_FILES and not self.upload:
      raise appinfo_errors.MissingHandlerAttribute(
          'Missing "%s" attribute for URL "%s".' % (UPLOAD, self.url))

    return mapping_type

  def CheckInitialized(self):
    """Adds additional checking to make sure a handler has correct fields.

    In addition to normal `ValidatedCheck`, this method calls `GetHandlerType`,
    which validates whether all of the handler fields are configured properly.

    Raises:
      UnknownHandlerType: If none of the handler ID attributes are set.
      UnexpectedHandlerAttribute: If an unexpected attribute is set for the
          discovered handler type.
      HandlerTypeMissingAttribute: If the handler is missing a required
          attribute for its handler type.
      ContentTypeSpecifiedMultipleTimes: If `mime_type` is inconsistent with
          `http_headers`.
    """
    super(URLMap, self).CheckInitialized()
    if self.GetHandlerType() in (STATIC_DIR, STATIC_FILES):
      # re how headers that affect caching interact per RFC 2616:
      #
      # Section 13.1.3 says that when there is "apparent conflict between
      # [Cache-Control] header values, the most restrictive interpretation is
      # applied".
      #
      # Section 14.21 says that Cache-Control: max-age overrides Expires
      # headers.
      #
      # Section 14.32 says that Pragma: no-cache has no meaning in responses;
      # therefore, we do not need to be concerned about that header here.
      self.AssertUniqueContentType()

  def AssertUniqueContentType(self):
    """Makes sure that `self.http_headers` is consistent with `self.mime_type`.

    This method assumes that `self` is a static handler, either
    `self.static_dir` or `self.static_files`. You cannot specify `None`.

    Raises:
      appinfo_errors.ContentTypeSpecifiedMultipleTimes: If `self.http_headers`
          contains a `Content-Type` header, and `self.mime_type` is set. For
          example, the following configuration would be rejected::

              handlers:
              - url: /static
                static_dir: static
                mime_type: text/html
                http_headers:
                  content-type: text/html


        As this example shows, a configuration will be rejected when
        `http_headers` and `mime_type` specify a content type, even when they
        specify the same content type.
    """
    used_both_fields = self.mime_type and self.http_headers
    if not used_both_fields:
      return

    content_type = self.http_headers.Get('Content-Type')
    if content_type is not None:
      raise appinfo_errors.ContentTypeSpecifiedMultipleTimes(
          'http_header specified a Content-Type header of %r in a handler that'
          ' also specified a mime_type of %r.' % (content_type, self.mime_type))

  def FixSecureDefaults(self):
    """Forces omitted `secure` handler fields to be set to 'secure: optional'.

    The effect is that `handler.secure` is never equal to the nominal default.
    """
    # See http://b/issue?id=2073962.
    if self.secure == SECURE_DEFAULT:
      self.secure = SECURE_HTTP_OR_HTTPS

  def WarnReservedURLs(self):
    """Generates a warning for reserved URLs.

    See the `version element documentation`_ to learn which URLs are reserved.

    .. _`version element documentation`:
       https://cloud.google.com/appengine/docs/python/config/appref#syntax
    """
    if self.url == '/form':
      logging.warning(
          'The URL path "/form" is reserved and will not be matched.')

  def ErrorOnPositionForAppInfo(self):
    """Raises an error if position is specified outside of AppInclude objects.

    Raises:
      PositionUsedInAppYamlHandler: If the `position` attribute is specified for
          an `app.yaml` file instead of an `include.yaml` file.
    """
    if self.position:
      raise appinfo_errors.PositionUsedInAppYamlHandler(
          'The position attribute was specified for this handler, but this is '
          'an app.yaml file.  Position attribute is only valid for '
          'include.yaml files.')


class AdminConsolePage(validation.Validated):
  """Class representing the admin console page in an `AdminConsole` object."""
  ATTRIBUTES = {
      URL: _URL_REGEX,
      NAME: _PAGE_NAME_REGEX,
  }


class AdminConsole(validation.Validated):
  """Class representing an admin console directives in application info."""
  ATTRIBUTES = {
      PAGES: validation.Optional(validation.Repeated(AdminConsolePage)),
  }

  @classmethod
  def Merge(cls, adminconsole_one, adminconsole_two):
    """Returns the result of merging two `AdminConsole` objects."""
    # Right now this method only needs to worry about the pages attribute of
    # `AdminConsole`. However, since this object is valid as part of an
    # `AppInclude` object, any objects added to `AdminConsole` in the future
    # must also be merged.  Rather than burying the merge logic in the process
    # of merging two `AppInclude` objects, it is centralized here. If you modify
    # the `AdminConsole` object to support other objects, you must also modify
    # this method to support merging those additional objects.

    if not adminconsole_one or not adminconsole_two:
      return adminconsole_one or adminconsole_two

    if adminconsole_one.pages:
      if adminconsole_two.pages:
        adminconsole_one.pages.extend(adminconsole_two.pages)
    else:
      adminconsole_one.pages = adminconsole_two.pages

    return adminconsole_one


class ErrorHandlers(validation.Validated):
  """Class representing error handler directives in application info."""
  ATTRIBUTES = {
      ERROR_CODE: validation.Optional(_ERROR_CODE_REGEX),
      FILE: _FILES_REGEX,
      MIME_TYPE: validation.Optional(str),
  }


class BuiltinHandler(validation.Validated):
  """Class representing built-in handler directives in application info.

  This class permits arbitrary keys, but their values must be described by the
  `validation.Options` object that is returned by `ATTRIBUTES`.
  """

  # `Validated` is a somewhat complicated class. It actually maintains two
  # dictionaries: the `ATTRIBUTES` dictionary and an internal `__dict__` object
  # that maintains key value pairs.
  #
  # The normal flow is that a key must exist in `ATTRIBUTES` in order to be able
  # to be inserted into `__dict__`. So that's why we force the
  # `ATTRIBUTES.__contains__` method to always return `True`; we want to accept
  # any attribute. Once the method returns `True`, then its value will be
  # fetched, which returns `ATTRIBUTES[key]`; that's why we override
  # `ATTRIBUTES.__getitem__` to return the validator for a `BuiltinHandler`
  # object.
  #
  # This is where it gets tricky. Once the validator object is returned, then
  # `__dict__[key]` is set to the validated object for that key. However, when
  # `CheckInitialized()` is called, it uses iteritems from `ATTRIBUTES` in order
  # to generate a list of keys to validate. This expects the `BuiltinHandler`
  # instance to contain every item in `ATTRIBUTES`, which contains every
  # built-in name seen so far by any `BuiltinHandler`. To work around this,
  # `__getattr__` always returns `None` for public attribute names. Note that
  # `__getattr__` is only called if `__dict__` does not contain the key. Thus,
  # the single built-in value set is validated.
  #
  # What's important to know is that in this implementation, only the keys in
  # `ATTRIBUTES` matter, and only the values in `__dict__` matter. The values in
  # `ATTRIBUTES` and the keys in `__dict__` are both ignored. The key in
  # `__dict__` is only used for the `__getattr__` function, but to find out what
  # keys are available, only `ATTRIBUTES` is ever read.

  class DynamicAttributes(dict):
    """Provides a dictionary object that will always claim to have a key.

    This dictionary returns a fixed value for any `get` operation. The fixed
    value that you pass in as a constructor parameter should be a
    `validation.Validated` object.
    """

    def __init__(self, return_value, **parameters):
      self.__return_value = return_value
      dict.__init__(self, parameters)

    def __contains__(self, _):
      return True

    def __getitem__(self, _):
      return self.__return_value

  ATTRIBUTES = DynamicAttributes(
      validation.Optional(validation.Options((ON, ON_ALIASES),
                                             (OFF, OFF_ALIASES))))

  def __init__(self, **attributes):
    """Ensures all BuiltinHandler objects at least use the `default` attribute.

    Args:
      **attributes: The attributes that you want to use.
    """
    self.builtin_name = ''
    super(BuiltinHandler, self).__init__(**attributes)

  def __setattr__(self, key, value):
    """Allows `ATTRIBUTES.iteritems()` to return set of items that have values.

    Whenever `validate` calls `iteritems()`, it is always called on
    `ATTRIBUTES`, not on `__dict__`, so this override is important to ensure
    that functions such as `ToYAML()` return the correct set of keys.

    Args:
      key: The key for the `iteritem` that you want to set.
      value: The value for the `iteritem` that you want to set.

    Raises:
      MultipleBuiltinsSpecified: If more than one built-in is defined in a list
          element.
    """
    if key == 'builtin_name':
      object.__setattr__(self, key, value)
    elif not self.builtin_name:
      self.ATTRIBUTES[key] = ''
      self.builtin_name = key
      super(BuiltinHandler, self).__setattr__(key, value)
    else:
      # Only the name of a built-in handler is currently allowed as an attribute
      # so the object can only be set once. If later attributes are desired of
      # a different form, this clause should be used to catch whenever more than
      # one object does not match a predefined attribute name.
      raise appinfo_errors.MultipleBuiltinsSpecified(
          'More than one builtin defined in list element.  Each new builtin '
          'should be prefixed by "-".')

  def __getattr__(self, key):
    if key.startswith('_'):
      # `__getattr__` is only called for attributes that don't exist in the
      # instance dictionary.
      raise AttributeError
    return None

  def GetUnnormalized(self, key):
    try:
      return super(BuiltinHandler, self).GetUnnormalized(key)
    except AttributeError:
      return getattr(self, key)

  def ToDict(self):
    """Converts a `BuiltinHander` object to a dictionary.

    Returns:
      A dictionary in `{builtin_handler_name: on/off}` form
    """
    return {self.builtin_name: getattr(self, self.builtin_name)}

  @classmethod
  def IsDefined(cls, builtins_list, builtin_name):
    """Finds if a builtin is defined in a given list of builtin handler objects.

    Args:
      builtins_list: A list of `BuiltinHandler` objects, typically
          `yaml.builtins`.
      builtin_name: The name of the built-in that you want to determine whether
          it is defined.

    Returns:
      `True` if `builtin_name` is defined by a member of `builtins_list`; all
      other results return `False`.
    """
    for b in builtins_list:
      if b.builtin_name == builtin_name:
        return True
    return False

  @classmethod
  def ListToTuples(cls, builtins_list):
    """Converts a list of `BuiltinHandler` objects.

    Args:
      builtins_list: A list of `BuildinHandler` objects to convert to tuples.

    Returns:
      A list of `(name, status)` that is derived from the `BuiltinHandler`
      objects.
    """
    return [(b.builtin_name, getattr(b, b.builtin_name)) for b in builtins_list]

  @classmethod
  def Validate(cls, builtins_list, runtime=None):
    """Verifies that all `BuiltinHandler` objects are valid and not repeated.

    Args:
      builtins_list: A list of `BuiltinHandler` objects to validate.
      runtime: If you specify this argument, warnings are generated for
          built-ins that have been deprecated in the given runtime.

    Raises:
      InvalidBuiltinFormat: If the name of a `BuiltinHandler` object cannot be
          determined.
      DuplicateBuiltinsSpecified: If a `BuiltinHandler` name is used more than
          once in the list.
    """
    seen = set()
    for b in builtins_list:
      if not b.builtin_name:
        raise appinfo_errors.InvalidBuiltinFormat(
            'Name of builtin for list object %s could not be determined.'
            % b)
      if b.builtin_name in seen:
        raise appinfo_errors.DuplicateBuiltinsSpecified(
            'Builtin %s was specified more than once in one yaml file.'
            % b.builtin_name)

      # This checking must be done here rather than in `apphosting/ext/builtins`
      # because `apphosting/ext/builtins` cannot differentiate between between
      # built-ins specified in `app.yaml` versus ones added in a built-in
      # include. There is a hole here where warnings are not generated for
      # deprecated built-ins that appear in user-created include files.
      if b.builtin_name == 'datastore_admin' and runtime == 'python':
        logging.warning(
            'The datastore_admin builtin is deprecated. You can find '
            'information on how to enable it through the Administrative '
            'Console here: '
            'http://developers.google.com/appengine/docs/adminconsole/'
            'datastoreadmin.html')
      elif b.builtin_name == 'mapreduce' and runtime == 'python':
        logging.warning(
            'The mapreduce builtin is deprecated. You can find more '
            'information on how to configure and use it here: '
            'http://developers.google.com/appengine/docs/python/dataprocessing/'
            'overview.html')

      seen.add(b.builtin_name)


class ApiConfigHandler(HandlerBase):
  """Class representing `api_config` handler directives in application info."""
  ATTRIBUTES = HandlerBase.ATTRIBUTES
  ATTRIBUTES.update({
      # Make `URL` and `SCRIPT` required for `api_config` stanza
      URL: validation.Regex(_URL_REGEX),
      HANDLER_SCRIPT: validation.Regex(_FILES_REGEX)
  })


class Library(validation.Validated):
  """Class representing the configuration of a single library."""

  ATTRIBUTES = {'name': validation.Type(str),
                'version': validation.Type(str)}

  def CheckInitialized(self):
    """Determines if the library configuration is not valid.

    Raises:
      appinfo_errors.InvalidLibraryName: If the specified library is not
          supported.
      appinfo_errors.InvalidLibraryVersion: If the specified library version is
          not supported.
    """
    super(Library, self).CheckInitialized()
    if self.name not in _NAME_TO_SUPPORTED_LIBRARY:
      raise appinfo_errors.InvalidLibraryName(
          'the library "%s" is not supported' % self.name)
    supported_library = _NAME_TO_SUPPORTED_LIBRARY[self.name]
    if self.version == 'latest':
      self.version = supported_library.latest_version
    elif self.version not in supported_library.supported_versions:
      raise appinfo_errors.InvalidLibraryVersion(
          ('%s version "%s" is not supported, ' + _USE_VERSION_FORMAT) % (
              self.name,
              self.version,
              '", "'.join(supported_library.non_deprecated_versions)))
    elif self.version in supported_library.deprecated_versions:
      use_vers = '", "'.join(supported_library.non_deprecated_versions)
      logging.warning(
          '%s version "%s" is deprecated, ' + _USE_VERSION_FORMAT,
          self.name,
          self.version,
          use_vers)


class CpuUtilization(validation.Validated):
  """Class representing the configuration of VM CPU utilization."""

  ATTRIBUTES = {
      CPU_UTILIZATION_UTILIZATION: validation.Optional(
          validation.Range(1e-6, 1.0, float)),
      CPU_UTILIZATION_AGGREGATION_WINDOW_LENGTH_SEC: validation.Optional(
          validation.Range(1, sys.maxsize)),
  }


class CustomMetric(validation.Validated):
  """Class representing CustomMetrics in AppInfoExternal."""

  ATTRIBUTES = {
      METRIC_NAME: validation.Regex(_NON_WHITE_SPACE_REGEX),
      TARGET_TYPE: validation.Regex(TARGET_TYPE_REGEX),
      CUSTOM_METRIC_UTILIZATION: validation.Optional(validation.TYPE_FLOAT),
      SINGLE_INSTANCE_ASSIGNMENT: validation.Optional(validation.TYPE_FLOAT),
      FILTER: validation.Optional(validation.TYPE_STR),
  }

  def CheckInitialized(self):
    """Determines if the CustomMetric is not valid.

    Raises:
      appinfo_errors.TooManyAutoscalingUtilizationTargetsError: If too many
      scaling targets are set.
      appinfo_errors.NotEnoughAutoscalingUtilizationTargetsError: If no scaling
      targets are set.
    """
    super(CustomMetric, self).CheckInitialized()
    if bool(self.target_utilization) and bool(self.single_instance_assignment):
      raise appinfo_errors.TooManyAutoscalingUtilizationTargetsError(
          ("There may be only one of '%s' or '%s'." % CUSTOM_METRIC_UTILIZATION,
           SINGLE_INSTANCE_ASSIGNMENT))
    elif not (bool(self.target_utilization) or
              bool(self.single_instance_assignment)):
      raise appinfo_errors.NotEnoughAutoscalingUtilizationTargetsError(
          ("There must be one of '%s' or '%s'." % CUSTOM_METRIC_UTILIZATION,
           SINGLE_INSTANCE_ASSIGNMENT))


class EndpointsApiService(validation.Validated):
  """Class representing EndpointsApiService in AppInfoExternal."""
  ATTRIBUTES = {
      ENDPOINTS_NAME:
          validation.Regex(_NON_WHITE_SPACE_REGEX),
      ROLLOUT_STRATEGY:
          validation.Optional(
              validation.Options(ROLLOUT_STRATEGY_FIXED,
                                 ROLLOUT_STRATEGY_MANAGED)),
      CONFIG_ID:
          validation.Optional(_NON_WHITE_SPACE_REGEX),
      TRACE_SAMPLING:
          validation.Optional(validation.TYPE_BOOL),
  }

  def CheckInitialized(self):
    """Determines if the Endpoints API Service is not valid.

    Raises:
      appinfo_errors.MissingEndpointsConfigId: If the config id is missing when
          the rollout strategy is unspecified or set to "fixed".
      appinfo_errors.UnexpectedEndpointsConfigId: If the config id is set when
          the rollout strategy is "managed".
    """
    super(EndpointsApiService, self).CheckInitialized()
    if (self.rollout_strategy != ROLLOUT_STRATEGY_MANAGED and
        self.config_id is None):
      raise appinfo_errors.MissingEndpointsConfigId(
          'config_id must be specified when rollout_strategy is unspecified or'
          ' set to "fixed"')
    elif (self.rollout_strategy == ROLLOUT_STRATEGY_MANAGED and
          self.config_id is not None):
      raise appinfo_errors.UnexpectedEndpointsConfigId(
          'config_id is forbidden when rollout_strategy is set to "managed"')


class AutomaticScaling(validation.Validated):
  """Class representing automatic scaling settings in AppInfoExternal."""
  ATTRIBUTES = {
      MINIMUM_IDLE_INSTANCES:
          validation.Optional(_IDLE_INSTANCES_REGEX),
      MAXIMUM_IDLE_INSTANCES:
          validation.Optional(_IDLE_INSTANCES_REGEX),
      MINIMUM_PENDING_LATENCY:
          validation.Optional(_PENDING_LATENCY_REGEX),
      MAXIMUM_PENDING_LATENCY:
          validation.Optional(_PENDING_LATENCY_REGEX),
      MAXIMUM_CONCURRENT_REQUEST:
          validation.Optional(_CONCURRENT_REQUESTS_REGEX),
      # Attributes for VM-based AutomaticScaling.
      MIN_NUM_INSTANCES:
          validation.Optional(validation.Range(1, sys.maxsize)),
      MAX_NUM_INSTANCES:
          validation.Optional(validation.Range(1, sys.maxsize)),
      COOL_DOWN_PERIOD_SEC:
          validation.Optional(validation.Range(60, sys.maxsize, int)),
      CPU_UTILIZATION:
          validation.Optional(CpuUtilization),
      STANDARD_MAX_INSTANCES:
          validation.Optional(validation.TYPE_INT),
      STANDARD_MIN_INSTANCES:
          validation.Optional(validation.TYPE_INT),
      STANDARD_TARGET_CPU_UTILIZATION:
          validation.Optional(validation.TYPE_FLOAT),
      STANDARD_TARGET_THROUGHPUT_UTILIZATION:
          validation.Optional(validation.TYPE_FLOAT),
      TARGET_NETWORK_SENT_BYTES_PER_SEC:
          validation.Optional(validation.Range(1, sys.maxsize)),
      TARGET_NETWORK_SENT_PACKETS_PER_SEC:
          validation.Optional(validation.Range(1, sys.maxsize)),
      TARGET_NETWORK_RECEIVED_BYTES_PER_SEC:
          validation.Optional(validation.Range(1, sys.maxsize)),
      TARGET_NETWORK_RECEIVED_PACKETS_PER_SEC:
          validation.Optional(validation.Range(1, sys.maxsize)),
      TARGET_DISK_WRITE_BYTES_PER_SEC:
          validation.Optional(validation.Range(1, sys.maxsize)),
      TARGET_DISK_WRITE_OPS_PER_SEC:
          validation.Optional(validation.Range(1, sys.maxsize)),
      TARGET_DISK_READ_BYTES_PER_SEC:
          validation.Optional(validation.Range(1, sys.maxsize)),
      TARGET_DISK_READ_OPS_PER_SEC:
          validation.Optional(validation.Range(1, sys.maxsize)),
      TARGET_REQUEST_COUNT_PER_SEC:
          validation.Optional(validation.Range(1, sys.maxsize)),
      TARGET_CONCURRENT_REQUESTS:
          validation.Optional(validation.Range(1, sys.maxsize)),
      CUSTOM_METRICS: validation.Optional(validation.Repeated(CustomMetric)),
  }


class ManualScaling(validation.Validated):
  """Class representing manual scaling settings in AppInfoExternal."""
  ATTRIBUTES = {
      INSTANCES: validation.Regex(_INSTANCES_REGEX),
  }


class BasicScaling(validation.Validated):
  """Class representing basic scaling settings in AppInfoExternal."""
  ATTRIBUTES = {
      MAX_INSTANCES: validation.Regex(_INSTANCES_REGEX),
      IDLE_TIMEOUT: validation.Optional(_IDLE_TIMEOUT_REGEX),
  }


class RuntimeConfig(validation.ValidatedDict):
  """Class for "vanilla" runtime configuration.

  Fields used vary by runtime, so validation is delegated to the per-runtime
  build processes.

  These are intended to be used during Dockerfile generation, not after VM boot.
  """

  KEY_VALIDATOR = validation.Regex('[a-zA-Z_][a-zA-Z0-9_]*')
  VALUE_VALIDATOR = str

class FlexibleRuntimeSettings(validation.Validated):
  """Class for App Engine Flexible runtime settings."""
  ATTRIBUTES = {
      OPERATING_SYSTEM: validation.Regex('[a-z0-9]+'),
      RUNTIME_VERSION: validation.Optional(str)
  }

class VmSettings(validation.ValidatedDict):
  """Class for VM settings.

  The settings are not further validated here. The settings are validated on
  the server side.
  """

  KEY_VALIDATOR = validation.Regex('[a-zA-Z_][a-zA-Z0-9_]*')
  VALUE_VALIDATOR = str

  @classmethod
  def Merge(cls, vm_settings_one, vm_settings_two):
    """Merges two `VmSettings` instances.

    If a variable is specified by both instances, the value from
    `vm_settings_one` is used.

    Args:
      vm_settings_one: The first `VmSettings` instance, or `None`.
      vm_settings_two: The second `VmSettings` instance, or `None`.

    Returns:
      The merged `VmSettings` instance, or `None` if both input instances are
      `None` or empty.
    """
    # Note that `VmSettings.copy()` results in a dict.
    result_vm_settings = (vm_settings_two or {}).copy()
    # TODO(user): Apply merge logic when feature is fully defined.
    # For now, we will merge the two dict and `vm_settings_one` will win
    # if key collides.
    result_vm_settings.update(vm_settings_one or {})
    return VmSettings(**result_vm_settings) if result_vm_settings else None


class BetaSettings(VmSettings):
  """Class for Beta (internal or unreleased) settings.

  This class is meant to replace `VmSettings` eventually.

  Note:
      All new beta settings must be registered in `shared_constants.py`.

  These settings are not validated further here. The settings are validated on
  the server side.
  """

  @classmethod
  def Merge(cls, beta_settings_one, beta_settings_two):
    """Merges two `BetaSettings` instances.

    Args:
      beta_settings_one: The first `BetaSettings` instance, or `None`.
      beta_settings_two: The second `BetaSettings` instance, or `None`.

    Returns:
      The merged `BetaSettings` instance, or `None` if both input instances are
      `None` or empty.
    """
    merged = VmSettings.Merge(beta_settings_one, beta_settings_two)
    return BetaSettings(**merged.ToDict()) if merged else None


class EnvironmentVariables(validation.ValidatedDict):
  """Class representing a mapping of environment variable key/value pairs."""

  KEY_VALIDATOR = validation.Regex('[a-zA-Z_][a-zA-Z0-9_]*')
  VALUE_VALIDATOR = str

  @classmethod
  def Merge(cls, env_variables_one, env_variables_two):
    """Merges two `EnvironmentVariables` instances.

    If a variable is specified by both instances, the value from
    `env_variables_two` is used.

    Args:
      env_variables_one: The first `EnvironmentVariables` instance or `None`.
      env_variables_two: The second `EnvironmentVariables` instance or `None`.

    Returns:
      The merged `EnvironmentVariables` instance, or `None` if both input
      instances are `None` or empty.
    """
    # Note that `EnvironmentVariables.copy()` results in a dict.
    result_env_variables = (env_variables_one or {}).copy()
    result_env_variables.update(env_variables_two or {})
    return (EnvironmentVariables(**result_env_variables)
            if result_env_variables else None)


def ValidateSourceReference(ref):
  """Determines if a source reference is valid.

  Args:
    ref: A source reference in the following format:
        `[repository_uri#]revision`.

  Raises:
    ValidationError: If the reference is malformed.
  """
  repo_revision = ref.split('#', 1)
  revision_id = repo_revision[-1]
  if not re.match(SOURCE_REVISION_RE_STRING, revision_id):
    raise validation.ValidationError('Bad revision identifier: %s' %
                                     revision_id)

  if len(repo_revision) == 2:
    uri = repo_revision[0]
    if not re.match(SOURCE_REPO_RE_STRING, uri):
      raise validation.ValidationError('Bad repository URI: %s' % uri)


def ValidateCombinedSourceReferencesString(source_refs):
  """Determines if `source_refs` contains a valid list of source references.

  Args:
    source_refs: A multi-line string containing one source reference per line.

  Raises:
    ValidationError: If the reference is malformed.
  """
  if len(source_refs) > SOURCE_REFERENCES_MAX_SIZE:
    raise validation.ValidationError(
        'Total source reference(s) size exceeds the limit: %d > %d' % (
            len(source_refs), SOURCE_REFERENCES_MAX_SIZE))

  for ref in source_refs.splitlines():
    ValidateSourceReference(ref.strip())


class HealthCheck(validation.Validated):
  """Class representing the health check configuration."""
  ATTRIBUTES = {
      ENABLE_HEALTH_CHECK: validation.Optional(validation.TYPE_BOOL),
      CHECK_INTERVAL_SEC: validation.Optional(validation.Range(0, sys.maxsize)),
      TIMEOUT_SEC: validation.Optional(validation.Range(0, sys.maxsize)),
      UNHEALTHY_THRESHOLD: validation.Optional(
          validation.Range(0, sys.maxsize)),
      HEALTHY_THRESHOLD: validation.Optional(validation.Range(0, sys.maxsize)),
      RESTART_THRESHOLD: validation.Optional(validation.Range(0, sys.maxsize)),
      HOST: validation.Optional(validation.TYPE_STR)}


class LivenessCheck(validation.Validated):
  """Class representing the liveness check configuration."""
  ATTRIBUTES = {
      CHECK_INTERVAL_SEC: validation.Optional(validation.Range(0, sys.maxsize)),
      TIMEOUT_SEC: validation.Optional(validation.Range(0, sys.maxsize)),
      FAILURE_THRESHOLD: validation.Optional(validation.Range(0, sys.maxsize)),
      SUCCESS_THRESHOLD: validation.Optional(validation.Range(0, sys.maxsize)),
      INITIAL_DELAY_SEC: validation.Optional(validation.Range(0, sys.maxsize)),
      PATH: validation.Optional(validation.TYPE_STR),
      HOST: validation.Optional(validation.TYPE_STR)}


class ReadinessCheck(validation.Validated):
  """Class representing the readiness check configuration."""
  ATTRIBUTES = {
      CHECK_INTERVAL_SEC: validation.Optional(validation.Range(0, sys.maxsize)),
      TIMEOUT_SEC: validation.Optional(validation.Range(0, sys.maxsize)),
      APP_START_TIMEOUT_SEC: validation.Optional(
          validation.Range(0, sys.maxsize)),
      FAILURE_THRESHOLD: validation.Optional(validation.Range(0, sys.maxsize)),
      SUCCESS_THRESHOLD: validation.Optional(validation.Range(0, sys.maxsize)),
      PATH: validation.Optional(validation.TYPE_STR),
      HOST: validation.Optional(validation.TYPE_STR)}


class VmHealthCheck(HealthCheck):
  """Class representing the configuration of the VM health check.

  Note:
      This class is deprecated and will be removed in a future release. Use
      `HealthCheck` instead.
  """
  pass


class Volume(validation.Validated):
  """Class representing the configuration of a volume."""

  ATTRIBUTES = {
      VOLUME_NAME: validation.TYPE_STR,
      SIZE_GB: validation.TYPE_FLOAT,
      VOLUME_TYPE: validation.TYPE_STR,
  }


class Resources(validation.Validated):
  """Class representing the configuration of VM resources."""

  ATTRIBUTES = {
      CPU: validation.Optional(validation.TYPE_FLOAT),
      MEMORY_GB: validation.Optional(validation.TYPE_FLOAT),
      DISK_SIZE_GB: validation.Optional(validation.TYPE_INT),
      VOLUMES: validation.Optional(validation.Repeated(Volume))
  }


class Network(validation.Validated):
  """Class representing the VM network configuration."""

  ATTRIBUTES = {
      # A list of port mappings in the form 'port' or 'external:internal'.
      FORWARDED_PORTS:
          validation.Optional(
              validation.Repeated(
                  validation.Regex('[0-9]+(:[0-9]+)?(/(udp|tcp))?'))),
      INSTANCE_TAG:
          validation.Optional(validation.Regex(GCE_RESOURCE_NAME_REGEX)),
      NETWORK_NAME:
          validation.Optional(validation.Regex(GCE_RESOURCE_PATH_REGEX)),
      SUBNETWORK_NAME:
          validation.Optional(validation.Regex(GCE_RESOURCE_NAME_REGEX)),
      SESSION_AFFINITY:
          validation.Optional(bool),
      INSTANCE_IP_MODE:
          validation.Optional(validation.Regex(FLEX_INSTANCE_IP_MODE_REGEX))
  }


class VpcAccessConnector(validation.Validated):
  """Class representing the VPC Access connector configuration."""

  ATTRIBUTES = {
      VPC_ACCESS_CONNECTOR_NAME:
          validation.Regex(VPC_ACCESS_CONNECTOR_NAME_REGEX),
      VPC_ACCESS_CONNECTOR_EGRESS_SETTING:
          validation.Optional(
              validation.Options(
                  VPC_ACCESS_CONNECTOR_EGRESS_SETTING_ALL_TRAFFIC,
                  VPC_ACCESS_CONNECTOR_EGRESS_SETTING_PRIVATE_RANGES_ONLY))
  }


class AppInclude(validation.Validated):
  """Class representing the contents of an included `app.yaml` file.

  This class is used for both `builtins` and `includes` directives.
  """

  # TODO(user): It probably makes sense to have a scheme where we do a
  # deep-copy of fields from `AppInfoExternal` when setting the `ATTRIBUTES`
  # here. Right now it's just copypasta.
  ATTRIBUTES = {
      BUILTINS: validation.Optional(validation.Repeated(BuiltinHandler)),
      INCLUDES: validation.Optional(validation.Type(list)),
      HANDLERS: validation.Optional(validation.Repeated(URLMap), default=[]),
      ADMIN_CONSOLE: validation.Optional(AdminConsole),
      MANUAL_SCALING: validation.Optional(ManualScaling),
      VM: validation.Optional(bool),
      VM_SETTINGS: validation.Optional(VmSettings),
      BETA_SETTINGS: validation.Optional(BetaSettings),
      ENV_VARIABLES: validation.Optional(EnvironmentVariables),
      BUILD_ENV_VARIABLES: validation.Optional(EnvironmentVariables),
      SKIP_FILES: validation.RegexStr(default=SKIP_NO_FILES),
      # TODO(user): add `LIBRARIES` here when we have a good story for
      # handling contradictory library requests.
  }

  @classmethod
  def MergeManualScaling(cls, appinclude_one, appinclude_two):
    """Takes the greater of `<manual_scaling.instances>` from the arguments.

    `appinclude_one` is mutated to be the merged result in this process.

    Also, this function must be updated if `ManualScaling` gets additional
    fields.

    Args:
      appinclude_one: The first object to merge. The object must have a
          `manual_scaling` field that contains a `ManualScaling()`.
      appinclude_two: The second object to merge. The object must have a
          `manual_scaling` field that contains a `ManualScaling()`.
    Returns:
      An object that is the result of merging
      `appinclude_one.manual_scaling.instances` and
      `appinclude_two.manual_scaling.instances`; this is returned as a revised
      `appinclude_one` object after the mutations are complete.
    """

    def _Instances(appinclude):
      """Determines the number of `manual_scaling.instances` sets.

      Args:
        appinclude: The include for which you want to determine the number of
            `manual_scaling.instances` sets.

      Returns:
        The number of instances as an integer. If the value of
        `manual_scaling.instances` evaluates to False (e.g. 0 or None), then
        return 0.
      """
      if appinclude.manual_scaling:
        if appinclude.manual_scaling.instances:
          return int(appinclude.manual_scaling.instances)
      return 0

    # We only want to mutate a param if at least one of the given
    # arguments has manual_scaling.instances set.
    if _Instances(appinclude_one) or _Instances(appinclude_two):
      instances = max(_Instances(appinclude_one), _Instances(appinclude_two))
      appinclude_one.manual_scaling = ManualScaling(instances=str(instances))
    return appinclude_one

  @classmethod
  def _CommonMergeOps(cls, one, two):
    """This function performs common merge operations.

    Args:
      one: The first object that you want to merge.
      two: The second object that you want to merge.

    Returns:
      An updated `one` object containing all merged data.
    """
    # Merge `ManualScaling`.
    AppInclude.MergeManualScaling(one, two)

    # Merge `AdminConsole` objects.
    one.admin_console = AdminConsole.Merge(one.admin_console,
                                           two.admin_console)

    # Preserve the specific value of `one.vm` (`None` or `False`) when neither
    # are `True`.
    one.vm = two.vm or one.vm

    # Merge `VmSettings` objects.
    one.vm_settings = VmSettings.Merge(one.vm_settings,
                                       two.vm_settings)

    # Merge `BetaSettings` objects.
    if hasattr(one, 'beta_settings'):
      one.beta_settings = BetaSettings.Merge(one.beta_settings,
                                             two.beta_settings)

    # Merge `EnvironmentVariables` objects. The values in `two.env_variables`
    # override the ones in `one.env_variables` in case of conflict.
    one.env_variables = EnvironmentVariables.Merge(one.env_variables,
                                                   two.env_variables)

    one.skip_files = cls.MergeSkipFiles(one.skip_files, two.skip_files)

    return one

  @classmethod
  def MergeAppYamlAppInclude(cls, appyaml, appinclude):
    """Merges an `app.yaml` file with referenced builtins/includes.

    Args:
      appyaml: The `app.yaml` file that you want to update with `appinclude`.
      appinclude: The includes that you want to merge into `appyaml`.

    Returns:
      An updated `app.yaml` file that includes the directives you specified in
      `appinclude`.
    """
    # All merge operations should occur in this function or in functions
    # referenced from this one.  That makes it much easier to understand what
    # goes wrong when included files are not merged correctly.

    if not appinclude:
      return appyaml

    # Merge handlers while paying attention to `position` attribute.
    if appinclude.handlers:
      tail = appyaml.handlers or []
      appyaml.handlers = []

      for h in appinclude.handlers:
        if not h.position or h.position == 'head':
          appyaml.handlers.append(h)
        else:
          tail.append(h)
        # Get rid of the `position` attribute since we no longer need it, and is
        # technically invalid to include in the resulting merged `app.yaml` file
        # that will be sent when deploying the application.
        h.position = None

      appyaml.handlers.extend(tail)

    appyaml = cls._CommonMergeOps(appyaml, appinclude)
    appyaml.NormalizeVmSettings()
    return appyaml

  @classmethod
  def MergeAppIncludes(cls, appinclude_one, appinclude_two):
    """Merges the non-referential state of the provided `AppInclude`.

    That is, `builtins` and `includes` directives are not preserved, but any
    static objects are copied into an aggregate `AppInclude` object that
    preserves the directives of both provided `AppInclude` objects.

    `appinclude_one` is updated to be the merged result in this process.

    Args:
      appinclude_one: First `AppInclude` to merge.
      appinclude_two: Second `AppInclude` to merge.

    Returns:
      `AppInclude` object that is the result of merging the static directives of
      `appinclude_one` and `appinclude_two`. An updated version of
      `appinclude_one` is returned.
    """

    # If one or both `appinclude` objects were `None`, return the object that
    # was not `None` or return `None`.
    if not appinclude_one or not appinclude_two:
      return appinclude_one or appinclude_two
    # Now, both `appincludes` are non-`None`.

    # Merge handlers.
    if appinclude_one.handlers:
      if appinclude_two.handlers:
        appinclude_one.handlers.extend(appinclude_two.handlers)
    else:
      appinclude_one.handlers = appinclude_two.handlers

    return cls._CommonMergeOps(appinclude_one, appinclude_two)

  @staticmethod
  def MergeSkipFiles(skip_files_one, skip_files_two):
    """Merges two `skip_files` directives.

    Args:
      skip_files_one: The first `skip_files` element that you want to merge.
      skip_files_two: The second `skip_files` element that you want to merge.

    Returns:
      A list of regular expressions that are merged.
    """
    if skip_files_one == SKIP_NO_FILES:
      return skip_files_two
    if skip_files_two == SKIP_NO_FILES:
      return skip_files_one
    return validation.RegexStr().Validate(
        [skip_files_one, skip_files_two], SKIP_FILES)
    # We exploit the handling of RegexStr where regex properties can be
    # specified as a list of regexes that are then joined with |.


class AppInfoExternal(validation.Validated):
  """Class representing users application info.

  This class is passed to a `yaml_object` builder to provide the validation
  for the application information file format parser.

  Attributes:
    application: Unique identifier for application.
    version: Application's major version.
    runtime: Runtime used by application.
    api_version: Which version of APIs to use.
    source_language: Optional specification of the source language. For example,
        you could specify `php-quercus` if this is a Java app that was generated
        from PHP source using Quercus.
    handlers: List of URL handlers.
    default_expiration: Default time delta to use for cache expiration for
        all static files, unless they have their own specific `expiration` set.
        See the documentation for the `URLMap.expiration` field for more
        information.
    skip_files: A regular expression object. Files that match this regular
        expression will not be uploaded by `appcfg.py`. For example::
            skip_files: |
              .svn.*|
              #.*#
    nobuild_files: A regular expression object. Files that match this regular
        expression will not be built into the app. This directive is valid for
        Go only.
    api_config: URL root and script or servlet path for enhanced API serving.
  """

  ATTRIBUTES = {
      # Regular expressions for these attributes are defined in
      # //apphosting/base/id_util.cc.
      APPLICATION: validation.Optional(APPLICATION_RE_STRING),
      # An alias for `APPLICATION`.
      PROJECT: validation.Optional(APPLICATION_RE_STRING),
      SERVICE: validation.Preferred(MODULE,
                                    validation.Optional(MODULE_ID_RE_STRING)),
      MODULE: validation.Deprecated(SERVICE,
                                    validation.Optional(MODULE_ID_RE_STRING)),
      VERSION: validation.Optional(MODULE_VERSION_ID_RE_STRING),
      RUNTIME: validation.Optional(RUNTIME_RE_STRING),
      RUNTIME_CHANNEL: validation.Optional(validation.Type(str)),
      # A new `api_version` requires a release of the `dev_appserver`, so it
      # is ok to hardcode the version names here.
      API_VERSION: validation.Optional(API_VERSION_RE_STRING),
      MAIN: validation.Optional(_FILES_REGEX),
      # The App Engine environment to run this version in. (VM vs. non-VM, etc.)
      ENV: validation.Optional(ENV_RE_STRING),
      ENDPOINTS_API_SERVICE: validation.Optional(EndpointsApiService),
      # The SDK will use this for generated Dockerfiles
      # hasattr guard the new Exec() validator temporarily
      ENTRYPOINT: validation.Optional(
          validation.Exec() if hasattr(
              validation, 'Exec') else validation.Type(str)),
      RUNTIME_CONFIG: validation.Optional(RuntimeConfig),
      INSTANCE_CLASS: validation.Optional(validation.Type(str)),
      SOURCE_LANGUAGE: validation.Optional(
          validation.Regex(SOURCE_LANGUAGE_RE_STRING)),
      AUTOMATIC_SCALING: validation.Optional(AutomaticScaling),
      MANUAL_SCALING: validation.Optional(ManualScaling),
      BASIC_SCALING: validation.Optional(BasicScaling),
      VM: validation.Optional(bool),
      VM_SETTINGS: validation.Optional(VmSettings),  # Deprecated
      BETA_SETTINGS: validation.Optional(BetaSettings),
      VM_HEALTH_CHECK: validation.Optional(VmHealthCheck),  # Deprecated
      HEALTH_CHECK: validation.Optional(HealthCheck),
      RESOURCES: validation.Optional(Resources),
      LIVENESS_CHECK: validation.Optional(LivenessCheck),
      READINESS_CHECK: validation.Optional(ReadinessCheck),
      NETWORK: validation.Optional(Network),
      VPC_ACCESS_CONNECTOR: validation.Optional(VpcAccessConnector),
      ZONES: validation.Optional(validation.Repeated(validation.TYPE_STR)),
      BUILTINS: validation.Optional(validation.Repeated(BuiltinHandler)),
      INCLUDES: validation.Optional(validation.Type(list)),
      HANDLERS: validation.Optional(validation.Repeated(URLMap), default=[]),
      LIBRARIES: validation.Optional(validation.Repeated(Library)),
      # TODO(user): change to a regex when `validation.Repeated` supports it
      SERVICES: validation.Optional(validation.Repeated(
          validation.Regex(_SERVICE_RE_STRING))),
      DEFAULT_EXPIRATION: validation.Optional(_EXPIRATION_REGEX),
      SKIP_FILES: validation.RegexStr(default=DEFAULT_SKIP_FILES),
      NOBUILD_FILES: validation.RegexStr(default=DEFAULT_NOBUILD_FILES),
      DERIVED_FILE_TYPE: validation.Optional(validation.Repeated(
          validation.Options(JAVA_PRECOMPILED, PYTHON_PRECOMPILED))),
      ADMIN_CONSOLE: validation.Optional(AdminConsole),
      ERROR_HANDLERS: validation.Optional(validation.Repeated(ErrorHandlers)),
      BACKENDS: validation.Optional(validation.Repeated(
          backendinfo.BackendEntry)),
      THREADSAFE: validation.Optional(bool),
      SERVICEACCOUNT: validation.Optional(validation.Type(str)),
      DATASTORE_AUTO_ID_POLICY: validation.Optional(
          validation.Options(DATASTORE_ID_POLICY_LEGACY,
                             DATASTORE_ID_POLICY_DEFAULT)),
      API_CONFIG: validation.Optional(ApiConfigHandler),
      CODE_LOCK: validation.Optional(bool),
      ENV_VARIABLES: validation.Optional(EnvironmentVariables),
      BUILD_ENV_VARIABLES: validation.Optional(EnvironmentVariables),
      STANDARD_WEBSOCKET: validation.Optional(bool),
      APP_ENGINE_APIS: validation.Optional(bool),
      FLEXIBLE_RUNTIME_SETTINGS: validation.Optional(FlexibleRuntimeSettings),
  }

  def CheckInitialized(self):
    """Performs non-regular expression-based validation.

    The following are verified:
        - At least one URL mapping is provided in the URL mappers.
        - The number of URL mappers doesn't exceed `MAX_URL_MAPS`.
        - The major version does not contain the string `-dot-`.
        - If `api_endpoints` are defined, an `api_config` stanza must be
          defined.
        - If the `runtime` is `python27` and `threadsafe` is set, then no CGI
          handlers can be used.
        - The version name doesn't start with `BUILTIN_NAME_PREFIX`.
        - If `redirect_http_response_code` exists, it is in the list of valid
          300s.
        - Module and service aren't both set. Services were formerly known as
          modules.

    Raises:
      DuplicateLibrary: If `library_name` is specified more than once.
      MissingURLMapping: If no `URLMap` object is present in the object.
      TooManyURLMappings: If there are too many `URLMap` entries.
      MissingApiConfig: If `api_endpoints` exists without an `api_config`.
      MissingThreadsafe: If `threadsafe` is not set but the runtime requires it.
      ThreadsafeWithCgiHandler: If the `runtime` is `python27`, `threadsafe` is
          set and CGI handlers are specified.
      TooManyScalingSettingsError: If more than one scaling settings block is
          present.
      RuntimeDoesNotSupportLibraries: If the libraries clause is used for a
          runtime that does not support it, such as `python25`.
    """
    super(AppInfoExternal, self).CheckInitialized()
    if self.runtime is None and not self.IsVm():
      raise appinfo_errors.MissingRuntimeError(
          'You must specify a "runtime" field for non-vm applications.')
    elif self.runtime is None:
      # Default optional to custom (we don't do that in attributes just so
      # we know that it's been defaulted)
      self.runtime = 'custom'
    if self.handlers and len(self.handlers) > MAX_URL_MAPS:
      raise appinfo_errors.TooManyURLMappings(
          'Found more than %d URLMap entries in application configuration' %
          MAX_URL_MAPS)

    vm_runtime_python27 = (
        self.runtime == 'vm' and
        (hasattr(self, 'vm_settings') and
         self.vm_settings and
         self.vm_settings.get('vm_runtime') == 'python27') or
        (hasattr(self, 'beta_settings') and
         self.beta_settings and
         self.beta_settings.get('vm_runtime') == 'python27'))

    if (self.threadsafe is None and
        (self.runtime == 'python27' or vm_runtime_python27)):
      raise appinfo_errors.MissingThreadsafe(
          'threadsafe must be present and set to a true or false YAML value')

    if self.auto_id_policy == DATASTORE_ID_POLICY_LEGACY:
      datastore_auto_ids_url = ('http://developers.google.com/'
                                'appengine/docs/python/datastore/'
                                'entities#Kinds_and_Identifiers')
      appcfg_auto_ids_url = ('http://developers.google.com/appengine/docs/'
                             'python/config/appconfig#auto_id_policy')
      logging.warning(
          "You have set the datastore auto_id_policy to 'legacy'. It is "
          "recommended that you select 'default' instead.\n"
          "Legacy auto ids are deprecated. You can continue to allocate\n"
          "legacy ids manually using the allocate_ids() API functions.\n"
          "For more information see:\n"
          + datastore_auto_ids_url + '\n' + appcfg_auto_ids_url + '\n')

    if (hasattr(self, 'beta_settings') and self.beta_settings
        and self.beta_settings.get('source_reference')):
      ValidateCombinedSourceReferencesString(
          self.beta_settings.get('source_reference'))

    if self.libraries:
      if not (vm_runtime_python27 or self.runtime == 'python27'):
        raise appinfo_errors.RuntimeDoesNotSupportLibraries(
            'libraries entries are only supported by the "python27" runtime')

      library_names = [library.name for library in self.libraries]
      for library_name in library_names:
        if library_names.count(library_name) > 1:
          raise appinfo_errors.DuplicateLibrary(
              'Duplicate library entry for %s' % library_name)

    if self.version and self.version.find(ALTERNATE_HOSTNAME_SEPARATOR) != -1:
      raise validation.ValidationError(
          'Version "%s" cannot contain the string "%s"' % (
              self.version, ALTERNATE_HOSTNAME_SEPARATOR))
    if self.version and self.version.startswith(BUILTIN_NAME_PREFIX):
      raise validation.ValidationError(
          ('Version "%s" cannot start with "%s" because it is a '
           'reserved version name prefix.') % (self.version,
                                               BUILTIN_NAME_PREFIX))
    if self.handlers:
      api_endpoints = [handler.url for handler in self.handlers
                       if handler.GetHandlerType() == HANDLER_API_ENDPOINT]
      if api_endpoints and not self.api_config:
        raise appinfo_errors.MissingApiConfig(
            'An api_endpoint handler was specified, but the required '
            'api_config stanza was not configured.')
      if self.threadsafe and self.runtime == 'python27':
        # VMEngines can handle python25 handlers, so we don't include
        # vm_runtime_python27 in the if statement above.
        for handler in self.handlers:
          if (handler.script and (handler.script.endswith('.py') or
                                  '/' in handler.script)):
            raise appinfo_errors.ThreadsafeWithCgiHandler(
                'threadsafe cannot be enabled with CGI handler: %s' %
                handler.script)
    if sum([bool(self.automatic_scaling),
            bool(self.manual_scaling),
            bool(self.basic_scaling)]) > 1:
      raise appinfo_errors.TooManyScalingSettingsError(
          "There may be only one of 'automatic_scaling', 'manual_scaling', "
          "or 'basic_scaling'.")

  def GetAllLibraries(self):
    """Returns a list of all `Library` instances active for this configuration.

    Returns:
      The list of active `Library` instances for this configuration. This
      includes directly-specified libraries as well as any required
      dependencies.
    """
    if not self.libraries:
      return []

    library_names = set(library.name for library in self.libraries)
    required_libraries = []

    for library in self.libraries:
      for required_name, required_version in REQUIRED_LIBRARIES.get(
          (library.name, library.version), []):
        if required_name not in library_names:
          required_libraries.append(Library(name=required_name,
                                            version=required_version))

    return [Library(**library.ToDict())
            for library in self.libraries + required_libraries]

  def GetNormalizedLibraries(self):
    """Returns a list of normalized `Library` instances for this configuration.

    Returns:
      The list of active `Library` instances for this configuration. This
      includes directly-specified libraries, their required dependencies, and
      any libraries enabled by default. Any libraries with `latest` as their
      version will be replaced with the latest available version.
    """
    libraries = self.GetAllLibraries()
    enabled_libraries = set(library.name for library in libraries)
    for library in _SUPPORTED_LIBRARIES:
      if library.default_version and library.name not in enabled_libraries:
        libraries.append(Library(name=library.name,
                                 version=library.default_version))
    return libraries

  def ApplyBackendSettings(self, backend_name):
    """Applies settings from the indicated backend to the `AppInfoExternal`.

    Backend entries can contain directives that modify other parts of the
    `app.yaml` file, such as the `start` directive, which adds a handler for the
    start request. This method performs those modifications.

    Args:
      backend_name: The name of a backend that is defined in the `backends`
          directive.

    Raises:
      BackendNotFound: If the indicated backend was not listed in the
          `backends` directive.
      DuplicateBackend: If the backend is found more than once in the `backends`
          directive.
    """
    if backend_name is None:
      return

    if self.backends is None:
      raise appinfo_errors.BackendNotFound

    self.version = backend_name

    match = None
    for backend in self.backends:
      if backend.name != backend_name:
        continue
      if match:
        raise appinfo_errors.DuplicateBackend
      else:
        match = backend

    if match is None:
      raise appinfo_errors.BackendNotFound

    if match.start is None:
      return

    start_handler = URLMap(url=_START_PATH, script=match.start)
    self.handlers.insert(0, start_handler)

  def GetEffectiveRuntime(self):
    """Returns the app's runtime, resolving VMs to the underlying `vm_runtime`.

    Returns:
      The effective runtime: The value of `beta/vm_settings.vm_runtime` if
      `runtime` is `vm`, or `runtime` otherwise.
    """
    if (self.runtime == 'vm' and hasattr(self, 'vm_settings')
        and self.vm_settings is not None):
      return self.vm_settings.get('vm_runtime')
    if (self.runtime == 'vm' and hasattr(self, 'beta_settings')
        and self.beta_settings is not None):
      return self.beta_settings.get('vm_runtime')
    return self.runtime

  def SetEffectiveRuntime(self, runtime):
    """Sets the runtime while respecting vm runtimes rules for runtime settings.

    Args:
       runtime: The runtime to use.
    """
    if self.IsVm():
      if not self.vm_settings:
        self.vm_settings = VmSettings()

      # Patch up vm runtime setting. Copy `runtime` to `vm_runtime` and set
      # runtime to the string `vm`.
      self.vm_settings['vm_runtime'] = runtime
      self.runtime = 'vm'
    else:
      self.runtime = runtime

  def NormalizeVmSettings(self):
    """Normalizes VM settings."""
    # NOTE(user): In the input files, `vm` is not a type of runtime, but
    # rather is specified as `vm: true|false`. In the code, `vm` is represented
    # as a value of `AppInfoExternal.runtime`.
    # NOTE(user): This hack is only being applied after the parsing of
    # `AppInfoExternal`. If the `vm` attribute can ever be specified in the
    # `AppInclude`, then this processing will need to be done there too.
    if self.IsVm():
      if not self.vm_settings:
        self.vm_settings = VmSettings()

      if 'vm_runtime' not in self.vm_settings:
        self.SetEffectiveRuntime(self.runtime)

      # Copy fields that are automatically added by the SDK or this class
      # to `beta_settings`.
      if hasattr(self, 'beta_settings') and self.beta_settings:
        # Only copy if `beta_settings` already exists, because we have logic in
        # `appversion.py` to discard all of `vm_settings` if anything is in
        # `beta_settings`. So we won't create an empty one just to add these
        # fields.
        for field in ['vm_runtime',
                      'has_docker_image',
                      'image',
                      'module_yaml_path']:
          if field not in self.beta_settings and field in self.vm_settings:
            self.beta_settings[field] = self.vm_settings[field]

  # TODO(user): `env` replaces `vm`. Remove `vm` when field is removed.
  def IsVm(self):
    return (self.vm or
            self.env in ['2', 'flex', 'flexible'])


def ValidateHandlers(handlers, is_include_file=False):
  """Validates a list of handler (`URLMap`) objects.

  Args:
    handlers: A list of a handler (`URLMap`) objects.
    is_include_file: If this argument is set to `True`, the handlers that are
        added as part of the `includes` directive are validated.
  """
  if not handlers:
    return

  for handler in handlers:
    handler.FixSecureDefaults()
    handler.WarnReservedURLs()
    if not is_include_file:
      handler.ErrorOnPositionForAppInfo()


def LoadSingleAppInfo(app_info):
  """Loads a single `AppInfo` object where one and only one is expected.

  This method validates that the values in the `AppInfo` match the
  validators that are defined in this file, in particular,
  `AppInfoExternal.ATTRIBUTES`.

  Args:
    app_info: A file-like object or string. If the argument is a string, the
        argument is parsed as a configuration file. If the argument is a
        file-like object, the data is read, then parsed.

  Returns:
    An instance of `AppInfoExternal` as loaded from a YAML file.

  Raises:
    ValueError: If a specified service is not valid.
    EmptyConfigurationFile: If there are no documents in YAML file.
    MultipleConfigurationFile: If more than one document exists in the YAML
        file.
    DuplicateBackend: If a backend is found more than once in the `backends`
        directive.
    yaml_errors.EventError: If the `app.yaml` file fails validation.
    appinfo_errors.MultipleProjectNames: If the `app.yaml` file has both an
        `application` directive and a `project` directive.
  """
  builder = yaml_object.ObjectBuilder(AppInfoExternal)
  handler = yaml_builder.BuilderHandler(builder)
  listener = yaml_listener.EventListener(handler)
  listener.Parse(app_info)

  app_infos = handler.GetResults()
  if len(app_infos) < 1:
    raise appinfo_errors.EmptyConfigurationFile()
  if len(app_infos) > 1:
    raise appinfo_errors.MultipleConfigurationFile()

  appyaml = app_infos[0]
  ValidateHandlers(appyaml.handlers)
  if appyaml.builtins:
    BuiltinHandler.Validate(appyaml.builtins, appyaml.runtime)

  # Allow `project: name` as an alias for `application: name`. If found, we
  # change the `project` field to `None`. (Deleting it would make a distinction
  # between loaded and constructed `AppInfoExternal` objects, since the latter
  # would still have the project field.)
  if appyaml.application and appyaml.project:
    raise appinfo_errors.MultipleProjectNames(
        'Specify one of "application: name" or "project: name"')
  elif appyaml.project:
    appyaml.application = appyaml.project
    appyaml.project = None

  appyaml.NormalizeVmSettings()
  return appyaml


class AppInfoSummary(validation.Validated):
  """This class contains only basic summary information about an app.

  This class is used to pass back information about the newly created app to
  users after a new version has been created.
  """
  # NOTE(user): Before you consider adding anything to this YAML definition,
  # you must solve the issue that old SDK versions will try to parse this new
  # value with the old definition and fail.  Basically we are stuck with this
  # definition for the time being.  The parsing of the value is done in
  ATTRIBUTES = {
      APPLICATION: APPLICATION_RE_STRING,
      MAJOR_VERSION: MODULE_VERSION_ID_RE_STRING,
      MINOR_VERSION: validation.TYPE_LONG
  }


def LoadAppInclude(app_include):
  """Loads a single `AppInclude` object where one and only one is expected.

  Args:
    app_include: A file-like object or string. The argument is set to a string,
        the argument is parsed as a configuration file. If the argument is set
        to a file-like object, the data is read and parsed.

  Returns:
    An instance of `AppInclude` as loaded from a YAML file.

  Raises:
    EmptyConfigurationFile: If there are no documents in the YAML file.
    MultipleConfigurationFile: If there is more than one document in the YAML
        file.
  """
  builder = yaml_object.ObjectBuilder(AppInclude)
  handler = yaml_builder.BuilderHandler(builder)
  listener = yaml_listener.EventListener(handler)
  listener.Parse(app_include)

  includes = handler.GetResults()
  if len(includes) < 1:
    raise appinfo_errors.EmptyConfigurationFile()
  if len(includes) > 1:
    raise appinfo_errors.MultipleConfigurationFile()

  includeyaml = includes[0]
  if includeyaml.handlers:
    for handler in includeyaml.handlers:
      handler.FixSecureDefaults()
      handler.WarnReservedURLs()
  if includeyaml.builtins:
    BuiltinHandler.Validate(includeyaml.builtins)

  return includeyaml


def ParseExpiration(expiration):
  """Parses an expiration delta string.

  Args:
    expiration: String that matches `_DELTA_REGEX`.

  Returns:
    Time delta in seconds.
  """
  delta = 0
  for match in re.finditer(_DELTA_REGEX, expiration):
    amount = int(match.group(1))
    units = _EXPIRATION_CONVERSIONS.get(match.group(2).lower(), 1)
    delta += amount * units
  return delta


#####################################################################
# These regexps must be the same as those in:
#   - apphosting/api/app_config/request_validator.cc
#   - java/com/google/appengine/tools/admin/AppVersionUpload.java
#   - java/com/google/apphosting/admin/legacy/LegacyAppInfo.java

# Forbid `.`, `..`, and leading `-`, `_ah/` or `/`
_file_path_negative_1_re = re.compile(r'\.\.|^\./|\.$|/\./|^-|^_ah/|^/')

# Forbid `//` and trailing `/`
_file_path_negative_2_re = re.compile(r'//|/$')

# Forbid any use of space other than in the middle of a directory
# or file name. Forbid line feeds and carriage returns.
_file_path_negative_3_re = re.compile(r'^ | $|/ | /|\r|\n')


# (erinjerison) Lint seems to think I'm specifying the word "character" as an
# argument. This isn't the case; it's part of a list to enable the list to
# build properly. Disabling it for now.
# pylint: disable=g-doc-args
def ValidFilename(filename):
  """Determines if a file name is valid.

  Args:
    filename: The file name to validate. The file name must be a valid file
        name:
            - It must only contain letters, numbers, and the following special
              characters:  `@`, `_`, `+`, `/` `$`, `.`, `-`, or '~'.
            - It must be less than 256 characters.
            - It must not contain `/./`, `/../`, or `//`.
            - It must not end in `/`.
            - All spaces must be in the middle of a directory or file name.

  Returns:
    An error string if the file name is invalid. `''` is returned if the file
    name is valid.
  """
  if not filename:
    return 'Filename cannot be empty'
  if len(filename) > 1024:
    return 'Filename cannot exceed 1024 characters: %s' % filename
  if _file_path_negative_1_re.search(filename) is not None:
    return ('Filename cannot contain "." or ".." '
            'or start with "-" or "_ah/": %s' %
            filename)
  if _file_path_negative_2_re.search(filename) is not None:
    return 'Filename cannot have trailing / or contain //: %s' % filename
  if _file_path_negative_3_re.search(filename) is not None:
    return 'Any spaces must be in the middle of a filename: %s' % filename
  return ''
