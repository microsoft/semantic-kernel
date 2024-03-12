# -*- coding: utf-8 -*- #
# Copyright 2018 Google LLC. All Rights Reserved.
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
"""Create a client certificate for a Cloud SQL instance."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os
from googlecloudsdk.api_lib.sql import api_util
from googlecloudsdk.api_lib.sql import exceptions
from googlecloudsdk.api_lib.sql import validate
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.sql import flags
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core.util import files
import six


class _BaseAddCert(object):
  """Base class for sql ssl client_certs create."""

  @staticmethod
  def Args(parser):
    """Declare flag and positional arguments for the command parser."""
    parser.add_argument(
        'common_name',
        help='User supplied name. Constrained to ```[a-zA-Z.-_ ]+```.')
    parser.add_argument(
        'cert_file',
        default=None,
        help=('Location of file which the private key of the created ssl-cert'
              ' will be written to.'))
    flags.AddInstance(parser)
    parser.display_info.AddFormat(flags.CLIENT_CERTS_FORMAT)

  def Run(self, args):
    """Create a client certificate for a Cloud SQL instance.

    Args:
      args: argparse.Namespace, The arguments that this command was invoked
          with.

    Returns:
      A dict object representing the operations resource describing the create
      operation if the create was successful.
    Raises:
      ArgumentError: If the file path provided cannot be written to.
    """

    if os.path.exists(args.cert_file):
      raise exceptions.ArgumentError(
          'file [{path}] already exists'.format(path=args.cert_file))

    # First check if args.out_file is writeable. If not, abort and don't create
    # the useless cert.
    try:
      files.WriteFileContents(
          args.cert_file, 'placeholder\n', private=True, create_path=False)
    except (files.Error, OSError) as e:
      raise exceptions.ArgumentError('unable to write [{path}]: {error}'.format(
          path=args.cert_file, error=six.text_type(e)))

    client = api_util.SqlClient(api_util.API_VERSION_DEFAULT)
    sql_client = client.sql_client
    sql_messages = client.sql_messages

    validate.ValidateInstanceName(args.instance)
    instance_ref = client.resource_parser.Parse(
        args.instance,
        params={'project': properties.VALUES.core.project.GetOrFail},
        collection='sql.instances')

    # TODO(b/36049399): figure out how to rectify the common_name and the
    # sha1fingerprint, so that things can work with the resource parser.

    result = sql_client.sslCerts.Insert(
        sql_messages.SqlSslCertsInsertRequest(
            project=instance_ref.project,
            instance=instance_ref.instance,
            sslCertsInsertRequest=sql_messages.SslCertsInsertRequest(
                commonName=args.common_name)))

    private_key = result.clientCert.certPrivateKey
    files.WriteFileContents(args.cert_file, private_key + '\n', private=True)

    cert_ref = client.resource_parser.Create(
        collection='sql.sslCerts',
        project=instance_ref.project,
        instance=instance_ref.instance,
        sha1Fingerprint=result.clientCert.certInfo.sha1Fingerprint)

    log.CreatedResource(cert_ref)
    return result.clientCert.certInfo


@base.ReleaseTracks(base.ReleaseTrack.GA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.ALPHA)
class AddCert(_BaseAddCert, base.CreateCommand):
  """Create a client certificate for a Cloud SQL instance."""
  pass
