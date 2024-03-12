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
"""Command for generating main.tf file to configure Terraform Provider."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.util.declarative import flags
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core.console import console_io
from googlecloudsdk.core.console import progress_tracker
from googlecloudsdk.core.util import files
from mako import runtime
from mako import template


_SCHEMA_VERSION = '0.2'
_MIN_PROVIDER_VERSION = 'v3.90.0'

_SUPPORTED_MSG = ('This command supports Google Terraform Provider version'
                  ' {}+ and Terraform Provider Schema {}'.format(
                      _MIN_PROVIDER_VERSION, _SCHEMA_VERSION))

_DETAILED_HELP = {
    'DESCRIPTION':
        """{description}

        """+ _SUPPORTED_MSG,
    'EXAMPLES':
        """
    To generate a `main.tf` file in the current directory using the gcloud default values for `zone`, `region` and `project` run:

      $ {command}

    To generate a `main.tf` file in the current directory using the user suppplied values for `zone`, `region` and `project` run:

      $ {command}  --project="my-project-id" --region="us-central1" --zone="us-central1-c

    To generate a `main.tf` file in the current directory using the gcloud default `billing_project` run:

      $ {command} --use-gcloud-billing-project

    To generate a `main.tf` file in the current directory using user specified `billing_project` value run:

      $ {command} --tf-user-project-override --tf-billing-project="my-other-project-id"
   """
}

_INIT_TEMPLATE_NAME = os.path.join(
    os.path.dirname(__file__), 'templates', 'main_tf.tpl')

INIT_FILE_TEMPLATE = template.Template(filename=_INIT_TEMPLATE_NAME)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class InitProvider(base.DeclarativeCommand):
  """Generate main.tf file to configure Google Cloud Terraform Provider."""

  detailed_help = _DETAILED_HELP

  def _GetBillingParams(self, args_namspace):
    """Process billing project flags in args and return Terraform settings."""
    use_gcloud_billing = args_namspace.use_gcloud_billing_project
    user_project_override = billing_project = None
    if use_gcloud_billing:
      billing_project = properties.VALUES.billing.quota_project.Get()
      user_project_override = 'true'
    elif args_namspace.tf_user_project_override:
      billing_project = args_namspace.tf_billing_project
      user_project_override = 'true'
    return user_project_override, billing_project

  @classmethod
  def Args(cls, parser):
    flags.AddInitProviderArgs(parser)

  def Run(self, args):
    do_override, billing_project = self._GetBillingParams(args)
    project = args.project or properties.VALUES.core.project.Get()
    region = args.region or properties.VALUES.compute.region.Get()
    zone = args.zone or properties.VALUES.compute.zone.Get()
    template_context = {
        'project': project,
        'region': region,
        'zone': zone,
        'user_override': do_override,
        'billing_project': billing_project
    }
    path = os.path.join(files.GetCWD(), 'main.tf')
    if os.path.isfile(path):
      console_io.PromptContinue('{} Exists.'.format(path),
                                prompt_string='Overwrite?',
                                cancel_on_no=True,
                                cancel_string='Init Provider cancelled.')
    with progress_tracker.ProgressTracker('Creating Terraform init module'):
      with files.FileWriter(path, create_path=True) as f:
        ctx = runtime.Context(f, **template_context)
        INIT_FILE_TEMPLATE.render_context(ctx)
    log.status.Print('Created Terraform module file {path}.'.format(path=path))
