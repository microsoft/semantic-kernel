# Copyright 2015 Google Inc.  All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Utilities for the Django web framework.

Provides Django views and helpers the make using the OAuth2 web server
flow easier. It includes an ``oauth_required`` decorator to automatically
ensure that user credentials are available, and an ``oauth_enabled`` decorator
to check if the user has authorized, and helper shortcuts to create the
authorization URL otherwise.

There are two basic use cases supported. The first is using Google OAuth as the
primary form of authentication, which is the simpler approach recommended
for applications without their own user system.

The second use case is adding Google OAuth credentials to an
existing Django model containing a Django user field. Most of the
configuration is the same, except for `GOOGLE_OAUTH_MODEL_STORAGE` in
settings.py. See "Adding Credentials To An Existing Django User System" for
usage differences.

Only Django versions 1.8+ are supported.

Configuration
===============

To configure, you'll need a set of OAuth2 web application credentials from
`Google Developer's Console <https://console.developers.google.com/project/_/apiui/credential>`.

Add the helper to your INSTALLED_APPS:

.. code-block:: python
   :caption: settings.py
   :name: installed_apps

    INSTALLED_APPS = (
        # other apps
        "django.contrib.sessions.middleware"
        "oauth2client.contrib.django_util"
    )

This helper also requires the Django Session Middleware, so
``django.contrib.sessions.middleware`` should be in INSTALLED_APPS as well.
MIDDLEWARE or MIDDLEWARE_CLASSES (in Django  versions <1.10) should also
contain the string 'django.contrib.sessions.middleware.SessionMiddleware'.


Add the client secrets created earlier to the settings. You can either
specify the path to the credentials file in JSON format

.. code-block:: python
   :caption:  settings.py
   :name: secrets_file

   GOOGLE_OAUTH2_CLIENT_SECRETS_JSON=/path/to/client-secret.json

Or, directly configure the client Id and client secret.


.. code-block:: python
   :caption: settings.py
   :name: secrets_config

   GOOGLE_OAUTH2_CLIENT_ID=client-id-field
   GOOGLE_OAUTH2_CLIENT_SECRET=client-secret-field

By default, the default scopes for the required decorator only contains the
``email`` scopes. You can change that default in the settings.

.. code-block:: python
   :caption: settings.py
   :name: scopes

   GOOGLE_OAUTH2_SCOPES = ('email', 'https://www.googleapis.com/auth/calendar',)

By default, the decorators will add an `oauth` object to the Django request
object, and include all of its state and helpers inside that object. If the
`oauth` name conflicts with another usage, it can be changed

.. code-block:: python
   :caption: settings.py
   :name: request_prefix

   # changes request.oauth to request.google_oauth
   GOOGLE_OAUTH2_REQUEST_ATTRIBUTE = 'google_oauth'

Add the oauth2 routes to your application's urls.py urlpatterns.

.. code-block:: python
   :caption: urls.py
   :name: urls

   from oauth2client.contrib.django_util.site import urls as oauth2_urls

   urlpatterns += [url(r'^oauth2/', include(oauth2_urls))]

To require OAuth2 credentials for a view, use the `oauth2_required` decorator.
This creates a credentials object with an id_token, and allows you to create
an `http` object to build service clients with. These are all attached to the
request.oauth

.. code-block:: python
   :caption: views.py
   :name: views_required

   from oauth2client.contrib.django_util.decorators import oauth_required

   @oauth_required
   def requires_default_scopes(request):
      email = request.oauth.credentials.id_token['email']
      service = build(serviceName='calendar', version='v3',
                    http=request.oauth.http,
                   developerKey=API_KEY)
      events = service.events().list(calendarId='primary').execute()['items']
      return HttpResponse("email: {0} , calendar: {1}".format(
                           email,str(events)))
      return HttpResponse(
          "email: {0} , calendar: {1}".format(email, str(events)))

To make OAuth2 optional and provide an authorization link in your own views.

