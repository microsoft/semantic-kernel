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

"""Command-line interface to gen_client."""

import argparse
import contextlib
import io
import json
import logging
import os
import pkgutil
import sys

from apitools.base.py import exceptions
from apitools.gen import gen_client_lib
from apitools.gen import util


def _CopyLocalFile(filename):
    with contextlib.closing(io.open(filename, 'w')) as out:
        src_data = pkgutil.get_data(
            'apitools.base.py', filename)
        if src_data is None:
            raise exceptions.GeneratedClientError(
                'Could not find file %s' % filename)
        out.write(src_data)


def _GetDiscoveryDocFromFlags(args):
    """Get the discovery doc from flags."""
    if args.discovery_url:
        try:
            return util.FetchDiscoveryDoc(args.discovery_url)
        except exceptions.CommunicationError:
            raise exceptions.GeneratedClientError(
                'Could not fetch discovery doc')

    infile = os.path.expanduser(args.infile) or '/dev/stdin'
    with io.open(infile, encoding='utf8') as f:
        return json.loads(util.ReplaceHomoglyphs(f.read()))


def _GetCodegenFromFlags(args):
    """Create a codegen object from flags."""
    discovery_doc = _GetDiscoveryDocFromFlags(args)
    names = util.Names(
        args.strip_prefix,
        args.experimental_name_convention,
        args.experimental_capitalize_enums)

    if args.client_json:
        try:
            with io.open(args.client_json, encoding='utf8') as client_json:
                f = json.loads(util.ReplaceHomoglyphs(client_json.read()))
                web = f.get('installed', f.get('web', {}))
                client_id = web.get('client_id')
                client_secret = web.get('client_secret')
        except IOError:
            raise exceptions.NotFoundError(
                'Failed to open client json file: %s' % args.client_json)
    else:
        client_id = args.client_id
        client_secret = args.client_secret

    if not client_id:
        logging.warning('No client ID supplied')
        client_id = ''

    if not client_secret:
        logging.warning('No client secret supplied')
        client_secret = ''

    client_info = util.ClientInfo.Create(
        discovery_doc, args.scope, client_id, client_secret,
        args.user_agent, names, args.api_key)
    outdir = os.path.expanduser(args.outdir) or client_info.default_directory
    if os.path.exists(outdir) and not args.overwrite:
        raise exceptions.ConfigurationValueError(
            'Output directory exists, pass --overwrite to replace '
            'the existing files.')
    if not os.path.exists(outdir):
        os.makedirs(outdir)

    return gen_client_lib.DescriptorGenerator(
        discovery_doc, client_info, names, args.root_package, outdir,
        base_package=args.base_package,
        protorpc_package=args.protorpc_package,
        init_wildcards_file=(args.init_file == 'wildcards'),
        use_proto2=args.experimental_proto2_output,
        unelidable_request_methods=args.unelidable_request_methods,
        apitools_version=args.apitools_version)


# TODO(craigcitro): Delete this if we don't need this functionality.
def _WriteBaseFiles(codegen):
    with util.Chdir(codegen.outdir):
        _CopyLocalFile('base_api.py')
        _CopyLocalFile('credentials_lib.py')
        _CopyLocalFile('exceptions.py')


def _WriteIntermediateInit(codegen):
    with io.open('__init__.py', 'w') as out:
        codegen.WriteIntermediateInit(out)


def _WriteProtoFiles(codegen):
    with util.Chdir(codegen.outdir):
        with io.open(codegen.client_info.messages_proto_file_name, 'w') as out:
            codegen.WriteMessagesProtoFile(out)
        with io.open(codegen.client_info.services_proto_file_name, 'w') as out:
            codegen.WriteServicesProtoFile(out)


def _WriteGeneratedFiles(args, codegen):
    if codegen.use_proto2:
        _WriteProtoFiles(codegen)
    with util.Chdir(codegen.outdir):
        with io.open(codegen.client_info.messages_file_name, 'w') as out:
            codegen.WriteMessagesFile(out)
        with io.open(codegen.client_info.client_file_name, 'w') as out:
            codegen.WriteClientLibrary(out)


def _WriteInit(codegen):
    with util.Chdir(codegen.outdir):
        with io.open('__init__.py', 'w') as out:
            codegen.WriteInit(out)


def _WriteSetupPy(codegen):
    with io.open('setup.py', 'w') as out:
        codegen.WriteSetupPy(out)


def GenerateClient(args):

    """Driver for client code generation."""

    codegen = _GetCodegenFromFlags(args)
    if codegen is None:
        logging.error('Failed to create codegen, exiting.')
        return 128
    _WriteGeneratedFiles(args, codegen)
    if args.init_file != 'none':
        _WriteInit(codegen)


def GeneratePipPackage(args):

    """Generate a client as a pip-installable tarball."""

    discovery_doc = _GetDiscoveryDocFromFlags(args)
    package = discovery_doc['name']
    original_outdir = os.path.expanduser(args.outdir)
    args.outdir = os.path.join(
        args.outdir, 'apitools/clients/%s' % package)
    args.root_package = 'apitools.clients.%s' % package
    codegen = _GetCodegenFromFlags(args)
    if codegen is None:
        logging.error('Failed to create codegen, exiting.')
        return 1
    _WriteGeneratedFiles(args, codegen)
    _WriteInit(codegen)
    with util.Chdir(original_outdir):
        _WriteSetupPy(codegen)
        with util.Chdir('apitools'):
            _WriteIntermediateInit(codegen)
            with util.Chdir('clients'):
                _WriteIntermediateInit(codegen)


