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

"""Service registry for apitools."""

import collections
import logging
import re
import textwrap

from apitools.base.py import base_api
from apitools.gen import util

# We're a code generator. I don't care.
# pylint:disable=too-many-statements

_MIME_PATTERN_RE = re.compile(r'(?i)[a-z0-9_*-]+/[a-z0-9_*-]+')


class ServiceRegistry(object):

    """Registry for service types."""

    def __init__(self, client_info, message_registry,
                 names, root_package, base_files_package,
                 unelidable_request_methods):
        self.__client_info = client_info
        self.__package = client_info.package
        self.__names = names
        self.__service_method_info_map = collections.OrderedDict()
        self.__message_registry = message_registry
        self.__root_package = root_package
        self.__base_files_package = base_files_package
        self.__unelidable_request_methods = unelidable_request_methods
        self.__all_scopes = set(self.__client_info.scopes)

    def Validate(self):
        self.__message_registry.Validate()

    @property
    def scopes(self):
        return sorted(list(self.__all_scopes))

    def __GetServiceClassName(self, service_name):
        return self.__names.ClassName(
            '%sService' % self.__names.ClassName(service_name))

    def __PrintDocstring(self, printer, method_info, method_name, name):
        """Print a docstring for a service method."""
        if method_info.description:
            description = util.CleanDescription(method_info.description)
            first_line, newline, remaining = method_info.description.partition(
                '\n')
            if not first_line.endswith('.'):
                first_line = '%s.' % first_line
            description = '%s%s%s' % (first_line, newline, remaining)
        else:
            description = '%s method for the %s service.' % (method_name, name)
        with printer.CommentContext():
            printer('r"""%s' % description)
        printer()
        printer('Args:')
        printer('  request: (%s) input message', method_info.request_type_name)
        printer('  global_params: (StandardQueryParameters, default: None) '
                'global arguments')
        if method_info.upload_config:
            printer('  upload: (Upload, default: None) If present, upload')
            printer('      this stream with the request.')
        if method_info.supports_download:
            printer(
                '  download: (Download, default: None) If present, download')
            printer('      data from the request via this stream.')
        printer('Returns:')
        printer('  (%s) The response message.', method_info.response_type_name)
        printer('"""')

    def __WriteSingleService(
            self, printer, name, method_info_map, client_class_name):
        printer()
        class_name = self.__GetServiceClassName(name)
        printer('class %s(base_api.BaseApiService):', class_name)
        with printer.Indent():
            printer('"""Service class for the %s resource."""', name)
            printer()
            printer('_NAME = %s', repr(name))

            # Print the configs for the methods first.
            printer()
            printer('def __init__(self, client):')
            with printer.Indent():
                printer('super(%s.%s, self).__init__(client)',
                        client_class_name, class_name)
                printer('self._upload_configs = {')
                with printer.Indent(indent='    '):
                    for method_name, method_info in method_info_map.items():
                        upload_config = method_info.upload_config
                        if upload_config is not None:
                            printer(
                                "'%s': base_api.ApiUploadInfo(", method_name)
                            with printer.Indent(indent='    '):
                                attrs = sorted(
                                    x.name for x in upload_config.all_fields())
                                for attr in attrs:
                                    printer('%s=%r,',
                                            attr, getattr(upload_config, attr))
                            printer('),')
                    printer('}')

            # Now write each method in turn.
            for method_name, method_info in method_info_map.items():
                printer()
                params = ['self', 'request', 'global_params=None']
                if method_info.upload_config:
                    params.append('upload=None')
                if method_info.supports_download:
                    params.append('download=None')
                printer('def %s(%s):', method_name, ', '.join(params))
                with printer.Indent():
                    self.__PrintDocstring(
                        printer, method_info, method_name, name)
                    printer("config = self.GetMethodConfig('%s')", method_name)
                    upload_config = method_info.upload_config
                    if upload_config is not None:
                        printer("upload_config = self.GetUploadConfig('%s')",
                                method_name)
                    arg_lines = [
                        'config, request, global_params=global_params']
                    if method_info.upload_config:
                        arg_lines.append(
                            'upload=upload, upload_config=upload_config')
                    if method_info.supports_download:
                        arg_lines.append('download=download')
                    printer('return self._RunMethod(')
                    with printer.Indent(indent='    '):
                        for line in arg_lines[:-1]:
                            printer('%s,', line)
                        printer('%s)', arg_lines[-1])
                printer()
                printer('{0}.method_config = lambda: base_api.ApiMethodInfo('
                        .format(method_name))
                with printer.Indent(indent='    '):
                    method_info = method_info_map[method_name]
                    attrs = sorted(
                        x.name for x in method_info.all_fields())
                    for attr in attrs:
                        if attr in ('upload_config', 'description'):
                            continue
                        value = getattr(method_info, attr)
                        if value is not None:
                            printer('%s=%r,', attr, value)
                printer(')')

    def __WriteProtoServiceDeclaration(self, printer, name, method_info_map):
        """Write a single service declaration to a proto file."""
        printer()
        printer('service %s {', self.__GetServiceClassName(name))
        with printer.Indent():
            for method_name, method_info in method_info_map.items():
                for line in textwrap.wrap(method_info.description,
                                          printer.CalculateWidth() - 3):
                    printer('// %s', line)
                printer('rpc %s (%s) returns (%s);',
                        method_name,
                        method_info.request_type_name,
                        method_info.response_type_name)
        printer('}')

    def WriteProtoFile(self, printer):
        """Write the services in this registry to out as proto."""
        self.Validate()
        client_info = self.__client_info
        printer('// Generated services for %s version %s.',
                client_info.package, client_info.version)
        printer()
        printer('syntax = "proto2";')
        printer('package %s;', self.__package)
        printer('import "%s";', client_info.messages_proto_file_name)
        printer()
        for name, method_info_map in self.__service_method_info_map.items():
            self.__WriteProtoServiceDeclaration(printer, name, method_info_map)

    def WriteFile(self, printer):
        """Write the services in this registry to out."""
        self.Validate()
        client_info = self.__client_info
        printer('"""Generated client library for %s version %s."""',
                client_info.package, client_info.version)
        printer('# NOTE: This file is autogenerated and should not be edited '
                'by hand.')
        printer()
        printer('from __future__ import absolute_import')
        printer()
        printer('from %s import base_api', self.__base_files_package)
        if self.__root_package:
            import_prefix = 'from {0} '.format(self.__root_package)
        else:
            import_prefix = ''
        printer('%simport %s as messages', import_prefix,
                client_info.messages_rule_name)
        printer()
        printer()
        printer('class %s(base_api.BaseApiClient):',
                client_info.client_class_name)
        with printer.Indent():
            printer(
                '"""Generated client library for service %s version %s."""',
                client_info.package, client_info.version)
            printer()
            printer('MESSAGES_MODULE = messages')
            printer('BASE_URL = {0!r}'.format(client_info.base_url))
            printer('MTLS_BASE_URL = {0!r}'.format(client_info.mtls_base_url))
            printer()
            printer('_PACKAGE = {0!r}'.format(client_info.package))
            printer('_SCOPES = {0!r}'.format(
                client_info.scopes or
                ['https://www.googleapis.com/auth/userinfo.email']))
            printer('_VERSION = {0!r}'.format(client_info.version))
            printer('_CLIENT_ID = {0!r}'.format(client_info.client_id))
            printer('_CLIENT_SECRET = {0!r}'.format(client_info.client_secret))
            printer('_USER_AGENT = {0!r}'.format(client_info.user_agent))
            printer('_CLIENT_CLASS_NAME = {0!r}'.format(
                client_info.client_class_name))
            printer('_URL_VERSION = {0!r}'.format(client_info.url_version))
            printer('_API_KEY = {0!r}'.format(client_info.api_key))
            printer()
            printer("def __init__(self, url='', credentials=None,")
            with printer.Indent(indent='             '):
                printer('get_credentials=True, http=None, model=None,')
                printer('log_request=False, log_response=False,')
                printer('credentials_args=None, default_global_params=None,')
                printer('additional_http_headers=None, '
                        'response_encoding=None):')
            with printer.Indent():
                printer('"""Create a new %s handle."""', client_info.package)
                printer('url = url or self.BASE_URL')
                printer(
                    'super(%s, self).__init__(', client_info.client_class_name)
                printer('    url, credentials=credentials,')
                printer('    get_credentials=get_credentials, http=http, '
                        'model=model,')
                printer('    log_request=log_request, '
                        'log_response=log_response,')
                printer('    credentials_args=credentials_args,')
                printer('    default_global_params=default_global_params,')
                printer('    additional_http_headers=additional_http_headers,')
                printer('    response_encoding=response_encoding)')
                for name in self.__service_method_info_map.keys():
                    printer('self.%s = self.%s(self)',
                            name, self.__GetServiceClassName(name))
            for name, method_info in self.__service_method_info_map.items():
                self.__WriteSingleService(
                    printer, name, method_info, client_info.client_class_name)

    def __RegisterService(self, service_name, method_info_map):
        if service_name in self.__service_method_info_map:
            raise ValueError(
                'Attempt to re-register descriptor %s' % service_name)
        self.__service_method_info_map[service_name] = method_info_map

    def __CreateRequestType(self, method_description, body_type=None):
        """Create a request type for this method."""
        schema = {}
        schema['id'] = self.__names.ClassName('%sRequest' % (
            self.__names.ClassName(method_description['id'], separator='.'),))
        schema['type'] = 'object'
        schema['properties'] = collections.OrderedDict()
        if 'parameterOrder' not in method_description:
            ordered_parameters = list(method_description.get('parameters', []))
        else:
            ordered_parameters = method_description['parameterOrder'][:]
            for k in method_description['parameters']:
                if k not in ordered_parameters:
                    ordered_parameters.append(k)
        for parameter_name in ordered_parameters:
            field_name = self.__names.CleanName(parameter_name)
            field = dict(method_description['parameters'][parameter_name])
            if 'type' not in field:
                raise ValueError('No type found in parameter %s' % field)
            schema['properties'][field_name] = field
        if body_type is not None:
            body_field_name = self.__GetRequestField(
                method_description, body_type)
            if body_field_name in schema['properties']:
                raise ValueError('Failed to normalize request resource name')
            if 'description' not in body_type:
                body_type['description'] = (
                    'A %s resource to be passed as the request body.' % (
                        self.__GetRequestType(body_type),))
            schema['properties'][body_field_name] = body_type
        self.__message_registry.AddDescriptorFromSchema(schema['id'], schema)
        return schema['id']

    def __CreateVoidResponseType(self, method_description):
        """Create an empty response type."""
        schema = {}
        method_name = self.__names.ClassName(
            method_description['id'], separator='.')
        schema['id'] = self.__names.ClassName('%sResponse' % method_name)
        schema['type'] = 'object'
        schema['description'] = 'An empty %s response.' % method_name
        self.__message_registry.AddDescriptorFromSchema(schema['id'], schema)
        return schema['id']

    def __NeedRequestType(self, method_description, request_type):
        """Determine if this method needs a new request type created."""
        if not request_type:
            return True
        method_id = method_description.get('id', '')
        if method_id in self.__unelidable_request_methods:
            return True
        message = self.__message_registry.LookupDescriptorOrDie(request_type)
        if message is None:
            return True
        field_names = [x.name for x in message.fields]
        parameters = method_description.get('parameters', {})
        for param_name, param_info in parameters.items():
            if (param_info.get('location') != 'path' or
                    self.__names.CleanName(param_name) not in field_names):
                break
        else:
            return False
        return True

    def __MaxSizeToInt(self, max_size):
        """Convert max_size to an int."""
        size_groups = re.match(r'(?P<size>\d+)(?P<unit>.B)?$', max_size)
        if size_groups is None:
            raise ValueError('Could not parse maxSize')
        size, unit = size_groups.group('size', 'unit')
        shift = 0
        if unit is not None:
            unit_dict = {'KB': 10, 'MB': 20, 'GB': 30, 'TB': 40}
            shift = unit_dict.get(unit.upper())
            if shift is None:
                raise ValueError('Unknown unit %s' % unit)
        return int(size) * (1 << shift)

    def __ComputeUploadConfig(self, media_upload_config, method_id):
        """Fill out the upload config for this method."""
        config = base_api.ApiUploadInfo()
        if 'maxSize' in media_upload_config:
            config.max_size = self.__MaxSizeToInt(
                media_upload_config['maxSize'])
        if 'accept' not in media_upload_config:
            logging.warn(
                'No accept types found for upload configuration in '
                'method %s, using */*', method_id)
        config.accept.extend([
            str(a) for a in media_upload_config.get('accept', '*/*')])

        for accept_pattern in config.accept:
            if not _MIME_PATTERN_RE.match(accept_pattern):
                logging.warn('Unexpected MIME type: %s', accept_pattern)
        protocols = media_upload_config.get('protocols', {})
        for protocol in ('simple', 'resumable'):
            media = protocols.get(protocol, {})
            for attr in ('multipart', 'path'):
                if attr in media:
                    setattr(config, '%s_%s' % (protocol, attr), media[attr])
        return config

    def __ComputeMethodInfo(self, method_description, request, response,
                            request_field):
        """Compute the base_api.ApiMethodInfo for this method."""
        relative_path = self.__names.NormalizeRelativePath(
            ''.join((self.__client_info.base_path,
                     method_description['path'])))
        method_id = method_description['id']
        ordered_params = []
        for param_name in method_description.get('parameterOrder', []):
            param_info = method_description['parameters'][param_name]
            if param_info.get('required', False):
                ordered_params.append(param_name)
        method_info = base_api.ApiMethodInfo(
            relative_path=relative_path,
            method_id=method_id,
            http_method=method_description['httpMethod'],
            description=util.CleanDescription(
                method_description.get('description', '')),
            query_params=[],
            path_params=[],
            ordered_params=ordered_params,
            request_type_name=self.__names.ClassName(request),
            response_type_name=self.__names.ClassName(response),
            request_field=request_field,
        )
        flat_path = method_description.get('flatPath', None)
        if flat_path is not None:
            flat_path = self.__names.NormalizeRelativePath(
                self.__client_info.base_path + flat_path)
            if flat_path != relative_path:
                method_info.flat_path = flat_path
        if method_description.get('supportsMediaUpload', False):
            method_info.upload_config = self.__ComputeUploadConfig(
                method_description.get('mediaUpload'), method_id)
        method_info.supports_download = method_description.get(
            'supportsMediaDownload', False)
        self.__all_scopes.update(method_description.get('scopes', ()))
        for param, desc in method_description.get('parameters', {}).items():
            param = self.__names.CleanName(param)
            location = desc['location']
            if location == 'query':
                method_info.query_params.append(param)
            elif location == 'path':
                method_info.path_params.append(param)
            else:
                raise ValueError(
                    'Unknown parameter location %s for parameter %s' % (
                        location, param))
        method_info.path_params.sort()
        method_info.query_params.sort()
        return method_info

    def __BodyFieldName(self, body_type):
        if body_type is None:
            return ''
        return self.__names.FieldName(body_type['$ref'])

    def __GetRequestType(self, body_type):
        return self.__names.ClassName(body_type.get('$ref'))

    def __GetRequestField(self, method_description, body_type):
        """Determine the request field for this method."""
        body_field_name = self.__BodyFieldName(body_type)
        if body_field_name in method_description.get('parameters', {}):
            body_field_name = self.__names.FieldName(
                '%s_resource' % body_field_name)
        # It's exceedingly unlikely that we'd get two name collisions, which
        # means it's bound to happen at some point.
        while body_field_name in method_description.get('parameters', {}):
            body_field_name = self.__names.FieldName(
                '%s_body' % body_field_name)
        return body_field_name

    def AddServiceFromResource(self, service_name, methods):
        """Add a new service named service_name with the given methods."""
        service_name = self.__names.CleanName(service_name)
        method_descriptions = methods.get('methods', {})
        method_info_map = collections.OrderedDict()
        items = sorted(method_descriptions.items())
        for method_name, method_description in items:
            method_name = self.__names.MethodName(method_name)

            # NOTE: According to the discovery document, if the request or
            # response is present, it will simply contain a `$ref`.
            body_type = method_description.get('request')
            if body_type is None:
                request_type = None
            else:
                request_type = self.__GetRequestType(body_type)
            if self.__NeedRequestType(method_description, request_type):
                request = self.__CreateRequestType(
                    method_description, body_type=body_type)
                request_field = self.__GetRequestField(
                    method_description, body_type)
            else:
                request = request_type
                request_field = base_api.REQUEST_IS_BODY

            if 'response' in method_description:
                response = method_description['response']['$ref']
            else:
                response = self.__CreateVoidResponseType(method_description)

            method_info_map[method_name] = self.__ComputeMethodInfo(
                method_description, request, response, request_field)

        nested_services = methods.get('resources', {})
        services = sorted(nested_services.items())
        for subservice_name, submethods in services:
            new_service_name = '%s_%s' % (service_name, subservice_name)
            self.AddServiceFromResource(new_service_name, submethods)

        self.__RegisterService(service_name, method_info_map)
