# Copyright (c) 2010 Robert Mela
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
#
from tests.compat import mock, unittest

import datetime
import hashlib
import hmac
import locale
import time

import boto.utils
from boto.utils import Password
from boto.utils import pythonize_name
from boto.utils import _build_instance_metadata_url
from boto.utils import get_instance_userdata
from boto.utils import retry_url
from boto.utils import LazyLoadMetadata

from boto.compat import json, _thread


@unittest.skip("http://bugs.python.org/issue7980")
class TestThreadImport(unittest.TestCase):
    def test_strptime(self):
        def f():
            for m in range(1, 13):
                for d in range(1,29):
                    boto.utils.parse_ts('2013-01-01T00:00:00Z')

        for _ in range(10):
            _thread.start_new_thread(f, ())

        time.sleep(3)


class TestPassword(unittest.TestCase):
    """Test basic password functionality"""

    def clstest(self, cls):
        """Insure that password.__eq__ hashes test value before compare."""
        password = cls('foo')
        self.assertNotEquals(password, 'foo')

        password.set('foo')
        hashed = str(password)
        self.assertEquals(password, 'foo')
        self.assertEquals(password.str, hashed)

        password = cls(hashed)
        self.assertNotEquals(password.str, 'foo')
        self.assertEquals(password, 'foo')
        self.assertEquals(password.str, hashed)

    def test_aaa_version_1_9_default_behavior(self):
        self.clstest(Password)

    def test_custom_hashclass(self):
        class SHA224Password(Password):
            hashfunc = hashlib.sha224

        password = SHA224Password()
        password.set('foo')
        self.assertEquals(hashlib.sha224(b'foo').hexdigest(), str(password))

    def test_hmac(self):
        def hmac_hashfunc(cls, msg):
            if not isinstance(msg, bytes):
                msg = msg.encode('utf-8')
            return hmac.new(b'mysecretkey', msg)

        class HMACPassword(Password):
            hashfunc = hmac_hashfunc

        self.clstest(HMACPassword)
        password = HMACPassword()
        password.set('foo')

        self.assertEquals(str(password),
                          hmac.new(b'mysecretkey', b'foo').hexdigest())

    def test_constructor(self):
        hmac_hashfunc = lambda msg: hmac.new(b'mysecretkey', msg)

        password = Password(hashfunc=hmac_hashfunc)
        password.set('foo')
        self.assertEquals(password.str,
                          hmac.new(b'mysecretkey', b'foo').hexdigest())


class TestPythonizeName(unittest.TestCase):
    def test_empty_string(self):
        self.assertEqual(pythonize_name(''), '')

    def test_all_lower_case(self):
        self.assertEqual(pythonize_name('lowercase'), 'lowercase')

    def test_all_upper_case(self):
        self.assertEqual(pythonize_name('UPPERCASE'), 'uppercase')

    def test_camel_case(self):
        self.assertEqual(pythonize_name('OriginallyCamelCased'),
                         'originally_camel_cased')

    def test_already_pythonized(self):
        self.assertEqual(pythonize_name('already_pythonized'),
                         'already_pythonized')

    def test_multiple_upper_cased_letters(self):
        self.assertEqual(pythonize_name('HTTPRequest'), 'http_request')
        self.assertEqual(pythonize_name('RequestForHTTP'), 'request_for_http')

    def test_string_with_numbers(self):
        self.assertEqual(pythonize_name('HTTPStatus200Ok'), 'http_status_200_ok')


class TestBuildInstanceMetadataURL(unittest.TestCase):
    def test_normal(self):
        # This is the all-defaults case.
        self.assertEqual(_build_instance_metadata_url(
                'http://169.254.169.254',
                'latest',
                'meta-data/'
            ),
            'http://169.254.169.254/latest/meta-data/'
        )

    def test_custom_path(self):
        self.assertEqual(_build_instance_metadata_url(
                'http://169.254.169.254',
                'latest',
                'dynamic/'
            ),
            'http://169.254.169.254/latest/dynamic/'
        )

    def test_custom_version(self):
        self.assertEqual(_build_instance_metadata_url(
                'http://169.254.169.254',
                '1.0',
                'meta-data/'
            ),
            'http://169.254.169.254/1.0/meta-data/'
        )

    def test_custom_url(self):
        self.assertEqual(_build_instance_metadata_url(
                'http://10.0.1.5',
                'latest',
                'meta-data/'
            ),
            'http://10.0.1.5/latest/meta-data/'
        )

    def test_all_custom(self):
        self.assertEqual(_build_instance_metadata_url(
                'http://10.0.1.5',
                '2013-03-22',
                'user-data'
            ),
            'http://10.0.1.5/2013-03-22/user-data'
        )

