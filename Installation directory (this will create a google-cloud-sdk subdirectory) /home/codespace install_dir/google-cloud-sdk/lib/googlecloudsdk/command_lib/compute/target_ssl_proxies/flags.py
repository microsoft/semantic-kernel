# -*- coding: utf-8 -*- #
# Copyright 2016 Google LLC. All Rights Reserved.
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
"""Flags and helpers for the compute target-ssl-proxies commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.command_lib.compute import completers as compute_completers
from googlecloudsdk.command_lib.compute import flags as compute_flags


DEFAULT_LIST_FORMAT = """\
    table(
      name,
      proxyHeader,
      service.basename(),
      sslCertificates.map().basename().list():label=SSL_CERTIFICATES,
      certificateMap.basename()
    )"""


class TargetSslProxiesCompleter(compute_completers.ListCommandCompleter):

  def __init__(self, **kwargs):
    super(TargetSslProxiesCompleter, self).__init__(
        collection='compute.targetSslProxies',
        list_command='compute target-ssl-proxies list --uri',
        **kwargs)


def TargetSslProxyArgument(required=True, plural=False):
  return compute_flags.ResourceArgument(
      resource_name='target SSL proxy',
      completer=TargetSslProxiesCompleter,
      plural=plural,
      custom_plural='target SSL proxies',
      required=required,
      global_collection='compute.targetSslProxies')
