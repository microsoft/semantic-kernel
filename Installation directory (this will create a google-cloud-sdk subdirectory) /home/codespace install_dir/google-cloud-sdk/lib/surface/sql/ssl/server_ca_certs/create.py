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
"""Create a server CA cert for a Cloud SQL instance."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.sql import api_util
from googlecloudsdk.api_lib.sql import operations
from googlecloudsdk.api_lib.sql import validate
from googlecloudsdk.api_lib.sql.ssl import server_ca_certs
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.sql import flags
from googlecloudsdk.core import log
from googlecloudsdk.core import properties


class _BaseAddCert(object):
  """Base class for sql server_ca_certs create."""

  @staticmethod
  def Args(parser):
    """Declare flag and positional arguments for the command parser."""
    base.ASYNC_FLAG.AddToParser(parser)
    flags.AddInstance(parser)
    parser.display_info.AddFormat(flags.SERVER_CA_CERTS_FORMAT)

  def Run(self, args):
    """Create a server CA cert for a Cloud SQL instance.

    Args:
      args: argparse.Namespace, The arguments that this command was invoked
          with.

    Returns:
      The upcoming Server CA Cert, if the operation was successful.
    """

    client = api_util.SqlClient(api_util.API_VERSION_DEFAULT)
    sql_client = client.sql_client
    sql_messages = client.sql_messages

    validate.ValidateInstanceName(args.instance)
    instance_ref = client.resource_parser.Parse(
        args.instance,
        params={'project': properties.VALUES.core.project.GetOrFail},
        collection='sql.instances')

    result_operation = sql_client.instances.AddServerCa(
        sql_messages.SqlInstancesAddServerCaRequest(
            project=instance_ref.project, instance=instance_ref.instance))

    operation_ref = client.resource_parser.Create(
        'sql.operations',
        operation=result_operation.name,
        project=instance_ref.project)

    operations.OperationsV1Beta4.WaitForOperation(
        sql_client, operation_ref, 'Creating Server CA Certificate')

    next_server_ca = server_ca_certs.GetNextServerCa(sql_client, sql_messages,
                                                     instance_ref)

    cert_ref = client.resource_parser.Create(
        collection='sql.sslCerts',
        project=instance_ref.project,
        instance=instance_ref.instance,
        sha1Fingerprint=next_server_ca.sha1Fingerprint)

    log.CreatedResource(cert_ref)
    return next_server_ca


@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.ALPHA)
class AddCert(_BaseAddCert, base.CreateCommand):
  """Create a server CA cert for a Cloud SQL instance."""
  pass
