# -*- coding: utf-8 -*- #
# Copyright 2020 Google Inc. All Rights Reserved.
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
"""services api-keys create command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.services import apikeys
from googlecloudsdk.api_lib.services import services_util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.services import common_flags
from googlecloudsdk.core import log
from googlecloudsdk.core import properties

OP_BASE_CMD = 'gcloud services operations '
OP_WAIT_CMD = OP_BASE_CMD + 'wait {0}'
DETAILED_HELP = {'EXAMPLES': """
        To create a key with display name and allowed ips specified:

          $ {command} --display-name="test name" --allowed-ips=2620:15c:2c4:203:2776:1f90:6b3b:217,104.133.8.78

        To create a key with annotations:

         $ {command} --annotations=foo=bar,abc=def

        To create a key with user-specified key id:

          $ {command} --key-id="my-key-id"

        To create a key with allowed referrers restriction:

          $ {command} --allowed-referrers="https://www.example.com/*,http://sub.example.com/*"

        To create a key with allowed ios app bundle ids:

          $ {command} --allowed-bundle-ids=my.app

        To create a key with allowed android application:

          $ {command} --allowed-application=sha1_fingerprint=foo1,package_name=bar.foo --allowed-application=sha1_fingerprint=foo2,package_name=foo.bar

        To create a key with allowed api targets (service name only):

          $ {command} --api-target=service=bar.service.com --api-target=service=foo.service.com

        To create a keys with allowed api targets (service and methods are
        specified):

          $ {command} --flags-file=my-flags.yaml

        The content of 'my-flags.yaml' is as following:

        ```
        - --api-target:
            service:
              - "foo.service.com"
        - --api-target:
            service:
              - "bar.service.com"
            methods:
              - "foomethod"
              - "barmethod"
        ```
        """}


@base.ReleaseTracks(
    base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA, base.ReleaseTrack.GA
)
class Create(base.CreateCommand):
  """Create an API key."""

  @staticmethod
  def Args(parser):
    common_flags.display_name_flag(parser=parser, suffix='to create')
    common_flags.add_key_create_args(parser)
    common_flags.key_id_flag(parser=parser, suffix='to create')
    base.ASYNC_FLAG.AddToParser(parser)

  def Run(self, args):
    """Run command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      None
    """
    project_id = properties.VALUES.core.project.GetOrFail()

    client = apikeys.GetClientInstance()
    messages = client.MESSAGES_MODULE

    key_proto = messages.V2Key(restrictions=messages.V2Restrictions())
    if args.IsSpecified('display_name'):
      key_proto.displayName = args.display_name
    if args.IsSpecified('allowed_referrers'):
      key_proto.restrictions.browserKeyRestrictions = messages.V2BrowserKeyRestrictions(
          allowedReferrers=args.allowed_referrers)
    elif args.IsSpecified('allowed_ips'):
      key_proto.restrictions.serverKeyRestrictions = messages.V2ServerKeyRestrictions(
          allowedIps=args.allowed_ips)
    elif args.IsSpecified('allowed_bundle_ids'):
      key_proto.restrictions.iosKeyRestrictions = messages.V2IosKeyRestrictions(
          allowedBundleIds=args.allowed_bundle_ids)
    elif args.IsSpecified('allowed_application'):
      key_proto.restrictions.androidKeyRestrictions = messages.V2AndroidKeyRestrictions(
          allowedApplications=apikeys.GetAllowedAndroidApplications(
              args, messages))
    if args.IsSpecified('api_target'):
      key_proto.restrictions.apiTargets = apikeys.GetApiTargets(args, messages)
    if args.IsSpecified('annotations'):
      key_proto.annotations = apikeys.GetAnnotations(args, messages)
    if args.IsSpecified('key_id'):
      request = messages.ApikeysProjectsLocationsKeysCreateRequest(
          parent=apikeys.GetParentResourceName(project_id),
          v2Key=key_proto,
          keyId=args.key_id,
      )
    else:
      request = messages.ApikeysProjectsLocationsKeysCreateRequest(
          parent=apikeys.GetParentResourceName(project_id), v2Key=key_proto
      )
    op = client.projects_locations_keys.Create(request)
    if not op.done:
      if args.async_:
        cmd = OP_WAIT_CMD.format(op.name)
        log.status.Print('Asynchronous operation is in progress... '
                         'Use the following command to wait for its '
                         'completion:\n {0}'.format(cmd))
        return op
      op = services_util.WaitOperation(op.name, apikeys.GetOperation)
    services_util.PrintOperationWithResponse(op)
    return op
  detailed_help = DETAILED_HELP
