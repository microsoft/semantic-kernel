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
"""Command for proxying to a given service."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.config import config_helper
from googlecloudsdk.command_lib.run import connection_context
from googlecloudsdk.command_lib.run import exceptions
from googlecloudsdk.command_lib.run import flags
from googlecloudsdk.command_lib.run import messages_util
from googlecloudsdk.command_lib.run import platforms
from googlecloudsdk.command_lib.run import pretty_print
from googlecloudsdk.command_lib.run import proxy
from googlecloudsdk.command_lib.run import resource_args
from googlecloudsdk.command_lib.run import serverless_operations
from googlecloudsdk.command_lib.util.concepts import concept_parsers
from googlecloudsdk.command_lib.util.concepts import presentation_specs
from googlecloudsdk.core.credentials import store


class Proxy(base.BinaryBackedCommand):
  """Proxy a service to localhost authenticating as the active account or with the specified token."""

  detailed_help = {
      'DESCRIPTION':
          """\
          {description}
          """,
      'EXAMPLES':
          """\
          To proxy the service 'my-service' at localhost port 8080:

              $ {command} my-service --port=8080

          To proxy the existing traffic tag 'my-tag' on the service 'my-service:

              $ {command} my-service --tag=my-tag
          """,
  }

  @staticmethod
  def CommonArgs(parser):
    service_presentation = presentation_specs.ResourcePresentationSpec(
        'SERVICE',
        resource_args.GetServiceResourceSpec(),
        'Service to proxy locally.',
        required=True,
        prefixes=False)
    flags.AddPortFlag(
        parser,
        help_text='Local port number to expose the proxied service. '
        'If not specified, it will be set to 8080.')
    flags.AddTokenFlag(parser)
    flags.AddDeployTagFlag(
        parser,
        help_text='Traffic tag of the service to expose via the proxy. If not '
        'specified, the default service URL will be proxied which may '
        'serve different revisions based on traffic-splits. '
        'Custom tags can be used to proxy specific revisions. Please see '
        'https://cloud.google.com/run/docs/rollouts-rollbacks-traffic-migration#tags.'
    )
    concept_parsers.ConceptParser([service_presentation]).AddToParser(parser)

  @staticmethod
  def Args(parser):
    Proxy.CommonArgs(parser)

  def _CheckPlatform(self):
    platform = platforms.GetPlatform()
    if platform != platforms.PLATFORM_MANAGED:
      raise exceptions.PlatformError(
          'This command is only supported for fully managed Cloud Run.')

  def Run(self, args):
    self._CheckPlatform()

    conn_context = connection_context.GetConnectionContext(
        args, flags.Product.RUN, self.ReleaseTrack())
    service_ref = args.CONCEPTS.service.Parse()
    flags.ValidateResource(service_ref)
    with serverless_operations.Connect(conn_context) as client:
      serv = client.GetService(service_ref)
    if not serv:
      raise exceptions.ArgumentError(
          messages_util.GetNotFoundMessage(conn_context, service_ref)
      )

    bind = '127.0.0.1:' + (args.port if args.port else '8080')
    host = self._GetUrl(serv, args.tag, service_ref.servicesId)

    command_executor = proxy.ProxyWrapper()
    pretty_print.Info(
        messages_util.GetStartDeployMessage(
            conn_context,
            service_ref,
            'Proxying to',
        )
    )
    pretty_print.Info('http://{} proxies to {}'.format(bind, host))

    if args.token:
      response = command_executor(host=host, token=args.token, bind=bind)
    else:
      # Keep restarting the proxy with fresh token before the token expires (1h)
      # until hitting a failure.
      while True:
        response = command_executor(
            host=host, token=_GetFreshIdToken(), bind=bind, duration='55m')
        if response.failed:
          break

    return self._DefaultOperationResponseHandler(response)

  def _GetUrl(self, serv, tag, serv_id):
    if not serv.status:
      raise exceptions.ArgumentError(
          'Status of service [{}] is not ready'.format(serv_id))
    if tag:
      for t in serv.status.traffic:
        if t.tag == tag:
          if not t.url:
            raise exceptions.ArgumentError(
                'URL for tag [{}] in service [{}] is not ready'.format(
                    tag, serv_id))
          return t.url
      raise exceptions.ArgumentError(
          'Cannot find tag [{}] in service [{}].'.format(tag, serv_id))
    # If not tag provided, use the default service URL.
    if not serv.status.url:
      raise exceptions.ArgumentError(
          'URL for service [{}] is not ready'.format(serv_id))
    return serv.status.url


def _GetFreshIdToken():
  cred = store.LoadFreshCredential()
  credential = config_helper.Credential(cred)
  return credential.id_token
