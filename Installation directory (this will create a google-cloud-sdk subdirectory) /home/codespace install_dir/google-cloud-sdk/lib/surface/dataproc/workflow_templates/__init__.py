# -*- coding: utf-8 -*- #
# Copyright 2015 Google LLC. All Rights Reserved.
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
"""The command group for cloud dataproc workflow templates."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base


class WorkflowTemplates(base.Group):
  r"""Create and manage Dataproc workflow templates.

  Create and manage Dataproc workflow templates.

  ## EXAMPLES

  To create a workflow template, run:

    $ {command} create my_template

  To instantiate a workflow template, run:

    $ {command} instantiate my_template

  To instantiate a workflow template from a file, run:

    $ {command} instantiate-from-file --file template.yaml

  To delete a workflow template, run:

    $ {command} delete my_template

  To view the details of a workflow template, run:

    $ {command} describe my_template

  To see the list of all workflow templates, run:

    $ {command} list

  To remove a job from a workflow template, run:

    $ {command} remove-job my_template --step-id id

  To update managed cluster in a workflow template, run:

    $ {command} set-managed-cluster my_template --num-masters 5

  To update cluster selector in a workflow template, run:

    $ {command} set-cluster-selector my_template \
        --cluster-labels environment=prod

  """

  pass
