#!/usr/bin/env python
#
# Copyright 2015 Google Inc.
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

"""Base class for api services."""

import base64
import contextlib
import datetime
import logging
import pprint


import six
from six.moves import http_client
from six.moves import urllib


from apitools.base.protorpclite import message_types
from apitools.base.protorpclite import messages
from apitools.base.py import encoding
from apitools.base.py import exceptions
from apitools.base.py import http_wrapper
from apitools.base.py import util

__all__ = [
    'ApiMethodInfo',
    'ApiUploadInfo',
    'BaseApiClient',
    'BaseApiService',
    'NormalizeApiEndpoint',
]

# TODO(user): Remove this once we quiet the spurious logging in
# oauth2client (or drop oauth2client).
logging.getLogger('oauth2client.util').setLevel(logging.ERROR)

_MAX_URL_LENGTH = 2048


class ApiUploadInfo(messages.Message):

    """Media upload information for a method.

    Fields:
      accept: (repeated) MIME Media Ranges for acceptable media uploads
          to this method.
      max_size: (integer) Maximum size of a media upload, such as 3MB
          or 1TB (converted to an integer).
      resumable_path: Path to use for resumable uploads.
      resumable_multipart: (boolean) Whether or not the resumable endpoint
          supports multipart uploads.
      simple_path: Path to use for simple uploads.
      simple_multipart: (boolean) Whether or not the simple endpoint
          supports multipart uploads.
    """
    accept = messages.StringField(1, repeated=True)
    max_size = messages.IntegerField(2)
    resumable_path = messages.StringField(3)
    resumable_multipart = messages.BooleanField(4)
    simple_path = messages.StringField(5)
    simple_multipart = messages.BooleanField(6)


class ApiMethodInfo(messages.Message):

    """Configuration info for an API method.

    All fields are strings unless noted otherwise.

    Fields:
      relative_path: Relative path for this method.
      flat_path: Expanded version (if any) of relative_path.
      method_id: ID for this method.
      http_method: HTTP verb to use for this method.
      path_params: (repeated) path parameters for this method.
      query_params: (repeated) query parameters for this method.
      ordered_params: (repeated) ordered list of parameters for
          this method.
      description: description of this method.
      request_type_name: name of the request type.
      response_type_name: name of the response type.
      request_field: if not null, the field to pass as the body
          of this POST request. may also be the REQUEST_IS_BODY
          value below to indicate the whole message is the body.
      upload_config: (ApiUploadInfo) Information about the upload
          configuration supported by this method.
      supports_download: (boolean) If True, this method supports
          downloading the request via the `alt=media` query
          parameter.
    """

    relative_path = messages.StringField(1)
    flat_path = messages.StringField(2)
    method_id = messages.StringField(3)
    http_method = messages.StringField(4)
    path_params = messages.StringField(5, repeated=True)
    query_params = messages.StringField(6, repeated=True)
    ordered_params = messages.StringField(7, repeated=True)
    description = messages.StringField(8)
    request_type_name = messages.StringField(9)
    response_type_name = messages.StringField(10)
    request_field = messages.StringField(11, default='')
    upload_config = messages.MessageField(ApiUploadInfo, 12)
    supports_download = messages.BooleanField(13, default=False)


REQUEST_IS_BODY = '<request>'


def _LoadClass(name, messages_module):
    if name.startswith('message_types.'):
        _, _, classname = name.partition('.')
        return getattr(message_types, classname)
    elif '.' not in name:
        return getattr(messages_module, name)
    else:
        raise exceptions.GeneratedClientError('Unknown class %s' % name)


def _RequireClassAttrs(obj, attrs):
    for attr in attrs:
        attr_name = attr.upper()
        if not hasattr(obj, '%s' % attr_name) or not getattr(obj, attr_name):
            msg = 'No %s specified for object of class %s.' % (
                attr_name, type(obj).__name__)
            raise exceptions.GeneratedClientError(msg)


def NormalizeApiEndpoint(api_endpoint):
    if not api_endpoint.endswith('/'):
        api_endpoint += '/'
    return api_endpoint


