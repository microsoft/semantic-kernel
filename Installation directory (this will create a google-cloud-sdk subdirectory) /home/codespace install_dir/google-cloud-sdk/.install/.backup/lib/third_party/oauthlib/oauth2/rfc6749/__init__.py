# -*- coding: utf-8 -*-
"""oauthlib.oauth2.rfc6749 ~~~~~~~~~~~~~~~~~~~~~~~

This module is an implementation of various logic needed
for consuming and providing OAuth 2.0 RFC6749.
"""
from __future__ import absolute_import, unicode_literals

import functools
import logging

from .errors import TemporarilyUnavailableError, ServerError
from .errors import FatalClientError, OAuth2Error

log = logging.getLogger(__name__)


class BaseEndpoint(object):

  def __init__(self):
    self._available = True
    self._catch_errors = False

  @property
  def available(self):
    return self._available

  @available.setter
  def available(self, available):
    self._available = available

  @property
  def catch_errors(self):
    return self._catch_errors

  @catch_errors.setter
  def catch_errors(self, catch_errors):
    self._catch_errors = catch_errors


def catch_errors_and_unavailability(f):

  @functools.wraps(f)
  def wrapper(endpoint, uri, *args, **kwargs):
    if not endpoint.available:
      e = TemporarilyUnavailableError()
      log.info('Endpoint unavailable, ignoring request %s.' % uri)
      return {}, e.json, 503

    if endpoint.catch_errors:
      try:
        return f(endpoint, uri, *args, **kwargs)
      except OAuth2Error:
        raise
      except FatalClientError:
        raise
      except Exception as e:
        error = ServerError()
        log.warning('Exception caught while processing request, %s.' % e)
        return {}, error.json, 500
    else:
      return f(endpoint, uri, *args, **kwargs)

  return wrapper
