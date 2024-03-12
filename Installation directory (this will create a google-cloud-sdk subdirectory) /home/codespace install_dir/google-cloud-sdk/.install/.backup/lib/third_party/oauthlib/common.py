# -*- coding: utf-8 -*-
"""oauthlib.common ~~~~~~~~~~~~~~

This module provides data structures and utilities common
to all implementations of OAuth.
"""
from __future__ import absolute_import, unicode_literals

import collections
import datetime
import logging
import re
import sys
import time

try:
  from secrets import randbits
  from secrets import SystemRandom
except ImportError:
  from random import getrandbits as randbits
  from random import SystemRandom
try:
  from urllib import quote as _quote
  from urllib import unquote as _unquote
  from urllib import urlencode as _urlencode
except ImportError:
  from urllib.parse import quote as _quote
  from urllib.parse import unquote as _unquote
  from urllib.parse import urlencode as _urlencode
try:
  import urlparse
except ImportError:
  import urllib.parse as urlparse

UNICODE_ASCII_CHARACTER_SET = ('abcdefghijklmnopqrstuvwxyz'
                               'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
                               '0123456789')

CLIENT_ID_CHARACTER_SET = (r' !"#$%&\'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMN'
                           'OPQRSTUVWXYZ[\\]^_`abcdefghijklmnopqrstuvwxyz{|}')

SANITIZE_PATTERN = re.compile(r'([^&;]*(?:password|token)[^=]*=)[^&;]+',
                              re.IGNORECASE)
INVALID_HEX_PATTERN = re.compile(r'%[^0-9A-Fa-f]|%[0-9A-Fa-f][^0-9A-Fa-f]')

always_safe = ('ABCDEFGHIJKLMNOPQRSTUVWXYZ'
               'abcdefghijklmnopqrstuvwxyz'
               '0123456789'
               '_.-')

log = logging.getLogger('oauthlib')

PY3 = sys.version_info[0] == 3

if PY3:
  unicode_type = str
else:
  unicode_type = unicode


# 'safe' must be bytes (Python 2.6 requires bytes, other versions allow either)
def quote(s, safe=b'/'):
  s = s.encode('utf-8') if isinstance(s, unicode_type) else s
  s = _quote(s, safe)
  # PY3 always returns unicode.  PY2 may return either, depending on whether
  # it had to modify the string.
  if isinstance(s, bytes):
    s = s.decode('utf-8')
  return s


def unquote(s):
  s = _unquote(s)
  # PY3 always returns unicode.  PY2 seems to always return what you give it,
  # which differs from quote's behavior.  Just to be safe, make sure it is
  # unicode before we return.
  if isinstance(s, bytes):
    s = s.decode('utf-8')
  return s


def urlencode(params):
  utf8_params = encode_params_utf8(params)
  urlencoded = _urlencode(utf8_params)
  if isinstance(urlencoded, unicode_type):  # PY3 returns unicode
    return urlencoded
  else:
    return urlencoded.decode('utf-8')


def encode_params_utf8(params):
  """Ensures that all parameters in a list of 2-element tuples are encoded to

    bytestrings using UTF-8
    """
  encoded = []
  for k, v in params:
    encoded.append((k.encode('utf-8') if isinstance(k, unicode_type) else k,
                    v.encode('utf-8') if isinstance(v, unicode_type) else v))
  return encoded


def decode_params_utf8(params):
  """Ensures that all parameters in a list of 2-element tuples are decoded to

    unicode using UTF-8.
    """
  decoded = []
  for k, v in params:
    decoded.append((k.decode('utf-8') if isinstance(k, bytes) else k,
                    v.decode('utf-8') if isinstance(v, bytes) else v))
  return decoded


urlencoded = set(always_safe) | set('=&;:%+~,*@!()/?\'$')


def urldecode(query):
  """Decode a query string in x-www-form-urlencoded format into a sequence

    of two-element tuples.

    Unlike urlparse.parse_qsl(..., strict_parsing=True) urldecode will enforce
    correct formatting of the query string by validation. If validation fails
    a ValueError will be raised. urllib.parse_qsl will only raise errors if
    any of name-value pairs omits the equals sign.
    """
  # Check if query contains invalid characters
  if query and not set(query) <= urlencoded:
    error = ('Error trying to decode a non urlencoded string. '
             'Found invalid characters: %s '
             "in the string: '%s'. "
             'Please ensure the request/response body is '
             'x-www-form-urlencoded.')
    raise ValueError(error % (set(query) - urlencoded, query))

  # Check for correctly hex encoded values using a regular expression
  # All encoded values begin with % followed by two hex characters
  # correct = %00, %A0, %0A, %FF
  # invalid = %G0, %5H, %PO
  if INVALID_HEX_PATTERN.search(query):
    raise ValueError('Invalid hex encoding in query string.')

  # We encode to utf-8 prior to parsing because parse_qsl behaves
  # differently on unicode input in python 2 and 3.
  # Python 2.7
  # >>> urlparse.parse_qsl(u'%E5%95%A6%E5%95%A6')
  # u'\xe5\x95\xa6\xe5\x95\xa6'
  # Python 2.7, non unicode input gives the same
  # >>> urlparse.parse_qsl('%E5%95%A6%E5%95%A6')
  # '\xe5\x95\xa6\xe5\x95\xa6'
  # but now we can decode it to unicode
  # >>> urlparse.parse_qsl('%E5%95%A6%E5%95%A6').decode('utf-8')
  # u'\u5566\u5566'
  # Python 3.3 however
  # >>> urllib.parse.parse_qsl(u'%E5%95%A6%E5%95%A6')
  # u'\u5566\u5566'
  query = query.encode('utf-8') if not PY3 and isinstance(
      query, unicode_type) else query
  # We want to allow queries such as "c2" whereas urlparse.parse_qsl
  # with the strict_parsing flag will not.
  params = urlparse.parse_qsl(query, keep_blank_values=True)

  # unicode all the things
  return decode_params_utf8(params)