def _urljoin(base, url):  # pylint: disable=invalid-name
    """Custom urljoin replacement supporting : before / in url."""
    # In general, it's unsafe to simply join base and url. However, for
    # the case of discovery documents, we know:
    #  * base will never contain params, query, or fragment
    #  * url will never contain a scheme or net_loc.
    # In general, this means we can safely join on /; we just need to
    # ensure we end up with precisely one / joining base and url. The
    # exception here is the case of media uploads, where url will be an
    # absolute url.
    if url.startswith('http://') or url.startswith('https://'):
        return urllib.parse.urljoin(base, url)
    new_base = base if base.endswith('/') else base + '/'
    new_url = url[1:] if url.startswith('/') else url
    return new_base + new_url


class _UrlBuilder(object):

    """Convenient container for url data."""

    def __init__(self, base_url, relative_path=None, query_params=None):
        components = urllib.parse.urlsplit(_urljoin(
            base_url, relative_path or ''))
        if components.fragment:
            raise exceptions.ConfigurationValueError(
                'Unexpected url fragment: %s' % components.fragment)
        self.query_params = urllib.parse.parse_qs(components.query or '')
        if query_params is not None:
            self.query_params.update(query_params)
        self.__scheme = components.scheme
        self.__netloc = components.netloc
        self.relative_path = components.path or ''

    @classmethod
    def FromUrl(cls, url):
        urlparts = urllib.parse.urlsplit(url)
        query_params = urllib.parse.parse_qs(urlparts.query)
        base_url = urllib.parse.urlunsplit((
            urlparts.scheme, urlparts.netloc, '', None, None))
        relative_path = urlparts.path or ''
        return cls(
            base_url, relative_path=relative_path, query_params=query_params)

    @property
    def base_url(self):
        return urllib.parse.urlunsplit(
            (self.__scheme, self.__netloc, '', '', ''))

    @base_url.setter
    def base_url(self, value):
        components = urllib.parse.urlsplit(value)
        if components.path or components.query or components.fragment:
            raise exceptions.ConfigurationValueError(
                'Invalid base url: %s' % value)
        self.__scheme = components.scheme
        self.__netloc = components.netloc

    @property
    def query(self):
        # TODO(user): In the case that some of the query params are
        # non-ASCII, we may silently fail to encode correctly. We should
        # figure out who is responsible for owning the object -> str
        # conversion.
        return urllib.parse.urlencode(self.query_params, True)

    @property
    def url(self):
        if '{' in self.relative_path or '}' in self.relative_path:
            raise exceptions.ConfigurationValueError(
                'Cannot create url with relative path %s' % self.relative_path)
        return urllib.parse.urlunsplit((
            self.__scheme, self.__netloc, self.relative_path, self.query, ''))


def _SkipGetCredentials():
    """Hook for skipping credentials. For internal use."""
    return False