class TestRetryURL(unittest.TestCase):
    def setUp(self):
        self.urlopen_patch = mock.patch('boto.compat.urllib.request.urlopen')
        self.opener_patch = mock.patch('boto.compat.urllib.request.build_opener')
        self.urlopen = self.urlopen_patch.start()
        self.opener = self.opener_patch.start()

    def tearDown(self):
        self.urlopen_patch.stop()
        self.opener_patch.stop()

    def set_normal_response(self, response):
        fake_response = mock.Mock()
        fake_response.read.return_value = response
        self.urlopen.return_value = fake_response

    def set_no_proxy_allowed_response(self, response):
        fake_response = mock.Mock()
        fake_response.read.return_value = response
        self.opener.return_value.open.return_value = fake_response

    def test_retry_url_uses_proxy(self):
        self.set_normal_response('normal response')
        self.set_no_proxy_allowed_response('no proxy response')

        response = retry_url('http://10.10.10.10/foo', num_retries=1)
        self.assertEqual(response, 'no proxy response')

    def test_retry_url_using_bytes_and_string_response(self):
        test_value = 'normal response'
        fake_response = mock.Mock()

        # test using unicode
        fake_response.read.return_value = test_value
        self.opener.return_value.open.return_value = fake_response
        response = retry_url('http://10.10.10.10/foo', num_retries=1)
        self.assertEqual(response, test_value)

        # test using bytes
        fake_response.read.return_value = test_value.encode('utf-8')
        self.opener.return_value.open.return_value = fake_response
        response = retry_url('http://10.10.10.10/foo', num_retries=1)
        self.assertEqual(response, test_value)

class TestLazyLoadMetadata(unittest.TestCase):

    def setUp(self):
        self.retry_url_patch = mock.patch('boto.utils.retry_url')
        boto.utils.retry_url = self.retry_url_patch.start()

    def tearDown(self):
        self.retry_url_patch.stop()

    def set_normal_response(self, data):
        # here "data" should be a list of return values in some order
        fake_response = mock.Mock()
        fake_response.side_effect = data
        boto.utils.retry_url = fake_response

    def test_meta_data_with_invalid_json_format_happened_once(self):
        # here "key_data" will be stored in the "self._leaves"
        # when the class "LazyLoadMetadata" initialized
        key_data = "test"
        invalid_data = '{"invalid_json_format" : true,}'
        valid_data = '{ "%s" : {"valid_json_format": true}}' % key_data
        url = "/".join(["http://169.254.169.254", key_data])
        num_retries = 2

        self.set_normal_response([key_data, invalid_data, valid_data])
        response = LazyLoadMetadata(url, num_retries)
        self.assertEqual(list(response.values())[0], json.loads(valid_data))

    def test_meta_data_with_invalid_json_format_happened_twice(self):
        key_data = "test"
        invalid_data = '{"invalid_json_format" : true,}'
        valid_data = '{ "%s" : {"valid_json_format": true}}' % key_data
        url = "/".join(["http://169.254.169.254", key_data])
        num_retries = 2

        self.set_normal_response([key_data, invalid_data, invalid_data])
        response = LazyLoadMetadata(url, num_retries)
        with self.assertRaises(ValueError):
            response.values()[0]

    def test_user_data(self):
        self.set_normal_response(['foo'])

        userdata = get_instance_userdata()

        self.assertEqual('foo', userdata)

        boto.utils.retry_url.assert_called_with(
            'http://169.254.169.254/latest/user-data',
            retry_on_404=False,
            num_retries=5, timeout=None)

    def test_user_data_timeout(self):
        self.set_normal_response(['foo'])

        userdata = get_instance_userdata(timeout=1, num_retries=2)

        self.assertEqual('foo', userdata)

        boto.utils.retry_url.assert_called_with(
            'http://169.254.169.254/latest/user-data',
            retry_on_404=False,
            num_retries=2, timeout=1)


