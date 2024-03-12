# -*- coding: utf-8 -*- #
# Copyright 2014 Google LLC. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""This module holds common flags used by the gcloud app commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import argparse

from googlecloudsdk.api_lib.app import logs_util
from googlecloudsdk.api_lib.storage import storage_util
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.app import exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core.docker import constants
from googlecloudsdk.core.docker import docker
from googlecloudsdk.third_party.appengine.api import appinfo

DOMAIN_FLAG = base.Argument(
    'domain',
    help=('A valid domain which may begin with a wildcard, such as: '
          '`example.com` or `*.example.com`'))

CERTIFICATE_ID_FLAG = base.Argument(
    'id',
    help=('The id of the certificate. This identifier is printed upon'
          ' creation of a new certificate. Run `{parent_command}'
          ' list` to view existing certificates.'))

LAUNCH_BROWSER = base.Argument(
    '--launch-browser',
    action='store_true', default=True, dest='launch_browser',
    help='Launch a browser if possible. When disabled, only displays the URL.')

IGNORE_CERTS_FLAG = base.Argument(
    '--ignore-bad-certs',
    action='store_true',
    default=False,
    hidden=True,
    help='THIS ARGUMENT NEEDS HELP TEXT.')

IGNORE_FILE_FLAG = base.Argument(
    '--ignore-file',
    help='Override the .gcloudignore file and use the specified file instead.')

FIREWALL_PRIORITY_FLAG = base.Argument(
    'priority',
    help=('An integer between 1 and 2^32-1 which indicates the evaluation order'
          ' of rules. Lowest priority rules are evaluated first. The handle '
          '`default` may also be used to refer to the final rule at priority'
          ' 2^32-1 which is always present in a set of rules.'))

LEVEL = base.Argument(
    '--level',
    help='Filter entries with severity equal to or higher than a given level.',
    required=False,
    default='any',
    choices=logs_util.LOG_LEVELS)

LOGS = base.Argument(
    '--logs',
    help=('Filter entries from a particular set of logs. Must be a '
          'comma-separated list of log names (request_log, stdout, stderr, '
          'etc).'),
    required=False,
    default=logs_util.DEFAULT_LOGS,
    metavar='APP_LOG',
    type=arg_parsers.ArgList(min_length=1))

SERVER_FLAG = base.Argument(
    '--server', hidden=True, help='THIS ARGUMENT NEEDS HELP TEXT.')

SERVICE = base.Argument(
    '--service', '-s', help='Limit to specific service.', required=False)

VERSION = base.Argument(
    '--version', '-v', help='Limit to specific version.', required=False)


def AddServiceVersionSelectArgs(parser, short_flags=False):
  """Add arguments to a parser for selecting service and version.

  Args:
    parser: An argparse.ArgumentParser.
    short_flags: bool, whether to add short flags `-s` and `-v` for service
      and version respectively.
  """

  parser.add_argument(
      '--service', *['-s'] if short_flags else [],
      required=False,
      help='The service ID.')
  parser.add_argument(
      '--version', *['-v'] if short_flags else [],
      required=False,
      help='The version ID.')


def AddCertificateIdFlag(parser, include_no_cert):
  """Add the --certificate-id flag to a domain-mappings command."""

  certificate_id = base.Argument(
      '--certificate-id',
      help=('A certificate id to use for this domain. May not be used on a '
            'domain mapping with automatically managed certificates. Use the '
            '`gcloud app ssl-certificates list` to see available certificates '
            'for this app.'))

  if include_no_cert:
    group = parser.add_mutually_exclusive_group()
    certificate_id.AddToParser(group)
    group.add_argument(
        '--no-certificate-id',
        action='store_true',
        help='Do not associate any certificate with this domain.')
  else:
    certificate_id.AddToParser(parser)