class BaseApiClient(object):

    """Base class for client libraries."""
    MESSAGES_MODULE = None

    _API_KEY = ''
    _CLIENT_ID = ''
    _CLIENT_SECRET = ''
    _PACKAGE = ''
    _SCOPES = []
    _USER_AGENT = ''

    def __init__(self, url, credentials=None, get_credentials=True, http=None,
                 model=None, log_request=False, log_response=False,
                 num_retries=5, max_retry_wait=60, credentials_args=None,
                 default_global_params=None, additional_http_headers=None,
                 check_response_func=None, retry_func=None,
                 response_encoding=None):
        _RequireClassAttrs(self, ('_package', '_scopes', 'messages_module'))
        if default_global_params is not None:
            util.Typecheck(default_global_params, self.params_type)
        self.__default_global_params = default_global_params
        self.log_request = log_request
        self.log_response = log_response
        self.__num_retries = 5
        self.__max_retry_wait = 60
        # We let the @property machinery below do our validation.
        self.num_retries = num_retries
        self.max_retry_wait = max_retry_wait
        self._credentials = credentials
        get_credentials = get_credentials and not _SkipGetCredentials()
        if get_credentials and not credentials:
            credentials_args = credentials_args or {}
            self._SetCredentials(**credentials_args)
        self._url = NormalizeApiEndpoint(url)
        self._http = http or http_wrapper.GetHttp()
        # Note that "no credentials" is totally possible.
        if self._credentials is not None:
            self._http = self._credentials.authorize(self._http)
        # TODO(user): Remove this field when we switch to proto2.
        self.__include_fields = None

        self.additional_http_headers = additional_http_headers or {}
        self.check_response_func = check_response_func
        self.retry_func = retry_func
        self.response_encoding = response_encoding
        # Since we can't change the init arguments without regenerating clients,
        # offer this hook to affect FinalizeTransferUrl behavior.
        self.overwrite_transfer_urls_with_client_base = False

        # TODO(user): Finish deprecating these fields.
        _ = model

        self.__response_type_model = 'proto'

    def _SetCredentials(self, **kwds):
        """Fetch credentials, and set them for this client.

        Note that we can't simply return credentials, since creating them
        may involve side-effecting self.

        Args:
          **kwds: Additional keyword arguments are passed on to GetCredentials.

        Returns:
          None. Sets self._credentials.
        """
        args = {
            'api_key': self._API_KEY,
            'client': self,
            'client_id': self._CLIENT_ID,
            'client_secret': self._CLIENT_SECRET,
            'package_name': self._PACKAGE,
            'scopes': self._SCOPES,
            'user_agent': self._USER_AGENT,
        }
        args.update(kwds)
        # credentials_lib can be expensive to import so do it only if needed.
        from apitools.base.py import credentials_lib
        # TODO(user): It's a bit dangerous to pass this
        # still-half-initialized self into this method, but we might need
        # to set attributes on it associated with our credentials.
        # Consider another way around this (maybe a callback?) and whether
        # or not it's worth it.
        self._credentials = credentials_lib.GetCredentials(**args)

    @classmethod
    def ClientInfo(cls):
        return {
            'client_id': cls._CLIENT_ID,
            'client_secret': cls._CLIENT_SECRET,
            'scope': ' '.join(sorted(util.NormalizeScopes(cls._SCOPES))),
            'user_agent': cls._USER_AGENT,
        }

    @property
    def base_model_class(self):
        return None

    @property
    def http(self):
        return self._http

    @property
    def url(self):
        return self._url

    @classmethod
    def GetScopes(cls):
        return cls._SCOPES

    @property
    def params_type(self):
        return _LoadClass('StandardQueryParameters', self.MESSAGES_MODULE)

    @property
    def user_agent(self):
        return self._USER_AGENT

    @property
    def _default_global_params(self):
        if self.__default_global_params is None:
            # pylint: disable=not-callable
            self.__default_global_params = self.params_type()
        return self.__default_global_params

    def AddGlobalParam(self, name, value):
        params = self._default_global_params
        setattr(params, name, value)

    @property
    def global_params(self):
        return encoding.CopyProtoMessage(self._default_global_params)

    @contextlib.contextmanager
    def IncludeFields(self, include_fields):
        self.__include_fields = include_fields
        yield
        self.__include_fields = None

    @property
    def response_type_model(self):
        return self.__response_type_model

    @contextlib.contextmanager
    def JsonResponseModel(self):
        """In this context, return raw JSON instead of proto."""
        old_model = self.response_type_model
        self.__response_type_model = 'json'
        yield
        self.__response_type_model = old_model

    @property
    def num_retries(self):
        return self.__num_retries

    @num_retries.setter
    def num_retries(self, value):
        util.Typecheck(value, six.integer_types)
        if value < 0:
            raise exceptions.InvalidDataError(
                'Cannot have negative value for num_retries')
        self.__num_retries = value

    @property
    def max_retry_wait(self):
        return self.__max_retry_wait

    @max_retry_wait.setter
    def max_retry_wait(self, value):
        util.Typecheck(value, six.integer_types)
        if value <= 0:
            raise exceptions.InvalidDataError(
                'max_retry_wait must be a postiive integer')
        self.__max_retry_wait = value

    @contextlib.contextmanager
    def WithRetries(self, num_retries):
        old_num_retries = self.num_retries
        self.num_retries = num_retries
        yield
        self.num_retries = old_num_retries

    def ProcessRequest(self, method_config, request):
        """Hook for pre-processing of requests."""
        if self.log_request:
            logging.info(
                'Calling method %s with %s: %s', method_config.method_id,
                method_config.request_type_name, request)
        return request

    def ProcessHttpRequest(self, http_request):
        """Hook for pre-processing of http requests."""
        http_request.headers.update(self.additional_http_headers)
        if self.log_request:
            logging.info('Making http %s to %s',
                         http_request.http_method, http_request.url)
            logging.info('Headers: %s', pprint.pformat(http_request.headers))
            if http_request.body:
                # TODO(user): Make this safe to print in the case of
                # non-printable body characters.
                logging.info('Body:\n%s',
                             http_request.loggable_body or http_request.body)
            else:
                logging.info('Body: (none)')
        return http_request

    def ProcessResponse(self, method_config, response):
        if self.log_response:
            logging.info('Response of type %s: %s',
                         method_config.response_type_name, response)
        return response

    # TODO(user): Decide where these two functions should live.
    def SerializeMessage(self, message):
        return encoding.MessageToJson(
            message, include_fields=self.__include_fields)

    def DeserializeMessage(self, response_type, data):
        """Deserialize the given data as method_config.response_type."""
        try:
            message = encoding.JsonToMessage(response_type, data)
        except (exceptions.InvalidDataFromServerError,
                messages.ValidationError, ValueError) as e:
            raise exceptions.InvalidDataFromServerError(
                'Error decoding response "%s" as type %s: %s' % (
                    data, response_type.__name__, e))
        return message

    def FinalizeTransferUrl(self, url):
        """Modify the url for a given transfer, based on auth and version."""
        url_builder = _UrlBuilder.FromUrl(url)
        if getattr(self.global_params, 'key', None):
            url_builder.query_params['key'] = self.global_params.key
        if self.overwrite_transfer_urls_with_client_base:
            client_url_builder = _UrlBuilder.FromUrl(self._url)
            url_builder.base_url = client_url_builder.base_url
        return url_builder.url