class TestStringToDatetimeParsing(unittest.TestCase):
    """ Test string to datetime parsing """
    def setUp(self):
        self._saved = locale.setlocale(locale.LC_ALL)
        try:
            locale.setlocale(locale.LC_ALL, 'de_DE.UTF-8')
        except locale.Error:
            self.skipTest('Unsupported locale setting')

    def tearDown(self):
        locale.setlocale(locale.LC_ALL, self._saved)

    def test_nonus_locale(self):
        test_string = 'Thu, 15 May 2014 09:06:03 GMT'

        # Default strptime shoudl fail
        with self.assertRaises(ValueError):
            datetime.datetime.strptime(test_string, boto.utils.RFC1123)

        # Our parser should succeed
        result = boto.utils.parse_ts(test_string)

        self.assertEqual(2014, result.year)
        self.assertEqual(5, result.month)
        self.assertEqual(15, result.day)
        self.assertEqual(9, result.hour)
        self.assertEqual(6, result.minute)


class TestHostIsIPV6(unittest.TestCase):

    def test_is_ipv6_no_brackets(self):
        hostname = 'bf1d:cb48:4513:d1f1:efdd:b290:9ff9:64be'
        result = boto.utils.host_is_ipv6(hostname)
        self.assertTrue(result)

    def test_is_ipv6_with_brackets(self):
        hostname = '[bf1d:cb48:4513:d1f1:efdd:b290:9ff9:64be]'
        result = boto.utils.host_is_ipv6(hostname)
        self.assertTrue(result)

    def test_is_ipv6_with_brackets_and_port(self):
        hostname = '[bf1d:cb48:4513:d1f1:efdd:b290:9ff9:64be]:8080'
        result = boto.utils.host_is_ipv6(hostname)
        self.assertTrue(result)

    def test_is_ipv6_no_brackets_abbreviated(self):
        hostname = 'bf1d:cb48:4513::'
        result = boto.utils.host_is_ipv6(hostname)
        self.assertTrue(result)

    def test_is_ipv6_with_brackets_abbreviated(self):
        hostname = '[bf1d:cb48:4513::'
        result = boto.utils.host_is_ipv6(hostname)
        self.assertTrue(result)

    def test_is_ipv6_with_brackets_and_port_abbreviated(self):
        hostname = '[bf1d:cb48:4513::]:8080'
        result = boto.utils.host_is_ipv6(hostname)
        self.assertTrue(result)

    def test_empty_string(self):
        result = boto.utils.host_is_ipv6('')
        self.assertFalse(result)

    def test_not_of_string_type(self):
        hostnames = [None, 0, False, [], {}]
        for h in hostnames:
            result = boto.utils.host_is_ipv6(h)
            self.assertFalse(result)

    def test_ipv4_no_port(self):
        result = boto.utils.host_is_ipv6('192.168.1.1')
        self.assertFalse(result)

    def test_ipv4_with_port(self):
        result = boto.utils.host_is_ipv6('192.168.1.1:8080')
        self.assertFalse(result)

    def test_hostnames_are_not_ipv6_with_port(self):
        result = boto.utils.host_is_ipv6('example.org:8080')
        self.assertFalse(result)

    def test_hostnames_are_not_ipv6_without_port(self):
        result = boto.utils.host_is_ipv6('example.org')
        self.assertFalse(result)


class TestParseHost(unittest.TestCase):

    def test_parses_ipv6_hosts_no_brackets(self):
        host = 'bf1d:cb48:4513:d1f1:efdd:b290:9ff9:64be'
        result = boto.utils.parse_host(host)
        self.assertEquals(result, host)

    def test_parses_ipv6_hosts_with_brackets_stripping_them(self):
        host = '[bf1d:cb48:4513:d1f1:efdd:b290:9ff9:64be]'
        result = boto.utils.parse_host(host)
        self.assertEquals(result, 'bf1d:cb48:4513:d1f1:efdd:b290:9ff9:64be')

    def test_parses_ipv6_hosts_with_brackets_and_port(self):
        host = '[bf1d:cb48:4513:d1f1:efdd:b290:9ff9:64be]:8080'
        result = boto.utils.parse_host(host)
        self.assertEquals(result, 'bf1d:cb48:4513:d1f1:efdd:b290:9ff9:64be')

    def test_parses_ipv4_hosts(self):
        host = '10.0.1.1'
        result = boto.utils.parse_host(host)
        self.assertEquals(result, host)

    def test_parses_ipv4_hosts_with_port(self):
        host = '192.168.168.200:8080'
        result = boto.utils.parse_host(host)
        self.assertEquals(result, '192.168.168.200')

    def test_parses_hostnames_with_port(self):
        host = 'example.org:8080'
        result = boto.utils.parse_host(host)
        self.assertEquals(result, 'example.org')

    def test_parses_hostnames_without_port(self):
        host = 'example.org'
        result = boto.utils.parse_host(host)
        self.assertEquals(result, host)

if __name__ == '__main__':
    unittest.main()
