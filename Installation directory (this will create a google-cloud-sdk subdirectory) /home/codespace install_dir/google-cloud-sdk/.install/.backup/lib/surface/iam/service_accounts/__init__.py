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

"""Commands for creating and manipulating service accounts."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base


class ServiceAccounts(base.Group):
  """Create and manipulate service accounts.

     Create and manipulate IAM service accounts. A service account is a special
     Google account that belongs to your application or a VM, instead of to an
     individual end user. Your application uses the service account to call the
     Google API of a service, so that the users aren't directly involved.

     Note: Service accounts use client quotas for tracking usage.

     More information on service accounts can be found at:
     https://cloud.google.com/iam/docs/service-accounts
  """