class BaseApiService(object):

    """Base class for generated API services."""

    def __init__(self, client):
        self.__client = client
        self._method_configs = {}
        self._upload_configs = {}

    @property
    def _client(self):
        return self.__client

    @property
    def client(self):
        return self.__client

    def GetMethodConfig(self, method):
        """Returns service cached method config for given method."""
        method_config = self._method_configs.get(method)
        if method_config:
            return method_config
        func = getattr(self, method, None)
        if func is None:
            raise KeyError(method)
        method_config = getattr(func, 'method_config', None)
        if method_config is None:
            raise KeyError(method)
        self._method_configs[method] = config = method_config()
        return config

    @classmethod
    def GetMethodsList(cls):
        return [f.__name__ for f in six.itervalues(cls.__dict__)
                if getattr(f, 'method_config', None)]

    def GetUploadConfig(self, method):
        return self._upload_configs.get(method)

    def GetRequestType(self, method):
        method_config = self.GetMethodConfig(method)
        return getattr(self.client.MESSAGES_MODULE,
                       method_config.request_type_name)

    def GetResponseType(self, method):
        method_config = self.GetMethodConfig(method)
        return getattr(self.client.MESSAGES_MODULE,
                       method_config.response_type_name)

    def __CombineGlobalParams(self, global_params, default_params):
        """Combine the given params with the defaults."""
        util.Typecheck(global_params, (type(None), self.__client.params_type))
        result = self.__client.params_type()
        global_params = global_params or self.__client.params_type()
        for field in result.all_fields():
            value = global_params.get_assigned_value(field.name)
            if value is None:
                value = default_params.get_assigned_value(field.name)
            if value not in (None, [], ()):
                setattr(result, field.name, value)
        return result

    def __EncodePrettyPrint(self, query_info):
        # The prettyPrint flag needs custom encoding: it should be encoded
        # as 0 if False, and ignored otherwise (True is the default).
        if not query_info.pop('prettyPrint', True):
            query_info['prettyPrint'] = 0
        # The One Platform equivalent of prettyPrint is pp, which also needs
        # custom encoding.
        if not query_info.pop('pp', True):
            query_info['pp'] = 0
        return query_info

    def __FinalUrlValue(self, value, field):
        """Encode value for the URL, using field to skip encoding for bytes."""
        if isinstance(field, messages.BytesField) and value is not None:
            return base64.urlsafe_b64encode(value)
        elif isinstance(value, six.text_type):
            return value.encode('utf8')
        elif isinstance(value, six.binary_type):
            return value.decode('utf8')
        elif isinstance(value, datetime.datetime):
            return value.isoformat()
        return value

    def __ConstructQueryParams(self, query_params, request, global_params):
        """Construct a dictionary of query parameters for this request."""
        # First, handle the global params.
        global_params = self.__CombineGlobalParams(
            global_params, self.__client.global_params)
        global_param_names = util.MapParamNames(
            [x.name for x in self.__client.params_type.all_fields()],
            self.__client.params_type)
        global_params_type = type(global_params)
        query_info = dict(
            (param,
             self.__FinalUrlValue(getattr(global_params, param),
                                  getattr(global_params_type, param)))
            for param in global_param_names)
        # Next, add the query params.
        query_param_names = util.MapParamNames(query_params, type(request))
        request_type = type(request)
        query_info.update(
            (param,
             self.__FinalUrlValue(getattr(request, param, None),
                                  getattr(request_type, param)))
            for param in query_param_names)
        query_info = dict((k, v) for k, v in query_info.items()
                          if v is not None)
        query_info = self.__EncodePrettyPrint(query_info)
        query_info = util.MapRequestParams(query_info, type(request))
        return query_info

    def __ConstructRelativePath(self, method_config, request,
                                relative_path=None):
        """Determine the relative path for request."""
        python_param_names = util.MapParamNames(
            method_config.path_params, type(request))
        params = dict([(param, getattr(request, param, None))
                       for param in python_param_names])
        params = util.MapRequestParams(params, type(request))
        return util.ExpandRelativePath(method_config, params,
                                       relative_path=relative_path)

    def __FinalizeRequest(self, http_request, url_builder):
        """Make any final general adjustments to the request."""
        if (http_request.http_method == 'GET' and
                len(http_request.url) > _MAX_URL_LENGTH):
            http_request.http_method = 'POST'
            http_request.headers['x-http-method-override'] = 'GET'
            http_request.headers[
                'content-type'] = 'application/x-www-form-urlencoded'
            http_request.body = url_builder.query
            url_builder.query_params = {}
        http_request.url = url_builder.url

    def __ProcessHttpResponse(self, method_config, http_response, request):
        """Process the given http response."""
        if http_response.status_code not in (http_client.OK,
                                             http_client.CREATED,
                                             http_client.NO_CONTENT):
            raise exceptions.HttpError.FromResponse(
                http_response, method_config=method_config, request=request)
        if http_response.status_code == http_client.NO_CONTENT:
            # TODO(user): Find out why _replace doesn't seem to work
            # here.
            http_response = http_wrapper.Response(
                info=http_response.info, content='{}',
                request_url=http_response.request_url)

        content = http_response.content
        if self._client.response_encoding and isinstance(content, bytes):
            content = content.decode(self._client.response_encoding)

        if self.__client.response_type_model == 'json':
            return content
        response_type = _LoadClass(method_config.response_type_name,
                                   self.__client.MESSAGES_MODULE)
        return self.__client.DeserializeMessage(response_type, content)

    def __SetBaseHeaders(self, http_request, client):
        """Fill in the basic headers on http_request."""
        # TODO(user): Make the default a little better here, and
        # include the apitools version.
        user_agent = client.user_agent or 'apitools-client/1.0'
        http_request.headers['user-agent'] = user_agent
        http_request.headers['accept'] = 'application/json'
        http_request.headers['accept-encoding'] = 'gzip, deflate'

    def __SetBody(self, http_request, method_config, request, upload):
        """Fill in the body on http_request."""
        if not method_config.request_field:
            return

        request_type = _LoadClass(
            method_config.request_type_name, self.__client.MESSAGES_MODULE)
        if method_config.request_field == REQUEST_IS_BODY:
            body_value = request
            body_type = request_type
        else:
            body_value = getattr(request, method_config.request_field)
            body_field = request_type.field_by_name(
                method_config.request_field)
            util.Typecheck(body_field, messages.MessageField)
            body_type = body_field.type

        # If there was no body provided, we use an empty message of the
        # appropriate type.
        body_value = body_value or body_type()
        if upload and not body_value:
            # We're going to fill in the body later.
            return
        util.Typecheck(body_value, body_type)
        http_request.headers['content-type'] = 'application/json'
        http_request.body = self.__client.SerializeMessage(body_value)

    def PrepareHttpRequest(self, method_config, request, global_params=None,
                           upload=None, upload_config=None, download=None):
        """Prepares an HTTP request to be sent."""
        request_type = _LoadClass(
            method_config.request_type_name, self.__client.MESSAGES_MODULE)
        util.Typecheck(request, request_type)
        request = self.__client.ProcessRequest(method_config, request)

        http_request = http_wrapper.Request(
            http_method=method_config.http_method)
        self.__SetBaseHeaders(http_request, self.__client)
        self.__SetBody(http_request, method_config, request, upload)

        url_builder = _UrlBuilder(
            self.__client.url, relative_path=method_config.relative_path)
        url_builder.query_params = self.__ConstructQueryParams(
            method_config.query_params, request, global_params)

        # It's important that upload and download go before we fill in the
        # relative path, so that they can replace it.
        if upload is not None:
            upload.ConfigureRequest(upload_config, http_request, url_builder)
        if download is not None:
            download.ConfigureRequest(http_request, url_builder)

        url_builder.relative_path = self.__ConstructRelativePath(
            method_config, request, relative_path=url_builder.relative_path)
        self.__FinalizeRequest(http_request, url_builder)

        return self.__client.ProcessHttpRequest(http_request)

    def _RunMethod(self, method_config, request, global_params=None,
                   upload=None, upload_config=None, download=None):
        """Call this method with request."""
        if upload is not None and download is not None:
            # TODO(user): This just involves refactoring the logic
            # below into callbacks that we can pass around; in particular,
            # the order should be that the upload gets the initial request,
            # and then passes its reply to a download if one exists, and
            # then that goes to ProcessResponse and is returned.
            raise exceptions.NotYetImplementedError(
                'Cannot yet use both upload and download at once')

        http_request = self.PrepareHttpRequest(
            method_config, request, global_params, upload, upload_config,
            download)

        # TODO(user): Make num_retries customizable on Transfer
        # objects, and pass in self.__client.num_retries when initializing
        # an upload or download.
        if download is not None:
            download.InitializeDownload(http_request, client=self.client)
            return

        http_response = None
        if upload is not None:
            http_response = upload.InitializeUpload(
                http_request, client=self.client)
        if http_response is None:
            http = self.__client.http
            if upload and upload.bytes_http:
                http = upload.bytes_http
            opts = {
                'retries': self.__client.num_retries,
                'max_retry_wait': self.__client.max_retry_wait,
            }
            if self.__client.check_response_func:
                opts['check_response_func'] = self.__client.check_response_func
            if self.__client.retry_func:
                opts['retry_func'] = self.__client.retry_func
            http_response = http_wrapper.MakeRequest(
                http, http_request, **opts)

        return self.ProcessHttpResponse(method_config, http_response, request)

    def ProcessHttpResponse(self, method_config, http_response, request=None):
        """Convert an HTTP response to the expected message type."""
        return self.__client.ProcessResponse(
            method_config,
            self.__ProcessHttpResponse(method_config, http_response, request))
