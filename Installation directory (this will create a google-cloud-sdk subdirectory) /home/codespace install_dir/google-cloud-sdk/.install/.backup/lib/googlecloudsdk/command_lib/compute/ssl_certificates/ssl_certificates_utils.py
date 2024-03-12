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
"""Code that's shared between multiple ssl_certificates subcommands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals


def IsRegionalSslCertificatesRef(ssl_certificate_ref):
  """Returns True if the SSL Certificate reference is regional."""
  return ssl_certificate_ref.Collection() == 'compute.regionSslCertificates'


def IsGlobalSslCertificatesRef(ssl_certificate_ref):
  """Returns True if the SSL Certificate reference is global."""
  return ssl_certificate_ref.Collection() == 'compute.sslCertificates'