def extract_params(raw):
  """Extract parameters and return them as a list of 2-tuples.

    Will successfully extract parameters from urlencoded query strings,
    dicts, or lists of 2-tuples. Empty strings/dicts/lists will return an
    empty list of parameters. Any other input will result in a return
    value of None.
    """
  if isinstance(raw, bytes) or isinstance(raw, unicode_type):
    try:
      params = urldecode(raw)
    except ValueError:
      params = None
  elif hasattr(raw, '__iter__'):
    try:
      dict(raw)
    except ValueError:
      params = None
    except TypeError:
      params = None
    else:
      params = list(raw.items() if isinstance(raw, dict) else raw)
      params = decode_params_utf8(params)
  else:
    params = None

  return params


def generate_nonce():
  """Generate pseudorandom nonce that is unlikely to repeat.

    Per `section 3.3`_ of the OAuth 1 RFC 5849 spec.
    Per `section 3.2.1`_ of the MAC Access Authentication spec.

    A random 64-bit number is appended to the epoch timestamp for both
    randomness and to decrease the likelihood of collisions.

    .. _`section 3.2.1`:
    https://tools.ietf.org/html/draft-ietf-oauth-v2-http-mac-01#section-3.2.1
    .. _`section 3.3`: https://tools.ietf.org/html/rfc5849#section-3.3
    """
  return unicode_type(unicode_type(randbits(64)) + generate_timestamp())


def generate_timestamp():
  """Get seconds since epoch (UTC).

    Per `section 3.3`_ of the OAuth 1 RFC 5849 spec.
    Per `section 3.2.1`_ of the MAC Access Authentication spec.

    .. _`section 3.2.1`:
    https://tools.ietf.org/html/draft-ietf-oauth-v2-http-mac-01#section-3.2.1
    .. _`section 3.3`: https://tools.ietf.org/html/rfc5849#section-3.3
    """
  return unicode_type(int(time.time()))


def generate_token(length=30, chars=UNICODE_ASCII_CHARACTER_SET):
  """Generates a non-guessable OAuth token

    OAuth (1 and 2) does not specify the format of tokens except that they
    should be strings of random characters. Tokens should not be guessable
    and entropy when generating the random characters is important. Which is
    why SystemRandom is used instead of the default random.choice method.
    """
  rand = SystemRandom()
  return ''.join(rand.choice(chars) for x in range(length))


def generate_signed_token(private_pem, request):
  import jwt

  now = datetime.datetime.utcnow()

  claims = {
      'scope': request.scope,
      'exp': now + datetime.timedelta(seconds=request.expires_in)
  }

  claims.update(request.claims)

  token = jwt.encode(claims, private_pem, 'RS256')
  token = to_unicode(token, 'UTF-8')

  return token


def verify_signed_token(public_pem, token):
  import jwt

  return jwt.decode(token, public_pem, algorithms=['RS256'])


def generate_client_id(length=30, chars=CLIENT_ID_CHARACTER_SET):
  """Generates an OAuth client_id

    OAuth 2 specify the format of client_id in
    https://tools.ietf.org/html/rfc6749#appendix-A.
    """
  return generate_token(length, chars)


def add_params_to_qs(query, params):
  """Extend a query with a list of two-tuples."""
  if isinstance(params, dict):
    params = params.items()
  queryparams = urlparse.parse_qsl(query, keep_blank_values=True)
  queryparams.extend(params)
  return urlencode(queryparams)


def add_params_to_uri(uri, params, fragment=False):
  """Add a list of two-tuples to the uri query components."""
  sch, net, path, par, query, fra = urlparse.urlparse(uri)
  if fragment:
    fra = add_params_to_qs(fra, params)
  else:
    query = add_params_to_qs(query, params)
  return urlparse.urlunparse((sch, net, path, par, query, fra))