def GenerateProto(args):
    """Generate just the two proto files for a given API."""

    codegen = _GetCodegenFromFlags(args)
    _WriteProtoFiles(codegen)


class _SplitCommaSeparatedList(argparse.Action):

    def __call__(self, parser, namespace, values, option_string=None):
        setattr(namespace, self.dest, values.split(','))


def main(argv=None):
    if argv is None:
        argv = sys.argv
    parser = argparse.ArgumentParser(
        description='Apitools Client Code Generator')

    discovery_group = parser.add_mutually_exclusive_group()
    discovery_group.add_argument(
        '--infile',
        help=('Filename for the discovery document. Mutually exclusive with '
              '--discovery_url'))

    discovery_group.add_argument(
        '--discovery_url',
        help=('URL (or "name.version") of the discovery document to use. '
              'Mutually exclusive with --infile.'))

    parser.add_argument(
        '--base_package',
        default='apitools.base.py',
        help='Base package path of apitools (defaults to apitools.base.py')

    parser.add_argument(
        '--protorpc_package',
        default='apitools.base.protorpclite',
        help=('Base package path of protorpc '
              '(defaults to apitools.base.protorpclite'))

    parser.add_argument(
        '--outdir',
        default='',
        help='Directory name for output files. (Defaults to the API name.)')

    parser.add_argument(
        '--overwrite',
        default=False, action='store_true',
        help='Only overwrite the output directory if this flag is specified.')

    parser.add_argument(
        '--root_package',
        default='',
        help=('Python import path for where these modules '
              'should be imported from.'))

    parser.add_argument(
        '--strip_prefix', nargs='*',
        default=[],
        help=('Prefix to strip from type names in the discovery document. '
              '(May be specified multiple times.)'))

    parser.add_argument(
        '--api_key',
        help=('API key to use for API access.'))

    parser.add_argument(
        '--client_json',
        help=('Use the given file downloaded from the dev. console for '
              'client_id and client_secret.'))

    parser.add_argument(
        '--client_id',
        default='1042881264118.apps.googleusercontent.com',
        help='Client ID to use for the generated client.')

    parser.add_argument(
        '--client_secret',
        default='x_Tw5K8nnjoRAqULM9PFAC2b',
        help='Client secret for the generated client.')

    parser.add_argument(
        '--scope', nargs='*',
        default=[],
        help=('Scopes to request in the generated client. '
              'May be specified more than once.'))

    parser.add_argument(
        '--user_agent',
        default='x_Tw5K8nnjoRAqULM9PFAC2b',
        help=('User agent for the generated client. '
              'Defaults to <api>-generated/0.1.'))

    parser.add_argument(
        '--generate_cli', dest='generate_cli', action='store_true',
        help='Ignored.')
    parser.add_argument(
        '--nogenerate_cli', dest='generate_cli', action='store_false',
        help='Ignored.')

    parser.add_argument(
        '--init-file',
        choices=['none', 'empty', 'wildcards'],
        type=lambda s: s.lower(),
        default='wildcards',
        help='Controls whether and how to generate package __init__.py file.')

    parser.add_argument(
        '--unelidable_request_methods',
        action=_SplitCommaSeparatedList,
        default=[],
        help=('Full method IDs of methods for which we should NOT try to '
              'elide the request type. (Should be a comma-separated list.'))

    parser.add_argument(
        '--apitools_version',
        default='', dest='apitools_version',
        help=('Apitools version used as a requirement in generated clients. '
              'Defaults to version of apitools used to generate the clients.'))

    parser.add_argument(
        '--experimental_capitalize_enums',
        default=False, action='store_true',
        help='Dangerous: attempt to rewrite enum values to be uppercase.')

    parser.add_argument(
        '--experimental_name_convention',
        choices=util.Names.NAME_CONVENTIONS,
        default=util.Names.DEFAULT_NAME_CONVENTION,
        help='Dangerous: use a particular style for generated names.')

    parser.add_argument(
        '--experimental_proto2_output',
        default=False, action='store_true',
        help='Dangerous: also output a proto2 message file.')

    subparsers = parser.add_subparsers(help='Type of generated code')

    client_parser = subparsers.add_parser(
        'client', help='Generate apitools client in destination folder')
    client_parser.set_defaults(func=GenerateClient)

    pip_package_parser = subparsers.add_parser(
        'pip_package', help='Generate apitools client pip package')
    pip_package_parser.set_defaults(func=GeneratePipPackage)

    proto_parser = subparsers.add_parser(
        'proto', help='Generate apitools client protos')
    proto_parser.set_defaults(func=GenerateProto)

    args = parser.parse_args(argv[1:])
    return args.func(args) or 0


if __name__ == '__main__':
    sys.exit(main())
