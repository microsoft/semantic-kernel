# -*- coding: utf-8 -*- #
# Copyright 2022 Google LLC. All Rights Reserved.
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
"""Generate RBAC policy files for Connect Gateway users."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import sys
import textwrap

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.container.fleet import kube_util
from googlecloudsdk.command_lib.container.fleet import rbac_util
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core.console import console_io
from googlecloudsdk.core.util import files as file_utils


@base.ReleaseTracks(
    base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA, base.ReleaseTrack.GA
)
class GenerateGatewayRbac(base.Command):
  # pylint: disable=line-too-long
  r"""Generate RBAC policy files for connected clusters by the user.

  {command} generates RBAC policies to be used by Connect Gateway API.

  Upon success, this command will write the output RBAC policy to the designated
  local file in dry run mode.

  Override RBAC policy: Y to override previous RBAC policy, N to stop. If
  overriding the --role, Y will clean up the previous RBAC policy and then apply
  the new one.

  ## EXAMPLES
    The current implementation supports multiple modes:

    Dry run mode to generate the RBAC policy file, and write to local directory:

      $ {command} --membership=my-cluster
      --users=foo@example.com,test-acct@test-project.iam.gserviceaccount.com
      --role=clusterrole/cluster-admin --rbac-output-file=./rbac.yaml

    Dry run mode to generate the RBAC policy, and print on screen:

      $ {command} --membership=my-cluster
      --users=foo@example.com,test-acct@test-project.iam.gserviceaccount.com
      --role=clusterrole/cluster-admin

    Anthos support mode, generate the RBAC policy file with read-only permission
    for TSE/Eng to debug customers' clusters:

      $ {command} --membership=my-cluster --anthos-support

    Apply mode, generate the RBAC policy and apply it to the specified cluster:

      $ {command} --membership=my-cluster
      --users=foo@example.com,test-acct@test-project.iam.gserviceaccount.com
      --role=clusterrole/cluster-admin --context=my-cluster-context
      --kubeconfig=/home/user/custom_kubeconfig --apply

    Revoke mode, revoke the RBAC policy for the specified users:

      $ {command} --membership=my-cluster
      --users=foo@example.com,test-acct@test-project.iam.gserviceaccount.com
      --role=clusterrole/cluster-admin --context=my-cluster-context
      --kubeconfig=/home/user/custom_kubeconfig --revoke

    The role to be granted to the users can either be cluster-scoped or
    namespace-scoped. To grant a namespace-scoped role to the users in dry run
    mode, run:

      $ {command} --membership=my-cluster
      --users=foo@example.com,test-acct@test-project.iam.gserviceaccount.com
      --role=role/mynamespace/namespace-reader

    The users provided can be using a Google identity (only email) or using
    external identity providers (starting with
    "principal://iam.googleapis.com"):

      $ {command} --membership=my-cluster
      --users=foo@example.com,principal://iam.googleapis.com/locations/global/workforcePools/pool/subject/user
      --role=clusterrole/cluster-admin --context=my-cluster-context
      --kubeconfig=/home/user/custom_kubeconfig --apply

    The groups can be provided as a Google identity (only email) or an
    external identity (starting with
    "principalSet://iam.googleapis.com"):

      $ {command} --membership=my-cluster
      --groups=group@example.com,principalSet://iam.googleapis.com/locations/global/workforcePools/pool/group/ExampleGroup
      --role=clusterrole/cluster-admin --context=my-cluster-context
      --kubeconfig=/home/user/custom_kubeconfig --apply
  """

  @classmethod
  def Args(cls, parser):
    parser.add_argument(
        '--membership',
        type=str,
        help=textwrap.dedent("""\
          Membership name to assign RBAC policy with.
        """),
    )
    parser.add_argument(
        '--role',
        type=str,
        help=textwrap.dedent("""\
          Namespace scoped role or cluster role.
        """),
    )
    parser.add_argument(
        '--rbac-output-file',
        type=str,
        help=textwrap.dedent("""\
          If specified, this command will execute in dry run mode and write to
          the file specified with this flag: the generated RBAC policy will not
          be applied to Kubernetes clusters,instead it will be written to the
          designated local file.
        """),
    )
    parser.add_argument(
        '--apply',
        action='store_true',
        help=textwrap.dedent("""\
          If specified, this command will generate RBAC policy and apply to the
          specified cluster.
        """),
    )
    parser.add_argument(
        '--context',
        type=str,
        help=textwrap.dedent("""\
          The cluster context as it appears in the kubeconfig file. You can get
        this value from the command line by running command:
        `kubectl config current-context`.
        """),
    )
    parser.add_argument(
        '--kubeconfig',
        type=str,
        help=textwrap.dedent("""\
            The kubeconfig file containing an entry for the cluster. Defaults to
            $KUBECONFIG if it is set in the environment, otherwise defaults to
            $HOME/.kube/config.
          """),
    )
    parser.add_argument(
        '--revoke',
        action='store_true',
        help=textwrap.dedent("""\
          If specified, this command will revoke the RBAC policy for the
          specified users.
        """),
    )
    identities = parser.add_mutually_exclusive_group(required=True)
    identities.add_argument(
        '--groups',
        type=str,
        help=textwrap.dedent("""\
          Group email address or third-party IAM group principal.
        """),
    )
    identities.add_argument(
        '--users',
        type=str,
        help=textwrap.dedent("""\
          User's email address, service account email address, or third-party IAM subject principal.
        """),
    )
    identities.add_argument(
        '--anthos-support',
        action='store_true',
        help=textwrap.dedent("""\
          If specified, this command will generate RBAC policy
          file for anthos support.
        """),
    )

  def Run(self, args):
    log.status.Print('Validating input arguments.')
    project_id = properties.VALUES.core.project.GetOrFail()

    # Validate the args value before generate the RBAC policy file.
    rbac_util.ValidateArgs(args)

    # Revoke RBAC policy for specified user from cluster.
    if args.revoke:
      sys.stdout.write(
          'Revoking the RBAC policy from cluster with kubeconfig: {}, context:'
          ' {}\n'.format(args.kubeconfig, args.context)
      )

      with kube_util.KubernetesClient(
          kubeconfig=getattr(args, 'kubeconfig', None),
          context=getattr(args, 'context', None),
      ) as kube_client:
        # Check Admin permissions.
        kube_client.CheckClusterAdminPermissions()
        identities_list = list()
        if args.users:
          identities_list = [(user, True) for user in args.users.split(',')]
        elif args.anthos_support:
          identities_list.append(
              (rbac_util.GetAnthosSupportUser(project_id), True)
          )
        elif args.groups:
          identities_list = [(group, False) for group in args.groups.split(',')]
        for identity, is_user in identities_list:
          message = 'The RBAC policy for {} will be cleaned up.'.format(
              identity
          )
          console_io.PromptContinue(message=message, cancel_on_no=True)
          log.status.Print('--------------------------------------------')
          log.status.Print(
              'Start cleaning up RBAC policy for: {}'.format(identity)
          )
          rbac = kube_client.GetRBACForOperations(
              args.membership,
              args.role,
              project_id,
              identity,
              is_user,
              args.anthos_support,
          )
          if kube_client.CleanUpRbacPolicy(rbac):
            log.status.Print(
                'Finished cleaning up the previous RBAC policy for: {}'.format(
                    identity
                )
            )
        return

    # Generate the RBAC policy file from args.
    generated_rbac = rbac_util.GenerateRBAC(args, project_id)

    if args.rbac_output_file:
      sys.stdout.write(
          'Generated RBAC policy is written to file: {} \n'.format(
              args.rbac_output_file
          )
      )
    else:
      sys.stdout.write('Generated RBAC policy is: \n')
      sys.stdout.write('--------------------------------------------\n')

    # Write the generated RBAC policy file to the file provided with
    # "--rbac-output-file" specified or print on the screen.
    final_rbac_policy = ''
    for user in sorted(generated_rbac.keys()):
      final_rbac_policy += generated_rbac.get(user)
    log.WriteToFileOrStdout(
        args.rbac_output_file if args.rbac_output_file else '-',
        final_rbac_policy,
        overwrite=True,
        binary=False,
        private=True,
    )

    # Apply generated RBAC policy to cluster.
    if args.apply:
      sys.stdout.write(
          'Applying the generate RBAC policy to cluster with kubeconfig: {},'
          ' context: {}\n'.format(args.kubeconfig, args.context)
      )

      with kube_util.KubernetesClient(
          kubeconfig=getattr(args, 'kubeconfig', None),
          context=getattr(args, 'context', None),
      ) as kube_client:
        # Check Admin permissions.
        kube_client.CheckClusterAdminPermissions()
        for identity, is_user in generated_rbac.keys():
          with file_utils.TemporaryDirectory() as tmp_dir:
            file = tmp_dir + '/rbac.yaml'
            current_rbac_policy = generated_rbac.get((identity, is_user))
            file_utils.WriteFileContents(file, current_rbac_policy)
            rbac = kube_client.GetRBACForOperations(
                args.membership,
                args.role,
                project_id,
                identity,
                is_user,
                args.anthos_support,)

            # Check whether there are existing RBAC policy for this user, if not,
            # will directly apply the new RBAC policy.
            if not kube_client.GetRbacPolicy(rbac):
              # Check whether there are role confliction, which required clean up.
              need_clean_up = False
              # Override when proposed RBAC policy has diff with existing one.
              override_check = False
              # Checking RBAC policy diff, return None, None if there are no diff.
              diff, err = kube_client.GetRbacPolicyDiff(file)

              if diff is not None:
                override_check = True
                log.status.Print(
                    'The new RBAC policy has diff with previous: \n {}'.format(
                        diff
                    )
                )

              if err is not None:
                # 'Invalid value' means the clusterrole/role permission has been
                # changed. This need to clean up old RBAC policy and then apply
                # the new one.
                if 'Invalid value' in err:
                  rbac_policy_name = kube_client.RbacPolicyName(
                      'permission', project_id, args.membership, identity
                  )

                  rbac_permission_policy = kube_client.GetRbacPermissionPolicy(
                      rbac_policy_name, args.role
                  )

                  log.status.Print(
                      'The existing RBAC policy has conflicts with proposed'
                      ' one:\n{}'.format(rbac_permission_policy)
                  )
                  need_clean_up = True
                  override_check = True
                else:
                  raise exceptions.Error(
                      'Error when getting diff for RBAC policy files for:'
                      ' {}, with error: {}'.format(identity, err)
                  )

              if override_check:
                message = 'The RBAC file will be overridden.'
                console_io.PromptContinue(message=message, cancel_on_no=True)

              if need_clean_up:
                log.status.Print('--------------------------------------------')
                log.status.Print(
                    'Start cleaning up previous RBAC policy for: {}'.format(
                        identity
                    )
                )
                if kube_client.CleanUpRbacPolicy(rbac):
                  log.status.Print(
                      'Finished cleaning up the previous RBAC policy for: {}'
                      .format(identity)
                  )

            try:
              log.status.Print(
                  'Writing RBAC policy for user: {} to cluster.'.format(identity)
              )
              kube_client.ApplyRbacPolicy(file)
            except Exception as e:
              log.status.Print(
                  'Error in applying the RBAC policy to cluster: {}'.format(e)
              )
              raise
          log.status.Print('Successfully applied the RBAC policy to cluster.')
