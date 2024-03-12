# -*- coding: utf-8 -*- #
# Copyright 2018 Google LLC. All Rights Reserved.
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
"""Command group for Cloud Memorystore Redis instances."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base


class Instances(base.Group):
  """Manage Cloud Memorystore Redis instances.

  ## EXAMPLES

  To create an instance with the name `my-redis-instance`, run:

    $ {command} create my-redis-instance

  To delete an instance with the name `my-redis-instance`, run:

    $ {command} delete my-redis-instance

  To display the details for an instance with the name `my-redis-instance`, run:

    $ {command} describe my-redis-instance

  To list all the instances, run:

    $ {command} list

  To set the label `env` to `prod` for an instance with the name
  `my-redis-instance`, run:

    $ {command} my-redis-instance --update-labels=env=prod
  """
