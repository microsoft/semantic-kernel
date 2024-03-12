# Copyright 2015 Google Inc.  All rights reserved.
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

"""This module contains the views used by the OAuth2 flows.

Their are two views used by the OAuth2 flow, the authorize and the callback
view. The authorize view kicks off the three-legged OAuth flow, and the
callback view validates the flow and if successful stores the credentials
in the configured storage."""

import hashlib
import json
import os

from django import http
from django import shortcuts
from django.conf import settings
from django.core import urlresolvers
from django.shortcuts import redirect
from django.utils import html
import jsonpickle
from six.moves.urllib import parse

from oauth2client import client
from oauth2client.contrib import django_util
from oauth2client.contrib.django_util import get_storage
from oauth2client.contrib.django_util import signals

_CSRF_KEY = 'google_oauth2_csrf_token'
_FLOW_KEY = 'google_oauth2_flow_{0}'


def _make_flow(request, scopes, return_url=None):
    """Creates a Web Server Flow

    Args:
        request: A Django request object.
        scopes: the request oauth2 scopes.
        return_url: The URL to return to after the flow is complete. Defaults
            to the path of the current request.

    Returns:
        An OAuth2 flow object that has been stored in the session.
    """
    # Generate a CSRF token to prevent malicious requests.
    csrf_token = hashlib.sha256(os.urandom(1024)).hexdigest()

    request.session[_CSRF_KEY] = csrf_token

    state = json.dumps({
        'csrf_token': csrf_token,
        'return_url': return_url,
    })

    flow = client.OAuth2WebServerFlow(
        client_id=django_util.oauth2_settings.client_id,
        client_secret=django_util.oauth2_settings.client_secret,
        scope=scopes,
        state=state,
        redirect_uri=request.build_absolute_uri(
            urlresolvers.reverse("google_oauth:callback")))

    flow_key = _FLOW_KEY.format(csrf_token)
    request.session[flow_key] = jsonpickle.encode(flow)
    return flow


def _get_flow_for_token(csrf_token, request):
    """ Looks up the flow in session to recover information about requested
    scopes.

    Args:
        csrf_token: The token passed in the callback request that should
            match the one previously generated and stored in the request on the
            initial authorization view.

    Returns:
        The OAuth2 Flow object associated with this flow based on the
        CSRF token.
    """
    flow_pickle = request.session.get(_FLOW_KEY.format(csrf_token), None)
    return None if flow_pickle is None else jsonpickle.decode(flow_pickle)


def oauth2_callback(request):
    """ View that handles the user's return from OAuth2 provider.

    This view verifies the CSRF state and OAuth authorization code, and on
    success stores the credentials obtained in the storage provider,
    and redirects to the return_url specified in the authorize view and
    stored in the session.

    Args:
        request: Django request.

    Returns:
         A redirect response back to the return_url.
    """
    if 'error' in request.GET:
        reason = request.GET.get(
            'error_description', request.GET.get('error', ''))
        reason = html.escape(reason)
        return http.HttpResponseBadRequest(
            'Authorization failed {0}'.format(reason))

    try:
        encoded_state = request.GET['state']
        code = request.GET['code']
    except KeyError:
        return http.HttpResponseBadRequest(
            'Request missing state or authorization code')

    try:
        server_csrf = request.session[_CSRF_KEY]
    except KeyError:
        return http.HttpResponseBadRequest(
            'No existing session for this flow.')

    try:
        state = json.loads(encoded_state)
        client_csrf = state['csrf_token']
        return_url = state['return_url']
    except (ValueError, KeyError):
        return http.HttpResponseBadRequest('Invalid state parameter.')

    if client_csrf != server_csrf:
        return http.HttpResponseBadRequest('Invalid CSRF token.')

    flow = _get_flow_for_token(client_csrf, request)

    if not flow:
        return http.HttpResponseBadRequest('Missing Oauth2 flow.')

    try:
        credentials = flow.step2_exchange(code)
    except client.FlowExchangeError as exchange_error:
        return http.HttpResponseBadRequest(
            'An error has occurred: {0}'.format(exchange_error))

    get_storage(request).put(credentials)

    signals.oauth2_authorized.send(sender=signals.oauth2_authorized,
                                   request=request, credentials=credentials)

    return shortcuts.redirect(return_url)


def oauth2_authorize(request):
    """ View to start the OAuth2 Authorization flow.

     This view starts the OAuth2 authorization flow. If scopes is passed in
     as a  GET URL parameter, it will authorize those scopes, otherwise the
     default scopes specified in settings. The return_url can also be
     specified as a GET parameter, otherwise the referer header will be
     checked, and if that isn't found it will return to the root path.

    Args:
       request: The Django request object.

    Returns:
         A redirect to Google OAuth2 Authorization.
    """
    return_url = request.GET.get('return_url', None)
    if not return_url:
        return_url = request.META.get('HTTP_REFERER', '/')

    scopes = request.GET.getlist('scopes', django_util.oauth2_settings.scopes)
    # Model storage (but not session storage) requires a logged in user
    if django_util.oauth2_settings.storage_model:
        if not request.user.is_authenticated():
            return redirect('{0}?next={1}'.format(
                settings.LOGIN_URL, parse.quote(request.get_full_path())))
        # This checks for the case where we ended up here because of a logged
        # out user but we had credentials for it in the first place
        else:
            user_oauth = django_util.UserOAuth2(request, scopes, return_url)
            if user_oauth.has_credentials():
                return redirect(return_url)

    flow = _make_flow(request=request, scopes=scopes, return_url=return_url)
    auth_url = flow.step1_get_authorize_url()
    return shortcuts.redirect(auth_url)
