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
"""services api-keys update command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.services import apikeys
from googlecloudsdk.api_lib.services import services_util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.services import common_flags
from googlecloudsdk.core import log

OP_BASE_CMD = 'gcloud services operations '
OP_WAIT_CMD = OP_BASE_CMD + 'wait {0}'
DETAILED_HELP = {
    'EXAMPLES':
        """
        To remove all restrictions of the key:

          $ {command} projects/myproject/keys/my-key-id --clear-restrictions

        To update display name and set allowed ips as server key restrictions:

          $ {command} projects/myproject/keys/my-key-id --display-name="test name" --allowed-ips=2620:15c:2c4:203:2776:1f90:6b3b:217,104.133.8.78

        To update annotations:

          $ {command} projects/myproject/keys/my-key-id --annotations=foo=bar,abc=def

        To update key's allowed referrers restriction:

          $ {command} projects/myproject/keys/my-key-id --allowed-referrers="https://www.example.com/*,http://sub.example.com/*"

        To update key's allowed ios app bundle ids:

          $ {command} projects/myproject/keys/my-key-id --allowed-bundle-ids=my.app

        To update key's allowed android application:

          $ {command} projects/myproject/keys/my-key-id --allowed-application=sha1_fingerprint=foo1,package_name=bar1 --allowed-application=sha1_fingerprint=foo2,package_name=bar2

        To update keys' allowed api target with multiple services:

          $ {command} projects/myproject/keys/my-key-id --api-target=service=bar.service.com --api-target=service=foo.service.com

        To update keys' allowed api target with service and method:

          $ {command} projects/myproject/keys/my-key-id  --flags-file=my-flags.yaml

          The content of 'my-flags.yaml' is as following:

          ```
            - --api-target:
                service: "foo.service.com"
            - --api-target:
                service: "bar.service.com"
                methods:
                - "foomethod"
                - "barmethod"
            ```
        """
}


@base.ReleaseTracks(
    base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA, base.ReleaseTrack.GA
)
class Update(base.UpdateCommand):
  """Update an API key's metadata."""

  @staticmethod
  def Args(parser):
    common_flags.key_flag(parser=parser, suffix='to update')
    common_flags.display_name_flag(parser=parser, suffix='to update')
    common_flags.add_key_update_args(parser)
    base.ASYNC_FLAG.AddToParser(parser)

  def Run(self, args):
    """Run command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      None
    """

    client = apikeys.GetClientInstance()
    messages = client.MESSAGES_MODULE

    key_ref = args.CONCEPTS.key.Parse()
    update_mask = []
    key_proto = messages.V2Key(
        name=key_ref.RelativeName(), restrictions=messages.V2Restrictions())
    if args.IsSpecified('annotations'):
      update_mask.append('annotations')
      key_proto.annotations = apikeys.GetAnnotations(args, messages)
    if args.IsSpecified('display_name'):
      update_mask.append('display_name')
      key_proto.displayName = args.display_name
    if args.IsSpecified('clear_annotations'):
      update_mask.append('annotations')
    if args.IsSpecified('clear_restrictions'):
      update_mask.append('restrictions')
    else:
      if args.IsSpecified('allowed_referrers'):
        update_mask.append('restrictions.browser_key_restrictions')
        key_proto.restrictions.browserKeyRestrictions = messages.V2BrowserKeyRestrictions(
            allowedReferrers=args.allowed_referrers)
      elif args.IsSpecified('allowed_ips'):
        update_mask.append('restrictions.server_key_restrictions')
        key_proto.restrictions.serverKeyRestrictions = messages.V2ServerKeyRestrictions(
            allowedIps=args.allowed_ips)
      elif args.IsSpecified('allowed_bundle_ids'):
        update_mask.append('restrictions.ios_key_restrictions')
        key_proto.restrictions.iosKeyRestrictions = messages.V2IosKeyRestrictions(
            allowedBundleIds=args.allowed_bundle_ids)
      elif args.IsSpecified('allowed_application'):
        update_mask.append('restrictions.android_key_restrictions')
        key_proto.restrictions.androidKeyRestrictions = messages.V2AndroidKeyRestrictions(
            allowedApplications=apikeys.GetAllowedAndroidApplications(
                args, messages))
      if args.IsSpecified('api_target'):
        update_mask.append('restrictions.api_targets')
        key_proto.restrictions.apiTargets = apikeys.GetApiTargets(
            args, messages)
    request = messages.ApikeysProjectsLocationsKeysPatchRequest(
        name=key_ref.RelativeName(),
        updateMask=','.join(update_mask),
        v2Key=key_proto)
    op = client.projects_locations_keys.Patch(request)
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