.. code-block:: python
   :caption: views.py
   :name: views_enabled2

   from oauth2client.contrib.django_util.decorators import oauth_enabled

   @oauth_enabled
   def optional_oauth2(request):
       if request.oauth.has_credentials():
           # this could be passed into a view
           # request.oauth.http is also initialized
           return HttpResponse("User email: {0}".format(
               request.oauth.credentials.id_token['email']))
       else:
           return HttpResponse(
               'Here is an OAuth Authorize link: <a href="{0}">Authorize'
               '</a>'.format(request.oauth.get_authorize_redirect()))

If a view needs a scope not included in the default scopes specified in
the settings, you can use [incremental auth](https://developers.google.com/identity/sign-in/web/incremental-auth)
and specify additional scopes in the decorator arguments.

.. code-block:: python
   :caption: views.py
   :name: views_required_additional_scopes

   @oauth_enabled(scopes=['https://www.googleapis.com/auth/drive'])
   def drive_required(request):
       if request.oauth.has_credentials():
           service = build(serviceName='drive', version='v2',
                http=request.oauth.http,
                developerKey=API_KEY)
           events = service.files().list().execute()['items']
           return HttpResponse(str(events))
       else:
           return HttpResponse(
               'Here is an OAuth Authorize link: <a href="{0}">Authorize'
               '</a>'.format(request.oauth.get_authorize_redirect()))


To provide a callback on authorization being completed, use the
oauth2_authorized signal:

.. code-block:: python
   :caption: views.py
   :name: signals

   from oauth2client.contrib.django_util.signals import oauth2_authorized

   def test_callback(sender, request, credentials, **kwargs):
       print("Authorization Signal Received {0}".format(
               credentials.id_token['email']))

   oauth2_authorized.connect(test_callback)

Adding Credentials To An Existing Django User System
=====================================================

As an alternative to storing the credentials in the session, the helper
can be configured to store the fields on a Django model. This might be useful
if you need to use the credentials outside the context of a user request. It
also prevents the need for a logged in user to repeat the OAuth flow when
starting a new session.

To use, change ``settings.py``

.. code-block:: python
   :caption:  settings.py
   :name: storage_model_config

   GOOGLE_OAUTH2_STORAGE_MODEL = {
       'model': 'path.to.model.MyModel',
       'user_property': 'user_id',
       'credentials_property': 'credential'
    }

Where ``path.to.model`` class is the fully qualified name of a
``django.db.model`` class containing a ``django.contrib.auth.models.User``
field with the name specified by `user_property` and a
:class:`oauth2client.contrib.django_util.models.CredentialsField` with the name
specified by `credentials_property`. For the sample configuration given,
our model would look like

.. code-block:: python
   :caption: models.py
   :name: storage_model_model

   from django.contrib.auth.models import User
   from oauth2client.contrib.django_util.models import CredentialsField

   class MyModel(models.Model):
       #  ... other fields here ...
       user = models.OneToOneField(User)
       credential = CredentialsField()
"""

import importlib

import django.conf
from django.core import exceptions
from django.core import urlresolvers
from six.moves.urllib import parse

from oauth2client import clientsecrets
from oauth2client import transport
from oauth2client.contrib import dictionary_storage
from oauth2client.contrib.django_util import storage

GOOGLE_OAUTH2_DEFAULT_SCOPES = ('email',)
GOOGLE_OAUTH2_REQUEST_ATTRIBUTE = 'oauth'


def _load_client_secrets(filename):
    """Loads client secrets from the given filename.

    Args:
        filename: The name of the file containing the JSON secret key.

    Returns:
        A 2-tuple, the first item containing the client id, and the second
        item containing a client secret.
    """
    client_type, client_info = clientsecrets.loadfile(filename)

    if client_type != clientsecrets.TYPE_WEB:
        raise ValueError(
            'The flow specified in {} is not supported, only the WEB flow '
            'type  is supported.'.format(client_type))
    return client_info['client_id'], client_info['client_secret']


def _get_oauth2_client_id_and_secret(settings_instance):
    """Initializes client id and client secret based on the settings.

    Args:
        settings_instance: An instance of ``django.conf.settings``.

    Returns:
        A 2-tuple, the first item is the client id and the second
         item is the client secret.
    """
    secret_json = getattr(settings_instance,
                          'GOOGLE_OAUTH2_CLIENT_SECRETS_JSON', None)
    if secret_json is not None:
        return _load_client_secrets(secret_json)
    else:
        client_id = getattr(settings_instance, "GOOGLE_OAUTH2_CLIENT_ID",
                            None)
        client_secret = getattr(settings_instance,
                                "GOOGLE_OAUTH2_CLIENT_SECRET", None)
        if client_id is not None and client_secret is not None:
            return client_id, client_secret
        else:
            raise exceptions.ImproperlyConfigured(
                "Must specify either GOOGLE_OAUTH2_CLIENT_SECRETS_JSON, or "
                "both GOOGLE_OAUTH2_CLIENT_ID and "
                "GOOGLE_OAUTH2_CLIENT_SECRET in settings.py")


def _get_storage_model():
    """This configures whether the credentials will be stored in the session
    or the Django ORM based on the settings. By default, the credentials
    will be stored in the session, unless `GOOGLE_OAUTH2_STORAGE_MODEL`
    is found in the settings. Usually, the ORM storage is used to integrate
    credentials into an existing Django user system.

    Returns:
        A tuple containing three strings, or None. If
        ``GOOGLE_OAUTH2_STORAGE_MODEL`` is configured, the tuple
        will contain the fully qualifed path of the `django.db.model`,
        the name of the ``django.contrib.auth.models.User`` field on the
        model, and the name of the
        :class:`oauth2client.contrib.django_util.models.CredentialsField`
        field on the model. If Django ORM storage is not configured,
        this function returns None.
    """
    storage_model_settings = getattr(django.conf.settings,
                                     'GOOGLE_OAUTH2_STORAGE_MODEL', None)
    if storage_model_settings is not None:
        return (storage_model_settings['model'],
                storage_model_settings['user_property'],
                storage_model_settings['credentials_property'])
    else:
        return None, None, None


class OAuth2Settings(object):
    """Initializes Django OAuth2 Helper Settings

    This class loads the OAuth2 Settings from the Django settings, and then
    provides those settings as attributes to the rest of the views and
    decorators in the module.

    Attributes:
      scopes: A list of OAuth2 scopes that the decorators and views will use
              as defaults.
      request_prefix: The name of the attribute that the decorators use to
                    attach the UserOAuth2 object to the Django request object.
      client_id: The OAuth2 Client ID.
      client_secret: The OAuth2 Client Secret.
    """

    def __init__(self, settings_instance):
        self.scopes = getattr(settings_instance, 'GOOGLE_OAUTH2_SCOPES',
                              GOOGLE_OAUTH2_DEFAULT_SCOPES)
        self.request_prefix = getattr(settings_instance,
                                      'GOOGLE_OAUTH2_REQUEST_ATTRIBUTE',
                                      GOOGLE_OAUTH2_REQUEST_ATTRIBUTE)
        info = _get_oauth2_client_id_and_secret(settings_instance)
        self.client_id, self.client_secret = info

        # Django 1.10 deprecated MIDDLEWARE_CLASSES in favor of MIDDLEWARE
        middleware_settings = getattr(settings_instance, 'MIDDLEWARE', None)
        if middleware_settings is None:
            middleware_settings = getattr(
                settings_instance, 'MIDDLEWARE_CLASSES', None)
        if middleware_settings is None:
            raise exceptions.ImproperlyConfigured(
                'Django settings has neither MIDDLEWARE nor MIDDLEWARE_CLASSES'
                'configured')

        if ('django.contrib.sessions.middleware.SessionMiddleware' not in
                middleware_settings):
            raise exceptions.ImproperlyConfigured(
                'The Google OAuth2 Helper requires session middleware to '
                'be installed. Edit your MIDDLEWARE_CLASSES or MIDDLEWARE '
                'setting to include \'django.contrib.sessions.middleware.'
                'SessionMiddleware\'.')
        (self.storage_model, self.storage_model_user_property,
         self.storage_model_credentials_property) = _get_storage_model()


oauth2_settings = OAuth2Settings(django.conf.settings)

_CREDENTIALS_KEY = 'google_oauth2_credentials'


def get_storage(request):
    """ Gets a Credentials storage object provided by the Django OAuth2 Helper
    object.

    Args:
        request: Reference to the current request object.

    Returns:
       An :class:`oauth2.client.Storage` object.
    """
    storage_model = oauth2_settings.storage_model
    user_property = oauth2_settings.storage_model_user_property
    credentials_property = oauth2_settings.storage_model_credentials_property

    if storage_model:
        module_name, class_name = storage_model.rsplit('.', 1)
        module = importlib.import_module(module_name)
        storage_model_class = getattr(module, class_name)
        return storage.DjangoORMStorage(storage_model_class,
                                        user_property,
                                        request.user,
                                        credentials_property)
    else:
        # use session
        return dictionary_storage.DictionaryStorage(
            request.session, key=_CREDENTIALS_KEY)


def _redirect_with_params(url_name, *args, **kwargs):
    """Helper method to create a redirect response with URL params.

    This builds a redirect string that converts kwargs into a
    query string.

    Args:
        url_name: The name of the url to redirect to.
        kwargs: the query string param and their values to build.

    Returns:
        A properly formatted redirect string.
    """
    url = urlresolvers.reverse(url_name, args=args)
    params = parse.urlencode(kwargs, True)
    return "{0}?{1}".format(url, params)


def _credentials_from_request(request):
    """Gets the authorized credentials for this flow, if they exist."""
    # ORM storage requires a logged in user
    if (oauth2_settings.storage_model is None or
            request.user.is_authenticated()):
        return get_storage(request).get()
    else:
        return None


class UserOAuth2(object):
    """Class to create oauth2 objects on Django request objects containing
    credentials and helper methods.
    """

    def __init__(self, request, scopes=None, return_url=None):
        """Initialize the Oauth2 Object.

        Args:
            request: Django request object.
            scopes: Scopes desired for this OAuth2 flow.
            return_url: The url to return to after the OAuth flow is complete,
                 defaults to the request's current URL path.
        """
        self.request = request
        self.return_url = return_url or request.get_full_path()
        if scopes:
            self._scopes = set(oauth2_settings.scopes) | set(scopes)
        else:
            self._scopes = set(oauth2_settings.scopes)

    def get_authorize_redirect(self):
        """Creates a URl to start the OAuth2 authorization flow."""
        get_params = {
            'return_url': self.return_url,
            'scopes': self._get_scopes()
        }

        return _redirect_with_params('google_oauth:authorize', **get_params)

    def has_credentials(self):
        """Returns True if there are valid credentials for the current user
        and required scopes."""
        credentials = _credentials_from_request(self.request)
        return (credentials and not credentials.invalid and
                credentials.has_scopes(self._get_scopes()))

    def _get_scopes(self):
        """Returns the scopes associated with this object, kept up to
         date for incremental auth."""
        if _credentials_from_request(self.request):
            return (self._scopes |
                    _credentials_from_request(self.request).scopes)
        else:
            return self._scopes

    @property
    def scopes(self):
        """Returns the scopes associated with this OAuth2 object."""
        # make sure previously requested custom scopes are maintained
        # in future authorizations
        return self._get_scopes()

    @property
    def credentials(self):
        """Gets the authorized credentials for this flow, if they exist."""
        return _credentials_from_request(self.request)

    @property
    def http(self):
        """Helper: create HTTP client authorized with OAuth2 credentials."""
        if self.has_credentials():
            return self.credentials.authorize(transport.get_http_object())
        return None
