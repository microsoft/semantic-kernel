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
"""Roll back to the previous server CA cert for a Cloud SQL instance."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.sql import api_util
from googlecloudsdk.api_lib.sql import exceptions
from googlecloudsdk.api_lib.sql import operations
from googlecloudsdk.api_lib.sql import validate
from googlecloudsdk.api_lib.sql.ssl import server_ca_certs
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.sql import flags
from googlecloudsdk.core import properties


class _BaseRollbackCert(object):
  """Base class for sql server_ca_certs rollback."""

  @staticmethod
  def Args(parser):
    """Declare flag and positional arguments for the command parser."""
    base.ASYNC_FLAG.AddToParser(parser)
    flags.AddInstance(parser)
    parser.display_info.AddFormat(flags.SERVER_CA_CERTS_FORMAT)

  def Run(self, args):
    """Roll back to the previous server CA cert for a Cloud SQL instance.

    Args:
      args: argparse.Namespace, The arguments that this command was invoked
          with.

    Returns:
      The Server CA Cert that was rolled back to, if the operation was
      successful.
    """

    client = api_util.SqlClient(api_util.API_VERSION_DEFAULT)
    sql_client = client.sql_client
    sql_messages = client.sql_messages

    validate.ValidateInstanceName(args.instance)
    instance_ref = client.resource_parser.Parse(
        args.instance,
        params={'project': properties.VALUES.core.project.GetOrFail},
        collection='sql.instances')

    previous_server_ca = server_ca_certs.GetPreviousServerCa(
        sql_client, sql_messages, instance_ref)

    if not previous_server_ca:
      raise exceptions.ResourceNotFoundError(
          'No previous Server CA Certificate exists.')

    result_operation = sql_client.instances.RotateServerCa(
        sql_messages.SqlInstancesRotateServerCaRequest(
            project=instance_ref.project,
            instance=instance_ref.instance,
            instancesRotateServerCaRequest=sql_messages.
            InstancesRotateServerCaRequest(
                rotateServerCaContext=sql_messages.RotateServerCaContext(
                    nextVersion=previous_server_ca.sha1Fingerprint))))

    operation_ref = client.resource_parser.Create(
        'sql.operations',
        operation=result_operation.name,
        project=instance_ref.project)

    operations.OperationsV1Beta4.WaitForOperation(
        sql_client, operation_ref,
        'Rolling back to previous Server CA Certificate')

    return previous_server_ca


@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.ALPHA)
class RollbackCert(_BaseRollbackCert, base.CreateCommand):
  """Roll back to the previous server CA cert for a Cloud SQL instance."""
  pass
