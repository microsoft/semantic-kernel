# -*- coding: utf-8 -*-
# Copyright 2013 Google Inc. All Rights Reserved.
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish, dis-
# tribute, sublicense, and/or sell copies of the Software, and to permit
# persons to whom the Software is furnished to do so, subject to the fol-
# lowing conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
# OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABIL-
# ITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT
# SHALL THE AUTHOR BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
# IN THE SOFTWARE.
"""Tests for gsutil utility functions."""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals

from gslib.utils import boto_util
from gslib.utils import constants
from gslib.utils import system_util
from gslib.utils import ls_helper
from gslib.utils import retry_util
from gslib.utils import text_util
from gslib.utils import unit_util
import gslib.tests.testcase as testcase
from gslib.tests.util import SetEnvironmentForTest
from gslib.tests.util import TestParams
from gslib.utils.text_util import CompareVersions
from gslib.utils.unit_util import DecimalShort
from gslib.utils.unit_util import HumanReadableWithDecimalPlaces
from gslib.utils.unit_util import PrettyTime
import httplib2

import os
import six
from six import add_move, MovedModule

add_move(MovedModule('mock', 'mock', 'unittest.mock'))
from six.moves import mock


# TODO: Split tests for <foo>_util methods out into their own test classes.
class TestUtil(testcase.GsUtilUnitTestCase):
  """Tests for utility functions."""

  def testMakeHumanReadable(self):
    """Tests converting byte counts to human-readable strings."""
    self.assertEqual(unit_util.MakeHumanReadable(0), '0 B')
    self.assertEqual(unit_util.MakeHumanReadable(1023), '1023 B')
    self.assertEqual(unit_util.MakeHumanReadable(1024), '1 KiB')
    self.assertEqual(unit_util.MakeHumanReadable(1024**2), '1 MiB')
    self.assertEqual(unit_util.MakeHumanReadable(1024**3), '1 GiB')
    self.assertEqual(unit_util.MakeHumanReadable(1024**3 * 5.3), '5.3 GiB')
    self.assertEqual(unit_util.MakeHumanReadable(1024**4 * 2.7), '2.7 TiB')
    self.assertEqual(unit_util.MakeHumanReadable(1024**5), '1 PiB')
    self.assertEqual(unit_util.MakeHumanReadable(1024**6), '1 EiB')

  def testMakeBitsHumanReadable(self):
    """Tests converting bit counts to human-readable strings."""
    self.assertEqual(unit_util.MakeBitsHumanReadable(0), '0 bit')
    self.assertEqual(unit_util.MakeBitsHumanReadable(1023), '1023 bit')
    self.assertEqual(unit_util.MakeBitsHumanReadable(1024), '1 Kibit')
    self.assertEqual(unit_util.MakeBitsHumanReadable(1024**2), '1 Mibit')
    self.assertEqual(unit_util.MakeBitsHumanReadable(1024**3), '1 Gibit')
    self.assertEqual(unit_util.MakeBitsHumanReadable(1024**3 * 5.3),
                     '5.3 Gibit')
    self.assertEqual(unit_util.MakeBitsHumanReadable(1024**4 * 2.7),
                     '2.7 Tibit')
    self.assertEqual(unit_util.MakeBitsHumanReadable(1024**5), '1 Pibit')
    self.assertEqual(unit_util.MakeBitsHumanReadable(1024**6), '1 Eibit')

  def testHumanReadableToBytes(self):
    """Tests converting human-readable strings to byte counts."""
    self.assertEqual(unit_util.HumanReadableToBytes('1'), 1)
    self.assertEqual(unit_util.HumanReadableToBytes('15'), 15)
    self.assertEqual(unit_util.HumanReadableToBytes('15.3'), 15)
    self.assertEqual(unit_util.HumanReadableToBytes('15.7'), 16)
    self.assertEqual(unit_util.HumanReadableToBytes('1023'), 1023)
    self.assertEqual(unit_util.HumanReadableToBytes('1k'), 1024)
    self.assertEqual(unit_util.HumanReadableToBytes('2048'), 2048)
    self.assertEqual(unit_util.HumanReadableToBytes('1 k'), 1024)
    self.assertEqual(unit_util.HumanReadableToBytes('1 K'), 1024)
    self.assertEqual(unit_util.HumanReadableToBytes('1 KB'), 1024)
    self.assertEqual(unit_util.HumanReadableToBytes('1 KiB'), 1024)
    self.assertEqual(unit_util.HumanReadableToBytes('1 m'), 1024**2)
    self.assertEqual(unit_util.HumanReadableToBytes('1 M'), 1024**2)
    self.assertEqual(unit_util.HumanReadableToBytes('1 MB'), 1024**2)
    self.assertEqual(unit_util.HumanReadableToBytes('1 MiB'), 1024**2)
    self.assertEqual(unit_util.HumanReadableToBytes('1 g'), 1024**3)
    self.assertEqual(unit_util.HumanReadableToBytes('1 G'), 1024**3)
    self.assertEqual(unit_util.HumanReadableToBytes('1 GB'), 1024**3)
    self.assertEqual(unit_util.HumanReadableToBytes('1 GiB'), 1024**3)
    self.assertEqual(unit_util.HumanReadableToBytes('1t'), 1024**4)
    self.assertEqual(unit_util.HumanReadableToBytes('1T'), 1024**4)
    self.assertEqual(unit_util.HumanReadableToBytes('1TB'), 1024**4)
    self.assertEqual(unit_util.HumanReadableToBytes('1TiB'), 1024**4)
    self.assertEqual(unit_util.HumanReadableToBytes('1\t   p'), 1024**5)
    self.assertEqual(unit_util.HumanReadableToBytes('1\t   P'), 1024**5)
    self.assertEqual(unit_util.HumanReadableToBytes('1\t   PB'), 1024**5)
    self.assertEqual(unit_util.HumanReadableToBytes('1\t   PiB'), 1024**5)
    self.assertEqual(unit_util.HumanReadableToBytes('1e'), 1024**6)
    self.assertEqual(unit_util.HumanReadableToBytes('1E'), 1024**6)
    self.assertEqual(unit_util.HumanReadableToBytes('1EB'), 1024**6)
    self.assertEqual(unit_util.HumanReadableToBytes('1EiB'), 1024**6)

  def testCompareVersions(self):
    """Tests CompareVersions for various use cases."""
    # CompareVersions(first, second) returns (g, m), where
    #   g is True if first known to be greater than second, else False.
    #   m is True if first known to be greater by at least 1 major version,
    (g, m) = CompareVersions('3.37', '3.2')
    self.assertTrue(g)
    self.assertFalse(m)
    (g, m) = CompareVersions('7', '2')
    self.assertTrue(g)
    self.assertTrue(m)
    (g, m) = CompareVersions('3.32', '3.32pre')
    self.assertTrue(g)
    self.assertFalse(m)
    (g, m) = CompareVersions('3.32pre', '3.31')
    self.assertTrue(g)
    self.assertFalse(m)
    (g, m) = CompareVersions('3.4pre', '3.3pree')
    self.assertTrue(g)
    self.assertFalse(m)

    (g, m) = CompareVersions('3.2', '3.37')
    self.assertFalse(g)
    self.assertFalse(m)
    (g, m) = CompareVersions('2', '7')
    self.assertFalse(g)
    self.assertFalse(m)
    (g, m) = CompareVersions('3.32pre', '3.32')
    self.assertFalse(g)
    self.assertFalse(m)
    (g, m) = CompareVersions('3.31', '3.32pre')
    self.assertFalse(g)
    self.assertFalse(m)
    (g, m) = CompareVersions('3.3pre', '3.3pre')
    self.assertFalse(g)
    self.assertFalse(m)

    (g, m) = CompareVersions('foobar', 'baz')
    self.assertFalse(g)
    self.assertFalse(m)
    (g, m) = CompareVersions('3.32', 'baz')
    self.assertFalse(g)
    self.assertFalse(m)

    (g, m) = CompareVersions('3.4', '3.3')
    self.assertTrue(g)
    self.assertFalse(m)
    (g, m) = CompareVersions('3.3', '3.4')
    self.assertFalse(g)
    self.assertFalse(m)
    (g, m) = CompareVersions('4.1', '3.33')
    self.assertTrue(g)
    self.assertTrue(m)
    (g, m) = CompareVersions('3.10', '3.1')
    self.assertTrue(g)
    self.assertFalse(m)

  def _AssertProxyInfosEqual(self, pi1, pi2):
    self.assertEqual(pi1.proxy_type, pi2.proxy_type)
    self.assertEqual(pi1.proxy_host, pi2.proxy_host)
    self.assertEqual(pi1.proxy_port, pi2.proxy_port)
    self.assertEqual(pi1.proxy_rdns, pi2.proxy_rdns)
    self.assertEqual(pi1.proxy_user, pi2.proxy_user)
    self.assertEqual(pi1.proxy_pass, pi2.proxy_pass)

  def testMakeMetadataLine(self):
    test_params = (TestParams(args=('AFairlyShortKey', 'Value'),
                              expected='    AFairlyShortKey:        Value'),
                   TestParams(args=('', 'Value'),
                              expected='    :                       Value'),
                   TestParams(args=('AnotherKey', 'Value'),
                              kwargs={'indent': 2},
                              expected='        AnotherKey:         Value'),
                   TestParams(args=('AKeyMuchLongerThanTheLast', 'Value'),
                              expected=('    AKeyMuchLongerThanTheLast:Value')))
    for params in test_params:
      line = ls_helper.MakeMetadataLine(*(params.args), **(params.kwargs))
      self.assertEqual(line, params.expected)

  def testSetProxyInfo(self):
    """Tests SetProxyInfo for various proxy use cases in boto file."""
    valid_proxy_types = ['socks4', 'socks5', 'http']
    valid_proxy_host = ['hostname', '1.2.3.4', None]
    valid_proxy_port = [8888, 0]
    valid_proxy_user = ['foo', None]
    valid_proxy_pass = ['Bar', None]
    valid_proxy_rdns = [True, False, None]

    proxy_type_spec = {
        'socks4': httplib2.socks.PROXY_TYPE_SOCKS4,
        'socks5': httplib2.socks.PROXY_TYPE_SOCKS5,
        'http': httplib2.socks.PROXY_TYPE_HTTP,
        'https': httplib2.socks.PROXY_TYPE_HTTP
    }

    #Generate all input combination values
    boto_proxy_config_test_values = [{
        'proxy_host': p_h,
        'proxy_type': p_t,
        'proxy_port': p_p,
        'proxy_user': p_u,
        'proxy_pass': p_s,
        'proxy_rdns': p_d
    }
                                     for p_h in valid_proxy_host
                                     for p_s in valid_proxy_pass
                                     for p_p in valid_proxy_port
                                     for p_u in valid_proxy_user
                                     for p_t in valid_proxy_types
                                     for p_d in valid_proxy_rdns]

    #Test all input combination values
    with SetEnvironmentForTest({'http_proxy': 'http://host:50'}):
      for test_values in boto_proxy_config_test_values:
        proxy_type = proxy_type_spec.get(test_values.get('proxy_type'))
        proxy_host = test_values.get('proxy_host')
        proxy_port = test_values.get('proxy_port')
        proxy_user = test_values.get('proxy_user')
        proxy_pass = test_values.get('proxy_pass')
        proxy_rdns = bool(test_values.get('proxy_rdns'))

        # Added to force socks proxies not to use rdns as in SetProxyInfo()
        if not (proxy_type == proxy_type_spec['http']):
          proxy_rdns = False

        expected = httplib2.ProxyInfo(proxy_host=proxy_host,
                                      proxy_type=proxy_type,
                                      proxy_port=proxy_port,
                                      proxy_user=proxy_user,
                                      proxy_pass=proxy_pass,
                                      proxy_rdns=proxy_rdns)

        # Checks to make sure environment variable fallbacks are working
        if not (expected.proxy_host and expected.proxy_port):
          expected = httplib2.ProxyInfo(proxy_type_spec['http'], 'host', 50)
          # Assume proxy_rnds is True if a proxy environment variable exists.
          if test_values.get('proxy_rdns') == None:
            expected.proxy_rdns = True

        self._AssertProxyInfosEqual(boto_util.SetProxyInfo(test_values),
                                    expected)

  def testProxyInfoFromEnvironmentVar(self):
    """Tests ProxyInfoFromEnvironmentVar for various cases."""
    valid_variables = ['http_proxy', 'https_proxy']
    if not system_util.IS_WINDOWS:
      # Dynamically set Windows environment variables are case-insensitive.
      valid_variables.append('HTTPS_PROXY')
    # Clear any existing environment variables for the duration of the test.
    clear_dict = {}
    for key in valid_variables:
      clear_dict[key] = None
    with SetEnvironmentForTest(clear_dict):
      for env_var in valid_variables:
        for url_string in ['hostname', 'http://hostname', 'https://hostname']:
          with SetEnvironmentForTest({env_var: url_string}):
            self._AssertProxyInfosEqual(
                boto_util.ProxyInfoFromEnvironmentVar(env_var),
                httplib2.ProxyInfo(
                    httplib2.socks.PROXY_TYPE_HTTP, 'hostname',
                    443 if env_var.lower().startswith('https') else 80))
            # Shouldn't populate info for other variables
            for other_env_var in valid_variables:
              if other_env_var == env_var:
                continue
              self._AssertProxyInfosEqual(
                  boto_util.ProxyInfoFromEnvironmentVar(other_env_var),
                  httplib2.ProxyInfo(httplib2.socks.PROXY_TYPE_HTTP, None, 0))
        for url_string in [
            '1.2.3.4:50', 'http://1.2.3.4:50', 'https://1.2.3.4:50'
        ]:
          with SetEnvironmentForTest({env_var: url_string}):
            self._AssertProxyInfosEqual(
                boto_util.ProxyInfoFromEnvironmentVar(env_var),
                httplib2.ProxyInfo(httplib2.socks.PROXY_TYPE_HTTP, '1.2.3.4',
                                   50))
        for url_string in [
            'foo:bar@1.2.3.4:50', 'http://foo:bar@1.2.3.4:50',
            'https://foo:bar@1.2.3.4:50'
        ]:
          with SetEnvironmentForTest({env_var: url_string}):
            self._AssertProxyInfosEqual(
                boto_util.ProxyInfoFromEnvironmentVar(env_var),
                httplib2.ProxyInfo(httplib2.socks.PROXY_TYPE_HTTP,
                                   '1.2.3.4',
                                   50,
                                   proxy_user='foo',
                                   proxy_pass='bar'))
        for url_string in [
            'bar@1.2.3.4:50', 'http://bar@1.2.3.4:50', 'https://bar@1.2.3.4:50'
        ]:
          with SetEnvironmentForTest({env_var: url_string}):
            self._AssertProxyInfosEqual(
                boto_util.ProxyInfoFromEnvironmentVar(env_var),
                httplib2.ProxyInfo(httplib2.socks.PROXY_TYPE_HTTP,
                                   '1.2.3.4',
                                   50,
                                   proxy_user='bar'))
      for env_var in ['proxy', 'noproxy', 'garbage']:
        for url_string in ['1.2.3.4:50', 'http://1.2.3.4:50']:
          with SetEnvironmentForTest({env_var: url_string}):
            self._AssertProxyInfosEqual(
                boto_util.ProxyInfoFromEnvironmentVar(env_var),
                httplib2.ProxyInfo(httplib2.socks.PROXY_TYPE_HTTP, None, 0))

  # We want to make sure the wrapped function is called without executing it.
  @mock.patch.object(retry_util.http_wrapper,
                     'HandleExceptionsAndRebuildHttpConnections')
  @mock.patch.object(retry_util.logging, 'info')
  def testWarnAfterManyRetriesHandler(self, mock_log_info_fn, mock_wrapped_fn):
    # The only ExceptionRetryArgs attributes that the function cares about are
    # num_retries and total_wait_sec; we can pass None for the other values.
    retry_args_over_threshold = retry_util.http_wrapper.ExceptionRetryArgs(
        None, None, None, 3, None, constants.LONG_RETRY_WARN_SEC + 1)
    retry_args_under_threshold = retry_util.http_wrapper.ExceptionRetryArgs(
        None, None, None, 2, None, constants.LONG_RETRY_WARN_SEC - 1)

    retry_util.LogAndHandleRetries()(retry_args_under_threshold)
    self.assertTrue(mock_wrapped_fn.called)
    # Check that we didn't emit a message.
    self.assertFalse(mock_log_info_fn.called)

    retry_util.LogAndHandleRetries()(retry_args_over_threshold)
    self.assertEqual(mock_wrapped_fn.call_count, 2)
    # Check that we did emit a message.
    self.assertTrue(mock_log_info_fn.called)

  def testUIDecimalShort(self):
    """Tests DecimalShort for UI."""
    self.assertEqual('12.3b', DecimalShort(12345678910))
    self.assertEqual('123.5m', DecimalShort(123456789))
    self.assertEqual('1.2k', DecimalShort(1234))
    self.assertEqual('1.0k', DecimalShort(1000))
    self.assertEqual('432', DecimalShort(432))
    self.assertEqual('43.2t', DecimalShort(43.25 * 10**12))
    self.assertEqual('43.2q', DecimalShort(43.25 * 10**15))
    self.assertEqual('43250.0q', DecimalShort(43.25 * 10**18))

  def testUIPrettyTime(self):
    """Tests PrettyTime for UI."""
    self.assertEqual('25:02:10', PrettyTime(90130))
    self.assertEqual('01:00:00', PrettyTime(3600))
    self.assertEqual('00:59:59', PrettyTime(3599))
    self.assertEqual('100+ hrs', PrettyTime(3600 * 100))
    self.assertEqual('999+ hrs', PrettyTime(3600 * 10000))

  def testUIHumanReadableWithDecimalPlaces(self):
    """Tests HumanReadableWithDecimalPlaces for UI."""
    self.assertEqual('1.0 GiB',
                     HumanReadableWithDecimalPlaces(1024**3 + 1024**2 * 10, 1))
    self.assertEqual('1.0 GiB', HumanReadableWithDecimalPlaces(1024**3), 1)
    self.assertEqual('1.01 GiB',
                     HumanReadableWithDecimalPlaces(1024**3 + 1024**2 * 10, 2))
    self.assertEqual('1.000 GiB',
                     HumanReadableWithDecimalPlaces(1024**3 + 1024**2 * 5, 3))
    self.assertEqual('1.10 GiB',
                     HumanReadableWithDecimalPlaces(1024**3 + 1024**2 * 100, 2))
    self.assertEqual('1.100 GiB',
                     HumanReadableWithDecimalPlaces(1024**3 + 1024**2 * 100, 3))
    self.assertEqual('10.00 MiB',
                     HumanReadableWithDecimalPlaces(1024**2 * 10, 2))
    # The test below is good for rounding.
    self.assertEqual('2.01 GiB', HumanReadableWithDecimalPlaces(2157969408, 2))
    self.assertEqual('2.0 GiB', HumanReadableWithDecimalPlaces(2157969408, 1))
    self.assertEqual('0 B', HumanReadableWithDecimalPlaces(0, 0))
    self.assertEqual('0.00 B', HumanReadableWithDecimalPlaces(0, 2))
    self.assertEqual('0.00000 B', HumanReadableWithDecimalPlaces(0, 5))

  def testAmzGenerationTypeConversions(self):
    amz_gen_as_str = six.ensure_str('9PpsRjBGjBh90IvIS96dgRc_UL6NyGqD')
    amz_gen_as_long = 25923956239092482442895228561437790190304192615858167521375267910356975448388
    self.assertEqual(text_util.DecodeLongAsString(amz_gen_as_long),
                     amz_gen_as_str)
    self.assertEqual(text_util.EncodeStringAsLong(amz_gen_as_str),
                     amz_gen_as_long)

  def DoTestAddQueryParamToUrl(self, url, param_name, param_val, expected_url):
    new_url = text_util.AddQueryParamToUrl(url, param_name, param_val)
    self.assertEqual(new_url, expected_url)

  def testAddQueryParamToUrlWorksForASCIIValues(self):
    # Note that the params here contain empty values and duplicates.
    old_url = 'http://foo.bar/path/endpoint?a=1&a=2&b=3&c='
    param_name = 'newparam'
    param_val = 'nevalue'
    expected_url = '{}&{}={}'.format(old_url, param_name, param_val)

    self.DoTestAddQueryParamToUrl(old_url, param_name, param_val, expected_url)

  def testAddQueryParamToUrlWorksForUTF8Values(self):
    old_url = 'http://foo.bar/path/êndpoint?Â=1&a=2&ß=3&c='
    param_name = 'nêwparam'
    param_val = 'nêwvalue'
    # Expected return value is a UTF-8 encoded `str`.
    expected_url = '{}&{}={}'.format(old_url, param_name, param_val)

    self.DoTestAddQueryParamToUrl(old_url, param_name, param_val, expected_url)

  def testAddQueryParamToUrlWorksForRawUnicodeValues(self):
    old_url = 'http://foo.bar/path/êndpoint?Â=1&a=2&ß=3&c='
    param_name = 'nêwparam'
    param_val = 'nêwvalue'
    # Since the original URL was a `unicode`, the returned URL should also be.
    expected_url = '{}&{}={}'.format(old_url, param_name, param_val)

    self.DoTestAddQueryParamToUrl(old_url, param_name, param_val, expected_url)

  @mock.patch.object(boto_util, 'GetMaxUploadCompressionBufferSize')
  def testGetMaxConcurrentCompressedUploadsMinimum(self, mock_config):
    """Test GetMaxConcurrentCompressedUploads returns at least 1."""
    mock_config.return_value = 0
    self.assertEqual(boto_util.GetMaxConcurrentCompressedUploads(), 1)
    mock_config.return_value = -1
    self.assertEqual(boto_util.GetMaxConcurrentCompressedUploads(), 1)
