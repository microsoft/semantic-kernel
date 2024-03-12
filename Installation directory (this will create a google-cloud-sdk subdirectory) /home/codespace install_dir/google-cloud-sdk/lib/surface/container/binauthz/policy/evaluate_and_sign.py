# -*- coding: utf-8 -*- #
# Copyright 2023 Google LLC. All Rights Reserved.
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
"""Evaluate policy command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.container.binauthz import apis
from googlecloudsdk.api_lib.container.binauthz import platform_policy
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.container.binauthz import flags
from googlecloudsdk.command_lib.container.binauthz import parsing
from googlecloudsdk.command_lib.container.binauthz import sigstore_image
from googlecloudsdk.command_lib.container.binauthz import util
from googlecloudsdk.core import log
from googlecloudsdk.core import yaml
from googlecloudsdk.core.exceptions import Error


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class EvaluateAndSign(base.Command):
  """Evaluate a Binary Authorization platform policy and sign the results, if conformant.

  ## EXAMPLES

  To evaluate and sign a policy using its resource name:

    $ {command} projects/my-proj/platforms/gke/policies/my-policy
    --resource=$KUBERNETES_RESOURCE

  To evaluate the same policy using flags against multiple images:

    $ {command} my-policy --platform=gke --project=my-proj --image=$IMAGE1
    --image=$IMAGE2

  To return a modified resource with attestations added as an annotation on the
  input resource, without uploading attestations to the registry:

    $ {command} projects/my-proj/platforms/gke/policies/my-policy
    --resource=$KUBERNETES_RESOURCE --output-file=$MODIFIED_RESOURCE --no-upload

  To upload attestations using Docker credentials located in a custom directory:

    $ {command} projects/my-proj/platforms/gke/policies/my-policy
    --image=$IMAGE --use-docker-creds --docker-config-dir=$CUSTOM_DIR
  """

  @staticmethod
  def Args(parser):
    flags.AddPlatformPolicyResourceArg(parser, 'to evaluate and sign')
    flags.AddEvaluationUnitArg(parser)
    flags.AddNoUploadArg(parser)
    flags.AddOutputFileArg(parser)
    flags.AddDockerCredsArgs(parser)

  def Run(self, args):
    policy_ref = args.CONCEPTS.policy_resource_name.Parse().RelativeName()
    platform_id = policy_ref.split('/')[3]
    if platform_id != 'gke':
      raise Error(
          "Found unsupported platform '{}'. Currently only 'gke' platform "
          'policies are supported.'.format(platform_id)
      )

    if args.output_file and not args.resource:
      raise util.Error('Cannot specify --output-file without --resource.')

    if args.use_docker_creds and args.no_upload:
      raise util.Error('Cannot specify --use-docker-creds with --no-upload.')

    if args.docker_config_dir and not args.use_docker_creds:
      raise util.Error(
          'Cannot specify --docker-config-dir without --use-docker-creds.'
      )

    if args.resource:
      resource_obj = parsing.LoadResourceFile(args.resource)
    else:
      resource_obj = util.GeneratePodSpecFromImages(args.image)
    response = platform_policy.Client('v1').Evaluate(
        policy_ref, resource_obj, True
    )

    # Set non-zero exit code for non-conformant verdicts to improve the
    # command's scriptability.
    if (
        response.verdict
        != apis.GetMessagesModule(
            'v1'
        ).EvaluateGkePolicyResponse.VerdictValueValuesEnum.CONFORMANT
    ):
      self.exit_code = 2
      return response

    # Upload attestations.
    if not args.no_upload:
      for attestation in response.attestations:
        image_url = sigstore_image.AttestationToImageUrl(attestation)
        log.Print('Uploading attestation for {}'.format(image_url))
        sigstore_image.UploadAttestationToRegistry(
            image_url=image_url,
            attestation=sigstore_image.StandardOrUrlsafeBase64Decode(
                attestation
            ),
            use_docker_creds=args.use_docker_creds,
            docker_config_dir=args.docker_config_dir,
        )

    # Write inline attestations.
    if args.output_file:
      modified_resource = util.AddInlineAttestationsToResource(
          resource_obj, response.attestations
      )
      if (
          parsing.GetResourceFileType(args.resource)
          == parsing.ResourceFileType.YAML
      ):
        modified_resource = yaml.dump(modified_resource)
      log.WriteToFileOrStdout(
          args.output_file,
          modified_resource,
          overwrite=True,
          binary=False,
          private=True,
      )

    return response
