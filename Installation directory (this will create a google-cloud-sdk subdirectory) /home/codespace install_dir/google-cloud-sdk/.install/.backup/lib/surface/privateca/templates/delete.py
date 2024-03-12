# -*- coding: utf-8 -*- #
# Copyright 2021 Google LLC. All Rights Reserved.
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
"""Delete a certificate template."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.privateca import base as privateca_base
from googlecloudsdk.api_lib.privateca import request_utils
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.privateca import operations
from googlecloudsdk.command_lib.privateca import resource_args
from googlecloudsdk.core import log
from googlecloudsdk.core.console import console_io


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Delete(base.DeleteCommand):
  r"""Delete a certificate template.

    ## EXAMPLES

    To delete a certificate template:

      $ {command} my-template --location=us-west1

    To delete a certificate template while skipping the confirmation input:

      $ {command} my-template --location=us-west1 --quiet
  """

  @staticmethod
  def Args(parser):
    resource_args.AddCertificateTemplatePositionalResourceArg(
        parser, 'to delete')

  def Run(self, args):
    client = privateca_base.GetClientInstance(api_version='v1')
    messages = privateca_base.GetMessagesModule(api_version='v1')

    template_ref = args.CONCEPTS.certificate_template.Parse()
    template_name = template_ref.RelativeName()

    if not console_io.PromptContinue(
        message='You are about to delete the certificate template [{}]'.format(
            template_ref.RelativeName()),
        default=True):
      log.status.Print('Aborted by user.')
      return

    operation = client.projects_locations_certificateTemplates.Delete(
        messages
        .PrivatecaProjectsLocationsCertificateTemplatesDeleteRequest(
            name=template_name,
            requestId=request_utils.GenerateRequestId()))

    operations.Await(
        operation, 'Deleting Certificate Template', api_version='v1')

    log.status.Print(
        'Deleted Certificate Template [{}].'.format(template_name))
