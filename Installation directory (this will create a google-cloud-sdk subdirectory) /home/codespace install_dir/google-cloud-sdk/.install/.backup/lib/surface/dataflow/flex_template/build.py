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
"""Implementation of gcloud dataflow flex_template build command.
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.dataflow import apis
from googlecloudsdk.calliope import actions
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.core import properties


def _CommonArgs(parser):
  """Registers flags for this command.

  Args:
    parser: argparse.ArgumentParser to register arguments with.
  """
  image_args = parser.add_mutually_exclusive_group(required=True)
  image_building_args = image_args.add_argument_group()
  parser.add_argument(
      'template_file_gcs_path',
      metavar='TEMPLATE_FILE_GCS_PATH',
      help=('The Google Cloud Storage location of the flex template file.'
            'Overrides if file already exists.'),
      type=arg_parsers.RegexpValidator(r'^gs://.*',
                                       'Must begin with \'gs://\''))

  image_args.add_argument(
      '--image',
      help=('Path to the any image registry location of the prebuilt flex '
            'template image.'))

  parser.add_argument(
      '--image-repository-username-secret-id',
      help=('Secret Manager secret id for the username to authenticate to '
            'private registry. Should be in the format '
            'projects/{project}/secrets/{secret}/versions/{secret_version} or '
            'projects/{project}/secrets/{secret}. If the version is not '
            'provided latest version will be used.'),
      type=arg_parsers.RegexpValidator(
          r'^projects\/[^\n\r\/]+\/secrets\/[^\n\r\/]+(\/versions\/[^\n\r\/]+)?$',
          'Must be in the format '
          '\'projects/{project}/secrets/{secret}\' or'
          '\'projects/{project}/secrets/{secret}/versions/{secret_version}\'.'))

  parser.add_argument(
      '--image-repository-password-secret-id',
      help=('Secret Manager secret id for the password to authenticate to '
            'private registry. Should be in the format '
            'projects/{project}/secrets/{secret}/versions/{secret_version} or '
            'projects/{project}/secrets/{secret}. If the version is not '
            'provided latest version will be used.'),
      type=arg_parsers.RegexpValidator(
          r'^projects\/[^\n\r\/]+\/secrets\/[^\n\r\/]+(\/versions\/[^\n\r\/]+)?$',
          'Must be in the format '
          '\'projects/{project}/secrets/{secret}\' or'
          '\'projects/{project}/secrets/{secret}/versions/{secret_version}\'.'))

  parser.add_argument(
      '--image-repository-cert-path',
      help=('The full URL to self-signed certificate of private registry in '
            'Cloud Storage. For example, gs://mybucket/mycerts/selfsigned.crt. '
            'The certificate provided in Cloud Storage must be DER-encoded and '
            'may be supplied in binary or printable (Base64) encoding. If the '
            'certificate is provided in Base64 encoding, it must be bounded at '
            'the beginning by -----BEGIN CERTIFICATE-----, and must be bounded '
            'at the end by -----END CERTIFICATE-----. If this parameter is '
            'provided, the docker daemon in the template launcher will be '
            'instructed to trust that certificate. '),
      type=arg_parsers.RegexpValidator(r'^gs://.*',
                                       'Must begin with \'gs://\''))

  parser.add_argument(
      '--sdk-language',
      help=('SDK language of the flex template job.'),
      choices=['JAVA', 'PYTHON', 'GO'],
      required=True)

  parser.add_argument(
      '--metadata-file',
      help='Local path to the metadata json file for the flex template.',
      type=arg_parsers.FileContents())

  parser.add_argument(
      '--print-only',
      help=('Prints the container spec to stdout. Does not save in '
            'Google Cloud Storage.'),
      default=False,
      action=actions.StoreBooleanProperty(
          properties.VALUES.dataflow.print_only))

  parser.add_argument(
      '--staging-location',
      help=('Default Google Cloud Storage location to stage local files.'
            "(Must be a URL beginning with 'gs://'.)"),
      type=arg_parsers.RegexpValidator(r'^gs://.*',
                                       'Must begin with \'gs://\''))

  parser.add_argument(
      '--temp-location',
      help=('Default Google Cloud Storage location to stage temporary files. '
            'If not set, defaults to the value for --staging-location.'
            "(Must be a URL beginning with 'gs://'.)"),
      type=arg_parsers.RegexpValidator(r'^gs://.*',
                                       'Must begin with \'gs://\''))

  parser.add_argument(
      '--service-account-email',
      type=arg_parsers.RegexpValidator(r'.*@.*\..*',
                                       'must provide a valid email address'),
      help='Default service account to run the workers as.')

  parser.add_argument(
      '--max-workers',
      type=int,
      help='Default maximum number of workers to run.')

  parser.add_argument(
      '--disable-public-ips',
      action=actions.StoreBooleanProperty(
          properties.VALUES.dataflow.disable_public_ips),
      help='Cloud Dataflow workers must not use public IP addresses.')

  parser.add_argument(
      '--num-workers',
      type=int,
      help='Initial number of workers to use by default.')

  parser.add_argument(
      '--worker-machine-type',
      help='Default type of machine to use for workers. Defaults to '
      'server-specified.')

  parser.add_argument(
      '--subnetwork',
      help='Default Compute Engine subnetwork for launching instances '
      'to run your pipeline.')

  parser.add_argument(
      '--network',
      help='Default Compute Engine network for launching instances to '
      'run your pipeline.')

  parser.add_argument(
      '--dataflow-kms-key',
      help='Default Cloud KMS key to protect the job resources.')

  region_group = parser.add_mutually_exclusive_group()
  region_group.add_argument(
      '--worker-region',
      help='Default region to run the workers in.')

  region_group.add_argument(
      '--worker-zone',
      help='Default zone to run the workers in.')

  parser.add_argument(
      '--enable-streaming-engine',
      action=actions.StoreBooleanProperty(
          properties.VALUES.dataflow.enable_streaming_engine),
      help='Enable Streaming Engine for the streaming job by default.')

  parser.add_argument(
      '--gcs-log-dir',
      help=('Google Cloud Storage directory to save build logs.'
            "(Must be a URL beginning with 'gs://'.)"),
      type=arg_parsers.RegexpValidator(r'^gs://.*',
                                       'Must begin with \'gs://\''),
      default=None)

  parser.add_argument(
      '--additional-experiments',
      metavar='ADDITIONAL_EXPERIMENTS',
      type=arg_parsers.ArgList(),
      action=arg_parsers.UpdateAction,
      help=
      ('Default experiments to pass to the job.'))

  parser.add_argument(
      '--additional-user-labels',
      metavar='ADDITIONAL_USER_LABELS',
      type=arg_parsers.ArgDict(),
      action=arg_parsers.UpdateAction,
      help=
      ('Default user labels to pass to the job.'))

  image_building_args.add_argument(
      '--image-gcr-path',
      help=('The Google Container Registry or Google Artifact Registry '
            'location to store the flex template image to be built.'),
      type=arg_parsers.RegexpValidator(
          r'^(.*\.){0,1}gcr.io/.*|^(.){2,}-docker.pkg.dev/.*',
          ('Must begin with \'[multi-region.]gcr.io/\' or '
           '\'[region.]-docker.pkg.dev/\'. Please check '
           'https://cloud.google.com/container-registry/docs/overview '
           'for available multi-regions in GCR or '
           'https://cloud.google.com/artifact-registry/docs/repo-organize#'
           'locations for available location in GAR')),
      required=True)
  pipeline_args = image_building_args.add_mutually_exclusive_group(
      required=True)
  pipeline_args.add_argument(
      '--jar',
      metavar='JAR',
      type=arg_parsers.ArgList(),
      action=arg_parsers.UpdateAction,
      help=('Local path to your dataflow pipeline jar file and all their '
            'dependent jar files required for the flex template classpath. '
            'You can pass them as a comma separated list or repeat '
            'individually with --jar flag. Ex: --jar="code.jar,dep.jar" or '
            '--jar code.jar, --jar dep.jar.'))

  pipeline_args.add_argument(
      '--py-path',
      metavar='PY_PATH',
      type=arg_parsers.ArgList(),
      action=arg_parsers.UpdateAction,
      help=('Local path to your dataflow pipeline python files and all their '
            'dependent files required for the flex template classpath. '
            'You can pass them as a comma separated list or repeat '
            'individually with --py-path flag. '
            'Ex: --py-path="path/pipleline/,path/dependency/" or '
            '--py-path path/pipleline/, --py-path path/dependency/.'))

  pipeline_args.add_argument(
      '--go-binary-path',
      metavar='GO_BINARY_PATH',
      help=('Local path to your compiled dataflow pipeline Go binary. '
            'The binary should be compiled to run on the target worker '
            'architecture (usually linux-amd64). See '
            'https://beam.apache.org/documentation/sdks/go-cross-compilation/ '
            'for more information.'))

  image_building_args.add_argument(
      '--flex-template-base-image',
      help=(
          'Flex template base image to be used while building the container'
          ' image. Allowed choices are JAVA8, JAVA11, JAVA17 or gcr.io path of'
          ' the specific version of the base image. For JAVA8, JAVA11 and'
          ' JAVA17 option, we use the latest base image version to build the'
          ' container. You can also provide a specific version from this link '
          ' https://gcr.io/dataflow-templates-base/'
      ),
      type=arg_parsers.RegexpValidator(
          r'^JAVA11$|^JAVA17$|^JAVA8$|^PYTHON3$|^GO$|^gcr.io/.*',
          "Must be JAVA11, JAVA17, JAVA8, PYTHON3, GO, or begin with 'gcr.io/'",
      ),
      required=True,
  )

  image_building_args.add_argument(
      '--env',
      metavar='ENV',
      type=arg_parsers.ArgDict(),
      action=arg_parsers.UpdateAction,
      help=
      ('Environment variables to create for the Dockerfile. '
       'You can pass them as a comma separated list or repeat individually '
       'with --env flag. Ex: --env="A=B,C=D" or --env A=B, --env C=D.'
       'When you reference files/dir in env variables, please specify relative '
       'path to the paths passed via --py-path.Ex: if you pass. '
       '--py-path="path/pipleline/" then set '
       'FLEX_TEMPLATE_PYTHON_PY_FILE="pipeline/pipeline.py" '
       'You can find the list of supported environment variables in this '
       'link. https://cloud.google.com/dataflow/docs/guides/templates/'
       'configuring-flex-templates'
       '#setting_required_dockerfile_environment_variables.'),
      required=True)


def _CommonRun(args):
  """Runs the command.

  Args:
    args: The arguments that were provided to this command invocation.

  Returns:
    A Job message.
  """
  template_args = apis.TemplateArguments(
      max_workers=args.max_workers,
      num_workers=args.num_workers,
      network=args.network,
      subnetwork=args.subnetwork,
      worker_machine_type=args.worker_machine_type,
      kms_key_name=args.dataflow_kms_key,
      staging_location=args.staging_location,
      temp_location=args.temp_location,
      disable_public_ips=properties.VALUES.dataflow.disable_public_ips.GetBool(
      ),
      service_account_email=args.service_account_email,
      worker_region=args.worker_region,
      worker_zone=args.worker_zone,
      enable_streaming_engine=properties.VALUES.dataflow.enable_streaming_engine
      .GetBool(),
      additional_experiments=args.additional_experiments,
      additional_user_labels=args.additional_user_labels)
  image_path = args.image
  if not args.image:
    image_path = args.image_gcr_path
    apis.Templates.BuildAndStoreFlexTemplateImage(args.image_gcr_path,
                                                  args.flex_template_base_image,
                                                  args.jar, args.py_path,
                                                  args.go_binary_path, args.env,
                                                  args.sdk_language,
                                                  args.gcs_log_dir)

  return apis.Templates.BuildAndStoreFlexTemplateFile(
      args.template_file_gcs_path, image_path, args.metadata_file,
      args.sdk_language, args.print_only, template_args,
      args.image_repository_username_secret_id,
      args.image_repository_password_secret_id, args.image_repository_cert_path)


@base.ReleaseTracks(base.ReleaseTrack.GA, base.ReleaseTrack.BETA)
class Build(base.Command):
  """Builds a flex template file from the specified parameters."""

  detailed_help = {
      'DESCRIPTION':
          'Builds a flex template file from the specified parameters.',
      'EXAMPLES':
          """\
          To build and store a the flex template json file, run:

            $ {command} gs://template-file-gcs-path --image=gcr://image-path \
              --metadata-file=/local/path/to/metadata.json --sdk-language=JAVA

          If using prebuilt template image from private registry, run:

            $ {command} gs://template-file-gcs-path \
              --image=private.registry.com:3000/image-path \
              --image-repository-username-secret-id="projects/test-project/secrets/username-secret"
              --image-repository-password-secret-id="projects/test-project/secrets/password-secret/versions/latest"
              --metadata-file=metadata.json
              --sdk-language=JAVA

          To build the template image and flex template json file, run:

            $ {command} gs://template-file-gcs-path \
              --image-gcr-path=gcr://path-to-store-image \
              --jar=path/to/pipeline.jar --jar=path/to/dependency.jar \
              --env=FLEX_TEMPLATE_JAVA_MAIN_CLASS=classpath \
              --flex-template-base-image=JAVA11 \
              --metadata-file=/local/path/to/metadata.json --sdk-language=JAVA
          """,
  }

  @staticmethod
  def Args(parser):
    _CommonArgs(parser)

  def Run(self, args):
    return _CommonRun(args)