def AddCertificateManagementFlag(parser):
  """Adds common flags to a domain-mappings command."""
  certificate_argument = base.ChoiceArgument(
      '--certificate-management',
      choices=['automatic', 'manual'],
      help_str=('Type of certificate management. \'automatic\' will provision '
                'an SSL certificate automatically while \'manual\' requires '
                'the user to provide a certificate id to provision.'))
  certificate_argument.AddToParser(parser)


def AddSslCertificateFlags(parser, required):
  """Add the common flags to an ssl-certificates command."""

  parser.add_argument(
      '--display-name',
      required=required,
      help='A display name for this certificate.')
  parser.add_argument(
      '--certificate',
      required=required,
      metavar='LOCAL_FILE_PATH',
      help="""\
      The file path for the new certificate to upload. Must be in PEM
      x.509 format including the header and footer.
      """)
  parser.add_argument(
      '--private-key',
      required=required,
      metavar='LOCAL_FILE_PATH',
      help="""\
      The file path to a local RSA private key file. The private key must be
      PEM encoded with header and footer and must be 2048 bits
      or fewer.
        """)


def AddFirewallRulesFlags(parser, required):
  """Add the common flags to a firewall-rules command."""

  parser.add_argument('--source-range',
                      required=required,
                      help=('An IP address or range in CIDR notation or'
                            ' the ```*``` wildcard to match all traffic.'))
  parser.add_argument('--action',
                      required=required,
                      choices=['ALLOW', 'DENY'],
                      type=lambda x: x.upper(),
                      help='Allow or deny matched traffic.')
  parser.add_argument(
      '--description', help='A text description of the rule.')


def ValidateDockerBuildFlag(unused_value):
  raise argparse.ArgumentTypeError("""\
The --docker-build flag no longer exists.

Docker images are now built remotely using Google Container Builder. To run a
Docker build on your own host, you can run:
  docker build -t gcr.io/<project>/<service.version> .
  gcloud docker push gcr.io/<project>/<service.version>
  gcloud app deploy --image-url=gcr.io/<project>/<service.version>
If you don't already have a Dockerfile, you must run:
  gcloud beta app gen-config
first to get one.
  """)


DOCKER_BUILD_FLAG = base.Argument(
    '--docker-build',
    hidden=True,
    help='THIS ARGUMENT NEEDS HELP TEXT.',
    type=ValidateDockerBuildFlag)


LOG_SEVERITIES = ['debug', 'info', 'warning', 'error', 'critical']


def GetCodeBucket(app, project):
  """Gets a bucket reference for a Cloud Build.

  Args:
    app: App resource for this project
    project: str, The name of the current project.

  Returns:
    storage_util.BucketReference, The bucket to use.
  """
  # Attempt to retrieve the default appspot bucket, if one can be created.
  log.debug('No bucket specified, retrieving default bucket.')
  if not app.codeBucket:
    raise exceptions.DefaultBucketAccessError(project)
  return storage_util.BucketReference.FromUrl(app.codeBucket)


VERSION_TYPE = arg_parsers.RegexpValidator(
    appinfo.MODULE_VERSION_ID_RE_STRING,
    'May only contain lowercase letters, digits, and hyphens. '
    'Must begin and end with a letter or digit. Must not exceed 63 characters.')


def ValidateImageUrl(image_url, services):
  """Check the user-provided image URL.

  Ensures that:
  - it is consistent with the services being deployed (there must be exactly
    one)
  - it is an image in a supported Docker registry

  Args:
    image_url: str, the URL of the image to deploy provided by the user
    services: list, the services to deploy

  Raises:
    MultiDeployError: if image_url is provided and more than one service is
      being deployed
    docker.UnsupportedRegistryError: if image_url is provided and does not point
      to one of the supported registries
  """
  # Validate the image url if provided, and ensure there is a single service
  # being deployed.
  if image_url is None:
    return
  if len(services) != 1:
    raise exceptions.MultiDeployError()
  for registry in constants.ALL_SUPPORTED_REGISTRIES:
    if image_url.startswith(registry):
      return
  raise docker.UnsupportedRegistryError(image_url)
