# -*- coding: utf-8 -*-
# Copyright 2018 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Shared utility structures and methods that require importing boto.

This module also imports httplib2 (as it is Boto's http transport and closely
tied to some of Boto's core functionality) and oauth2client.
"""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals

import os
import pkgutil
import tempfile
import textwrap

import six
import boto
from boto import config
import boto.auth
from boto.exception import NoAuthHandlerFound
from boto.gs.connection import GSConnection
from boto.provider import Provider
from boto.pyami.config import BotoConfigLocations

import gslib
from gslib import context_config
from gslib.exception import CommandException
from gslib.utils import system_util
from gslib.utils.constants import DEFAULT_GCS_JSON_API_VERSION
from gslib.utils.constants import DEFAULT_GSUTIL_STATE_DIR
from gslib.utils.constants import SSL_TIMEOUT_SEC
from gslib.utils.constants import UTF8
from gslib.utils.unit_util import HumanReadableToBytes
from gslib.utils.unit_util import ONE_MIB

import httplib2
from oauth2client.client import HAS_CRYPTO

if six.PY3:
  long = int

# Globals in this module are set according to values in the boto config.
BOTO_IS_SECURE = config.get('Boto', 'is_secure', True)
CERTIFICATE_VALIDATION_ENABLED = config.get('Boto',
                                            'https_validate_certificates', True)

configured_certs_file = None  # Single certs file for use across all processes.
temp_certs_file = None  # Temporary certs file for cleanup upon exit.


def ConfigureCertsFile():
  """Configures and returns the CA Certificates file.

  If one is already configured, use it. Otherwise, use the cert roots
  distributed with gsutil.

  Returns:
    string filename of the certs file to use.
  """
  certs_file = boto.config.get('Boto', 'ca_certificates_file', None)
  # The 'system' keyword indicates to use the system installed certs. Some
  # Linux distributions patch the stack such that the Python SSL
  # infrastructure picks up the system installed certs by default, thus no
  #  action necessary on our part
  if certs_file == 'system':
    return None
  if not certs_file:
    global configured_certs_file, temp_certs_file
    if not configured_certs_file:
      configured_certs_file = os.path.abspath(
          os.path.join(gslib.GSLIB_DIR, 'data', 'cacerts.txt'))
      if not os.path.exists(configured_certs_file):
        # If the file is not present on disk, this means the gslib module
        # doesn't actually exist on disk anywhere. This can happen if it's
        # being imported from a zip file. Unfortunately, we have to copy the
        # certs file to a local temp file on disk because the underlying SSL
        # socket requires it to be a filesystem path.
        certs_data = pkgutil.get_data('gslib', 'data/cacerts.txt')
        if not certs_data:
          raise CommandException('Certificates file not found. Please '
                                 'reinstall gsutil from scratch')
        certs_data = six.ensure_str(certs_data)
        fd, fname = tempfile.mkstemp(suffix='.txt', prefix='gsutil-cacerts')
        f = os.fdopen(fd, 'w')
        f.write(certs_data)
        f.close()
        temp_certs_file = fname
        configured_certs_file = temp_certs_file
    certs_file = configured_certs_file
  return certs_file


def ConfigureNoOpAuthIfNeeded():
  """Sets up no-op auth handler if no boto credentials are configured."""
  if not HasConfiguredCredentials():
    if (config.has_option('Credentials', 'gs_service_client_id') and
        not HAS_CRYPTO):
      if system_util.InvokedViaCloudSdk():
        raise CommandException('\n'.join(
            textwrap.wrap(
                'Your gsutil is configured with an OAuth2 service account, but '
                'you do not have PyOpenSSL or PyCrypto 2.6 or later installed. '
                'Service account authentication requires one of these libraries; '
                'please reactivate your service account via the gcloud auth '
                'command and ensure any gcloud packages necessary for '
                'service accounts are present.')))
      else:
        raise CommandException('\n'.join(
            textwrap.wrap(
                'Your gsutil is configured with an OAuth2 service account, but '
                'you do not have PyOpenSSL or PyCrypto 2.6 or later installed. '
                'Service account authentication requires one of these libraries; '
                'please install either of them to proceed, or configure a '
                'different type of credentials with "gsutil config".')))
    else:
      # With no boto config file the user can still access publicly readable
      # buckets and objects.
      from gslib import no_op_auth_plugin  # pylint: disable=unused-variable


def GetCertsFile():
  return configured_certs_file


def GetCleanupFiles():
  """Returns a list of temp files to delete (if possible) when program exits."""
  return [temp_certs_file] if temp_certs_file else []


def GetConfigFilePaths():
  """Returns a list of the path(s) to the boto config file(s) to be loaded."""
  potential_config_paths = BotoConfigLocations

  # When Boto's pyami.config.Config class is initialized, it attempts to read
  # this file, transform it into valid Boto config syntax, and load credentials
  # from it, but it does not add this file to BotoConfigLocations.
  if 'AWS_CREDENTIAL_FILE' in os.environ:
    potential_config_paths.append(os.environ['AWS_CREDENTIAL_FILE'])
  # Provider-specific config files, like the one below, are checked for and
  # loaded when Boto's Provider class is initialized. These aren't listed in
  # BotoConfigLocations, but can still affect what credentials are loaded, so
  # we display them in our config list to make auth'n debugging easier.
  aws_cred_file = os.path.join(os.path.expanduser('~'), '.aws', 'credentials')
  if os.path.isfile(aws_cred_file):
    potential_config_paths.append(aws_cred_file)

  # Only return credential files which we have permission to read (and thus can
  # actually load credentials from).
  readable_config_paths = []
  for path in potential_config_paths:
    try:
      with open(path, 'r'):
        readable_config_paths.append(path)
    except IOError:
      pass
  return readable_config_paths


def GetFriendlyConfigFilePaths():
  """Like GetConfigFilePaths but returns a not-found message if paths empty."""
  readable_config_paths = GetConfigFilePaths()
  if len(readable_config_paths) == 0:
    readable_config_paths.append('No config found')
  return readable_config_paths


def GetGsutilStateDir():
  """Returns the location of the directory for gsutil state files.

  Certain operations, such as cross-process credential sharing and
  resumable transfer tracking, need a known location for state files which
  are created by gsutil as-needed.

  This location should only be used for storing data that is required to be in
  a static location.

  Returns:
    Path to directory for gsutil static state files.
  """
  config_file_dir = config.get('GSUtil', 'state_dir', DEFAULT_GSUTIL_STATE_DIR)
  system_util.CreateDirIfNeeded(config_file_dir)
  return config_file_dir


def GetCredentialStoreFilename():
  # As of gsutil 4.29, this changed from 'credstore' to 'credstore2' because
  # of a change to the underlying credential storage format.
  return os.path.join(GetGsutilStateDir(), 'credstore2')


def GetGceCredentialCacheFilename():
  return os.path.join(GetGsutilStateDir(), 'gcecredcache')


def GetGcsJsonApiVersion():
  return config.get('GSUtil', 'json_api_version', DEFAULT_GCS_JSON_API_VERSION)


# Resumable downloads and uploads make one HTTP call per chunk (and must be
# in multiples of 256KiB). Overridable for testing.
def GetJsonResumableChunkSize():
  chunk_size = config.getint('GSUtil', 'json_resumable_chunk_size',
                             long(1024 * 1024 * 100))
  if chunk_size == 0:
    chunk_size = long(1024 * 256)
  elif chunk_size % long(1024 * 256) != 0:
    chunk_size += (long(1024 * 256) - (chunk_size % (long(1024 * 256))))
  return chunk_size


def GetLastCheckedForGsutilUpdateTimestampFile():
  return os.path.join(GetGsutilStateDir(), '.last_software_update_check')


def GetMaxConcurrentCompressedUploads():
  """Gets the max concurrent transport compressed uploads allowed in parallel.

  Returns:
    The max number of concurrent transport compressed uploads allowed in
    parallel without exceeding the max_upload_compression_buffer_size.
  """
  upload_chunk_size = GetJsonResumableChunkSize()
  # From apitools compression.py.
  compression_chunk_size = 16 * ONE_MIB
  total_upload_size = (upload_chunk_size + compression_chunk_size + 17 + 5 *
                       (((compression_chunk_size - 1) / 16383) + 1))
  max_concurrent_uploads = (GetMaxUploadCompressionBufferSize() /
                            total_upload_size)
  if max_concurrent_uploads <= 0:
    max_concurrent_uploads = 1
  return max_concurrent_uploads


def GetMaxRetryDelay():
  return config.getint('Boto', 'max_retry_delay', 32)


def GetMaxUploadCompressionBufferSize():
  """Get the max amount of memory compressed transport uploads may buffer."""
  return HumanReadableToBytes(
      config.get('GSUtil', 'max_upload_compression_buffer_size', '2GiB'))


def GetNewHttp(http_class=httplib2.Http, **kwargs):
  """Creates and returns a new httplib2.Http instance.

  Args:
    http_class: Optional custom Http class to use.
    **kwargs: Arguments to pass to http_class constructor.

  Returns:
    An initialized httplib2.Http instance.
  """

  ##Get Proxy configuration from boto file, defaults are None, 0 and False
  proxy_host = config.get('Boto', 'proxy', None)  #needed for if clause below
  boto_proxy_config = {
      'proxy_host':
          proxy_host,
      'proxy_type':
          config.get('Boto', 'proxy_type', 'http'),
      'proxy_port':
          config.getint('Boto', 'proxy_port'),
      'proxy_user':
          config.get('Boto', 'proxy_user', None),
      'proxy_pass':
          config.get('Boto', 'proxy_pass', None),
      'proxy_rdns':
          config.get('Boto', 'proxy_rdns', True if proxy_host else None)
  }

  #Use SetProxyInfo to convert boto config to httplib2.proxyinfo object
  proxy_info = SetProxyInfo(boto_proxy_config)

  # Some installers don't package a certs file with httplib2, so use the
  # one included with gsutil.
  kwargs['ca_certs'] = GetCertsFile()
  # Use a non-infinite SSL timeout to avoid hangs during network flakiness.
  kwargs['timeout'] = SSL_TIMEOUT_SEC
  http = http_class(proxy_info=proxy_info, **kwargs)
  http.disable_ssl_certificate_validation = (not config.getbool(
      'Boto', 'https_validate_certificates'))

  global_context_config = context_config.get_context_config()
  if global_context_config and global_context_config.use_client_certificate:
    http.add_certificate(key=global_context_config.client_cert_path,
                         cert=global_context_config.client_cert_path,
                         domain='',
                         password=global_context_config.client_cert_password)

  return http


# Retry for 10 minutes with exponential backoff, which corresponds to
# the maximum Downtime Period specified in the GCS SLA
# (https://cloud.google.com/storage/sla)
def GetNumRetries():
  return config.getint('Boto', 'num_retries', 23)


def GetTabCompletionLogFilename():
  return os.path.join(GetGsutilStateDir(), 'tab-completion-logs')


def GetTabCompletionCacheFilename():
  tab_completion_dir = os.path.join(GetGsutilStateDir(), 'tab-completion')
  # Limit read permissions on the directory to owner for privacy.
  system_util.CreateDirIfNeeded(tab_completion_dir, mode=0o700)
  return os.path.join(tab_completion_dir, 'cache')


def HasConfiguredCredentials():
  """Determines if boto credential/config file exists."""
  has_goog_creds = (config.has_option('Credentials', 'gs_access_key_id') and
                    config.has_option('Credentials', 'gs_secret_access_key'))
  has_amzn_creds = (config.has_option('Credentials', 'aws_access_key_id') and
                    config.has_option('Credentials', 'aws_secret_access_key'))
  has_oauth_creds = (config.has_option('Credentials',
                                       'gs_oauth2_refresh_token'))
  has_external_creds = (config.has_option('Credentials',
                                          'gs_external_account_file'))
  has_external_account_authorized_user_creds = (config.has_option(
      'Credentials', 'gs_external_account_authorized_user_file'))
  has_service_account_creds = (
      HAS_CRYPTO and
      config.has_option('Credentials', 'gs_service_client_id') and
      config.has_option('Credentials', 'gs_service_key_file'))

  if (has_goog_creds or has_amzn_creds or has_oauth_creds or
      has_service_account_creds or has_external_creds or
      has_external_account_authorized_user_creds):
    return True

  valid_auth_handler = None
  try:
    valid_auth_handler = boto.auth.get_auth_handler(GSConnection.DefaultHost,
                                                    config,
                                                    Provider('google'),
                                                    requested_capability=['s3'])
    # Exclude the no-op auth handler as indicating credentials are configured.
    # Note we can't use isinstance() here because the no-op module may not be
    # imported so we can't get a reference to the class type.
    if 'NoOpAuth' == getattr(
        getattr(valid_auth_handler, '__class__', None),
        '__name__',
        None):  # yapf: disable
      valid_auth_handler = None
  except NoAuthHandlerFound:
    pass

  return valid_auth_handler


def JsonResumableChunkSizeDefined():
  chunk_size_defined = config.get('GSUtil', 'json_resumable_chunk_size', None)
  return chunk_size_defined is not None


def MonkeyPatchBoto():
  """Apply gsutil-specific patches to Boto.

  Here be dragons. Sorry.

  Note that this method should not be used as a replacement for contributing
  fixes to the upstream Boto library. However, the Boto library has historically
  not been consistent about release cadence, so upstream fixes may not be
  available immediately in a version which we can pin to. Also, some fixes may
  only be applicable to gsutil. In such cases, patches should be applied to the
  Boto library here (and removed if/when they are included in the upstream
  repository and included in an official new release that we pull in). This
  method should be invoked after all other Boto-related initialization has been
  completed.
  """
  # We have to do all sorts of gross things here (dynamic imports, invalid names
  # to resolve symbols in copy/pasted methods, invalid spacing from copy/pasted
  # methods, etc.), so we just disable pylint warnings for this whole method.
  # yapf: disable
  # pylint: disable=all

  # This should have already been imported if this method was called in the
  # correct place, but we need to perform the import within this method for
  # this module to recognize it.  We don't import this at module level because
  # its import timing is important and is managed elsewhere.
  import gcs_oauth2_boto_plugin

  # TODO(https://github.com/boto/boto/issues/3831): Remove this if the GitHub
  # issue is ever addressed.
  orig_get_plugin_method = boto.plugin.get_plugin

  def _PatchedGetPluginMethod(cls, requested_capability=None):
    handler_subclasses = orig_get_plugin_method(
        cls, requested_capability=requested_capability)
    # In Boto's logic, higher precedence handlers should be closer to the end
    # of the list.  We always want to prefer OAuth2 credentials over HMAC
    # credentials if both are present, so we shuffle OAuth2 handlers to the end
    # of the handler list.
    xml_oauth2_handlers = (
        gcs_oauth2_boto_plugin.oauth2_plugin.OAuth2ServiceAccountAuth,
        gcs_oauth2_boto_plugin.oauth2_plugin.OAuth2Auth)
    new_result = (
        # We need to sort each of these to avoid inconsistent handler selection
        # when multiple credential types are configured in Python 3.5. See
        # https://issuetracker.google.com/issues/135709541 for specific logs.
        sorted(
            [r for r in handler_subclasses if r not in xml_oauth2_handlers],
            # Types aren't sortable, so we use their names:
            key=(lambda handler_t: handler_t.__name__),
        ) +  # Now append XML handlers to the end (highest precedence)
        sorted(
            [r for r in handler_subclasses if r in xml_oauth2_handlers],
            key=(lambda handler_t: handler_t.__name__),
        ))
    return new_result

  boto.plugin.get_plugin = _PatchedGetPluginMethod

  #########################################################################

  # TODO(boto>2.49.0): Remove this.
  # Fixes SSL issue where SNI was not being used for OpenSSL 1.1.1+
  # https://github.com/boto/boto/pull/3843/files

  # Import modules and resolve symbols used by our patch method.
  import socket
  import ssl
  InvalidCertificateException = (
      boto.https_connection.InvalidCertificateException)
  ValidateCertificateHostname = (
      boto.https_connection.ValidateCertificateHostname)

  def _PatchedConnectMethod(self):
    # The lines below were copied directly from the Boto file, so we don't lint
    # or otherwise alter them.
    if hasattr(self, "timeout"):
      sock = socket.create_connection((self.host, self.port), self.timeout)
    else:
      sock = socket.create_connection((self.host, self.port))
    msg = "wrapping ssl socket; "
    if self.ca_certs:
      msg += "CA certificate file=%s" % self.ca_certs
    else:
      msg += "using system provided SSL certs"
    boto.log.debug(msg)
    if hasattr(ssl, 'SSLContext') and getattr(ssl, 'HAS_SNI', False):
      # Use SSLContext so we can specify server_hostname for SNI
      # (Required for connections to storage.googleapis.com)
      context = ssl.SSLContext(ssl.PROTOCOL_SSLv23)
      context.verify_mode = ssl.CERT_REQUIRED
      if self.ca_certs:
        context.load_verify_locations(self.ca_certs)
      if self.cert_file:
        context.load_cert_chain(self.cert_file, self.key_file)
      self.sock = context.wrap_socket(sock, server_hostname=self.host)
      # Add attributes only set in SSLSocket constructor without context:
      self.sock.keyfile = self.key_file
      self.sock.certfile = self.cert_file
      self.sock.cert_reqs = context.verify_mode
      self.sock.ssl_version = ssl.PROTOCOL_SSLv23
      self.sock.ca_certs = self.ca_certs
      self.sock.ciphers = None
    else:
      self.sock = ssl.wrap_socket(sock,
                                  keyfile=self.key_file,
                                  certfile=self.cert_file,
                                  cert_reqs=ssl.CERT_REQUIRED,
                                  ca_certs=self.ca_certs)
    cert = self.sock.getpeercert()
    hostname = self.host.split(':', 0)[0]
    if not ValidateCertificateHostname(cert, hostname):
      raise InvalidCertificateException(
          hostname, cert, 'remote hostname "%s" does not match '
          'certificate' % hostname)
    # End `_PatchedConnectMethod` declaration.

  boto.https_connection.CertValidatingHTTPSConnection.connect = (
      _PatchedConnectMethod)


def ProxyInfoFromEnvironmentVar(proxy_env_var):
  """Reads proxy info from the environment and converts to httplib2.ProxyInfo.

  Args:
    proxy_env_var: Environment variable string to read, such as http_proxy or
       https_proxy.

  Returns:
    httplib2.ProxyInfo constructed from the environment string.
  """
  proxy_url = os.environ.get(proxy_env_var)
  if not proxy_url or not proxy_env_var.lower().startswith('http'):
    return httplib2.ProxyInfo(httplib2.socks.PROXY_TYPE_HTTP, None, 0)
  proxy_protocol = proxy_env_var.lower().split('_')[0]
  if not proxy_url.lower().startswith('http'):
    # proxy_info_from_url requires a protocol, which is always http or https.
    proxy_url = proxy_protocol + '://' + proxy_url
  return httplib2.proxy_info_from_url(proxy_url, method=proxy_protocol)


def ResumableThreshold():
  return config.getint('GSUtil', 'resumable_threshold', 8 * ONE_MIB)


def SetProxyInfo(boto_proxy_config):
  """Sets proxy info from boto and environment and converts to httplib2.ProxyInfo.

  Args:
    dict: Values read from the .boto file

  Returns:
    httplib2.ProxyInfo constructed from boto or environment variable string.
  """
  #Defining proxy_type based on httplib2 library, accounting for None entry too.
  proxy_type_spec = {'socks4': 1, 'socks5': 2, 'http': 3, 'https': 3}

  #proxy_type defaults to 'http (3)' for backwards compatibility
  proxy_type = proxy_type_spec.get(
      boto_proxy_config.get('proxy_type').lower(), proxy_type_spec['http'])
  proxy_host = boto_proxy_config.get('proxy_host')
  proxy_port = boto_proxy_config.get('proxy_port')
  proxy_user = boto_proxy_config.get('proxy_user')
  proxy_pass = boto_proxy_config.get('proxy_pass')
  proxy_rdns = bool(boto_proxy_config.get('proxy_rdns'))

  #For proxy_info below, proxy_rdns fails for socks4 and socks5 so restricting use
  #to http only
  proxy_info = httplib2.ProxyInfo(proxy_host=proxy_host,
                                  proxy_type=proxy_type,
                                  proxy_port=proxy_port,
                                  proxy_user=proxy_user,
                                  proxy_pass=proxy_pass,
                                  proxy_rdns=proxy_rdns)

  #Added to force socks proxies not to use rdns
  if not (proxy_info.proxy_type == proxy_type_spec['http']):
    proxy_info.proxy_rdns = False

  if not (proxy_info.proxy_host and proxy_info.proxy_port):
    # Fall back to using the environment variable. Use only http proxies.
    for proxy_env_var in ['http_proxy', 'https_proxy', 'HTTPS_PROXY']:
      if proxy_env_var in os.environ and os.environ[proxy_env_var]:
        proxy_info = ProxyInfoFromEnvironmentVar(proxy_env_var)
        # Assume proxy_rnds is True if a proxy environment variable exists.
        if boto_proxy_config.get('proxy_rdns') == None:
          proxy_info.proxy_rdns = True
        break

  return proxy_info


def UsingCrcmodExtension():
  boto_opt = boto.config.get('GSUtil', 'test_assume_fast_crcmod', None)
  if boto_opt is not None:
    return boto_opt
  # Python 3 makes this attribute tough to access due to the way the top-level
  # crcmod package imports and (identically) names its crcmod module. The only
  # way to get it is "from crcmod.crcmod import _usingExtension". This is the
  # alternative form of that statement, but doesn't pollute this module's
  # namespace with a "_usingExtension" attribute. This also works in both Python
  # 2.7 and 3.5+.
  nested_crcmod = __import__(
      'crcmod.crcmod',
      globals(),
      locals(),
      ['_usingExtension'],
      0,
  )
  return getattr(nested_crcmod, '_usingExtension', False)


# TODO(boto-2.49.0): Remove when we pull in the next version of Boto.
def _PatchedShouldRetryMethod(self, response, chunked_transfer=False):
  """Replaces boto.s3.key's should_retry() to handle KMS-encrypted objects."""
  # We copy/pasted this from boto and slightly modified it; keep the old
  # formatting style.
  # yapf: disable
  provider = self.bucket.connection.provider

  if not chunked_transfer:
    if response.status in [500, 503]:
      # 500 & 503 can be plain retries.
      return True

    if response.getheader('location'):
      # If there's a redirect, plain retry.
      return True

  if 200 <= response.status <= 299:
    self.etag = response.getheader('etag')
    md5 = self.md5
    if isinstance(md5, bytes):
      md5 = md5.decode(UTF8)

    # If you use customer-provided encryption keys, the ETag value that
    # Amazon S3 returns in the response will not be the MD5 of the
    # object.
    amz_server_side_encryption_customer_algorithm = response.getheader(
        'x-amz-server-side-encryption-customer-algorithm', None)
    # The same is applicable for KMS-encrypted objects in gs buckets.
    goog_customer_managed_encryption = response.getheader(
        'x-goog-encryption-kms-key-name', None)
    if (amz_server_side_encryption_customer_algorithm is None and
            goog_customer_managed_encryption is None):
      if self.etag != '"%s"' % md5:
        raise provider.storage_data_error(
            'ETag from S3 did not match computed MD5. '
            '%s vs. %s' % (self.etag, self.md5))

    return True

  if response.status == 400:
    # The 400 must be trapped so the retry handler can check to
    # see if it was a timeout.
    # If ``RequestTimeout`` is present, we'll retry. Otherwise, bomb
    # out.
    body = response.read()
    err = provider.storage_response_error(
        response.status,
        response.reason,
        body
    )

    if err.error_code in ['RequestTimeout']:
      raise boto.exception.PleaseRetryException(
          "Saw %s, retrying" % err.error_code,
          response=response
      )

  return False

def HasUserSpecifiedGsHost():
  gs_host = boto.config.get('Credentials', 'gs_host', None)
  default_host = six.ensure_str(boto.gs.connection.GSConnection.DefaultHost)

  if gs_host is not None:
    return default_host == six.ensure_str(gs_host)

  return False

def UsingGsHmac():
  # NOTE: External credentials are omitted intentionally as HMAC takes priority
  # over the external credentials types.
  config = boto.config
  has_refresh_token = config.has_option('Credentials', 'gs_oauth2_refresh_token')
  has_service_account_credentials = (
    config.has_option('Credentials', 'gs_service_client_id')
    and config.has_option('Credentials', 'gs_service_key_file'))
  has_hmac_credentials = (
    config.has_option('Credentials', 'gs_access_key_id')
    and config.has_option('Credentials', 'gs_secret_access_key'))
  return (not has_refresh_token and not has_service_account_credentials
    and has_hmac_credentials)
