# -*- coding: utf-8 -*- #
# Copyright 2013 Google LLC. All Rights Reserved.
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
"""Deletes an SSL certificate for a Cloud SQL instance."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.sql import api_util
from googlecloudsdk.api_lib.sql import cert
from googlecloudsdk.api_lib.sql import exceptions
from googlecloudsdk.api_lib.sql import operations
from googlecloudsdk.api_lib.sql import validate
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.sql import flags
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core.console import console_io


class _BaseDelete(object):
  """Base class for sql ssl_certs delete."""

  @staticmethod
  def Args(parser):
    """Args is called by calliope to gather arguments for this command.

    Args:
      parser: An argparse parser that you can use to add arguments that go
          on the command line after this command. Positional arguments are
          allowed.
    """
    base.ASYNC_FLAG.AddToParser(parser)
    parser.add_argument(
        'common_name',
        help='User supplied name. Constrained to ```[a-zA-Z.-_ ]+```.')
    flags.AddInstance(parser)


@base.ReleaseTracks(base.ReleaseTrack.GA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.ALPHA)
class Delete(_BaseDelete, base.Command):
  """Deletes an SSL certificate for a Cloud SQL instance."""

  def Run(self, args):
    """Deletes an SSL certificate for a Cloud SQL instance.

    Args:
      args: argparse.Namespace, The arguments that this command was invoked
          with.

    Returns:
      A dict object representing the operations resource describing the delete
      operation if the api request was successful.
    Raises:
      ResourceNotFoundError: The ssl cert could not be found for the instance.
    """
    client = api_util.SqlClient(api_util.API_VERSION_DEFAULT)
    sql_client = client.sql_client
    sql_messages = client.sql_messages

    validate.ValidateInstanceName(args.instance)
    instance_ref = client.resource_parser.Parse(
        args.instance,
        params={'project': properties.VALUES.core.project.GetOrFail},
        collection='sql.instances')

    # TODO(b/36050482): figure out how to rectify the common_name and the
    # sha1fingerprint, so that things can work with the resource parser.

    console_io.PromptContinue(
        message='{0} will be deleted. New connections can no longer be made '
        'using this certificate. Existing connections are not affected.'.format(
            args.common_name),
        default=True,
        cancel_on_no=True)

    cert_ref = cert.GetCertRefFromName(sql_client, sql_messages,
                                       client.resource_parser, instance_ref,
                                       args.common_name)
    if not cert_ref:
      raise exceptions.ResourceNotFoundError(
          'no ssl cert named [{name}] for instance [{instance}]'.format(
              name=args.common_name, instance=instance_ref))

    result = sql_client.sslCerts.Delete(
        sql_messages.SqlSslCertsDeleteRequest(
            project=cert_ref.project,
            instance=cert_ref.instance,
            sha1Fingerprint=cert_ref.sha1Fingerprint))

    operation_ref = client.resource_parser.Create(
        'sql.operations', operation=result.name, project=cert_ref.project)

    if args.async_:
      return sql_client.operations.Get(
          sql_messages.SqlOperationsGetRequest(
              project=operation_ref.project,
              operation=operation_ref.operation))

    operations.OperationsV1Beta4.WaitForOperation(sql_client, operation_ref,
                                                  'Deleting sslCert')

    log.DeletedResource(cert_ref)
