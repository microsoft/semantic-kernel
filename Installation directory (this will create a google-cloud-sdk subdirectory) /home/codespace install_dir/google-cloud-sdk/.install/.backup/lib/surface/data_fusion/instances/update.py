# -*- coding: utf-8 -*- #
# Copyright 2019 Google Inc. All Rights Reserved.
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
"""Command to update a Data Fusion instance."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import encoding

from googlecloudsdk.api_lib.data_fusion import datafusion as df
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.data_fusion import operation_poller
from googlecloudsdk.command_lib.data_fusion import resource_args
from googlecloudsdk.command_lib.util.args import labels_util
from googlecloudsdk.core import log


class Update(base.UpdateCommand):
  # pylint:disable=line-too-long
  r"""Updates a Cloud Data Fusion instance."""
  detailed_help = {
      'DESCRIPTION':
          """\
       If run asynchronously with `--async`, exits after printing an operation
       that can be used to poll the status of the creation operation via:

         {command} operations list
          """,
      'EXAMPLES':
          """\
        To update instance 'my-instance' in project 'my-project' and location
        'my-location' to version `6.9.2`, run:

          $ {command} --project=my-project --location=my-location --version=6.9.2 my-instance

        To update instance 'my-instance' in project 'my-project' and location
        'my-location' to patch revision '6.9.2.1', run:

          $ {command} --project=my-project --location=my-location --version=6.9.2 --patch_revision=6.9.2.1 my-instance
          """,
  }

  # REST API Field Names for the updateMask
  FIELD_PATH_OPTIONS = 'options'
  FIELD_PATH_ENABLE_RBAC = 'enableRbac'
  FIELD_PATH_ENABLE_STACKDRIVER_LOGGING = 'enableStackdriverLogging'
  FIELD_PATH_ENABLE_STACKDRIVER_MONITORING = 'enableStackdriverMonitoring'

  @staticmethod
  def Args(parser):
    resource_args.AddInstanceResourceArg(parser, 'Instance to update.')
    base.ASYNC_FLAG.AddToParser(parser)
    labels_util.AddCreateLabelsFlags(parser)
    parser.add_argument(
        '--enable_stackdriver_logging',
        action='store_true',
        help='Enable Stackdriver logging for this Data Fusion instance.')
    parser.add_argument(
        '--enable_stackdriver_monitoring',
        action='store_true',
        help='Enable Stackdriver monitoring for this Data Fusion instance.')
    parser.add_argument(
        '--enable_rbac',
        action='store_true',
        help='Enable granular role-based access control for this Data Fusion instance.'
    )
    parser.add_argument(
        '--options',
        type=arg_parsers.ArgDict(),
        metavar='KEY=VALUE',
        help='Options to use for instance update, '
        'specified as KEY1=VALUE1,KEY2=VALUE2.')
    parser.add_argument('--version', help='Version of Datafusion to update to.')
    parser.add_argument('--patch_revision', help='Patch revision version of Cloud Data Fusion to update to.')

  def Run(self, args):
    datafusion = df.Datafusion()
    instance_ref = args.CONCEPTS.instance.Parse()

    labels = args.labels or {}
    enable_stackdriver_logging = None
    enable_stackdriver_monitoring = None
    enable_rbac = None
    options = {}

    fields_to_update = []
    if args.IsSpecified('options'):
      options = args.options
      fields_to_update.append(self.FIELD_PATH_OPTIONS)
    if args.IsSpecified('enable_rbac'):
      fields_to_update.append(self.FIELD_PATH_ENABLE_RBAC)
      enable_rbac = args.enable_rbac
    if args.IsSpecified('enable_stackdriver_logging'):
      fields_to_update.append(self.FIELD_PATH_ENABLE_STACKDRIVER_LOGGING)
      enable_stackdriver_logging = args.enable_stackdriver_logging
    if args.IsSpecified('enable_stackdriver_monitoring'):
      fields_to_update.append(self.FIELD_PATH_ENABLE_STACKDRIVER_MONITORING)
      enable_stackdriver_monitoring = args.enable_stackdriver_monitoring

    version = args.version
    instance = datafusion.messages.Instance(
        name=instance_ref.RelativeName(),
        version=version,
        patchRevision=args.patch_revision,
        enableStackdriverLogging=enable_stackdriver_logging,
        enableStackdriverMonitoring=enable_stackdriver_monitoring,
        enableRbac=enable_rbac,
        options=encoding.DictToAdditionalPropertyMessage(
            options, datafusion.messages.Instance.OptionsValue, True),
        labels=encoding.DictToAdditionalPropertyMessage(
            labels, datafusion.messages.Instance.LabelsValue, True))
    request = datafusion.messages.DatafusionProjectsLocationsInstancesPatchRequest(
        instance=instance,
        updateMask=','.join(fields_to_update),
        name=instance_ref.RelativeName())

    operation = datafusion.client.projects_locations_instances.Patch(request)

    if args.async_:
      log.CreatedResource(
          instance_ref.RelativeName(), kind='instance', is_async=True)
      return operation
    else:
      waiter.WaitFor(
          operation_poller.OperationPoller(),
          operation.name,
          'Waiting for [{}] to complete. This may take several minutes.'.format(
              operation.name),
          wait_ceiling_ms=df.OPERATION_TIMEOUT)
      log.UpdatedResource(
          instance_ref.RelativeName(), kind='instance', is_async=False)
