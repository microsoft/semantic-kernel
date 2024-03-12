# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""Delete a root certificate authority."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from dateutil import tz

from googlecloudsdk.api_lib.privateca import base as privateca_base
from googlecloudsdk.api_lib.privateca import request_utils
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.privateca import flags
from googlecloudsdk.command_lib.privateca import operations
from googlecloudsdk.command_lib.privateca import resource_args
from googlecloudsdk.core import log
from googlecloudsdk.core.console import console_io
from googlecloudsdk.core.util import times
import six


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Delete(base.DeleteCommand):
  r"""Delete a Root Certificate Authority.

    Delete a Root Certificate Authority. Deleted Root Certificate Authorities
    may be recovered with the `{parent_command} undelete` command within a grace
    period of 30 days.

    Use the --skip-grace-period flag to delete as soon as possible without the
    30-day grace period to undelete.

    Note that any user-managed KMS keys or Google Cloud Storage buckets
    will not be affected by this operation. You will need to delete the user-
    managed resources separately once the CA is deleted. Any Google-managed
    resources will be cleaned up.

    The CA specified in this command MUST:

      1) be in the DISABLED or STAGED state.
      2) have no un-revoked or un-expired certificates. Use the revoke command
         to revoke any active certificates.

    Use the `--ignore-active-certificates` flag to remove 2) as a requirement.

    ## EXAMPLES

    To delete a root CA:

      $ {command} prod-root --pool=my-pool --location=us-west1

    To delete a CA while skipping the confirmation
    input:

      $ {command} prod-root --pool=my-pool --location=us-west1 --quiet

    To undo the deletion for a root CA:

      $ {parent_command} undelete prod-root --pool=my-pool --location=us-west1
  """

  @staticmethod
  def Args(parser):
    resource_args.AddCertAuthorityPositionalResourceArg(parser, 'to delete')
    flags.AddIgnoreActiveCertificatesFlag(parser)
    flags.AddSkipGracePeriodFlag(parser)
    flags.AddIgnoreDependentResourcesFlag(parser)

  def Run(self, args):
    client = privateca_base.GetClientInstance(api_version='v1')
    messages = privateca_base.GetMessagesModule(api_version='v1')

    ca_ref = args.CONCEPTS.certificate_authority.Parse()

    prompt_message = (
        'You are about to delete Certificate Authority [{}].').format(
            ca_ref.RelativeName())
    if args.ignore_dependent_resources:
      prompt_message += (
          '\nThis deletion will happen without '
          'checking if the CA\'s CA Pool is being used by another '
          'resource, which may cause unintended and effects on any '
          'dependent resource(s) since the CA Pool would not be '
          'able to issue certificates.')
    if args.skip_grace_period:
      prompt_message += (
          '\nThis deletion will happen as '
          'soon as possible without a 30-day grace period where '
          'undeletion would have been allowed. If you proceed, there '
          'will be no way to recover this CA.')

    if not console_io.PromptContinue(message=prompt_message, default=True):
      log.status.Print('Aborted by user.')
      return

    current_ca = client.projects_locations_caPools_certificateAuthorities.Get(
        messages
        .PrivatecaProjectsLocationsCaPoolsCertificateAuthoritiesGetRequest(
            name=ca_ref.RelativeName()))

    resource_args.CheckExpectedCAType(
        messages.CertificateAuthority.TypeValueValuesEnum.SELF_SIGNED,
        current_ca,
        version='v1')

    operation = client.projects_locations_caPools_certificateAuthorities.Delete(
        messages
        .PrivatecaProjectsLocationsCaPoolsCertificateAuthoritiesDeleteRequest(
            name=ca_ref.RelativeName(),
            ignoreActiveCertificates=args.ignore_active_certificates,
            skipGracePeriod=args.skip_grace_period,
            ignoreDependentResources=args.ignore_dependent_resources,
            requestId=request_utils.GenerateRequestId()))

    try:
      ca_response = operations.Await(
          operation, 'Deleting Root CA', api_version='v1')
    except waiter.OperationError as e:
      # API error message refers to the proto field name which is slightly
      # different from the gcloud flag name.
      raise operations.OperationError(
          six.text_type(e).replace('`ignore_active_certificates` parameter',
                                   '`--ignore-active-certificates` flag'))
    ca = operations.GetMessageFromResponse(ca_response,
                                           messages.CertificateAuthority)

    formatted_expire_time = times.ParseDateTime(ca.expireTime).astimezone(
        tz.tzutc()).strftime('%Y-%m-%dT%H:%MZ')

    if args.skip_grace_period:
      log.status.Print('Deleted Root CA [{}]. CA can not be undeleted.'.format(
          ca_ref.RelativeName()))
    else:
      log.status.Print(
          'Deleted Root CA [{}]. CA can be undeleted until {}.'.format(
              ca_ref.RelativeName(), formatted_expire_time))