def safe_string_equals(a, b):
  """ Near-constant time string comparison.

    Used in order to avoid timing attacks on sensitive information such
    as secret keys during request verification (`rootLabs`_).

    .. _`rootLabs`:
    http://rdist.root.org/2010/01/07/timing-independent-array-comparison/

    """
  if len(a) != len(b):
    return False

  result = 0
  for x, y in zip(a, b):
    result |= ord(x) ^ ord(y)
  return result == 0


def to_unicode(data, encoding='UTF-8'):
  """Convert a number of different types of objects to unicode."""
  if isinstance(data, unicode_type):
    return data

  if isinstance(data, bytes):
    return unicode_type(data, encoding=encoding)

  if hasattr(data, '__iter__'):
    try:
      dict(data)
    except TypeError:
      pass
    except ValueError:
      # Assume it's a one dimensional data structure
      return (to_unicode(i, encoding) for i in data)
    else:
      # We support 2.6 which lacks dict comprehensions
      if hasattr(data, 'items'):
        data = data.items()
      return dict(
          ((to_unicode(k, encoding), to_unicode(v, encoding)) for k, v in data))

  return data


class CaseInsensitiveDict(dict):
  """Basic case insensitive dict with strings only keys."""

  proxy = {}

  def __init__(self, data):
    self.proxy = dict((k.lower(), k) for k in data)
    for k in data:
      self[k] = data[k]

  def __contains__(self, k):
    return k.lower() in self.proxy

  def __delitem__(self, k):
    key = self.proxy[k.lower()]
    super(CaseInsensitiveDict, self).__delitem__(key)
    del self.proxy[k.lower()]

  def __getitem__(self, k):
    key = self.proxy[k.lower()]
    return super(CaseInsensitiveDict, self).__getitem__(key)

  def get(self, k, default=None):
    return self[k] if k in self else default

  def __setitem__(self, k, v):
    super(CaseInsensitiveDict, self).__setitem__(k, v)
    self.proxy[k.lower()] = k

  def update(self, *args, **kwargs):
    super(CaseInsensitiveDict, self).update(*args, **kwargs)
    for k in dict(*args, **kwargs):
      self.proxy[k.lower()] = k


class Request(object):
  """A malleable representation of a signable HTTP request.

    Body argument may contain any data, but parameters will only be decoded if
    they are one of:

    * urlencoded query string
    * dict
    * list of 2-tuples

    Anything else will be treated as raw body data to be passed through
    unmolested.
    """

  def __init__(self,
               uri,
               http_method='GET',
               body=None,
               headers=None,
               encoding='utf-8'):
    # Convert to unicode using encoding if given, else assume unicode
    encode = lambda x: to_unicode(x, encoding) if encoding else x

    self.uri = encode(uri)
    self.http_method = encode(http_method)
    self.headers = CaseInsensitiveDict(encode(headers or {}))
    self.body = encode(body)
    self.decoded_body = extract_params(self.body)
    self.oauth_params = []
    self.validator_log = {}

    self._params = {
        'access_token': None,
        'client': None,
        'client_id': None,
        'client_secret': None,
        'code': None,
        'code_challenge': None,
        'code_challenge_method': None,
        'code_verifier': None,
        'extra_credentials': None,
        'grant_type': None,
        'redirect_uri': None,
        'refresh_token': None,
        'request_token': None,
        'response_type': None,
        'scope': None,
        'scopes': None,
        'state': None,
        'token': None,
        'user': None,
        'token_type_hint': None,

        # OpenID Connect
        'response_mode': None,
        'nonce': None,
        'display': None,
        'prompt': None,
        'claims': None,
        'max_age': None,
        'ui_locales': None,
        'id_token_hint': None,
        'login_hint': None,
        'acr_values': None
    }
    self._params.update(dict(urldecode(self.uri_query)))
    self._params.update(dict(self.decoded_body or []))

  def __getattr__(self, name):
    if name in self._params:
      return self._params[name]
    else:
      raise AttributeError(name)

  def __repr__(self):
    body = self.body
    headers = self.headers.copy()
    if body:
      body = SANITIZE_PATTERN.sub('\1<SANITIZED>', str(body))
    if 'Authorization' in headers:
      headers['Authorization'] = '<SANITIZED>'
    return ('<oauthlib.Request url="%s", http_method="%s", headers="%s", '
            'body="%s">') % (
        self.uri, self.http_method, headers, body)

  @property
  def uri_query(self):
    return urlparse.urlparse(self.uri).query

  @property
  def uri_query_params(self):
    if not self.uri_query:
      return []
    return urlparse.parse_qsl(
        self.uri_query, keep_blank_values=True, strict_parsing=True)

  @property
  def duplicate_params(self):
    seen_keys = collections.defaultdict(int)
    all_keys = (p[0] for p in (self.decoded_body or []) + self.uri_query_params)
    for k in all_keys:
      seen_keys[k] += 1
    return [k for k, c in seen_keys.items() if c > 1]
