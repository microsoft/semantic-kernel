# -*- coding: utf-8 -*- # Lint as: python3
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
"""The products command group for the Apigee CLI."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base


class Products(base.Group):
  """Manage Apigee API products."""

  detailed_help = {
      "DESCRIPTION": """
          {description}

          `{command}` manipulates API products. These are collections of
          deployed API resources, combined with quota settings and metadata,
          used to deliver customized and productized API bundles to the
          developer community.
          """,
      "EXAMPLES": """
          To list all API products in the active Cloud Platform project, run:

              $ {command} list

          To create an API product named ``my-apis'' by answering interactive
          prompts about its included proxies and access policies, run:

              $ {command} create my-apis

          To create an API product named ``prod-apis'' that makes every API
          proxy deployed to the ``prod'' environment publicly available, run:

              $ {command} create prod-apis --environments=prod --all-proxies --public-access

          To get a JSON object describing an existing API product, run:

              $ {command} describe PRODUCT_NAME --organization=ORG_NAME --format=json

          To add another API proxy to an existing API product, run:

              $ {command} update PRODUCT_NAME --add-api=API_NAME

          To edit the publicly visible name and description of an API product,
          run:

              $ {command} update PRODUCT_NAME --display-name="New Name" --description="A new description of this product."

          To make an existing product publicly visible and automatically allow
          developers access to it, run:

              $ {command} update PRODUCT_NAME --public-access --automatic-approval

          To delete an existing API product, run:

              $ {command} delete PRODUCT_NAME
          """,
  }
