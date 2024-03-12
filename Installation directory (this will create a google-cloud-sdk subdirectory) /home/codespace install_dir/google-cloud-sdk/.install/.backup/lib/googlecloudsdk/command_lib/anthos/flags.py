# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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
"""Command line flags for Anthos commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.core.util import files

_MERGE_STRATEGIES = {
    'resource-merge': ('perform a structural comparison of the '
                       'original/updated Resources, and merge the changes '
                       'into the local package.'),
    'fast-forward': ('fail without updating if the local package was modified'
                     ' since it was fetched.'),
    'alpha-git-patch': ("use 'git format-patch' and 'git am' to apply a patch "
                        'of the changes between the source version and '
                        'destination version. Requires the local package to '
                        'have been committed to a local git repo.'),
    'force-delete-replace': ('This will wipe all local changes to the package. '
                             'Deletes the contents of local package from '
                             'PACKAGE_DIR and replace them with the remote '),
}


def GetFlagOrPositional(name, positional=False, **kwargs):
  """Return argument called name as either flag or positional."""
  dest = name.replace('-', '_').upper()
  if positional:
    flag = dest
    kwargs.pop('required', None)
  else:
    flag = '--{}'.format(name.replace('_', '-').lower())
  if not positional:
    kwargs['dest'] = dest
  return base.Argument(flag, **kwargs)


def GetRepoURIFlag(positional=True,
                   required=True,
                   help_override=None,
                   metavar=None):
  """Get REPO_URI flag."""
  help_txt = help_override or """\
      Git repository URI containing 1 or more packages as where:

      * REPO_URI - URI of a git repository containing 1 or more packages as
        subdirectories. In most cases the .git suffix should be specified to
        delimit the REPO_URI from the PKG_PATH, but this is not required for
        widely recognized repo prefixes.  If REPO_URI cannot be parsed then
        an error will be printed an asking for '.git' to be specified
        as part of the argument. e.g. https://github.com/kubernetes/examples.git

      * PKG_PATH (optional) - Path to Git subdirectory containing Anthos package files.
       Uses '/' as the path separator (regardless of OS). e.g. staging/cockroachdb.
       Defaults to the root directory.

      * GIT_REF (optional)- A git tag, branch, ref or commit for the remote version of the
        package to fetch. Defaults to the repository default branch e.g. @main
  """
  if not metavar:
    metavar = 'REPO_URI[.git]/[PKG_PATH][@GIT_REF]'
  return GetFlagOrPositional(
      name='repo_uri',
      positional=positional,
      required=required,
      help=help_txt,
      metavar=metavar)


def GetPackagePathFlag(metavar=None):
  return GetFlagOrPositional(
      name='package_path',
      positional=False,
      required=False,
      help="""\
      Path to remote subdirectory containing Kubernetes Resource configuration
      files or directories.
      Defaults to the root directory.
      Uses '/' as the path separator (regardless of OS).
      e.g. staging/cockroachdb
      """,
      metavar=metavar)


def GetLocalDirFlag(positional=True,
                    required=True,
                    help_override=None,
                    metavar=None):
  """Get Local Package directory flag."""
  help_txt = help_override or """\
      The local directory to fetch the package to.
      e.g. ./my-cockroachdb-copy
      * If the directory does NOT exist: create the specified directory
        and write the package contents to it

      * If the directory DOES exist: create a NEW directory under the
        specified one, defaulting the name to the Base of REPO/PKG_PATH

      * If the directory DOES exist and already contains a directory with
        the same name of the one that would be created: fail
      """
  return GetFlagOrPositional(
      name='LOCAL_DIR',
      positional=positional,
      required=required,
      type=ExpandLocalDirAndVersion,
      help=help_txt,
      metavar=metavar)


def GetFilePatternFlag():
  return GetFlagOrPositional(
      name='pattern',
      positional=False,
      required=False,
      help="""\
      Pattern to use for writing files. May contain the following formatting
      verbs %n: metadata.name, %s: metadata.namespace, %k: kind
      (default "%n_%k.yaml")
      """)


def GetStrategyFlag():
  return base.Argument(
      '--strategy',
      required=False,
      choices=_MERGE_STRATEGIES,
      help='Controls how changes to the local package are handled.')


def GetDryRunFlag(help_override=None):
  help_txt = help_override or ('If true and command fails print the '
                               'underlying command that was executed and '
                               'its exit status.')
  return base.Argument(
      '--dry-run', action='store_true', required=False, help=help_txt)


def GetDescriptionFlag():
  return base.Argument(
      '--description', required=False, help='Description of the Package.')


def GetNameFlag():
  return base.Argument('--name', required=False, help='Name of the package.')


def GetTagsFlag():
  return base.Argument(
      '--tags',
      required=False,
      type=arg_parsers.ArgDict(),
      metavar='TAG=VALUE',
      help='Tags for the package.')


def GetInfoUrlFlag():
  return base.Argument(
      '--info-url',
      required=False,
      help='Url with more info about the package.')


def ExpandLocalDirAndVersion(directory):
  """Expand HOME relative (~) directory with optional git_ref.

  Args:
      directory: str, directory path in the format PATH[/][@git_ref].

  Returns:
      str, expanded full directory path with git_ref (if provided)
  """
  path = directory.split('@') if directory else ''
  full_dir = files.ExpandHomeDir(path[0])
  if len(path) == 2:
    full_dir += '@' + path[1]

  return full_dir


# Anthos Auth
def GetClusterFlag(positional=False,
                   required=False,
                   help_override=None,
                   metavar=None):
  """Anthos operation cluster name flag."""
  help_txt = help_override or ('Cluster to authenticate against. If no cluster '
                               'is specified, the command will print a list '
                               'of available options.')
  return GetFlagOrPositional(
      name='CLUSTER',
      positional=positional,
      required=required,
      help=help_txt,
      metavar=metavar)


def GetLoginConfigFlag():
  return base.Argument(
      '--login-config',
      required=False,
      help='Specifies the configuration yaml '
      'file for login. Can be a file path or a URL.')


def GetLoginConfigCertFlag():
  return base.Argument(
      '--login-config-cert',
      required=False,
      type=ExpandLocalDirAndVersion,
      help='Specifies the CA certificate file to be added to trusted pool '
      'for making HTTPS connections to a `--login-config` URL.')


def GetUserFlag():
  return base.Argument(
      '--user',
      required=False,
      help='If configuring multiple user accounts in the same kubecconfig '
      'file, you can specify a user to differentiate between them.')


def GetSetPreferredAuthenticationFlag():
  return base.Argument(
      '--set-preferred-auth',
      required=False,
      action='store_true',
      help='If set, forces update of preferred '
      'authentication for given cluster')


def GetServerFlag():
  return base.Argument(
      '--server',
      required=False,
      help=(
          'Specifies the URL of API server of the cluster to authenticate'
          ' against.'
      ),
  )


def GetOutputDirFlag(positional=False,
                     required=False,
                     help_override=None,
                     metavar='OUTPUT-DIR',
                     default=None):
  """Anthos operation local output directory flag."""
  help_txt = help_override or ('The output directory of the cluster resources.'
                               ' If empty will export files to ./CLUSTER_NAME')
  return GetFlagOrPositional(
      name='OUTPUT_DIRECTORY',
      positional=positional,
      required=required,
      type=ExpandLocalDirAndVersion,
      help=help_txt,
      default=default,
      metavar=metavar)


def GetLocationFlag():
  """Anthos location flag."""
  return base.Argument(
      '--location',
      required=False,
      help='Specifies the Google Cloud location to use. If not'
      'specified will use the current compute/zone property.')


def GetMergeFromFlag():
  """Anthos create-login-config Merge-From flag."""
  return base.Argument(
      '--merge-from',
      required=False,
      help='Specifies the file path of an existing login '
      'configuration file to merge with.')


def GetConfigOutputFileFlag():
  """Anthos create-login-config output flag."""
  return base.Argument(
      '--output',
      required=False,
      type=ExpandLocalDirAndVersion,
      help='Destination to write login configuration file. '
      'Defaults to "kubectl-anthos-config.yaml".')


# Anthos auth token flags.
def GetTypeFlag():
  """Anthos auth token type flag, specifies the type of token to be created."""
  return base.ChoiceArgument(
      '--type',
      required=True,
      choices=['aws', 'oidc'],
      help_str='Type of token to be created.')


def GetAwsStsRegionFlag():
  """Anthos auth token aws-sts-region flag, specifies the region for AWS STS endpoint for creating AWS token."""
  return base.Argument(
      '--aws-sts-region', required=False, help='Region for AWS STS endpoint.')


def GetTokenClusterFlag():
  """Anthos auth token cluster flag, specifies cluster name for creating AWS token."""
  return base.Argument(
      '--cluster',
      required=False,
      help='Name of the cluster for which token is created.')


def GetIdTokenFlag():
  """Anthos auth token id-token flag, specifies the ID Token received from identity provider after authorization flow."""
  return base.Argument(
      '--id-token',
      required=False,
      help='ID Token received from identity provider after authorization flow.')


def GetAccessTokenFlag():
  """Anthos auth token access-token flag, specifies the Access Token received from identity provider after authorization flow."""
  return base.Argument(
      '--access-token',
      required=False,
      help=(
          'Access Token received from identity provider after authorization'
          ' flow.'
      ),
  )


def GetAccessTokenExpiryFlag():
  """Anthos auth token access-token-expiry flag, specifies the Expiration time of access token received from identity provider after authorization flow."""
  return base.Argument(
      '--access-token-expiry',
      required=False,
      help=(
          'Expiration time of access token received from identity provider'
          ' after authorization flow. The expected format is the number of'
          ' seconds elapsed since January 1, 1970 UTC.'
      ),
  )


def GetRefreshTokenFlag():
  """Anthos auth token refresh-token flag, specifies the Refresh Token received from identity provider after authorization flow."""
  return base.Argument(
      '--refresh-token',
      required=False,
      help=(
          'Refresh Token received from identity provider after authorization'
          ' flow.'
      ),
  )


def GetClientIdFlag():
  """Anthos auth token client-id flag, specifies the ClientID is the id for OIDC client application."""
  return base.Argument(
      '--client-id',
      required=False,
      help='ClientID is the id for OIDC client application.')


def GetClientSecretFlag():
  """Anthos auth token client-secret flag, specifies the Client Secret is the shared secret between OIDC client application and OIDC provider."""
  return base.Argument(
      '--client-secret',
      required=False,
      help=(
          'Client Secret is the shared secret between OIDC client application'
          ' and OIDC provider.'
      ),
  )


def GetIdpCertificateAuthorityDataFlag():
  """Anthos auth token idp-certificate-authority-data flag, specifies the PEM-encoded certificate authority certificate for OIDC provider."""
  return base.Argument(
      '--idp-certificate-authority-data',
      required=False,
      help='PEM-encoded certificate authority certificate for OIDC provider.')


def GetIdpIssuerUrlFlag():
  """Anthos auth token idp-issuer-url flag, specifies the URI for the OIDC provider."""
  return base.Argument(
      '--idp-issuer-url',
      required=False,
      help=(
          'URI for the OIDC provider. This URI should point to the level below'
          ' .well-known/openid-configuration.'
      ),
  )


def GetKubeconfigPathFlag():
  """Anthos auth token kubeconfig-path flag, specifies the Path to the kubeconfig path that would be updated with ID and access token on expiry."""
  return base.Argument(
      '--kubeconfig-path',
      required=False,
      help=(
          'Path to the kubeconfig path that would be updated with ID and access'
          ' token on expiry.'
      ),
  )


def GetTokenUserFlag():
  """Anthos auth token user flag, specifies the User used in kubeconfig."""
  return base.Argument(
      '--user', required=False, help='User used in kubeconfig.'
  )
